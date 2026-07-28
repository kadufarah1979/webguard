# Tarefas — Motor de Testes Ativos

> Derivado de #[[file:design.md]]

## Pré-condições

- [ ] Sub-funcionalidade `01` concluída.
- [ ] Consentimento L-2 já implementado na UI (sub-01).

## Plano de execução

- [ ] 1. **ActiveConfig + PlannedRequest models**
  - Adicionar a `models.py`: `ActiveConfig`, `PlannedRequest`, `DetectionRule`
  - Type check passa
  - _Requisitos: fundação_

- [ ] 2. **TemplateLoader + validação de segurança**
  - Implementar parse de YAML, validação de campos obrigatórios
  - Implementar `validate_safety()` com regex de padrões proibidos
  - Testes: template válido, template com campo faltando, template com DROP
  - _Requisitos: S4-1.1, RN-7_

- [ ] 3. **InjectionPlanner**
  - Implementar geração de PlannedRequest a partir de template + URL
  - Suportar: query_params, body_params (form), path_segments
  - Testes: URL com 3 params → N planned requests por template
  - _Requisitos: S4-1.1_


- [ ] 4. **DetectionEngine**
  - Implementar avaliação: time, content (regex), status, diff
  - Implementar confirmation rounds para time-based
  - Testes: response com delay → detected, response rápida → not detected,
    response com SQL error regex → detected
  - _Requisitos: S4-1.2, S4-1.3, S4-1.4_

- [ ] 5. **PayloadEngine (orquestrador)**
  - Implementar `run_category()`: load → plan → execute → detect
  - Integrar com RequestGuard (modo ativo)
  - Implementar baseline request para time-based (ADL-8)
  - Testes: pipeline completo com mock transport
  - _Requisitos: S4-1.5, S4-1.6_

- [ ] 6. **Templates YAML — SQLi**
  - Criar `templates/sqli/time-based-mysql.yaml`
  - Criar `templates/sqli/time-based-postgres.yaml`
  - Criar `templates/sqli/error-based.yaml`
  - Criar `templates/sqli/boolean-based.yaml`
  - Implementar `analyzers/active/sqli.py`
  - Testes com fixtures: response lenta, response com SQL error, response diferenciada
  - _Requisitos: S4-2_

- [ ] 7. **Templates YAML — XSS**
  - Criar `templates/xss/reflected-basic.yaml`
  - Criar `templates/xss/reflected-context.yaml`
  - Implementar `analyzers/active/xss.py` com geração de marcador único
  - Testes: marcador refletido sem encoding, com encoding, em atributo
  - _Requisitos: S4-3_

- [ ] 8. **Templates YAML — Command Injection**
  - Criar `templates/cmdi/time-based-unix.yaml`
  - Criar `templates/cmdi/time-based-windows.yaml`
  - Implementar `analyzers/active/cmdi.py`
  - Testes: response lenta → detected
  - _Requisitos: S4-4_

- [ ] 9. **Templates YAML — SSTI**
  - Criar `templates/ssti/math-expressions.yaml`
  - Implementar `analyzers/active/ssti.py` com confirmação dupla
  - Testes: 49 na response → detectado, 56 confirma
  - _Requisitos: S4-5_

- [ ] 10. **Templates YAML — Path Traversal**
  - Criar `templates/traversal/unix.yaml`
  - Criar `templates/traversal/windows.yaml`
  - Implementar `analyzers/active/traversal.py`
  - Testes: response com root:x:0:0 → detected
  - _Requisitos: S4-6_


- [ ] 11. **Templates YAML — Open Redirect**
  - Criar `templates/redirect/open-redirect.yaml`
  - Implementar `analyzers/active/redirect.py`
  - Testes: 302 com Location externo → detected
  - _Requisitos: S4-7_

- [ ] 12. **IDOR analyzer**
  - Implementar `analyzers/active/idor.py` (lógica custom, sem template)
  - Detecção de segmentos numéricos + variação
  - Testes: URL com /123, respostas com IDs adjacentes
  - _Requisitos: S4-8_

- [ ] 13. **Enumeração de diretórios + arquivos sensíveis**
  - Implementar `analyzers/active/dir_enum.py`
  - Implementar `analyzers/active/sensitive_files.py`
  - Criar `data/wordlists/common.txt` (~500 paths)
  - Implementar custom 404 detection (ADL-9)
  - Testes: 200 para .git/config, 404 custom vs real, 403
  - _Requisitos: S4-9_

- [ ] 14. **Autenticação fraca**
  - Implementar `analyzers/active/weak_auth.py`
  - Detectar formulário de login no HTML (heurística)
  - Testar até 5 credenciais padrão
  - Testes: formulário detectado + login falhou, login com redirect (sucesso)
  - _Requisitos: S4-10_

- [ ] 15. **Nuclei bridge**
  - Implementar `bridge/nuclei.py`
  - Parse de output JSON line-by-line
  - Mapeamento para Finding
  - Testes: output gravado do nuclei real → Findings corretos
  - Teste de graceful handling quando nuclei não está instalado
  - _Requisitos: S4-11_

- [ ] 16. **UI — seleção de categorias**
  - Adicionar à scan_page: lista de checkboxes por categoria
  - Selecionar/limpar todas
  - Mostrar nuclei checkbox apenas se disponível
  - _Requisitos: S4-12_

- [ ] 17. **UI — progresso por categoria e cancelamento granular**
  - Mostrar status por categoria na lista de resultados
  - Botão cancelar por categoria
  - _Requisitos: S4-13_

- [ ] 18. **Validação de segurança dos templates (CI-ready)**
  - Script `scripts/validate_templates.py` que verifica todos os YAML
  - Rodar como parte do pytest (test_template_safety.py)
  - _Requisitos: RN-7_

- [ ] 19. **Verificação final**
  - Pipeline ativo completo com mock transport para cada categoria
  - Verificar rate limit no RequestLog
  - Verificar que nenhum template contém padrão destrutivo
  - Portões do Artigo III passam, cobertura ≥85%
  - _Requisitos: todos_

## Dependências

```
1 ──▶ 2 ──▶ 3 ──▶ 4 ──▶ 5
                         │
     6, 7, 8, 9, 10, 11 (paralelos, dependem de 5)
     12, 13, 14 (paralelos, dependem de 5)
     15 (independente, depende apenas de models)
     16, 17 (dependem de 5 + UI da sub-01)
     18 (depende de 6-11)
     19 (depende de todos)
```

## Registro de desvios

| Data | Tarefa | Desvio | Afeta o épico? | Documento corrigido? |
|---|---|---|---|---|
