# Game Studio — kanon kierunku

**[English → §13](#13-english-summary)**

**Status:** kierunek (nie zaimplementowany) · **v0.2** · 2026-08-14  
**Edytor:** [Lore Editor](../README.md) 0.7.8+ (domyślnie tryb pisarz)  
**Silnik:** [KarmazynOs](https://github.com/Maciej-EriAmo/KarmazynOs) + **substrat** (atomy, bąble, `T`, tick, reach-GC, `.kafd`)  
**Projekcja:** Mrowisko / SDL — luneta na Store, nie drugi silnik  
**Sąsiad:** [Adventure Studio](ADVENTURE_STUDIO_PLAN.md) — Quest = wątek MG; w playerze quest = hook po eksporcie

Zasada: **spiąć to, co jest; dołożyć tylko brak.** Przycisk = działająca ścieżka.

---

## 1. Produkt

> Silnik **już jest** (KarmazynOs + substrat). Lore-editor jest autorem kanonu. Mrowisko jest lunetą.  
> Dla ludzi: **generator gry z opisu własnego świata** — „co opiszesz i zaakceptujesz, to grasz”.  
> Bez cudzych marek, bez pakietów IP, bez prawników.

```
[ Lore Editor ]     Pisarz / switch Edycja gry
        │  ten sam .kafd
        ▼
[ lore-game ]       projekcja: Play, ujęcie, później sekwencer
        │           kod: C:\Users\drwis\lore-game
        ▼
[ KarmazynOs + Store ]   ← SILNIK
        ├── IO SDL / pygame (widok, input, dirty/hot)
        ├── ujęcie / replay     (§6)
        └── później sekwencer   (ten sam Store)
```

Dołożyć wolno: czasowniki projekcji (`idź` → `mów` → `walcz`) i cechy w `.kafd`.  
Nie wolno: Unity, drugi VM, silnik z promptu.

**Nazwy:** Game Studio = linia. **Edycja gry** = switch w lore-editorze. **Mrowisko** = demo + poligon. **lore-game** = repo projekcji (gra + film).  
Nie trzecie okno „Studio” (zajęte: Karmazyn Studio, Cynober Studio).

---

## 2. Co już jest

| Element | Gdzie | Rola |
|---------|--------|------|
| Postać, Miejsce, Scena, relacje | lore 0.7.8 | NPC, komora, beat |
| Media KAFS / `A_STREAM` | cynober-db ≥ 8.2.5 | sprite, dźwięk, tło |
| Dirty/hot paint | Luneta / płótno atomów | kontrakt malowania |
| Lore Pack `.kafd` | `lore/cynober_patch.py` | kanon poziomu = kanon powieści |
| Mapa grafu | `graph_view.py` | graf komór |
| Stany temporalne | `Stany` | wariant / flaga |
| `karmazyn_lua` 1.1.2 | KarmazynOs | gość — nie silnik questów sam z siebie |
| SDL / `project_hot` | `karmazyn_studio` | IO; nie mylić z Game Studio |
| Thermal Invaders | `KarmazynOs/archiwum/` | precedens: atom = obiekt gry |

README lore-editor: pisarz, bez Lua, bez silnika gry — to **zostaje default**. Switch odsłania resztę.

---

## 3. Switch „Edycja gry”

Wyłączony domyślnie. Nie otwiera nowego programu.

| W UI | Kiedy |
|------|--------|
| Komora = Miejsce + `prowadzi_do` + pozycja | G1 — zapis w `.kafd` |
| Aktor = Postać + `sprite` + `(x,y)` | G1 + media 0.7.8 |
| Graf komór | mapa + filtr |
| **Uruchom demo** | G2 — woła `lore-game play` na tym samym `.kafd` |
| Quest / kroki | po Adventure P1–P2 |
| Lua `on_enter` | gdy G2 **naprawdę** woła hook |
| Film / sekwencer | nie w pierwszym switchu |

Zakaz kafelków „Lua / tilemap / Unreal” zanim ścieżka zapisuje i odtwarza.

---

## 4. Model (atomy i bąble)

Store = tożsamość, `T`, wiązania. Nie siatka pikseli, nie cały tilemap w Store.

| W `.kafd` | Projekcja |
|-----------|-----------|
| komora = bąbel (Miejsce) | ściany **tej** komory |
| aktor = atom (Postać) | sprite, interpolacja |
| `prowadzi_do` | drzwi |
| `(x,y)` | ruch |
| `T` | próg ticka i paint |

**Quest:** w Adventure = Cel / Stawka / Status (MG). W playerze = trigger po **eksporcie**. Lua nie parsuje KarminQL w 60 Hz.

---

## 5. Poligon: Mrowisko

Cel: udowodnić narzędzia, nie wydać gry.

1. Dwie komory, `prowadzi_do`.  
2. Jedna sterowana mrówka, 2–3 NPC **do minięcia** (celowo bez interakcji).  
3. Ściany zatrzymują; NPC = dekoracja.  
4. Widok z góry — SDL/pygame jako IO w KarmazynOs, nie silnik w lore-editorze.  
5. Play żyje w **lore-game** i czyta ten sam `.kafd` (0.1: headless).  
6. Ujęcie = §6.

Gdy to działa — narzędzie istnieje. Reszta gier siada na: encja, relacja, media, eksport, luneta.

---

## 6. Format ujęcia

Nie zamiennik MP4. Zapis **nielicznych obiektów**: `id · x · y · (z) · T · t`.  
50 aktorów × 30 Hz × 60 s ≈ MB, nie setki MB wideo.

Bąbel ujęcia wiąże aktorów i komorę. Ścieżki = rzadkie próbki + interpolacja. Klucz = snapshot bąbla. Ciężkie media = osobny `A_STREAM`.

**Dysk i CPU:** rzadkie próbki / tylko dirty-hot. Ekran i tak dostaje vsync. Przy wszystkim gorącym koszt = pełna klatka — próg `T` obowiązkowy.

**GPU:** jak silnik gry (instancing, dirty rect), nie jak ffmpeg. Kodeki już robią makrobloki + dekoder na karcie — nie piszemy drugiego H.264. Sprzętowy dekoder tylko dla `A_STREAM`.

Fotoreal z samych `(punkt, T)` nie wraca. Kino i stan mogą żyć w jednym bąblu, nie w jednym magicznym pliku.

**Film 3D:** ten sam kanon, inny odtwarzacz (sekwencer). Nie w pierwszym switchu.

---

## 7. Rynek, fani, hasło

Są wiki (World Anvil), VTT, silniki, Twine. „Napisz i Graj” zwykle gubi id albo idzie w chmurę.

Nisza: **notatki → spacer → ujęcie** w jednym `.kafd`, silnik = substrat. Most z zeszytu do spaceru, nie lepszy Roblox.

Roblox wygrywa platformą (fizyka, UGC, gracze). My — jednym Store na prozę / play / replay, offline, `T` w kanonie.

**Hasło:** generator dla fanów **własnego** lore. Co opiszesz (i zaakceptujesz), to masz — w granicach czasowników.

| Opiszesz | Masz |
|----------|------|
| komory, kto, kto kogo mija | spacer |
| + czasownik `mów` / `walcz` | twardsza gra, ten sam `.kafd` |
| „zrób Dawn of War / W40k” | nie na pudełku |

Cudze IP: prywatny plik użytkownika — jego sprawa. My nie hostujemy, nie brandingujemy, nie sprzedajemy packów. Draft AI → Store tylko po OK (Adventure P5).

---

## 8. Świat na żądanie (nie silnik na żądanie)

```
opis → draft LLM → akceptacja → .kafd → ta sama projekcja
```

AI wypełnia typy, które Store już rozumie (komory, aktorzy, kroki). Nie stawia silnika. Dynamika = nowe czasowniki na substracie.

Bez zamkniętej listy czasowników „generator” to kod, który udaje grę.

---

## 9. Kolejność (G0–G7)

| # | Co | Kryterium |
|---|-----|-----------|
| **G0** | Ten dokument + repo [lore-game](../../lore-game/docs/CANON.md) | README wskazuje kierunek, nie feature |
| **G1** | Switch + `prowadzi_do`, pozycja, sprite w `.kafd` | test store / `lore_bind` |
| **G2** | Mrowisko: 2 komory, 1 gracz, NPC pass-through | `lore-game play` z projektu |
| **G3** | Ujęcie §6 | replay; da się wznowić |
| **G4** | Adventure Quest w tym świecie | typ w panelu |
| **G5** | Lua `on_enter` gdy G2 woła | pusty hook też prawdziwy |
| **G6** | Eksport schematu (Adventure P7) | zero KarminQL w klatce |
| **G7** | Sekwencer | po codziennym Play |

G5 po G2. G7 po G3. Projekcja w KarmazynOs. Nie fork Holona.

---

## 10. To nie jest

- Roblox / Unreal / DaVinci / drugi H.264  
- trzecie puste Studio  
- Lua przy starcie pisarza  
- tilemap całego świata w Store  
- Quest edytora = quest silnika (bez eksportu)  
- film 3D w pierwszym switchu  
- silnik z promptu albo drugi silnik obok substratu  
- produkt / pack cudzego uniwersum  

---

## 11. Decyzje (2026-08-14)

1. Switch **autorski** w lore-editorze (pisarz zostaje default). Play / ujęcie / sekwencer = sibling **lore-game**, nie trzecie Studio i nie drugi silnik.  
2. Mrowisko = poligon, nie cel końcowy.  
3. Spiąć istniejące; dołożyć brak.  
4. Silnik = KarmazynOs + substrat; player = projekcja w lore-game.  
5. Ujęcie = rzadkie `(t,x,y,T)`; paint = dirty/hot.  
6. GPU jak gra, nie jak kodek.  
7. Completeness = jeden kanon na wiele dzieł.  
8. Świat na żądanie, nie silnik na żądanie.  
9. Produkt = generator z opisu **własnego** lore; zero packów IP.

---

## 12. Pliki

- [ADVENTURE_STUDIO_PLAN.md](ADVENTURE_STUDIO_PLAN.md)  
- [KIERUNEK_MULTIMEDIA_STREAMING.md](KIERUNEK_MULTIMEDIA_STREAMING.md)  
- [CHANGELOG.md](CHANGELOG.md)  
- Projekcja: `C:\Users\drwis\lore-game` (`docs/CANON.md`)  
- KarmazynOs: `Documents/studio_sdl.md`, `LUA/README.md`

---

## 13. English summary

**Engine = KarmazynOs + substrate.** Lore Editor authors the world (writer default; Game-edit switch). Play / shot live in sibling repo `lore-game` — not a third Studio. Anthill is the proving ground (0.1 headless; SDL is IO). Product: **describe your own lore, accept the draft, play it** — no franchise packs. Shots are sparse `(t,x,y,T)`; paint dirty/hot; GPU like a game, not a second H.264. On-demand **world**, not on-demand engine. Verbs grow (`walk` → `talk` → `fight`) on the same store. Offline `.kafd` is the niche vs lore-wikis and vs Roblox.
