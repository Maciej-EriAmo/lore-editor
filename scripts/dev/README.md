# Skrypty deweloperskie

Jednorazowe i pomocnicze skrypty (audyt, repro, odzyskiwanie).  
**Nie** są częścią instalacji dla pisarzy.

Instalacja / build (w katalogu nadrzędnym `scripts/`):

- `install_writer.ps1`
- `install_fonts.ps1`
- `build_nuitka.ps1` — standalone Windows (`dist/LoreEditor-<ver>-win64.zip`)

`ROOT` w skryptach to katalog repo (`scripts/dev/../..`), nie `scripts/`.

Uruchamianie z korzenia repo, np.:

```powershell
python scripts/dev/test_crud.py
python scripts/dev/probe_dirty_read.py
python scripts/dev/probe_review_bugs.py
```

| Skrypt | Po co |
|--------|--------|
| `probe_dirty_read.py` | Odczyty / ROZWIŃ vs `world.dirty` |
| `probe_review_bugs.py` | Discard close, strict restore, auth remote |
| `test_crud.py` | Szybki CRUD poza unittest |
| `audit_*.py` | Inspekcja bubble_index / zapytań (projekt w cwd) |

Testy regresji (kanon):

```powershell
python -m unittest discover -s tests -q
```
