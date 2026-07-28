"""Analisador de DNS e infraestrutura — resolve registros e identifica hosting."""

from __future__ import annotations

import socket
import subprocess
from urllib.parse import urlparse

from webguard.core.models import Confidence, Finding, ScanRecord, Severity
from webguard.core.registry import analyzer


@analyzer(mode="passive", name="dns-infrastructure")
async def analyze_dns(record: ScanRecord) -> list[Finding]:
    """Coleta informações DNS do alvo: IPs, MX, NS, TXT (SPF/DMARC/DKIM)."""
    findings: list[Finding] = []
    hostname = urlparse(record.final_url).hostname or ""

    if not hostname:
        return findings

    info_lines: list[str] = []

    # 1. Resolução A/AAAA
    try:
        ips = socket.getaddrinfo(hostname, None)
        unique_ips = sorted(set(addr[4][0] for addr in ips))
        info_lines.append(f"  [IPs] {', '.join(unique_ips)}")
    except Exception:
        unique_ips = []
        info_lines.append("  [IPs] Não foi possível resolver")

    # 2. Registros via dig/nslookup (se disponível)
    mx_records = _query_dns(hostname, "MX")
    ns_records = _query_dns(hostname, "NS")
    txt_records = _query_dns(hostname, "TXT")

    if mx_records:
        info_lines.append(f"  [MX] {', '.join(mx_records[:5])}")
    if ns_records:
        info_lines.append(f"  [NS] {', '.join(ns_records[:5])}")

    # 3. SPF/DMARC/DKIM
    spf = [t for t in txt_records if "v=spf1" in t.lower()]
    dmarc = _query_dns(f"_dmarc.{hostname}", "TXT")
    dmarc_records = [t for t in dmarc if "v=dmarc1" in t.lower()]

    if spf:
        info_lines.append(f"  [SPF] {spf[0][:100]}")
    else:
        info_lines.append("  [SPF] Não encontrado")

    if dmarc_records:
        info_lines.append(f"  [DMARC] {dmarc_records[0][:100]}")
    else:
        info_lines.append("  [DMARC] Não encontrado")

    # 4. Identificar hosting/CDN por IP ou NS
    hosting = _identify_hosting(unique_ips, ns_records)
    if hosting:
        info_lines.append(f"  [Hosting] {hosting}")

    # Finding principal: resumo DNS
    findings.append(Finding(
        id="DNS-INFO",
        category="dns",
        severity=Severity.INFO,
        title=f"Informações DNS de {hostname}",
        evidence="\n".join(info_lines),
        explanation="Registros DNS públicos do domínio. Revelam infraestrutura, "
                    "serviço de email e políticas de autenticação de email.",
        remediation="Informativo — verifique se SPF e DMARC estão configurados "
                    "para prevenir spoofing de email.",
        reference="https://mxtoolbox.com/",
        analyzer="dns-infrastructure",
        confidence=Confidence.CONFIRMED,
    ))

    # Alertas de segurança
    if not spf:
        findings.append(Finding(
            id="DNS-NO-SPF",
            category="dns",
            severity=Severity.MEDIUM,
            title="Registro SPF ausente",
            evidence=f"Nenhum registro TXT com 'v=spf1' encontrado para {hostname}",
            explanation="Sem SPF, qualquer servidor pode enviar emails fingindo ser "
                        "o domínio, facilitando phishing.",
            remediation=f'Adicione um registro TXT:\n{hostname}. IN TXT "v=spf1 include:_spf.google.com ~all"',
            reference="https://www.cloudflare.com/learning/dns/dns-records/dns-spf-record/",
            analyzer="dns-infrastructure",
            confidence=Confidence.CONFIRMED,
        ))

    if not dmarc_records:
        findings.append(Finding(
            id="DNS-NO-DMARC",
            category="dns",
            severity=Severity.MEDIUM,
            title="Registro DMARC ausente",
            evidence=f"Nenhum registro TXT com 'v=DMARC1' encontrado para _dmarc.{hostname}",
            explanation="Sem DMARC, não há política definida para emails que falham "
                        "SPF/DKIM, deixando o domínio vulnerável a spoofing.",
            remediation=f'Adicione:\n_dmarc.{hostname}. IN TXT "v=DMARC1; p=reject; rua=mailto:dmarc@{hostname}"',
            reference="https://dmarc.org/overview/",
            analyzer="dns-infrastructure",
            confidence=Confidence.CONFIRMED,
        ))

    return findings


def _query_dns(domain: str, record_type: str) -> list[str]:
    """Consulta DNS via dig (fallback: nslookup)."""
    try:
        result = subprocess.run(
            ["dig", "+short", domain, record_type],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return [line.strip().strip('"') for line in result.stdout.strip().split("\n") if line.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: nslookup
    try:
        result = subprocess.run(
            ["nslookup", f"-type={record_type}", domain],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.split("\n")
            records = []
            for line in lines:
                if "mail exchanger" in line.lower() or "nameserver" in line.lower() or "text" in line.lower():
                    parts = line.split("=")
                    if len(parts) > 1:
                        records.append(parts[-1].strip().strip('"'))
            return records
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return []


def _identify_hosting(ips: list[str], ns_records: list[str]) -> str:
    """Identifica provedor de hosting por IP ranges ou nameservers."""
    ns_text = " ".join(ns_records).lower()

    # Por nameservers
    if "awsdns" in ns_text:
        return "AWS (Route 53)"
    if "cloudflare" in ns_text:
        return "Cloudflare"
    if "google" in ns_text or "googledomains" in ns_text:
        return "Google Cloud"
    if "azure" in ns_text or "microsoft" in ns_text:
        return "Microsoft Azure"
    if "digitalocean" in ns_text:
        return "DigitalOcean"
    if "linode" in ns_text or "akamai" in ns_text:
        return "Akamai/Linode"
    if "hostgator" in ns_text:
        return "HostGator"
    if "godaddy" in ns_text or "domaincontrol" in ns_text:
        return "GoDaddy"
    if "registrar-servers" in ns_text or "namecheap" in ns_text:
        return "Namecheap"
    if "vercel" in ns_text:
        return "Vercel"
    if "netlify" in ns_text:
        return "Netlify"

    # Tentar reverse DNS no primeiro IP
    if ips:
        try:
            reverse = socket.gethostbyaddr(ips[0])
            rname = reverse[0].lower()
            if "amazonaws" in rname:
                return "AWS EC2"
            if "googleusercontent" in rname:
                return "Google Cloud"
            if "azure" in rname:
                return "Microsoft Azure"
            if "linode" in rname:
                return "Linode"
            if "digitalocean" in rname:
                return "DigitalOcean"
            if "vultr" in rname:
                return "Vultr"
            if "hetzner" in rname:
                return "Hetzner"
            if "ovh" in rname:
                return "OVH"
        except Exception:
            pass

    return ""
