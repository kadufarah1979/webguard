# Identidade Visual — WebGuard "Hacker Edition"

> **Guia de estilo visual.** Este documento define a estética da interface e é referência
> para toda decisão de UI nas quatro sub-funcionalidades.
>
> Referência arquitetural: #[[file:../epic-design.md]]

## Filosofia

A interface transmite **competência técnica e controle**: o usuário é o operador de uma
ferramenta séria, não o consumidor de um app bonitinho. O visual evoca terminais,
ferramentas de pentest e dashboards de segurança — sem cair no clichê ilegível.

**Regra de ouro:** se uma escolha estética prejudica a legibilidade ou a usabilidade,
a usabilidade vence. Terminal aesthetic ≠ terminal limitations.

## Paleta de cores

Fundo quase preto com acentos neon. Saturação controlada para não cansar.

| Token | Hex | Uso |
|---|---|---|
| `bg-primary` | `#0D1117` | Fundo da janela (como GitHub dark) |
| `bg-secondary` | `#161B22` | Cards, painéis, áreas elevadas |
| `bg-input` | `#1C2128` | Campos de entrada |
| `border-subtle` | `#30363D` | Bordas de containers |
| `text-primary` | `#C9D1D9` | Texto normal (não branco puro — reduz fadiga) |
| `text-secondary` | `#8B949E` | Labels, metadata, timestamps |
| `text-muted` | `#484F58` | Placeholders, items desabilitados |
| `accent-green` | `#00FF41` | Primário — prompts, progresso, sucesso, títulos |
| `accent-cyan` | `#00D4FF` | Secundário — links, botões hover, informativo |
| `accent-red` | `#FF3E3E` | Severidade crítica, erros |
| `accent-orange` | `#FF9500` | Severidade alta |
| `accent-yellow` | `#FFD500` | Severidade média |
| `accent-blue` | `#58A6FF` | Severidade baixa |
| `accent-purple` | `#BC8CFF` | Nuclei, integrações externas |
| `glow-green` | `#00FF41` com 20% opacity | Glow sutil em foco |

## Tipografia

| Contexto | Fonte | Fallback | Tamanho |
|---|---|---|---|
| Interface toda | `JetBrains Mono` | `Fira Code`, `Source Code Pro`, `monospace` | 13px |
| Títulos/banners | `JetBrains Mono Bold` | — | 16px |
| Achados: evidência | `JetBrains Mono` | — | 12px |
| Achados: explicação | `JetBrains Mono` | — | 13px |
| Botões | `JetBrains Mono Medium` | — | 13px, uppercase |

**Toda a interface é monoespaçada.** Isso reforça o ar de terminal e garante alinhamento
natural em tabelas e logs.

## Componentes visuais

### Header / Banner de startup

Ao abrir, a janela exibe um ASCII art sutil do nome:

```
██╗    ██╗███████╗██████╗  ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗
██║    ██║██╔════╝██╔══██╗██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗
██║ █╗ ██║█████╗  ██████╔╝██║  ███╗██║   ██║███████║██████╔╝██║  ██║
██║███╗██║██╔══╝  ██╔══██╗██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
╚███╔███╔╝███████╗██████╔╝╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
 ╚══╝╚══╝ ╚══════╝╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝
                    [ Passive & Active Security Scanner ]
                              v1.0.0 :: ready
```

Renderizado em `accent-green` sobre `bg-primary`. Desaparece ao iniciar o primeiro scan
(ou ocupa um espaço fixo mínimo no topo).

### Campo de URL

```
┌─────────────────────────────────────────────────────────────┐
│ ➜  TARGET: │ https://example.com_                           │
└─────────────────────────────────────────────────────────────┘
```

- Prompt `➜  TARGET:` em `accent-green`
- Cursor piscante estilo terminal (bloco, não linha)
- Borda em `border-subtle`, muda para `accent-green` + glow no foco
- Validação inline: se inválida, borda muda para `accent-red`

### Seletor de modo

```
┌───────────────────────────────────┐
│  ○ PASSIVE  ●━━ ACTIVE ━━●       │
│                                   │
│  ⚠ MODO ATIVO: envia payloads    │
│    ao alvo. Use somente em        │
│    sistemas que você controla.    │
└───────────────────────────────────┘
```

