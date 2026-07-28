"""Janela principal do WebGuard."""

from __future__ import annotations

from urllib.parse import urlparse

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GLib, Gtk  # noqa: E402

from webguard.core.controller import ScanController  # noqa: E402
from webguard.core.models import Finding, Mode, Severity, ScanMetadata  # noqa: E402


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

SEVERITY_COLORS = {
    Severity.CRITICAL: "severity-critical",
    Severity.HIGH: "severity-high",
    Severity.MEDIUM: "severity-medium",
    Severity.LOW: "severity-low",
    Severity.INFO: "severity-info",
    Severity.INDETERMINATE: "severity-info",
}

SEVERITY_LABELS = {
    Severity.CRITICAL: "CRITICAL",
    Severity.HIGH: "HIGH",
    Severity.MEDIUM: "MEDIUM",
    Severity.LOW: "LOW",
    Severity.INFO: "INFO",
    Severity.INDETERMINATE: "INDETERMINATE",
}


def _is_valid_url(text: str) -> bool:
    """Valida se o texto é uma URL razoável."""
    if not text.strip():
        return False
    url = text.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    return bool(parsed.hostname and "." in parsed.hostname)


class WebGuardWindow(Adw.ApplicationWindow):
    """Janela principal com visual hacker."""

    def __init__(self, **kwargs) -> None:  # type: ignore
        super().__init__(**kwargs)

        self.set_title("web::guard")
        self.set_default_size(1000, 700)

        self._controller = ScanController()
        self._is_scanning = False

        # Layout principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header bar minimal
        header = Adw.HeaderBar()
        title_label = Gtk.Label(label="web::guard")
        title_label.add_css_class("accent-green")
        header.set_title_widget(title_label)
        main_box.append(header)

        # Content com ViewStack
        self._stack = Adw.ViewStack()

        # Página de Scan
        scan_page = self._build_scan_page()
        self._stack.add_titled(scan_page, "scan", "Scanner")

        # Página de Log
        log_page = self._build_log_page()
        self._stack.add_titled(log_page, "log", "Log")

        # Switcher
        switcher = Adw.ViewSwitcherBar()
        switcher.set_stack(self._stack)
        switcher.set_reveal(True)

        main_box.append(self._stack)
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

        self._url_entry = Gtk.Entry()
        self._url_entry.set_placeholder_text("https://meusite.com")
        self._url_entry.add_css_class("url-entry")
        self._url_entry.set_hexpand(True)
        self._url_entry.connect("changed", self._on_url_changed)
        self._url_entry.connect("activate", self._on_url_activate)
        url_box.append(self._url_entry)
        page.append(url_box)

        # Mode selector
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        passive_label = Gtk.Label(label="○ PASSIVE")
        passive_label.add_css_class("mode-passive")
        mode_box.append(passive_label)

        self._mode_switch = Gtk.Switch()
        mode_box.append(self._mode_switch)

        active_label = Gtk.Label(label="ACTIVE ○")
        active_label.add_css_class("mode-active")
        mode_box.append(active_label)

        mode_box.set_halign(Gtk.Align.CENTER)
        page.append(mode_box)

        # Scan button
        self._scan_btn = Gtk.Button(label="▶  INICIAR VARREDURA")
        self._scan_btn.add_css_class("scan-button")
        self._scan_btn.set_halign(Gtk.Align.CENTER)
        self._scan_btn.set_sensitive(False)  # Desabilitado até URL válida
        self._scan_btn.connect("clicked", self._on_scan_clicked)
        page.append(self._scan_btn)

        # Progress area
        self._progress_label = Gtk.Label(label="")
        self._progress_label.add_css_class("progress-text")
        self._progress_label.set_halign(Gtk.Align.START)
        page.append(self._progress_label)

        # Results area
        results_scroll = Gtk.ScrolledWindow()
        results_scroll.set_vexpand(True)
        self._results_list = Gtk.ListBox()
        self._results_list.set_selection_mode(Gtk.SelectionMode.NONE)
        results_scroll.set_child(self._results_list)
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
        self._log_list = Gtk.ListBox()
        self._log_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        log_scroll.set_child(self._log_list)
        page.append(log_scroll)

        return page

    # --- Handlers ---

    def _on_url_changed(self, entry: Gtk.Entry) -> None:
        """Valida URL em tempo real e habilita/desabilita o botão."""
        text = entry.get_text()
        valid = _is_valid_url(text)
        self._scan_btn.set_sensitive(valid and not self._is_scanning)

        if text and not valid:
            entry.add_css_class("error")
        else:
            entry.remove_css_class("error")

    def _on_url_activate(self, entry: Gtk.Entry) -> None:
        """Enter no campo de URL inicia o scan se válido."""
        if _is_valid_url(entry.get_text()) and not self._is_scanning:
            self._start_scan()

    def _on_scan_clicked(self, button: Gtk.Button) -> None:
        """Botão de scan clicado."""
        if self._is_scanning:
            self._cancel_scan()
        else:
            self._start_scan()

    def _start_scan(self) -> None:
        """Inicia a varredura."""
        url = self._url_entry.get_text().strip()
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        mode = Mode.ACTIVE if self._mode_switch.get_active() else Mode.PASSIVE

        # Limpar resultados anteriores
        while True:
            row = self._results_list.get_row_at_index(0)
            if row is None:
                break
            self._results_list.remove(row)

        # Atualizar UI
        self._is_scanning = True
        self._scan_btn.set_label("■  ABORTAR")
        self._scan_btn.remove_css_class("scan-button")
        self._scan_btn.add_css_class("cancel-button")
        self._url_entry.set_sensitive(False)
        self._mode_switch.set_sensitive(False)
        self._progress_label.set_label("[░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0% :: Iniciando...")

        # Importar analyzers para registrar no registry
        import webguard.analyzers.passive.headers  # noqa: F401
        import webguard.analyzers.passive.fingerprint  # noqa: F401

        # Iniciar scan
        self._controller.start_scan(
            url,
            mode,
            on_finding=self._on_finding_from_thread,
            on_progress=self._on_progress_from_thread,
            on_done=self._on_done_from_thread,
            on_error=self._on_error_from_thread,
        )

    def _cancel_scan(self) -> None:
        """Cancela a varredura."""
        self._controller.cancel()
        self._progress_label.set_label("[CANCELADO]")
        self._reset_ui()

    def _reset_ui(self) -> None:
        """Restaura UI ao estado pré-scan."""
        self._is_scanning = False
        self._scan_btn.set_label("▶  INICIAR VARREDURA")
        self._scan_btn.remove_css_class("cancel-button")
        self._scan_btn.add_css_class("scan-button")
        self._url_entry.set_sensitive(True)
        self._mode_switch.set_sensitive(True)
        self._on_url_changed(self._url_entry)  # Re-avaliar estado do botão

    # --- Callbacks do controller (chamados da thread worker via GLib.idle_add) ---

    def _on_finding_from_thread(self, finding: Finding) -> None:
        """Recebe achado da thread — agenda na main loop."""
        GLib.idle_add(self._add_finding_to_ui, finding)

    def _on_progress_from_thread(self, stage: str, percent: float) -> None:
        """Recebe progresso da thread."""
        GLib.idle_add(self._update_progress, stage, percent)

    def _on_done_from_thread(self, metadata: ScanMetadata, findings: list[Finding]) -> None:
        """Scan concluído."""
        GLib.idle_add(self._on_scan_done, metadata, findings)

    def _on_error_from_thread(self, error: str) -> None:
        """Erro durante scan."""
        GLib.idle_add(self._on_scan_error, error)

    # --- UI updates (main thread) ---

    def _update_progress(self, stage: str, percent: float) -> None:
        """Atualiza barra de progresso."""
        width = 30
        filled = int(percent * width)
        empty = width - filled
        bar = "■" * filled + "░" * empty
        pct = int(percent * 100)
        self._progress_label.set_label(f"[{bar}] {pct:3d}% :: {stage}")
        return False  # Remove do idle

    def _add_finding_to_ui(self, finding: Finding) -> None:
        """Adiciona um achado à lista de resultados."""
        row = Gtk.ListBoxRow()
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.set_margin_top(8)
        card.set_margin_bottom(8)
        card.set_margin_start(12)
        card.set_margin_end(12)
        card.add_css_class("finding-card")
        card.add_css_class(finding.severity.value)

        # Header: [SEVERITY] ID :: Title
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        badge = Gtk.Label(label=f"[{SEVERITY_LABELS.get(finding.severity, 'INFO')}]")
        badge.add_css_class("severity-badge")
        badge.add_css_class(SEVERITY_COLORS.get(finding.severity, "severity-info"))
        header_box.append(badge)

        title = Gtk.Label(label=f"{finding.id} :: {finding.title}")
        title.add_css_class("accent-green")
        title.set_halign(Gtk.Align.START)
        title.set_hexpand(True)
        title.set_wrap(True)
        header_box.append(title)
        card.append(header_box)

        # Evidence
        ev_label = Gtk.Label(label="EVIDENCE:")
        ev_label.add_css_class("section-label")
        ev_label.set_halign(Gtk.Align.START)
        card.append(ev_label)

        evidence = Gtk.Label(label=finding.evidence)
        evidence.add_css_class("evidence-block")
        evidence.set_halign(Gtk.Align.START)
        evidence.set_wrap(True)
        evidence.set_selectable(True)
        card.append(evidence)

        # Remediation
        fix_label = Gtk.Label(label="FIX:")
        fix_label.add_css_class("section-label")
        fix_label.set_halign(Gtk.Align.START)
        card.append(fix_label)

        fix = Gtk.Label(label=finding.remediation)
        fix.add_css_class("evidence-block")
        fix.set_halign(Gtk.Align.START)
        fix.set_wrap(True)
        fix.set_selectable(True)
        card.append(fix)

        row.set_child(card)
        self._results_list.append(row)
        return False

    def _on_scan_done(self, metadata: ScanMetadata, findings: list[Finding]) -> None:
        """Scan finalizado com sucesso."""
        total = len(findings)
        duration = metadata.duration_ms / 1000
        status = "CANCELADO" if metadata.cancelled else "CONCLUÍDO"
        self._progress_label.set_label(
            f"[{'■' * 30}] 100% :: {status} — {total} achados em {duration:.1f}s"
        )
        self._reset_ui()
        return False

    def _on_scan_error(self, error: str) -> None:
        """Erro durante scan."""
        self._progress_label.set_label(f"[ERRO] {error}")
        self._reset_ui()
        return False
