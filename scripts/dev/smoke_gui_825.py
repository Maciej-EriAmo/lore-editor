"""Smoke: LoreStore + EditorWindow against cynober-db 8.2.5."""
from __future__ import annotations

import tempfile
from importlib.metadata import version
from pathlib import Path

from lore.editor_window import EditorWindow
from lore.store import LoreStore


def main() -> None:
    print("cynober-db", version("cynober-db"))
    td = Path(tempfile.mkdtemp(prefix="lore_smoke_"))
    print("project_dir", td)

    store = LoreStore.open_local("Smoke8_2_5", project_dir=str(td))
    store.dodaj_postac("Bohater", notatka="smoke 8.2.5")
    store.ustaw("Bohater", "Rola", "protagonista")
    store.zapisz()
    assert store.encja_istnieje("Bohater"), "Bohater missing after save"
    entries = store.wszystkie_wpisy()
    print("entries", entries)
    assert "Bohater" in entries
    kafd = list(td.rglob("*.kafd"))
    print("kafd", kafd)
    assert kafd, "no .kafd after zapisz"

    win = EditorWindow(store, initial_files=[])
    root = win.root
    root.update_idletasks()
    root.update()
    assert root.winfo_exists()
    print("window", root.winfo_width(), "x", root.winfo_height())
    print("title", root.title())
    root.after(600, root.destroy)
    root.mainloop()
    try:
        store.close(zapisz_lore=False)
    except Exception as e:
        print("close warn", e)
    print("SMOKE_GUI_OK")


if __name__ == "__main__":
    main()
