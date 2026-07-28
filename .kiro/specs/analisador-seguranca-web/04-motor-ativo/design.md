# Design Local — Motor de Testes Ativos

> Arquitetura macro: #[[file:../epic-design.md]]
> Requisitos: #[[file:requirements.md]]

## Status

| Campo | Valor |
|---|---|
| Fase | `Em revisão` |
| Aprovado por | `PENDENTE` |

## Conformidade com o épico

| Item do épico | Consumo |
|---|---|
| ADE-1 (RequestGuard) | Usa guard em modo ativo (destinos expandidos conforme L-1) |
| ADE-2 (Registry) | Registra analisadores ativos no registry |
| ADE-3 (Templates YAML) | Implementa parser e motor |
| ADE-4 (Nuclei bridge) | Implementa `bridge/nuclei.py` |
| ADE-5 (Thread worker) | Reutiliza infra da sub-01 |

## Visão geral

O motor ativo opera em pipeline:

```
Categorias selecionadas
       │
       ▼
┌─────────────────────┐
│ Template Loader     │  ← lê YAMLs de templates/
└──────────┬──────────┘
           │ list[PayloadTemplate]
           ▼
┌─────────────────────┐
│ Injection Planner   │  ← decide onde injetar (params, body, path)
└──────────┬──────────┘
           │ list[PlannedRequest]
           ▼
┌─────────────────────┐
│ Request Executor    │  ← submete via RequestGuard com concorrência/rate limit
└──────────┬──────────┘
           │ list[(PlannedRequest, httpx.Response)]
           ▼
┌─────────────────────┐
│ Detection Engine    │  ← aplica regra de detecção do template
└──────────┬──────────┘
           │ list[Finding]
           ▼
       Controller (callbacks → UI)
```

## Componentes

### `webguard.analyzers.active.engine` — PayloadEngine

```python
class PayloadEngine:
    """Orquestra a execução de templates de uma categoria."""

    def __init__(self, guard: RequestGuard, ctx: ScanContext, config: ActiveConfig):
        ...

    async def run_category(self, category: str, target_url: str) -> list[Finding]:
        """Carrega templates da categoria, planeja injeções, executa, detecta."""
        ...
```

### `webguard.analyzers.active.engine` — TemplateLoader

```python
class TemplateLoader:
    """Carrega e valida templates YAML."""

    @staticmethod
    def load_category(category: str) -> list[PayloadTemplate]:
        ...

    @staticmethod
    def validate_safety(template: PayloadTemplate) -> bool:
        """Verifica que payloads não contêm operações destrutivas."""
        ...
```

### `webguard.analyzers.active.engine` — InjectionPlanner

```python
class InjectionPlanner:
    """Gera requisições concretas a partir de templates + URL alvo."""

    def plan(self, url: str, template: PayloadTemplate) -> list[PlannedRequest]:
        """Para cada injection_point × payload variant, gera uma requisição."""
        ...
```

### `webguard.analyzers.active.engine` — DetectionEngine

```python
class DetectionEngine:
    """Avalia resposta contra regra de detecção do template."""

    async def evaluate(self, planned: PlannedRequest, response: httpx.Response,
                       baseline_time: float, template: PayloadTemplate) -> Finding | None:
        ...
```

Tipos de detecção:
- `time`: compara `response.elapsed` com `threshold_ms`. Confirma com N rounds.
- `content`: aplica regex na resposta.
- `status`: verifica se status code indica sucesso inesperado.
- `diff`: compara resposta com baseline (para boolean-based e IDOR).

### `webguard.analyzers.active.{sqli,xss,cmdi,...}`

Cada módulo de categoria é um thin wrapper que:
1. Define paths de templates YAML
2. Pode adicionar lógica de pré/pós-processamento específica
3. É registrado com `@analyzer(mode="active", name="sqli")`

```python
@analyzer(mode="active", name="sqli")
async def analyze_sqli(record: ScanRecord, engine: PayloadEngine) -> list[Finding]:
    """Executa templates de SQLi contra os parâmetros do record."""
    return await engine.run_category("sqli", record.target_url)
```

### `webguard.bridge.nuclei` — NucleiBridge

```python
class NucleiBridge:
    """Executa nuclei como subprocesso e converte output."""

    @staticmethod
    def is_available() -> bool:
        """Verifica se nuclei está no PATH."""
        ...

    async def run(self, url: str, severity: str, rate_limit: int,
                  ctx: ScanContext) -> list[Finding]:
        """Executa nuclei -json e converte cada linha para Finding."""
        ...
```

