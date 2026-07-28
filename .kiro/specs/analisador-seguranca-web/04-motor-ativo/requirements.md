# Requisitos Locais — Motor de Testes Ativos

> **Sub-funcionalidade 04 do épico Analisador de Segurança Web**
>
> Herança: #[[file:../epic-requirements.md]]

## Status

| Campo | Valor |
|---|---|
| Fase | `Em revisão` |
| Estimativa | ~46h |
| Depende de | `01-nucleo-e-cabecalhos` |
| Aprovado por | `PENDENTE` |

## Herança do épico

- **Leis herdadas:** L-1 a L-9 (especialmente L-1 modo ativo, L-2, L-7)
- **Regras transversais:** RN-1 a RN-8 (especialmente RN-7, RN-8)
- **Requisitos épicos atendidos:** E-2, E-6
- **Restrições adicionais:** esta sub-funcionalidade só pode ser executada em modo ativo
  com consentimento confirmado (L-2 já implementado na sub-01).

## Introdução

Implementa o motor de payloads e os módulos de teste ativo que descobrem vulnerabilidades
exploráveis: injeções (SQL, XSS, command, template), traversal, IDOR, open redirect,
enumeração de diretórios/arquivos sensíveis, autenticação fraca, e integração com nuclei
para CVEs conhecidos.

## Fora de escopo

- Exploração pós-descoberta (exfiltração, escalação).
- Spider — trabalha com a URL/endpoints informados pelo usuário.
- Fuzzing genérico / brute force extenso.
- XSS armazenado que exige múltiplas sessões (detecção limitada ao GET subsequente).

## Requisitos

### Requisito S4-1 — Motor de payloads baseado em templates

**História de usuário:** Como desenvolvedor, quero que os testes sejam extensíveis sem
alterar código.

#### Critérios de aceitação

1. QUANDO o modo ativo é executado ENTÃO o motor DEVE carregar templates YAML do diretório
   `templates/` e gerar requisições conforme os campos: `injection_points`, `payloads`,
   `detection`.
2. QUANDO o template define detecção `type: time` DEVE medir tempo de resposta e comparar
   com `threshold_ms` (padrão 5000ms), confirmando com `confirmation_rounds` (padrão 2).
3. QUANDO define `type: content` DEVE verificar se o padrão regex aparece na resposta.
4. QUANDO define `type: status` DEVE verificar se o status code indica sucesso inesperado.
5. QUANDO um payload produz detecção positiva ENTÃO DEVE emitir `Finding` com evidência:
   payload enviado + trecho relevante da resposta + tempo decorrido.
6. QUANDO nenhum payload da categoria detecta DEVE emitir `Informativo` por categoria.

### Requisito S4-2 — SQL Injection

**História de usuário:** Como desenvolvedor, quero saber se meu site é vulnerável a
injeção SQL.

#### Critérios de aceitação

1. QUANDO a URL possui parâmetros GET ENTÃO o motor DEVE testar cada um com payloads
   time-based, error-based e boolean-based.
2. Time-based: se resposta demora ≥5s (round 1) e demora novamente no round 2 com mesmo
   delay, e resposta sem payload demora <1s → confirmado.
3. Error-based: se resposta contém mensagem de erro SQL reconhecida (regex) → confirmado.
4. Boolean-based: se `AND 1=1` retorna conteúdo diferente de `AND 1=2` → likely.
5. QUANDO detectado DEVE emitir `Crítica` com payload e evidência.
6. Payloads NÃO devem conter operações destrutivas (RN-7): sem DROP, DELETE, UPDATE, INSERT.

### Requisito S4-3 — XSS Refletido

**História de usuário:** Como desenvolvedor, quero saber se meu site reflete entrada sem
encoding.

#### Critérios de aceitação

1. QUANDO a URL possui parâmetros ENTÃO o motor DEVE injetar marcador único
   (`<wg-xss-{random}>`) e verificar se aparece na resposta sem encoding HTML.
2. SE aparece sem encoding DEVE emitir `Alta` com o parâmetro, payload e trecho da resposta.
3. SE aparece com encoding (`&lt;wg-xss`) DEVE emitir `Informativo` (corretamente tratado).
4. Payloads progressivos: marcador simples → com atributo → com evento → confirma contexto.

