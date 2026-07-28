"""WebGuard — Application entry point."""

from __future__ import annotations

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, Gtk  # noqa: E402

from webguard.ui.window import WebGuardWindow  # noqa: E402


class WebGuardApp(Adw.Application):
    """Aplicação principal GTK4 + libadwaita."""

    def __init__(self) -> None:
        super().__init__(
            application_id="dev.webguard.app",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_activate(self) -> None:
        # Forçar dark mode
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        # Carregar CSS customizado
        self._load_css()

        # Criar janela
        win = WebGuardWindow(application=self)
        win.present()

    def _load_css(self) -> None:
        """Carrega o tema hacker via CssProvider."""
        import importlib.resources as resources

        css_provider = Gtk.CssProvider()

        # Tentar carregar do pacote, fallback para path relativo
        try:
            css_path = resources.files("webguard.ui").joinpath("style.css")
            css_provider.load_from_data(css_path.read_text().encode())
        except Exception:
            import pathlib

            css_file = pathlib.Path(__file__).parent / "ui" / "style.css"
            if css_file.exists():
                css_provider.load_from_path(str(css_file))

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )


def main() -> None:
    """Entry point."""
    app = WebGuardApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
