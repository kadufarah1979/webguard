---
inclusion: manual
---

# Convenções por Tipo de Arquivo

> **Pasta `conditional/` — ativadores por glob pattern.**
> Ao preencher, troque o front-matter para o padrão real do projeto:
>
> ```yaml
> ---
> inclusion: fileMatch
> fileMatchPattern: "src/**/*.tsx"
> ---
> ```
>
> Este é o modo mais eficiente: a convenção de React só entra no contexto quando um `.tsx`
> está em jogo. Crie **um arquivo por tecnologia** em vez de um arquivo gigante com todas —
> caso contrário o glob deixa de ser seletivo e você paga por tudo.
>
> Nomeie o arquivo pela tecnologia: `frontend-react.md`, `api-endpoints.md`,
> `delphi-pascal.md`, `migrations-sql.md`.

## Escopo deste arquivo

- **Padrão de arquivos:** `TODO — ex.: src/**/*.tsx`
- **Se aplica a:** `TODO`

## Convenções obrigatórias

- `TODO`
- `TODO`

## Padrão correto

```
TODO — exemplo curto e real de código que segue o padrão.
Um exemplo concreto comunica mais que cinco parágrafos de descrição.
```

## Antipadrões

O que já causou problema aqui e não deve ser repetido.

```
TODO — exemplo do que NÃO fazer, com uma linha explicando o motivo.
```

## Checklist antes de commitar arquivo deste tipo

- [ ] `TODO`
- [ ] `TODO`

---

## Sugestões de arquivos para esta pasta

| Arquivo | `fileMatchPattern` sugerido |
|---|---|
| `frontend-react.md` | `src/**/*.{tsx,jsx}` |
| `api-endpoints.md` | `src/**/{routes,controllers}/**/*` |
| `testes.md` | `**/*.{test,spec}.*` |
| `migrations-sql.md` | `**/migrations/**/*.sql` |
| `infra-terraform.md` | `**/*.tf` |
| `ci-cd.md` | `.github/workflows/*.yml` |
