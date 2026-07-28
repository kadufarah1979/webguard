# Requisitos do Épico — Analisador de Segurança Web (Passivo + Ativo)

> **Regras globais do módulo · Épico acima de 80h**
>
> As leis abaixo valem para **todas** as sub-funcionalidades. Uma sub-funcionalidade pode
> adicionar restrições; nunca pode remover ou contradizer as daqui.

## Status

| Campo | Valor |
|---|---|
| Fase | `Aprovado` |
| Estimativa total | ~140h |
| Sub-funcionalidades | 4 |
| Aprovado por | Usuário |
| Data | 2026-07-28 |

## Introdução

Ferramenta desktop para Ubuntu/GNOME que combina **análise passiva** e **testes ativos de
vulnerabilidade** em uma interface unificada. O usuário informa a URL de um site e escolhe
o modo de operação:

- **Modo Passivo** — observa o que o servidor entrega a um visitante comum e conclui a
  partir disso. Seguro para qualquer site.
- **Modo Ativo** — envia payloads de teste para descobrir vulnerabilidades exploráveis.
  Exclusivo para sistemas que o usuário controla ou tem autorização escrita para testar.

A ferramenta entrega achados acionáveis: cada apontamento diz o que está errado, demonstra
com evidência literal, explica o impacto real e oferece a correção concreta.

Uso pessoal, em uma única máquina. Sem servidor, sem conta, sem telemetria.

## Fronteira do módulo

**Este módulo é responsável por:**

- Coletar a resposta HTTP, metadados TLS e conteúdo de uma URL informada.
- Analisar passivamente: cabeçalhos, certificado, cookies, CORS, recursos, JS.
- Testar ativamente: injeção (SQL, XSS, command injection, template injection), traversal
  de caminho, IDOR, open redirect, SSRF cego, enumeração de diretórios e arquivos
  sensíveis, autenticação fraca, e vulnerabilidades conhecidas via templates.
- Apresentar achados em interface GNOME nativa, com exportação.
- Integrar opcionalmente com `nuclei` (se instalado) para cobertura estendida.

**Este módulo NÃO é responsável por:**

- Análise autenticada com sessão do alvo (não faz login automático — aceita cookies/tokens
  fornecidos manualmente para testar áreas protegidas).
- Varredura em lote ou agendada — uma URL por vez, iniciada por ação humana explícita.
- Correção automática de qualquer coisa no alvo.
- Exploração pós-descoberta (exfiltração, escalação, persistência).
- Varredura de portas ou enumeração de subdomínios (fora do escopo HTTP).

**Fora de escopo da v1:** histórico e comparação entre execuções, empacotamento
Flatpak/Flathub, spider/crawler automático (o escopo ativo é por URL/endpoint informado),
análise de páginas que exigem renderização JavaScript completa.

## Leis globais

### L-1 — Dois modos com fronteiras explícitas

A ferramenta opera em exatamente dois modos. O modo determina quais requisições são
permitidas:

**Modo Passivo** — só emite requisições para:
1. A URL informada e sua cadeia de redirects.
2. Sub-recursos referenciados pelo documento retornado.
3. `/robots.txt` e `/.well-known/security.txt`.
4. Handshakes TLS para identificar versões aceitas.

**Modo Ativo** — além do escopo passivo, pode:
5. Repetir requisições com payloads de teste em parâmetros, cabeçalhos e corpo.
6. Sondar caminhos de uma wordlist definida (enumeração de diretórios/arquivos).
7. Testar variações de entrada para detectar injeção, traversal e redirecionamento.
8. Executar templates de vulnerabilidade (internos ou do nuclei).

O modo é escolhido pelo usuário **antes** da execução e não muda durante ela. O modo
ativo **jamais** é executado sem consentimento explícito.

### L-2 — Consentimento obrigatório para modo ativo

Antes de qualquer execução ativa, a interface DEVE:
1. Exibir aviso claro de que payloads de teste serão enviados ao alvo.
2. Informar que isso pode ser ilegal sem autorização do proprietário.
3. Exigir confirmação explícita ("Eu sou o proprietário ou tenho autorização escrita").
4. Registrar data, hora e URL do consentimento no log local da execução.

O botão de execução ativa não pode ser acionado por acidente (não é o padrão, exige
seleção deliberada do modo).

### L-3 — Transparência e comedimento

