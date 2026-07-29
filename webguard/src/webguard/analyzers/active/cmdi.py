"""Command Injection — testa injeção de comandos via time-based."""

from __future__ import annotations

import asyncio
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import httpx

from webguard.core.models import (
    Confidence, Finding, Mode, RateLimiter, ScanContext, ScanRecord, Severity,
)
from webguard.core.guard import RequestGuard
from webguard.core.registry import analyzer

SLEEP_DELAY = 5
TIME_THRESHOLD = 4.0
CONFIRMATION_ROUNDS = 2

# Payloads de command injection (time-based, inofensivos)
CMDI_PAYLOADS = [
    # Unix
    ("; sleep {delay}", "Unix semicolon"),
    ("| sleep {delay}", "Unix pipe"),
    ("|| sleep {delay}", "Unix OR"),
    ("& sleep {delay}", "Unix background"),
    ("&& sleep {delay}", "Unix AND"),
    ("`sleep {delay}`", "Unix backtick"),
    ("$(sleep {delay})", "Unix subshell"),
    # Windows
    ("& ping -n {delay} 127.0.0.1", "Windows ping delay"),
    ("| ping -n {delay} 127.0.0.1", "Windows pipe ping"),
    ("&& timeout /t {delay}", "Windows timeout"),
]


@analyzer(mode="active", name="command-injection")
async def analyze_cmdi(record: ScanRecord) -> list[Finding]:
    """Testa Command Injection nos parâmetros da URL."""
    findings: list[Finding] = []

    parsed = urlparse(record.target_url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    if not params:
        findings.append(Finding(
            id="CMDI-NO-PARAMS",
            category="cmdi",
            severity=Severity.INFO,
            title="Nenhum parâmetro para testar Command Injection",
            evidence=f"URL: {record.target_url}",
            explanation="Sem parâmetros para injetar comandos.",
            remediation="Teste endpoints com parâmetros manualmente.",
            reference="https://owasp.org/www-community/attacks/Command_Injection",
            analyzer="command-injection",
            confidence=Confidence.CONFIRMED,
        ))
        return findings

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

        baseline_time = await _get_baseline(guard, record.target_url)

        for param_name in params:
            finding = await _test_param_cmdi(guard, parsed, params, param_name, baseline_time)
            if finding:
                findings.append(finding)

    if not any(f.severity in (Severity.CRITICAL, Severity.HIGH) for f in findings):
        findings.append(Finding(
            id="CMDI-NOT-FOUND",
            category="cmdi",
            severity=Severity.INFO,
            title="Nenhuma Command Injection detectada",
            evidence=f"Parâmetros testados: {', '.join(params.keys())}",
            explanation="Nenhum payload time-based produziu delay esperado.",
            remediation="Informativo.",
            reference="https://owasp.org/www-community/attacks/Command_Injection",
            analyzer="command-injection",
            confidence=Confidence.INDETERMINATE,
        ))

    return findings


async def _get_baseline(guard, url) -> float:
    times = []
    for _ in range(2):
        try:
            start = time.monotonic()
            await guard.request("GET", url, timeout=15.0)
            times.append(time.monotonic() - start)
        except Exception:
            times.append(1.0)
        await asyncio.sleep(0.2)
    return sum(times) / len(times) if times else 1.0


async def _test_param_cmdi(guard, parsed, params, param_name, baseline_time) -> Finding | None:
    for payload_tpl, technique in CMDI_PAYLOADS[:6]:  # Limitar
        payload = payload_tpl.format(delay=SLEEP_DELAY)
        injected_url = _inject_param(parsed, params, param_name, payload)

        try:
            start = time.monotonic()
            await guard.request("GET", injected_url, timeout=SLEEP_DELAY + 10)
            elapsed = time.monotonic() - start
        except Exception:
            continue

        if elapsed < (baseline_time + TIME_THRESHOLD):
            await asyncio.sleep(0.1)
            continue

        # Confirmação
        try:
            start = time.monotonic()
            await guard.request("GET", injected_url, timeout=SLEEP_DELAY + 10)
            elapsed2 = time.monotonic() - start
        except Exception:
            continue

        if elapsed2 >= (baseline_time + TIME_THRESHOLD):
            return Finding(
                id=f"CMDI-{param_name.upper()[:20]}",
                category="cmdi",
                severity=Severity.CRITICAL,
                title=f"Command Injection no parâmetro '{param_name}'",
                evidence=(
                    f"Payload: {payload}\n"
                    f"Técnica: {technique}\n"
                    f"Baseline: {baseline_time:.2f}s\n"
                    f"Round 1: {elapsed:.2f}s | Round 2: {elapsed2:.2f}s\n"
                    f"Delay esperado: {SLEEP_DELAY}s"
                ),
                payload_sent=payload,
                explanation="O servidor executou o comando sleep injetado, "
                            "confirmando injeção de comandos do sistema operacional.",
                remediation=(
                    "NUNCA passe entrada do usuário para shell/exec/system.\n"
                    "Use APIs da linguagem em vez de comandos shell.\n"
                    "Se inevitável, use allowlist estrita de caracteres permitidos."
                ),
                reference="https://owasp.org/www-community/attacks/Command_Injection",
                analyzer="command-injection",
                confidence=Confidence.CONFIRMED,
            )

        await asyncio.sleep(0.2)

    return None


def _inject_param(parsed, params, target_param, payload):
    new_params = {}
    for key, values in params.items():
        if key == target_param:
            new_params[key] = (values[0] if values else "") + payload
        else:
            new_params[key] = values[0] if values else ""
    new_query = urlencode(new_params)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path,
                       parsed.params, new_query, parsed.fragment))
