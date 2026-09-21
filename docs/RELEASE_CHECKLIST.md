# Checklista release — Lore Editor

Używaj przed oddaniem zipa / instalacji standalone pisarzowi.

## 1. Wersja (jedno źródło prawdy)

| Miejsce | Oczekiwane |
|---------|------------|
| `pyproject.toml` → `version` | np. `0.7.9` |
| `lore/__init__.py` → `__version__` | to samo |
| `lore-editor --version` | to samo |
| README / README_EN nagłówek | to samo |
| `docs/CHANGELOG.md` sekcja | to samo |
| ZIP | `dist/LoreEditor-<ver>-win64.zip` |

```powershell
python -c "from lore import __version__; print(__version__)"
python run_lore_editor.py --version
Select-String -Path pyproject.toml -Pattern 'version\s*='
```

## 2. Silnik

```powershell
python -c "import importlib.metadata as m; print(m.version('cynober-db'))"
```

Wymagane: **cynober-db ≥ 8.2.5** (nie 8.2.4 z PyPI).

## 3. Testy

```powershell
python -m unittest discover -s tests -v
python scripts\dev\smoke_gui_825.py
```

Oba muszą zakończyć się sukcesem.

## 4. Build standalone

```powershell
.\scripts\build_nuitka.ps1
# po buildzie (dla 0.7.9):
.\scripts\dev\verify_standalone_079.ps1
```

Sprawdź:

- [ ] `dist\run_lore_editor.dist\run_lore_editor.exe` istnieje
- [ ] `dist\LoreEditor-<ver>-win64.zip` istnieje (wersja = pyproject)
- [ ] Stare ZIP/EXE trafiają do `dist/archive/` (skrypt robi to automatycznie)
- [ ] `lore\data\sjp\` i `lore\locales\` są w `.dist` (dane + EN UI)
- [ ] `ProductVersion` PE = `<ver>.0` (verify script)

## 5. Instalacja u pisarza (opcjonalnie na tej maszynie)

```powershell
.\scripts\install_standalone.ps1
```

- [ ] `%LOCALAPPDATA%\LoreEditor\run_lore_editor.exe`
- [ ] skrót pulpitu / Menu Start
- [ ] domyślna powieść: `%USERPROFILE%\dokumenty\lore`

## 6. Smoke ręczny (exe, ~2 min)

1. Uruchom skrót lub `run_lore_editor.exe --version` (jeśli konsola wyłączona — Pomoc → O programie / F1).
2. Nowy rozdział → wpisz tekst → Ctrl+S → powstaje `.kafd` + plik tekstowy w katalogu projektu.
3. Panel: **+ Postać** → zapisz → zamknij → otwórz ponownie → postać jest.
4. F7 (pisownia) — SJP ładuje się (brak komunikatu „brak słownika” gdy pliki SJP są w paczce).
5. Media → dodaj małe JPG do postaci → lista / podgląd.
6. Język → English → etykiety EN (część po restarcie OK).

## 7. Po release

- [ ] Wpis w `docs/CHANGELOG.md` (build / zip)
- [ ] Usuń lub oznacz stare `LoreEditor-*-win64.zip` w `dist/`, żeby nie pomylić pisarza
- [ ] Commit: wersja + changelog + artefakt tylko jeśli repo trzyma zip (domyślnie `dist/` w `.gitignore`)
