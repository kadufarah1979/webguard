# hooks/

Automação reativa: pares **evento → ação** que rodam sem alguém pedir.

## Aviso importante sobre estes dois arquivos

Os hooks aqui são **placeholders desativados** (`"enabled": false`) e por dois motivos
distintos precisam de uma conferência antes do primeiro uso:

1. **Os padrões de arquivo e comandos são genéricos.** `src/**/*.ts` e afins provavelmente
   não correspondem à estrutura real do seu projeto.
2. **O schema não foi validado contra a documentação oficial.** Os arquivos foram escritos
   no formato `enabled` / `name` / `description` / `version` / `when.type` / `then.type`,
   com `then.type` entre `askAgent` (envia um prompt ao agente) e `runCommand` (executa
   shell). Confirme os nomes de campo, os valores de `when.type` aceitos e a extensão de
   arquivo esperada na documentação de hooks em <https://kiro.dev/docs/hooks/> antes de
   ligar — em algumas versões o arquivo precisa ter extensão `.kiro.hook` em vez de `.json`.

Ligue um hook por vez, verifique que ele disparou como esperado, e só então ligue o próximo.

## Os dois hooks do template

| Arquivo | Momento | Ação |
|---|---|---|
| `pre-write-security.json` | Ao editar código-fonte | Varredura OWASP + Cláusula Pétrea da constituição |
| `post-task-validation.json` | Ao concluir tarefa de spec | Roda os portões de qualidade e reverte a marcação se falhar |

## Princípios para novos hooks

- **Um hook, uma responsabilidade.** Hook que faz cinco coisas falha de forma ilegível.
- **Escopo estreito no `patterns`.** Disparar em `**/*` custa tokens e atenção em cada save.
- **Determinístico primeiro.** Se lint, formatter ou teste resolvem, use `runCommand`.
  Reserve `askAgent` para julgamento que uma ferramenta não consegue fazer.
- **Falha ruidosa.** Um hook de validação que passa silenciosamente quando deveria falhar
  é pior que não ter hook.
- **Nunca auto-corrija segurança sem revisão.** Reporte o achado; deixe a decisão no humano.
