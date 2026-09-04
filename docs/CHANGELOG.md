# Changelog — Lore Editor

Format: skrót dla deweloperów i pisarzy. Szczegóły w README / F1.

## 0.7.9

### Silnik
- Wymaganie **cynober-db ≥ 8.2.5** (hotfix `cynober_paths` w wheel; 8.2.4 z PyPI psuło `cynober_worlds` / lokalny lore).
- Docs/pomoc: bump z 8.2.2 → 8.2.5 (HSL1, auth scrypt, KAFS jak wcześniej).

## 0.7.8

### Kierunek (docs)
- [GAME_STUDIO.md](GAME_STUDIO.md) v0.2 — generator z opisu własnego lore; silnik = KarmazynOs + substrat.
- Projekcja Play / ujęcie: sibling repo `lore-game` (nie trzecie Studio).

### Porządek (uczciwość)
- RPC `lista_mediow`: błąd tunelu/serwera nie udaje pustej listy.
- `_resolve_media_atom_id` nie zmyśla `m_{encja}_{rola}` gdy listy nie ma.
- `session_info` legacy nie zgłasza `connected: True` bez gniazda.
- `_run_line`: `status=error` zawsze wyjątek (nie „brak wyników”).
- Historia: zepsuty/brakujący manifest odtwarzany z `snapshots/`.
- Odczyt: brak pliku to OSError, nie „plik binarny”.
- Zmiana katalogu: błąd przywrócenia poprzedniego projektu nie jest połykany.
- Zapis karty: `end-1c` zamiast `tk.END` (nie dopisuje dodatkowego `\\n` przy każdym Ctrl+S).
- `write_text`: `errors=strict` — nie zamienia cicho znaków na `?`.
- Uszkodzony JSON (sesja, locale, typografia, słownik pisowni): kwarantanna `*.bak`, nie nadpisanie.
- `parse_stany`: zły JSON to wyjątek, nie puste stany.
- Mapa lore: błąd otwarcia rozdziału nie udaje pustego grafu.
- Historia strict: nieudane usunięcie sieroty to błąd, nie „pełny restore”.
- `read_kafd_vfs_meta`: `store_stats.error` to wyjątek, nie pusta meta.
- `world_meta_from_disk`: zepsuty sidecar → `*.bak`; bez fallbacku błąd .kafd nie jest ukrywany.
- `sync_atom_id_counter`: jak API i fallback padną — wyjątek, nie cichy licznik.
- AstraEdit: zapis anulowany/nieudany nie flushuje lore; błąd lore po zapisie jest widoczny; menu Lore nie znika po cichu.
- Loader AstraEdit: „Brak AstraEdit” zawiera przyczyny nieudanego importu.
- Lista przy rozdziale: zepsuty podgląd = typ „błąd” + komunikat, nie „?”.
- Po restore: nieczytelna karta to ostrzeżenie, nie pominięcie.
- Pomoc F1: przy locale EN nie spada na PL tytuł (crash `index`).
- `help_topics`: tylko `ImportError` na i18n — inne błędy nie są chowane.
- Paczka locale z pustym/zepsutym `ui.json` nie rejestruje się jako język.
- Entry-point locale: `warnings.warn`, nie ciche `continue`.
- Jawny profil RPC (`--profile`) + błąd configu = wyjątek, nie puste creds.
- `scripts/dev`: `ROOT` to repo, nie `scripts/` (audyt nie udaje braku `.kafd`).
- SJP: pliki są, a hunspell nie wstał → „SJP.PL nie wczytany”, nie „brak słownika”.

### Media — menu i panel
- **Menu „Media”** na belce: dodaj zdjęcie / muzykę / film / dowolny plik, podgląd, lista, eksport.
- Duplikaty w **Lore** + skróty: `Ctrl+Shift+I` (obraz), `Ctrl+Shift+U` (audio), `Ctrl+Shift+M` (wideo).
- Panel Lore: ramka **Media** z przyciskami +Zdjęcie / +Dźwięk / +Film.
- F1: temat **Media (zdjęcia, dźwięk, film)** · pełny **EN** (`locales/en/help.json` + ui).
- README / README_EN zaktualizowane.

### Media — naprawy backendu
- **Nuitka / wheel:** `karmazyn_media*` + `cynober_media_rpc` + PIL w buildzie; `pyproject` cynober-db eksportuje preview/canvas.
- **Lazy load:** atomy `media` / `media_seg` nie są zwijane; T mediów ≥ T_HOT.
- **Restore bąbli:** bindings z `metadata.v.bindings` (nie tylko top-level).
- **GUI:** filetypes z spacjami (Windows Tk); dirty rejestru po `dodaj_media`.
- **Weryfikacja:** `tests/test_media_lore_store.py`, `scripts/dev/verify_media_pipeline.py` (`--rpc` opcjonalnie).

## 0.7.6

### Grafiki / media (teraz)
- **Lokalnie:** Dołącz plik → atom w bąblu postaci; lista + podgląd (płótno / player).
- **RPC:** `put_media` / `get_media` (KAFS); **`MEDIA LIST "encja"`** na serwerze → `lista_mediow` nie jest pusta.
- Auto-postaci przy dołączaniu; check `kafs_enabled` przed uploadem.

### Sieć (cynober-db 8.2+)
- **RPC** — czytelne błędy połączenia (HSS/HSL); ostrzeżenie bez **kafs-stream**.
- **RpcLoreBackend.client** + `session_info()`.
- Zależność: `cynober-db>=8.2.5` (od 0.7.9; wcześniej 8.2.2+).

## 0.7.5

### Naprawy i hardening
- **ROZWIŃ** — lokalny unfold przez `unfold_runtime` (wcześniej martwa składnia `ROZWIJ` w silniku); na RPC mapowane do `ROZWIJ` (cynober-server).
- **Historia** — pełne przywrócenie (`strict=True`): usuwa rozdziały `.txt`/`.md` spoza snapshota; `strict=False` = merge.
- **RPC / Zespół** — host poza 127.0.0.1 wymaga user+token (fail-fast); `LORE_RPC_ALLOW_ANON=1`, `LORE_RPC_REQUIRE_AUTH=1`.
- **Panel Zespół** — pola User/Token; ostrzeżenie przy syncu na zdalny host (zaufana sieć LAN).
- **Zapis** — partial (tekst OK, lore nie) → nie udaje pełnego sukcesu; autosave jak ręczny zapis.
- **Zamykanie** — dialog lore: tak / nie / anuluj.

### Docs i release
- README (PL/EN), F1 (sieć, historia), `docs/PLUGINY_*` / `LANGUAGE_PLUGINS`.
- Build: `scripts/build_nuitka.ps1` → `dist/LoreEditor-0.7.5-win64.zip` (+ exe).

### Testy
- 104 unittestów (ROZWIŃ, strict/merge restore, auth remote/loopback).

## 0.7.4

- Locale packs PL / EN / plugin `tlh`
- RPC login (`--rpc-user` / `LORE_RPC_*`)
- Safe close bez fałszywego flush
- Dirty-on-read naprawy; izolacja projektów
- Autosave: raport błędów

## 0.7.3 i wcześniej

- Panel lore, temporal, zapytania, historia, spellcheck SJP, standalone Nuitka, katalog pracy `dokumenty/lore`.
