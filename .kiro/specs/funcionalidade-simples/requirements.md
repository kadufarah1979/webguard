# Requisitos — `[NOME DA FUNCIONALIDADE]`

> **Fase 1 de 3 · O "Quê" e o "Porquê"**
> Escopo padrão: até 80h. Acima disso, use a estrutura de épico.
>
> Este documento descreve **comportamento observável**. Nenhuma menção a classe, tabela,
> biblioteca ou endpoint — isso é assunto do `design.md`.
>
> **Portão:** não avance para o design sem aprovação humana explícita deste arquivo.

## Status

| Campo | Valor |
|---|---|
| Fase | `Rascunho` / `Em revisão` / `Aprovado` |
| Estimativa | `TODO h` |
| Aprovado por | `TODO` |
| Data | `TODO` |

## Introdução

`TODO — 3 a 5 frases. Que problema real existe hoje, quem sofre com ele, e o que muda
quando esta funcionalidade existir. Escreva para alguém que não conhece o código.`

## Objetivo de negócio

`TODO — por que agora? Qual métrica se move?`

## Fora de escopo

Declarar o que **não** será feito é o que impede o escopo de crescer no meio da implementação.

- `TODO`
- `TODO`

## Glossário

| Termo | Definição |
|---|---|
| `TODO` | `TODO` |

## Requisitos

Formato **EARS**: cada critério é uma condição verificável, não uma opinião.
`SHALL` = obrigatório. Um critério que não pode ser testado não é um critério.

### Requisito 1 — `[Título curto]`

**História de usuário:** Como `[papel]`, quero `[capacidade]`, para que `[benefício]`.

#### Critérios de aceitação

1. QUANDO `[evento/gatilho]` ENTÃO o sistema DEVE `[resposta observável]`
2. SE `[condição de exceção]` ENTÃO o sistema DEVE `[tratamento]`
3. ENQUANTO `[estado contínuo]` o sistema DEVE `[comportamento mantido]`
4. ONDE `[contexto/plataforma específica]` o sistema DEVE `[adaptação]`

### Requisito 2 — `[Título curto]`

**História de usuário:** Como `[papel]`, quero `[capacidade]`, para que `[benefício]`.

#### Critérios de aceitação

1. QUANDO `TODO` ENTÃO o sistema DEVE `TODO`
2. SE `TODO` ENTÃO o sistema DEVE `TODO`

## Requisitos não funcionais

Só inclua o que tem número. "Deve ser rápido" não é requisito.

- **Desempenho:** `TODO — ex.: p95 abaixo de 300ms com 50 req/s`
- **Segurança:** herda a Cláusula Pétrea de #[[file:../../constitution.md]] e adiciona: `TODO`
- **Acessibilidade:** `TODO — ex.: WCAG 2.1 AA nos fluxos novos`
- **Observabilidade:** `TODO — o que precisa ser medido em produção`
- **Compatibilidade:** `TODO — navegadores, versões, dispositivos`

## Perguntas abertas

Ambiguidade registrada aqui é ambiguidade que não vira bug depois.

| # | Pergunta | Responsável | Status |
|---|---|---|---|
| 1 | `TODO` | `TODO` | Aberta |

## Critério de conclusão da funcionalidade

Esta funcionalidade está pronta quando:

- [ ] Todos os critérios de aceitação acima são verificáveis e verificados.
- [ ] Nenhuma pergunta aberta permanece em aberto.
- [ ] Os portões do Artigo III da constituição passam.
