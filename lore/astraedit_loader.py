"""Ładowanie AstraEdit — vendor, lokalna kopia, ASTRAEDIT_PATH."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Type


def load_astraedit_gui() -> Type:
    repo = Path(__file__).resolve().parent.parent
    vendor_script = repo / "vendor" / "Astraedit" / "Astraedit-4.5.py"
    candidates: list[Path] = []
    env_path = os.environ.get("ASTRAEDIT_PATH", "").strip()
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend([
        Path.home() / "Documents" / "AstraEdit",
        repo / "AstraEdit",
    ])

    scripts: list[Path] = []
    if vendor_script.is_file():
        scripts.append(vendor_script)
    for base in candidates:
        if not base.is_dir():
            continue
        sys.path.insert(0, str(base))
        for name in ("AstraEdit.pyw", "AstraEdit.py", "Astraedit-4.5.py"):
            p = base / name
            if p.is_file() and p not in scripts:
                scripts.append(p)

    for script in scripts:
        try:
            spec = importlib.util.spec_from_file_location("astraedit_mod", script)
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "AstraEditGUI"):
                return mod.AstraEditGUI
        except Exception:
            continue

    try:
        from AstraEdit import AstraEditGUI  # type: ignore
        return AstraEditGUI
    except ImportError:
        pass

    raise ImportError(
        "Brak AstraEdit. Uruchom scripts/install_writer.ps1 lub ustaw ASTRAEDIT_PATH."
    )