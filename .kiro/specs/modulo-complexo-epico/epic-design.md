# Design do Épico — `[NOME DO MÓDULO]`

> **Arquitetura macro do módulo**
>
> Define as estruturas compartilhadas — banco, contratos de fronteira, padrões
> transversais — que todas as sub-funcionalidades consomem. Decisão que afeta mais de uma
> sub-funcionalidade pertence a este documento; decisão local pertence ao `design.md` da
> sub-funcionalidade.
>
> Base: #[[file:epic-requirements.md]]

## Status

| Campo | Valor |
|---|---|
| Fase | `Rascunho` / `Em revisão` / `Aprovado` |
| Aprovado por | `TODO` |

## Visão arquitetural

```
TODO — diagrama macro. Mostre as sub-funcionalidades como blocos, o que elas
compartilham, e onde ficam as fronteiras do módulo.

Ex.:
  ┌─────────────────── Módulo ───────────────────┐
  │  sub-func-1        sub-func-2                │
  │      │                 │                    │
  │      └──────┬──────────┘                    │
  │        Núcleo compartilhado                  │
  │        (entidades, contratos, políticas)     │
  └──────────────────┬───────────────────────────┘
                     ▼
              Persistência / serviços externos
```

## Decisões arquiteturais do épico

### ADE-1 — `[Decisão]`

- **Contexto:** `TODO`
- **Decisão:** `TODO`
- **Alternativas descartadas:** `TODO — e por quê.`
- **Consequências para as sub-funcionalidades:** `TODO`
- **Rastreia:** Requisito `E-TODO` / Lei `L-TODO`

### ADE-2 — `[Decisão]`

- **Contexto:** `TODO`
- **Decisão:** `TODO`
- **Alternativas descartadas:** `TODO`
- **Consequências:** `TODO`

## Modelo de dados compartilhado

O schema do módulo vive aqui. Uma sub-funcionalidade **não** cria tabela sem que ela seja
registrada neste documento.

```
TODO — entidades, relações, índices, constraints.
```

### Estratégia de migração

- **Ordem:** `TODO — quais migrações precisam existir antes de qual sub-funcionalidade.`
- **Compatibilidade durante a transição:** `TODO`
- **Rollback:** `TODO`

## Contratos de fronteira

O que o módulo expõe para fora. Mudança aqui é mudança quebradiça — versione.

```
TODO — interfaces públicas, eventos publicados, formato das mensagens.
```

| Contrato | Tipo | Consumidor | Versionamento |
|---|---|---|---|
| `TODO` | API / evento | `TODO` | `TODO` |

## Núcleo compartilhado

Componentes que mais de uma sub-funcionalidade usa. Construídos **uma vez**, aqui.

| Componente | Responsabilidade | Usado por |
|---|---|---|
| `TODO` | `TODO` | `sub-func-1`, `sub-func-2` |

## Padrões transversais obrigatórios

Como cada lei global é implementada na prática, para que as sub-funcionalidades não
inventem soluções divergentes.

| Lei | Mecanismo de implementação |
|---|---|
| L-1 | `TODO` |
| L-2 | `TODO` |

- **Tratamento de erro:** `TODO — padrão único do módulo.`
- **Autorização:** `TODO — onde o guard vive, como é aplicado.`
- **Observabilidade:** `TODO — convenção de nomes de métrica e log.`

## Estratégia de testes do módulo

- **O que é testado no nível do épico:** `TODO — integração entre sub-funcionalidades, fluxo ponta a ponta.`
- **O que fica para cada sub-funcionalidade:** `TODO`
- **Ambiente e dados de teste compartilhados:** `TODO`

## Sequenciamento

```
epic-design (este documento) ──▶ núcleo compartilhado ──▶ sub-func-1 ──▶ sub-func-2
```

O núcleo compartilhado precisa existir antes da primeira sub-funcionalidade. Construir
sub-funcionalidade contra um núcleo inexistente gera retrabalho garantido.

## Rastreabilidade

| Requisito épico / Lei | Onde é atendido |
|---|---|
| E-1 | `TODO` |
| L-1 | `TODO` |
