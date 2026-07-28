# Requisitos Locais — Núcleo e Análise de Cabeçalhos

> **Sub-funcionalidade 01 do épico Analisador de Segurança Web**
>
> Fatia vertical fim a fim: janela GTK, entrada de URL, camada de coleta com as travas,
> motor de achados, e o primeiro analisador (cabeçalhos de segurança).
>
> Herança: #[[file:../epic-requirements.md]]

## Status

| Campo | Valor |
|---|---|
| Fase | `Aprovado` |
| Estimativa | ~34h |
| Depende de | — (fundação do projeto) |
| Aprovado por | Usuário |

## Herança do épico

- **Leis globais herdadas:** L-1 a L-9 (todas)
- **Regras transversais:** RN-1 a RN-6
- **Requisitos épicos atendidos:** E-1, E-3.4, E-4
- **Restrições adicionais:** nenhuma

## Introdução

Esta sub-funcionalidade entrega uma aplicação funcional de ponta a ponta: o usuário abre a
janela, digita uma URL, escolhe o modo (passivo/ativo — embora só passivo funcione até a
sub-04), confirma, e recebe achados sobre cabeçalhos de segurança. Também construi a
infraestrutura compartilhada que as demais sub-funcionalidades consomem: models, guard,
collector, controller, registry e shell da UI.

## Fora de escopo

- Análise de TLS/certificado (sub-02)
- Análise de cookies (sub-02)
- Análise de documento HTML (sub-03)
- Motor de payloads ativos (sub-04)
- Exportação de relatório (sub-03)
- Integração nuclei (sub-04)

## Requisitos

### Requisito S1-1 — Entrada e validação de URL

**História de usuário:** Como usuário, quero digitar a URL do site e ter feedback imediato
se ela é válida, para não precisar esperar o scan falhar.

#### Critérios de aceitação

1. QUANDO o usuário digita no campo de URL ENTÃO o sistema DEVE validar em tempo real e
   indicar visualmente se é válida (esquema + host no mínimo).
2. QUANDO a URL é informada sem esquema ENTÃO o sistema DEVE assumir `https://` e exibir
   a URL completa resultante.
3. SE a URL é sintaticamente inválida e o usuário tenta iniciar ENTÃO o sistema DEVE
   bloquear a execução e destacar o campo com mensagem de erro.
4. QUANDO a URL é válida ENTÃO o sistema DEVE habilitar o botão de execução.

### Requisito S1-2 — Seleção de modo e consentimento

**História de usuário:** Como usuário, quero escolher entre análise passiva e ativa, com
clareza sobre o que cada modo faz.

#### Critérios de aceitação

1. QUANDO a janela abre ENTÃO o modo padrão é `Passivo` e nenhum consentimento é necessário.
2. QUANDO o usuário seleciona `Ativo` ENTÃO o sistema DEVE exibir aviso conforme L-2 e
   exigir confirmação antes de habilitar execução.
3. SE o usuário cancela o consentimento ENTÃO o sistema DEVE reverter a seleção para `Passivo`.
4. QUANDO o consentimento é confirmado ENTÃO o sistema DEVE registrar timestamp e URL no
   contexto da execução.

### Requisito S1-3 — Coleta HTTP com travas

**História de usuário:** Como responsável pelo uso, quero que a ferramenta respeite os
limites de L-1 e L-3, para que eu saiba exatamente o que ela fez.

#### Critérios de aceitação

1. QUANDO a análise passiva executa ENTÃO o coletor DEVE emitir apenas requisições
   permitidas por L-1 modo passivo.
2. QUANDO uma requisição é emitida ENTÃO o guard DEVE registrar no log: timestamp, método,
   URL, status recebido e tempo decorrido.
3. SE um componente tenta emitir requisição fora do escopo do modo ENTÃO o guard DEVE
   bloquear, registrar como erro interno, e não emitir.
4. ENQUANTO requisições são emitidas DEVE respeitar o intervalo mínimo de 200ms (passivo).
5. QUANDO a URL redireciona ENTÃO o coletor DEVE seguir a cadeia (até 10 hops) e registrar
   cada URL intermediária.
6. SE o host não resolve, recusa conexão ou excede timeout (15s) ENTÃO o coletor DEVE
   retornar erro com motivo técnico, sem lançar exceção.

### Requisito S1-4 — Análise de cabeçalhos de segurança

**História de usuário:** Como desenvolvedor, quero saber quais cabeçalhos de segurança
estão ausentes ou mal configurados no meu site.

