"""Okno edytora tekstu — karty, menu, skróty klawiszowe."""

from __future__ import annotations

import re
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Optional

from lore.dictionary_view import open_name_dictionary, open_spellcheck
from lore.document_hooks import on_file_opened, on_file_saved
from lore.i18n import get_locale, list_locales, set_locale, t
from lore.panel import LorePanel
from lore.paths import (
    default_work_dir,
    load_last_file,
    save_last_file,
    save_last_work_dir,
)
from lore.store import LoreStore
from lore.text_io import read_text_smart, write_text_atomic
from lore.theme import apply_theme, style_text
from lore.export_docx import DocxExportError, export_available, export_manuscript_docx
from lore.help_view import open_help
from lore.history_view import open_history_window
from lore.manuscript import paginate, profile_for_preset
from lore.print_preview import open_print_preview
from lore.typography import (
    apply_typography,
    load_typography_settings,
    list_presets_by_category,
    refresh_body_tag,
    save_typography_settings,
    settings_summary,
    TypographySettings,
)

_AUTOSAVE_MS = 60_000


def _word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


@dataclass
class _TabState:
    text: scrolledtext.ScrolledText = field(repr=False)
    frame: ttk.Frame = field(repr=False)
    path: str = ""
    encoding: str = "utf-8"
    dirty: bool = False


