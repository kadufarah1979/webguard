# specs/

Ciclo documental das iniciativas. Uma pasta por iniciativa, nomeada em kebab-case
descritivo.

## Escolha da estrutura

| Esforço estimado | Estrutura | Arquivos |
|---|---|---|
| Até 80h | `funcionalidade-simples/` | `requirements.md`, `design.md`, `tasks.md` |
| Acima de 80h | `modulo-complexo-epico/` | `epic-requirements.md`, `epic-design.md` + `sub-funcionalidade-N/` com o trio local |

As duas pastas presentes são **placeholders**. Duplique a que servir e renomeie.

## O ciclo e seus portões

```
requirements.md ──(aprovar)──▶ design.md ──(aprovar)──▶ tasks.md ──(aprovar)──▶ implementação
```

Por que os portões existem: corrigir um mal-entendido no `requirements.md` custa uma frase.
Corrigir o mesmo mal-entendido depois de implementado custa uma sprint.

## O que vai em cada arquivo

| Arquivo | Responde | Nunca contém |
|---|---|---|
| `requirements.md` | O quê e por quê | Nome de classe, tabela, biblioteca, endpoint |
| `design.md` | Como, e o que foi descartado | Ordem de execução, estimativa |
| `tasks.md` | Em que ordem, por quem verificado | Decisão de arquitetura nova |

Se uma decisão de arquitetura aparece pela primeira vez no `tasks.md`, o design está
incompleto — volte uma fase.

## Herança no épico

`epic-requirements.md` e `epic-design.md` valem como **lei** para todas as
sub-funcionalidades. Uma sub-funcionalidade detalha o que é local a ela e **jamais**
contradiz o épico. Se a contradição for necessária, o épico está errado e é corrigido
primeiro.

## Ciclo de vida

Specs concluídas não são apagadas — são o registro histórico de por que o sistema é como é.
Marque o status no topo de cada documento (`Rascunho` / `Em revisão` / `Aprovado` /
`Implementado`) e mantenha a pasta.
