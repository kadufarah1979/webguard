"""Analisador de formulários e endpoints — mapeia superfície de interação."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from webguard.core.models import Confidence, Finding, ScanRecord, Severity
from webguard.core.registry import analyzer


@analyzer(mode="passive", name="forms-endpoints")
async def analyze_forms_endpoints(record: ScanRecord) -> list[Finding]:
    """Detecta formulários, APIs e endpoints referenciados no HTML/JS."""
    findings: list[Finding] = []
    body = record.response_body
    base_host = urlparse(record.final_url).hostname or ""

    # 1. Formulários
    forms = re.findall(
        r'<form[^>]*>(.*?)</form>',
        body, re.IGNORECASE | re.DOTALL
    )
    form_info: list[str] = []
    for i, form_match in enumerate(re.finditer(r'<form([^>]*)>', body, re.IGNORECASE)):
        attrs = form_match.group(1)
        action = re.search(r'action=["\']([^"\']*)', attrs, re.IGNORECASE)
        method = re.search(r'method=["\']([^"\']*)', attrs, re.IGNORECASE)
        action_val = action.group(1) if action else "(sem action)"
        method_val = (method.group(1) if method else "GET").upper()

        # Inputs do formulário
        form_end = body.find("</form>", form_match.end())
        form_body = body[form_match.start():form_end] if form_end > 0 else ""
        inputs = re.findall(r'<input[^>]*name=["\']([^"\']+)', form_body, re.IGNORECASE)
        input_types = re.findall(r'<input[^>]*type=["\']([^"\']+)', form_body, re.IGNORECASE)

        has_password = "password" in " ".join(input_types).lower()
        form_info.append(
            f"  [{method_val}] {action_val} — campos: {', '.join(inputs[:8])}"
            f"{' ⚠ SENHA' if has_password else ''}"
        )

        if i >= 10:
            form_info.append(f"  ... e mais {len(forms) - 10} formulários")
            break

    if form_info:
        findings.append(Finding(
            id="FORMS-DETECTED",
            category="forms",
            severity=Severity.INFO,
            title=f"Formulários detectados ({min(len(forms), len(form_info))})",
            evidence="\n".join(form_info),
            explanation="Formulários são pontos de entrada para interação com o backend. "
                        "Cada um é um potencial vetor para injeção, CSRF ou brute force.",
            remediation="Informativo — cada formulário será testado no modo ativo.",
            reference="",
            analyzer="forms-endpoints",
            confidence=Confidence.CONFIRMED,
        ))

        # Formulário de login
        login_forms = [f for f in form_info if "SENHA" in f]
        if login_forms:
            findings.append(Finding(
                id="FORMS-LOGIN",
                category="forms",
                severity=Severity.INFO,
                title="Formulário de login detectado",
                evidence="\n".join(login_forms),
                explanation="Formulário com campo de senha identificado. Verifique "
                            "proteção contra brute force (rate limit, CAPTCHA).",
                remediation="Garanta rate limiting, CAPTCHA após N tentativas, "
                            "e não revele se o usuário existe.",
                reference="https://owasp.org/www-project-web-security-testing-guide/",
                analyzer="forms-endpoints",
                confidence=Confidence.CONFIRMED,
            ))

    # 2. Endpoints de API no JavaScript
    api_patterns = [
        r'["\'](?:/api/[^\s"\'<>]+)',
        r'["\'](?:https?://[^\s"\'<>]*?/api/[^\s"\'<>]+)',
        r'fetch\(["\']([^\s"\'<>]+)',
        r'axios\.[a-z]+\(["\']([^\s"\'<>]+)',
        r'XMLHttpRequest.*?open\(["\'][A-Z]+["\']\s*,\s*["\']([^\s"\'<>]+)',
        r'\.ajax\(\{[^}]*url:\s*["\']([^\s"\'<>]+)',
    ]

    endpoints: set[str] = set()
    for pattern in api_patterns:
        for match in re.finditer(pattern, body, re.IGNORECASE):
            endpoint = match.group(1) if match.lastindex else match.group(0).strip("\"'")
            endpoint = endpoint.strip("\"'")
            if endpoint and len(endpoint) > 3 and not endpoint.endswith(('.js', '.css', '.png', '.jpg')):
                endpoints.add(endpoint)

    if endpoints:
        sorted_endpoints = sorted(endpoints)[:25]
        findings.append(Finding(
            id="FORMS-API-ENDPOINTS",
            category="forms",
            severity=Severity.INFO,
            title=f"Endpoints de API detectados ({len(endpoints)})",
            evidence="\n".join(f"  {e}" for e in sorted_endpoints),
            explanation="Endpoints de API encontrados no JavaScript. Cada um é "
                        "um ponto de interação testável para autenticação, "
                        "autorização e injeção.",
            remediation="Informativo — verifique autenticação e autorização em cada endpoint.",
            reference="",
            analyzer="forms-endpoints",
            confidence=Confidence.LIKELY,
        ))

    # 3. Recursos de terceiros (supply chain)
    external_scripts: set[str] = set()
    for match in re.finditer(r'<script[^>]+src=["\']([^"\']+)', body, re.IGNORECASE):
        src = match.group(1)
        parsed = urlparse(src)
        if parsed.hostname and parsed.hostname.lower() != base_host.lower():
            external_scripts.add(f"{parsed.hostname}{parsed.path}")

    if external_scripts:
        findings.append(Finding(
            id="FORMS-EXTERNAL-SCRIPTS",
            category="forms",
            severity=Severity.INFO,
            title=f"Scripts de terceiros carregados ({len(external_scripts)})",
            evidence="\n".join(f"  {s}" for s in sorted(external_scripts)[:15]),
            explanation="Scripts externos representam superfície de supply chain attack. "
                        "Se um CDN for comprometido, o site é afetado.",
            remediation="Use Subresource Integrity (SRI) para scripts externos:\n"
                        '<script src="..." integrity="sha384-..." crossorigin="anonymous">',
            reference="https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity",
            analyzer="forms-endpoints",
            confidence=Confidence.CONFIRMED,
        ))

    return findings
