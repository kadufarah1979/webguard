---
inclusion: manual
---

# Domínio e Glossário

> **Pasta `auto/` — injeção semântica por similaridade.**
> Ao preencher, troque o front-matter para `inclusion: auto`.
>
> Este arquivo entra no contexto quando a conversa **se parece** com o assunto dele. Por isso
> vale escrever com os termos exatos que aparecem nas conversas reais do time — a
> recuperação depende dessa correspondência semântica.

## Como escrever para recuperação semântica

- Use o vocabulário do negócio, não paráfrases genéricas.
- Um arquivo por área de domínio. Um arquivo que fala de tudo é recuperado para tudo, e aí
  o modo `auto/` perde a função.
- Inclua sinônimos que o time usa na prática — é assim que a similaridade acerta.

## Glossário do domínio

| Termo | Significado no negócio | Como aparece no código | Não confundir com |
|---|---|---|---|
| `TODO` | `TODO` | `TODO` | `TODO` |
| `TODO` | `TODO` | `TODO` | `TODO` |

## Entidades principais

### `[Entidade]`

- **O que representa:** `TODO`
- **Ciclo de vida:** `TODO — estados possíveis e transições válidas.`
- **Invariantes:** `TODO — o que precisa ser sempre verdade, sob qualquer circunstância.`
- **Quem pode alterar:** `TODO`

## Regras de negócio

Documente a regra **e o motivo**. Regra sem motivo é reescrita por engano na primeira
refatoração.

### RN-1 — `[Nome]`

- **Regra:** `TODO`
- **Por que existe:** `TODO`
- **Consequência de violar:** `TODO`

## Decisões já tomadas

Evita reabrir discussão encerrada.

| Decisão | Quando | Motivo | Alternativa descartada |
|---|---|---|---|
| `TODO` | `TODO` | `TODO` | `TODO` |

## Armadilhas conhecidas

`TODO — o que parece bug mas é comportamento intencional; o que já quebramos antes.`
