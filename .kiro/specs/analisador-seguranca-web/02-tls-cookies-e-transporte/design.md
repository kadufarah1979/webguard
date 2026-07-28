# Design Local — TLS, Cookies e Transporte

> Arquitetura macro: #[[file:../epic-design.md]]
> Requisitos: #[[file:requirements.md]]

## Status

| Campo | Valor |
|---|---|
| Fase | `Em revisão` |
| Aprovado por | `PENDENTE` |

## Conformidade com o épico

| Item do épico | Consumo |
|---|---|
| ADE-2 (registry) | Registra 3 novos analisadores |
| ScanRecord.tls | Preenche `TLSInfo` na coleta |
| ScanRecord.cookies | Preenche `CookieInfo[]` |
| Finding unificado | Todos os achados seguem o formato |

## Visão geral

Adiciona 3 analisadores passivos ao registry e expande o collector para preencher os campos
`tls` e `cookies` do `ScanRecord`.

## Componentes

### `webguard.core.collector` — extensão

Modifica `collect()` para:
- Após resposta, extrair cert chain via `ssl.SSLSocket.getpeercert()` e popular `TLSInfo`
- Extrair cookies via `httpx.Cookies` e popular `CookieInfo[]`

### `webguard.core.tls_probe` — novo módulo

```python
async def probe_tls_versions(host: str, port: int, guard: RequestGuard) -> list[str]:
    """Tenta handshake com cada versão e retorna as aceitas."""
```

Usa `ssl.SSLContext` com `maximum_version` forçado para cada tentativa. Não passa pelo
httpx — é socket direto (permitido por L-1 item 4).

### `webguard.analyzers.passive.tls`

```python
@analyzer(mode="passive", name="tls-certificate")
async def analyze_tls(record: ScanRecord) -> list[Finding]:
    ...
```

### `webguard.analyzers.passive.cookies`

```python
@analyzer(mode="passive", name="cookies")
async def analyze_cookies(record: ScanRecord) -> list[Finding]:
    ...
```

Heurística para "cookie de sessão": nome contém `session`, `sess`, `sid`, `token`, `auth`,
`csrf` (case-insensitive).

### `webguard.analyzers.passive.transport`

```python
@analyzer(mode="passive", name="transport")
async def analyze_transport(record: ScanRecord) -> list[Finding]:
    ...
```

Verifica redirect HTTP→HTTPS e qualidade do HSTS.

## Decisões locais

### ADL-4 — Probe TLS com socket direto

- **Decisão:** usar `ssl` stdlib em vez de httpx para testar versões de protocolo.
- **Motivo:** httpx não expõe controle sobre `maximum_version`; lib `cryptography` é
  overkill para apenas testar se o handshake fecha.

### ADL-5 — Heurística de cookie de sessão por nome

- **Decisão:** julgar se cookie é "de sessão" pelo nome (regex em palavras-chave).
- **Motivo:** sem estado (não faz login), é a única informação disponível. Achado declara
  `confidence: "likely"` quando baseado em heurística.

## Rastreabilidade

| Requisito | Onde |
|---|---|
| S2-1 | `tls.py` |
| S2-2 | `tls_probe.py` + `tls.py` |
| S2-3 | `cookies.py` |
| S2-4 | `transport.py` |
