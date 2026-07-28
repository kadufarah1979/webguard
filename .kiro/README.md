# A Anatomia da Pasta `.kiro/`

Template de **SDD (Spec Driven Development)** — placeholder reutilizável para qualquer
projeto deste repositório. Copie, preencha os `TODO` e apague o que não usar.

## Mapa

```
.kiro/
├── constitution.md                    # O DNA inegociável da engenharia
├── hooks/                             # Automação reativa disparada por eventos
│   ├── pre-write-security.json        # Varredura OWASP pré-escrita
│   └── post-task-validation.json      # Disparador assíncrono de testes
├── specs/                             # Ciclo documental das iniciativas
│   ├── funcionalidade-simples/        # Padrão · até 80h
│   │   ├── requirements.md            # O "Quê" e o "Porquê"
│   │   ├── design.md                  # Arquitetura técnica e contratos
│   │   └── tasks.md                   # Tarefas atômicas e dependências
│   └── modulo-complexo-epico/         # Épicos · acima de 80h
│       ├── epic-requirements.md       # Regras globais do módulo
│       ├── epic-design.md             # Arquitetura macro
│       ├── sub-funcionalidade-1/
│       │   ├── requirements.md        # Requisitos locais da sub-funcionalidade
│       │   ├── design.md              # Contratos de API locais
│       │   └── tasks.md               # Tarefas atômicas locais
│       └── sub-funcionalidade-2/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
└── steering/                          # Engenharia de contexto e direcionamento
    ├── always/                        # Diretrizes globais injetadas em toda chamada
    ├── auto/                          # Injeção semântica por similaridade
    ├── conditional/                   # Ativadores por glob pattern (*.tsx, *.pas…)
    └── manual/                        # Inclusões sob demanda feitas pelo desenvolvedor
```

## As quatro camadas

| Camada | Pergunta que responde | Frequência de mudança |
|---|---|---|
| `constitution.md` | Quais regras nunca quebramos? | Raríssima — exige emenda |
| `steering/` | O que o agente precisa saber sempre? | Baixa — evolui com o projeto |
| `specs/` | O que estamos construindo agora? | Alta — uma por iniciativa |
| `hooks/` | O que deve acontecer automaticamente? | Baixa |

## Como escolher entre spec simples e épico

O corte é o **esforço estimado**, conforme a anatomia acima:

- **Até 80h → `funcionalidade-simples/`**: um trio `requirements` → `design` → `tasks`.
- **Acima de 80h → `modulo-complexo-epico/`**: `epic-requirements` e `epic-design`
  estabelecem as leis e a arquitetura macro do módulo; cada `sub-funcionalidade-N/`
  herda essas leis e detalha apenas o que é local a ela.

Regra de herança: uma sub-funcionalidade **nunca** contradiz o épico. Se precisar
contradizer, o épico está errado e deve ser corrigido primeiro.

## O ciclo

```
requirements.md  →  design.md  →  tasks.md  →  implementação
     (aprovar)      (aprovar)     (aprovar)      (executar)
```

Cada seta é um portão de aprovação humana. O agente não avança sozinho de uma fase para a
próxima, e não começa a implementar com uma fase anterior em aberto.

## Referência de arquivos

Dentro de qualquer steering ou spec, é possível injetar o conteúdo de outro arquivo:

```
#[[file:../../constitution.md]]        ← de dentro de specs/<nome>/, alcança a constituição
#[[file:../epic-requirements.md]]      ← de uma sub-funcionalidade, alcança o épico
#[[file:../../../docs/openapi.yaml]]   ← de specs/<nome>/, alcança a raiz do repositório
```

O caminho é **relativo ao arquivo que contém a referência**. Isso permite que uma spec
consuma um contrato OpenAPI ou GraphQL sem duplicar o conteúdo.

## Convenção de nomes das specs

As pastas `funcionalidade-simples/` e `modulo-complexo-epico/` são **placeholders**.
Ao iniciar algo real, renomeie para um slug descritivo em kebab-case:

```
specs/autenticacao-oauth/          ← bom
specs/checkout-multi-moeda/        ← bom
specs/nova-feature/                ← ruim, não diz nada
```
