"""XSS Refletido — testa reflexão de input sem encoding."""

from __future__ import annotations

import asyncio
import random
import string
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import httpx

from webguard.core.models import (
    Confidence, Finding, Mode, RateLimiter, ScanContext, ScanRecord, Severity,
)
from webguard.core.guard import RequestGuard
from webguard.core.registry import analyzer


def _random_marker() -> str:
    """Gera marcador único para detectar reflexão."""
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"wg{rand}"


# Payloads progressivos (do mais simples ao mais complexo)
def _get_xss_payloads(marker: str) -> list[tuple[str, str]]:
    return [
        # Nível 1: marcador simples (detecta reflexão bruta)
        (f"<{marker}>", "tag HTML simples"),
        # Nível 2: script tag
        (f"<script>{marker}</script>", "script tag"),
        # Nível 3: event handler
        (f'"><img src=x onerror={marker}>', "img onerror"),
        # Nível 4: em atributo
        (f'" onmouseover="{marker}"', "atributo evento"),
        # Nível 5: tag SVG
        (f"<svg/onload={marker}>", "svg onload"),
        # Nível 6: variações de encoding
        (f"<ScRiPt>{marker}</ScRiPt>", "case mixing"),
        (f"<img src=x onerror=alert({marker})>", "img alert"),
    ]


@analyzer(mode="active", name="xss-reflected")
async def analyze_xss(record: ScanRecord) -> list[Finding]:
    """Testa XSS refletido nos parâmetros da URL."""
    findings: list[Finding] = []

    parsed = urlparse(record.target_url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    if not params:
        findings.append(Finding(
            id="XSS-NO-PARAMS",
            category="xss",
            severity=Severity.INFO,
            title="Nenhum parâmetro para testar XSS",
            evidence=f"URL: {record.target_url}",
            explanation="Sem parâmetros query string para injetar.",
            remediation="Teste endpoints com parâmetros manualmente.",
            reference="https://owasp.org/www-community/attacks/xss/",
            analyzer="xss-reflected",
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
            finding = await _test_param_xss(guard, parsed, params, param_name)
            if finding:
                findings.append(finding)

    if not any(f.severity in (Severity.CRITICAL, Severity.HIGH) for f in findings):
        findings.append(Finding(
            id="XSS-NOT-FOUND",
            category="xss",
            severity=Severity.INFO,
            title="Nenhum XSS refletido detectado",
            evidence=f"Parâmetros testados: {', '.join(params.keys())}",
            explanation="Nenhum payload foi refletido sem encoding.",
            remediation="Informativo.",
            reference="https://owasp.org/www-community/attacks/xss/",
            analyzer="xss-reflected",
            confidence=Confidence.INDETERMINATE,
        ))

    return findings


async def _test_param_xss(guard, parsed, params, param_name) -> Finding | None:
    """Testa XSS em um parâmetro específico."""
    marker = _random_marker()
    payloads = _get_xss_payloads(marker)

    for payload, technique in payloads:
        injected_url = _inject_param(parsed, params, param_name, payload)
        try:
            response = await guard.request("GET", injected_url, timeout=10.0)
            body = response.text

            # Verificar se o marcador aparece SEM encoding HTML
            if marker in body:
                # Verificar se está em contexto executável
                # Se a tag completa aparece, é reflexão sem sanitização
                if f"<{marker}>" in body or f"<script>{marker}" in body:
                    return Finding(
                        id=f"XSS-REFLECTED-{param_name.upper()[:20]}",
                        category="xss",
                        severity=Severity.HIGH,
                        title=f"XSS Refletido no parâmetro '{param_name}'",
                        evidence=(
                            f"Payload: {payload}\n"
                            f"Técnica: {technique}\n"
                            f"Marcador '{marker}' refletido sem encoding no HTML.\n"
                            f"URL: {injected_url}"
                        ),
                        payload_sent=payload,
                        explanation="O input é refletido no HTML sem encoding, "
                                    "permitindo execução de JavaScript arbitrário "
                                    "no navegador da vítima.",
                        remediation=(
                            "Encode toda saída com HTML entities:\n"
                            "  &lt; &gt; &amp; &quot; &#x27;\n\n"
                            "Use funções de template auto-escaping.\n"
                            "Adicione Content-Security-Policy para mitigação adicional."
                        ),
                        reference="https://owasp.org/www-community/attacks/xss/",
                        analyzer="xss-reflected",
                        confidence=Confidence.CONFIRMED,
                    )

                # Reflexão parcial (marcador aparece mas não a tag)
                if payload.replace(marker, "") not in body:
                    return Finding(
                        id=f"XSS-PARTIAL-{param_name.upper()[:20]}",
                        category="xss",
                        severity=Severity.MEDIUM,
                        title=f"Reflexão parcial no parâmetro '{param_name}'",
                        evidence=(
                            f"Payload: {payload}\n"
                            f"Marcador refletido, tags parcialmente filtradas.\n"
                            f"URL: {injected_url}"
                        ),
                        payload_sent=payload,
                        explanation="O input é parcialmente refletido. Pode ser "
                                    "possível bypassar o filtro com encoding alternativo.",
                        remediation="Use output encoding consistente, não blacklists.",
                        reference="https://owasp.org/www-community/attacks/xss/",
                        analyzer="xss-reflected",
                        confidence=Confidence.LIKELY,
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