- Toggle estilo switch com labels em uppercase mono
- `PASSIVE` em `accent-cyan`, `ACTIVE` em `accent-red`
- Aviso aparece com animação de fade-in ao selecionar ativo

### Categorias de teste (modo ativo)

```
┌─ MÓDULOS DE ATAQUE ─────────────────────────┐
│  [✓] SQL Injection          [✓] XSS         │
│  [✓] Command Injection      [✓] SSTI        │
│  [✓] Path Traversal         [✓] IDOR        │
│  [✓] Open Redirect          [✓] Dir Enum    │
│  [✓] Weak Auth              [ ] Nuclei      │
│                                              │
│  [SELECT ALL]  [CLEAR]                       │
└──────────────────────────────────────────────┘
```

- Checkboxes customizados com `[✓]` em verde, `[ ]` em cinza
- Nome das categorias em `text-primary` com hover em `accent-green`
- Nuclei em `accent-purple` quando disponível, `text-muted` quando não

### Botão de execução

```
╔══════════════════════════════╗
║   ▶  INICIAR VARREDURA      ║
╚══════════════════════════════╝
```

- Background `accent-green` com texto `bg-primary` (contraste invertido)
- Bordas duplas (Unicode box drawing)
- Hover: glow pulsante sutil
- Disabled: `text-muted` sem borda dupla
- Durante scan: muda para `■ ABORTAR` em `accent-red`

### Progresso durante scan

```
[■■■■■■■■■■░░░░░░░░░░] 47% :: analyzing headers...
├── [✓] DNS Resolution .............. 45ms
├── [✓] TLS Handshake ............... 120ms
├── [✓] HTTP GET .................... 340ms
├── [-] Security Headers ............ running
└── [ ] Cookies ..................... waiting
```

- Barra de progresso com `■` (preenchido) e `░` (vazio) em mono
- Cada etapa com indicador: `[✓]` verde, `[-]` amarelo piscante, `[ ]` cinza
- Tempo em `text-secondary`
- Texto da etapa atual com efeito de digitação (caractere a caractere, 50ms/char)

### Achados

```
┌─[CRITICAL]──────────────────────────────────────────────────┐
│ HDR-CSP-MISSING :: Content-Security-Policy ausente          │
├─────────────────────────────────────────────────────────────┤
│ EVIDENCE:                                                    │
│ > O cabeçalho Content-Security-Policy não está presente     │
│ > na resposta HTTP.                                          │
│                                                              │
│ RISK:                                                        │
│ Sem CSP, o navegador não restringe quais scripts podem      │
│ executar, facilitando exploração de XSS.                    │
│                                                              │
│ FIX:                                                         │
│ ┌──────────────────────────────────────────────────────┐    │
│ │ Content-Security-Policy: default-src 'self';         │    │
│ │   script-src 'self'; object-src 'none'         [📋]  │    │
│ └──────────────────────────────────────────────────────┘    │
│                                                              │
│ REF: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP  │
└─────────────────────────────────────────────────────────────┘
```

- Tag de severidade com cor correspondente e borda colorida
- `CRITICAL` → `accent-red`, `HIGH` → `accent-orange`, `MEDIUM` → `accent-yellow`,
  `LOW` → `accent-blue`, `INFO` → `text-secondary`
- Seções com labels em uppercase `text-secondary`
- Bloco de correção com fundo `bg-input` e botão copiar `[📋]`
- Ao expandir, efeito de "revelação" (slide down, 200ms)

### Log de requisições

```
┌─ REQUEST LOG ─────────────────────────────────────────────────────────┐
│ TIME      METHOD  URL                              STATUS  ELAPSED    │
│────────────────────────────────────────────────────────────────────────│
│ 18:42:01  GET     https://target.com/              200     340ms      │
│ 18:42:01  GET     https://target.com/robots.txt    404      89ms      │
│ 18:42:02  GET     https://target.com/.well-known/  200     120ms      │
│ 18:42:02  ✗ BLOCKED  /admin (scope violation)      ---     ---        │
└───────────────────────────────────────────────────────────────────────┘
```

- Tabela alinhada em mono (colunas com largura fixa)
- Linhas bloqueadas em `accent-red` com `✗ BLOCKED`
- Status 2xx em `accent-green`, 3xx em `accent-cyan`, 4xx em `accent-yellow`, 5xx em `accent-red`
- Scroll com scrollbar fina estilo terminal

