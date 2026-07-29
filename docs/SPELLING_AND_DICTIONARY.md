# Name dictionary and spell checking

**[Polski → SLOWNIK_I_PISOWNIA.md](SLOWNIK_I_PISOWNIA.md)**

**Status:** implemented (offline-first)  
**UI:** **Edit** menu · shortcuts **Ctrl+Shift+D**, **F7**  
**In-app help:** “Dictionary and spelling” / “Słownik i pisownia”

---

## Purpose

Two separate writer features:

1. **Name dictionary (lore)** — quick browse and insert of characters, places, and other graph entries.
2. **Spell checking** — orthography for chapter text offline (no network).

This is **not** a thesaurus or encyclopaedia. Proper names come from the Lore panel; orthography comes from SJP.PL (PL) or EN backends.

---

## Name dictionary (Ctrl+Shift+D)

| Element | Behaviour |
|---------|-----------|
| Data source | `LoreStore.wszystkie_wpisy()` + `podglad()` |
| Search | Name fragment or note/description text |
| Filter | Lore type (Character / Postać, Place, …) |
| Editor selection | Seeds the search field |
| Insert | Name at caret (replaces selection) |

UI module: `lore/dictionary_view.py` → `NameDictionaryDialog`.

---

## Spell check (F7)

Backend depends on **locale** (`meta.json` → `spell`, or active UI language):

| `spell` / locale | Engine |
|------------------|--------|
| `pl` (default) | SJP.PL hunspell → fallback `pl_common.txt.gz` |
| `en` | optional hunspell `lore/data/en_US/en_US` → EN bootstrap |
| other (`tlh`, `ja`, …) | lore + `.lore-spelling.json` + session only |

### Decision order (“is this word OK?”)

1. **Session** — “Ignore” for this F7 dialog  
2. **Lore** — full names and tokens from the graph  
3. **Project** — `.lore-spelling.json` in the novel folder  
4. **Acronyms** — all caps, length 2–6 (e.g. FBI)  
5. **Hunspell** (when available for the locale: SJP / en_US) via **spylls**  
6. **Fallback** — frequency list PL or EN bootstrap  

Tokenization: Latin + Polish letters; **CJK / Japanese** is not word-tokenized yet (needs a dedicated tokenizer later).

### SJP.PL engine (`spell=pl`)

| File | Role |
|------|------|
| `lore/data/sjp/pl_PL.aff` | Affix rules |
| `lore/data/sjp/pl_PL.dic` | Lemmas + flags |
| `lore/data/sjp/NOTICE.txt` | Attribution / license choice |
| `lore/data/sjp/README_pl_PL.txt` | Upstream README |

- Source: <https://sjp.pl/slownik/ort/>  
- **License (upstream choice):** GPL 2, LGPL 2.1, MPL 1.1, **Apache 2.0**, CC BY 4.0  
- **This project uses Apache 2.0** + attribution (compatible with MIT app code)

Engine: PyPI **`spylls`**.

Load: `lore.spellcheck.load_sjp_dictionary()` / `load_en_dictionary()` (cached).  
UI label: `backend_label(lang)`.

### Optional EN hunspell

```
lore/data/en_US/en_US.aff
lore/data/en_US/en_US.dic
```

Without them, EN uses a built-in common-word list + lore.

### Project file `.lore-spelling.json`

Created on first **Add to dictionary** in the F7 dialog.

```json
{
  "version": 1,
  "words": ["myword", "neologism"]
}
```

Words are matched with `casefold()`. Include the file in project backups.

### Spell UI

| Button | Action |
|--------|--------|
| Replace | Insert selected suggestion |
| Ignore | Skip for the rest of the dialog session |
| Add to dictionary | Write to `.lore-spelling.json` |
| Next | Next unknown word |
| Search in lore… | Opens name dictionary for the current word |

Unknown words are underlined in the editor (`spell_err` tag).

Modules: `lore/spellcheck.py`, `lore/dictionary_view.py`.

---

## Packaging

```toml
dependencies = [
  "spylls>=0.1.7",
]

[tool.setuptools.package-data]
lore = ["data/*.gz", "data/*.txt", "data/sjp/*", "locales/*/*"]
```

Nuitka/exe builds must ship `lore/data/` (including `sjp/`), or F7 falls back to frequency lists only.

---

## Tests

```bash
python -m unittest discover -s tests -p "test_spellcheck.py" -v
```

Coverage: PL tokenization, lore names, project dict, SJP load, inflection, suggestions.

---

## Limits

- No stylistic thesaurus — orthography + lore names only.  
- No live check on every keystroke (F7 only).  
- First load of `pl_PL.dic` via spylls may take a few seconds.  
- Intentional “errors” / neologisms: **Add to dictionary** or a lore entry.
