"""HackerProgressBar — barra de progresso estilo terminal com blocos ■░."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402


class HackerProgressBar(Gtk.Label):
    """Barra de progresso com caracteres ■ (preenchido) e ░ (vazio)."""

    def __init__(self, width: int = 30) -> None:
        super().__init__(label="")
        self._width = width
        self._fraction = 0.0
        self._stage = ""
        self.add_css_class("progress-text")
        self.set_halign(Gtk.Align.START)
        self._update_display()

    def set_fraction(self, fraction: float) -> None:
        """Define progresso (0.0 a 1.0)."""
        self._fraction = max(0.0, min(1.0, fraction))
        self._update_display()

    def set_stage(self, stage: str) -> None:
        """Define texto da etapa atual."""
        self._stage = stage
        self._update_display()

    def _update_display(self) -> None:
        """Reconstrói o texto da barra."""
        filled = int(self._fraction * self._width)
        empty = self._width - filled
        bar = "■" * filled + "░" * empty
        percent = int(self._fraction * 100)
        text = f"[{bar}] {percent:3d}%"
        if self._stage:
            text += f" :: {self._stage}"
        self.set_label(text)
