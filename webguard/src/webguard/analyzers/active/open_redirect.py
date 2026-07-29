"""Open Redirect — testa redirecionamento para domínio externo."""

from __future__ import annotations

import asyncio
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import httpx

from webguard.core.models import (
    Confidence, Finding, Mode, RateLimiter,
    ScanContext, ScanRecord, Severity,
)
from webguard.core.guard import RequestGuard
from webguard.core.registry import analyzer

# Nomes de parâmetros que tipicamente controlam redirect
REDIRECT_PARAMS = {
    "url", "redirect", "next", "return", "returnto",
    "goto", "link", "dest", "destination", "redir",
    "redirect_uri", "redirect_url", "return_url",
    "continue", "target", "rurl", "forward",
}

EVIL_DOMAIN = "https://evil.example.com"

REDIRECT_PAYLOADS = [
    "https://evil.example.com",
    "//evil.example.com",
    "https://evil.example.com%00",
    "https://target.com@evil.example.com",
    "/\\evil.example.com",
    "//evil.example.com/%2f..",
]


@analyzer(mode="active", name="open-redirect")
async def analyze_redirect(record: ScanRecord) -> list[Finding]:
    """Testa Open Redirect em parâmetros de URL."""
    findings: list[Finding] = []

    parsed = urlparse(record.target_url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    # Filtrar parâmetros que parecem ser de redirect
    redirect_candidates = {
        k: v for k, v in params.items()
        if k.lower() in REDIRECT_PARAMS
    }

    # Se não tem parâmetros com nome de redirect,
    # testar todos que tenham URL como valor
    if not redirect_candidates:
        for k, v in params.items():
            val = v[0] if v else ""
            if val.startswith(("http", "/", "//")) or "url" in k.lower():
                redirect_candidates[k] = v

    if not redirect_candidates:
        findings.append(Finding(
            id="REDIRECT-NO-PARAMS",
            category="redirect",
            severity=Severity.INFO,
            title="Nenhum parâmetro de redirecionamento detectado",
            evidence=f"Parâmetros: {', '.join(params.keys()) or 'nenhum'}",
            explanation="Nenhum parâmetro com nome ou valor sugestivo de redirect.",
            remediation="Informativo.",
            reference="https://cheatsheetseries.owasp.org/cheatsheets/"
                      "Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html",
            analyzer="open-redirect",
            confidence=Confidence.CONFIRMED,
        ))
        return findings

    ctx = ScanContext()
    rate_limiter = RateLimiter(mode=Mode.ACTIVE, requests_per_second=10)

    async with httpx.AsyncClient(
        verify=False, timeout=15.0, follow_redirects=False
    ) as client:
        guard = RequestGuard(
            mode=Mode.ACTIVE,
            target_url=record.target_url,
            rate_limiter=rate_limiter,
            ctx=ctx,
            client=client,
        )

        for param_name in redirect_candidates:
            finding = await _test_redirect(guard, parsed, params, param_name)
            if finding:
                findings.append(finding)

    if not any(f.severity in (Severity.MEDIUM, Severity.HIGH) for f in findings):
        findings.append(Finding(
            id="REDIRECT-NOT-FOUND",
            category="redirect",
            severity=Severity.INFO,
            title="Nenhum Open Redirect detectado",
            evidence=f"Parâmetros testados: {', '.join(redirect_candidates.keys())}",
            explanation="Nenhum payload causou redirect para domínio externo.",
            remediation="Informativo.",
            reference="https://cheatsheetseries.owasp.org/cheatsheets/"
                      "Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html",
            analyzer="open-redirect",
            confidence=Confidence.INDETERMINATE,
        ))

    return findings


async def _test_redirect(guard, parsed, params, param_name) -> Finding | None:
    for payload in REDIRECT_PAYLOADS:
        injected_url = _inject_param(parsed, params, param_name, payload)
        try:
            response = await guard.request(
                "GET", injected_url, timeout=10.0, follow_redirects=False
            )

            # Verificar redirect (3xx) para domínio externo
            if response.status_code in range(300, 400):
                location = response.headers.get("location", "")
                loc_parsed = urlparse(location)
                if loc_parsed.hostname and "evil.example" in loc_parsed.hostname:
                    return Finding(
                        id=f"REDIRECT-{param_name.upper()[:20]}",
                        category="redirect",
                        severity=Severity.MEDIUM,
                        title=f"Open Redirect no parâmetro '{param_name}'",
                        evidence=(
                            f"Payload: {payload}\n"
                            f"Status: {response.status_code}\n"
                            f"Location: {location}\n"
                            f"URL: {injected_url}"
                        ),
                        payload_sent=payload,
                        explanation="O servidor redireciona para um domínio externo "
                                    "controlado pelo atacante, permitindo phishing.",
                        remediation=(
                            "Valide a URL de destino contra uma allowlist.\n"
                            "Nunca redirecione para URLs absolutas vindas do usuário.\n"
                            "Use apenas paths relativos para redirects internos."
                        ),
                        reference="https://cheatsheetseries.owasp.org/cheatsheets/"
                                  "Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html",
                        analyzer="open-redirect",
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
