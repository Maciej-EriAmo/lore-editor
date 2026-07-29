# Kierunek rozwoju: multimedia, strumienie i rozszerzenie bazy

**[English → MULTIMEDIA_STREAMING_ROADMAP.md](MULTIMEDIA_STREAMING_ROADMAP.md)**

**Status:** kierunek architektoniczny (nieimplementowany)  
**Kontekst:** rozmowa o warstwach ramki Cynober/Karmazyn, bąblach i docelowym strumieniowaniu  
**Metafora:** *YouTube na sterydach* — publikacja i odtwarzanie multimediów osadzonych w grafie lore, z termodynamiką atomów, seekiem KAFD i tunelem Karmazyn zamiast HTTP-CDN.

---

## Wizja

Multimedia (obraz, audio, wideo, binaria) nie są osobną „warstwą 7” ani osobną bazą SQL. Są **atomami w bąblach** — tak jak dziś postać, notatka czy relacja. Strumieniowanie to nie upload pliku na FTP, lecz **przepływ atomów KAFD** po istniejącym tunelu Cynober (TCP + HSS + HSL), z RPC jako **płaszczyzną sterowania**.

Docelowo:

- **YouTube-owe:** kanał = bąbel, klip = atom(y) z MIME i temperaturą, odtwarzacz seekuje i buforuje gorące fragmenty.
- **Na sterydach:** ten sam klip jest w **grafie lore** (powiązany z postacią, rozdziałem, epoką), ma **T / stan termiczny**, deduplikację CAS, sync zespołu przez Cynober — nie izolowany blob w S3.

---

## Co już jest (fundament)

| Element | Gdzie | Rola |
|---------|-------|------|
| **Bąbel** | `karmazyn_substrate.Bubble` | Scope + `bindings: nazwa → atom_id` |
| **Atom z binariami** | `atom.metadata["data"]` | Payload obrazu/audio/wideo |
| **KAFD v2** | `karmazyn_kafd.py` | Jeden format: MIME, `ATYPE`, `F_STREAMING`, seek + stream |
| **KAFD_FLOW (KAFS)** | `karmazyn_kafd.KAFDFlowWriter/Reader` | Ramki strumienia atomów po socket/pipe |
| **Lore Pack** | `lore/cynober_patch.py` | Bąble jako `__bubble__` w `.kafd` |
| **Tunel RPC** | `cynober_client` + `cynober-server` | KarminQL w JSON, ramka `[4B len][encrypted]` |
| **HSL prismy** | `karmazyn_hsl` | Capability tokens — dziś `karminql:query`, miejsce na rozszerzenia |
| **Gossip** | `cynober_gossip.py` | Sync phi-space; BubbleVFS (`.soul`) — **przyszłość** |

**Luka:** tunel RPC nie przenosi jeszcze KAFS; multimedia w Lore Editorze = pliki lokalne lub przyszłe atomy w `.kafd`, nie strumień sieciowy.

---

## Dwa protokoły ramek (control vs data)

### Płaszczyzna sterowania — Cynober RPC (dziś)

```
TCP → [4B len][encrypted] → zlib → JSON {"query": "…", "cap": "…"} → KarminQL
```

Małe payloady: metadane, indeks, bind/unbind, seek offset, lista bąbli, zapytania semantyczne.

### Płaszczyzna danych — KAFS (docelowo)

```
TCP → (ta sama koperta Karmazyn) → decrypted → KAFS:
  [KAFS magic][FT_ATOM][ID][MIME][T][ATYPE][DATA][CRC] … [FT_END]
```

Duże payloady: portret JPEG, ścieżka WAV, segment wideo; sortowanie **malejąco po T** (gorące pierwsze).

### Wspólna koperta transportowa

Surowy TCP zostaje cienki. **Karmazyn frame** (`_send_frame` / `_recv_frame`) — wspólna koperta dla obu typów payloadu. Semantyka siedzi wysoko; multimedia nie wymagają HTTP ani osobnego portu.

---

## Docelowy stos (od dołu)

```
1. Ethernet / Wi-Fi
2. IP
3. TCP
4. Ramka Karmazyn          [4B big-endian len][payload]
5. Szyfrowanie + HSL AAD   (cap zależny od typu: rpc:query | media:stream)
6. Multiplikser typu       (1 B lub magic: RPC_JSON | KAFS | …)
7a. RPC: zlib → JSON → KarminQL     (kontrola)
7b. KAFS: FT_ATOM → atom+MIME+data  (multimedia)
8. Semantyka: bąbel → bindings → atomy w grafie Cynober
```

---

## Multiplex w tunelu (propozycja implementacji)

Po ustanowieniu HSL, każda ramka Karmazyn w fazie danych:

| Pole | Opis |
|------|------|
| `frame_kind` | `0x01` = RPC JSON, `0x02` = KAFS chunk, `0x03` = gossip phi (opcjonalnie) |
| reszta | jak dziś: compress (RPC) / raw KAFS body → encrypt → length prefix |

