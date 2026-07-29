"""Controller — orquestra execução em thread worker (ADE-5, L-8, L-9)."""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Callable

import httpx

from webguard.core.collector import Collector
from webguard.core.guard import RequestGuard
from webguard.core.models import (
    CollectError,
    Finding,
    Mode,
    RateLimiter,
    ScanContext,
    ScanMetadata,
    Severity,
    Confidence,
)
from webguard.core.registry import get_analyzers


# Callback types
OnFinding = Callable[[Finding], None]
OnProgress = Callable[[str, float], None]  # (stage_name, percent 0-1)
OnDone = Callable[[ScanMetadata, list[Finding]], None]
OnError = Callable[[str], None]


class ScanController:
    """Orquestra a execução de um scan completo."""

    def __init__(self) -> None:
        self._ctx: ScanContext | None = None
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start_scan(
        self,
        url: str,
        mode: Mode,
        *,
        on_finding: OnFinding | None = None,
        on_progress: OnProgress | None = None,
        on_done: OnDone | None = None,
        on_error: OnError | None = None,
    ) -> None:
        """Lança a thread worker com o scan."""
        if self.is_running:
            return

        self._ctx = ScanContext()
        self._thread = threading.Thread(
            target=self._run_in_thread,
            args=(url, mode, on_finding, on_progress, on_done, on_error),
            daemon=True,
        )
        self._thread.start()

    def cancel(self) -> None:
        """Sinaliza cancelamento."""
        if self._ctx:
            self._ctx.cancel()

    def _run_in_thread(
        self,
        url: str,
        mode: Mode,
        on_finding: OnFinding | None,
        on_progress: OnProgress | None,
        on_done: OnDone | None,
        on_error: OnError | None,
    ) -> None:
        """Executa o event loop async na thread worker."""
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                self._execute_scan(url, mode, on_finding, on_progress, on_done, on_error)
            )
        except Exception as e:
            if on_error:
                on_error(f"Erro fatal: {e}")
        finally:
            loop.close()

    async def _execute_scan(
        self,
        url: str,
        mode: Mode,
        on_finding: OnFinding | None,
        on_progress: OnProgress | None,
        on_done: OnDone | None,
        on_error: OnError | None,
    ) -> None:
        """Pipeline principal do scan."""
        assert self._ctx is not None
        ctx = self._ctx
        start_time = time.monotonic()
        all_findings: list[Finding] = []

        # Notifica início
        if on_progress:
            on_progress("Iniciando coleta...", 0.0)

        # Criar client, rate limiter e guard
        rate_limiter = RateLimiter(mode=mode)

        async with httpx.AsyncClient(verify=True, http2=True) as client:
            guard = RequestGuard(
                mode=mode,
                target_url=url,
                rate_limiter=rate_limiter,
                ctx=ctx,
                client=client,
            )

            # Fase 1: Coleta
            if on_progress:
                on_progress("Coletando resposta HTTP...", 0.1)

            collector = Collector()
            result = await collector.collect(url, guard, ctx)

            if isinstance(result, CollectError):
                if on_error:
                    on_error(f"Falha na coleta: {result.reason} — {result.detail}")
                if on_done:
                    metadata = ScanMetadata(
                        target_url=url,
                        final_url=result.url,
                        mode=mode,
                        timestamp=ctx.request_log[0].timestamp if ctx.request_log else __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
                        duration_ms=(time.monotonic() - start_time) * 1000,
                        total_requests=len(ctx.request_log),
                        cancelled=ctx.is_cancelled(),
                    )
                    on_done(metadata, all_findings)
                return

            record = result

            # Fase 2: Executar analisadores
            # Modo ativo roda passivos + ativos; passivo roda só passivos
            analyzers = get_analyzers(mode.value)
            if mode == Mode.ACTIVE:
                analyzers = get_analyzers("passive") + get_analyzers("active")
            total = len(analyzers)

            for i, entry in enumerate(analyzers):
                if ctx.is_cancelled():
                    break

                stage_name = f"Analisando: {entry.name}..."
                progress = 0.2 + (0.7 * (i / max(total, 1)))
                if on_progress:
                    on_progress(stage_name, progress)

                try:
                    findings = await entry.fn(record)
                    for finding in findings:
                        all_findings.append(finding)
                        ctx.add_finding(finding)
                        if on_finding:
                            on_finding(finding)
                except Exception as e:
                    # L-9: falha isolada — registra e continua
                    error_finding = Finding(
                        id=f"ERR-{entry.name.upper()}",
                        category="internal",
                        severity=Severity.INDETERMINATE,
                        title=f"Erro no analisador {entry.name}",
                        evidence=str(e),
                        explanation="O analisador falhou durante a execução.",
                        remediation="Verifique os logs e reporte o bug.",
                        reference="",
                        analyzer=entry.name,
                        confidence=Confidence.INDETERMINATE,
                    )
                    all_findings.append(error_finding)
                    if on_finding:
                        on_finding(error_finding)

            # Finalizar
            duration_ms = (time.monotonic() - start_time) * 1000
            if on_progress:
                on_progress("Concluído.", 1.0)

            if on_done:
                from datetime import datetime, timezone
                metadata = ScanMetadata(
                    target_url=url,
                    final_url=record.final_url,
                    mode=mode,
                    timestamp=record.timestamp,
                    duration_ms=duration_ms,
                    total_requests=len(ctx.request_log),
                    cancelled=ctx.is_cancelled(),
                )
                on_done(metadata, all_findings)
