---
inclusion: manual
---

# Produto e Stack

> **Pasta `always/` — diretriz global injetada em toda chamada.**
> Ao preencher, troque o front-matter para `inclusion: always`.
> Enquanto estiver cheio de `TODO`, mantenha `manual` para não poluir o contexto.
>
> Cada palavra aqui é paga em toda interação. Seja brutalmente conciso: se passar de
> ~50 linhas, algo aqui pertence a `auto/` ou `conditional/`.

## O produto em uma frase

`TODO — o que é, para quem, resolvendo o quê.`

## Stack

| Camada | Tecnologia | Versão |
|---|---|---|
| Linguagem | `TODO` | `TODO` |
| Runtime | `TODO` | `TODO` |
| Framework | `TODO` | `TODO` |
| Banco | `TODO` | `TODO` |
| Testes | `TODO` | `TODO` |
| Gerenciador de pacotes | `TODO` | `TODO` |

## Comandos

Sempre use estes comandos; não invente variações.

```bash
TODO   # instalar dependências
TODO   # rodar em desenvolvimento
TODO   # testes (modo single-run, nunca watch)
TODO   # lint
TODO   # type check
TODO   # build
```

## Estrutura de pastas

```
TODO — apenas os diretórios que importam para decidir onde um arquivo novo vai.
```

## Convenções não negociáveis do dia a dia

- `TODO — ex.: nunca criar arquivo em src/ sem teste correspondente.`
- `TODO — ex.: toda entrada externa validada com zod na borda.`
- `TODO — ex.: erros de domínio como tipos, não strings.`

## Fluxo esperado do agente

1. Specs em `.kiro/specs/` antes de implementar.
2. A constituição (`.kiro/constitution.md`) tem autoridade final.
3. Pedir confirmação antes de instalar dependência, alterar schema ou tocar em CI/CD.
