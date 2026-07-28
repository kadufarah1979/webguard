"""TypingLabel — revelação de texto caractere a caractere."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk  # noqa: E402


class TypingLabel(Gtk.Label):
    """GtkLabel que revela texto um caractere por vez, estilo terminal."""

    def __init__(self, interval_ms: int = 50) -> None:
        super().__init__(label="")
        self._interval_ms = interval_ms
        self._full_text = ""
        self._current_pos = 0
        self._source_id: int | None = None
        self.add_css_class("progress-text")

    def type_text(self, text: str) -> None:
        """Inicia a digitação do texto."""
        self.stop()
        self._full_text = text
        self._current_pos = 0
        self.set_label("")
        self._source_id = GLib.timeout_add(self._interval_ms, self._tick)

    def set_instant(self, text: str) -> None:
        """Define texto instantaneamente (sem animação)."""
        self.stop()
        self._full_text = text
        self._current_pos = len(text)
        self.set_label(text)

    def stop(self) -> None:
        """Para a animação."""
        if self._source_id is not None:
            GLib.source_remove(self._source_id)
            self._source_id = None

    def _tick(self) -> bool:
        """Adiciona um caractere por tick."""
        if self._current_pos >= len(self._full_text):
            self._source_id = None
            return False  # Para o timeout

        self._current_pos += 1
        self.set_label(self._full_text[: self._current_pos])
        return True  # Continua
