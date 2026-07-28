# Design do Épico — Analisador de Segurança Web (Passivo + Ativo)

> **Arquitetura macro do módulo**
>
> Define as estruturas compartilhadas que todas as sub-funcionalidades consomem.
> Base: #[[file:epic-requirements.md]]

## Status

| Campo | Valor |
|---|---|
| Fase | `Aprovado` |
| Aprovado por | Usuário |

## Visão arquitetural

```
┌──────────────────────────── Aplicação GTK4 ─────────────────────────────┐
│                                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────────────────┐  │
│  │  UI Layer   │◄──►│  Controller  │◄──►│      Result Store         │  │
│  │  (GTK4 +    │    │  (orquestra  │    │  (achados + log de reqs)  │  │
│  │  libadwaita)│    │   execução)  │    └───────────────────────────┘  │
│  └─────────────┘    └──────┬───────┘                                   │
│                            │                                            │
│         ┌──────────────────┼───────────────────────┐                   │
│         ▼                  ▼                       ▼                    │
│  ┌─────────────┐   ┌─────────────┐   ┌────────────────────┐           │
│  │  Collector   │   │  Payload    │   │  Nuclei Bridge     │           │
│  │  (httpx +    │   │  Engine     │   │  (subprocesso)     │           │
│  │   TLS probe) │   │  (gera +    │   └────────────────────┘           │
│  │              │   │   submete)  │                                     │
│  └──────┬───────┘   └──────┬──────┘                                    │
│         │                  │                                            │
│         ▼                  ▼                                            │
│  ┌─────────────────────────────────────────────────────────┐           │
│  │                   Request Guard (L-1)                    │           │
│  │   — valida modo vs. destino antes de emitir             │           │
│  │   — registra toda requisição no log                     │           │
│  │   — aplica rate limit (L-3)                             │           │
│  └─────────────────────────────────────────────────────────┘           │
│                            │                                            │
│                            ▼                                            │
│                     ┌─────────────┐                                     │
│                     │   Network   │                                     │
│                     │   (httpx)   │                                     │
│                     └─────────────┘                                     │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────┐           │
│  │              Analyzers (funções puras)                   │           │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │           │
│  │  │ Headers  │ │ TLS/Cert │ │ Cookies  │ │ Document │  │           │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │           │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │           │
│  │  │   CORS   │ │   SRI    │ │ Banners  │ │  JS Libs │  │           │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │           │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │           │
│  │  │  SQLi    │ │   XSS    │ │ CmdInj   │ │  SSTI    │  │           │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │           │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │           │
│  │  │Traversal │ │  IDOR    │ │ Redirect │ │  DirEnum │  │           │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │           │
│  └─────────────────────────────────────────────────────────┘           │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────┐           │
│  │              Exporters                                   │           │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐               │           │
│  │  │ Markdown │ │   JSON   │ │   HTML   │               │           │
│  │  └──────────┘ └──────────┘ └──────────┘               │           │
│  └─────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Decisões arquiteturais do épico

### ADE-1 — Request Guard como ponto único de saída

- **Contexto:** L-1 define escopo de requisições por modo. Precisamos garantir
  arquiteturalmente (não por disciplina) que nenhum componente emite requisição fora do
  escopo.
- **Decisão:** toda requisição HTTP passa por um `RequestGuard` que valida modo + destino
  antes de delegar ao `httpx.AsyncClient`. O guard é o único componente que detém o client.
- **Alternativas descartadas:** confiar que cada analisador respeite o escopo (frágil);
  interceptor no nível de transporte (complexo e menos legível).
- **Consequências:** overhead mínimo (uma validação por requisição); toda violação é
  detectada e logada antes de sair. Testes podem injetar um guard que rejeita tudo e
  verifica que nenhum analisador tenta burlar.

### ADE-2 — Analisadores como funções puras registradas

- **Contexto:** L-5 exige separação entre coleta e análise; L-9 exige isolamento de falha.
- **Decisão:** cada analisador é uma função `async def analyze(record: ScanRecord) ->
  list[Finding]`. Um registry central descobre analisadores por decorador (`@analyzer`).
  O controller chama cada um em isolamento (`try/except`).
- **Alternativas descartadas:** herança de classe abstrata (verbosidade sem ganho);
  pipeline sequencial obrigatório (impede paralelismo entre analisadores independentes).
- **Consequências:** adicionar um analisador é criar um módulo com uma função decorada —
  nenhum outro arquivo precisa ser alterado. Testes são `analyze(fixture) == expected`.

### ADE-3 — Motor de payloads com templates declarativos

- **Contexto:** E-2 exige testes ativos em 13 categorias. Hardcodar payloads em Python
  torna atualização e extensão dolorosas.
- **Decisão:** payloads são declarados em arquivos YAML (um por categoria) com estrutura:
  `id`, `name`, `severity`, `injection_points`, `payloads[]`, `detection` (regex, time,
  status, content). O motor lê os templates, gera as requisições e avalia as respostas.
- **Alternativas descartadas:** tudo em código (inflexível); formato nuclei nativo (acoplaria
  ao nuclei e é complexo demais para nosso motor leve).
- **Consequências:** usuário avançado pode adicionar templates sem tocar em Python; a
  base embarcada pode ser atualizada sem release novo. Precisa de parser YAML, mas
  `pyyaml` é dependência leve.

### ADE-4 — Nuclei como subprocesso opaco

- **Contexto:** E-6 exige integração com nuclei, mas nuclei é binário Go externo.
- **Decisão:** a bridge executa `nuclei` como subprocesso com flags que produzem JSON
  line-delimited. A bridge converte cada linha para `Finding`. Sem API Go, sem binding.
- **Alternativas descartadas:** importar nuclei como library (impossível em Python);
  reimplementar templates nuclei (inviável).
- **Consequências:** nuclei é dependência **opcional** do sistema, não do pacote Python.
  Se não está instalado, a feature é desabilitada gracefully. Atualização do nuclei é
  independente da ferramenta.

### ADE-5 — Async + thread worker para GTK

- **Contexto:** L-8 exige interface responsiva; GTK não suporta `asyncio` nativamente na
  main loop.
- **Decisão:** a execução do scan roda em uma thread dedicada com seu próprio event loop
  `asyncio`. Resultados parciais são enviados à UI via `GLib.idle_add`. Cancelamento via
  `asyncio.Event` compartilhado.
- **Alternativas descartadas:** `Gio.Task` (menos controle sobre o event loop async);
  multiprocessing (overhead de serialização para achados).
- **Consequências:** a UI nunca bloqueia; achados aparecem em tempo real; cancelamento é
  cooperativo (cada etapa checa o evento).

### ADE-6 — Formato de achado unificado (L-6)

- **Contexto:** L-6 exige formato único; E-6 exige converter achados do nuclei.
- **Decisão:** estrutura `Finding` é um dataclass frozen com campos obrigatórios. Todos
  os produtores (analisadores internos, motor de payloads, bridge nuclei) emitem
  `Finding`. A UI e os exporters consomem apenas `Finding`.
- **Consequências:** a interface é desacoplada de como o achado foi produzido. Ordenação,
  filtragem e exportação são genéricas.

## Modelo de dados compartilhado

### `ScanRecord` — o registro de coleta

```python
@dataclass(frozen=True)
class TLSInfo:
    protocol_version: str            # "TLSv1.3"
    cipher_suite: str
    certificate_chain: list[CertInfo]
    supported_protocols: list[str]   # todas as versões aceitas