Toda requisição carrega User-Agent identificável e fixo. As requisições ao alvo respeitam:
- **Modo Passivo:** intervalo mínimo configurável (padrão 200ms), serializado.
- **Modo Ativo:** concorrência configurável (padrão 5 threads), com rate limit por segundo
  configurável (padrão 10 req/s). O usuário pode ajustar para não derrubar o alvo.

### L-4 — Privacidade: nada sai da máquina

A URL analisada, os resultados e qualquer dado coletado nunca são enviados a terceiros.
Sem telemetria, sem relatório de erro remoto, sem consulta a API externa. A base de
payloads e de vulnerabilidades conhecidas é local e embarcada; atualização é ato explícito.

### L-5 — Separação entre coleta, ataque e análise

Três camadas separadas:
- **Coletor** — emite requisições HTTP conforme o modo autorizado.
- **Motor de payloads** — gera variações de entrada e as submete via coletor.
- **Analisador** — função pura sobre respostas coletadas, decide se há achado.

Consequência: todo analisador é testável offline por fixture. A suíte de testes nunca
acessa a internet.

### L-6 — Formato único de achado

Todo apontamento tem: identificador estável, severidade, título, **evidência literal**
(o que foi enviado + o que foi recebido), explicação do risco, correção concreta, e
referência (CWE, OWASP, CVE quando aplicável). Achado sem evidência não é emitido.

### L-7 — Nenhum falso absoluto

Resultado inconclusivo é `Indeterminado` com motivo. Nunca "seguro" por ausência de
evidência, nunca "vulnerável" por suposição. No modo ativo, "vulnerável" exige evidência
de comportamento anômalo **observado**, não apenas o envio do payload.

### L-8 — Interface sempre responsiva

Nenhuma operação de rede ocorre na thread da interface. A janela permanece interativa
durante toda a execução, com progresso visível, log em tempo real e cancelamento funcional.

### L-9 — Falha isolada

Falha de um analisador ou de um payload não interrompe os demais nem derruba a aplicação.
Cada módulo de teste reporta seus próprios erros sem contaminar os vizinhos.

## Regras de negócio transversais

| # | Regra | Vale para |
|---|---|---|
| RN-1 | Escala de severidade: `Crítica`, `Alta`, `Média`, `Baixa`, `Informativo` | Todas |
| RN-2 | `Crítica`/`Alta` exigem impacto concreto demonstrado ou reproduzível | Todas |
| RN-3 | No modo passivo, ausência de cabeçalho recomendado é no máximo `Média` | Passivo |
| RN-4 | No modo ativo, vulnerabilidade confirmada com resposta anômala é no mínimo `Alta` | Ativo |
| RN-5 | Identificador de achado é estável entre versões | Todas |
| RN-6 | Todo texto de interface e de achado em português do Brasil | Todas |
| RN-7 | Payloads não devem causar dano permanente ao alvo (sem DROP TABLE, sem escrita destrutiva) | Ativo |
| RN-8 | Payloads de detecção usam técnicas de confirmação inofensivas (sleep-based, reflexão, cálculo) | Ativo |

## Requisitos de nível épico

### Requisito E-1 — Análise passiva de ponta a ponta

**História de usuário:** Como desenvolvedor, quero informar a URL de um site e receber
apontamentos de segurança passivos, para saber o que corrigir sem atacar o alvo.

#### Critérios de aceitação

1. QUANDO o usuário informa uma URL e aciona análise passiva ENTÃO o sistema DEVE executar
   todos os analisadores passivos e apresentar achados agrupados por severidade.
2. QUANDO a URL é informada sem esquema ENTÃO o sistema DEVE assumir `https://` e registrar.
3. SE a URL é sintaticamente inválida ENTÃO o sistema DEVE recusar sem emitir requisição.
4. SE o host não resolve ou recusa conexão ENTÃO o sistema DEVE exibir o motivo e preservar
   achados dos analisadores já concluídos.
5. ENQUANTO a análise está em curso DEVE exibir etapa atual e permitir cancelamento.
6. QUANDO termina DEVE informar data, hora e URL final após redirects.

### Requisito E-2 — Teste ativo de vulnerabilidades

**História de usuário:** Como desenvolvedor testando meu próprio site, quero executar
testes ativos de vulnerabilidade, para descobrir falhas exploráveis antes de um atacante.

#### Critérios de aceitação

