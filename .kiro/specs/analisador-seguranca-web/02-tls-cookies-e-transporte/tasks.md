# Tarefas — TLS, Cookies e Transporte

> Derivado de #[[file:design.md]]

## Pré-condições

- [ ] Sub-funcionalidade `01` concluída (models, guard, collector, controller, registry).

## Plano de execução

- [ ] 1. **Expandir o Collector para TLS e cookies**
  - Popular `ScanRecord.tls` com `TLSInfo` extraído via ssl
  - Popular `ScanRecord.cookies` com `CookieInfo[]` extraído do httpx
  - Testes: fixture com cert chain mockado, fixture com Set-Cookie
  - _Requisitos: fundação para S2-1, S2-3_

- [ ] 2. **Implementar TLS probe**
  - `tls_probe.py`: testa TLS 1.0, 1.1, 1.2, 1.3 via ssl.SSLContext
  - Chamado pelo collector após obter resposta
  - Testes: mock de socket que aceita/recusa por versão
  - _Requisitos: S2-2_

- [ ] 3. **Analisador de certificado TLS**
  - `analyzers/passive/tls.py`
  - Verifica: expiração, SAN, cadeia, algoritmo, proximidade de expirar
  - Testes: cert expirado, cert bom, cert com SHA-1, hostname não bate
  - _Requisitos: S2-1_

- [ ] 4. **Analisador de cookies**
  - `analyzers/passive/cookies.py`
  - Verifica: Secure, HttpOnly, SameSite, escopo, expiração longa
  - Heurística de sessão por nome
  - Testes: cookie sem Secure, cookie perfeito, cookie de sessão sem HttpOnly
  - _Requisitos: S2-3_

- [ ] 5. **Analisador de transporte (redirect + HSTS)**
  - `analyzers/passive/transport.py`
  - Emite GET http:// via guard (permitido: mesmo host)
  - Verifica: 301 vs 302, HSTS max-age, cadeia longa
  - Testes: redirect correto, redirect 302, sem redirect, HSTS curto
  - _Requisitos: S2-4_

- [ ] 6. **Verificação final**
  - Pipeline completo com collector mockado incluindo TLS e cookies
  - Portões do Artigo III passam
  - Cobertura mantém ≥85%
  - _Requisitos: todos_

## Dependências

```
1 ──▶ 2 ──▶ 3
1 ──▶ 4
5 (independente, usa guard existente)
3 + 4 + 5 ──▶ 6
```

## Registro de desvios

| Data | Tarefa | Desvio | Afeta o épico? | Documento corrigido? |
|---|---|---|---|---|