#### Critérios de aceitação

1. QUANDO a coleta termina com sucesso ENTÃO o analisador de cabeçalhos DEVE verificar:
   - `Content-Security-Policy` (presença + qualidade: `unsafe-inline`, `unsafe-eval`,
     wildcards em script-src, `object-src` ausente)
   - `Strict-Transport-Security` (presença, max-age mínimo, includeSubDomains, preload)
   - `X-Content-Type-Options` (presença, valor `nosniff`)
   - `X-Frame-Options` (presença, valores DENY ou SAMEORIGIN)
   - `Referrer-Policy` (presença, valor seguro)
   - `Permissions-Policy` (presença, diretivas sensíveis restritivas)
   - `Cross-Origin-Opener-Policy` (presença)
   - `Cross-Origin-Embedder-Policy` (presença)
   - `Cross-Origin-Resource-Policy` (presença)
   - `Cache-Control` em respostas com dados sensíveis
2. QUANDO um cabeçalho obrigatório está ausente ENTÃO o sistema DEVE emitir achado com
   severidade conforme RN-3, evidência "Cabeçalho X ausente na resposta", e o valor
   recomendado em formato copiável.
3. QUANDO um cabeçalho está presente mas mal configurado ENTÃO DEVE explicar o que está
   errado no valor específico (ex.: "CSP contém 'unsafe-inline' em script-src").
4. QUANDO todos os cabeçalhos verificados estão corretos ENTÃO DEVE emitir um achado
   `Informativo` confirmando o que foi verificado e passou.
5. QUANDO a CSP existe ENTÃO o analisador DEVE decompor as diretivas e avaliar
   individualmente (não tratar como opaco).

### Requisito S1-5 — Apresentação de resultados

**História de usuário:** Como usuário, quero ver os achados de forma clara e organizada
durante e após a análise.

#### Critérios de aceitação

1. ENQUANTO a análise executa ENTÃO o sistema DEVE exibir achados conforme são produzidos
   (tempo real, sem esperar o fim).
2. QUANDO a análise termina ENTÃO os achados DEVEM estar agrupados por severidade em
   ordem decrescente.
3. QUANDO o usuário clica em um achado ENTÃO o sistema DEVE expandir mostrando evidência
   completa, explicação e correção.
4. QUANDO a correção contém valor configurável ENTÃO DEVE ser apresentada em bloco
   copiável (botão de copiar).
5. QUANDO a análise falha por erro de rede ENTÃO DEVE exibir o motivo na mesma tela sem
   perder achados já produzidos.

### Requisito S1-6 — Log de requisições

**História de usuário:** Como responsável pelo uso, quero ver todas as requisições que a
ferramenta fez, para comprovar que não excedeu o escopo.

#### Critérios de aceitação

1. QUANDO o usuário navega ao log ENTÃO DEVE ver a lista completa de requisições da última
   execução com timestamp, método, URL e status.
2. QUANDO o usuário clica em uma entrada ENTÃO DEVE ver detalhes: headers enviados, tempo
   decorrido, tamanho da resposta.
3. SE alguma requisição foi bloqueada pelo guard ENTÃO DEVE aparecer destacada como erro
   interno.

### Requisito S1-7 — Cancelamento

**História de usuário:** Como usuário, quero poder cancelar a análise a qualquer momento
sem esperar.

#### Critérios de aceitação

1. QUANDO o usuário aciona cancelar ENTÃO o sistema DEVE interromper requisições pendentes
   em até 2 segundos.
2. QUANDO cancelado ENTÃO o sistema DEVE preservar e exibir os achados já produzidos até
   o momento do cancelamento.
3. QUANDO cancelado ENTÃO o status DEVE indicar claramente que a análise foi interrompida.

## Requisitos não funcionais locais

- Interface responsiva: a janela nunca congela durante a coleta (L-8).
- Tempo de startup da aplicação: menos de 2s até a janela estar interativa.
- Consumo de memória: menos de 200MB durante análise de site típico.

## Perguntas abertas

| # | Pergunta | Responsável | Status |
|---|---|---|---|

(Nenhuma — as perguntas relevantes foram resolvidas no épico.)

## Critério de conclusão

- [ ] Todos os critérios S1-* verificados com fixtures e em teste manual.
- [ ] Guard comprovadamente bloqueia requisição fora do escopo (teste automatizado).
- [ ] Portões do Artigo III passam.
- [ ] A aplicação abre, aceita URL, executa análise passiva de cabeçalhos e exibe achados.