### Requisito S4-4 — Command Injection

**História de usuário:** Como desenvolvedor, quero saber se meu site é vulnerável a
injeção de comandos.

#### Critérios de aceitação

1. QUANDO a URL possui parâmetros DEVE testar com payloads time-based (sleep/ping delay).
2. SE resposta demora ≥5s nos 2 rounds E <1s sem payload → `Crítica`.
3. Payloads: `; sleep 5`, `| sleep 5`, `$(sleep 5)`, `` `sleep 5` ``.
4. NÃO usar payloads que escrevam no filesystem ou modifiquem estado (RN-7).

### Requisito S4-5 — Template Injection (SSTI)

**História de usuário:** Como desenvolvedor, quero saber se meu site avalia templates de
forma insegura.

#### Critérios de aceitação

1. DEVE testar expressões matemáticas: `{{7*7}}`, `${7*7}`, `<%= 7*7 %>`, `#{7*7}`.
2. SE a resposta contém `49` no lugar do input original → `Alta` com evidência.
3. DEVE testar variações de encoding para bypass de filtros básicos.
4. Confirmação: enviar `{{7*8}}` e verificar `56` para descartar coincidência.

### Requisito S4-6 — Path Traversal

**História de usuário:** Como desenvolvedor, quero saber se meu site permite acesso a
arquivos fora do diretório permitido.

#### Critérios de aceitação

1. QUANDO a URL possui parâmetros com valor que pode ser caminho (heurística: contém `/`
   ou `.`) DEVE testar com `../../etc/passwd`, variações de encoding e null byte.
2. SE resposta contém padrão `root:x:0:0` → `Crítica`.
3. DEVE testar também `..\\` para Windows (`boot.ini`, `win.ini`).
4. Variações: double encoding, unicode normalization, truncation.

### Requisito S4-7 — Open Redirect

**História de usuário:** Como desenvolvedor, quero saber se meu site pode ser usado para
redirecionamento malicioso.

#### Critérios de aceitação

1. QUANDO a URL possui parâmetros cujo nome sugere URL (url, redirect, next, return, goto,
   link, dest, redir, target) DEVE testar com `https://evil.example.com`.
2. SE a resposta é 3xx com Location para domínio externo → `Média`.
3. DEVE testar variações: `//evil.example.com`, `https:evil.example.com`, 
   `https://target.com@evil.example.com`.

### Requisito S4-8 — IDOR

**História de usuário:** Como desenvolvedor, quero saber se endpoints com IDs numéricos
são acessíveis sem verificação de permissão.

#### Critérios de aceitação

1. QUANDO a URL contém segmento numérico (ex.: `/api/users/123`) DEVE testar variações:
   `122`, `124`, `0`, `1`, `9999`.
2. SE variação retorna 200 com corpo diferente de vazio e diferente de "não autorizado"
   → `Alta` com `confidence: "likely"` (sem autenticação não há certeza).
3. DEVE também testar parâmetros com valores numéricos.
4. Evidência: ID original, ID testado, status, tamanho da resposta.

### Requisito S4-9 — Enumeração de diretórios e arquivos sensíveis

**História de usuário:** Como desenvolvedor, quero saber se há caminhos sensíveis
expostos no meu servidor.

#### Critérios de aceitação

1. DEVE testar wordlist embarcada (~500 caminhos) incluindo: `.git/config`, `.git/HEAD`,
   `.env`, `.DS_Store`, `wp-config.php`, `backup/`, `admin/`, `.htaccess`,
   `phpinfo.php`, `server-status`, `web.config`, `crossdomain.xml`, etc.
2. SE o caminho retorna 200 com conteúdo relevante → severidade conforme categoria:
   - `.git/config`, `.env`, `wp-config.php` → `Crítica` (exposição de credenciais)
   - `.DS_Store`, `backup/`, `admin/` → `Alta`
   - Diretório listável (HTML com "Index of") → `Alta`
   - `robots.txt` com caminhos sensíveis → `Informativo`
