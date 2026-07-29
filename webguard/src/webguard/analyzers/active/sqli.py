"""SQL Injection — testes time-based, error-based e boolean-based."""

from __future__ import annotations

import re
import time
import asyncio
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import httpx

from webguard.core.models import (
    Confidence, Finding, Mode, RateLimiter, ScanContext, ScanRecord, Severity,
)
from webguard.core.guard import RequestGuard
from webguard.core.registry import analyzer

# Threshold para time-based (segundos)
SLEEP_DELAY = 5
TIME_THRESHOLD = 4.0  # Se demorar mais que 4s, provavelmente funcionou
CONFIRMATION_ROUNDS = 2

# Payloads time-based (MySQL, PostgreSQL, MSSQL, SQLite)
TIME_PAYLOADS = [
    # MySQL
    ("' OR SLEEP({delay})-- -", "MySQL SLEEP"),
    ("' OR SLEEP({delay})#", "MySQL SLEEP (#)"),
    ("1' AND SLEEP({delay})-- -", "MySQL AND SLEEP"),
    # PostgreSQL
    ("'; SELECT pg_sleep({delay})-- -", "PostgreSQL pg_sleep"),
    ("' OR pg_sleep({delay})::text='1", "PostgreSQL pg_sleep inline"),
    # MSSQL
    ("'; WAITFOR DELAY '0:0:{delay}'-- -", "MSSQL WAITFOR"),
    ("' OR 1=1; WAITFOR DELAY '0:0:{delay}'-- -", "MSSQL WAITFOR OR"),
    # SQLite (não tem sleep nativo, mas heavy query)
    ("' AND 1=randomblob(500000000)-- -", "SQLite heavy query"),
]

# Payloads error-based
ERROR_PAYLOADS = [
    "'",
    "''",
    '"',
    "' OR '1'='1",
    "' OR ''='",
    "1' ORDER BY 100-- -",
    "1 UNION SELECT NULL-- -",
    "') OR ('1'='1",
    "' AND EXTRACTVALUE(1, CONCAT(0x7e, VERSION()))-- -",
]

# Padrões de erro SQL na resposta
SQL_ERROR_PATTERNS = [
    re.compile(r"you have an error in your sql syntax", re.I),
    re.compile(r"warning.*?mysql", re.I),
    re.compile(r"unclosed quotation mark", re.I),
    re.compile(r"quoted string not properly terminated", re.I),
    re.compile(r"ORA-\d{5}", re.I),
    re.compile(r"Microsoft OLE DB Provider for SQL Server", re.I),
    re.compile(r"ODBC SQL Server Driver", re.I),
    re.compile(r"SQLServer JDBC Driver", re.I),
    re.compile(r"PostgreSQL.*?ERROR", re.I),
    re.compile(r"pg_query\(\).*?ERROR", re.I),
    re.compile(r"unterminated.*?string", re.I),
    re.compile(r"SQL syntax.*?MySQL", re.I),
    re.compile(r"valid MySQL result", re.I),
    re.compile(r"MySqlClient\.", re.I),
    re.compile(r"com\.mysql\.jdbc", re.I),
    re.compile(r"Syntax error.*?in query expression", re.I),
    re.compile(r"Data type mismatch", re.I),
    re.compile(r"SQLSTATE\[", re.I),
    re.compile(r"sqlite3\.OperationalError", re.I),
    re.compile(r"SQLite/JDBCDriver", re.I),
    re.compile(r"near \".*?\": syntax error", re.I),
    re.compile(r"SELECTs to the left and right.*?do not have the same number", re.I),
]

# Payloads boolean-based
BOOL_TRUE_PAYLOADS = [
    "' AND '1'='1",
    "' AND 1=1-- -",
    "1 AND 1=1",
]
BOOL_FALSE_PAYLOADS = [
    "' AND '1'='2",
    "' AND 1=2-- -",
    "1 AND 1=2",
]


