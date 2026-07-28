# Constituição de Engenharia

> **O DNA inegociável da engenharia deste repositório.**
>
> Este é o documento de maior autoridade do projeto. Em caso de conflito entre a
> constituição, um steering, uma spec ou uma sugestão pontual em chat, **a constituição vence**.
> Alterar este arquivo é um ato deliberado: exige justificativa registrada na seção
> _Histórico de Emendas_ ao final.
>
> `[PLACEHOLDER]` — preencha as seções marcadas com `TODO` no início de um novo projeto
> e remova o que não se aplicar.

## Artigo I — Identidade do Projeto

- **Nome:** WebGuard
- **Problema que resolve:** Descobrir vulnerabilidades e más configurações de segurança em um site web a partir de uma única URL, sem precisar consultar vários serviços online.
- **Não-objetivos:** Não é scanner de portas, não faz spider automático, não explora pós-descoberta, não substitui pentest completo.
- **Stack primária:** Python 3.12+ · GTK4 + libadwaita · httpx · pytest
- **Versões travadas:** Python ≥3.12, GTK4 ≥4.12, libadwaita ≥1.4, httpx ≥0.27

## Artigo II — Princípios Invioláveis

1. **Especificação antes de código.** Nenhuma funcionalidade é implementada sem uma spec
   correspondente em `.kiro/specs/`. Correções triviais e typos são a única exceção.
2. **Rastreabilidade total.** Toda tarefa em `tasks.md` referencia o requisito que a
   justifica. Código sem requisito rastreável é dívida técnica por definição.
3. **Nenhuma suposição silenciosa.** Ambiguidade encontrada durante a implementação
   interrompe o fluxo e volta para o `requirements.md` — não é resolvida por adivinhação.
4. **Reversibilidade.** Toda mudança precisa ter caminho de rollback claro antes de ir a produção.
5. **O teste define o pronto.** Uma tarefa só está concluída quando sua verificação
   automatizada existe e passa.

## Artigo III — Portões de Qualidade (Definition of Done)

Uma tarefa está `[x]` concluída somente quando **todos** os itens abaixo são verdadeiros:

- [ ] O comportamento descrito no requisito é observável e verificado.
- [ ] Lint e formatação passam sem exceções pontuais (`ruff check src/ tests/ && ruff format --check src/ tests/`).
- [ ] Type check passa sem `any` novo e sem supressões (`mypy src/`).
- [ ] Testes automatizados passam (`pytest --cov=src/webguard --cov-fail-under=85 tests/`).
- [ ] Cobertura não regride abaixo de 85%.
- [ ] Nenhum segredo, credencial, token ou dado pessoal real foi introduzido.
- [ ] Documentação afetada foi atualizada no mesmo commit.

## Artigo IV — Segurança (Cláusula Pétrea)

Estas regras não admitem exceção negociada em chat:

- Segredos **nunca** em código, teste, fixture, log ou histórico do git. Somente via
  variável de ambiente.
- Toda entrada externa é hostil até ser validada no limite do sistema (borda da API).
- Consultas a banco sempre parametrizadas. Concatenação de SQL com entrada do usuário é
  proibida.
- Autorização é verificada no servidor, por recurso. Esconder um botão na UI não é
  controle de acesso.
- Dependência nova exige justificativa: o que ela resolve, por que não resolvemos sem ela,
  e qual sua superfície de risco.
- Erros não vazam stack trace, query ou detalhe de infraestrutura para o cliente.

## Artigo V — Padrões de Código

- **Nomes:** snake_case para módulos, funções e variáveis; PascalCase para classes e dataclasses; UPPER_SNAKE para constantes. Arquivos nomeados pelo conceito que contêm (`guard.py`, não `utils.py`).
- **Estrutura de pastas:** conforme definido no `epic-design.md` — `src/webguard/{ui,core,analyzers,bridge,exporters,templates,data}` e `tests/`.
- **Tratamento de erro:** exceções tipadas herdando de `WebGuardError`; analisadores nunca lançam — retornam `Finding` com `indeterminate`; boundary de erro no controller.
- **Comentários:** explicam _por quê_, nunca _o quê_. Código que precisa de comentário
  para ser lido deve ser reescrito.
- **Tamanho:** função que não cabe na tela faz coisas demais. Máximo sugerido: 40 linhas.

## Artigo VI — Fluxo de Trabalho

- **Branches:** `feature/<spec-slug>`, `fix/<issue-number>`, `chore/<slug>`
- **Commits:** imperativo, primeira linha ≤ 72 caracteres, corpo explica o motivo.
- **Nunca commitar direto na branch default.** Toda mudança entra via Pull Request.
- **PR:** referencia a spec, lista o que foi verificado e como reverter.

## Artigo VII — Limites da Autonomia do Agente

O agente **pode**, sem confirmação: ler o repositório, criar e editar specs, propor design,
rodar lint, type check e testes.

O agente **deve pedir confirmação** antes de: instalar ou atualizar dependências, alterar
schema de banco, escrever em arquivos de CI/CD, mexer em infraestrutura, apagar arquivos,
reescrever histórico do git, ou fazer qualquer chamada a serviço externo que gere custo.

O agente **nunca**: faz push forçado, desativa hooks de verificação, contorna um portão de
qualidade para "entregar mais rápido", ou marca uma tarefa como concluída sem verificação.

## Histórico de Emendas

| Data | Artigo | Mudança | Motivo |
|---|---|---|---|
| 2026-07-28 | I, III, V, VI | Preenchido com dados do projeto WebGuard | Bootstrap do projeto |
