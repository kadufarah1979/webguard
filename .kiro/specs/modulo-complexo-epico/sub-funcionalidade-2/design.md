# Design Local — `[NOME DA SUB-FUNCIONALIDADE]`

> **Contratos de API locais**
>
> Detalha apenas o que é local. A arquitetura macro, o schema compartilhado e os padrões
> transversais estão em #[[file:../epic-design.md]] e são **consumidos**, não redefinidos.
>
> Base local: #[[file:requirements.md]]

## Status

| Campo | Valor |
|---|---|
| Fase | `Rascunho` / `Em revisão` / `Aprovado` |
| Aprovado por | `TODO` |

## Conformidade com o épico

| Item do épico | Como esta sub-funcionalidade o consome |
|---|---|
| Decisão ADE-1 | `TODO` |
| Núcleo compartilhado `TODO` | `TODO` |
| Padrão transversal da Lei L-1 | `TODO` |

**Nada novo no schema compartilhado?** `confirmado / precisa de alteração no epic-design`

Se esta sub-funcionalidade precisa alterar o modelo compartilhado, pare: atualize
`epic-design.md` primeiro e obtenha aprovação.

## Visão geral

`TODO — a estratégia técnica local, em um parágrafo.`

## Decisões locais

### ADL-1 — `[Decisão]`

- **Contexto:** `TODO`
- **Decisão:** `TODO`
- **Alternativas descartadas:** `TODO`
- **Consequências:** `TODO`
- **Rastreia:** `S2-TODO`

## Componentes locais

### `[NomeDoComponente]`

- **Responsabilidade única:** `TODO`
- **Consome do núcleo compartilhado:** `TODO`
- **Não faz:** `TODO`
- **Rastreia:** `S2-TODO`

## Contratos de API locais

O foco deste documento.

```
TODO — assinaturas, tipos de request/response, formato de erro.
```

| Método / Evento | Caminho | Entrada | Saída | Erros | Requisito |
|---|---|---|---|---|---|
| `TODO` | `TODO` | `TODO` | `TODO` | `TODO` | `S2-TODO` |

**Contratos de fronteira do módulo que esta sub-funcionalidade implementa:** `TODO`

## Dados locais

- **Usa do schema compartilhado:** `TODO`
- **Estruturas exclusivamente locais:** `TODO`
- **Migração local necessária:** `sim / não`

## Tratamento de erro

Segue o padrão único do módulo. Registre apenas as situações específicas desta
sub-funcionalidade.

| Situação | Detecção | Resposta | Log / métrica |
|---|---|---|---|
| `TODO` | `TODO` | `TODO` | `TODO` |

## Estratégia de testes local

| Nível | O que cobre | Requisito |
|---|---|---|
| Unitário | `TODO` | `S2-TODO` |
| Integração | `TODO` | `S2-TODO` |

**Integração com outras sub-funcionalidades:** `TODO — o que precisa existir para testar isso.`

## Rastreabilidade

| Requisito | Onde é atendido |
|---|---|
| S2-1 | `TODO` |
| S2-2 | `TODO` |