3. SE retorna 403 para caminho sensível DEVE emitir `Informativo` (existe mas protegido).
4. Distinguir 404 genuíno de custom 404 (comparar com resposta a caminho sabidamente
   inexistente `/wg-baseline-404-check-{random}`).

### Requisito S4-10 — Autenticação fraca

**História de usuário:** Como desenvolvedor, quero saber se painéis administrativos usam
credenciais padrão.

#### Critérios de aceitação

1. QUANDO a enumeração de diretórios (S4-9) encontra painel com formulário de login DEVE
   testar credenciais padrão: admin/admin, admin/password, admin/1234, root/root.
2. SE login bem-sucedido (heurística: redirect pós-login, cookie de sessão setado,
   mensagem de boas-vindas) → `Crítica`.
3. DEVE testar no máximo 5 combinações para não configurar brute force.
4. SE há rate limit detectável (resposta 429 ou delay crescente) DEVE parar e emitir
   `Informativo` (rate limit funciona).

### Requisito S4-11 — Integração nuclei

**História de usuário:** Como desenvolvedor avançado, quero usar templates nuclei para
cobertura de CVEs.

#### Critérios de aceitação

1. QUANDO nuclei está instalado (`which nuclei` exit 0) DEVE exibir checkbox "Incluir
   templates nuclei" na seleção de categorias.
2. QUANDO selecionado DEVE executar: `nuclei -u {url} -severity critical,high,medium
   -json -silent -rate-limit {rate}` como subprocesso.
3. DEVE converter cada linha JSON do nuclei para `Finding` com mapeamento:
   - `info.name` → `title`
   - `info.severity` → `severity`
   - `matched-at` → `evidence`
   - `info.reference` → `reference`
   - `template-id` → `id` com prefixo "NUCLEI-"
4. SE nuclei não está instalado DEVE exibir mensagem com instruções: "Instale nuclei:
   `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest`".
5. SE nuclei falha (exit != 0) DEVE exibir stderr como erro sem derrubar a análise.
6. DEVE respeitar rate limit configurado (passa `-rate-limit` ao nuclei).

### Requisito S4-12 — Seleção de categorias

**História de usuário:** Como usuário, quero escolher quais categorias de teste executar.

#### Critérios de aceitação

1. QUANDO modo ativo é selecionado DEVE exibir lista de categorias com checkbox:
   SQL Injection, XSS, Command Injection, SSTI, Path Traversal, Open Redirect, IDOR,
   Diretórios/Arquivos, Autenticação, Nuclei (se disponível).
2. QUANDO o usuário desmarca uma categoria DEVE excluí-la da execução.
3. DEVE haver botão "Selecionar todas" e "Limpar todas".
4. QUANDO nenhuma categoria está selecionada o botão Analisar DEVE estar desabilitado.

### Requisito S4-13 — Progresso e cancelamento granular

**História de usuário:** Como usuário, quero ver o progresso por categoria e poder
cancelar categorias individualmente.

#### Critérios de aceitação

1. ENQUANTO testes ativos executam DEVE exibir por categoria: nome, status (aguardando /
   em execução / concluída / cancelada), achados parciais.
2. QUANDO o usuário cancela uma categoria DEVE interromper apenas ela, mantendo as demais.
3. QUANDO o usuário cancela tudo DEVE interromper todas em até 2s.

## Requisitos não funcionais locais

- Concorrência padrão: 5 requisições simultâneas (configurável 1-20).
- Rate limit padrão: 10 req/s (configurável 1-50).
- Timeout por requisição: 10s para payloads normais, 15s para time-based (para dar margem
  ao threshold de 5s).
- Nenhum payload destrutivo: validação estática dos templates (scripts de CI podem
  verificar que templates não contêm DROP/DELETE/UPDATE/TRUNCATE).

## Critério de conclusão

- [ ] Todos os critérios S4-* verificados com fixtures.
- [ ] Motor de payloads testado com templates de cada categoria.
- [ ] Nuclei bridge testada com output gravado (sem nuclei real na CI).
- [ ] Nenhum payload YAML contém operação destrutiva (validação automatizada).
- [ ] Rate limit respeitado e verificável no log.
- [ ] Portões do Artigo III passam.
