# Lore Editor

**[Polski → README.md](README.md)**

Lore editor for **writers** — characters, ideas, influences, relationships — on the [Cynober DB](https://github.com/Maciej-EriAmo/DBase) engine.

A **writing tool** (offline-first) — no Lua, no game engine.

The lore graph lives in a **dedicated Cynober DB** (**Karmazyn** atom format, `.kafd` file). This is not plain SQL or a generic web API — see [Networking](#networking).

**Version:** `lore-editor --version` or **Help → About** (**F1**).

## Install

```bash
pip install "cynober-db>=8.0.1"
pip install -e .
```

Dependencies include:

| Package | Role |
|---------|------|
| `cynober-db` | Lore graph engine (Karmazyn / KarminQL) |
| `python-docx` | Manuscript export to Word |
| `spylls` | Hunspell engine (spelling + SJP.PL dictionary) |

**Writer (standalone app, no Python):** see [Standalone Windows app](#standalone-windows-app-no-python).

**Dev (Python + shortcut):**

```powershell
.\scripts\install_writer.ps1 -Project MyNovel
```

Optional fonts (Lexend, OpenDyslexic):

```powershell
.\scripts\install_fonts.ps1
```

## Project — zero config

### Work directory (priority order)

1. **`--project-dir DIR`** — explicit folder  
2. **`LORE_PROJECT_DIR`** — environment variable  
3. **`.lore-project`** — in cwd or parent directories  
4. **Last GUI choice** — File → Project folder… (`~/.lore_editor/last_work_dir.json`)  
5. **Default:** `../dokumenty/lore` relative to the `lore-editor` repo root  
   Override: `LORE_DEFAULT_WORK_DIR`.

**In the GUI:**

| Action | Where |
|--------|--------|
| Pick novel folder | **File → Project folder…** (`Ctrl+Shift+O`) or **Folder…** |
| Back to `dokumenty/lore` | **File → Default folder (documents/lore)** |
| Quick open | Project path on the **status bar** (right) |

**Session:** on start, last work directory and **last chapter file** are restored if they still exist. A `.lore-project` marker inside the *app source* tree is ignored.

```powershell
lore-editor
# → …/dokumenty/lore  (created on first run)

lore-editor --project-dir ~/documents/OtherNovel
set LORE_PROJECT_DIR=D:\Writing\Saga
lore-editor

cd ~/documents/MyNovel   # contains .lore-project
lore-editor
```

`.lore-project` file:

```
name=MyNovel
```

World name = `name=` from the marker, `--project`, or the folder name.

On **first run** in a folder:

- `.lore-project`
- `.lore-history/` (snapshots of lore + chapters)
- `Name.kafd` (on first lore save)

## Folder layout

```
MyNovel/
  .lore-project
  .lore-history/
    README.txt
    manifest.json
    snapshots/
  chapter_01.txt
  chapter_02.md
  MyNovel.kafd              # lore graph (Lore Pack)
  .lore-spelling.json       # optional project spell words
```

| Path | Holds |
|------|--------|
| `.txt` / `.md` | Chapter prose |
| `.kafd` | Lore graph + file pointers |
| `.lore-project` | Cynober world name |
| `.lore-history/` | Restore snapshots |
| `.lore-spelling.json` | Project dictionary (F7 → Add to dictionary) |

### Name dictionary and spelling

- **Edit → Name dictionary…** (`Ctrl+Shift+D`) — browse lore names, insert into text.
- **Edit → Check spelling…** (`F7`) — offline:
  - **PL:** **SJP.PL** hunspell ([sjp.pl](https://sjp.pl/slownik/ort/)), [spylls](https://pypi.org/project/spylls/)
  - **EN:** hunspell `en_US` if present under `lore/data/en_US/`, else common EN list
  - lore names + `.lore-spelling.json` always
  - other locales: lore + project dict

SJP attribution: `lore/data/sjp/NOTICE.txt`. Details: **Help → Dictionary and spelling** and [docs/SPELLING_AND_DICTIONARY.md](docs/SPELLING_AND_DICTIONARY.md).

Legacy (`*.meta.json` + `shards/`) is **auto-migrated** into a single `.kafd` on save.

**Backup:** copy the whole project folder, including `.lore-history/`.

## UI language (locale packs)

Menus, toolbar, panel, and status use **locale packs** — separate from KarminQL and `.kafd` values.

| Source | Code | Notes |
|--------|------|--------|
| Built-in | `pl` | Polish (default) |
| Built-in | `en` | English — `lore/locales/en/` |
| Plugin (example) | `tlh` | Klingon template — `plugins/locales/tlh/` |

```powershell
lore-editor --locale en
lore-editor --locale tlh
$env:LORE_LOCALE = "en"; lore-editor
```

- In-app **Language** menu (`~/.lore_editor/settings.json`)
- **`LORE_LOCALE`** wins at startup
- Extra packs: `LORE_LOCALE_PATHS` or entry point `lore_editor.locale`

**How to add a language (Japanese / Klingon template):** [docs/LANGUAGE_PLUGINS.md](docs/LANGUAGE_PLUGINS.md)  
Polish original: [docs/PLUGINY_JEZYKOWE.md](docs/PLUGINY_JEZYKOWE.md).

> KarminQL commands (`UTRWAL`, `ZNAJDŹ`) and graph types (`Postać`, …) are **not** translated — the same `.kafd` works under PL and EN UI.

## Running

```bash
lore-editor                              # default work dir (offline)
lore-editor --project-dir D:\Writing\X
lore-editor --file chapter_01.txt
lore-editor chapter_01.txt chapter_02.md
lore-editor --locale en
lore-editor --rpc --host 192.168.1.10    # see networking below
```

## Networking

**Trap:** `--host` and port `8080` look like “plain TCP”, but Lore Editor does **not** speak HTTP, REST, or SQL. Network mode uses the **Karmazyn protocol** (HSS handshake, HSL, binary frames) and **KarminQL-RPC** JSON on **cynober-server** from **cynober-db**.

### Default — offline (recommended)

| Layer | Technology |
|-------|------------|
| Editor → lore | In-process Python |
| Graph engine | **Cynober DB** (KarminQL) |
| Lore storage | `.kafd` — **Karmazyn** atoms |
| Chapters | Local `.txt` / `.md` |

No sockets. Firewall does not matter.

### Network — Karmazyn + Cynober DB

Enable explicitly: `lore-editor --rpc --host ADDR [--port 8080]`.

| Layer | What |
|-------|------|
| Transport | TCP/IP (default **8080**) |
| Handshake | **Karmazyn HSS** |
| Session | **Karmazyn HSL** (RPC capability) |
| Framing | Binary length-prefix frames — **not** HTTP text |
| Payload | JSON `"query"` = KarminQL line |
| Protocol version | `Cynober-Secure-1.2` (`cynober_client`) |
| Server | **cynober-server** |

Chapters stay **local**; only the **lore graph** goes over the wire.

```bash
cynober-server

lore-editor --rpc --host 192.168.1.10 --port 8080

# Server with auth.json:
lore-editor --rpc --host 192.168.1.10 --rpc-user writer --rpc-token secret
# LORE_RPC_USER / LORE_RPC_TOKEN  or user+token in ~/.karmazyn_client.json
```

#### RPC auth (0.7.5+)

| Situation | Behaviour |
|-----------|-----------|
| **127.0.0.1 / localhost** without token | Allowed (dev / local server without auth) |
| **Remote** host without user+token | **Error** — fail-fast |
| Remote server without auth | Set `LORE_RPC_ALLOW_ANON=1` (explicit) |
| Force auth on loopback | `LORE_RPC_REQUIRE_AUTH=1` |

Trusted LAN/VPN only — do not expose cynober-server on the public internet without a tunnel. Prefer env/profile over `--rpc-token` (visible in process list).

**cynober-db:** prefer **≥ 8.0.2** (world ACL + gossip fixes). Local: `pip install -e path/to/DBase`.

### Team sync (Team tab)

**cynober_replicate** (push / pull / sync) — again TCP to **cynober-server**, not FTP of `.kafd`. Requires local mode with a saved project file. Same auth rules as RPC: non-loopback hosts need user+token (Team panel fields or `LORE_RPC_*`).

### Common mistakes

| You might think… | Reality |
|------------------|---------|
| HTTP/REST on 8080 | **No.** Port 8080 is **cynober-server**, not a web API. |
| Lore is SQL | **No.** Karmazyn atoms in `.kafd`. |
| Any TCP JSON is fine | **No.** HSS → HSL → frames first; then KarminQL-RPC. |
| Sync = rsync the `.kafd` | **Not** the app protocol (file backup is fine). |
| Custom backend without cynober-server | **No.** Client speaks only **Cynober-Secure-1.2**. |

Help: **Help → Network: Karmazyn and Cynober DB** (F1).

## In-app help

**Help** menu or **F1**. Titles follow the active locale; Polish names below:

| Topic | Content |
|-------|---------|
| Writer’s guide | Quick start, save, history, UI language |
| Keyboard shortcuts | Ctrl+S, Ctrl+W, Ctrl+F… |
| Fonts and appearance | Draft / print / accessibility presets |
| Print and export | Page preview, DOCX, screenplay |
| Lore panel | Characters, links, team sync |
| Dictionary and spelling | Lore names, F7, SJP / EN |
| Temporal context | Per-chapter character state |
| Semantic queries | Graph search |
| Change history | Snapshots, restore |
| Files and Lore Pack | What is inside `.kafd` |
| Network: Karmazyn and Cynober DB | Protocol and `--rpc` |
| About | Version, licenses |

## Text editor

### Files and tabs

- Multiple tabs
- Close: tab `×`, **Ctrl+W**, middle-click
- **Autosave** every 60 s for paths already on disk — also flushes lore; errors surface in the status bar

### Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New tab |
| Ctrl+O | Open |
| Ctrl+S | Save chapter **and** lore (transactional) |
| Ctrl+Shift+S | Save as… |
| Ctrl+W | Close tab |
| Ctrl+Z / Ctrl+Y | Undo / Redo |
| Ctrl+F | Find in chapter |
| Ctrl+Shift+D | Name dictionary |
| Ctrl+Shift+O | Project folder… |
| F7 | Spell check |
| F1 | Help |

### Saving

| Action | Writes |
|--------|--------|
| **Save** (Ctrl+S) | Chapter text **and** lore `.kafd` |
| **Autosave** | Same as Ctrl+S every 60 s |
| **Save lore project** | Lore only |

Closing warns if the lore graph is dirty. Discard (`zapisz_lore=False`) does **not** flush unsaved graph changes to disk.

### Appearance

**View** menu — `%USERPROFILE%\.lore_editor\typography.json`.

Drafting: Courier / Calibri / Arial · Print: Garamond / Times New Roman · Accessibility: OpenDyslexic / Lexend.

### Print and export

**Print** menu: page preview (screenplay / submission / print-ready) and **DOCX** export.

## Lore panel

Tabs: **Chapter · Search · Team**.

Links to a chapter need an **open file** in the editor.

| Button | Role |
|--------|------|
| **+ Character** | Create character; auto-link if a chapter is open |
| **+ Idea** | Note linked to the chapter |
| **+ Influence** | Inspiration with “inspiruje” relation |
| **Link to chapter** | Bind selected entry to current file |
| **Connect to…** | Relation between two entries |
| **Unlink / Delete** | Unlink file or remove entry (snapshot first) |
| **Relationship map** | Graph around chapter or entry |

### Temporal context

Editing notes with a chapter open stores **per-chapter** mutations — other chapters keep their state.

### Thermodynamics

List order uses temperature: **hot / warm / cold / tomb** (long unused).

### Semantic search

```
characters near Anna not from 5
typ:Postać "ally"
```

### History

Manual restore points and snapshot list under **Lore** menu. Snapshots cover `.kafd` + all chapters.

### Team

Local mode + **cynober-server**. Push / Pull / Sync.

## Standalone Windows app (no Python)

Built with Nuitka; novel files go to `dokumenty\lore`, **not** the install folder.

```powershell
.\scripts\build_nuitka.ps1
.\scripts\install_standalone.ps1
# → %LOCALAPPDATA%\LoreEditor\
```

Or unpack `LoreEditor-*-win64.zip` and run `run_lore_editor.exe`.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Documentation in this repo

| File | Topic |
|------|--------|
| [docs/LANGUAGE_PLUGINS.md](docs/LANGUAGE_PLUGINS.md) | Locale packs (EN) |
| [docs/PLUGINY_JEZYKOWE.md](docs/PLUGINY_JEZYKOWE.md) | Locale packs (PL) |
| [docs/SPELLING_AND_DICTIONARY.md](docs/SPELLING_AND_DICTIONARY.md) | Spelling (EN) |
| [docs/SLOWNIK_I_PISOWNIA.md](docs/SLOWNIK_I_PISOWNIA.md) | Spelling (PL) |
| [docs/MULTIMEDIA_STREAMING_ROADMAP.md](docs/MULTIMEDIA_STREAMING_ROADMAP.md) | Media roadmap (EN) |
| [docs/KIERUNEK_MULTIMEDIA_STREAMING.md](docs/KIERUNEK_MULTIMEDIA_STREAMING.md) | Media roadmap (PL) |

## License

Lore Editor code: **MIT**.

### Spelling components

| Component | Source | License (choice) |
|-----------|--------|------------------|
| Polish orthography | [SJP.PL](https://sjp.pl/slownik/ort/) (`lore/data/sjp/`) | **Apache 2.0** (among others) |
| Hunspell in Python | [spylls](https://pypi.org/project/spylls/) | per PyPI package |

This project uses SJP.PL under **Apache 2.0** with attribution — see `lore/data/sjp/NOTICE.txt`.
