# Tarefas Locais — `[NOME DA SUB-FUNCIONALIDADE]`

> **Tarefas atômicas locais**
> Derivadas de #[[file:design.md]]. Uma tarefa por vez, com verificação entre cada uma.

## Pré-condições

A execução não começa antes de todas serem verdadeiras:

- [ ] `epic-design.md` aprovado.
- [ ] Núcleo compartilhado do módulo implementado e disponível.
- [ ] Sub-funcionalidades das quais esta depende concluídas (`TODO` ou "—").

## Convenção de marcação

`[ ]` não iniciada · `[-]` em andamento (uma por vez) · `[x]` concluída **e** verificada.

## Plano de execução

- [ ] 1. Contratos locais
  - Definir os tipos e assinaturas da seção Contratos de API locais do design
  - Reutilizar os tipos do núcleo compartilhado em vez de redeclarar
  - Type check passa
  - _Requisitos: S2-TODO_

- [ ] 2. Lógica local
- [ ] 2.1 Implementar o componente principal
  - Respeitar a responsabilidade única definida no design
  - Testes unitários cobrindo cada critério de aceitação
  - _Requisitos: S2-TODO_
- [ ] 2.2 Aplicar os padrões transversais do épico
  - Implementar via os mecanismos do `epic-design.md`, sem solução paralela
  - Verificar que as leis globais herdadas são respeitadas
  - _Requisitos: leis L-TODO_

- [ ] 3. Expor a API local
  - Implementar handler com validação na borda e autorização por recurso
  - Testes de integração cobrindo caminho feliz e caminhos de erro
  - _Requisitos: S2-TODO_

- [ ] 4. Verificação e integração
  - Executar os portões do Artigo III da constituição
  - Percorrer cada critério `S2-*` e confirmar um a um
  - Confirmar que nenhuma lei global do épico foi violada
  - Confirmar que os contratos consumidos por outras sub-funcionalidades continuam válidos
  - _Requisitos: todos_

## Dependências

```
1 ──▶ 2.1 ──▶ 2.2 ──▶ 3 ──▶ 4
```

`TODO — ajuste conforme o real.`

## Registro de desvios

Desvio que afeta o épico exige correção do `epic-design.md`, não apenas desta pasta.

| Data | Tarefa | Desvio | Afeta o épico? | Documento corrigido? |
|---|---|---|---|---|
| `TODO` | `TODO` | `TODO` | `sim / não` | `TODO` |
