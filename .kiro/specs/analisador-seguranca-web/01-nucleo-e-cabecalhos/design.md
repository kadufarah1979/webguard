# Design Local — Núcleo e Análise de Cabeçalhos

> **Contratos de API locais**
>
> Detalha a implementação da fundação e do primeiro analisador.
> Arquitetura macro: #[[file:../epic-design.md]]
> Requisitos locais: #[[file:requirements.md]]
> Identidade visual: #[[file:visual-identity.md]]

## Status

| Campo | Valor |
|---|---|
| Fase | `Aprovado` |
| Aprovado por | Usuário |

## Conformidade com o épico

| Item do épico | Como esta sub-funcionalidade o consome |
|---|---|
| ADE-1 (RequestGuard) | Implementa `guard.py` como ponto único de saída |
| ADE-2 (Analyzers como funções) | Implementa `registry.py` + decorador `@analyzer` |
| ADE-5 (Async + thread) | Implementa worker thread em `controller.py` |
| ADE-6 (Finding unificado) | Implementa `models.py` com Finding dataclass |
| ScanRecord | Implementa versão completa em `models.py` |

**Nada novo no schema compartilhado?** Confirmado — esta sub-funcionalidade define o schema.

## Visão geral

A sub-01 cria toda a infraestrutura do projeto e um analisador funcional. A entrega é uma
aplicação GTK4 que:
1. Aceita URL → valida → coleta com guard → analisa cabeçalhos → exibe achados em tempo real.

## Decisões locais

### ADL-1 — Validação de URL com urllib.parse + resolução DNS lazy

- **Decisão:** validar sintaticamente com `urllib.parse.urlparse` (esquema + netloc); a
  resolução DNS acontece apenas na coleta, não na validação visual.
- **Motivo:** validação instantânea sem rede; erros de DNS são tratados como falha de
  coleta, não de validação.

### ADL-2 — Um arquivo por cabeçalho verificado

- **Decisão:** dentro de `analyzers/passive/headers.py`, cada cabeçalho é uma função
  interna. Se o arquivo crescer demais (>300 linhas), extrair para
  `analyzers/passive/headers/` com um arquivo por cabeçalho.
- **Motivo:** começar simples, extrair se necessário.

### ADL-3 — CSP parser próprio e simples

- **Decisão:** parser de CSP que tokeniza por `;` e depois por espaço. Não usa lib externa.
- **Motivo:** o parsing de CSP é trivial (diretiva + valores separados por espaço) e não
  justifica dependência. O julgamento (unsafe-inline, wildcards) é lógica de negócio nossa.

## Componentes construídos nesta sub-funcionalidade

### `webguard.core.models`

Define todos os dataclasses do épico: `ScanRecord`, `Finding`, `TLSInfo`, `CertInfo`,
`CookieInfo`, `RequestLog`, `PayloadTemplate`.

### `webguard.core.guard` — RequestGuard

```python
class RequestGuard:
    """Ponto único de saída HTTP. Valida modo + destino + rate limit."""

    def __init__(self, mode: Mode, target_url: str, rate_limiter: RateLimiter, ctx: ScanContext):
        ...

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Emite requisição se permitida pelo modo; caso contrário, bloqueia e loga."""
        ...

    def is_allowed(self, url: str) -> bool:
        """Verifica se a URL está no escopo do modo atual."""
        ...
```

Regras de `is_allowed` no modo passivo:
- Mesmo host da URL original (case-insensitive)
- Caminhos `/robots.txt` e `/.well-known/security.txt` do mesmo host
- Sub-recursos referenciados (URLs passadas explicitamente pelo collector)

### `webguard.core.collector` — Collector

```python
class Collector:
    """Coleta a resposta HTTP e monta o ScanRecord."""

    async def collect(self, url: str, guard: RequestGuard, ctx: ScanContext) -> ScanRecord | CollectError:
        """Busca a URL, segue redirects, coleta metadados."""
        ...
```