### Dialog de consentimento (modo ativo)

```
╔══════════════════════════════════════════════════════════════╗
║  ⚠  AVISO DE SEGURANÇA                                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  O modo ATIVO enviará payloads de teste ao alvo:            ║
║  https://target.com                                          ║
║                                                              ║
║  Isso pode:                                                  ║
║  • Gerar logs no servidor alvo                               ║
║  • Disparar alertas de WAF/IDS                               ║
║  • Ser ILEGAL sem autorização do proprietário                ║
║                                                              ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │ [✓] Eu sou o proprietário ou tenho autorização       │   ║
║  │     escrita para testar este sistema.                 │   ║
║  └──────────────────────────────────────────────────────┘   ║
║                                                              ║
║     [CANCELAR]              [▶ CONFIRMAR E PROSSEGUIR]       ║
╚══════════════════════════════════════════════════════════════╝
```

- Fundo semi-transparente escuro atrás (overlay)
- Borda dupla em `accent-orange`
- Checkbox obrigatório para habilitar o botão de confirmação
- Botão confirmar só acende (verde) após marcar o checkbox

### Animações e efeitos

| Efeito | Onde | Implementação |
|---|---|---|
| Typing effect | Etapa atual no progresso | `GLib.timeout_add(50, append_char)` |
| Cursor piscante | Campo de URL quando vazio | CSS `animation: blink 1s step-end infinite` |
| Glow on focus | Campos e botões | CSS `box-shadow` com `glow-green` |
| Pulse | Botão durante hover | CSS `animation: pulse 2s ease-in-out infinite` |
| Scanline | Background da janela (muito sutil) | CSS pseudo-element com gradiente repeating |
| Fade-in | Achados aparecendo | CSS `animation: fadeIn 0.3s ease-out` |
| Status blink | `[-]` running indicator | CSS `animation: blink 0.8s` |

### Scanline effect (opcional, muito sutil)

Uma linha semi-transparente (`rgba(0, 255, 65, 0.03)`) percorrendo a tela de cima a baixo
lentamente (8s por ciclo). Imperceptível conscientemente mas adiciona o "feel" de monitor
CRT. Desabilitável nas preferências.

## Implementação técnica

### CSS customizado via GTK4

GTK4 suporta CSS via `Gtk.CssProvider`. O tema hacker é um arquivo `style.css` carregado
no startup:

```python
css_provider = Gtk.CssProvider()
css_provider.load_from_path(get_resource_path("style.css"))
Gtk.StyleContext.add_provider_for_display(
    Gdk.Display.get_default(),
    css_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)
```

### Forçar dark mode

```python
style_manager = Adw.StyleManager.get_default()
style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
```

### Fonte monoespaçada global

Via CSS:
```css
* {
    font-family: "JetBrains Mono", "Fira Code", "Source Code Pro", monospace;
    font-size: 13px;
}
```

### Widgets customizados para efeitos

- `TypingLabel` — GtkLabel que revela texto caractere a caractere via timeout
- `ProgressBar` — custom draw com `■░` em vez da barra nativa
- `BlinkingCursor` — GtkLabel com animação CSS de blink

## Responsividade

A janela tem tamanho mínimo de **900×600** e se adapta a telas maiores. Em telas 4K:
- Escala com o fator do GNOME (font-size escala automaticamente)
- Largura máxima de conteúdo: 1200px (centralizado)

## Acessibilidade (preservada)

O visual hacker **não** compromete:
- Navegação por teclado (Tab order, Enter para ativar, Esc para fechar dialogs)
- Contraste: todas as combinações de cor passam WCAG AA em fonte mono 13px
- Screen readers: labels e ARIA roles intactos (o CSS não afeta a árvore de acessibilidade)
- Animações respeitam `prefers-reduced-motion` do sistema

## Ícone da aplicação

SVG com um escudo (`shield`) estilizado em neon verde sobre fundo escuro, com um `>_`
(prompt) dentro do escudo. Simples, reconhecível em 16px e 512px.

## Nome estilizado

Em contextos onde o nome aparece por extenso, usar:
- UI: `WebGuard` (sem estilização extra, a fonte mono já basta)
- Terminal/about: `web::guard v1.0.0`
- Splash: ASCII art acima
