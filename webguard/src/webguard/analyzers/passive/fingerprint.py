"""Analisador de fingerprinting — detecta tecnologias, linguagem, framework, servidor."""

from __future__ import annotations

import re

from webguard.core.models import Confidence, Finding, ScanRecord, Severity
from webguard.core.registry import analyzer


# Padrões de detecção organizados por categoria
HEADER_SIGNATURES: list[dict[str, str]] = [
    # Servidores web
    {"header": "server", "pattern": r"nginx", "tech": "Nginx", "category": "Servidor Web"},
    {"header": "server", "pattern": r"apache", "tech": "Apache", "category": "Servidor Web"},
    {"header": "server", "pattern": r"cloudflare", "tech": "Cloudflare", "category": "CDN/Proxy"},
    {"header": "server", "pattern": r"Microsoft-IIS", "tech": "IIS", "category": "Servidor Web"},
    {"header": "server", "pattern": r"LiteSpeed", "tech": "LiteSpeed", "category": "Servidor Web"},
    {"header": "server", "pattern": r"openresty", "tech": "OpenResty", "category": "Servidor Web"},
    {"header": "server", "pattern": r"gunicorn", "tech": "Gunicorn (Python)", "category": "Servidor Web"},
    {"header": "server", "pattern": r"Kestrel", "tech": "Kestrel (.NET)", "category": "Servidor Web"},
    {"header": "server", "pattern": r"Cowboy", "tech": "Cowboy (Erlang/Elixir)", "category": "Servidor Web"},
    # Linguagens/Frameworks via X-Powered-By
    {"header": "x-powered-by", "pattern": r"PHP/?([\d.]*)", "tech": "PHP", "category": "Linguagem"},
    {"header": "x-powered-by", "pattern": r"ASP\.NET", "tech": "ASP.NET", "category": "Framework"},
    {"header": "x-powered-by", "pattern": r"Express", "tech": "Express.js (Node.js)", "category": "Framework"},
    {"header": "x-powered-by", "pattern": r"Next\.js", "tech": "Next.js", "category": "Framework"},
    {"header": "x-powered-by", "pattern": r"Phusion Passenger", "tech": "Passenger (Ruby)", "category": "Servidor Web"},
    {"header": "x-powered-by", "pattern": r"Servlet", "tech": "Java Servlet", "category": "Framework"},
    # Frameworks via headers específicos
    {"header": "x-aspnet-version", "pattern": r".*", "tech": "ASP.NET", "category": "Framework"},
    {"header": "x-aspnetmvc-version", "pattern": r".*", "tech": "ASP.NET MVC", "category": "Framework"},
    {"header": "x-drupal-cache", "pattern": r".*", "tech": "Drupal", "category": "CMS"},
    {"header": "x-generator", "pattern": r"Drupal", "tech": "Drupal", "category": "CMS"},
    {"header": "x-generator", "pattern": r"WordPress", "tech": "WordPress", "category": "CMS"},
    {"header": "x-powered-cms", "pattern": r".*", "tech": "CMS detectado", "category": "CMS"},
    {"header": "x-turbo-charged-by", "pattern": r"LiteSpeed", "tech": "LiteSpeed Cache", "category": "Cache"},
    {"header": "x-varnish", "pattern": r".*", "tech": "Varnish Cache", "category": "Cache"},
    {"header": "x-cache", "pattern": r".*", "tech": "Cache Layer", "category": "Cache"},
    {"header": "cf-ray", "pattern": r".*", "tech": "Cloudflare", "category": "CDN/Proxy"},
    {"header": "x-amz-cf-id", "pattern": r".*", "tech": "AWS CloudFront", "category": "CDN/Proxy"},
    {"header": "x-vercel-id", "pattern": r".*", "tech": "Vercel", "category": "Hosting"},
    {"header": "x-netlify-request-id", "pattern": r".*", "tech": "Netlify", "category": "Hosting"},
    {"header": "x-github-request-id", "pattern": r".*", "tech": "GitHub Pages", "category": "Hosting"},
    {"header": "x-heroku-request-id", "pattern": r".*", "tech": "Heroku", "category": "Hosting"},
    {"header": "x-railway-request-id", "pattern": r".*", "tech": "Railway", "category": "Hosting"},
]