- Segue até 10 redirects
- Timeout por requisição: 15s
- Registra cada hop no `redirect_chain`
- Trunca body em 2MB
- Retorna `CollectError` (não lança) em caso de falha

### `webguard.core.registry` — Registry

```python
_analyzers: list[AnalyzerFunc] = []

def analyzer(*, mode: str, name: str):
    """Decorador que registra um analisador."""
    def decorator(fn):
        _analyzers.append(AnalyzerEntry(fn=fn, mode=mode, name=name))
        return fn
    return decorator

def get_analyzers(mode: str) -> list[AnalyzerEntry]:
    ...
```

### `webguard.core.controller` — Controller

```python
class ScanController:
    """Orquestra a execução em thread worker."""

    def start_scan(self, url: str, mode: Mode, on_finding, on_progress, on_done, on_error):
        """Lança a thread worker."""
        ...

    def cancel(self):
        """Sinaliza cancelamento via ctx.cancel_event."""
        ...
```

Internamente:
1. Cria `ScanContext`, `RateLimiter`, `RequestGuard`
2. Chama `Collector.collect()`
3. Itera sobre `get_analyzers(mode)`, chamando cada um em `try/except`
4. Para cada `Finding` produzido, chama `on_finding` via `GLib.idle_add`

### `webguard.analyzers.passive.headers` — Analisador de cabeçalhos

```python
@analyzer(mode="passive", name="security-headers")
async def analyze_headers(record: ScanRecord) -> list[Finding]:
    ...
```

Verifica os 10 cabeçalhos listados em S1-4. Para CSP, decompõe diretivas e avalia:
- `script-src`: presença de `'unsafe-inline'`, `'unsafe-eval'`, `*`, `data:`
- `object-src`: deve ser `'none'`
- `base-uri`: deve existir
- `default-src`: fallback se diretiva específica ausente

### `webguard.ui.window` — Janela principal

