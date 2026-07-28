"""Analisador de cookies — verifica atributos de segurança."""

from __future__ import annotations

import re

from webguard.core.models import Confidence, Finding, ScanRecord, Severity
from webguard.core.registry import analyzer

SESSION_PATTERNS = re.compile(
    r"(sess|session|sid|token|auth|jwt|csrf|xsrf|login|credential|phpsessid|jsessionid|"
    r"asp\.net_sessionid|connect\.sid|laravel_session|_rails_session)",
    re.IGNORECASE,
)


@analyzer(mode="passive", name="cookies")
async def analyze_cookies(record: ScanRecord) -> list[Finding]:
    """Verifica atributos de segurança de todos os cookies."""
    findings: list[Finding] = []
    cookies = record.cookies
    is_https = record.final_url.startswith("https://")

    if not cookies:
        findings.append(Finding(
            id="COOKIE-NONE",
            category="cookies",
            severity=Severity.INFO,
            title="Nenhum cookie definido na resposta",
            evidence="O servidor não enviou cabeçalhos Set-Cookie.",
            explanation="Informativo — sem cookies não há risco de atributos ausentes.",
            remediation="Nenhuma ação necessária.",
            reference="",
            analyzer="cookies",
            confidence=Confidence.CONFIRMED,
        ))
        return findings

    info_lines: list[str] = []
    issues_found = False

    for cookie in cookies:
        is_session = bool(SESSION_PATTERNS.search(cookie.name))
        cookie_issues: list[str] = []

        # Secure
        if is_https and not cookie.secure:
            cookie_issues.append("Secure ausente")
            if is_session:
                findings.append(Finding(
                    id=f"COOKIE-NO-SECURE-{cookie.name[:30].upper()}",
                    category="cookies",
                    severity=Severity.HIGH,
                    title=f"Cookie de sessão '{cookie.name}' sem flag Secure",
                    evidence=f"Cookie: {cookie.name} | Secure: false | HTTPS: true",
                    explanation="Sem Secure, o cookie é enviado também em conexões HTTP, "
                                "permitindo interceptação por MITM.",
                    remediation=f"Adicione Secure ao cookie '{cookie.name}'.",
                    reference="https://owasp.org/www-community/controls/SecureCookieAttribute",
                    analyzer="cookies",
                    confidence=Confidence.CONFIRMED,
                ))
                issues_found = True

        # HttpOnly
        if is_session and not cookie.httponly:
            cookie_issues.append("HttpOnly ausente")
            findings.append(Finding(
                id=f"COOKIE-NO-HTTPONLY-{cookie.name[:30].upper()}",
                category="cookies",
                severity=Severity.HIGH,
                title=f"Cookie de sessão '{cookie.name}' sem flag HttpOnly",
                evidence=f"Cookie: {cookie.name} | HttpOnly: false",
                explanation="Sem HttpOnly, JavaScript pode acessar o cookie via "
                            "document.cookie, facilitando exfiltração por XSS.",
                remediation=f"Adicione HttpOnly ao cookie '{cookie.name}'.",
                reference="https://owasp.org/www-community/HttpOnly",
                analyzer="cookies",
                confidence=Confidence.CONFIRMED,
            ))
            issues_found = True

        # SameSite
        if not cookie.samesite or cookie.samesite.lower() == "none":
            if is_session:
                cookie_issues.append(f"SameSite={cookie.samesite or 'ausente'}")
                findings.append(Finding(
                    id=f"COOKIE-SAMESITE-{cookie.name[:30].upper()}",
                    category="cookies",
                    severity=Severity.MEDIUM,
                    title=f"Cookie '{cookie.name}' sem SameSite adequado",
                    evidence=f"Cookie: {cookie.name} | SameSite: {cookie.samesite or 'não definido'}",
                    explanation="Sem SameSite (ou com SameSite=None), o cookie é enviado "
                                "em requisições cross-site, facilitando CSRF.",
                    remediation=f"Defina SameSite=Lax ou SameSite=Strict para '{cookie.name}'.",
                    reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite",
                    analyzer="cookies",
                    confidence=Confidence.CONFIRMED,
                ))
                issues_found = True

        # Resumo
        flags = []
        if cookie.secure:
            flags.append("Secure")
        if cookie.httponly:
            flags.append("HttpOnly")
        if cookie.samesite:
            flags.append(f"SameSite={cookie.samesite}")
        session_tag = " [SESSÃO]" if is_session else ""
        problems = f" ⚠ {', '.join(cookie_issues)}" if cookie_issues else ""
        info_lines.append(f"  {cookie.name}{session_tag}: {' | '.join(flags) or 'sem flags'}{problems}")

    # Finding de resumo
    findings.append(Finding(
        id="COOKIE-SUMMARY",
        category="cookies",
        severity=Severity.INFO,
        title=f"Resumo de cookies ({len(cookies)} encontrados)",
        evidence="\n".join(info_lines),
        explanation="Lista de cookies com seus atributos de segurança.",
        remediation="Verifique se cookies de sessão têm Secure, HttpOnly e SameSite.",
        reference="https://owasp.org/www-project-web-security-testing-guide/",
        analyzer="cookies",
        confidence=Confidence.CONFIRMED,
    ))

    if not issues_found and cookies:
        findings.append(Finding(
            id="COOKIE-ALL-OK",
            category="cookies",
            severity=Severity.INFO,
            title="Todos os cookies com atributos de segurança adequados",
            evidence="Nenhum problema encontrado nos atributos dos cookies.",
            explanation="Os cookies estão configurados com as flags de segurança esperadas.",
            remediation="Nenhuma ação necessária.",
            reference="",
            analyzer="cookies",
            confidence=Confidence.CONFIRMED,
        ))

    return findings
