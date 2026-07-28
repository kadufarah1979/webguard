# Requisitos Locais — TLS, Cookies e Transporte

> **Sub-funcionalidade 02 do épico Analisador de Segurança Web**
>
> Herança: #[[file:../epic-requirements.md]]

## Status

| Campo | Valor |
|---|---|
| Fase | `Em revisão` |
| Estimativa | ~28h |
| Depende de | `01-nucleo-e-cabecalhos` |
| Aprovado por | `PENDENTE` |

## Herança do épico

- **Leis globais herdadas:** L-1 a L-9
- **Regras transversais:** RN-1 a RN-6
- **Requisitos épicos atendidos:** E-1 (parcial — famílias adicionais)
- **Restrições adicionais:** nenhuma

## Introdução

Adiciona três famílias de análise passiva sobre a infraestrutura criada na sub-01:
certificado TLS e versões de protocolo, atributos de cookies, e cadeia de redirecionamento
HTTP→HTTPS.

## Fora de escopo

- Verificação de revogação (OCSP, CRL) — exigiria requisição a terceiros, viola L-4.
- CT log check — mesma razão.
- Avaliação de cipher suites (complexidade alta, valor marginal para uso pessoal).

## Requisitos

### Requisito S2-1 — Análise de certificado TLS

**História de usuário:** Como desenvolvedor, quero saber se meu certificado tem problemas
antes que expire ou seja rejeitado por browsers.

#### Critérios de aceitação

1. QUANDO a conexão TLS é estabelecida ENTÃO o analisador DEVE verificar:
   - Validade: certificado não expirado
   - Expiração próxima: menos de 30 dias para expirar → `Média`
   - SAN: hostname da URL presente nos Subject Alternative Names
   - Cadeia: cadeia completa até root reconhecida
   - Algoritmo de assinatura: SHA-1 ou MD5 → `Alta`
   - Versão do certificado: v3
2. QUANDO o certificado está expirado ENTÃO DEVE emitir `Crítica` com data de expiração.
3. QUANDO o hostname não está nos SANs ENTÃO DEVE emitir `Alta` com CN e SANs listados.
4. QUANDO tudo está correto DEVE emitir `Informativo` com validade restante.

### Requisito S2-2 — Versões de protocolo TLS

**História de usuário:** Como desenvolvedor, quero saber se meu servidor aceita versões
inseguras de TLS.

#### Critérios de aceitação

1. QUANDO a análise executa ENTÃO o analisador DEVE tentar handshake com TLS 1.0, 1.1,
   1.2 e 1.3 contra o mesmo host.
2. SE TLS 1.0 ou 1.1 é aceito ENTÃO DEVE emitir `Alta` com o protocolo aceito como evidência.
3. SE apenas TLS 1.2+ é aceito DEVE emitir `Informativo` confirmando.
4. QUANDO TLS 1.3 não é aceito DEVE emitir `Baixa` como recomendação.

### Requisito S2-3 — Análise de cookies

**História de usuário:** Como desenvolvedor, quero saber se meus cookies estão protegidos.

#### Critérios de aceitação

1. QUANDO a resposta contém `Set-Cookie` ENTÃO o analisador DEVE verificar cada cookie:
   - `Secure` ausente em HTTPS → `Alta`
   - `HttpOnly` ausente em cookie de sessão (heurística por nome) → `Alta`
   - `SameSite` ausente ou `None` sem Secure → `Média`
   - Escopo (`domain`) amplo demais (domínio pai desnecessário) → `Média`
   - Expiração longa sem justificativa (>1 ano) → `Baixa`
2. QUANDO um cookie não tem `Secure` em site HTTPS ENTÃO a evidência DEVE mostrar o
   nome do cookie e os atributos presentes.
3. QUANDO todos os cookies estão corretos DEVE emitir `Informativo`.
4. QUANDO não há cookies DEVE emitir `Informativo` indicando que nenhum cookie foi setado.

### Requisito S2-4 — Cadeia de redirect e HSTS

**História de usuário:** Como desenvolvedor, quero saber se a transição HTTP→HTTPS está
correta e se HSTS está configurado.

#### Critérios de aceitação

1. QUANDO a URL usa HTTPS ENTÃO o analisador DEVE verificar se a versão HTTP (porta 80)
   redireciona para HTTPS com status 301 (não 302).
2. SE HTTP não redireciona para HTTPS ENTÃO DEVE emitir `Alta`.
3. SE redireciona com 302 em vez de 301 ENTÃO DEVE emitir `Média` (não é cacheável).
4. QUANDO HSTS está presente DEVE verificar `max-age` (mínimo recomendado: 1 ano =
   31536000).
5. SE HSTS `max-age` < 1 ano ENTÃO DEVE emitir `Baixa` com valor atual e recomendado.
6. QUANDO há cadeia de redirects > 3 hops DEVE emitir `Baixa` informativa.

## Requisitos não funcionais locais

- Handshakes TLS adicionais (S2-2) não devem exceder 10s no total.
- Análise de cookies é O(n) com n = número de cookies; sem limite prático.

## Critério de conclusão

- [ ] Todos os critérios S2-* verificados com fixtures.
- [ ] Handshakes TLS testados com mock (sem rede real na suíte).
- [ ] Portões do Artigo III passam.
