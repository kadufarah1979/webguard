# Design — `[NOME DA FUNCIONALIDADE]`

> **Fase 2 de 3 · Arquitetura técnica e contratos**
> Aqui entra o "Como". Todo elemento deste documento precisa rastrear para um requisito
> aprovado em #[[file:requirements.md]] — se não rastreia, é escopo inventado.
>
> **Portão:** não avance para as tarefas sem aprovação humana explícita deste arquivo.

## Status

| Campo | Valor |
|---|---|
| Fase | `Rascunho` / `Em revisão` / `Aprovado` |
| Requisitos base | `requirements.md` versão `TODO` |
| Aprovado por | `TODO` |

## Visão geral

`TODO — em um parágrafo: a estratégia técnica escolhida e o princípio que a organiza.`

## Decisões de arquitetura

A parte mais valiosa deste documento. Registre o que foi **descartado** e por quê — é isso
que impede a discussão de reabrir em três meses.

### AD-1 — `[Decisão]`

- **Contexto:** `TODO`
- **Decisão:** `TODO`
- **Alternativas descartadas:** `TODO — e o motivo de cada descarte.`
- **Consequências:** `TODO — inclusive as negativas que aceitamos.`
- **Rastreia:** Requisito `TODO`

### AD-2 — `[Decisão]`

- **Contexto:** `TODO`
- **Decisão:** `TODO`
- **Alternativas descartadas:** `TODO`
- **Consequências:** `TODO`
- **Rastreia:** Requisito `TODO`

## Arquitetura

```
TODO — diagrama em texto ou mermaid. Mostre o fluxo do dado, não a lista de pastas.

Ex.:
  Cliente ──▶ Controller ──▶ Serviço ──▶ Repositório ──▶ Banco
                  │              │
                  │              └──▶ Serviço externo
                  └──▶ Validação de entrada (borda)
```

## Componentes

### `[NomeDoComponente]`

- **Responsabilidade única:** `TODO`
- **Depende de:** `TODO`
- **Não faz:** `TODO — limite explícito, evita o componente virar um depósito.`
- **Rastreia:** Requisito `TODO`

## Contratos e interfaces

Assinaturas e formatos, não implementação.

```
TODO — tipos, interfaces, schema de request/response.

Se houver um contrato formal versionado, referencie em vez de duplicar:
#[[file:../../../docs/openapi.yaml]]
```

### Endpoints / eventos

| Método / Evento | Caminho | Entrada | Saída | Erros | Requisito |
|---|---|---|---|---|---|
| `TODO` | `TODO` | `TODO` | `TODO` | `TODO` | `TODO` |

## Modelo de dados

```
TODO — entidades, campos, tipos, obrigatoriedade, relações.
```

- **Migração necessária:** `sim / não` — se sim, descreva o caminho de ida **e** de volta.
- **Dados existentes:** `TODO — o que acontece com o que já está no banco?`

## Tratamento de erro

| Situação | Detecção | Resposta ao cliente | Log / métrica |
|---|---|---|---|
| Entrada inválida | `TODO` | `TODO` | `TODO` |
| Dependência indisponível | `TODO` | `TODO` | `TODO` |
| Falha inesperada | `TODO` | Mensagem genérica, sem detalhe interno | `TODO` |

## Segurança do design

- **Autenticação:** `TODO`
- **Autorização:** `TODO — qual verificação, em que camada, por qual recurso.`
- **Dados sensíveis:** `TODO — o que é sensível aqui, como é protegido em trânsito e em repouso.`
- **Superfície nova exposta:** `TODO`

## Estratégia de testes

| Nível | O que cobre | Requisito verificado |
|---|---|---|
| Unitário | `TODO` | `TODO` |
| Integração | `TODO` | `TODO` |
| Ponta a ponta | `TODO` | `TODO` |

**Casos de borda que precisam de teste:** `TODO — vazio, nulo, limite, concorrência, duplicidade.`

## Impacto no que já existe

- **Arquivos/módulos afetados:** `TODO`
- **Quebra de compatibilidade:** `sim / não` — se sim, qual o plano de transição.
- **Feature flag:** `TODO`
- **Rollback:** `TODO — como desfazer sem perder dado.`

## Rastreabilidade

Toda linha desta tabela precisa estar preenchida antes da aprovação.

| Requisito | Onde é atendido no design |
|---|---|
| 1.1 | `TODO` |
| 1.2 | `TODO` |
| 2.1 | `TODO` |