HTML_SIGNATURES: list[dict[str, str]] = [
    # Meta generators
    {"pattern": r'<meta[^>]+generator[^>]+WordPress\s*([\d.]*)', "tech": "WordPress", "category": "CMS"},
    {"pattern": r'<meta[^>]+generator[^>]+Joomla', "tech": "Joomla", "category": "CMS"},
    {"pattern": r'<meta[^>]+generator[^>]+Drupal', "tech": "Drupal", "category": "CMS"},
    {"pattern": r'<meta[^>]+generator[^>]+Wix\.com', "tech": "Wix", "category": "CMS/Builder"},
    {"pattern": r'<meta[^>]+generator[^>]+Shopify', "tech": "Shopify", "category": "E-commerce"},
    {"pattern": r'<meta[^>]+generator[^>]+Hugo', "tech": "Hugo", "category": "Static Site Generator"},
    {"pattern": r'<meta[^>]+generator[^>]+Jekyll', "tech": "Jekyll", "category": "Static Site Generator"},
    {"pattern": r'<meta[^>]+generator[^>]+Gatsby', "tech": "Gatsby", "category": "Static Site Generator"},
    # Frameworks JavaScript
    {"pattern": r'<div id="__next"', "tech": "Next.js (React)", "category": "Framework JS"},
    {"pattern": r'<div id="__nuxt"', "tech": "Nuxt.js (Vue)", "category": "Framework JS"},
    {"pattern": r'<div id="app"[^>]*>.*?</div>\s*<script', "tech": "Vue.js (provável)", "category": "Framework JS"},
    {"pattern": r'_next/static', "tech": "Next.js", "category": "Framework JS"},
    {"pattern": r'__NEXT_DATA__', "tech": "Next.js", "category": "Framework JS"},
    {"pattern": r'__NUXT__', "tech": "Nuxt.js", "category": "Framework JS"},
    {"pattern": r'ng-version="', "tech": "Angular", "category": "Framework JS"},
    {"pattern": r'ng-app[="\s]', "tech": "AngularJS (legacy)", "category": "Framework JS"},
    {"pattern": r'data-reactroot', "tech": "React", "category": "Framework JS"},
    {"pattern": r'data-svelte', "tech": "Svelte", "category": "Framework JS"},
    {"pattern": r'ember-view', "tech": "Ember.js", "category": "Framework JS"},
    {"pattern": r'<script[^>]+gatsby', "tech": "Gatsby", "category": "Framework JS"},
    # Bibliotecas JS
    {"pattern": r'jquery[.-]?([\d.]+)\.(?:min\.)?js', "tech": "jQuery", "category": "Biblioteca JS"},
    {"pattern": r'bootstrap[.-]?([\d.]+)\.(?:min\.)?(?:js|css)', "tech": "Bootstrap", "category": "Framework CSS"},
    {"pattern": r'tailwindcss|tailwind\.', "tech": "Tailwind CSS", "category": "Framework CSS"},
    {"pattern": r'font-awesome|fontawesome', "tech": "Font Awesome", "category": "Biblioteca CSS"},
    {"pattern": r'googleapis\.com/ajax/libs/', "tech": "Google CDN", "category": "CDN"},
    {"pattern": r'cdnjs\.cloudflare\.com', "tech": "cdnjs", "category": "CDN"},
    {"pattern": r'unpkg\.com', "tech": "unpkg", "category": "CDN"},
    # Backend hints no HTML
    {"pattern": r'wp-content|wp-includes', "tech": "WordPress", "category": "CMS"},
    {"pattern": r'sites/default/files|drupal\.js', "tech": "Drupal", "category": "CMS"},
    {"pattern": r'/joomla|com_content', "tech": "Joomla", "category": "CMS"},
    {"pattern": r'laravel_session|csrf-token.*content="[A-Za-z0-9+/=]{40}"', "tech": "Laravel (PHP)", "category": "Framework"},
    {"pattern": r'csrfmiddlewaretoken|__django', "tech": "Django (Python)", "category": "Framework"},
    {"pattern": r'_rails|csrf-token.*authenticity_token', "tech": "Ruby on Rails", "category": "Framework"},
    {"pattern": r'__RequestVerificationToken', "tech": "ASP.NET", "category": "Framework"},
    {"pattern": r'blazor\.webassembly|_blazor', "tech": "Blazor (.NET)", "category": "Framework"},
    # Analytics e serviços
    {"pattern": r'google-analytics\.com|gtag\(', "tech": "Google Analytics", "category": "Analytics"},
    {"pattern": r'googletagmanager\.com', "tech": "Google Tag Manager", "category": "Analytics"},
    {"pattern": r'facebook\.net/.*fbevents|fbq\(', "tech": "Facebook Pixel", "category": "Analytics"},
    {"pattern": r'hotjar\.com', "tech": "Hotjar", "category": "Analytics"},
    {"pattern": r'cdn\.segment\.com', "tech": "Segment", "category": "Analytics"},
    {"pattern": r'recaptcha|hcaptcha', "tech": "CAPTCHA", "category": "Segurança"},
]