Mapeamento nuclei → Finding:

| Campo nuclei (JSON) | Campo Finding |
|---|---|
| `template-id` | `id` (prefixo "NUCLEI-") |
| `info.name` | `title` |
| `info.severity` | `severity` |
| `matched-at` | `evidence` |
| `info.description` | `explanation` |
| `info.remediation` | `remediation` (ou genérico) |
| `info.reference[]` | `reference` (primeiro item) |
| — | `analyzer = "nuclei"` |
| — | `confidence = "confirmed"` |

### `webguard.data.wordlists/common.txt`

Wordlist curada (~500 caminhos). Organizada por categoria:

```
# Version control
.git/config
.git/HEAD
.gitignore
.svn/entries
.hg/

# Environment & config
.env
.env.local
.env.production
wp-config.php
web.config
...
```

## Decisões locais

### ADL-8 — Baseline request para detecção time-based

- **Decisão:** antes de enviar payloads time-based, medir o tempo de resposta normal
  (3 requests sem payload, média). Threshold = baseline + `delay` do template.
- **Motivo:** servidores lentos causam falso positivo se comparamos apenas com threshold
  absoluto.

### ADL-9 — Custom 404 detection para enumeração

- **Decisão:** antes da wordlist, enviar request a `/wg-404-baseline-{uuid}`. Armazenar
  status + tamanho + hash do body. Usar como referência para distinguir 404 customizado.
- **Motivo:** muitos sites retornam 200 com página "não encontrado".

### ADL-10 — Cada categoria é isolada e cancelável

- **Decisão:** o controller executa categorias como tasks concorrentes com `asyncio.gather`
  + per-category cancel event.
- **Motivo:** permite cancelamento granular (S4-13) e uma categoria falhando não bloqueia
  as demais (L-9).

### ADL-11 — Validação estática de segurança dos templates

- **Decisão:** `TemplateLoader.validate_safety()` verifica regex contra padrões proibidos
  (DROP, DELETE, UPDATE, INSERT, TRUNCATE, rm, shutdown, reboot, format, mkfs).
- **Motivo:** RN-7. Barreira contra contribuição acidental de template destrutivo.
  Pode ser integrada como teste de CI.

## Modelo: `PlannedRequest`

```python
@dataclass
class PlannedRequest:
    method: str
    url: str
    headers: dict[str, str]
    body: str | None
    template_id: str
    payload_value: str
    injection_point: str          # "query_param:name", "body_param:x", "path_segment:2"
    detection: DetectionRule
```

## Modelo: `ActiveConfig`

```python
@dataclass
class ActiveConfig:
    concurrency: int = 5          # 1-20
    rate_limit_rps: float = 10    # 1-50
    timeout_normal: float = 10.0
    timeout_time_based: float = 15.0
    confirmation_rounds: int = 2
    time_threshold_ms: int = 5000
```

## Estratégia de testes

| Nível | O que | Como |
|---|---|---|
| Unit: TemplateLoader | Parse YAML, validação de segurança | Templates de teste |
| Unit: InjectionPlanner | Geração de PlannedRequests | URL com params conhecidos |
| Unit: DetectionEngine | Avaliação time/content/status/diff | Responses mockadas |
| Unit: NucleiBridge | Parse de output JSON | Linhas JSON gravadas |
| Integration: engine | Categoria completa com mock transport | Fixture fim a fim |
| Integration: safety | Nenhum template contém pattern proibido | Script de validação |

## Rastreabilidade

| Requisito | Onde |
|---|---|
| S4-1 | `engine.py` (TemplateLoader, InjectionPlanner, DetectionEngine) |
| S4-2 | `sqli.py` + `templates/sqli/*.yaml` |
| S4-3 | `xss.py` + `templates/xss/*.yaml` |
| S4-4 | `cmdi.py` + `templates/cmdi/*.yaml` |
| S4-5 | `ssti.py` + `templates/ssti/*.yaml` |
| S4-6 | `traversal.py` + `templates/traversal/*.yaml` |
| S4-7 | `redirect.py` + `templates/redirect/*.yaml` |
| S4-8 | `idor.py` (lógica custom, sem template YAML) |
| S4-9 | `dir_enum.py` + `sensitive_files.py` + wordlist |
| S4-10 | `weak_auth.py` (lógica custom) |
| S4-11 | `bridge/nuclei.py` |
| S4-12 | `ui/scan_page.py` (category selection) |
| S4-13 | `controller.py` (per-category cancel) |
