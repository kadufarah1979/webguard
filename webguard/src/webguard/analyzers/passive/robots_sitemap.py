"""Analisador de robots.txt e sitemap — revela caminhos ocultos e estrutura."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from webguard.core.models import Confidence, Finding, ScanRecord, Severity
from webguard.core.registry import analyzer

SENSITIVE_PATHS = re.compile(
    r"(admin|login|dashboard|panel|config|backup|api|internal|private|secret|"
    r"wp-admin|phpmyadmin|cpanel|\.git|\.env|debug|staging|dev)",
    re.IGNORECASE,
)


@analyzer(mode="passive", name="robots-sitemap")
async def analyze_robots_sitemap(record: ScanRecord) -> list[Finding]:
    """Analisa robots.txt e sitemap para revelar estrutura e caminhos ocultos."""
    findings: list[Finding] = []
    body = record.response_body
    headers = {k.lower(): v for k, v in record.response_headers.items()}

    # Extrair robots.txt hints do HTML (link)
    # Na prática o collector já buscou robots.txt — vamos analisar se veio
    # Por agora, analisamos o que está visível: links internos e sitemap ref

    # 1. Links internos encontrados no HTML
    internal_paths = _extract_internal_paths(body, record.final_url)
    if internal_paths:
        sensitive = [p for p in internal_paths if SENSITIVE_PATHS.search(p)]
        info_lines = [f"  Total de caminhos internos: {len(internal_paths)}"]
        info_lines.append(f"  Exemplos: {', '.join(internal_paths[:15])}")

        findings.append(Finding(
            id="PATHS-INTERNAL",
            category="structure",
            severity=Severity.INFO,
            title=f"Estrutura de URLs internas ({len(internal_paths)} caminhos)",
            evidence="\n".join(info_lines),
            explanation="Caminhos internos extraídos dos links no HTML. Revelam a "
                        "estrutura do site e possíveis áreas de interesse.",
            remediation="Informativo — verifique se caminhos sensíveis não estão expostos.",
            reference="",
            analyzer="robots-sitemap",
            confidence=Confidence.CONFIRMED,
        ))

        if sensitive:
            findings.append(Finding(
                id="PATHS-SENSITIVE",
                category="structure",
                severity=Severity.MEDIUM,
                title=f"Caminhos potencialmente sensíveis encontrados ({len(sensitive)})",
                evidence=f"Caminhos: {', '.join(sensitive[:20])}",
                explanation="Estes caminhos podem indicar painéis admin, APIs internas, "
                            "ou diretórios que não deveriam ser publicamente linkados.",
                remediation="Verifique se estes caminhos exigem autenticação e não "
                            "estão indexados por engines de busca.",
                reference="https://owasp.org/www-project-web-security-testing-guide/",
                analyzer="robots-sitemap",
                confidence=Confidence.LIKELY,
            ))

    # 2. Detectar referências a sitemap
    sitemap_refs = re.findall(r'(https?://[^\s<>"]+sitemap[^\s<>"]*\.xml)', body, re.IGNORECASE)
    if sitemap_refs:
        findings.append(Finding(
            id="PATHS-SITEMAP",
            category="structure",
            severity=Severity.INFO,
            title=f"Referências a sitemap encontradas ({len(sitemap_refs)})",
            evidence="\n".join(f"  {s}" for s in sitemap_refs[:10]),
            explanation="Sitemaps revelam a estrutura completa do site, útil para "
                        "mapear superfície de ataque.",
            remediation="Informativo — sitemaps são normais. Verifique se não listam "
                        "páginas que deveriam ser privadas.",
            reference="https://www.sitemaps.org/",
            analyzer="robots-sitemap",
            confidence=Confidence.CONFIRMED,
        ))

    # 3. Comentários HTML reveladores
    comments = re.findall(r'<!--(.*?)-->', body, re.DOTALL)
    interesting_comments = []
    for c in comments[:50]:  # Limitar
        c_stripped = c.strip()
        if len(c_stripped) > 10 and any(kw in c_stripped.lower() for kw in [
            "todo", "fixme", "hack", "bug", "password", "secret", "key",
            "api", "token", "debug", "temp", "remove", "deprecated"
        ]):
            interesting_comments.append(c_stripped[:150])

    if interesting_comments:
        findings.append(Finding(
            id="PATHS-COMMENTS",
            category="structure",
            severity=Severity.LOW,
            title=f"Comentários HTML reveladores ({len(interesting_comments)})",
            evidence="\n".join(f"  <!-- {c} -->" for c in interesting_comments[:10]),
            explanation="Comentários no HTML podem vazar informações sobre a "
                        "implementação, TODOs, credenciais ou endpoints internos.",
            remediation="Remova comentários de desenvolvimento do HTML em produção.",
            reference="https://owasp.org/www-project-web-security-testing-guide/",
            analyzer="robots-sitemap",
            confidence=Confidence.CONFIRMED,
        ))

    return findings


def _extract_internal_paths(html: str, base_url: str) -> list[str]:
    """Extrai caminhos internos únicos dos links no HTML."""
    parsed_base = urlparse(base_url)
    base_host = parsed_base.hostname or ""

    paths: set[str] = set()
    # href e src
    for match in re.finditer(r'(?:href|src|action)=["\']([^"\']+)["\']', html, re.IGNORECASE):
        url = match.group(1)
        parsed = urlparse(url)

        # Caminho relativo
        if not parsed.scheme and not parsed.netloc:
            path = parsed.path
            if path and path != "/" and not path.startswith(("#", "javascript:", "mailto:", "tel:")):
                paths.add(path)
        # Mesmo host
        elif parsed.hostname and parsed.hostname.lower() == base_host.lower():
            if parsed.path and parsed.path != "/":
                paths.add(parsed.path)

    return sorted(paths)[:100]
