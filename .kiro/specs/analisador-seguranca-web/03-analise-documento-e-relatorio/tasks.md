# Tarefas — Análise do Documento e Relatório

> Derivado de #[[file:design.md]]

## Pré-condições

- [ ] Sub-funcionalidade `01` concluída.

## Plano de execução

- [ ] 1. **Analisador CORS**
  - Implementar `analyzers/passive/cors.py`
  - Modificar collector para enviar `Origin: https://evil.example` no request
  - Testes: ACAO *, ACAO refletido, ACAO + credentials, sem CORS
  - _Requisitos: S3-1_

- [ ] 2. **Analisador SRI**
  - Implementar `analyzers/passive/sri.py`
  - Testes: script externo sem integrity, com integrity, mesmo domínio
  - _Requisitos: S3-2_

- [ ] 3. **Analisador de conteúdo misto**
  - Implementar `analyzers/passive/mixed_content.py`
  - Testes: script http://, imagem http://, tudo https://, site http://
  - _Requisitos: S3-3_

- [ ] 4. **Analisador de banners e source maps**
  - Implementar `analyzers/passive/banners.py`
  - Testes: Server com versão, Server sem versão, sourceMappingURL presente
  - _Requisitos: S3-4_

- [ ] 5. **Analisador de bibliotecas JS**
  - Implementar `analyzers/passive/js_libs.py`
  - Criar `data/js_vulns.json` com pelo menos 5 bibliotecas (jQuery, Angular, React,
    Bootstrap, Lodash) e suas CVEs conhecidas
  - Testes: jQuery 3.5.0 detectado → CVE, jQuery 3.7.1 → limpo, versão não detectável
  - _Requisitos: S3-5_

- [ ] 6. **Detecção de site SPA (aviso JS)**
  - Implementar heurística em `js_libs.py` ou módulo dedicado
  - Testes: HTML com React root e quase vazio, HTML normal com conteúdo
  - _Requisitos: S3-7_

- [ ] 7. **Exportador Markdown**
  - Implementar `exporters/markdown.py`
  - Testes: golden file com achados conhecidos
  - _Requisitos: S3-6.1_

- [ ] 8. **Exportador JSON**
  - Implementar `exporters/json_export.py`
  - Testes: schema válido, campos presentes, version "1.0"
  - _Requisitos: S3-6.2_

- [ ] 9. **Exportador HTML**
  - Implementar `exporters/html_export.py`
  - Testes: HTML válido, CSS embutido, âncoras de severidade funcionam
  - _Requisitos: S3-6.3_

- [ ] 10. **UI — botão de exportar + file chooser**
  - Adicionar `GtkFileDialog` à scan_page com seleção de formato
  - Conectar aos exportadores
  - Testes: botão desabilitado antes da análise, habilitado depois
  - _Requisitos: S3-6.4, S3-6.5_

- [ ] 11. **Verificação final**
  - Pipeline com fixtures HTML ricas (scripts externos, cookies, mixed content)
  - Exportar nos 3 formatos e verificar
  - Portões do Artigo III passam, cobertura ≥85%
  - _Requisitos: todos_

## Dependências

```
1, 2, 3, 4, 5, 6 (paralelos entre si)
7, 8, 9 (paralelos entre si)
10 depende de 7+8+9
11 depende de todos
```

## Registro de desvios

| Data | Tarefa | Desvio | Afeta o épico? | Documento corrigido? |
|---|---|---|---|---|