@dataclass(frozen=True)
class CertInfo:
    subject: dict[str, str]
    issuer: dict[str, str]
    not_before: datetime
    not_after: datetime
    san: list[str]
    serial: str
    signature_algorithm: str

@dataclass(frozen=True)
class RequestLog:
    timestamp: datetime
    method: str
    url: str
    headers_sent: dict[str, str]
    payload: str | None              # None para passivo
    status_code: int | None
    response_headers: dict[str, str]
    response_body_snippet: str       # primeiros 4KB
    elapsed_ms: float
    mode: Literal["passive", "active"]

@dataclass(frozen=True)
class ScanRecord:
    target_url: str                  # URL original informada
    final_url: str                   # URL após redirects
    redirect_chain: list[str]
    response_status: int
    response_headers: dict[str, str]
    response_body: str               # HTML completo (até 2MB)
    cookies: list[CookieInfo]
    tls: TLSInfo | None
    timestamp: datetime
    mode: Literal["passive", "active"]
    request_log: list[RequestLog]
```

### `Finding` — o achado

```python
@dataclass(frozen=True)
class Finding:
    id: str                          # estável, ex.: "HDR-CSP-MISSING"
    category: str                    # ex.: "headers", "sqli", "xss"
    severity: Literal["critical", "high", "medium", "low", "info", "indeterminate"]
    title: str                       # pt-BR, conciso
    evidence: str                    # o que foi observado literalmente
    payload_sent: str | None         # o que foi enviado (modo ativo)
    explanation: str                 # por que importa
    remediation: str                 # correção concreta
    reference: str                   # CWE, OWASP, CVE, ou URL de doc
    analyzer: str                    # quem produziu
    confidence: Literal["confirmed", "likely", "indeterminate"]
```

### `PayloadTemplate` — template de teste ativo

```yaml
# Exemplo: sqli-time-based.yaml
id: SQLI-TIME-001
name: "SQL Injection — Time-based (MySQL SLEEP)"
category: sqli
severity: critical
cwe: "CWE-89"
injection_points:
  - query_params
  - body_params
  - path_segments
