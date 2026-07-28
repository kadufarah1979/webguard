---
inclusion: manual
---

# Runbook Operacional

> **Pasta `manual/` — inclusão sob demanda feita pelo desenvolvedor.**
> Este arquivo já está no modo correto: `inclusion: manual`. Custo zero de contexto até
> alguém referenciá-lo explicitamente na conversa.
>
> É o lugar certo para procedimentos longos, detalhados e usados raramente — exatamente o
> tipo de conteúdo que não deve competir por espaço no contexto do dia a dia.

## Procedimentos deste arquivo

| Procedimento | Quando usar |
|---|---|
| Deploy | `TODO` |
| Rollback | `TODO` |
| Migração de banco | `TODO` |
| Investigação de incidente | `TODO` |

## Deploy

**Pré-condições:**

- [ ] Portões do Artigo III da constituição passando na branch.
- [ ] `TODO`

**Passos:**

```bash
TODO   # 1.
TODO   # 2.
```

**Verificação pós-deploy:** `TODO — o que olhar, por quanto tempo, qual sinal indica falha.`

## Rollback

**Gatilho para acionar:** `TODO — critério objetivo, decidido antes do incidente, não durante.`

```bash
TODO
```

**Cuidado com dados:** `TODO — o rollback do código reverte a migração? Se não, o que fazer?`

## Migração de banco

- **Antes:** backup verificado (`TODO — comando e como confirmar que o backup é válido`).
- **Aplicar:** `TODO`
- **Reverter:** `TODO`
- **Migração destrutiva** (drop de coluna/tabela) exige aprovação humana explícita e
  janela combinada. O agente nunca executa isso por iniciativa própria.

## Investigação de incidente

1. `TODO — onde estão os logs.`
2. `TODO — quais métricas/dashboards olhar primeiro.`
3. `TODO — como reproduzir localmente.`
4. Registrar a causa raiz e criar spec de correção em `.kiro/specs/`.

---

## Outros arquivos que pertencem a esta pasta

`onboarding.md` · `troubleshooting.md` · `release.md` · `auditoria-seguranca.md` ·
`recuperacao-desastre.md`
