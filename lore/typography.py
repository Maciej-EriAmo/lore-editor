"""Presety czcionek i interlinii dla edytora rozdziałów."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

try:
    import tkinter as tk
    from tkinter import font as tkfont
except ImportError:
    tk = None  # type: ignore
    tkfont = None  # type: ignore

SETTINGS_DIR = Path.home() / ".lore_editor"
SETTINGS_FILE = SETTINGS_DIR / "typography.json"

TAG_BODY = "lore_body"


@dataclass(frozen=True)
class TypographyPreset:
    id: str
    label: str
    category: str
    family: str
    fallbacks: Tuple[str, ...]
    size: int
    line_spacing: float
    hint: str = ""

    def menu_label(self) -> str:
        return self.label


PRESETS: Tuple[TypographyPreset, ...] = (
    TypographyPreset(
        "drafting_courier_new",
        "Courier New — maszynopis",
        "drafting",
        "Courier New",
        ("Consolas",),
        12,
        1.5,
        "Klasyczny maszynopis; 1 strona ≈ 1 min (scenariusz).",
    ),
    TypographyPreset(
        "drafting_courier_prime",
        "Courier Prime — maszynopis",
        "drafting",
        "Courier Prime",
        ("Courier New", "Consolas"),
        12,
        1.5,
        "Nowoczesny maszynopis scenariuszowy.",
    ),
    TypographyPreset(
        "drafting_calibri",
        "Calibri — szkic",
        "drafting",
        "Calibri",
        ("Segoe UI", "Arial"),
        11,
        1.5,
        "Bezszeryfowa, lekka przy długich sesjach.",
    ),
    TypographyPreset(
        "drafting_arial",
        "Arial — szkic",
        "drafting",
        "Arial",
        ("Calibri", "Segoe UI"),
        11,
        1.5,
        "Prosta bezszeryfowa — standard Windows.",
    ),
    TypographyPreset(
        "print_garamond",
        "Garamond — powieść / druk",
        "print",
        "Garamond",
        ("EB Garamond", "Times New Roman"),
        12,
        1.0,
        "Elegancka, oszczędna — typowy wybór wydawców.",
    ),
    TypographyPreset(
        "print_times",
        "Times New Roman — maszynopis",
        "print",
        "Times New Roman",
        ("Times",),
        12,
        1.0,
        "Standard tradycyjnych wydawnictw (rękopis do wysyłki).",
    ),
    TypographyPreset(
        "a11y_opendyslexic",
        "OpenDyslexic",
        "accessibility",
        "OpenDyslexic",
        ("Lexend Deca", "Arial"),
        12,
        1.5,
        "Litery rozdzielone — łatwiejsza redakcja przy dysleksji.",
    ),
    TypographyPreset(
        "a11y_lexend",
        "Lexend",
        "accessibility",
        "Lexend",
        ("Lexend Deca", "Calibri", "Arial"),
        12,
        1.5,
        "Wysoka czytelność przy zmęczonym wzroku.",
    ),
)

_LEGACY_PRESET_MAP = {
    "drafting_courier": "drafting_courier_new",
    "drafting_sans": "drafting_calibri",
}

_PRESET_BY_ID = {p.id: p for p in PRESETS}


def get_preset(preset_id: str) -> TypographyPreset:
    return _PRESET_BY_ID.get(preset_id, PRESETS[0])

CATEGORY_LABELS = {
    "drafting": "Szkic (drafting)",
    "print": "Druk i publikacja",
    "accessibility": "Czytelność",
}


@dataclass
class TypographySettings:
    preset_id: str = "drafting_courier_new"
    size: Optional[int] = None
    line_spacing: Optional[float] = None

    def resolved(self) -> Tuple[TypographyPreset, int, float]:
        preset = _PRESET_BY_ID.get(self.preset_id) or PRESETS[0]
        size = self.size if self.size is not None else preset.size
        spacing = self.line_spacing if self.line_spacing is not None else preset.line_spacing
        return preset, size, spacing


def list_presets_by_category() -> List[Tuple[str, str, List[TypographyPreset]]]:
    order = ("drafting", "print", "accessibility")
    out: List[Tuple[str, str, List[TypographyPreset]]] = []
    for cat in order:
        items = [p for p in PRESETS if p.category == cat]
        if items:
            out.append((cat, CATEGORY_LABELS.get(cat, cat), items))
    return out


def resolve_font_family(
    preset: TypographyPreset,
    *,
    families: Optional[Iterable[str]] = None,
) -> str:
    """Wybierz pierwszą dostępną rodzinę czcionek (Tk / system)."""
    if families is None:
        if tkfont is None:
            return preset.family
        families = tkfont.families()
    available = set(families)
    for name in (preset.family, *preset.fallbacks):
        if name in available:
            return name
    return "Courier New" if "Courier New" in available else "TkFixedFont"


def spacing2_pixels(size: int, line_spacing: float) -> int:
    """Dodatkowy odstęp między wierszami (spacing2) dla Tk Text."""
    if line_spacing <= 1.0:
        return 0
    return max(0, int(round(size * (line_spacing - 1.0) * 1.35)))


def load_typography_settings() -> TypographySettings:
    try:
        raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return TypographySettings()
        preset_id = str(raw.get("preset_id", "drafting_courier_new"))
        preset_id = _LEGACY_PRESET_MAP.get(preset_id, preset_id)
        if preset_id not in _PRESET_BY_ID:
            preset_id = "drafting_courier_new"
        size = raw.get("size")
        line_spacing = raw.get("line_spacing")
        return TypographySettings(
            preset_id=preset_id,
            size=int(size) if size is not None else None,
            line_spacing=float(line_spacing) if line_spacing is not None else None,
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return TypographySettings()


def save_typography_settings(settings: TypographySettings) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {k: v for k, v in asdict(settings).items() if v is not None}
    SETTINGS_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def apply_typography(
    text: "tk.Text",
    settings: TypographySettings,
    *,
    families: Optional[Iterable[str]] = None,
) -> str:
    """Zastosuj czcionkę i interlinię do widżetu Text. Zwraca wybraną rodzinę."""
    preset, size, line_spacing = settings.resolved()
    family = resolve_font_family(preset, families=families)
    text.configure(font=(family, size))
    extra = spacing2_pixels(size, line_spacing)
    text.tag_configure(TAG_BODY, spacing1=0, spacing2=extra, spacing3=0)
    text.tag_add(TAG_BODY, "1.0", "end")
    text.tag_lower(TAG_BODY)
    return family


def refresh_body_tag(text: "tk.Text") -> None:
    """Po edycji — utrzymaj tag interlinii na całym tekście."""
    if TAG_BODY not in text.tag_names():
        return
    text.tag_add(TAG_BODY, "1.0", "end")


def settings_summary(settings: TypographySettings, *, family: str = "") -> str:
    preset, size, spacing = settings.resolved()
    fam = family or preset.family
    return f"{preset.label} · {fam} {size} pt · interlinia {spacing:g}"