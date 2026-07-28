# Tarefas — Núcleo e Análise de Cabeçalhos

> **Plano de execução derivado de** #[[file:design.md]]
>
> Uma tarefa por vez. Verificação entre cada uma.

## Pré-condições

- [ ] `epic-design.md` aprovado.
- [ ] Ambiente de desenvolvimento configurado (Python 3.12, GTK4, libadwaita).

## Plano de execução

- [x] 1. **Scaffold do projeto**
  - Criar `pyproject.toml` com dependências, scripts, configuração de ruff/mypy/pytest
  - Criar estrutura de pastas conforme epic-design (src/webguard/*, tests/*)
  - Criar `src/webguard/__init__.py` com `__version__`
  - Verificar que `ruff check`, `mypy`, `pytest` rodam sem erro (vazio)
  - _Requisitos: fundação técnica, nenhum requisito funcional específico_

- [x] 2. **Models (dataclasses compartilhados)**
  - Implementar `models.py`: `ScanRecord`, `Finding`, `TLSInfo`, `CertInfo`, `CookieInfo`,
    `RequestLog`, `ScanContext`, `CollectError`, `Mode` (enum), `RateLimiter`
  - Testes unitários: instanciação, frozen, serialização para dict
  - Type check passa
  - _Requisitos: fundação para L-5, L-6_

- [x] 3. **RequestGuard**
  - Implementar `guard.py`: `RequestGuard` com `is_allowed()`, `request()`, logging
  - Testes unitários: permite URL do mesmo host, bloqueia URL externa, respeita modo,
    registra no log, bloqueia e registra violação
  - Sem rede nos testes (mock transport)
  - _Requisitos: S1-3.1, S1-3.3, S1-6.3, L-1_

- [x] 4. **Collector**
  - Implementar `collector.py`: `Collector.collect()` com redirect, timeout, truncamento
  - Testes: segue redirect, para em 10 hops, timeout retorna CollectError,
    body truncado em 2MB, registra cada RequestLog
  - Mock transport (sem rede)
  - _Requisitos: S1-3.2, S1-3.4, S1-3.5, S1-3.6_

- [x] 5. **Registry de analisadores**
  - Implementar `registry.py`: decorador `@analyzer`, `get_analyzers(mode)`
  - Testes: decorar função, recuperar por modo, isolar por modo
  - _Requisitos: fundação para ADE-2_

- [x] 6. **Controller**
  - Implementar `controller.py`: `ScanController` com thread worker, asyncio loop,
    callback `on_finding`/`on_progress`/`on_done`/`on_error`, cancelamento
  - Testes: mock collector + mock analyzer → verifica sequência de callbacks,
    cancelamento interrompe dentro de 2s
  - _Requisitos: S1-7, L-8, L-9_

- [x] 7. **Analisador de cabeçalhos**
  - Implementar `analyzers/passive/headers.py`: decorado com `@analyzer(mode="passive")`
  - Implementar verificação dos 10 cabeçalhos listados em S1-4
  - Implementar parser de CSP e avaliação por diretiva
  - Testes por cabeçalho: ausente → finding, presente correto → sem finding,
    malconfigurado → finding com evidência específica
  - Testes CSP: unsafe-inline, unsafe-eval, wildcard, object-src ausente,
    CSP completa e correta → informativo
  - _Requisitos: S1-4.1, S1-4.2, S1-4.3, S1-4.4, S1-4.5_

- [ ] 8. **UI — Shell da aplicação + tema hacker**
  - Implementar `app.py`: `Gtk.Application` com `AdwApplicationWindow`
  - Implementar `window.py`: `AdwViewStack` com páginas Scan e Log
  - Criar `style.css`: paleta hacker (bg #0D1117, accent-green #00FF41, etc.)
  - Forçar dark mode: `Adw.StyleManager.set_color_scheme(FORCE_DARK)`
  - Carregar JetBrains Mono como fonte global via CSS
  - Implementar `widgets/ascii_banner.py`: logo Unicode no topo
  - Implementar `widgets/typing_label.py`: revelação caractere a caractere
  - Implementar `widgets/hacker_progress.py`: barra com `■░`
  - Verificar que a aplicação abre com visual hacker sem erro
  - _Requisitos: fundação visual, visual-identity.md_

- [ ] 9. **UI — Página de scan (estilo terminal)**
  - Implementar `scan_page.py`: campo de URL com prompt `➜ TARGET:` em verde,
    cursor bloco piscante, validação inline com borda vermelha
  - Switch de modo: `PASSIVE` (cyan) / `ACTIVE` (vermelho) com uppercase
  - Grid de categorias com `[✓]`/`[ ]` customizados (modo ativo)
  - Dialog de consentimento (L-2): bordas duplas Unicode, checkbox obrigatório
  - Botão `▶ INICIAR VARREDURA` verde inversão / `■ ABORTAR` vermelho
  - Progresso: `■░` + etapas `[✓]`/`[-]`/`[ ]` + typing effect
  - Achados em `AdwExpanderRow` com tag severidade colorida, seções
    EVIDENCE/RISK/FIX, bloco copiável, animação fade-in
  - Conectar ao `ScanController`
  - _Requisitos: S1-1, S1-2, S1-5, S1-7, visual-identity.md_

- [ ] 10. **UI — Página de log (estilo htop)**
  - Implementar `log_page.py`: tabela mono alinhada TIME|METHOD|URL|STATUS|ELAPSED
  - Status colorido: 2xx verde, 3xx cyan, 4xx amarelo, 5xx vermelho
  - Linhas bloqueadas: `✗ BLOCKED` em vermelho
  - Painel de detalhes ao clicar (headers enviados)
  - _Requisitos: S1-6.1, S1-6.2, S1-6.3, visual-identity.md_

- [ ] 11. **Integração e verificação final**
  - Executar pipeline completo com collector mockado: URL → achados → UI
  - Verificar todos os critérios S1-* com fixtures
  - Rodar portões: `ruff check && ruff format --check && mypy src/ && pytest --cov`
  - Confirmar cobertura ≥85% na camada core + analyzers
  - Teste manual: abrir aplicação, analisar um site real, verificar achados
  - _Requisitos: todos_

## Dependências

```
1 ──▶ 2 ──▶ 3 ──▶ 4 ──▶ 5 ──▶ 6 ──▶ 7
                                      │
8 ──────────────────────────────────▶ 9 ──▶ 10 ──▶ 11
```

Tarefas 1-7 (backend) e 8 (UI shell) podem ser paralelas.
Tarefa 9 depende de 6 (controller) e 8 (shell).

## Registro de desvios

| Data | Tarefa | Desvio | Afeta o épico? | Documento corrigido? |
|---|---|---|---|---|