1. QUANDO o usuário seleciona modo ativo e confirma consentimento (L-2) ENTÃO o sistema
   DEVE executar os módulos de teste ativo selecionados contra o alvo.
2. QUANDO um payload produz resposta anômala indicativa de vulnerabilidade ENTÃO o sistema
   DEVE registrar o achado com: payload enviado, resposta recebida, e classificação.
3. SE o usuário não confirma consentimento ENTÃO o sistema DEVE recusar a execução ativa
   e oferecer o modo passivo como alternativa.
4. QUANDO o usuário seleciona categorias específicas de teste ENTÃO o sistema DEVE executar
   apenas as selecionadas, não todas.
5. ENQUANTO testes ativos executam DEVE exibir progresso por categoria, achados em tempo
   real, e permitir cancelamento granular (por categoria ou total).
6. QUANDO um teste causa timeout ou erro de conexão ENTÃO o sistema DEVE registrar, reduzir
   concorrência automaticamente, e continuar com os demais.

### Requisito E-3 — Achados acionáveis

**História de usuário:** Como desenvolvedor, quero que cada apontamento me diga exatamente
o que fazer, para que eu não precise pesquisar o significado.

#### Critérios de aceitação

1. QUANDO um achado é apresentado ENTÃO DEVE exibir severidade, evidência literal (payload
   enviado + resposta), explicação do risco e correção concreta.
2. QUANDO a correção envolve configuração DEVE apresentar o valor sugerido copiável.
3. SE um analisador não conclui DEVE registrar como `Indeterminado` com motivo.
4. QUANDO nenhum problema é encontrado DEVE indicar o que foi verificado e passou.
5. QUANDO o achado tem CWE/CVE associado DEVE exibir o identificador com link.

### Requisito E-4 — Registro de atividade

**História de usuário:** Como responsável pelo uso da ferramenta, quero ver exatamente o
que ela fez, para comprovar que não excedeu o escopo autorizado.

#### Critérios de aceitação

1. QUANDO qualquer análise executa DEVE registrar todas as requisições emitidas com
   timestamp, método, URL, código de resposta e tamanho.
2. QUANDO o usuário solicita DEVE exibir o log completo da última execução, filtrável.
3. QUANDO em modo ativo DEVE registrar também o payload enviado em cada requisição.
4. SE uma requisição é bloqueada pela camada de coleta (violação de L-1) DEVE registrar
   como erro interno visível.

### Requisito E-5 — Exportação do relatório

**História de usuário:** Como desenvolvedor, quero exportar o resultado completo.

#### Critérios de aceitação

1. QUANDO exporta em Markdown DEVE gerar documento com URL, data, modo utilizado, e todos
   os achados com severidade, evidência e correção.
2. QUANDO exporta em JSON DEVE gerar estrutura versionada para processamento automatizado.
3. QUANDO exporta em HTML DEVE gerar relatório visual navegável por severidade.
4. SE o destino não é acessível DEVE informar a falha sem perder o resultado em memória.

### Requisito E-6 — Integração com nuclei (opcional)

**História de usuário:** Como desenvolvedor avançado, quero usar templates do nuclei para
cobertura estendida de CVEs conhecidos, sem sair da ferramenta.

#### Critérios de aceitação

1. QUANDO nuclei está instalado no sistema DEVE exibir opção de executar templates nuclei.
2. QUANDO o usuário seleciona categorias de templates DEVE executar nuclei como subprocesso
   com os parâmetros adequados e capturar a saída.
3. QUANDO nuclei reporta achados DEVE convertê-los para o formato único de achado (L-6) e
   apresentar junto aos achados internos.
4. SE nuclei não está instalado DEVE informar com instruções de instalação e continuar
   funcionando apenas com o motor interno.
5. QUANDO nuclei retorna erro DEVE exibir a mensagem sem derrubar a análise.

## Requisitos não funcionais do módulo

- **Desempenho:** análise passiva completa em até 30s; teste ativo de uma categoria em até
  2min para um site típico; a interface responde em menos de 100ms durante execução.
- **Segurança:** herda #[[file:../../constitution.md]] e adiciona: conteúdo recebido do alvo
  é dado hostil — nunca executado, nunca interpretado como markup na interface, truncado
  antes de exibir. Payloads embarcados não contêm exploits destrutivos.
