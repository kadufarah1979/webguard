"""Analisador de TLS/Certificado — verifica validade, versões, algoritmo."""

from __future__ import annotations

import ssl
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse

from webguard.core.models import Confidence, Finding, ScanRecord, Severity
from webguard.core.registry import analyzer


@analyzer(mode="passive", name="tls-certificate")
async def analyze_tls(record: ScanRecord) -> list[Finding]:
    """Verifica certificado TLS e versões de protocolo aceitas."""
    findings: list[Finding] = []
    parsed = urlparse(record.final_url)
    hostname = parsed.hostname or ""
    port = parsed.port or 443

    if parsed.scheme != "https" or not hostname:
        findings.append(Finding(
            id="TLS-NOT-HTTPS",
            category="tls",
            severity=Severity.HIGH,
            title="Site não usa HTTPS",
            evidence=f"URL final: {record.final_url}",
            explanation="Sem HTTPS, todo o tráfego é transmitido em texto claro, "
                        "permitindo interceptação de dados, credenciais e sessões.",
            remediation="Configure HTTPS com certificado válido (Let's Encrypt é gratuito).",
            reference="https://letsencrypt.org/",
            analyzer="tls-certificate",
            confidence=Confidence.CONFIRMED,
        ))
        return findings

    # Obter certificado
    cert_info = _get_certificate(hostname, port)
    if not cert_info:
        findings.append(Finding(
            id="TLS-CERT-ERROR",
            category="tls",
            severity=Severity.INDETERMINATE,
            title="Não foi possível obter o certificado",
            evidence=f"Falha ao conectar em {hostname}:{port} para extrair cert.",
            explanation="Pode indicar problema de rede ou configuração TLS inválida.",
            remediation="Verifique se o servidor aceita conexões TLS na porta correta.",
            reference="",
            analyzer="tls-certificate",
            confidence=Confidence.INDETERMINATE,
        ))
        return findings

    cert, protocol_version, cipher = cert_info
    info_lines: list[str] = []

    # Sujeito e emissor
    subject = dict(x[0] for x in cert.get("subject", []))
    issuer = dict(x[0] for x in cert.get("issuer", []))
    cn = subject.get("commonName", "N/A")
    issuer_org = issuer.get("organizationName", issuer.get("commonName", "N/A"))
    info_lines.append(f"  [CN] {cn}")
    info_lines.append(f"  [Emissor] {issuer_org}")

    # SANs
    sans = []
    for entry_type, value in cert.get("subjectAltName", []):
        if entry_type == "DNS":
            sans.append(value)
    if sans:
        info_lines.append(f"  [SANs] {', '.join(sans[:10])}")
        if len(sans) > 10:
            info_lines.append(f"         ... e mais {len(sans) - 10}")

    # Validade
    not_before = cert.get("notBefore", "")
    not_after = cert.get("notAfter", "")
    info_lines.append(f"  [Válido de] {not_before}")
    info_lines.append(f"  [Válido até] {not_after}")

    # Protocolo e cipher
    info_lines.append(f"  [Protocolo] {protocol_version}")
    info_lines.append(f"  [Cipher] {cipher}")

    # Serial
    serial = cert.get("serialNumber", "N/A")
    info_lines.append(f"  [Serial] {serial}")

    # Finding informativo
    findings.append(Finding(
        id="TLS-CERT-INFO",
        category="tls",
        severity=Severity.INFO,
        title=f"Certificado TLS — {issuer_org}",
        evidence="\n".join(info_lines),
        explanation="Informações do certificado TLS do servidor.",
        remediation="Informativo — verifique a validade e os SANs.",
        reference="https://www.ssllabs.com/ssltest/",
        analyzer="tls-certificate",
        confidence=Confidence.CONFIRMED,
    ))

    # Verificar expiração
    if not_after:
        try:
            exp_date = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            exp_date = exp_date.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            days_left = (exp_date - now).days

            if days_left < 0:
                findings.append(Finding(
                    id="TLS-CERT-EXPIRED",
                    category="tls",
                    severity=Severity.CRITICAL,
                    title=f"Certificado EXPIRADO há {abs(days_left)} dias",
                    evidence=f"Expirou em: {not_after}",
                    explanation="Certificado expirado causa erros de navegador e "
                                "indica abandono ou falha na automação de renovação.",
                    remediation="Renove o certificado imediatamente.",
                    reference="https://letsencrypt.org/",
                    analyzer="tls-certificate",
                    confidence=Confidence.CONFIRMED,
                ))
            elif days_left < 30:
                findings.append(Finding(
                    id="TLS-CERT-EXPIRING",
                    category="tls",
                    severity=Severity.MEDIUM,
                    title=f"Certificado expira em {days_left} dias",
                    evidence=f"Expira em: {not_after} ({days_left} dias restantes)",
                    explanation="Certificado próximo da expiração. Se a renovação "
                                "automática falhar, o site ficará inacessível.",
                    remediation="Verifique a automação de renovação (certbot, etc.).",
                    reference="https://letsencrypt.org/docs/",
                    analyzer="tls-certificate",
                    confidence=Confidence.CONFIRMED,
                ))
        except Exception:
            pass

    # Verificar hostname no SAN
    if sans and hostname not in sans and not any(
        _matches_wildcard(hostname, san) for san in sans
    ):
        findings.append(Finding(
            id="TLS-CERT-MISMATCH",
            category="tls",
            severity=Severity.HIGH,
            title="Hostname não está nos SANs do certificado",
            evidence=f"Hostname: {hostname}\nSANs: {', '.join(sans[:5])}",
            explanation="O certificado não cobre este hostname, causando "
                        "warnings de navegador e possível MITM.",
            remediation="Emita um certificado que inclua o hostname correto.",
            reference="https://www.ssllabs.com/ssltest/",
            analyzer="tls-certificate",
            confidence=Confidence.CONFIRMED,
        ))

    # Verificar versões TLS inseguras
    tls_versions = _check_tls_versions(hostname, port)
    if tls_versions:
        insecure = [v for v in tls_versions if v in ("TLSv1", "TLSv1.0", "TLSv1.1")]
        if insecure:
            findings.append(Finding(
                id="TLS-INSECURE-VERSION",
                category="tls",
                severity=Severity.HIGH,
                title=f"Versões TLS inseguras aceitas: {', '.join(insecure)}",
                evidence=f"Versões aceitas: {', '.join(tls_versions)}",
                explanation="TLS 1.0 e 1.1 têm vulnerabilidades conhecidas (BEAST, POODLE) "
                            "e são considerados obsoletos.",
                remediation="Desabilite TLS 1.0 e 1.1. Use apenas TLS 1.2+.",
                reference="https://www.ssllabs.com/ssltest/",
                analyzer="tls-certificate",
                confidence=Confidence.CONFIRMED,
            ))

    return findings


