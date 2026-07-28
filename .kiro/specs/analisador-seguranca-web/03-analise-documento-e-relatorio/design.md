# Design Local — Análise do Documento e Relatório

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
| ADE-2 (registry) | Registra 5-6 novos analisadores passivos |
| ADE-6 (Finding) | Todos os achados seguem o formato |
| Exporters (epic-design) | Implementa os 3 formatos |

## Componentes

### `webguard.analyzers.passive.cors`

Verifica `Access-Control-Allow-Origin` e `Access-Control-Allow-Credentials` na resposta.
Para detecção de reflexão (S3-1.2), o collector já envia `Origin: https://evil.example` na
requisição — isso está dentro de L-1 (é a URL informada, apenas com header adicional).

### `webguard.analyzers.passive.sri`

Parseia HTML com BeautifulSoup, encontra `<script>` e `<link>` com domínio diferente,
verifica presença de `integrity`.

### `webguard.analyzers.passive.mixed_content`

Parseia HTML, encontra src/href/action com `http://` quando a página é HTTPS. Classifica
active vs passive content.

### `webguard.analyzers.passive.banners`

Verifica headers `Server`, `X-Powered-By`, `X-AspNet-Version`. Verifica
`sourceMappingURL` no HTML e nos headers de resposta.

### `webguard.analyzers.passive.js_libs`

Estratégia de detecção de versão:
1. Regex em URLs de CDN conhecidas (`/jquery-3.6.1.min.js`, etc.)
2. Regex no conteúdo inline (variáveis de versão comuns)
3. Lookup na base `data/js_vulns.json`

Formato da base:
```json
{
  "jquery": {
    "versions": {
      "3.5.0": [{"cve": "CVE-2020-11022", "severity": "medium", "fixed": "3.5.1"}]
    },
    "detection_patterns": ["jquery[-.]?(\\d+\\.\\d+\\.\\d+)"]
  }
}
```

### `webguard.exporters.markdown`

Template Jinja2-like (f-strings ou `string.Template` para evitar dep):
- Cabeçalho com metadata
- Seção por severidade
- Cada achado com evidência em code block

### `webguard.exporters.json_export`

```python
def export_json(findings: list[Finding], metadata: ScanMetadata) -> str:
    return json.dumps({"version": "1.0", "metadata": ..., "findings": [...]}, indent=2)
```

### `webguard.exporters.html_export`

HTML autocontido com CSS embutido. Tabela de resumo + detalhes por achado. Navegação por
âncora por severidade.

## Decisões locais

### ADL-6 — CORS reflection check com Origin header

- **Decisão:** enviar `Origin: https://evil.example` na requisição de coleta para testar
  se ACAO reflete.
- **Justificativa:** é uma requisição normal com um header a mais (como qualquer browser
  cross-origin faria). Cabe em L-1 item 1.

### ADL-7 — Base de JS vulns derivada do Retire.js

- **Decisão:** converter o repositório Retire.js (MIT) para formato próprio simplificado.
- **Justificativa:** Retire.js é MIT, permite derivação. Formato próprio evita dep de
  runtime e reduz tamanho. Atualização é `make update-js-vulns` (script de conversão).

## Rastreabilidade

| Requisito | Onde |
|---|---|
| S3-1 | `cors.py` |
| S3-2 | `sri.py` |
| S3-3 | `mixed_content.py` |
| S3-4 | `banners.py` |
| S3-5 | `js_libs.py` |
| S3-6 | `exporters/{markdown,json_export,html_export}.py` |
| S3-7 | `js_libs.py` (ou analisador dedicado `spa_detection.py`) |