- **Confiabilidade:** falha de um módulo não interrompe os demais.
- **Testabilidade:** cobertura mínima de 85% na camada de análise, suíte offline.
- **Plataforma:** Ubuntu 24.04 LTS+, GNOME, Python 3.12+, GTK4 + libadwaita.
- **Acessibilidade:** navegável por teclado, tema claro/escuro do sistema.

## Decomposição

| Sub-funcionalidade | Escopo | Estimativa | Depende de |
|---|---|---|---|
| `01-nucleo-e-cabecalhos` | Janela GTK, entrada de URL, camada de coleta com travas L-1/L-3, motor de achados, analisador passivo de cabeçalhos, seleção de modo, consentimento L-2 | ~34h | — |
| `02-tls-cookies-e-transporte` | Certificado/TLS, cookies, redirect, cadeia, HSTS preload | ~28h | `01` |
| `03-analise-documento-e-relatorio` | CORS, SRI, conteúdo misto, banners, source maps, libs JS vulneráveis, exportação MD/JSON/HTML | ~32h | `01` |
| `04-motor-ativo` | Motor de payloads (SQLi, XSS, command injection, template injection, path traversal, IDOR, open redirect, enumeração de diretórios), integração nuclei | ~46h | `01` |

**Ordem:** `01` primeiro (fundação e já útil sozinha), depois `02`, `03` e `04` em qualquer
ordem entre si. A `04` é a mais complexa e independe das análises passivas de `02`/`03`.

## Categorias de teste ativo (escopo da sub-funcionalidade 04)

| Categoria | Técnica de detecção | Severidade típica |
|---|---|---|
| SQL Injection | Payloads time-based (SLEEP/WAITFOR), error-based, boolean-based | Crítica |
| XSS Refletido | Injeção de marcadores únicos, verificação de reflexão sem encoding | Alta |
| XSS Armazenado | Detecção limitada: verifica se payload persiste em GET subsequente | Alta |
| Command Injection | Payloads time-based (sleep), concatenação de comandos | Crítica |
| Template Injection (SSTI) | Expressões matemáticas ({{7*7}}), verificação de avaliação | Alta |
| Path Traversal | Sequências ../.. com variações de encoding, verificação de conteúdo | Alta |
| Open Redirect | Payloads em parâmetros de redirecionamento, verificação de Location | Média |
| IDOR | Variação incremental/previsível de IDs em endpoints, comparação de respostas | Alta |
| Enumeração de diretórios | Wordlist de caminhos sensíveis (.git, .env, backup, admin) | Média-Alta |
| Arquivos sensíveis expostos | .git/config, .env, .DS_Store, wp-config.php, etc. | Alta |
| Autenticação fraca | Credenciais padrão em painéis conhecidos, rate limit ausente | Alta |
| Cabeçalhos de segurança em endpoints | CSP bypass, CORS misconfiguration em APIs | Média |
| Vulnerabilidades conhecidas (nuclei) | Templates da comunidade por tecnologia/CVE | Variável |

## Perguntas abertas

| # | Pergunta | Bloqueia | Status |
|---|---|---|---|
| 1 | Fixar `ruff` + `mypy` + `pytest` como portões de qualidade na constituição? | Nenhuma tarefa diretamente | Aberta |
| 2 | Base de bibliotecas JS vulneráveis: embarcar Retire.js (verificar licença) ou apenas detectar versão? | `03` | Aberta |
| 3 | Sites que exigem JS para renderizar: aceitar HTML vazio com aviso na v1? | `03` | Aberta |
| 4 | Wordlist de enumeração de diretórios: embarcar uma curada (~500 caminhos) ou permitir wordlist externa? | `04` | Aberta |
| 5 | Para SQLi time-based, qual tempo de sleep usar como threshold? (sugestão: 5s) | `04` | Aberta |

## Critério de conclusão do épico

- [ ] As quatro sub-funcionalidades concluídas e verificadas.
- [ ] E-1 a E-6 verificáveis de ponta a ponta contra um alvo controlado.
- [ ] Modo ativo **nunca** executa sem consentimento explícito (L-2) — verificar por teste.
- [ ] Nenhuma lei global violada — registro de requisições comprova conformidade.
- [ ] Payloads ativos não causam dano permanente (RN-7) — verificar por revisão.
- [ ] Suíte completa executando offline, sem acesso à rede.
- [ ] nuclei integrado e funcional quando presente, graceful quando ausente.
