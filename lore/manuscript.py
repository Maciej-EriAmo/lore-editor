"""Paginacja, profile wydawnicze i statystyki rękopisu."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

SCREENPLAY_LINES_PER_PAGE = 55
SCREENPLAY_SECONDS_PER_PAGE = 60


@dataclass(frozen=True)
class ManuscriptProfile:
    id: str
    label: str
    font_family: str
    font_size_pt: int
    line_spacing: float
    page_format: str  # A4 | Letter
    margin_mm: float
    chars_per_inch: float
    lines_per_page: Optional[int] = None
    words_per_page: Optional[int] = None
    screenplay_timing: bool = False

    @property
    def page_size_mm(self) -> Tuple[float, float]:
        if self.page_format == "Letter":
            return (215.9, 279.4)
        return (210.0, 297.0)  # A4


PROFILES: Tuple[ManuscriptProfile, ...] = (
    ManuscriptProfile(
        "screenplay",
        "Scenariusz (Courier, 55 wierszy/str.)",
        "Courier New",
        12,
        1.0,
        "Letter",
        25.4,
        10.0,
        lines_per_page=SCREENPLAY_LINES_PER_PAGE,
        screenplay_timing=True,
    ),
    ManuscriptProfile(
        "submission",
        "Rękopis do wysyłki (TNR 12, interlinia 2,0)",
        "Times New Roman",
        12,
        2.0,
        "A4",
        25.4,
        12.0,
        words_per_page=250,
    ),
    ManuscriptProfile(
        "print_ready",
        "Gotowy do druku (TNR 12, interlinia 1,0)",
        "Times New Roman",
        12,
        1.0,
        "A4",
        20.0,
        12.0,
        words_per_page=350,
    ),
)

_PROFILE_BY_ID = {p.id: p for p in PROFILES}


@dataclass
class PageSlice:
    number: int
    start_line: int
    end_line: int
    lines: List[str]
    preview: str


@dataclass
class ManuscriptStats:
    profile: ManuscriptProfile
    total_lines: int
    wrapped_lines: int
    pages: int
    words: int
    chars: int
    estimated_minutes: Optional[float] = None
    page_slices: Tuple[PageSlice, ...] = ()

    def summary(self) -> str:
        parts = [f"{self.pages} str."]
        if self.profile.screenplay_timing and self.estimated_minutes is not None:
            m = int(round(self.estimated_minutes))
            parts.append(f"~{m} min")
        else:
            parts.append(f"{self.words} słów")
        return " · ".join(parts)


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _wrap_line(line: str, chars_per_line: int) -> List[str]:
    if chars_per_line <= 1:
        return [line] if line else [""]
    if not line:
        return [""]
    out: List[str] = []
    rest = line
    while len(rest) > chars_per_line:
        cut = rest.rfind(" ", 0, chars_per_line + 1)
        if cut <= 0:
            cut = chars_per_line
        out.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    out.append(rest)
    return out


def _chars_per_line(profile: ManuscriptProfile) -> int:
    width_mm, _ = profile.page_size_mm
    usable_in = (width_mm - 2 * profile.margin_mm) / 25.4
    return max(40, int(usable_in * profile.chars_per_inch))


def _lines_per_page_calc(profile: ManuscriptProfile) -> int:
    if profile.lines_per_page:
        return profile.lines_per_page
    _, height_mm = profile.page_size_mm
    usable_mm = height_mm - 2 * profile.margin_mm
    line_height_mm = profile.font_size_pt * 0.3528 * profile.line_spacing
    return max(20, int(usable_mm / line_height_mm))


def wrap_document(text: str, profile: ManuscriptProfile) -> List[str]:
    cpl = _chars_per_line(profile)
    wrapped: List[str] = []
    for raw in text.splitlines():
        wrapped.extend(_wrap_line(raw, cpl))
    if not wrapped:
        wrapped = [""]
    return wrapped


def paginate(text: str, profile_id: str = "print_ready") -> ManuscriptStats:
    profile = _PROFILE_BY_ID.get(profile_id, PROFILES[-1])
    words = word_count(text)
    chars = len(text)
    raw_lines = text.splitlines()
    total_lines = len(raw_lines) if raw_lines else 1

    if profile.words_per_page and not profile.lines_per_page:
        wrapped = wrap_document(text, profile)
        lpp = _lines_per_page_calc(profile)
        slices = _slice_by_lines(wrapped, lpp)
        pages = max(1, math.ceil(words / profile.words_per_page)) if words else 1
        est_min = None
    elif profile.lines_per_page:
        lines = raw_lines if raw_lines else [""]
        lpp = profile.lines_per_page
        pages = max(1, math.ceil(len(lines) / lpp))
        wrapped = lines
        slices = _slice_by_lines(lines, lpp)
        est_min = pages * (SCREENPLAY_SECONDS_PER_PAGE / 60.0) if profile.screenplay_timing else None
    else:
        wrapped = wrap_document(text, profile)
        lpp = _lines_per_page_calc(profile)
        pages = max(1, math.ceil(len(wrapped) / lpp))
        slices = _slice_by_lines(wrapped, lpp)
        est_min = None

    return ManuscriptStats(
        profile=profile,
        total_lines=total_lines,
        wrapped_lines=len(wrapped),
        pages=pages,
        words=words,
        chars=chars,
        estimated_minutes=est_min,
        page_slices=tuple(slices),
    )


def _slice_by_lines(lines: List[str], lpp: int) -> List[PageSlice]:
    slices: List[PageSlice] = []
    if not lines:
        lines = [""]
    page_num = 1
    for start in range(0, len(lines), lpp):
        chunk = lines[start : start + lpp]
        preview = "\n".join(chunk[:4])
        if len(chunk) > 4:
            preview += "\n…"
        slices.append(
            PageSlice(
                number=page_num,
                start_line=start + 1,
                end_line=start + len(chunk),
                lines=chunk,
                preview=preview.strip(),
            )
        )
        page_num += 1
    return slices


def profile_for_preset(preset_id: str) -> str:
    """Mapuj preset edytora na profil paginacji."""
    pid = preset_id
    if preset_id == "drafting_courier":
        pid = "drafting_courier_new"
    elif preset_id == "drafting_sans":
        pid = "drafting_calibri"
    if pid in ("drafting_courier_new", "drafting_courier_prime"):
        return "screenplay"
    if pid in ("print_garamond", "print_times"):
        return "print_ready"
    return "submission"


def get_profile(profile_id: str) -> ManuscriptProfile:
    return _PROFILE_BY_ID.get(profile_id, PROFILES[0])