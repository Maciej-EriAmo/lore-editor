# Changelog — Lore Editor

Format: skrót dla deweloperów i pisarzy. Szczegóły w README / F1.

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
