"""Analisador de cabeçalhos de segurança (S1-4)."""

from __future__ import annotations

from webguard.core.models import Confidence, Finding, ScanRecord, Severity
from webguard.core.registry import analyzer


@analyzer(mode="passive", name="security-headers")
async def analyze_headers(record: ScanRecord) -> list[Finding]:
    """Verifica os 10 cabeçalhos de segurança listados em S1-4."""
    findings: list[Finding] = []
    headers = {k.lower(): v for k, v in record.response_headers.items()}

    findings.extend(_check_csp(headers))
    findings.extend(_check_hsts(headers))
    findings.extend(_check_x_content_type_options(headers))
    findings.extend(_check_x_frame_options(headers))
    findings.extend(_check_referrer_policy(headers))
    findings.extend(_check_permissions_policy(headers))
    findings.extend(_check_coop(headers))
    findings.extend(_check_coep(headers))
    findings.extend(_check_corp(headers))
    findings.extend(_check_cache_control(headers))

    # Se nenhum problema encontrado, informativo
    if all(f.severity == Severity.INFO for f in findings):
        findings.append(Finding(
            id="HDR-ALL-PASS",
            category="headers",
            severity=Severity.INFO,
            title="Todos os cabeçalhos de segurança verificados estão presentes e corretos",
            evidence="CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, "
                     "Permissions-Policy, COOP, COEP, CORP verificados.",
            explanation="O site implementa os cabeçalhos de segurança recomendados.",
            remediation="Nenhuma ação necessária.",
            reference="https://owasp.org/www-project-secure-headers/",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    return findings


# --- CSP ---


def _check_csp(headers: dict[str, str]) -> list[Finding]:
    """Verifica Content-Security-Policy."""
    findings: list[Finding] = []
    csp = headers.get("content-security-policy")

    if not csp:
        findings.append(Finding(
            id="HDR-CSP-MISSING",
            category="headers",
            severity=Severity.MEDIUM,
            title="Content-Security-Policy ausente",
            evidence="O cabeçalho Content-Security-Policy não está presente na resposta.",
            explanation="Sem CSP, o navegador não restringe quais scripts podem executar, "
                        "tornando XSS mais fácil de explorar.",
            remediation="Adicione o cabeçalho:\n"
                        "Content-Security-Policy: default-src 'self'; script-src 'self'; "
                        "object-src 'none'; base-uri 'self'",
            reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))
        return findings

    # Parse CSP e avalia
    directives = _parse_csp(csp)

    # Verificar script-src
    script_src = directives.get("script-src", directives.get("default-src", ""))
    if "'unsafe-inline'" in script_src:
        findings.append(Finding(
            id="HDR-CSP-UNSAFE-INLINE",
            category="headers",
            severity=Severity.MEDIUM,
            title="CSP permite 'unsafe-inline' em script-src",
            evidence=f"Content-Security-Policy: ...script-src {script_src}...",
            explanation="'unsafe-inline' permite execução de scripts inline, anulando grande "
                        "parte da proteção contra XSS.",
            remediation="Remova 'unsafe-inline' de script-src e use nonces ou hashes:\n"
                        "script-src 'self' 'nonce-{random}'",
            reference="https://csp-evaluator.withgoogle.com/",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    if "'unsafe-eval'" in script_src:
        findings.append(Finding(
            id="HDR-CSP-UNSAFE-EVAL",
            category="headers",
            severity=Severity.MEDIUM,
            title="CSP permite 'unsafe-eval' em script-src",
            evidence=f"Content-Security-Policy: ...script-src {script_src}...",
            explanation="'unsafe-eval' permite eval(), Function() e similares, "
                        "ampliando a superfície de ataque para XSS.",
            remediation="Remova 'unsafe-eval' e refatore o código para não usar eval().",
            reference="https://csp-evaluator.withgoogle.com/",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    if "*" in script_src.split():
        findings.append(Finding(
            id="HDR-CSP-WILDCARD",
            category="headers",
            severity=Severity.HIGH,
            title="CSP contém wildcard (*) em script-src",
            evidence=f"Content-Security-Policy: ...script-src {script_src}...",
            explanation="Wildcard permite carregar scripts de qualquer origem, "
                        "tornando a CSP efetivamente inútil.",
            remediation="Substitua * pelas origens específicas necessárias.",
            reference="https://csp-evaluator.withgoogle.com/",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    # object-src deve ser 'none'
    object_src = directives.get("object-src", "")
    if not object_src or "'none'" not in object_src:
        findings.append(Finding(
            id="HDR-CSP-OBJECT-SRC",
            category="headers",
            severity=Severity.MEDIUM,
            title="CSP não restringe object-src a 'none'",
            evidence=f"object-src: {object_src or '(ausente)'}",
            explanation="Sem object-src 'none', plugins como Flash podem ser carregados, "
                        "permitindo bypass da CSP.",
            remediation="Adicione: object-src 'none'",
            reference="https://csp-evaluator.withgoogle.com/",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    # base-uri deve existir
    if "base-uri" not in directives:
        findings.append(Finding(
            id="HDR-CSP-BASE-URI",
            category="headers",
            severity=Severity.LOW,
            title="CSP não define base-uri",
            evidence="Diretiva base-uri ausente na CSP.",
            explanation="Sem base-uri, um atacante pode injetar <base> e redirecionar "
                        "URLs relativas para domínio malicioso.",
            remediation="Adicione: base-uri 'self'",
            reference="https://csp-evaluator.withgoogle.com/",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    return findings


def _parse_csp(csp: str) -> dict[str, str]:
    """Tokeniza CSP em diretiva → valores."""
    directives: dict[str, str] = {}
    for part in csp.split(";"):
        part = part.strip()
        if not part:
            continue
        tokens = part.split(None, 1)
        directive_name = tokens[0].lower()
        directive_value = tokens[1] if len(tokens) > 1 else ""
        directives[directive_name] = directive_value
    return directives


# --- HSTS ---


def _check_hsts(headers: dict[str, str]) -> list[Finding]:
    """Verifica Strict-Transport-Security."""
    findings: list[Finding] = []
    hsts = headers.get("strict-transport-security")

    if not hsts:
        findings.append(Finding(
            id="HDR-HSTS-MISSING",
            category="headers",
            severity=Severity.MEDIUM,
            title="Strict-Transport-Security ausente",
            evidence="O cabeçalho Strict-Transport-Security não está presente.",
            explanation="Sem HSTS, o navegador aceita conexões HTTP para o site, "
                        "permitindo ataques de downgrade (SSL stripping).",
            remediation="Adicione:\n"
                        "Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
            reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"
                      "/Strict-Transport-Security",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))
        return findings

    # Verificar max-age
    max_age = _extract_max_age(hsts)
    if max_age is not None and max_age < 31536000:
        findings.append(Finding(
            id="HDR-HSTS-SHORT",
            category="headers",
            severity=Severity.LOW,
            title="HSTS max-age abaixo do recomendado",
            evidence=f"Strict-Transport-Security: {hsts}",
            explanation=f"max-age={max_age} ({max_age // 86400} dias) é menor que "
                        "o recomendado de 1 ano (31536000).",
            remediation="Aumente max-age para 31536000 (1 ano):\n"
                        "Strict-Transport-Security: max-age=31536000; includeSubDomains",
            reference="https://hstspreload.org/",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    return findings


def _extract_max_age(hsts: str) -> int | None:
    """Extrai valor de max-age do HSTS."""
    for part in hsts.lower().split(";"):
        part = part.strip()
        if part.startswith("max-age="):
            try:
                return int(part.split("=", 1)[1].strip())
            except ValueError:
                return None
    return None


# --- X-Content-Type-Options ---


def _check_x_content_type_options(headers: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    value = headers.get("x-content-type-options")

    if not value:
        findings.append(Finding(
            id="HDR-XCTO-MISSING",
            category="headers",
            severity=Severity.LOW,
            title="X-Content-Type-Options ausente",
            evidence="O cabeçalho X-Content-Type-Options não está presente.",
            explanation="Sem este cabeçalho, o navegador pode interpretar respostas com "
                        "MIME type incorreto (MIME sniffing), potencialmente executando "
                        "conteúdo malicioso.",
            remediation="Adicione:\nX-Content-Type-Options: nosniff",
            reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"
                      "/X-Content-Type-Options",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))
    elif value.strip().lower() != "nosniff":
        findings.append(Finding(
            id="HDR-XCTO-INVALID",
            category="headers",
            severity=Severity.LOW,
            title="X-Content-Type-Options com valor inválido",
            evidence=f"X-Content-Type-Options: {value}",
            explanation="O único valor válido é 'nosniff'.",
            remediation="Corrija para:\nX-Content-Type-Options: nosniff",
            reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"
                      "/X-Content-Type-Options",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    return findings


# --- X-Frame-Options ---


def _check_x_frame_options(headers: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    value = headers.get("x-frame-options")

    if not value:
        findings.append(Finding(
            id="HDR-XFO-MISSING",
            category="headers",
            severity=Severity.MEDIUM,
            title="X-Frame-Options ausente",
            evidence="O cabeçalho X-Frame-Options não está presente.",
            explanation="Sem proteção contra framing, o site pode ser embutido em iframe "
                        "malicioso para ataques de clickjacking.",
            remediation="Adicione:\nX-Frame-Options: DENY\n\n"
                        "Ou use CSP frame-ancestors:\n"
                        "Content-Security-Policy: frame-ancestors 'none'",
            reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"
                      "/X-Frame-Options",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))
    elif value.strip().upper() not in ("DENY", "SAMEORIGIN"):
        findings.append(Finding(
            id="HDR-XFO-INVALID",
            category="headers",
            severity=Severity.MEDIUM,
            title="X-Frame-Options com valor não recomendado",
            evidence=f"X-Frame-Options: {value}",
            explanation="Valores válidos são DENY ou SAMEORIGIN. ALLOW-FROM é obsoleto.",
            remediation="Corrija para:\nX-Frame-Options: DENY",
            reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"
                      "/X-Frame-Options",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    return findings


# --- Referrer-Policy ---


def _check_referrer_policy(headers: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    value = headers.get("referrer-policy")

    SAFE_VALUES = {
        "no-referrer",
        "no-referrer-when-downgrade",
        "same-origin",
        "strict-origin",
        "strict-origin-when-cross-origin",
    }

    if not value:
        findings.append(Finding(
            id="HDR-RP-MISSING",
            category="headers",
            severity=Severity.LOW,
            title="Referrer-Policy ausente",
            evidence="O cabeçalho Referrer-Policy não está presente.",
            explanation="Sem Referrer-Policy, o navegador pode enviar a URL completa "
                        "(incluindo parâmetros sensíveis) como referrer para sites externos.",
            remediation="Adicione:\nReferrer-Policy: strict-origin-when-cross-origin",
            reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"
                      "/Referrer-Policy",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))
    elif value.strip().lower() == "unsafe-url":
        findings.append(Finding(
            id="HDR-RP-UNSAFE",
            category="headers",
            severity=Severity.MEDIUM,
            title="Referrer-Policy definida como 'unsafe-url'",
            evidence=f"Referrer-Policy: {value}",
            explanation="'unsafe-url' envia a URL completa em todas as requisições, "
                        "incluindo cross-origin.",
            remediation="Corrija para:\nReferrer-Policy: strict-origin-when-cross-origin",
            reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"
                      "/Referrer-Policy",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    return findings


# --- Permissions-Policy ---


def _check_permissions_policy(headers: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    value = headers.get("permissions-policy")

    if not value:
        findings.append(Finding(
            id="HDR-PP-MISSING",
            category="headers",
            severity=Severity.LOW,
            title="Permissions-Policy ausente",
            evidence="O cabeçalho Permissions-Policy não está presente.",
            explanation="Sem Permissions-Policy, o site permite que qualquer iframe "
                        "embutido acesse funcionalidades sensíveis (câmera, microfone, "
                        "geolocalização).",
            remediation="Adicione:\n"
                        "Permissions-Policy: camera=(), microphone=(), geolocation=()",
            reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"
                      "/Permissions-Policy",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    return findings


# --- COOP ---


def _check_coop(headers: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    value = headers.get("cross-origin-opener-policy")

    if not value:
        findings.append(Finding(
            id="HDR-COOP-MISSING",
            category="headers",
            severity=Severity.LOW,
            title="Cross-Origin-Opener-Policy ausente",
            evidence="O cabeçalho Cross-Origin-Opener-Policy não está presente.",
            explanation="Sem COOP, janelas abertas por links externos podem manter "
                        "referência ao window.opener, permitindo ataques de tab-nabbing.",
            remediation="Adicione:\nCross-Origin-Opener-Policy: same-origin",
            reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"
                      "/Cross-Origin-Opener-Policy",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    return findings


# --- COEP ---


def _check_coep(headers: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    value = headers.get("cross-origin-embedder-policy")

    if not value:
        findings.append(Finding(
            id="HDR-COEP-MISSING",
            category="headers",
            severity=Severity.LOW,
            title="Cross-Origin-Embedder-Policy ausente",
            evidence="O cabeçalho Cross-Origin-Embedder-Policy não está presente.",
            explanation="Sem COEP, o site não pode usar SharedArrayBuffer e outros "
                        "recursos que requerem isolamento cross-origin.",
            remediation="Adicione:\nCross-Origin-Embedder-Policy: require-corp",
            reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"
                      "/Cross-Origin-Embedder-Policy",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    return findings


# --- CORP ---


def _check_corp(headers: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    value = headers.get("cross-origin-resource-policy")

    if not value:
        findings.append(Finding(
            id="HDR-CORP-MISSING",
            category="headers",
            severity=Severity.LOW,
            title="Cross-Origin-Resource-Policy ausente",
            evidence="O cabeçalho Cross-Origin-Resource-Policy não está presente.",
            explanation="Sem CORP, recursos do site podem ser carregados por qualquer "
                        "origem, potencialmente permitindo exfiltração via side-channels.",
            remediation="Adicione:\nCross-Origin-Resource-Policy: same-origin",
            reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"
                      "/Cross-Origin-Resource-Policy",
            analyzer="security-headers",
            confidence=Confidence.CONFIRMED,
        ))

    return findings


# --- Cache-Control ---


def _check_cache_control(headers: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    value = headers.get("cache-control", "")

    # Só relevante se a resposta contém dados potencialmente sensíveis
    # Heurística: se tem Set-Cookie ou content-type com form/json
    content_type = headers.get("content-type", "")
    has_cookies = "set-cookie" in headers
    is_dynamic = "json" in content_type or "html" in content_type

    if (has_cookies or is_dynamic) and not value:
        findings.append(Finding(
            id="HDR-CC-MISSING",
            category="headers",
            severity=Severity.LOW,
            title="Cache-Control ausente em resposta dinâmica",
            evidence="Resposta com conteúdo dinâmico/cookies sem Cache-Control.",
            explanation="Respostas dinâmicas sem Cache-Control podem ser armazenadas "
                        "por proxies intermediários, expondo dados de outros usuários.",
            remediation="Adicione:\nCache-Control: no-store, no-cache, must-revalidate",
            reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"
                      "/Cache-Control",
            analyzer="security-headers",
            confidence=Confidence.LIKELY,
        ))

    return findings
