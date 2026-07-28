# Tarefas — `[NOME DA FUNCIONALIDADE]`

> **Fase 3 de 3 · Tarefas atômicas e dependências**
> Plano de execução derivado de #[[file:design.md]].
>
> **Portão:** este é o único documento que o agente executa. Uma tarefa por vez, com
> verificação entre cada uma.

## Regras de uma tarefa atômica

- Cabe em **uma sessão de trabalho** (referência: 1 a 4 horas).
- Toca um conjunto **nomeável** de arquivos.
- Termina em estado **verificável** — o repositório nunca fica quebrado entre tarefas.
- Referencia o **requisito** que a justifica. Tarefa sem requisito é escopo inventado.
- Descreve **ação de código**, não atividade humana. "Alinhar com o time" não é tarefa aqui.

## Convenção de marcação

| Marca | Significado |
|---|---|
| `[ ]` | Não iniciada |
| `[-]` | Em andamento (apenas uma por vez) |
| `[x]` | Concluída **e** verificada pelos portões do Artigo III |

## Plano de execução

- [ ] 1. Preparar fundação e contratos
  - Criar os tipos e interfaces definidos na seção Contratos do design
  - Sem lógica de negócio ainda — apenas as formas que o resto vai consumir
  - Garantir que o type check passa com as novas definições
  - _Requisitos: TODO_

- [ ] 2. Implementar a camada de dados
- [ ] 2.1 Definir entidades e migração
  - Escrever a migração de ida e a de volta
  - Verificar que a migração roda em banco limpo e em banco com dados
  - _Requisitos: TODO_
- [ ] 2.2 Implementar o repositório com testes
  - Escrever os testes das operações antes da implementação
  - Cobrir os casos de borda listados no design
  - _Requisitos: TODO_

- [ ] 3. Implementar a regra de negócio
  - Implementar o serviço conforme a responsabilidade única definida no design
  - Testes unitários cobrindo cada critério de aceitação do requisito
  - _Requisitos: TODO_

- [ ] 4. Expor a interface externa
  - Implementar o endpoint/handler com validação de entrada na borda
  - Implementar autorização por recurso no servidor
  - Teste de integração cobrindo caminho feliz e caminhos de erro
  - _Requisitos: TODO_

- [ ] 5. Tratamento de erro e observabilidade
  - Implementar a tabela de tratamento de erro do design
  - Confirmar que nenhuma resposta vaza stack trace ou detalhe interno
  - Adicionar as métricas e logs definidos nos requisitos não funcionais
  - _Requisitos: TODO_

- [ ] 6. Verificação final
  - Executar a suíte completa e os portões do Artigo III
  - Percorrer cada critério de aceitação do `requirements.md` e confirmar um a um
  - Atualizar a documentação afetada
  - _Requisitos: todos_

## Dependências

```
1 ──▶ 2.1 ──▶ 2.2 ──▶ 3 ──▶ 4 ──▶ 5 ──▶ 6
```

`TODO — ajuste conforme o real. Marque explicitamente o que pode rodar em paralelo.`

## Registro de desvios

Quando a implementação revelar que o design estava errado, registre aqui e **corrija o
design** — não deixe o código e o documento divergirem em silêncio.

| Data | Tarefa | Desvio | Documento corrigido? |
|---|---|---|---|
| `TODO` | `TODO` | `TODO` | `TODO` |
