"""Server-Side Template Injection (SSTI) — testa avaliação de expressões."""

from __future__ import annotations

import asyncio
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import httpx

from webguard.core.models import (
    Confidence, Finding, Mode, RateLimiter, ScanContext, ScanRecord, Severity,
)
from webguard.core.guard import RequestGuard
from webguard.core.registry import analyzer

# Pares de payload e resultado esperado
SSTI_PAYLOADS = [
    # Jinja2 / Twig / Django
    ("{{7*7}}", "49", "Jinja2/Twig"),
    ("{{7*'7'}}", "7777777", "Jinja2"),
    ("${7*7}", "49", "Freemarker/Mako"),
    ("<%= 7*7 %>", "49", "ERB (Ruby)"),
    ("#{7*7}", "49", "Ruby interpolation"),
    ("{{config}}", "Config", "Jinja2 config leak"),
    # Confirmação (segundo cálculo diferente)
    ("{{8*8}}", "64", "Confirmação Jinja2"),
    ("${8*8}", "64", "Confirmação Freemarker"),
]


@analyzer(mode="active", name="ssti")
async def analyze_ssti(record: ScanRecord) -> list[Finding]:
    """Testa Server-Side Template Injection."""
    findings: list[Finding] = []

    parsed = urlparse(record.target_url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    if not params:
        findings.append(Finding(
            id="SSTI-NO-PARAMS",
            category="ssti",
            severity=Severity.INFO,
            title="Nenhum parâmetro para testar SSTI",
            evidence=f"URL: {record.target_url}",
            explanation="Sem parâmetros para injetar expressões de template.",
            remediation="Teste endpoints com parâmetros manualmente.",
            reference="https://owasp.org/www-project-web-security-testing-guide/",
            analyzer="ssti",
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
            finding = await _test_param_ssti(guard, parsed, params, param_name)
            if finding:
                findings.append(finding)

    if not any(f.severity in (Severity.CRITICAL, Severity.HIGH) for f in findings):
        findings.append(Finding(
            id="SSTI-NOT-FOUND",
            category="ssti",
            severity=Severity.INFO,
            title="Nenhuma Template Injection detectada",
            evidence=f"Parâmetros testados: {', '.join(params.keys())}",
            explanation="Nenhuma expressão matemática foi avaliada pelo servidor.",
            remediation="Informativo.",
            reference="https://portswigger.net/research/server-side-template-injection",
            analyzer="ssti",
            confidence=Confidence.INDETERMINATE,
        ))

    return findings


async def _test_param_ssti(guard, parsed, params, param_name) -> Finding | None:
    for payload, expected, engine in SSTI_PAYLOADS[:6]:
        injected_url = _inject_param(parsed, params, param_name, payload)
        try:
            response = await guard.request("GET", injected_url, timeout=10.0)
            body = response.text

            if expected in body and payload not in body:
                # O resultado aparece mas não o payload literal — foi avaliado!
                # Tentar confirmar com segundo cálculo
                confirm_payload = "{{8*8}}" if "{{" in payload else "${8*8}"
                confirm_url = _inject_param(parsed, params, param_name, confirm_payload)
                try:
                    confirm_resp = await guard.request("GET", confirm_url, timeout=10.0)
                    confirmed = "64" in confirm_resp.text and confirm_payload not in confirm_resp.text
                except Exception:
                    confirmed = False

                severity = Severity.CRITICAL if confirmed else Severity.HIGH
                confidence = Confidence.CONFIRMED if confirmed else Confidence.LIKELY

                return Finding(
                    id=f"SSTI-{param_name.upper()[:20]}",
                    category="ssti",
                    severity=severity,
                    title=f"Template Injection ({engine}) no parâmetro '{param_name}'",
                    evidence=(
                        f"Payload: {payload} → resultado: {expected}\n"
                        f"Engine provável: {engine}\n"
                        f"Confirmação (8*8=64): {'SIM' if confirmed else 'não tentado/falhou'}\n"
                        f"URL: {injected_url}"
                    ),
                    payload_sent=payload,
                    explanation=f"O servidor avaliou a expressão matemática do template "
                                f"({payload} → {expected}), confirmando que a entrada é "
                                "processada como código de template. Isso pode levar a "
                                "execução remota de código (RCE).",
                    remediation=(
                        "NUNCA passe entrada do usuário como template.\n"
                        "Use templates pré-compilados com variáveis separadas.\n"
                        "Sandbox o engine de template se possível."
                    ),
                    reference="https://portswigger.net/research/server-side-template-injection",
                    analyzer="ssti",
                    confidence=confidence,
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
