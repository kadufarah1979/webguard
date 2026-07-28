"""Analisador de emails e contatos expostos no site."""

from __future__ import annotations

import re

from webguard.core.models import Confidence, Finding, ScanRecord, Severity
from webguard.core.registry import analyzer

EMAIL_REGEX = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)

PHONE_REGEX = re.compile(
    r'(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}'
)


@analyzer(mode="passive", name="emails-contacts")
async def analyze_emails(record: ScanRecord) -> list[Finding]:
    """Detecta emails, telefones e contatos expostos no HTML."""
    findings: list[Finding] = []
    body = record.response_body

    # 1. Emails
    emails = list(set(EMAIL_REGEX.findall(body)))
    # Filtrar falsos positivos comuns
    emails = [e for e in emails if not e.endswith(('.png', '.jpg', '.gif', '.css', '.js', '.svg'))]
    emails = [e for e in emails if '@' in e and '.' in e.split('@')[1]]

    if emails:
        findings.append(Finding(
            id="CONTACT-EMAILS",
            category="information",
            severity=Severity.LOW,
            title=f"Emails expostos no site ({len(emails)})",
            evidence="\n".join(f"  {e}" for e in sorted(emails)[:20]),
            explanation="Emails visíveis no HTML podem ser coletados por spammers "
                        "e usados em ataques de phishing direcionado (spear phishing).",
            remediation="Considere usar formulários de contato em vez de expor emails "
                        "diretamente, ou ofusque com JavaScript.",
            reference="https://owasp.org/www-project-web-security-testing-guide/",
            analyzer="emails-contacts",
            confidence=Confidence.CONFIRMED,
        ))

    # 2. Links para redes sociais e perfis
    social_patterns = {
        "Twitter/X": r'(?:twitter\.com|x\.com)/([A-Za-z0-9_]+)',
        "LinkedIn": r'linkedin\.com/(?:in|company)/([A-Za-z0-9_-]+)',
        "GitHub": r'github\.com/([A-Za-z0-9_-]+)',
        "Facebook": r'facebook\.com/([A-Za-z0-9._-]+)',
        "Instagram": r'instagram\.com/([A-Za-z0-9._-]+)',
        "YouTube": r'youtube\.com/(?:c/|channel/|@)([A-Za-z0-9_-]+)',
    }

    social_found: list[str] = []
    for platform, pattern in social_patterns.items():
        matches = re.findall(pattern, body, re.IGNORECASE)
        for match in set(matches[:3]):
            social_found.append(f"  [{platform}] {match}")

    if social_found:
        findings.append(Finding(
            id="CONTACT-SOCIAL",
            category="information",
            severity=Severity.INFO,
            title=f"Perfis de redes sociais encontrados ({len(social_found)})",
            evidence="\n".join(social_found[:15]),
            explanation="Perfis sociais associados ao site. Úteis para reconhecimento "
                        "e engenharia social.",
            remediation="Informativo — verifique se os perfis listados são intencionais.",
            reference="",
            analyzer="emails-contacts",
            confidence=Confidence.CONFIRMED,
        ))

    # 3. Possíveis API keys ou tokens no HTML
    secrets_patterns = [
        (r'(?:api[_-]?key|apikey)["\s:=]+["\']?([A-Za-z0-9_\-]{20,})', "API Key"),
        (r'(?:secret|token)["\s:=]+["\']?([A-Za-z0-9_\-]{20,})', "Secret/Token"),
        (r'AKIA[A-Z0-9]{16}', "AWS Access Key"),
        (r'(?:sk_live|sk_test)_[A-Za-z0-9]{24,}', "Stripe Key"),
        (r'AIza[A-Za-z0-9_\-]{35}', "Google API Key"),
        (r'ghp_[A-Za-z0-9]{36}', "GitHub Token"),
    ]

    secrets_found: list[str] = []
    for pattern, name in secrets_patterns:
        matches = re.findall(pattern, body)
        for match in matches[:3]:
            # Mostrar apenas início e fim para não vazar
            if len(match) > 10:
                masked = f"{match[:4]}...{match[-4:]}"
            else:
                masked = match
            secrets_found.append(f"  [{name}] {masked}")

    if secrets_found:
        findings.append(Finding(
            id="CONTACT-SECRETS",
            category="information",
            severity=Severity.CRITICAL,
            title=f"Possíveis credenciais/tokens expostos no HTML ({len(secrets_found)})",
            evidence="\n".join(secrets_found),
            explanation="Tokens, API keys ou credenciais foram encontrados no código-fonte "
                        "HTML. Isso permite acesso não autorizado a serviços.",
            remediation="REMOVA IMEDIATAMENTE. Revogue as chaves comprometidas e "
                        "gere novas. Use variáveis de ambiente, não código-fonte.",
            reference="https://owasp.org/www-project-web-security-testing-guide/",
            analyzer="emails-contacts",
            confidence=Confidence.LIKELY,
        ))

    return findings
