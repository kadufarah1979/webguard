"""Registry de analisadores — descoberta por decorador (ADE-2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from webguard.core.models import Finding, ScanRecord

# Tipo de função analisadora
AnalyzerFunc = Callable[[ScanRecord], Coroutine[Any, Any, list[Finding]]]


@dataclass(frozen=True)
class AnalyzerEntry:
    """Entrada no registry."""

    fn: AnalyzerFunc
    mode: str  # "passive" ou "active"
    name: str


_analyzers: list[AnalyzerEntry] = []


def analyzer(*, mode: str, name: str) -> Callable[[AnalyzerFunc], AnalyzerFunc]:
    """Decorador que registra um analisador no registry global."""

    def decorator(fn: AnalyzerFunc) -> AnalyzerFunc:
        _analyzers.append(AnalyzerEntry(fn=fn, mode=mode, name=name))
        return fn

    return decorator


def get_analyzers(mode: str) -> list[AnalyzerEntry]:
    """Retorna analisadores registrados para o modo especificado."""
    return [a for a in _analyzers if a.mode == mode]


def get_all_analyzers() -> list[AnalyzerEntry]:
    """Retorna todos os analisadores registrados."""
    return list(_analyzers)


def clear_registry() -> None:
    """Limpa o registry — apenas para testes."""
    _analyzers.clear()
