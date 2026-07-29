# Roadmap: multimedia, streams, and database extension

**[Polski → KIERUNEK_MULTIMEDIA_STREAMING.md](KIERUNEK_MULTIMEDIA_STREAMING.md)**

**Status:** architectural direction (not fully implemented)  
**Context:** Cynober/Karmazyn frame layers, bubbles, target streaming  
**Metaphor:** *YouTube on steroids* — media embedded in the lore graph, with atom thermodynamics, KAFD seek, and a Karmazyn tunnel instead of an HTTP CDN.

---

## Vision

Images, audio, video, and binaries are **not** a separate “layer 7” or a SQL sidecar. They are **atoms inside bubbles** — like a character, note, or relation today. Streaming is not “upload to FTP”; it is a **flow of KAFD atoms** over the existing Cynober tunnel (TCP + HSS + HSL), with RPC as the **control plane**.

Target:

- **YouTube-like:** channel = bubble, clip = atom(s) with MIME and temperature; player seeks and buffers hot fragments.
- **On steroids:** the same clip sits in the **lore graph** (linked to character, chapter, era), has **T / thermal state**, CAS dedup, team sync via Cynober — not an isolated S3 blob.

---

## What already exists (foundation)

| Piece | Where | Role |
|-------|-------|------|
| **Bubble** | `karmazyn_substrate.Bubble` | Scope + `bindings: name → atom_id` |
| **Atom with binaries** | `atom.metadata["data"]` | Image/audio/video payload |
| **KAFD v2** | `karmazyn_kafd.py` | MIME, `ATYPE`, `F_STREAMING`, seek + stream |
| **KAFD_FLOW (KAFS)** | `KAFDFlowWriter/Reader` | Atom stream frames over socket/pipe |
| **Lore Pack** | `lore/cynober_patch.py` | Bubbles as `__bubble__` in `.kafd` |
| **RPC tunnel** | `cynober_client` + `cynober-server` | KarminQL in JSON, encrypted frames |
| **HSL prisms** | `karmazyn_hsl` | Capability tokens (`karminql:query` today) |
| **Gossip** | `cynober_gossip.py` | Phi-space sync; BubbleVFS (`.soul`) — **future** |

**Gap:** the RPC tunnel does not carry KAFS yet; Lore Editor media are local files or future atoms in `.kafd`, not a network stream.

---

## Two frame protocols (control vs data)

### Control plane — Cynober RPC (today)

```
TCP → [4B len][encrypted] → zlib → JSON {"query": "…", "cap": "…"} → KarminQL
```

Small payloads: metadata, index, bind/unbind, seek offset, bubble list, semantic queries.

### Data plane — KAFS (target)

```
TCP → (same Karmazyn envelope) → decrypt → KAFS:
  [KAFS magic][FT_ATOM][ID][MIME][T][ATYPE][DATA][CRC] … [FT_END]
```

Large payloads: JPEG portrait, WAV, video segments; sort **by descending T** (hot first).

### Shared transport envelope

Raw TCP stays thin. **Karmazyn framing** (`_send_frame` / `_recv_frame`) is the common envelope. Semantics stay high-level; media do not need HTTP or a second port.

---

## Target stack (bottom-up)

```
1. Ethernet / Wi-Fi
2. IP
3. TCP
4. Karmazyn frame          [4B BE len][payload]
5. Crypto + HSL AAD        (cap: rpc:query | media:stream)
6. Type multiplexer        (RPC_JSON | KAFS | …)
7a. RPC: zlib → JSON → KarminQL     (control)
7b. KAFS: FT_ATOM → atom+MIME+data  (media)
8. Semantics: bubble → bindings → Cynober atoms
```

---

## Tunnel multiplex (implementation sketch)

After HSL, each Karmazyn data-phase frame:

| Field | Meaning |
|-------|---------|
| `frame_kind` | `0x01` RPC JSON, `0x02` KAFS chunk, `0x03` gossip (optional) |
| rest | as today: compress (RPC) / raw KAFS → encrypt → length prefix |

Negotiate in handshake **caps**, e.g. prisms `["karminql", "kafs-stream"]`.  
New HSL capability: `media:stream` (parallel to `rpc:query`).

---

## Data model: bubble as “channel”

Example bubble `character.Anna`:

| Binding | Atom | MIME | ATYPE |
|---------|------|------|-------|
| `portrait` | `a42` | `image/png` | `A_RAW` |
| `voice` | `a43` | `audio/ogg` | `A_RAW` / `A_STREAM` |
| `video` | `a44` | `video/mp4` | `A_STREAM` |
| `bio` | `a45` | `text/plain` | text in `v` |

RPC (control): show bubble, seek atom, bind to chapter.  
KAFS (data): stream bubble atoms; consumer stops when `T` drops below a threshold.

---

## Lore Editor roadmap role

| Phase | Behaviour |
|-------|-----------|
| **Today** | Local chapters; `--rpc` = text graph only; `.kafd` = Lore Pack |
| **Phase 1** | Media atoms in `.kafd` (character portraits in the panel) |
| **Phase 2** | Local preview via KAFD stream / `kafd_tool` |
| **Phase 3** | `--rpc` + KAFS from cynober-server (team “lore cinema”) |
| **Phase 4** | BubbleVFS sync via gossip/replicate |

The editor stays **offline-first**; network and streams remain optional, like today’s `--rpc`.

---

## “YouTube on steroids” (operational mapping)

| YouTube (simplified) | Cynober + KAFS |
|----------------------|----------------|
| Channel | Bubble (scope + bindings) |
| Video | Atom(s) `A_RAW` / `A_STREAM` + MIME |
| CDN / HTTP range | KAFS seek + hot-first T ordering |
| Metadata / API | KarminQL-RPC |
| Auth | HSL capability + PSK / HSS |
| Recommendations | Lore graph + semantic queries + thermodynamics |

Difference: media do **not** live beside lore — they are **part of the same Cynober world**.

---

## Work order

1. **cynober-db:** `frame_kind` multiplex in RPC + server `handle_client`
2. **cynober-db:** HSL prism `kafs-stream` + integration tests
3. **cynober-db:** gossip/replicate for BubbleVFS (`.soul`)
4. **lore-editor:** `LoreStore` API to attach media to entities
5. **lore-editor:** panel preview (local KAFD, then RPC stream)
6. **Docs:** F1 help + README “this is not HTTP streaming”

---

## What not to do

- Do not build a separate HTTP media server on 8080  
- Do not treat FTP/SFTP/rsync as the *app* protocol (file backup is fine)  
- Do not stuff large binaries into JSON-RPC without KAFS  
- Do not reintroduce a SQL media model — media = Karmazyn atoms in bubbles  

---

## Related files

| Path | Topic |
|------|-------|
| `karmazyn_kafd.py` | KAFD v2, KAFS, MIME, streaming |
| `karmazyn_substrate.py` | Bubbles, bindings |
| `karmazyn_hsl.py` | Capabilities, prisms |
| `cynober_rpc.py` | Handshake, RPC, encrypt |
| `cynober_gossip.py` | Phi sync; BubbleVFS TODO |
| `lore/cynober_patch.py` | Lore Pack, `__bubble__` |
| `README_EN.md` | Networking (Karmazyn, not HTTP) |

---

*Roadmap last updated: 2026-07-10 · English translation for Lore Editor 0.7.4+*