payloads:
  - value: "' OR SLEEP({delay})-- -"
    variants:
      - "' OR SLEEP({delay})#"
      - "\" OR SLEEP({delay})-- -"
      - "1; SELECT SLEEP({delay})-- -"
detection:
  type: time
  threshold_ms: 5000
  delay: 5
  confirmation_rounds: 2
metadata:
  description: "Injeta SLEEP e verifica se o tempo de resposta excede o threshold."
  safe: true
  reference: "https://owasp.org/www-community/attacks/SQL_Injection"
```

### `CookieInfo`

```python
@dataclass(frozen=True)
class CookieInfo:
    name: str
    value_snippet: str               # primeiros 20 chars (não armazenar valor completo)
    domain: str
    path: str
    secure: bool
    httponly: bool
    samesite: str | None
    expires: datetime | None
```

## Contratos de fronteira

A ferramenta é standalone — não expõe API para fora. As fronteiras são:

| Fronteira | Tipo | Direção |
|---|---|---|
| Alvo HTTP | Requisições HTTP/HTTPS | Saída (via RequestGuard) |
| nuclei CLI | Subprocesso stdin/stdout | Saída/Entrada |
| Sistema de arquivos | Exportação de relatório | Saída |
| GTK/libadwaita | Renderização | Entrada/Saída |

## Estrutura de pastas do projeto

```
webguard/                            # nome do projeto
├── pyproject.toml                   # build system, dependências, scripts
├── src/
│   └── webguard/
│       ├── __init__.py
│       ├── app.py                   # GtkApplication, janela principal
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── window.py            # AdwApplicationWindow
│       │   ├── scan_page.py         # entrada de URL, seleção de modo
│       │   ├── results_page.py      # lista de achados
│       │   ├── log_page.py          # log de requisições
│       │   ├── style.css            # tema hacker (paleta, animações, fontes)
│       │   └── widgets/             # componentes reutilizáveis
│       │       ├── __init__.py
│       │       ├── ascii_banner.py  # logo Unicode
│       │       ├── typing_label.py  # revelação caractere a caractere
│       │       └── hacker_progress.py # barra ■░
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py            # ScanRecord, Finding, etc.
│       │   ├── controller.py        # orquestra execução
│       │   ├── guard.py             # RequestGuard (L-1, L-3)
│       │   ├── collector.py         # coleta HTTP + TLS
│       │   └── registry.py          # registry de analisadores
│       ├── analyzers/
│       │   ├── __init__.py
│       │   ├── passive/
│       │   │   ├── __init__.py
│       │   │   ├── headers.py
│       │   │   ├── tls.py
│       │   │   ├── cookies.py
│       │   │   ├── cors.py
│       │   │   ├── sri.py
│       │   │   ├── banners.py
│       │   │   ├── mixed_content.py
│       │   │   └── js_libs.py
│       │   └── active/
│       │       ├── __init__.py
│       │       ├── engine.py        # motor de payloads
│       │       ├── sqli.py
│       │       ├── xss.py
│       │       ├── cmdi.py
│       │       ├── ssti.py
│       │       ├── traversal.py
│       │       ├── idor.py
│       │       ├── redirect.py
│       │       ├── dir_enum.py
│       │       ├── sensitive_files.py
│       │       └── weak_auth.py
│       ├── templates/               # YAML de payloads
│       │   ├── sqli/
│       │   ├── xss/
│       │   ├── cmdi/
│       │   ├── ssti/
│       │   ├── traversal/
│       │   ├── redirect/
│       │   └── dir_enum/
│       ├── data/
│       │   ├── wordlists/           # enumeração de diretórios (~500)
│       │   └── js_vulns.json        # base local de libs JS vulneráveis
│       ├── bridge/
│       │   ├── __init__.py
│       │   └── nuclei.py            # integração opcional
│       └── exporters/
│           ├── __init__.py
│           ├── markdown.py
│           ├── json_export.py
│           └── html_export.py
├── tests/
│   ├── conftest.py                  # fixtures compartilhadas
│   ├── fixtures/                    # respostas HTTP gravadas
│   ├── test_analyzers/
│   ├── test_active/
│   ├── test_guard.py
│   ├── test_collector.py
│   ├── test_exporters.py
│   └── test_nuclei_bridge.py
└── data/
    └── wordlists/
        └── common.txt               # wordlist curada
