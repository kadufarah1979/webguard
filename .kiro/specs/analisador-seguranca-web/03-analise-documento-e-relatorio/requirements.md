# Requisitos Locais — Análise do Documento e Relatório

> **Sub-funcionalidade 03 do épico Analisador de Segurança Web**
>
> Herança: #[[file:../epic-requirements.md]]

## Status

| Campo | Valor |
|---|---|
| Fase | `Em revisão` |
| Estimativa | ~32h |
| Depende de | `01-nucleo-e-cabecalhos` |
| Aprovado por | `PENDENTE` |

## Herança do épico

- **Leis herdadas:** L-1 a L-9
- **Regras transversais:** RN-1 a RN-6
- **Requisitos épicos atendidos:** E-1 (famílias adicionais), E-3 (parcial), E-5

## Introdução

Análises que dependem do conteúdo HTML e da relação entre recursos: CORS, SRI, conteúdo
misto, vazamento de banners, source maps e bibliotecas JS com vulnerabilidades conhecidas.
Também implementa a exportação de relatório em Markdown, JSON e HTML.

## Fora de escopo

- Renderização JavaScript (aceita HTML como entregue; emite aviso se body é quase vazio).
- Spider/crawler — analisa apenas a resposta da URL informada.
- Base de vulnerabilidades online — somente base local embarcada.

## Requisitos

### Requisito S3-1 — CORS

**História de usuário:** Como desenvolvedor, quero saber se a política CORS do meu site
tem falhas exploráveis.

#### Critérios de aceitação

1. QUANDO `Access-Control-Allow-Origin` é `*` com `Access-Control-Allow-Credentials: true`
   ENTÃO DEVE emitir `Crítica`.
2. QUANDO ACAO reflete a origem do request sem validação DEVE emitir `Alta`.
3. QUANDO ACAO é `*` sem credentials DEVE emitir `Informativo` (normalmente intencional).
4. QUANDO CORS não está presente DEVE registrar como `Informativo` (não é problema).

### Requisito S3-2 — Subresource Integrity (SRI)

**História de usuário:** Como desenvolvedor, quero saber se recursos de terceiros são
carregados sem verificação de integridade.

#### Critérios de aceitação

1. QUANDO `<script>` ou `<link rel="stylesheet">` referencia origem diferente E não tem
   atributo `integrity` ENTÃO DEVE emitir `Média` com a URL do recurso.
2. QUANDO `integrity` está presente DEVE emitir `Informativo`.
3. QUANDO o recurso é do mesmo domínio SRI não é necessário — sem achado.

### Requisito S3-3 — Conteúdo misto

**História de usuário:** Como desenvolvedor, quero saber se meu site HTTPS carrega
recursos por HTTP.

#### Critérios de aceitação

1. QUANDO o site é HTTPS e o HTML contém referências `http://` a scripts, iframes ou
   formulários ENTÃO DEVE emitir `Alta` (mixed active content).
2. QUANDO contém referências `http://` a imagens, fontes ou CSS ENTÃO DEVE emitir
   `Média` (mixed passive content).
3. QUANDO não há conteúdo misto DEVE emitir `Informativo`.

### Requisito S3-4 — Vazamento de informação (banners e source maps)

**História de usuário:** Como desenvolvedor, quero saber se meu servidor expõe versão
de software ou source maps.

#### Critérios de aceitação

1. QUANDO `Server` ou `X-Powered-By` contém nome e versão DEVE emitir `Baixa`.
2. QUANDO HTML contém `sourceMappingURL` acessível publicamente DEVE emitir `Média`.
3. QUANDO `X-AspNet-Version`, `X-AspNetMvc-Version`, ou headers similares estão presentes
   DEVE emitir `Baixa` com o valor.

### Requisito S3-5 — Bibliotecas JavaScript vulneráveis

**História de usuário:** Como desenvolvedor, quero saber se meu site usa bibliotecas JS
com vulnerabilidades conhecidas.

#### Critérios de aceitação

1. QUANDO o HTML contém `<script src="...">` com biblioteca detectável (jQuery, Angular,
   React, Bootstrap, Lodash, etc.) ENTÃO o analisador DEVE extrair a versão.
2. QUANDO a versão detectada está na base local de vulnerabilidades DEVE emitir achado com
   severidade da CVE, versão afetada e versão corrigida.
3. QUANDO a versão não está na base DEVE registrar `Informativo` com a versão detectada.
4. QUANDO não é possível detectar versão DEVE emitir `Indeterminado` com motivo.
5. A base local é derivada do Retire.js (licença MIT — permitida). Atualização manual.

### Requisito S3-6 — Exportação de relatório

**História de usuário:** Como desenvolvedor, quero exportar o resultado para anexar a um
issue ou compartilhar.

#### Critérios de aceitação

1. QUANDO o usuário exporta em Markdown ENTÃO DEVE gerar documento com: URL, data, modo,
   todos os achados com severidade, evidência e correção.
2. QUANDO exporta em JSON DEVE gerar com schema versionado (`version: "1.0"`), array de
   achados com todos os campos de `Finding`.
3. QUANDO exporta em HTML DEVE gerar relatório autocontido com CSS embutido, navegável
   por severidade.
4. SE a análise não foi executada ENTÃO o botão de exportar DEVE estar desabilitado.
5. SE o arquivo de destino não é gravável DEVE informar erro e manter resultado em memória.

### Requisito S3-7 — Aviso de site que exige JavaScript

**História de usuário:** Como usuário, quero saber quando a análise pode estar incompleta
porque o site depende de JS para renderizar.

#### Critérios de aceitação

1. QUANDO o HTML retornado contém menos de 500 bytes de conteúdo não-script E contém
   framework SPA detectável (React root, Angular app, Vue #app) ENTÃO DEVE emitir
   `Informativo` avisando que o conteúdo pode ser renderizado por JavaScript e a análise
   do documento pode estar incompleta.

## Requisitos não funcionais locais

- Parse de HTML via BeautifulSoup com parser `html.parser` (stdlib, sem dep extra).
- Base de JS vulns em `data/js_vulns.json`, ~100KB estimado.

## Critério de conclusão

- [ ] Todos os critérios S3-* verificados com fixtures HTML.
- [ ] Exportadores testados contra golden files.
- [ ] Portões do Artigo III passam.
