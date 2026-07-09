# Lore Editor

Edytor lore dla **pisarzy** — postacie, pomysły, wpływy, koligacje — na silniku [Cynober DB](https://github.com/Maciej-EriAmo/DBase).

Narzędzie **pisarskie** (offline-first) — bez Lua, bez silnika gry.

## Instalacja

```bash
pip install cynober-db>=8.0.1
pip install -e .
```

Windows:

```powershell
.\scripts\install_writer.ps1 -Project MojaPowiesc
```

## Projekt — zero konfiguracji

**Opcja A:** uruchom z folderu powieści — cwd = projekt:

```powershell
cd ~/Documents/MojaPowiesc
lore-editor
```

Nazwa projektu = nazwa folderu (np. `MojaPowiesc`).

**Opcja B:** plik `.lore-project` w katalogu:

```
name=MojaPowiesc
```

Edytor szuka pliku w cwd i katalogach nadrzędnych.

**Opcja C:** jawnie:

```bash
lore-editor --project-dir ~/Documents/MojaPowiesc
```

Przy pierwszym uruchomieniu tworzy się `.lore-project` i pliki `.kafd`.

## Layout folderu

```
MojaPowiesc/
  .lore-project
  rozdzial_01.txt
  rozdzial_02.md
  MojaPowiesc.kafd
  MojaPowiesc.meta.json
```

## Uruchomienie

```bash
lore-editor                              # z katalogu projektu
lore-editor --file rozdzial_01.txt       # jeden plik
lore-editor rozdzial_01.txt rozdzial_02.md   # kilka kart
lore-editor --rpc --host 192.168.1.10    # lore na serwerze
```

### Edytor wbudowany

- **Karty** — wiele plików naraz (`Ctrl+W` zamyka kartę)
- **Plik** — Nowy, Otwórz, Zapisz, Zapisz jako…
- **Edycja** — Cofnij/Ponów, Znajdź (`Ctrl+F`), przełącz zawijanie wierszy
- **Skróty** — `Ctrl+N` `Ctrl+O` `Ctrl+S` `Ctrl+Shift+S`
- **Status** — liczba słów i znaków, kodowanie pliku
- **Autosave** — co 60 s (tylko pliki już zapisane na dysku)
- **Panel lore** — zakładki Rozdział · Szukaj · Zespół

## Pakiet exe (Nuitka)

```powershell
.\scripts\build_nuitka.ps1
# wynik: dist\run_lore_editor.exe
```

Skopiuj exe do folderu projektu lub uruchamiaj z katalogu z `.lore-project`.  
**Uwaga:** pierwszy build Nuitka trwa długo (~5–15 min); exe ma ~30–80 MB (Cynober w środku).

## Testy

```bash
python -m unittest discover -s tests -v
```

## Licencja

MIT