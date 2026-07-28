# Requisitos do Épico — `[NOME DO MÓDULO]`

> **Regras globais do módulo · Épico acima de 80h**
>
> Este documento estabelece as **leis** que toda sub-funcionalidade deste módulo herda e
> obedece. Ele não descreve telas nem fluxos específicos — descreve o que é verdade em
> **todo** o módulo, sempre.
>
> Uma sub-funcionalidade pode adicionar restrições. Nunca pode remover ou contradizer as
> daqui. Se precisar contradizer, este documento está errado e é corrigido primeiro.

## Status

| Campo | Valor |
|---|---|
| Fase | `Rascunho` / `Em revisão` / `Aprovado` |
| Estimativa total | `TODO h` |
| Sub-funcionalidades | `TODO` |
| Aprovado por | `TODO` |

## Introdução

`TODO — que capacidade de negócio este módulo inteiro entrega, e por que ela é grande
demais para uma spec única.`

## Fronteira do módulo

Definir a fronteira é o que evita o épico virar "onde colocamos tudo que sobrou".

- **Este módulo é responsável por:** `TODO`
- **Este módulo NÃO é responsável por:** `TODO`
- **Consome de outros módulos:** `TODO`
- **Expõe para outros módulos:** `TODO`

## Leis globais

Numeradas para serem citadas diretamente pelas sub-funcionalidades (`herda L-1`).

### L-1 — `[Nome da lei]`

`TODO — ex.: "Toda operação que altera saldo é registrada em log de auditoria imutável,
sem exceção, inclusive em falha."`

### L-2 — `[Nome da lei]`

`TODO — ex.: "Nenhum dado deste módulo cruza a fronteira sem passar pelo serializador
que remove campos sensíveis."`

### L-3 — `[Nome da lei]`

`TODO`

## Regras de negócio transversais

| # | Regra | Vale para |
|---|---|---|
| RN-1 | `TODO` | Todas as sub-funcionalidades |
| RN-2 | `TODO` | `TODO` |

## Requisitos de nível épico

Requisitos que **nenhuma** sub-funcionalidade sozinha atende — eles emergem do módulo inteiro.

### Requisito E-1 — `[Título]`

**História de usuário:** Como `[papel]`, quero `[capacidade do módulo]`, para que `[benefício]`.

#### Critérios de aceitação

1. QUANDO `TODO` ENTÃO o sistema DEVE `TODO`
2. SE `TODO` ENTÃO o sistema DEVE `TODO`

### Requisito E-2 — `[Título]`

#### Critérios de aceitação

1. QUANDO `TODO` ENTÃO o sistema DEVE `TODO`

## Requisitos não funcionais do módulo

Valem como piso para todas as sub-funcionalidades.

- **Desempenho:** `TODO`
- **Segurança:** herda #[[file:../../constitution.md]] e adiciona: `TODO`
- **Auditoria:** `TODO`
- **Disponibilidade:** `TODO`

## Decomposição

Cada sub-funcionalidade deve ser entregável e verificável de forma independente.

| Sub-funcionalidade | Escopo em uma frase | Estimativa | Depende de |
|---|---|---|---|
| `sub-funcionalidade-1` | `TODO` | `TODO h` | — |
| `sub-funcionalidade-2` | `TODO` | `TODO h` | `sub-funcionalidade-1` |

**Ordem de entrega e por quê:** `TODO`

## Perguntas abertas

| # | Pergunta | Bloqueia qual sub-funcionalidade? | Status |
|---|---|---|---|
| 1 | `TODO` | `TODO` | Aberta |

## Critério de conclusão do épico

- [ ] Todas as sub-funcionalidades estão concluídas e verificadas.
- [ ] Os requisitos de nível épico (E-*) são verificáveis de ponta a ponta.
- [ ] Nenhuma lei global foi violada por nenhuma sub-funcionalidade.
