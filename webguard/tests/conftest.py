"""Fixtures compartilhadas para testes do WebGuard."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from webguard.core.models import Mode, ScanRecord


@pytest.fixture
def make_scan_record():
    """Factory de ScanRecord para testes de analisadores."""

    def _make(
        *,
        headers: dict[str, str] | None = None,
        body: str = "<html><body>test</body></html>",
        status: int = 200,
        url: str = "https://example.com",
        mode: Mode = Mode.PASSIVE,
    ) -> ScanRecord:
        return ScanRecord(
            target_url=url,
            final_url=url,
            redirect_chain=[],
            response_status=status,
            response_headers=headers or {},
            response_body=body,
            cookies=[],
            tls=None,
            timestamp=datetime.now(timezone.utc),
            mode=mode,
            request_log=[],
        )

    return _make