```

## Padrões transversais obrigatórios

### Tratamento de erro

| Situação | Detecção | Ação |
|---|---|---|
| Analisador lança exceção | `try/except` no controller | Log erro, Finding com `indeterminate`, continua |
| Timeout de requisição | `httpx.TimeoutException` | Log, marca no RequestLog, continua |
| Destino recusa conexão | `httpx.ConnectError` | Reporta na UI, preserva achados já coletados |
| Guard bloqueia requisição | Validação no guard | Log como erro interno, não emite, `Finding` informativo |
| nuclei falha | Exit code != 0 | Exibe stderr, continua sem nuclei |
| Payload causa resposta inesperada | Detecção no motor | Registra como indeterminado, não afirma vuln |

### Rate limiting (L-3)

```python
class RateLimiter:
    """Token bucket com configuração por modo."""
    def __init__(self, mode: str, requests_per_second: float = 10, min_interval_ms: float = 200):
        if mode == "passive":
            self._interval = min_interval_ms / 1000
            self._semaphore = asyncio.Semaphore(1)  # serializado
        else:
            self._interval = 1.0 / requests_per_second
            self._semaphore = asyncio.Semaphore(5)  # concorrência configurável

    async def acquire(self):
        async with self._semaphore:
            await asyncio.sleep(self._interval)
```

### Cancelamento

```python
class ScanContext:
    """Compartilhado entre controller e workers."""
    def __init__(self):
        self.cancel_event = asyncio.Event()
        self.findings: list[Finding] = []
        self.request_log: list[RequestLog] = []

    def is_cancelled(self) -> bool:
        return self.cancel_event.is_set()

    def cancel(self):
        self.cancel_event.set()
```

Cada etapa checa `ctx.is_cancelled()` antes de emitir a próxima requisição.

### Comunicação thread worker → UI

```python
def _on_finding(self, finding: Finding):
    """Chamado na worker thread; agenda update na main."""
    GLib.idle_add(self._ui_append_finding, finding)

def _on_progress(self, stage: str, percent: float):
    GLib.idle_add(self._ui_update_progress, stage, percent)
```

## Dependências do projeto

```toml
[project]
requires-python = ">=3.12"
dependencies = [
    "PyGObject>=3.46",
    "httpx[http2]>=0.27",
    "cryptography>=42.0",
    "beautifulsoup4>=4.12",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.5",
    "mypy>=1.10",
    "pytest-cov>=5.0",
]
```

GTK4 e libadwaita vêm via pacotes do sistema (`libgtk-4-dev`, `libadwaita-1-dev`,
`gir1.2-adw-1`).

## Portões de qualidade (resolução da pergunta 1)

Fixados para o Artigo III da constituição:

```bash
ruff check src/ tests/              # lint
ruff format --check src/ tests/     # formatação
mypy src/                           # type check
pytest --cov=src/webguard --cov-fail-under=85 tests/  # testes + cobertura
```

## Estratégia de testes do módulo

| Nível | O que cobre | Como |
|---|---|---|
| Unitário (analisadores) | Cada analisador contra fixtures | `pytest` com respostas HTTP gravadas |
| Unitário (motor de payloads) | Parsing de templates + geração de requisições | Fixtures YAML + mock do guard |
| Unitário (guard) | Rejeição de requisições fora do modo | Sem rede, mock do client |
| Integração (controller) | Pipeline completo com collector mockado | Fixture → controller → findings |
| Integração (nuclei bridge) | Parsing de saída JSON do nuclei | Output gravado do nuclei |
| Integração (exporters) | Finding → arquivo exportado legível | Comparação com golden files |

**Nenhum teste acessa a internet.** O `conftest.py` instala um transport mock no httpx que
serve as fixtures gravadas.

## Sequenciamento

```
epic-design (este doc) ──▶ 01-nucleo-e-cabecalhos ──▶ 02-tls-cookies ──▶ 03-documento ──▶ 04-motor-ativo
                                                          └──────────────────┘     └──────────────────┘
                                                             podem ser paralelas entre si
```

O núcleo compartilhado (models, guard, collector, controller, registry, UI shell) é
construído dentro de `01` como a primeira fatia vertical. As demais sub-funcionalidades
adicionam analisadores sobre essa fundação.

## Rastreabilidade

| Requisito | Onde é atendido |
|---|---|
| E-1 | Controller + analyzers passivos + UI results_page |
| E-2 | Payload Engine + active analyzers + UI results_page |
| E-3 | Finding dataclass + results_page + exporters |
| E-4 | RequestLog + guard + log_page |
| E-5 | Exporters (markdown, json, html) |
| E-6 | NucleiBridge + Finding conversion |
| L-1 | RequestGuard |
| L-2 | scan_page (consent dialog) |
| L-3 | RateLimiter |
| L-4 | Nenhuma chamada de rede nos testes |
| L-5 | Collector separado de analyzers; Finding como output |
| L-6 | Finding dataclass com campos obrigatórios |
| L-7 | Detecção exige evidência observada |
| L-8 | Thread worker + GLib.idle_add |
| L-9 | try/except por analisador no controller |
