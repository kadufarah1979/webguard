"""RequestGuard — ponto único de saída HTTP (ADE-1, L-1, L-3)."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from webguard.core.models import (
    GuardViolation,
    Mode,
    RateLimiter,
    RequestLog,
    ScanContext,
)


class RequestGuard:
    """Valida modo vs. destino antes de emitir, registra toda requisição no log."""

    PASSIVE_ALLOWED_PATHS = frozenset({"/robots.txt", "/.well-known/security.txt"})

    def __init__(
        self,
        mode: Mode,
        target_url: str,
        rate_limiter: RateLimiter,
        ctx: ScanContext,
        client: httpx.AsyncClient,
    ) -> None:
        self._mode = mode
        self._target_host = urlparse(target_url).hostname or ""
        self._target_url = target_url
        self._rate_limiter = rate_limiter
        self._ctx = ctx
        self._client = client
        self._allowed_external_urls: set[str] = set()

    @property
    def mode(self) -> Mode:
        return self._mode

    def allow_url(self, url: str) -> None:
        """Registra uma URL externa como permitida (sub-recursos referenciados)."""
        self._allowed_external_urls.add(url)

    def is_allowed(self, url: str) -> bool:
        """Verifica se a URL está no escopo do modo atual."""
        parsed = urlparse(url)
        request_host = (parsed.hostname or "").lower()
        target_host = self._target_host.lower()

        # Mesmo host sempre permitido
        if request_host == target_host:
            if self._mode == Mode.PASSIVE:
                return True
            else:
                # Modo ativo: qualquer path do mesmo host é permitido
                return True

        # URL explicitamente permitida (sub-recursos referenciados)
        if url in self._allowed_external_urls:
            return True

        # Modo ativo: hosts diferentes não são permitidos (L-1)
        return False

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        content: str | None = None,
        timeout: float = 15.0,
        follow_redirects: bool = True,
    ) -> httpx.Response:
        """Emite requisição se permitida; bloqueia e loga se não."""
        now = datetime.now(timezone.utc)

        if not self.is_allowed(url):
            # Registra violação bloqueada
            blocked_log = RequestLog(
                timestamp=now,
                method=method,
                url=url,
                headers_sent=headers or {},
                payload=content,
                status_code=None,
                response_headers={},
                response_body_snippet="",
                elapsed_ms=0.0,
                mode=self._mode.value,
                blocked=True,
                block_reason=f"URL fora do escopo do modo {self._mode.value}",
            )
            self._ctx.add_request_log(blocked_log)
            raise GuardViolation(
                f"Requisição bloqueada: {method} {url} — fora do escopo {self._mode.value}"
            )

        # Rate limiting
        await self._rate_limiter.acquire()

        try:
            start = datetime.now(timezone.utc)
            response = await self._client.request(
                method,
                url,
                headers=headers,
                content=content,
                timeout=timeout,
                follow_redirects=follow_redirects,
            )
            elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000

            # Registra no log
            body_snippet = response.text[:4096] if response.text else ""
            log_entry = RequestLog(
                timestamp=now,
                method=method,
                url=url,
                headers_sent=headers or {},
                payload=content,
                status_code=response.status_code,
                response_headers=dict(response.headers),
                response_body_snippet=body_snippet,
                elapsed_ms=elapsed,
                mode=self._mode.value,
            )
            self._ctx.add_request_log(log_entry)

            return response

        finally:
            self._rate_limiter.release()
