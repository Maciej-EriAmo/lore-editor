# Language plugins (locale packs)

**[Polski → PLUGINY_JEZYKOWE.md](PLUGINY_JEZYKOWE.md)**

**App version:** 0.7.5+  
**Module:** `lore/i18n/` · built-in: `lore/locales/en/` · example: `plugins/locales/tlh/`

Lore Editor keeps **UI language** separate from KarminQL and values stored in `.kafd`.  
Database commands (`UTRWAL`, `ZNAJDŹ`) and graph types (`Postać`, …) stay stable — only menu, toolbar, panel, status, and optional help text are translated.

## Quick start

```powershell
# Built-in English
lore-editor --locale en

# Klingon sample plugin from the repo
$env:LORE_LOCALE="tlh"
lore-editor

# One session only:
lore-editor --locale tlh
```

Preference is stored in `%USERPROFILE%\.lore_editor\settings.json` (`"locale": "en"`).

Environment variable **`LORE_LOCALE`** wins at startup.

In the app: **Language** menu (registered packs).

---

## What a pack contains

A directory with at least:

| File | Required | Description |
|------|----------|-------------|
| `meta.json` | yes | `code`, `name`, `native_name`, `spell` |
| `ui.json` | yes | `key` → UI string |
| `help.json` | no | help topics `{ id: { title, body } }` |

### `meta.json` (Klingon example)

```json
{
  "code": "tlh",
  "name": "Klingon",
  "native_name": "tlhIngan Hol",
  "spell": "tlh",
  "author": "You",
  "version": "0.1"
}
```

- **`code`** — id (`en`, `ja`, `tlh`)  
- **`spell`** — spell backend: `pl`, `en`, or custom (fallback: lore names + project dictionary)  
- **`native_name`** — label in the **Language** menu  

### `ui.json`

Keys as in `lore/locales/en/ui.json`, e.g.:

```json
{
  "menu.file": "teywI'",
  "file.save": "pol",
  "app.ready": "ruch"
}
```

Missing keys fall back to **built-in Polish**, then to the raw key.

---

## Where to put a plugin

### 1. Plugin directory (simplest)

```
plugins/locales/<code>/
  meta.json
  ui.json
  help.json      # optional
```

Repo sample: **`plugins/locales/tlh/`** (Klingon).

Extra paths:

```powershell
$env:LORE_LOCALE_PATHS="D:\my-locales;D:\other\tlh"
```

Each entry is either a pack folder with `ui.json`, or a parent of such folders.

### 2. Setuptools entry point

```toml
[project.entry-points."lore_editor.locale"]
tlh = "my_tlh_package:get_pack"
```

```python
from pathlib import Path
from lore.i18n import LocalePack, load_locale_dir

def get_pack():
    return load_locale_dir(Path(__file__).parent / "data")
```

---

## Adding a language step by step (Klingon as template)

1. Copy folder:
   ```text
   plugins/locales/tlh  →  plugins/locales/ja
   ```
2. Edit `meta.json`: `"code": "ja"`, `"native_name": "日本語"`, `"spell": "ja"`.
3. Translate all strings in `ui.json` (start with `menu.*` and `file.*`).
4. Optionally add `help.json` with `writer_guide`.
5. Run:
   ```powershell
   lore-editor --locale ja
   ```
6. The new item should appear under **Language**.

For **Japanese**, orthography is not PL hunspell — start with lore names + `.lore-spelling.json`. Full morphology (Sudachi/MeCab) would be a separate `spell` backend.

---

## Spelling vs locale

| `spell` | Behaviour |
|---------|-----------|
| `pl` | SJP.PL (`lore/data/sjp/pl_PL`) + fallback list |
| `en` | hunspell under `lore/data/en_US` if present; else common EN + lore |
| other | lore + project dictionary + session “ignore” |

Tokenization is still Latin + Polish; CJK needs a future tokenizer.  
Details: [SPELLING_AND_DICTIONARY.md](SPELLING_AND_DICTIONARY.md).

---

## Important `ui.json` keys

| Prefix | Examples |
|--------|----------|
| `app.*` | `app.name`, `app.ready`, `app.language` |
| `menu.*` | `menu.file`, `menu.edit`, `menu.lore`, `menu.help` |
| `file.*` | `file.new`, `file.save`, `file.quit` |
| `edit.*` | `edit.find`, `edit.spellcheck` |
| `panel.*` | `panel.add_character`, `panel.tab_chapter`, `panel.push` |
| `help.*` | `help.writer_guide`, `help.title` |
| `dialog.*` | `dialog.save`, `dialog.unsaved_lore_ask` |
| `status.*` | `status.autosave_failed`, `status.close_save_failed` |

Full reference: `lore/locales/en/ui.json` (built-in PL defaults in `lore/i18n/core.py`).

### Optional `help.json`

```json
{
  "writer_guide": { "title": "…", "body": "…" },
  "shortcuts": { "title": "…", "body": "…" },
  "spell": { "title": "…", "body": "…" }
}
```

IDs map to Polish topics: `writer_guide`, `shortcuts`, `fonts`, `print`, `panel`, `spell`, `temporal`, `query`, `history`.

---

## Code API

```python
from lore.i18n import t, set_locale, list_locales, discover_and_load

discover_and_load()
set_locale("en")
print(t("menu.file"))  # "File"

for pack in list_locales():
    print(pack.code, pack.display_name(), pack.source)
```

---

## What **not** to translate in a plugin

- KarminQL / RPC commands (`WYBIERZ ŚWIAT`, …)
- Graph relation keys (`wplywa_na`, …)
- `Typ` values already stored in projects (`Postać`, …)

So a PL project opens under EN UI without data migration.

---

## Built-in English

Pack **`lore/locales/en/`** ships with the app (no external plugin).

```powershell
lore-editor --locale en
```

---

## Notes for 0.7.4

- Locale packs: PL / EN / plugin `tlh`
- RPC login (`--rpc-user` / `LORE_RPC_USER` + token)
- Safe close: `close(zapisz_lore=False)` does **not** flush a dirty world
- Read-only KarminQL does not mark the world dirty
- Autosave reports failures
- Project dirs isolated without global `CYNOBER_WORLDS_DIR`

## Notes for 0.7.5 (app-wide)

- RPC / Team: non-loopback host **requires** user+token (fail-fast); use `LORE_RPC_ALLOW_ANON=1` only on purpose
- Team panel: User/Token fields + warning for remote hosts
- History: full restore (strict) drops chapter files not in the snapshot
- Local unfold: **ROZWIŃ** (ROZWIJ alias on the wire for cynober-server)
- Autosave matches manual save when text succeeds but lore fails
- Standalone build: `LoreEditor-0.7.5-win64` (`scripts/build_nuitka.ps1`)

---

*The `tlh` sample is intentionally incomplete as a language — it is a structural template, not an official Klingon localization.*
