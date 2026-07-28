"""Janela principal do WebGuard."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk  # noqa: E402


ASCII_BANNER = """\
██╗    ██╗███████╗██████╗  ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗
██║    ██║██╔════╝██╔══██╗██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗
██║ █╗ ██║█████╗  ██████╔╝██║  ███╗██║   ██║███████║██████╔╝██║  ██║
██║███╗██║██╔══╝  ██╔══██╗██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
╚███╔███╔╝███████╗██████╔╝╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
 ╚══╝╚══╝ ╚══════╝╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝
            [ Passive & Active Security Scanner ]
                      v1.0.0 :: ready\
"""


class WebGuardWindow(Adw.ApplicationWindow):
    """Janela principal com visual hacker."""

    def __init__(self, **kwargs) -> None:  # type: ignore
        super().__init__(**kwargs)

        self.set_title("web::guard")
        self.set_default_size(1000, 700)

        # Layout principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header bar minimal
        header = Adw.HeaderBar()
        title_label = Gtk.Label(label="web::guard")
        title_label.add_css_class("accent-green")
        header.set_title_widget(title_label)
        main_box.append(header)

        # Content com ViewStack
        stack = Adw.ViewStack()

        # Página de Scan
        scan_page = self._build_scan_page()
        stack.add_titled(scan_page, "scan", "Scanner")

        # Página de Log
        log_page = self._build_log_page()
        stack.add_titled(log_page, "log", "Log")

        # Switcher
        switcher = Adw.ViewSwitcherBar()
        switcher.set_stack(stack)
        switcher.set_reveal(True)

        main_box.append(stack)
        main_box.append(switcher)

        self.set_content(main_box)

    def _build_scan_page(self) -> Gtk.Widget:
        """Constrói a página de scan com visual terminal."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        page.set_margin_top(20)
        page.set_margin_bottom(20)
        page.set_margin_start(24)
        page.set_margin_end(24)

        # ASCII Banner
        banner = Gtk.Label(label=ASCII_BANNER)
        banner.add_css_class("ascii-banner")
        banner.set_halign(Gtk.Align.CENTER)
        page.append(banner)

        # URL Input
        url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        prompt = Gtk.Label(label="➜  TARGET:")
        prompt.add_css_class("accent-green")
        url_box.append(prompt)

        url_entry = Gtk.Entry()
        url_entry.set_placeholder_text("https://meusite.com")
        url_entry.add_css_class("url-entry")
        url_entry.set_hexpand(True)
        url_box.append(url_entry)
        page.append(url_box)

        # Mode selector
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        passive_label = Gtk.Label(label="○ PASSIVE")
        passive_label.add_css_class("mode-passive")
        mode_box.append(passive_label)

        mode_switch = Gtk.Switch()
        mode_box.append(mode_switch)

        active_label = Gtk.Label(label="ACTIVE ○")
        active_label.add_css_class("mode-active")
        mode_box.append(active_label)

        mode_box.set_halign(Gtk.Align.CENTER)
        page.append(mode_box)

        # Scan button
        scan_btn = Gtk.Button(label="▶  INICIAR VARREDURA")
        scan_btn.add_css_class("scan-button")
        scan_btn.set_halign(Gtk.Align.CENTER)
        page.append(scan_btn)

        # Progress area (inicialmente oculto)
        progress_label = Gtk.Label(label="")
        progress_label.add_css_class("progress-text")
        progress_label.set_halign(Gtk.Align.START)
        page.append(progress_label)

        # Results area
        results_scroll = Gtk.ScrolledWindow()
        results_scroll.set_vexpand(True)
        results_list = Gtk.ListBox()
        results_list.set_selection_mode(Gtk.SelectionMode.NONE)
        results_scroll.set_child(results_list)
        page.append(results_scroll)

        return page

    def _build_log_page(self) -> Gtk.Widget:
        """Constrói a página de log estilo htop."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page.set_margin_top(12)
        page.set_margin_bottom(12)
        page.set_margin_start(16)
        page.set_margin_end(16)

        # Header da tabela
        header_label = Gtk.Label(
            label="  TIME      METHOD  URL                                    STATUS  ELAPSED"
        )
        header_label.add_css_class("section-label")
        header_label.set_halign(Gtk.Align.START)
        page.append(header_label)

        separator = Gtk.Separator()
        page.append(separator)

        # Lista de logs
        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_vexpand(True)
        log_list = Gtk.ListBox()
        log_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        log_scroll.set_child(log_list)
        page.append(log_scroll)

        return page
