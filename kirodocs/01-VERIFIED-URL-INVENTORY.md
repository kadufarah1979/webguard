# Verified kiro.dev URL Inventory (search-index derived)

## What this is and is NOT

This file was assembled **entirely** from `remote_web_search` results — the only network
channel that functions in this sandbox (see `00-NETWORK-DIAGNOSTIC.md`).

- **IS:** confirmation that these URLs exist and are indexed, with each page's title and the
  short snippet the search index returned.
- **IS NOT:** the documentation. Snippets are 1–2 sentences, capped at 30 verbatim words per
  source. They are typically only each page's opening paragraph. Body content, hook/steering
  schemas, field tables, trigger-type enumerations, and code examples are **not** present.

**Do not treat any snippet below as a complete or authoritative answer.** Nothing here was
written from memory; every line is traceable to a listed URL.

Content was rephrased for compliance with licensing restrictions where summarized.

## Mapping of the requested URLs to real, indexed URLs

The requested `/index.md` variants never returned an origin response. The search index shows
the canonical live paths use **trailing slashes, not `index.md`**:

| Requested | Indexed canonical URL | Exists per index? |
|---|---|---|
| `/docs/hooks/index.md` | [/docs/hooks/](https://kiro.dev/docs/hooks/) | yes |
| `/docs/steering/index.md` | [/docs/steering/](https://kiro.dev/docs/steering/) | yes |
| `/docs/specs/index.md` | [/docs/specs/](https://kiro.dev/docs/specs/) | yes |
| `/docs/specs/concepts/index.md` | `/docs/specs/concepts` | **no title/snippet returned — likely does not exist** |
| `/docs/cli/hooks/index.md` | [/docs/cli/hooks/](https://kiro.dev/docs/cli/hooks/) | yes |
| `/docs/cli/steering/index.md` | [/docs/cli/steering/](https://kiro.dev/docs/cli/steering/) | yes |
| `/docs/cli/v3/hooks/index.md` | [/docs/cli/v3/hooks/](https://kiro.dev/docs/cli/v3/hooks/) | yes |
| `/docs/cli/v3/index.md` | [/docs/cli/v3/](https://kiro.dev/docs/cli/v3/) | yes |
| `/llms.txt` | — | **not indexed; existence unconfirmed** |

Note on `/docs/specs/concepts`: the search tool echoed the URL back with an empty title and
empty snippet, and every real specs sub-page it surfaced was a *different* path
(`feature-specs/`, `bugfix-specs/`, `quick-spec/`, `best-practices/`). This suggests the
`concepts` page has been reorganized away, but because the proxy blocked us we **never saw an
HTTP status**, so this is inference from the index, not a confirmed 404.

## Snippets retrieved — Hooks

- [Hooks (IDE)](https://kiro.dev/docs/hooks/) — describes agent hooks as automated triggers
  that run agent prompts or shell commands in response to IDE events, replacing manual
  requests for routine work.
- [Hooks (CLI v3)](https://kiro.dev/docs/cli/v3/hooks/) — v3 hooks are described as standalone
  files with a versioned schema, two action types (shell commands and agent prompts), and
  added lifecycle triggers for specs, file deletion, and manual invocation; defined once in
  `.kiro/hooks/` and applying across all workspace agents.
- [Hooks (CLI)](https://kiro.dev/docs/cli/hooks/) — hooks run custom commands at points in the
  agent lifecycle and around tool execution, enabling validation, logging, formatting, and
  context gathering.
- [Hook types](https://kiro.dev/docs/hooks/types/) — covers the available trigger types and
  how to pick one. *(Trigger type names themselves were not in the snippet.)*
- [Hook examples](https://kiro.dev/docs/hooks/examples/) — real-world hook implementations with
  trigger type, target patterns, and full instructions.
- [Blog: agent hooks](https://kiro.dev/blog/automate-your-development-workflow-with-agent-hooks/)
  — frames hooks as if-then logic for the dev environment, driven by natural language.
- [Blog: README files](https://kiro.dev/blog/how-i-stopped-worrying-about-readme-files/) —
  mentions a hook configuration carrying a title, description, event, watched file paths, and
  instructions sent to Kiro when the event fires.

## Snippets retrieved — Steering

- [Steering (IDE)](https://kiro.dev/docs/steering/) — persistent workspace knowledge via
  markdown files so conventions, libraries, and standards don't need re-explaining per chat.
- [Steering (CLI)](https://kiro.dev/docs/cli/steering/) — same concept, explicitly located in
  `.kiro/steering/`.
- [Steering the agent (Web)](https://kiro.dev/docs/web/steering/) — Kiro Web (Preview) variant.
- [Configuration](https://kiro.dev/docs/cli/chat/configuration/) — notes that agents, prompts,
  skills, steering, settings, and sessions all resolve against `KIRO_HOME` when set.

The three inclusion modes (`always`, `fileMatch`, `manual`) appear only in **third-party**
sources ([LobeHub](https://lobehub.com/skills/pr-pm-prpm-creating-kiro-packages),
[Medium](https://medium.com/@pjay1010/efficient-token-usage-on-kiro-a-practical-guide-7c2da8d1070b)),
**not** in any official snippet retrieved. Treat as unverified.

## Snippets retrieved — Specs

- [Specs](https://kiro.dev/docs/specs/) — structured artifacts formalizing development of
  features and bug fixes, turning high-level ideas into detailed, trackable implementation plans.
- [Feature Specs](https://kiro.dev/docs/specs/feature-specs/) — structured path through
  requirements gathering, technical design, and implementation planning.
- [Requirements-First Workflow](https://kiro.dev/docs/specs/feature-specs/requirements-first/)
  — the traditional approach: establish what the system should do before how to build it.
- [Design-First Workflow](https://kiro.dev/docs/specs/feature-specs/tech-design-first/) —
  starts from technical design/architecture and derives feasible requirements from it.
- [Bugfix Specs](https://kiro.dev/docs/specs/bugfix-specs/) — models root-cause identification,
  what should change, and explicit preservation of what should not.
- [Quick Spec](https://kiro.dev/docs/specs/quick-spec/) — a session mode generating
  requirements, design, and tasks in one pass after up-front clarifying questions, instead of
  per-phase approval.
- [Best practices](https://kiro.dev/docs/specs/best-practices/) — indicates the workflow is
  chosen at spec creation and changing approach means creating a new Feature Spec.
- [Specs in CLI](https://kiro.dev/docs/cli/v3/specs/) — a built-in Spec agent on the unified
  engine, with verification between tasks.
- [Specs (Web)](https://kiro.dev/docs/web/specs/) — plan (requirements/design/tasks) then
  implement and open a PR, reviewable in-browser.

## Snippets retrieved — CLI v3 and related reference

- [CLI 3.0 (Early Access)](https://kiro.dev/docs/cli/v3/) — built on the same unified agent
  harness as the Kiro IDE and Kiro Web, so engine improvements ship to all clients together.
- [Custom agents](https://kiro.dev/docs/cli/custom-agents/) — each custom agent is a config
  file specifying accessible tools, permissions, and context.
- [Agent configuration reference](https://kiro.dev/docs/cli/custom-agents/configuration-reference/)
  — the richest snippet returned; mentions `name`, `description`, `prompt`, and
  `welcomeMessage` fields and support for `file://` URIs to keep long prompts external.
- [CLI commands](https://kiro.dev/docs/cli/reference/cli-commands/) — command/argument reference.
- [Settings](https://kiro.dev/docs/cli/reference/settings/) — telemetry, chat behavior, key
  bindings, feature toggles.
- [Built-in tools](https://kiro.dev/docs/cli/reference/built-in-tools/) — built-in tool collection.
- [Get started (CLI)](https://kiro.dev/docs/cli/) / [Get started (docs root)](https://kiro.dev/docs/)
- [What's new in IDE 1.0](https://kiro.dev/docs/whats-new-1-0/) — mentions defining custom
  agents as Markdown files with tag-based tool access (read, write, shell, web), inline MCP
  servers and permission rules, shareable via version control.

## THIRD-PARTY sources (NOT official documentation)

Surfaced by search; **unverified, may be outdated or wrong**. Included only because the task
asked for third-party leads if official access failed. Content is *not* endorsed as accurate.

- [github.com/awsdataarchitect/kiro-best-practices](https://github.com/awsdataarchitect/kiro-best-practices/blob/main/CONTRIBUTING.md)
  — snippet shows a `"then": { "type": "askAgent", "prompt": ... }` fragment, implying a
  `when`/`then` JSON hook shape.
- [kenhuangus.substack.com — hook/event-driven automation](https://kenhuangus.substack.com/p/chapter-11-hook-event-driven-automation)
  — claims two hook actions, `runCommand` and `askAgent`.
- [github.com/cremich/promptz.lib](https://github.com/cremich/promptz.lib/blob/main/steering/kiro-specs.md) — vendored steering file about Kiro specs.
- [github.com/jasonkneen/kiro](https://github.com/jasonkneen/kiro/blob/main/spec-process-guide/process/tasks-phase.md) — a spec-process guide describing a Requirements → Design → Tasks flow.
- [github.com/sanmak/specops](https://github.com/sanmak/specops/blob/main/docs/STEERING_GUIDE.md) — third-party steering guide.
- [gist: Quick Team Guide](https://gist.github.com/sai-praveen-os/9c66e4a06dc3c0119a727fd4cbcdef30)
- [zenn.dev Kiro Hooks guide (JA)](https://zenn.dev/qingwu/articles/5ff367c46a7e87),
  [zenn.dev Agent Steering (JA)](https://zenn.dev/oikon/articles/kiro-steering),
  [qes.co.jp steering priority (JA)](https://www.qes.co.jp/media/aws/Kiro/a799),
  [qes.co.jp agent hooks (JA)](https://www.qes.co.jp/media/aws/Kiro/a767)

These repos could not be cloned or read — `github.com` and `raw.githubusercontent.com` are
proxy-blocked and `gh` is unauthenticated. They are search-index leads only.

## Bottom line

The exact hook file schema, the enumerated trigger/event names, and the steering front-matter
inclusion syntax — the details most likely being asked about — were **not** retrievable. They
require either an unblocked fetch of the pages above or user-pasted content.