class EditorWindow:
    """Standalone edytor rozdziałów z panelem lore."""

    def __init__(
        self,
        lore: LoreStore,
        *,
        initial_files: Optional[list[str]] = None,
    ) -> None:
        self._lore = lore
        self._proj = lore.nazwa_projektu()
        self._proj_root = lore.katalog_projektu()
        self._tabs: dict[str, _TabState] = {}
        self._find_dialog: Optional[tk.Toplevel] = None
        self._typography = load_typography_settings()

        self.root = tk.Tk()
        preset, size, spacing = self._typography.resolved()
        self._font_family_var = tk.StringVar(master=self.root, value=self._typography.preset_id)
        self._font_size_var = tk.IntVar(master=self.root, value=size)
        self._line_spacing_var = tk.DoubleVar(master=self.root, value=spacing)
        self.root.title(f"{t('app.name')} — {self._proj}")
        self.root.geometry("1150x720")
        self.root.minsize(900, 560)
        apply_theme(self.root)

        self._status_var = tk.StringVar(value=t("app.ready"))
        self._proj_label_var = tk.StringVar(value=f"  ·  {self._proj}")
        self._path_status_var = tk.StringVar(value=str(self._proj_root))
        self._locale_var = tk.StringVar(master=self.root, value=get_locale())
        self._build_ui()
        self._build_menu()
        self._bind_shortcuts()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._schedule_autosave()

        files = [f for f in (initial_files or []) if f and Path(f).is_file()]
        if not files:
            # Przywróć ostatni plik z sesji (w katalogu projektu lub absolutny)
            restored = self._resolve_session_file()
            if restored is not None:
                files = [str(restored)]
        if files:
            for path in files:
                self._open_path(path)
        else:
            self._new_tab()
        # Zapamiętaj katalog od razu przy starcie
        save_last_work_dir(self._proj_root)

    def run(self) -> None:
        self.root.mainloop()

    def _resolve_session_file(self) -> Optional[Path]:
        """Ostatni plik z sesji, jeśli nadal istnieje (preferuj w katalogu projektu)."""
        last = load_last_file()
        if last is None:
            return None
        try:
            last.relative_to(self._proj_root.resolve())
            return last
        except ValueError:
            # plik spoza bieżącego projektu — otwórz tylko jeśli istnieje
            return last if last.is_file() else None

    def _remember_file(self, path: str | Path) -> None:
        save_last_file(path, project_dir=self._proj_root)

    def _current_tab(self) -> Optional[_TabState]:
        try:
            tab_id = self._notebook.select()
            if not tab_id:
                return None
            return self._tabs.get(tab_id)
        except tk.TclError:
            return None

    def _current_file(self) -> str:
        tab = self._current_tab()
        return tab.path if tab else ""

    def _tab_display_name(self, tab: _TabState) -> str:
        if tab.path:
            try:
                name = Path(tab.path).resolve().relative_to(self._proj_root)
                label = str(name)
            except ValueError:
                label = Path(tab.path).name
        else:
            label = t("app.untitled")
        return f"{label}*" if tab.dirty else label

    def _tab_label(self, tab: _TabState) -> str:
        return f"{self._tab_display_name(tab)}  ×"

    def _update_tab_title(self, tab_id: str) -> None:
        tab = self._tabs.get(tab_id)
        if tab is None:
            return
        self._notebook.tab(tab_id, text=self._tab_label(tab))

    def _update_window_title(self) -> None:
        tab = self._current_tab()
        base = f"{t('app.name')} — {self._proj}"
        if tab and tab.path:
            name = Path(tab.path).name
            base += f" — {name}"
            if tab.dirty:
                base += " *"
        elif tab and tab.dirty:
            base += " — *"
        self.root.title(base)

    def _update_status(self) -> None:
        tab = self._current_tab()
        if tab is None:
            self._status_var.set(t("app.ready"))
            return
        content = self._tab_content(tab)
        words = _word_count(content)
        enc = tab.encoding
        dirty = f" · {t('app.unsaved')}" if tab.dirty else ""
        words_lbl = t("app.words")
        if tab.path:
            try:
                rel = Path(tab.path).resolve().relative_to(self._proj_root)
                path_lbl = str(rel)
            except ValueError:
                path_lbl = Path(tab.path).name
            ms = paginate(content, profile_for_preset(self._typography.preset_id))
            self._status_var.set(
                f"{path_lbl} · {words} {words_lbl} · {ms.summary()} · {enc}{dirty}"
            )
        else:
            ms = paginate(content, profile_for_preset(self._typography.preset_id))
            self._status_var.set(
                f"{t('app.untitled')} · {words} {words_lbl} · {ms.summary()}{dirty}"
            )

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=(8, 6))
        top.pack(fill="x")
        self._title_lbl = ttk.Label(top, text=t("app.name"), style="Head.TLabel")
        self._title_lbl.pack(side="left")
        ttk.Label(top, textvariable=self._proj_label_var, style="Dim.TLabel").pack(side="left")

        toolbar = ttk.Frame(top)
        toolbar.pack(side="right")
        self._tb_new = ttk.Button(toolbar, text=t("file.new"), command=self._new_tab)
        self._tb_new.pack(side="left", padx=2)
        self._tb_open = ttk.Button(toolbar, text=t("file.open"), command=self._open_dialog)
        self._tb_open.pack(side="left", padx=2)
        self._tb_save = ttk.Button(toolbar, text=t("file.save"), command=self._save)
        self._tb_save.pack(side="left", padx=2)
        self._tb_save_as = ttk.Button(toolbar, text=t("file.save_as"), command=self._save_as)
        self._tb_save_as.pack(side="left", padx=2)
        self._tb_catalog = ttk.Button(toolbar, text=t("toolbar.catalog"), command=self._choose_project_dir)
        self._tb_catalog.pack(side="left", padx=2)
        self._tb_close = ttk.Button(toolbar, text=t("file.close_tab"), command=self._close_current_tab)
        self._tb_close.pack(side="left", padx=2)

        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        left = ttk.Frame(paned)
        paned.add(left, weight=3)

        self._notebook = ttk.Notebook(left)
        self._notebook.pack(fill="both", expand=True)
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._notebook.bind("<Button-1>", self._on_tab_click, add="+")
        self._notebook.bind("<Button-2>", self._on_tab_middle_click, add="+")

        self._panel = LorePanel(paned, self._lore, get_current_file=self._current_file)
        paned.add(self._panel, weight=1)

        status = ttk.Frame(self.root, padding=(8, 4))
        status.pack(fill="x", side="bottom")
        ttk.Label(status, textvariable=self._status_var, style="Dim.TLabel").pack(side="left")
        path_lbl = ttk.Label(status, textvariable=self._path_status_var, style="Dim.TLabel", cursor="hand2")
        path_lbl.pack(side="right")
        path_lbl.bind("<Button-1>", lambda _e: self._choose_project_dir())

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)

        file_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu.file"), menu=file_m)
        file_m.add_command(label=t("file.new"), accelerator="Ctrl+N", command=self._new_tab)
        file_m.add_command(label=t("file.open"), accelerator="Ctrl+O", command=self._open_dialog)
        file_m.add_separator()
        file_m.add_command(label=t("file.save"), accelerator="Ctrl+S", command=self._save)
        file_m.add_command(label=t("file.save_as"), accelerator="Ctrl+Shift+S", command=self._save_as)
        file_m.add_separator()
        file_m.add_command(
            label=t("file.project_dir"),
            accelerator="Ctrl+Shift+O",
            command=self._choose_project_dir,
        )
        file_m.add_command(
            label=t("file.default_dir"),
            command=self._use_default_project_dir,
        )
        file_m.add_separator()
        file_m.add_command(label=t("file.close_tab"), accelerator="Ctrl+W", command=self._close_current_tab)
        file_m.add_command(label=t("file.save_lore"), command=self._save_lore)
        file_m.add_separator()
        file_m.add_command(label=t("file.quit"), command=self._on_close)

        edit_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu.edit"), menu=edit_m)
        edit_m.add_command(label=t("edit.undo"), accelerator="Ctrl+Z", command=self._undo)
        edit_m.add_command(label=t("edit.redo"), accelerator="Ctrl+Y", command=self._redo)
        edit_m.add_separator()
        edit_m.add_command(label=t("edit.find"), accelerator="Ctrl+F", command=self._show_find)
        edit_m.add_command(
            label=t("edit.name_dict"),
            accelerator="Ctrl+Shift+D",
            command=self._show_name_dictionary,
        )
        edit_m.add_command(
            label=t("edit.spellcheck"),
            accelerator="F7",
            command=self._show_spellcheck,
        )
        edit_m.add_separator()
        edit_m.add_command(label=t("edit.wrap"), command=self._toggle_wrap)

        lore_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu.lore"), menu=lore_m)
        lore_m.add_command(label=t("lore.refresh"), command=self._panel.odswiez)
        lore_m.add_command(label=t("file.save_lore"), command=self._save_lore)
        lore_m.add_separator()
        lore_m.add_command(label=t("lore.snapshot"), command=self._create_snapshot)
        lore_m.add_command(label=t("lore.history"), command=self._show_history)
        lore_m.add_separator()
        lore_m.add_command(
            label=t("media.attach_image"),
            command=lambda: self._panel.attach_media("image"),
        )
        lore_m.add_command(
            label=t("media.attach_audio"),
            command=lambda: self._panel.attach_media("audio"),
        )
        lore_m.add_command(
            label=t("media.attach_video"),
            command=lambda: self._panel.attach_media("video"),
        )

        # Osobne menu Media — łatwe do znalezienia (zdjęcia / muzyka / film)
        media_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu.media"), menu=media_m)
        media_m.add_command(
            label=t("media.attach_image"),
            accelerator="Ctrl+Shift+I",
            command=lambda: self._panel.attach_media("image"),
        )
        media_m.add_command(
            label=t("media.attach_audio"),
            accelerator="Ctrl+Shift+U",
            command=lambda: self._panel.attach_media("audio"),
        )
        media_m.add_command(
            label=t("media.attach_video"),
            accelerator="Ctrl+Shift+M",
            command=lambda: self._panel.attach_media("video"),
        )
        media_m.add_command(
            label=t("media.attach_any"),
            command=lambda: self._panel.attach_media("any"),
        )
        media_m.add_separator()
        media_m.add_command(
            label=t("media.preview"),
            command=self._panel.preview_media,
        )
        media_m.add_command(
            label=t("media.list"),
            command=self._panel.list_media,
        )
        media_m.add_command(
            label=t("media.export"),
            command=self._panel.export_media,
        )

        view_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu.view"), menu=view_m)
        for _cat_id, cat_label, items in list_presets_by_category():
            sub = tk.Menu(view_m, tearoff=0)
            view_m.add_cascade(label=cat_label, menu=sub)
            for preset in items:
                sub.add_radiobutton(
                    label=preset.menu_label(),
                    variable=self._font_family_var,
                    value=preset.id,
                    command=self._on_typography_preset,
                )
        view_m.add_separator()
        size_m = tk.Menu(view_m, tearoff=0)
        view_m.add_cascade(label=t("view.font_size"), menu=size_m)
        for pt in (11, 12):
            size_m.add_radiobutton(
                label=f"{pt} pt",
                variable=self._font_size_var,
                value=pt,
                command=self._on_typography_size,
            )
        spacing_m = tk.Menu(view_m, tearoff=0)
        view_m.add_cascade(label=t("view.line_spacing"), menu=spacing_m)
        for sp, label in ((1.0, "1,0 — druk / gotowy tekst"), (1.5, "1,5 — szkic roboczy")):
            spacing_m.add_radiobutton(
                label=label,
                variable=self._line_spacing_var,
                value=sp,
                command=self._on_typography_spacing,
            )

        print_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu.print"), menu=print_m)
        prev_m = tk.Menu(print_m, tearoff=0)
        print_m.add_cascade(label=t("print.preview"), menu=prev_m)
        prev_m.add_command(
            label="Scenariusz (Courier, 1 str. ≈ 1 min)",
            command=lambda: self._show_print_preview("screenplay"),
        )
        prev_m.add_command(
            label="Rękopis do wysyłki (TNR, interlinia 2,0)",
            command=lambda: self._show_print_preview("submission"),
        )
        prev_m.add_command(
            label="Gotowy do druku (TNR, interlinia 1,0)",
            command=lambda: self._show_print_preview("print_ready"),
        )
        print_m.add_separator()
        exp_m = tk.Menu(print_m, tearoff=0)
        print_m.add_cascade(label=t("print.export_docx"), menu=exp_m)
        exp_m.add_command(
            label="Rękopis do wydawnictwa (TNR 12, margines 2,5 cm)",
            command=lambda: self._export_docx("submission"),
        )
        exp_m.add_command(
            label="Scenariusz (Courier 12)",
            command=lambda: self._export_docx("screenplay"),
        )
        exp_m.add_command(
            label="Gotowy do druku (TNR 12, interlinia 1,0)",
            command=lambda: self._export_docx("print_ready"),
        )

        lang_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("app.language"), menu=lang_m)
        for pack in list_locales():
            lang_m.add_radiobutton(
                label=f"{pack.display_name()} ({pack.code})",
                variable=self._locale_var,
                value=pack.code,
                command=lambda c=pack.code: self._change_locale(c),
            )

        help_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu.help"), menu=help_m)
        help_m.add_command(
            label=t("help.writer_guide"),
            accelerator="F1",
            command=lambda: open_help(self.root, t("help.writer_guide")),
        )
        help_m.add_command(
            label=t("help.shortcuts"),
            command=lambda: open_help(self.root, t("help.shortcuts")),
        )
        help_m.add_command(
            label=t("help.fonts"),
            command=lambda: open_help(self.root, t("help.fonts")),
        )
        help_m.add_command(
            label=t("help.print"),
            command=lambda: open_help(self.root, t("help.print")),
        )
        help_m.add_command(
            label=t("help.panel"),
            command=lambda: open_help(self.root, t("help.panel")),
        )
        help_m.add_command(
            label=t("help.media"),
            command=lambda: open_help(self.root, t("help.media")),
        )
        help_m.add_command(
            label=t("help.spell"),
            command=lambda: open_help(self.root, t("help.spell")),
        )
        help_m.add_command(
            label=t("help.temporal"),
            command=lambda: open_help(self.root, t("help.temporal")),
        )
        help_m.add_command(
            label=t("help.query"),
            command=lambda: open_help(self.root, t("help.query")),
        )
        help_m.add_command(
            label=t("help.history"),
            command=lambda: open_help(self.root, t("help.history")),
        )
        help_m.add_command(
            label=t("help.network"),
            command=lambda: open_help(self.root, t("help.network")),
        )
        help_m.add_separator()
        help_m.add_command(
            label=t("help.about"),
            command=lambda: open_help(self.root, t("help.about")),
        )

    def _bind_shortcuts(self) -> None:
        self.root.bind_all("<Control-n>", lambda e: self._new_tab())
        self.root.bind_all("<Control-o>", lambda e: self._open_dialog())
        self.root.bind_all("<Control-s>", lambda e: self._save())
        self.root.bind_all("<Control-Shift-S>", lambda e: self._save_as())
        self.root.bind_all("<Control-w>", lambda e: self._close_current_tab())
        self.root.bind_all("<Control-f>", lambda e: self._show_find())
        self.root.bind_all("<Control-Shift-D>", lambda e: self._show_name_dictionary())
        self.root.bind_all("<Control-Shift-O>", lambda e: self._choose_project_dir())
        self.root.bind_all(
            "<Control-Shift-I>", lambda e: self._panel.attach_media("image")
        )
        self.root.bind_all(
            "<Control-Shift-U>", lambda e: self._panel.attach_media("audio")
        )
        self.root.bind_all(
            "<Control-Shift-M>", lambda e: self._panel.attach_media("video")
        )
        self.root.bind_all("<F7>", lambda e: self._show_spellcheck())
        self.root.bind_all(
            "<F1>", lambda e: open_help(self.root, t("help.writer_guide"))
        )

    def _create_tab(self, content: str = "", path: str = "", encoding: str = "utf-8") -> str:
        frame = ttk.Frame(self._notebook)
        text = scrolledtext.ScrolledText(frame, wrap="word", undo=True)
        style_text(text, height=24, mono=False)
        self._apply_typography_to_widget(text)
        text.pack(fill="both", expand=True)
        if content:
            text.insert("1.0", content)

        self._notebook.add(frame, text="Bez tytułu")
        tab_id = str(frame)
        state = _TabState(text=text, frame=frame, path=path, encoding=encoding)
        self._tabs[tab_id] = state

        def _on_modify(_event=None):
            if not text.edit_modified():
                return
            text.edit_modified(False)
            if not state.dirty:
                state.dirty = True
                self._update_tab_title(tab_id)
                self._update_window_title()
            refresh_body_tag(text)
            self._update_status()

        text.bind("<<Modified>>", _on_modify)
        self._notebook.select(tab_id)
        self._update_tab_title(tab_id)
        self._update_window_title()
        self._update_status()
        return tab_id

    def _new_tab(self) -> None:
        self._create_tab()

    def _on_tab_changed(self, _event=None) -> None:
        tab = self._current_tab()
        self._update_window_title()
        self._update_status()
        if tab and tab.path:
            on_file_opened(self._lore, tab.path, self._panel)
            self._remember_file(tab.path)

    def _open_dialog(self) -> None:
        paths = filedialog.askopenfilenames(
            parent=self.root,
            initialdir=str(self._proj_root),
            filetypes=[("Tekst", "*.txt *.md"), ("Markdown", "*.md"), ("Wszystkie", "*.*")],
        )
        for path in paths:
            if path:
                self._open_path(path)

    def _open_path(self, path: str) -> None:
        for tab_id, state in self._tabs.items():
            if state.path and Path(state.path).resolve() == Path(path).resolve():
                self._notebook.select(tab_id)
                return

        try:
            content, enc = read_text_smart(path)
        except (OSError, ValueError) as e:
            messagebox.showerror("Błąd otwarcia", str(e), parent=self.root)
            return

        tab_id = self._create_tab(content, path=path, encoding=enc)
        on_file_opened(self._lore, path, self._panel)
        self._update_tab_title(tab_id)
        self._remember_file(path)

    def _save_tab(self, tab: _TabState, *, save_as: bool = False) -> bool:
        path = tab.path
        if not path or save_as:
            path = filedialog.asksaveasfilename(
                parent=self.root,
                initialdir=str(self._proj_root),
                initialfile=Path(path).name if path else "rozdzial.txt",
                defaultextension=".txt",
                filetypes=[("Tekst", "*.txt *.md"), ("Markdown", "*.md")],
            )
            if not path:
                return False
            tab.path = path

        content = self._tab_content(tab)
        try:
            on_file_saved(
                self._lore,
                tab.path,
                self._panel,
                content=content,
                encoding=tab.encoding,
            )
        except (OSError, UnicodeEncodeError) as e:
            messagebox.showerror("Błąd zapisu", str(e), parent=self.root)
            return False
        except Exception as e:
            # Tekst mógł już trafić na dysk — nie twierdź, że cały zapis OK.
            messagebox.showerror(
                "Zapis",
                f"Tekst zapisany, ale lore nie: {e}\nSpróbuj „Zapisz projekt lore”.",
                parent=self.root,
            )
            tab.dirty = False  # treść pliku jest na dysku
            tab_id = self._tab_id_for(tab)
            if tab_id:
                self._update_tab_title(tab_id)
            self._update_window_title()
            self._update_status()
            if tab.path:
                self._remember_file(tab.path)
            return False

        tab.dirty = False
        tab_id = self._tab_id_for(tab)
        if tab_id:
            self._update_tab_title(tab_id)
        self._update_window_title()
        self._update_status()
        if tab.path:
            self._remember_file(tab.path)
        return True

    def _tab_id_for(self, tab: _TabState) -> Optional[str]:
        for tab_id, state in self._tabs.items():
            if state is tab:
                return tab_id
        return None

    def _save(self) -> None:
        tab = self._current_tab()
        if tab is None:
            return
        self._save_tab(tab)

    def _save_as(self) -> None:
        tab = self._current_tab()
        if tab is None:
            return
        self._save_tab(tab, save_as=True)

    def _undo(self) -> None:
        tab = self._current_tab()
        if tab:
            try:
                tab.text.edit_undo()
            except tk.TclError:
                pass

    def _redo(self) -> None:
        tab = self._current_tab()
        if tab:
            try:
                tab.text.edit_redo()
            except tk.TclError:
                pass

    def _sync_typography_from_vars(self) -> TypographySettings:
        self._typography = TypographySettings(
            preset_id=self._font_family_var.get(),
            size=int(self._font_size_var.get()),
            line_spacing=float(self._line_spacing_var.get()),
        )
        return self._typography

    def _apply_typography_to_widget(self, text: scrolledtext.ScrolledText) -> str:
        return apply_typography(text, self._typography)

    def _apply_typography_all(self) -> str:
        family = ""
        for state in self._tabs.values():
            family = self._apply_typography_to_widget(state.text)
        return family

    def _persist_typography(self, family: str = "") -> None:
        save_typography_settings(self._typography)
        if not family:
            tab = self._current_tab()
            if tab:
                family = tab.text.cget("font").split()[0] if tab.text.cget("font") else ""
        self._status_var.set("Wygląd: " + settings_summary(self._typography, family=family))

    def _on_typography_preset(self) -> None:
        from lore.typography import get_preset

        preset = get_preset(self._font_family_var.get())
        if preset:
            self._font_size_var.set(preset.size)
            self._line_spacing_var.set(preset.line_spacing)
        self._sync_typography_from_vars()
        family = self._apply_typography_all()
        self._persist_typography(family)

    def _on_typography_size(self) -> None:
        self._sync_typography_from_vars()
        family = self._apply_typography_all()
        self._persist_typography(family)

    def _on_typography_spacing(self) -> None:
        self._sync_typography_from_vars()
        family = self._apply_typography_all()
        self._persist_typography(family)

    def _tab_content(self, tab: _TabState) -> str:
        # end-1c: Tk zawsze trzyma dodatkowy \\n; tk.END dopisywałby go przy każdym zapisie
        return tab.text.get("1.0", "end-1c")

    def _current_text_content(self) -> str:
        tab = self._current_tab()
        return self._tab_content(tab) if tab else ""

    def _show_print_preview(self, profile_id: str) -> None:
        tab = self._current_tab()
        if tab is None:
            messagebox.showinfo("Wydruk", "Otwórz kartę z tekstem.", parent=self.root)
            return
        title = "Podgląd — scenariusz" if profile_id == "screenplay" else "Podgląd druku"
        open_print_preview(self.root, self._current_text_content(), profile_id=profile_id, title=title)

    def _export_docx(self, profile_id: str) -> None:
        tab = self._current_tab()
        if tab is None:
            messagebox.showinfo("Eksport", "Otwórz kartę z tekstem.", parent=self.root)
            return
        if not export_available():
            messagebox.showerror(
                "Eksport DOCX",
                "Zainstaluj pakiet: pip install python-docx",
                parent=self.root,
            )
            return
        default = Path(tab.path).stem if tab.path else "rozdzial"
        path = filedialog.asksaveasfilename(
            parent=self.root,
            initialdir=str(self._proj_root),
            initialfile=f"{default}_rekopis.docx",
            defaultextension=".docx",
            filetypes=[("Word", "*.docx")],
        )
        if not path:
            return
        try:
            export_manuscript_docx(
                self._current_text_content(),
                path,
                profile_id=profile_id,
                title=Path(tab.path).stem if tab.path else "",
            )
            messagebox.showinfo("Eksport DOCX", f"Zapisano:\n{path}", parent=self.root)
        except (DocxExportError, OSError) as e:
            messagebox.showerror("Eksport DOCX", str(e), parent=self.root)

    def _toggle_wrap(self) -> None:
        tab = self._current_tab()
        if tab is None:
            return
        current = tab.text.cget("wrap")
        tab.text.configure(wrap="none" if current == "word" else "word")
        self._status_var.set("Zawijanie wierszy: " + ("włączone" if tab.text.cget("wrap") == "word" else "wyłączone"))

    def _show_find(self) -> None:
        tab = self._current_tab()
        if tab is None:
            return

        if self._find_dialog is not None and self._find_dialog.winfo_exists():
            self._find_dialog.lift()
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("Znajdź")
        dlg.transient(self.root)
        dlg.resizable(False, False)
        self._find_dialog = dlg

        ttk.Label(dlg, text="Szukaj:", padding=8).grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(dlg, width=36)
        entry.grid(row=0, column=1, padx=8, pady=8)
        try:
            entry.insert(0, tab.text.get("sel.first", "sel.last"))
        except tk.TclError:
            pass
        entry.focus_set()

        def _find_next():
            query = entry.get()
            if not query:
                return
            start = tab.text.index("insert")
            pos = tab.text.search(query, start, stopindex=tk.END)
            if not pos:
                pos = tab.text.search(query, "1.0", stopindex=tk.END)
            if pos:
                end = f"{pos}+{len(query)}c"
                tab.text.tag_remove("find_hit", "1.0", tk.END)
                tab.text.tag_add("find_hit", pos, end)
                tab.text.tag_configure("find_hit", background="#264f78")
                tab.text.mark_set("insert", end)
                tab.text.see(pos)
            else:
                messagebox.showinfo("Znajdź", "Nie znaleziono.", parent=dlg)

        ttk.Button(dlg, text="Dalej", command=_find_next).grid(row=1, column=1, sticky="e", padx=8, pady=(0, 8))
        entry.bind("<Return>", lambda e: _find_next())
        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)

    def _show_name_dictionary(self) -> None:
        tab = self._current_tab()
        text = tab.text if tab else None
        open_name_dictionary(self.root, self._lore, text)

    def _show_spellcheck(self) -> None:
        tab = self._current_tab()
        if tab is None:
            messagebox.showinfo("Pisownia", "Otwórz kartę z tekstem.", parent=self.root)
            return
        open_spellcheck(
            self.root,
            tab.text,
            self._lore,
            project_root=self._proj_root,
        )

    def _confirm_save_tab(self, tab: _TabState) -> bool:
        answer = messagebox.askyesnocancel(
            "Niezapisane zmiany",
            f"Zapisać zmiany w „{self._tab_display_name(tab).rstrip('*')}”?",
            parent=self.root,
        )
        if answer is None:
            return False
        if answer and not self._save_tab(tab):
            return False
        return True

    def _tab_id_at(self, event: tk.Event) -> Optional[str]:
        try:
            clicked = self._notebook.tk.call(self._notebook._w, "identify", "tab", event.x, event.y)
        except tk.TclError:
            return None
        if clicked in ("", None):
            return None
        tabs = self._notebook.tabs()
        try:
            return tabs[int(clicked)]
        except (ValueError, IndexError, tk.TclError):
            return clicked if clicked in tabs else None

    def _on_tab_click(self, event: tk.Event) -> Optional[str]:
        tab_id = self._tab_id_at(event)
        if not tab_id:
            return None
        bbox = self._notebook.bbox(tab_id)
        if not bbox:
            return None
        x, _y, width, _h = bbox
        if event.x > x + width - 22:
            self._close_tab_by_id(tab_id)
            return "break"
        return None

    def _on_tab_middle_click(self, event: tk.Event) -> str:
        tab_id = self._tab_id_at(event)
        if tab_id:
            self._close_tab_by_id(tab_id)
        return "break"

    def _close_tab_by_id(self, tab_id: str) -> bool:
        tab = self._tabs.get(tab_id)
        if tab is None:
            return True
        if tab.dirty:
            self._notebook.select(tab_id)
            if not self._confirm_save_tab(tab):
                return False
        self._notebook.forget(tab_id)
        tab.frame.destroy()
        del self._tabs[tab_id]
        if not self._tabs:
            self._new_tab()
        else:
            self._update_window_title()
            self._update_status()
        return True

    def _close_current_tab(self) -> None:
        tab_id = self._notebook.select()
        if tab_id:
            self._close_tab_by_id(tab_id)

    def _save_lore(self) -> None:
        try:
            self._lore.zapisz(historia_auto=False)
            self._panel.odswiez()
            self._status_var.set("Projekt lore zapisany")
        except Exception as e:
            messagebox.showerror("Błąd", str(e), parent=self.root)

    def _choose_project_dir(self) -> None:
        """Plik → Katalog projektu… — wybór folderu powieści z GUI."""
        kwargs = dict(
            parent=self.root,
            title="Katalog projektu (powieść)",
            initialdir=str(self._proj_root),
        )
        try:
            chosen = filedialog.askdirectory(**kwargs, mustexist=False)
        except TypeError:
            chosen = filedialog.askdirectory(**kwargs)
        if not chosen:
            return
        self._switch_project_dir(Path(chosen))

    def _use_default_project_dir(self) -> None:
        """Przełącz na domyślny ../dokumenty/lore."""
        target = default_work_dir()
        if not messagebox.askyesno(
            "Domyślny katalog",
            f"Ustawić katalog projektu na:\n{target} ?",
            parent=self.root,
        ):
            return
        self._switch_project_dir(target)

    def _switch_project_dir(self, new_root: Path) -> None:
        """Zamknij bieżący projekt i otwórz inny katalog (tryb lokalny)."""
        new_root = Path(new_root).expanduser().resolve()
        if new_root == self._proj_root.resolve():
            self._status_var.set(f"Katalog bez zmian: {new_root}")
            return

        if not self._lore.tryb_lokalny():
            messagebox.showinfo(
                "Katalog projektu",
                "W trybie sieciowym (--rpc) zmień katalog przy starcie:\n"
                f"  lore-editor --rpc --project-dir \"{new_root}\"\n\n"
                "Albo zamknij edytor i uruchom lokalnie.",
                parent=self.root,
            )
            return

        # Zapisz karty
        for tab_id in list(self._tabs.keys()):
            tab = self._tabs[tab_id]
            if tab.dirty:
                self._notebook.select(tab_id)
                if not self._confirm_save_tab(tab):
                    return

        zapisz_lore = True
        if self._lore.lore_niezapisane():
            ans = messagebox.askyesnocancel(
                "Niezapisane lore",
                "Zapisać graf lore przed zmianą katalogu?",
                parent=self.root,
            )
            if ans is None:
                return
            zapisz_lore = bool(ans)

        old = self._lore
        try:
            old.close(zapisz_lore=zapisz_lore)
        except Exception as e:
            if not messagebox.askyesno(
                "Katalog projektu",
                f"Nie udało się domknąć poprzedniego projektu:\n{e}\n\nKontynuować?",
                parent=self.root,
            ):
                return

        try:
            new_root.mkdir(parents=True, exist_ok=True)
            new_lore = LoreStore.open_local(project_dir=new_root)
        except Exception as e:
            messagebox.showerror(
                "Katalog projektu",
                f"Nie otwarto „{new_root}”:\n{e}",
                parent=self.root,
            )
            # próba powrotu — najlepiej nie zostawiać bez store; otwórz stary root
            try:
                self._lore = LoreStore.open_local(project_dir=self._proj_root)
                self._panel.set_lore(self._lore)
            except Exception as e2:
                messagebox.showerror(
                    "Katalog projektu",
                    "Nie otwarto nowego katalogu i nie przywrócono poprzedniego:\n"
                    f"{e}\n{e2}",
                    parent=self.root,
                )
            return

        self._lore = new_lore
        self._proj = new_lore.nazwa_projektu()
        self._proj_root = new_lore.katalog_projektu()
        save_last_work_dir(self._proj_root)
        try:
            import os

            os.chdir(self._proj_root)
        except OSError:
            pass

        self._proj_label_var.set(f"  ·  {self._proj}")
        self._path_status_var.set(str(self._proj_root))
        self._panel.set_lore(self._lore)

        # Wyczyść karty (tekst starego projektu) — bez ponownego potwierdzenia (już zapisane)
        for tab_id in list(self._tabs.keys()):
            tab = self._tabs[tab_id]
            self._notebook.forget(tab_id)
            tab.frame.destroy()
            del self._tabs[tab_id]

        restored = self._resolve_session_file()
        opened = False
        if restored is not None and restored.is_file():
            try:
                restored.resolve().relative_to(self._proj_root.resolve())
            except ValueError:
                restored = None
            if restored is not None:
                self._open_path(str(restored))
                opened = True
        if not opened:
            self._new_tab()

        self._update_window_title()
        self._update_status()
        self._status_var.set(f"Katalog projektu: {self._proj_root}")
        messagebox.showinfo(
            "Katalog projektu",
            f"Otwarto projekt „{self._proj}”\n{self._proj_root}",
            parent=self.root,
        )

    def _create_snapshot(self) -> None:
        from tkinter import simpledialog

        opis = simpledialog.askstring(
            "Punkt przywracania",
            "Opis (opcjonalnie):",
            parent=self.root,
        )
        if opis is None:
            return
        try:
            info = self._lore.utworz_snapshot(opis)
            if info:
                self._status_var.set(f"Snapshot: {info.label}")
            else:
                messagebox.showinfo("Historia", "Brak zmian od ostatniego snapshotu.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Historia", str(e), parent=self.root)

    def _change_locale(self, code: str) -> None:
        try:
            pack = set_locale(code, persist=True)
        except KeyError as e:
            messagebox.showerror(t("app.language"), str(e), parent=self.root)
            self._locale_var.set(get_locale())
            return
        self._locale_var.set(pack.code)
        # Przebuduj menu i pasek — etykiety z nowej paczki
        self._build_menu()
        self._build_ui_labels()
        self._update_status()
        self._update_window_title()
        messagebox.showinfo(
            t("app.language"),
            t("app.language_restart", name=pack.display_name()),
            parent=self.root,
        )

    def _build_ui_labels(self) -> None:
        """Odśwież etykiety toolbara / tytułu po zmianie locale."""
        self._status_var.set(t("app.ready"))
        for attr, key in (
            ("_title_lbl", "app.name"),
            ("_tb_new", "file.new"),
            ("_tb_open", "file.open"),
            ("_tb_save", "file.save"),
            ("_tb_save_as", "file.save_as"),
            ("_tb_catalog", "toolbar.catalog"),
            ("_tb_close", "file.close_tab"),
        ):
            w = getattr(self, attr, None)
            if w is not None:
                try:
                    w.configure(text=t(key))
                except tk.TclError:
                    pass

    def _show_history(self) -> None:
        open_history_window(self.root, self._lore, on_restored=self._odswiez_z_dysku)

    def _odswiez_z_dysku(self) -> None:
        """Po przywróceniu snapshotu — przeładuj otwarte karty z plików."""
        failed: list[str] = []
        for tab_id, tab in list(self._tabs.items()):
            if not tab.path or not Path(tab.path).is_file():
                continue
            try:
                content, enc = read_text_smart(tab.path)
            except (OSError, ValueError) as e:
                failed.append(f"{Path(tab.path).name}: {e}")
                continue
            tab.text.delete("1.0", tk.END)
            tab.text.insert("1.0", content)
            tab.encoding = enc
            tab.dirty = False
            self._update_tab_title(tab_id)
        self._panel.odswiez()
        self._update_window_title()
        self._update_status()
        if failed:
            messagebox.showwarning(
                "Historia",
                "Przywrócono snapshot, ale nie przeładowano kart:\n"
                + "\n".join(failed[:5]),
                parent=self.root,
            )

    def _schedule_autosave(self) -> None:
        self._autosave_fail_streak = 0

        def _tick():
            failed: list[str] = []
            partial_lore: list[str] = []
            for tab_id, tab in list(self._tabs.items()):
                if tab.dirty and tab.path:
                    try:
                        on_file_saved(
                            self._lore,
                            tab.path,
                            self._panel,
                            content=self._tab_content(tab),
                            encoding=tab.encoding,
                        )
                        tab.dirty = False
                        self._update_tab_title(tab_id)
                    except (OSError, UnicodeEncodeError) as e:
                        # Plik nie zapisany — zostaw dirty, spróbuj ponownie.
                        failed.append(f"{Path(tab.path).name}: {e}")
                    except Exception as e:
                        # Tekst mógł już trafić na dysk (transakcja: tekst → lore).
                        # Jak w ręcznym zapisie: dirty tekstu False, lore osobno.
                        tab.dirty = False
                        self._update_tab_title(tab_id)
                        partial_lore.append(f"{Path(tab.path).name}: {e}")
            if failed:
                self._autosave_fail_streak += 1
                # nie spamuj co minutę — status zawsze, dialog co 3. nieudaną rundę
                self._status_var.set(t("status.autosave_failed", error=failed[0]))
                if self._autosave_fail_streak % 3 == 1:
                    messagebox.showwarning(
                        t("app.name"),
                        t("status.autosave_failed", error="\n".join(failed[:3])),
                        parent=self.root,
                    )
            elif partial_lore:
                self._autosave_fail_streak = 0
                msg = partial_lore[0]
                self._status_var.set(
                    f"Autosave: tekst OK, lore nie — {msg} (Zapisz projekt lore)"
                )
                if not getattr(self, "_autosave_partial_warned", False):
                    self._autosave_partial_warned = True
                    messagebox.showwarning(
                        t("app.name"),
                        "Autosave zapisał tekst, ale nie graf lore.\n"
                        "Użyj „Zapisz projekt lore” albo Ctrl+S po naprawie.\n\n"
                        + "\n".join(partial_lore[:3]),
                        parent=self.root,
                    )
            else:
                self._autosave_fail_streak = 0
            self._update_window_title()
            # partial_lore: status już ustawiony; failed: status błędu
            if not failed and not partial_lore:
                self._update_status()
            self.root.after(_AUTOSAVE_MS, _tick)

        self.root.after(_AUTOSAVE_MS, _tick)

    def _on_close(self) -> None:
        for tab_id in list(self._tabs.keys()):
            tab = self._tabs[tab_id]
            if tab.dirty:
                self._notebook.select(tab_id)
                if not self._confirm_save_tab(tab):
                    return
        zapisz_lore = True
        if self._lore.lore_niezapisane():
            ans = messagebox.askyesnocancel(
                t("dialog.unsaved_lore"),
                t("dialog.unsaved_lore_ask"),
                parent=self.root,
            )
            if ans is None:
                return
            zapisz_lore = bool(ans)
            if not zapisz_lore and not messagebox.askokcancel(
                t("dialog.close_no_save"),
                t("dialog.close_no_save_ask"),
                parent=self.root,
            ):
                return
        try:
            self._lore.close(zapisz_lore=zapisz_lore)
        except Exception as e:
            if not messagebox.askyesno(
                t("app.name"),
                t("status.close_save_failed", error=str(e))
                + "\n\nZamknąć mimo błędu?",
                parent=self.root,
            ):
                return
        self.root.destroy()


def run_editor_window(
    lore: LoreStore,
    *,
    initial_files: Optional[list[str]] = None,
) -> None:
    EditorWindow(lore, initial_files=initial_files).run()