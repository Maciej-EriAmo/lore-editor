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
lore-editor                          # z katalogu projektu
lore-editor --file rozdzial_01.txt
lore-editor --astraedit              # z AstraEdit (osobna instalacja)
lore-editor --rpc --host 192.168.1.10 # lore na serwerze
```

Panel ma zakładki: **Rozdział** · **Szukaj** · **Zespół** (sync plików).

## Pakiet exe (Nuitka)

```powershell
.\scripts\build_nuitka.ps1
# wynik: dist\run_lore_editor.exe
```

Skopiuj exe do folderu projektu lub uruchamiaj z katalogu z `.lore-project`.  
**Uwaga:** pierwszy build Nuitka trwa długo (~5–15 min); exe ma ~30–80 MB (Cynober w środku).  
Tryb `--astraedit` nie jest w exe — wymaga osobnego Pythona / AstraEdit.

## Testy

```bash
python -m unittest discover -s tests -v
```

## Licencja

MIT