COOKIE_SIGNATURES: list[dict[str, str]] = [
    {"pattern": r"PHPSESSID", "tech": "PHP", "category": "Linguagem"},
    {"pattern": r"JSESSIONID", "tech": "Java", "category": "Linguagem"},
    {"pattern": r"ASP\.NET_SessionId", "tech": "ASP.NET", "category": "Framework"},
    {"pattern": r"laravel_session", "tech": "Laravel (PHP)", "category": "Framework"},
    {"pattern": r"_rails_session|_session_id", "tech": "Ruby on Rails", "category": "Framework"},
    {"pattern": r"connect\.sid", "tech": "Express.js (Node.js)", "category": "Framework"},
    {"pattern": r"django_session|csrftoken", "tech": "Django (Python)", "category": "Framework"},
    {"pattern": r"flask_session|session=\.", "tech": "Flask (Python)", "category": "Framework"},
    {"pattern": r"__cf_bm|__cfduid", "tech": "Cloudflare", "category": "CDN/Proxy"},
    {"pattern": r"wp-settings|wordpress", "tech": "WordPress", "category": "CMS"},
    {"pattern": r"AWSALB|AWSALBCORS", "tech": "AWS ALB", "category": "Infra"},
]


@analyzer(mode="passive", name="technology-fingerprint")
async def analyze_fingerprint(record: ScanRecord) -> list[Finding]:
    """Detecta tecnologias, linguagem, framework, servidor e serviços do site."""
    findings: list[Finding] = []
    detected: dict[str, dict[str, str]] = {}  # tech -> {category, evidence, version}

    headers = {k.lower(): v for k, v in record.response_headers.items()}
    body = record.response_body

    # 1. Detecção por headers
    for sig in HEADER_SIGNATURES:
        header_value = headers.get(sig["header"], "")
        if header_value:
            match = re.search(sig["pattern"], header_value, re.IGNORECASE)
            if match:
                version = match.group(1) if match.lastindex and match.lastindex >= 1 else ""
                key = sig["tech"]
                if key not in detected:
                    detected[key] = {
                        "category": sig["category"],
                        "evidence": f"Header {sig['header']}: {header_value}",
                        "version": version,
                    }

    # 2. Detecção por HTML
    for sig in HTML_SIGNATURES:
        match = re.search(sig["pattern"], body, re.IGNORECASE | re.DOTALL)
        if match:
            version = match.group(1) if match.lastindex and match.lastindex >= 1 else ""
            key = sig["tech"]
            if key not in detected:
                # Truncar evidência para não ficar gigante
                snippet = match.group(0)[:120]
                detected[key] = {
                    "category": sig["category"],
                    "evidence": f"HTML: ...{snippet}...",
                    "version": version,
                }

    # 3. Detecção por cookies
    for cookie in record.cookies:
        for sig in COOKIE_SIGNATURES:
            if re.search(sig["pattern"], cookie.name, re.IGNORECASE):
                key = sig["tech"]
                if key not in detected:
                    detected[key] = {
                        "category": sig["category"],
                        "evidence": f"Cookie: {cookie.name}",
                        "version": "",
                    }

    # 4. Inferir linguagem se não detectada diretamente
    language = _infer_language(detected)

    # Gerar findings
    if not detected:
        findings.append(Finding(
            id="FP-NO-TECH",
            category="fingerprint",
            severity=Severity.INFO,
            title="Nenhuma tecnologia identificada",
            evidence="Não foi possível detectar tecnologias a partir dos headers, "
                     "HTML e cookies da resposta.",
            explanation="O site pode estar bem configurado para não expor informações "
                        "de tecnologia, ou usar tecnologias não reconhecidas pelo scanner.",
            remediation="Nenhuma ação necessária — não expor tecnologias é uma boa prática.",
            reference="https://owasp.org/www-project-web-security-testing-guide/",
            analyzer="technology-fingerprint",
            confidence=Confidence.CONFIRMED,
        ))
        return findings

    # Agrupar por categoria para o resumo
    by_category: dict[str, list[str]] = {}
    for tech, info in detected.items():
        cat = info["category"]
        version_str = f" {info['version']}" if info["version"] else ""
        by_category.setdefault(cat, []).append(f"{tech}{version_str}")

    # Finding principal: resumo de tecnologias
    summary_lines = []
    for cat, techs in sorted(by_category.items()):
        summary_lines.append(f"  [{cat}] {', '.join(techs)}")

    findings.append(Finding(
        id="FP-STACK-DETECTED",
        category="fingerprint",
        severity=Severity.INFO,
        title=f"Stack tecnológica detectada ({len(detected)} tecnologias)",
        evidence="\n".join(summary_lines),
        explanation="As tecnologias abaixo foram identificadas a partir de headers HTTP, "
                    "conteúdo HTML e cookies. Essa informação ajuda a entender a superfície "
                    "de ataque e buscar vulnerabilidades específicas.",
        remediation="Considere remover headers que expõem versões (Server, X-Powered-By) "
                    "e meta tags generator. Isso não é segurança por obscuridade — é redução "
                    "de informação gratuita para atacantes.",
        reference="https://owasp.org/www-project-web-security-testing-guide/"
                  "latest/4-Web_Application_Security_Testing/"
                  "01-Information_Gathering/02-Fingerprint_Web_Server",
        analyzer="technology-fingerprint",
        confidence=Confidence.CONFIRMED,
    ))

    # Linguagem inferida
    if language:
        findings.append(Finding(
            id="FP-LANGUAGE",
            category="fingerprint",
            severity=Severity.INFO,
            title=f"Linguagem de backend detectada: {language}",
            evidence=f"Inferido a partir de: {_language_evidence(language, detected)}",
            explanation=f"O backend provavelmente usa {language}. Isso pode direcionar "
                        "a busca por vulnerabilidades específicas da linguagem/runtime.",
            remediation="Informativo — nenhuma ação necessária.",
            reference="",
            analyzer="technology-fingerprint",
            confidence=Confidence.LIKELY,
        ))

    # Findings de versão exposta (risco de segurança)
    for tech, info in detected.items():
        if info["version"] and info["category"] in ("Servidor Web", "Linguagem", "Framework"):
            findings.append(Finding(
                id=f"FP-VERSION-{tech.upper().replace(' ', '-').replace('.', '')[:20]}",
                category="fingerprint",
                severity=Severity.LOW,
                title=f"Versão exposta: {tech} {info['version']}",
                evidence=info["evidence"],
                explanation=f"A versão exata ({info['version']}) permite a um atacante "
                            "buscar CVEs específicas para essa versão.",
                remediation=f"Remova ou ofusque a versão de {tech} nos headers de resposta.",
                reference="https://owasp.org/www-project-web-security-testing-guide/",
                analyzer="technology-fingerprint",
                confidence=Confidence.CONFIRMED,
            ))

    return findings


