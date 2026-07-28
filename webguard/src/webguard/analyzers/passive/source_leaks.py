"""Analisador de vazamentos no código-fonte — detecta informações sensíveis."""

from __future__ import annotations

import re

from webguard.core.models import Confidence, Finding, ScanRecord, Severity
from webguard.core.registry import analyzer


@analyzer(mode="passive", name="source-leaks")
async def analyze_source_leaks(record: ScanRecord) -> list[Finding]:
    """Detecta informações sensíveis vazadas no HTML e headers."""
    findings: list[Finding] = []
    body = record.response_body
    headers = {k.lower(): v for k, v in record.response_headers.items()}

    # 1. Source maps expostos
    sourcemap_patterns = [
        r'//[#@]\s*sourceMappingURL=([^\s]+)',
        r'/\*[#@]\s*sourceMappingURL=([^\s*]+)',
    ]
    sourcemaps: list[str] = []
    for pattern in sourcemap_patterns:
        sourcemaps.extend(re.findall(pattern, body))
    if "sourcemap" in headers or "x-sourcemap" in headers:
        sourcemaps.append(headers.get("sourcemap", headers.get("x-sourcemap", "")))

    if sourcemaps:
        findings.append(Finding(
            id="LEAK-SOURCEMAPS",
            category="leaks",
            severity=Severity.MEDIUM,
            title=f"Source maps expostos ({len(sourcemaps)})",
            evidence="\n".join(f"  {s}" for s in sourcemaps[:10]),
            explanation="Source maps permitem reconstruir o código-fonte original "
                        "(antes de minificação/bundling), expondo lógica de negócio, "
                        "caminhos internos e possíveis credenciais hardcoded.",
            remediation="Remova sourceMappingURL do código em produção ou restrinja "
                        "acesso aos .map files no servidor.",
            reference="https://developer.chrome.com/docs/devtools/javascript/source-maps/",
            analyzer="source-leaks",
            confidence=Confidence.CONFIRMED,
        ))

    # 2. Caminhos internos (filesystem paths)
    path_patterns = [
        r'(/(?:home|var|usr|opt|etc|tmp|Users|Windows|Program Files)[/\\][^\s<>"\']{5,})',
        r'([A-Z]:\\[^\s<>"\']{5,})',
        r'(/app/[^\s<>"\']{5,})',
    ]
    internal_paths: list[str] = []
    for pattern in path_patterns:
        matches = re.findall(pattern, body)
        internal_paths.extend(matches[:5])

    if internal_paths:
        findings.append(Finding(
            id="LEAK-INTERNAL-PATHS",
            category="leaks",
            severity=Severity.LOW,
            title=f"Caminhos internos do servidor expostos ({len(internal_paths)})",
            evidence="\n".join(f"  {p[:100]}" for p in internal_paths[:10]),
            explanation="Caminhos de filesystem internos revelam a estrutura do "
                        "servidor, facilitando path traversal e enumeração.",
            remediation="Remova paths absolutos do HTML. Configure o servidor para "
                        "não incluir paths em mensagens de erro.",
            reference="https://owasp.org/www-project-web-security-testing-guide/",
            analyzer="source-leaks",
            confidence=Confidence.CONFIRMED,
        ))

    # 3. IPs internos
    internal_ip_pattern = re.compile(
        r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
        r'172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|'
        r'192\.168\.\d{1,3}\.\d{1,3})\b'
    )
    internal_ips = list(set(internal_ip_pattern.findall(body)))
    # Verificar também nos headers
    for h_val in headers.values():
        internal_ips.extend(internal_ip_pattern.findall(h_val))
    internal_ips = list(set(internal_ips))

    if internal_ips:
        findings.append(Finding(
            id="LEAK-INTERNAL-IPS",
            category="leaks",
            severity=Severity.LOW,
            title=f"IPs internos expostos ({len(internal_ips)})",
            evidence="\n".join(f"  {ip}" for ip in internal_ips[:10]),
            explanation="IPs de rede interna (RFC 1918) expostos no HTML ou headers "
                        "revelam a topologia da rede interna.",
            remediation="Remova referências a IPs internos do código e configure "
                        "o proxy reverso para não propagar headers internos.",
            reference="https://owasp.org/www-project-web-security-testing-guide/",
            analyzer="source-leaks",
            confidence=Confidence.CONFIRMED,
        ))

    # 4. Stack traces e erros de debug
    debug_patterns = [
        (r'(?:Traceback \(most recent call last\)|File "[^"]+", line \d+)', "Python stack trace"),
        (r'(?:at [A-Za-z0-9_.$]+\.[A-Za-z0-9_.$]+\([^)]*\.java:\d+\))', "Java stack trace"),
        (r'(?:Fatal error|Warning|Notice):.*?in\s+/[^\s]+ on line \d+', "PHP error"),
        (r'(?:System\.(?:NullReferenceException|ArgumentException|InvalidOperationException))', ".NET exception"),
        (r'(?:SQLSTATE\[|mysql_|pg_|ORA-\d{5})', "Database error"),
        (r'(?:DEBUG|DEVELOPMENT|staging).*?(?:true|enabled|mode)', "Debug mode indicator"),
    ]

    debug_found: list[str] = []
    for pattern, name in debug_patterns:
        matches = re.findall(pattern, body, re.IGNORECASE)
        if matches:
            debug_found.append(f"  [{name}] {matches[0][:100]}")

    if debug_found:
        findings.append(Finding(
            id="LEAK-DEBUG-INFO",
            category="leaks",
            severity=Severity.HIGH,
            title=f"Informações de debug/erro expostas ({len(debug_found)})",
            evidence="\n".join(debug_found[:10]),
            explanation="Stack traces, mensagens de erro detalhadas ou indicadores de "
                        "modo debug expõem internals da aplicação: linguagem, framework, "
                        "paths, queries e estrutura de banco.",
            remediation="Desabilite modo debug em produção. Configure error handling "
                        "para retornar mensagens genéricas ao cliente.",
            reference="https://owasp.org/www-project-web-security-testing-guide/",
            analyzer="source-leaks",
            confidence=Confidence.CONFIRMED,
        ))

    # 5. Versões e metadados de desenvolvimento
    dev_meta: list[str] = []
    # Generator meta tag
    gen = re.search(r'<meta[^>]+generator[^>]+content=["\']([^"\']+)', body, re.IGNORECASE)
    if gen:
        dev_meta.append(f"  [Generator] {gen.group(1)}")

    # Powered-by comment
    powered = re.search(r'<!--.*?(powered by|built with|generated by)\s+([^-]+)', body, re.IGNORECASE)
    if powered:
        dev_meta.append(f"  [Built with] {powered.group(2).strip()[:80]}")

    if dev_meta:
        findings.append(Finding(
            id="LEAK-META-VERSION",
            category="leaks",
            severity=Severity.LOW,
            title="Metadados de versão/geração encontrados",
            evidence="\n".join(dev_meta),
            explanation="Meta tags de geração revelam CMS e versão exata, "
                        "permitindo busca direcionada de exploits.",
            remediation="Remova meta tags generator em produção.",
            reference="",
            analyzer="source-leaks",
            confidence=Confidence.CONFIRMED,
        ))

    return findings
