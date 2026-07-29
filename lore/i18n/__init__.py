"""
Międzynarodowość Lore Editor — locale packs (wbudowane + pluginy).

  from lore.i18n import t, set_locale, get_locale, list_locales

  set_locale("en")
  label = t("menu.file")
"""

from __future__ import annotations

from lore.i18n.core import (
    LocalePack,
    discover_and_load,
    get_locale,
    list_locales,
    load_locale_dir,
    register_pack,
    set_locale,
    t,
    ui,
)

__all__ = [
    "LocalePack",
    "discover_and_load",
    "get_locale",
    "list_locales",
    "load_locale_dir",
    "register_pack",
    "set_locale",
    "t",
    "ui",
]