def _get_certificate(hostname: str, port: int) -> tuple[dict, str, str] | None:
    """Conecta e extrai informações do certificado."""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                protocol = ssock.version() or "unknown"
                cipher_info = ssock.cipher()
                cipher_name = cipher_info[0] if cipher_info else "unknown"
                return cert, protocol, cipher_name
    except Exception:
        return None


def _matches_wildcard(hostname: str, pattern: str) -> bool:
    """Verifica se hostname casa com wildcard (*.example.com)."""
    if pattern.startswith("*."):
        suffix = pattern[2:]
        parts = hostname.split(".", 1)
        return len(parts) == 2 and parts[1] == suffix
    return hostname == pattern


def _check_tls_versions(hostname: str, port: int) -> list[str]:
    """Testa quais versões TLS são aceitas."""
    accepted: list[str] = []
    versions_to_test = [
        (ssl.TLSVersion.TLSv1, "TLSv1.0"),
        (ssl.TLSVersion.TLSv1_1, "TLSv1.1"),
        (ssl.TLSVersion.TLSv1_2, "TLSv1.2"),
    ]

    for version, name in versions_to_test:
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.minimum_version = version
            ctx.maximum_version = version
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname):
                    accepted.append(name)
        except Exception:
            pass

    # TLS 1.3
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        ctx.maximum_version = ssl.TLSVersion.TLSv1_3
        with socket.create_connection((hostname, port), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname):
                accepted.append("TLSv1.3")
    except Exception:
        pass

    return accepted