@analyzer(mode="active", name="sql-injection")
async def analyze_sqli(record: ScanRecord) -> list[Finding]:
    """Testa SQL Injection nos parâmetros da URL."""
    findings: list[Finding] = []

    # Extrair parâmetros da URL
    parsed = urlparse(record.target_url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    if not params:
        findings.append(Finding(
            id="SQLI-NO-PARAMS",
            category="sqli",
            severity=Severity.INFO,
            title="Nenhum parâmetro GET para testar SQL Injection",
            evidence=f"URL: {record.target_url}",
            explanation="A URL não possui parâmetros query string. SQL Injection "
                        "tipicamente requer pontos de injeção em parâmetros.",
            remediation="Informativo — teste manualmente endpoints com parâmetros.",
            reference="https://owasp.org/www-community/attacks/SQL_Injection",
            analyzer="sql-injection",
            confidence=Confidence.CONFIRMED,
        ))
        return findings

    # Precisamos do guard para fazer requests — recriamos aqui
    ctx = ScanContext()
    rate_limiter = RateLimiter(mode=Mode.ACTIVE, requests_per_second=10)

    async with httpx.AsyncClient(verify=False, timeout=20.0) as client:
        guard = RequestGuard(
            mode=Mode.ACTIVE,
            target_url=record.target_url,
            rate_limiter=rate_limiter,
            ctx=ctx,
            client=client,
        )

        # Baseline: tempo normal de resposta
        baseline_time = await _get_baseline_time(guard, record.target_url)

        for param_name, param_values in params.items():
            original_value = param_values[0] if param_values else ""

            # 1. Error-based
            error_finding = await _test_error_based(
                guard, parsed, params, param_name, original_value, record.target_url
            )
            if error_finding:
                findings.append(error_finding)
                continue  # Se já confirmou, não precisa testar mais

            # 2. Time-based
            time_finding = await _test_time_based(
                guard, parsed, params, param_name, original_value,
                baseline_time, record.target_url
            )
            if time_finding:
                findings.append(time_finding)
                continue

            # 3. Boolean-based
            bool_finding = await _test_boolean_based(
                guard, parsed, params, param_name, original_value, record.target_url
            )
            if bool_finding:
                findings.append(bool_finding)

    if not any(f.severity in (Severity.CRITICAL, Severity.HIGH) for f in findings):
        findings.append(Finding(
            id="SQLI-NOT-FOUND",
            category="sqli",
            severity=Severity.INFO,
            title="Nenhuma SQL Injection detectada nos parâmetros testados",
            evidence=f"Parâmetros testados: {', '.join(params.keys())}",
            explanation="Nenhum dos payloads produziu resposta indicativa de SQL Injection. "
                        "Isso não garante ausência — apenas que os testes automáticos não detectaram.",
            remediation="Informativo — considere testes manuais mais aprofundados.",
            reference="https://owasp.org/www-community/attacks/SQL_Injection",
            analyzer="sql-injection",
            confidence=Confidence.INDETERMINATE,
        ))

    return findings


async def _get_baseline_time(guard: RequestGuard, url: str) -> float:
    """Mede o tempo normal de resposta (média de 3 requests)."""
    times: list[float] = []
    for _ in range(3):
        try:
            start = time.monotonic()
            await guard.request("GET", url, timeout=15.0)
            elapsed = time.monotonic() - start
            times.append(elapsed)
        except Exception:
            times.append(1.0)
        await asyncio.sleep(0.2)
    return sum(times) / len(times) if times else 1.0


async def _test_error_based(
    guard: RequestGuard,
    parsed,
    params: dict,
    param_name: str,
    original_value: str,
    target_url: str,
) -> Finding | None:
    """Testa error-based SQLi."""
    for payload in ERROR_PAYLOADS:
        injected_url = _inject_param(parsed, params, param_name, payload)
        try:
            response = await guard.request("GET", injected_url, timeout=10.0)
            body = response.text

            for pattern in SQL_ERROR_PATTERNS:
                match = pattern.search(body)
                if match:
                    return Finding(
                        id=f"SQLI-ERROR-{param_name.upper()[:20]}",
                        category="sqli",
                        severity=Severity.CRITICAL,
                        title=f"SQL Injection (Error-based) no parâmetro '{param_name}'",
                        evidence=(
                            f"Payload: {payload}\n"
                            f"URL: {injected_url}\n"
                            f"Erro SQL na resposta: {match.group(0)[:200]}"
                        ),
                        payload_sent=payload,
                        explanation="A aplicação retorna mensagens de erro SQL quando "
                                    "caracteres especiais são injetados. Isso confirma "
                                    "que a entrada não é sanitizada e a query é vulnerável.",
                        remediation=(
                            "Use queries parametrizadas (prepared statements):\n"
                            "  cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))\n\n"
                            "NUNCA concatene entrada do usuário diretamente na query."
                        ),
                        reference="https://owasp.org/www-community/attacks/SQL_Injection",
                        analyzer="sql-injection",
                        confidence=Confidence.CONFIRMED,
                    )
        except Exception:
            continue
        await asyncio.sleep(0.1)

    return None


async def _test_time_based(
    guard: RequestGuard,
    parsed,
    params: dict,
    param_name: str,
    original_value: str,
    baseline_time: float,
    target_url: str,
) -> Finding | None:
    """Testa time-based SQLi com confirmação."""
    for payload_template, db_name in TIME_PAYLOADS[:4]:  # Limitar a 4 para não demorar
        payload = payload_template.format(delay=SLEEP_DELAY)
        injected_url = _inject_param(parsed, params, param_name, payload)

        # Round 1
        try:
            start = time.monotonic()
            await guard.request("GET", injected_url, timeout=SLEEP_DELAY + 10)
            elapsed = time.monotonic() - start
        except Exception:
            continue

        if elapsed < (baseline_time + TIME_THRESHOLD):
            await asyncio.sleep(0.1)
            continue

        # Confirmação: round 2
        confirmed = True
        for _ in range(CONFIRMATION_ROUNDS - 1):
            try:
                start = time.monotonic()
                await guard.request("GET", injected_url, timeout=SLEEP_DELAY + 10)
                elapsed2 = time.monotonic() - start
                if elapsed2 < (baseline_time + TIME_THRESHOLD):
                    confirmed = False
                    break
            except Exception:
                confirmed = False
                break

        if confirmed:
            return Finding(
                id=f"SQLI-TIME-{param_name.upper()[:20]}",
                category="sqli",
                severity=Severity.CRITICAL,
                title=f"SQL Injection (Time-based) no parâmetro '{param_name}'",
                evidence=(
                    f"Payload: {payload}\n"
                    f"URL: {injected_url}\n"
                    f"Baseline: {baseline_time:.2f}s\n"
                    f"Com payload: {elapsed:.2f}s (delay esperado: {SLEEP_DELAY}s)\n"
                    f"DB provável: {db_name}\n"
                    f"Confirmado em {CONFIRMATION_ROUNDS} rounds."
                ),
                payload_sent=payload,
                explanation=f"O servidor demorou ~{SLEEP_DELAY}s a mais que o normal "
                            "quando o payload de sleep foi injetado, confirmando que a "
                            "query SQL está sendo executada com a entrada do usuário.",
                remediation=(
                    "Use queries parametrizadas (prepared statements):\n"
                    "  cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))\n\n"
                    "NUNCA concatene entrada do usuário diretamente na query."
                ),
                reference="https://owasp.org/www-community/attacks/SQL_Injection",
                analyzer="sql-injection",
                confidence=Confidence.CONFIRMED,
            )

        await asyncio.sleep(0.2)

    return None


async def _test_boolean_based(
    guard: RequestGuard,
    parsed,
    params: dict,
    param_name: str,
    original_value: str,
    target_url: str,
) -> Finding | None:
    """Testa boolean-based SQLi comparando respostas true vs false."""
    for true_payload, false_payload in zip(BOOL_TRUE_PAYLOADS, BOOL_FALSE_PAYLOADS):
        true_url = _inject_param(parsed, params, param_name, original_value + true_payload)
        false_url = _inject_param(parsed, params, param_name, original_value + false_payload)

        try:
            true_resp = await guard.request("GET", true_url, timeout=10.0)
            await asyncio.sleep(0.1)
            false_resp = await guard.request("GET", false_url, timeout=10.0)
        except Exception:
            continue

        # Se as respostas são significativamente diferentes
        true_len = len(true_resp.text)
        false_len = len(false_resp.text)

        # Diferença > 10% e ambas retornaram 200
        if (true_resp.status_code == 200 and false_resp.status_code == 200 and
                true_len > 100 and abs(true_len - false_len) > true_len * 0.1):
            return Finding(
                id=f"SQLI-BOOL-{param_name.upper()[:20]}",
                category="sqli",
                severity=Severity.HIGH,
                title=f"SQL Injection (Boolean-based) no parâmetro '{param_name}'",
                evidence=(
                    f"Payload TRUE: {true_payload} → {true_len} bytes\n"
                    f"Payload FALSE: {false_payload} → {false_len} bytes\n"
                    f"Diferença: {abs(true_len - false_len)} bytes ({abs(true_len - false_len) / true_len * 100:.1f}%)"
                ),
                payload_sent=f"TRUE: {true_payload} | FALSE: {false_payload}",
                explanation="A resposta muda significativamente entre condições true/false, "
                            "indicando que a condição SQL é avaliada pelo banco.",
                remediation=(
                    "Use queries parametrizadas (prepared statements).\n"
                    "NUNCA concatene entrada do usuário diretamente na query."
                ),
                reference="https://owasp.org/www-community/attacks/SQL_Injection",
                analyzer="sql-injection",
                confidence=Confidence.LIKELY,
            )

        await asyncio.sleep(0.1)

    return None


def _inject_param(parsed, params: dict, target_param: str, payload: str) -> str:
    """Reconstrói a URL com o payload no parâmetro alvo."""
    new_params = {}
    for key, values in params.items():
        if key == target_param:
            new_params[key] = payload
        else:
            new_params[key] = values[0] if values else ""

    new_query = urlencode(new_params)
    return urlunparse((
        parsed.scheme, parsed.netloc, parsed.path,
        parsed.params, new_query, parsed.fragment
    ))