`AdwApplicationWindow` com tema hacker (ver `visual-identity.md`):
- `AdwHeaderBar` minimal com título `web::guard` em `accent-green`
- `AdwViewStack` com 2 páginas: Scan e Log
- `AdwViewSwitcherBar` para navegação (ícones mono)
- Fundo `bg-primary` (#0D1117), fonte JetBrains Mono global
- Dark mode forçado via `Adw.StyleManager.set_color_scheme(FORCE_DARK)`
- CSS customizado carregado no startup (`style.css`)
- ASCII art banner no topo (desaparece ao iniciar scan)

### `webguard.ui.scan_page` — Página de scan

- Campo de URL estilo terminal: prompt `➜ TARGET:` em verde, cursor bloco piscante
- Toggle de modo: `PASSIVE` (cyan) / `ACTIVE` (vermelho) com labels uppercase
- Checkboxes de categorias (`[✓]`/`[ ]`) quando modo ativo — grid 2 colunas
- Dialog de consentimento com bordas duplas Unicode e checkbox obrigatório
- Botão `▶ INICIAR VARREDURA` em verde (inversão) com glow hover
- Durante scan: muda para `■ ABORTAR` em vermelho
- Progresso: barra `■░` + etapas com `[✓]`/`[-]`/`[ ]` + typing effect na etapa atual
- `GtkListBox` de achados com borda colorida por severidade e revelação fade-in

### `webguard.ui.results_page` → integrada na scan_page

Achados aparecem abaixo do formulário. Cada achado é um `AdwExpanderRow` estilizado:
- Tag de severidade colorida: `[CRITICAL]` vermelho, `[HIGH]` laranja, etc.
- Seções: `EVIDENCE:` / `RISK:` / `FIX:` em labels uppercase cinza
- Bloco de correção com fundo `bg-input` e botão copiar `[📋]`
- Ao expandir: animação slide-down (200ms)

### `webguard.ui.log_page` — Página de log

- Tabela mono alinhada estilo `htop`:
  `TIME | METHOD | URL | STATUS | ELAPSED`
- Status colorido: 2xx verde, 3xx cyan, 4xx amarelo, 5xx vermelho
- Linhas bloqueadas pelo guard: `✗ BLOCKED` em vermelho
- Scrollbar fina, painel de detalhes ao clicar

### `webguard.ui.style.css` — Tema CSS

Arquivo CSS carregado via `Gtk.CssProvider` com:
- Cores da paleta do `visual-identity.md`
- Animações: blink cursor, pulse hover, glow focus, fadeIn achados
- Scanline overlay (muito sutil, desabilitável)
- Override de widgets nativos para visual terminal

### `webguard.ui.widgets/` — Widgets customizados

- `TypingLabel`: GtkLabel com revelação caractere a caractere (50ms/char)
- `HackerProgressBar`: draw custom com `■░` ao invés da barra nativa
- `AsciiArtBanner`: GtkLabel com o logo em bloco Unicode

## Contratos — Formato dos achados de cabeçalhos

Exemplos concretos para guiar a implementação:

```python
Finding(
    id="HDR-CSP-MISSING",
    category="headers",
    severity="medium",
    title="Content-Security-Policy ausente",
    evidence="O cabeçalho Content-Security-Policy não está presente na resposta.",
    payload_sent=None,
    explanation="Sem CSP, o navegador não tem restrições sobre quais scripts podem "
                "executar, tornando XSS mais fácil de explorar.",
    remediation="Adicione o cabeçalho:\n"
                "Content-Security-Policy: default-src 'self'; script-src 'self'; "
                "object-src 'none'; base-uri 'self'",
    reference="https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP",
    analyzer="security-headers",
    confidence="confirmed",
)

Finding(
    id="HDR-CSP-UNSAFE-INLINE",
    category="headers",
    severity="medium",
    title="CSP permite 'unsafe-inline' em script-src",
    evidence="Content-Security-Policy: script-src 'self' 'unsafe-inline'",
    payload_sent=None,
    explanation="'unsafe-inline' permite execução de scripts inline, anulando grande "
                "parte da proteção que a CSP oferece contra XSS.",
    remediation="Remova 'unsafe-inline' de script-src e use nonces ou hashes:\n"
                "script-src 'self' 'nonce-{random}'",
    reference="https://csp-evaluator.withgoogle.com/",
    analyzer="security-headers",
    confidence="confirmed",
)
```

## Tratamento de erro local

| Situação | Ação |
|---|---|
| URL inválida | Bloqueia botão, mensagem no campo |
| DNS não resolve | `CollectError(reason="dns_resolution_failed", detail=...)` |
| Conexão recusada | `CollectError(reason="connection_refused", ...)` |
| Timeout | `CollectError(reason="timeout", ...)` |
| Redirect loop (>10) | `CollectError(reason="too_many_redirects", ...)` |
| Analisador lança exceção | Finding `indeterminate` + log |

## Estratégia de testes local

| Nível | O que | Como |
|---|---|---|
| Unit: headers | Cada cabeçalho ausente/presente/malconfigurado | Fixture com headers dict |
| Unit: CSP parser | Cada diretiva e valor problemático | Strings CSP conhecidas |
| Unit: guard | Permite/bloqueia URLs por modo | Sem rede |
| Unit: collector | Segue redirects, trunca, respeita timeout | httpx mock transport |
| Integration: controller | URL → achados completos | Fixture end-to-end |
| Manual: UI | Abre, digita URL, vê achados | Na máquina do usuário |

## Rastreabilidade

| Requisito | Onde é atendido |
|---|---|
| S1-1 | `scan_page.py` + `urllib.parse` |
| S1-2 | `scan_page.py` (switch + dialog consentimento) |
| S1-3 | `guard.py` + `collector.py` + `RateLimiter` |
| S1-4 | `analyzers/passive/headers.py` |
| S1-5 | `scan_page.py` (AdwExpanderRow) |
| S1-6 | `log_page.py` + `RequestLog` |
| S1-7 | `controller.py` (cancel_event) + botão cancelar |
