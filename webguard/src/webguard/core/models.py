"""Modelos de dados compartilhados do WebGuard."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal


class Mode(Enum):
    """Modo de operação do scanner."""

    PASSIVE = "passive"
    ACTIVE = "active"


class Severity(str, Enum):
    """Escala de severidade unificada (RN-1)."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    INDETERMINATE = "indeterminate"


class Confidence(str, Enum):
    """Nível de confiança do achado."""

    CONFIRMED = "confirmed"
    LIKELY = "likely"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class CertInfo:
    """Informações de um certificado na cadeia TLS."""

    subject: dict[str, str]
    issuer: dict[str, str]
    not_before: datetime
    not_after: datetime
    san: list[str]
    serial: str
    signature_algorithm: str


@dataclass(frozen=True)
class TLSInfo:
    """Dados extraídos do handshake TLS."""

    protocol_version: str
    cipher_suite: str
    certificate_chain: list[CertInfo]
    supported_protocols: list[str]


@dataclass(frozen=True)
class CookieInfo:
    """Metadados de um cookie recebido."""

    name: str
    value_snippet: str  # primeiros 20 chars
    domain: str
    path: str
    secure: bool
    httponly: bool
    samesite: str | None
    expires: datetime | None


@dataclass(frozen=True)
class RequestLog:
    """Registro de uma requisição emitida (para o log de atividade)."""

    timestamp: datetime
    method: str
    url: str
    headers_sent: dict[str, str]
    payload: str | None  # None para passivo
    status_code: int | None
    response_headers: dict[str, str]
    response_body_snippet: str  # primeiros 4KB
    elapsed_ms: float
    mode: Literal["passive", "active"]
    blocked: bool = False
    block_reason: str | None = None


@dataclass(frozen=True)
class Finding:
    """Achado de segurança — formato único (L-6)."""

    id: str
    category: str
    severity: Severity
    title: str
    evidence: str
    explanation: str
    remediation: str
    reference: str
    analyzer: str
    confidence: Confidence
    payload_sent: str | None = None


@dataclass(frozen=True)
class CollectError:
    """Erro de coleta — sem exceção lançada (L-9)."""

    reason: str  # "dns_resolution_failed", "connection_refused", "timeout", etc.
    detail: str
    url: str


@dataclass(frozen=True)
class ScanRecord:
    """Registro completo de uma coleta — entrada para os analisadores."""

    target_url: str
    final_url: str
    redirect_chain: list[str]
    response_status: int
    response_headers: dict[str, str]
    response_body: str  # até 2MB
    cookies: list[CookieInfo]
    tls: TLSInfo | None
    timestamp: datetime
    mode: Mode
    request_log: list[RequestLog]


@dataclass
class ScanContext:
    """Contexto compartilhado entre controller e workers — cancelamento + estado."""

    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    findings: list[Finding] = field(default_factory=list)
    request_log: list[RequestLog] = field(default_factory=list)
    consent_timestamp: datetime | None = None
    consent_url: str | None = None

    def is_cancelled(self) -> bool:
        """Verifica se o scan foi cancelado."""
        return self.cancel_event.is_set()

    def cancel(self) -> None:
        """Sinaliza cancelamento."""
        self.cancel_event.set()

    def add_finding(self, finding: Finding) -> None:
        """Adiciona achado ao estado."""
        self.findings.append(finding)

    def add_request_log(self, log: RequestLog) -> None:
        """Adiciona entrada ao log de requisições."""
        self.request_log.append(log)


@dataclass
class RateLimiter:
    """Token bucket com configuração por modo (L-3)."""

    mode: Mode
    requests_per_second: float = 10.0
    min_interval_ms: float = 200.0
    concurrency: int = 5

    def __post_init__(self) -> None:
        if self.mode == Mode.PASSIVE:
            self._interval = self.min_interval_ms / 1000.0
            self._semaphore = asyncio.Semaphore(1)
        else:
            self._interval = 1.0 / self.requests_per_second
            self._semaphore = asyncio.Semaphore(self.concurrency)

    async def acquire(self) -> None:
        """Aguarda até que a requisição possa ser emitida."""
        await self._semaphore.acquire()
        await asyncio.sleep(self._interval)

    def release(self) -> None:
        """Libera o slot após a requisição."""
        self._semaphore.release()


@dataclass(frozen=True)
class ActiveConfig:
    """Configuração do motor ativo."""

    concurrency: int = 5
    rate_limit_rps: float = 10.0
    timeout_normal: float = 10.0
    timeout_time_based: float = 15.0
    confirmation_rounds: int = 2
    time_threshold_ms: int = 5000


@dataclass(frozen=True)
class ScanMetadata:
    """Metadados de uma execução — para exportação."""

    target_url: str
    final_url: str
    mode: Mode
    timestamp: datetime
    duration_ms: float
    total_requests: int
    cancelled: bool


class WebGuardError(Exception):
    """Exceção base do projeto."""


class CollectorError(WebGuardError):
    """Erro na camada de coleta."""


class GuardViolation(WebGuardError):
    """Tentativa de requisição fora do escopo do modo (L-1 violation)."""