Negocjacja w **caps handshake**:

```json
{
  "version": "Cynober-Secure-1.2",
  "hsl": "HSL-1.1",
  "prisms": ["karminql", "kafs-stream"],
  "crypto": ["hss", "ecdh", "simple"]
}
```

Nowe capability HSL: `media:stream` (analogicznie do `rpc:query`).

---

## Model danych: bąbel jako „kanał”

Przykład bąbla `postać.Anna`:

| Binding | Atom | MIME | ATYPE |
|---------|------|------|-------|
| `portret` | `a42` | `image/png` | `A_RAW` |
| `głos` | `a43` | `audio/ogg` | `A_RAW` lub `A_STREAM` |
| `wideo` | `a44` | `video/mp4` | `A_STREAM` (głowica + segmenty) |
| `bio` | `a45` | `text/plain` | tekst w `v` |

Operacje RPC (sterowanie):

- `POKAŻ bąbel "postać.Anna"`
- `SEEK atom a44 OFFSET 1048576` (gdy API dojdzie)
- `PODŁĄCZ a42 DO "rozdział_03"`

Operacje KAFS (dane):

- strumień atomów bąbla do klienta; konsument przerywa gdy `T < próg`
- odtwarzacz (`kafd_tool` → mpv/ffplay) dostaje natywny format bez konwersji do HTTP

---

## Lore Editor — rola w roadmapie

| Faza | Zachowanie |
|------|------------|
| **Dziś** | Rozdziały lokalnie; `--rpc` = tylko graf tekstowy; `.kafd` = Lore Pack |
| **Faza 1** | Atomy multimedialne w `.kafd` (portret postaci, referencje w panelu Lore) |
| **Faza 2** | Podgląd lokalny przez KAFD stream / `kafd_tool` |
| **Faza 3** | `--rpc` + KAFS: strumień z cynober-server (zespołowe „kino lore”) |
| **Faza 4** | Sync BubbleVFS przez gossip/replicate — spójność bąbli między węzłami |

Edytor pozostaje **offline-first**; sieć i strumienie są opcjonalne, jak dziś `--rpc`.

---

## YouTube na sterydach — co to znaczy operacyjnie

| YouTube (uproszczone) | Cynober + KAFS |
|----------------------|----------------|
| Kanał | Bąbel (scope + bindings) |
| Wideo | Atom(y) `A_RAW` / `A_STREAM` z MIME |
| CDN / HTTP range | KAFS seek + gorące atomy pierwsze (T-ordering) |
| Metadane / API | KarminQL-RPC |
| Subskrypcja / auth | HSL capability + PSK / HSS |
| Rekomendacje | Graf lore + zapytania semantyczne + termodynamika |
| Komentarze | Atomy powiązane relacjami w tym samym świecie |

Różnica: multimedia **nie żyją obok** lore — są **częścią tego samego świata Cynober**, z historią, kontekstem czasowym i sync zespołu.

---

## Zależności i kolejność prac

1. **cynober-db:** multiplex `frame_kind` w `cynober_rpc` + obsługa w `cynober_server.handle_client`
2. **cynober-db:** prism `kafs-stream` w HSL + testy integracyjne KAFS przez tunel
3. **cynober-db:** gossip / replicate dla BubbleVFS (`.soul`) — `bubbles_synced: true`
4. **lore-editor:** API w `LoreStore` — dołączanie mediów do encji (atom w bąblu)
5. **lore-editor:** podgląd w panelu (lokalny KAFD, potem strumień RPC)
6. **Dokumentacja:** rozszerzyć pomoc F1 i README (sekcja „To nie jest” — KAFS ≠ HTTP streaming)

---

## Czego nie robić

- Nie budować osobnego serwera HTTP dla mediów na porcie 8080
- Nie traktować FTP/SFTP/rsync jako protokołu aplikacji (backup plików OK)
- Nie pakować dużych binariów do JSON-RPC bez KAFS (limit ramki, zlib overhead)
- Nie duplikować modelu SQL — multimedia = atomy Karmazyn w bąblach

---

## Powiązane pliki w ekosystemie

| Pakiet / plik | Temat |
|---------------|-------|
| `karmazyn_kafd.py` | KAFD v2, KAFS, MIME, streaming |
| `karmazyn_substrate.py` | Bąble, bindings |
| `karmazyn_hsl.py` | Capability, prismy, AAD |
| `cynober_rpc.py` | Handshake, RPC, encrypt |
| `cynober_gossip.py` | Sync phi; BubbleVFS TODO |
| `lore/cynober_patch.py` | Lore Pack, `__bubble__` |
| `README.md` | Komunikacja i sieć (Karmazyn, nie HTTP) |

---

*Ostatnia aktualizacja kierunku: 2026-07-10*