def _infer_language(detected: dict[str, dict[str, str]]) -> str:
    """Infere a linguagem de backend a partir das tecnologias detectadas."""
    language_map = {
        "PHP": "PHP",
        "Laravel (PHP)": "PHP",
        "WordPress": "PHP",
        "Drupal": "PHP",
        "Joomla": "PHP",
        "Django (Python)": "Python",
        "Flask (Python)": "Python",
        "Gunicorn (Python)": "Python",
        "Express.js (Node.js)": "JavaScript (Node.js)",
        "Next.js": "JavaScript (Node.js)",
        "Next.js (React)": "JavaScript (Node.js)",
        "Nuxt.js (Vue)": "JavaScript (Node.js)",
        "ASP.NET": "C# (.NET)",
        "ASP.NET MVC": "C# (.NET)",
        "Blazor (.NET)": "C# (.NET)",
        "Kestrel (.NET)": "C# (.NET)",
        "Ruby on Rails": "Ruby",
        "Passenger (Ruby)": "Ruby",
        "Java Servlet": "Java",
        "Cowboy (Erlang/Elixir)": "Elixir/Erlang",
    }

    for tech in detected:
        if tech in language_map:
            return language_map[tech]

    return ""


def _language_evidence(language: str, detected: dict[str, dict[str, str]]) -> str:
    """Retorna a evidência que levou à inferência da linguagem."""
    language_map = {
        "PHP": ["PHP", "Laravel (PHP)", "WordPress", "Drupal", "Joomla"],
        "Python": ["Django (Python)", "Flask (Python)", "Gunicorn (Python)"],
        "JavaScript (Node.js)": ["Express.js (Node.js)", "Next.js", "Next.js (React)", "Nuxt.js (Vue)"],
        "C# (.NET)": ["ASP.NET", "ASP.NET MVC", "Blazor (.NET)", "Kestrel (.NET)"],
        "Ruby": ["Ruby on Rails", "Passenger (Ruby)"],
        "Java": ["Java Servlet"],
        "Elixir/Erlang": ["Cowboy (Erlang/Elixir)"],
    }

    techs = language_map.get(language, [])
    found = [t for t in techs if t in detected]
    if found:
        evidences = [detected[t]["evidence"] for t in found]
        return "; ".join(evidences)
    return "heurística"
