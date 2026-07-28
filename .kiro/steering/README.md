---
inclusion: manual
---

# steering/

Engenharia de contexto: o conhecimento persistente do projeto, para não reexplicar as
mesmas convenções em cada conversa.

> Este README é **documentação**, não regra — daí o `inclusion: manual` acima. Sem esse
> front-matter ele é injetado no contexto como se fosse uma diretriz do projeto
> (comportamento observado na prática: qualquer `.md` nesta pasta sem front-matter passa a
> valer como regra de workspace).

## Os quatro modos

As subpastas organizam os arquivos por **estratégia de ativação**:

| Pasta | Ativação | Custo em tokens | Use para |
|---|---|---|---|
| `always/` | Injetado em toda chamada | Alto — pago sempre | Poucas verdades que valem para tudo |
| `auto/` | Injeção semântica por similaridade | Médio — sob relevância | Domínio, glossário, decisões consultáveis |
| `conditional/` | Glob pattern (`*.tsx`, `*.pas`…) | Baixo — só no arquivo certo | Convenção específica de tecnologia |
| `manual/` | Sob demanda pelo desenvolvedor | Zero até ser pedido | Runbooks, procedimentos raros |

## Importante: a pasta organiza, o front-matter ativa

A pasta é convenção humana para leitura. Quem determina a ativação de fato é o
**front-matter** no topo do arquivo:

```markdown
---
inclusion: always
---
```

```markdown
---
inclusion: fileMatch
fileMatchPattern: "src/**/*.tsx"
---
```

```markdown
---
inclusion: manual
---
```

Mantenha os dois coerentes: arquivo dentro de `conditional/` deve ter `fileMatch` no
front-matter. Pasta e front-matter divergentes é a principal fonte de confusão nesta
estrutura.

> Os placeholders desta pasta estão todos com `inclusion: manual` **de propósito**: um
> arquivo cheio de `TODO` injetado em toda requisição seria lido como instrução real e
> degradaria as respostas. Ao preencher um arquivo, troque o `inclusion` para o modo da
> pasta em que ele está.
>
### O que foi verificado empiricamente

Durante a criação deste template, dois comportamentos foram observados diretamente:

- Um `.md` em `.kiro/steering/` **sem front-matter** é carregado e passa a valer como regra
  de workspace, sem nenhuma ação do desenvolvedor.
- Um `.md` com `inclusion: manual` **não** é carregado automaticamente.

Os valores `always`, `auto` e `fileMatch`/`fileMatchPattern`, por outro lado, **não** puderam
ser confirmados neste ambiente (sem acesso à rede). Valide-os em
<https://kiro.dev/docs/steering/> antes de depender deles, e ative um arquivo por vez.

## Regra de ouro do `always/`

Cada palavra em `always/` é paga em **toda** interação, para sempre. Antes de adicionar algo
lá, pergunte: *isso é verdade em todo arquivo deste projeto?* Se a resposta for "quase
sempre", o lugar é `conditional/` ou `auto/`.

Sintoma de `always/` inflado: o agente começa a ignorar partes das instruções.

## O que não colocar em steering

- **Segredos.** Steering vai para o git e entra no contexto do modelo.
- **Regras inegociáveis.** Essas vivem em `constitution.md`, que tem autoridade maior.
- **O que estamos construindo agora.** Isso é spec, não steering.
- **Documentação extensa duplicada.** Referencie com `#[[file:caminho]]`.

## Escrevendo bom steering

- Imperativo e específico: "use `zod` para validar entrada na borda" vence "valide bem".
- Mostre o padrão com um exemplo curto de código correto.
- Diga também o que **não** fazer, quando o erro é comum.
- Um arquivo, um assunto. Nomeie pelo assunto, não por `notas.md`.
