# Adventure Studio — plan i pseudokod

**Produkt:** rozszerzenie [Lore Editor](../README.md) w stronę **reżyserii przygody**  
(MG, CRPG, przygodówki) — nie silnik gry, nie kolejny wiki.

**Wersja planu:** 0.1 · 2026-08  
**Baza:** lore-editor 0.7.x · Cynober / Karmazyn (`.kafd`) · offline-first  
**Zasada:** kanon w grafie; modele worldgen i MG dostają **eksporty**, nie odwrotnie.

---

## 1. Wizja (jednym zdaniem)

> Edytor trzyma **kanon świata** i produkuje dwa wyjścia:  
> **(A) prompt pack** dla modeli generujących światy / treść,  
> **(B) brief dla mistrza gry** — czytelny opis sesji / questa / lokacji.

Modele (lokalne `gemma3:4b` / większe worldgen) **nie są źródłem prawdy**.  
Wpis do kanonu tylko po **akceptacji** reżysera.

---

## 2. Role w systemie

| Rola | Odpowiedzialność |
|------|------------------|
| **Kanon (Cynober)** | Encje, relacje, status, temporal, media |
| **Studio (ten plan)** | Typy adventure, walidacja, eksporty A/B, opcjonalny LLM-draft |
| **Worldgen model** | Wypełnia luki wg prompt pack |
| **MG / reżyser** | Gra, decyzje, akceptacja draftów |
| **Silnik gry (później)** | Import schematu — poza MVP |

---

## 3. Model danych (fazy)

### Faza A — Narracja (MVP)

```
TypLore (istniejące)     + nowe:
  Postać, Miejsce,         Quest
  Scena, Pomysł, …         QuestStep   (opcjonalnie jako cechy + kolejność w Quest)
```

**Quest** (bąbel):

| Pole | Znaczenie |
|------|-----------|
| `Status` | `szkic` \| `gotowy` \| `w_toku` \| `domkniety` \| `porzucony` |
| `Cel` | co ma osiągnąć gracz / partia |
| `Stawka` | co się stanie przy porażce / sukcesie |
| `Notatka` / `Opis` | wolny tekst reżysera |
| `Kroki` | lista uporządkowana (JSON w polu *lub* osobne encje) |

**Relacje (reuse + ewentualnie nowe etykiety UI):**

| UI | Graf | Znaczenie |
|----|------|-----------|
| zawiera | `zawiera` | quest → kroki / podwątki |
| występuje w | `wystepuje_w` | postać / item w queście |
| nawiązuje do | `nawiazuje_do` | quest → scena / pomysł |
| koliguje z | `koliguje_z` | quest ↔ quest (side) |
| odblokowuje *(nowe)* | `odblokowuje` | krok/quest → quest/scena |
| dzieje się w *(nowe)* | `dzieje_sie_w` | quest/krok → miejsce |

### Faza B — Przestrzeń (po MVP)

- **Lokacja** — wyjścia, tagi, NPC na miejscu (relacje, nie tilemap)  
- **Miasto / Region** — zbiór lokacji (`zawiera`)  
- **Poziom** (abstrakcja) — graf pokoi / triggerów jako encje + relacje  

### Faza C — Mechanika (później)

- **Reguła / Cecha / Przedmiot** jako typy  
- Walidacja spójności („quest wymaga cechy X”)  
- Export do GameStore / JSON schema silnika  

**Poza zakresem planu 0.1:** edytor tilemap 2D/3D, combat sim, Lua runtime.

---

## 4. Dwa eksporty (rdzeń produktu)

### A — Prompt pack (dla modeli)

Cel: **kontrolowany** kontekst + zadanie + twarde reguły.

```
[ROLE]
[CANON]          ← skondensowany graf (nie cały dump)
[SCOPE]          ← co wolno zmieniać / czego nie
[TASK]           ← np. „dopisz 2 side-questy”
[FORMAT]         ← JSON / markdown zgodny ze schematem importu
[HARD_RULES]     ← living NPC, ton, język
```

### B — Brief MG (dla człowieka)

Cel: **stół / sesja**, zero JSON-a.

- One-pager questa  
- Karta lokacji / postaci (sekrety, hooki)  
- Clock / „co jeśli gracze nic nie zrobią”  
- 3 otwarcia sesji  

Format: Markdown (v1) → opcjonalnie DOCX (istniejący tor `export_docx`).

---

## 5. Plan wdrożenia (kolejność PR)

| # | Deliverable | Kryterium gotowości |
|---|-------------|---------------------|
| **P0** | Ten dokument + decyzja nazewnictwa UI (`Quest` vs `Wątek`) | merge docs |
| **P1** | `TypLore.QUEST` + pola + i18n PL/EN + panel (CRUD jak Postać) | testy store/panel |
| **P2** | Kroki questa (lista w polu `Kroki` JSON) + proste relacje do postaci/miejsc | unittest + ręczny smoke |
| **P3** | `lore/export_prompt.py` + `lore/export_gm.py` + menu **Eksport** | plik/schowek, golden string tests |
| **P4** | Szablony promptów (fill-gap, expand-quest, consistency) | 3 szablony, parametryzowane |
| **P5** | Opcjonalny LLM local (`LORE_LLM_*` / Ollama) — **draft only**, diff UI | nigdy auto-write do kanonu |
| **P6** | Lokacja (typ + wyjścia jako relacje) | po stabilnym P3–P4 |
| **P7** | Export schema JSON dla silnika / GameStore | kontrakt wersjonowany |

**Nie zaczynać P6–P7** zanim P3 nie jest w codziennym użyciu.

---

## 6. Architektura modułów (docelowa)

```
lore/
  types.py              # + QUEST, pola adventure
  store.py              # + quest helpers (cienkie)
  panel.py              # lista/filtr questów (lub podpanel)
  adventure/
    __init__.py
    models.py           # dataclass QuestView, Step, ExportOptions
    graph_query.py      # zbieranie podgrafu wokół questa / lokacji
    condense.py         # CANON: skrót z limitem tokenów
    export_prompt.py    # Prompt pack
    export_gm.py        # Brief MG
    templates/          # .md.j2 lub zwykłe format()
    llm_draft.py        # opcjonalnie: Ollama chat → DraftProposal
    accept_draft.py     # mapowanie DraftProposal → mutacje store (po OK)
```

Zależności:

- `adventure/*` woła tylko **LoreStore** (zero KarminQL w UI).  
- LLM za protokołem jak `ChatClient` (requests → Ollama); brak LLM = eksporty działają.

---

## 7. Pseudokod

### 7.1 Typy i widok questa

```pseudo
# lore/types.py (rozszerzenie)
enum TypLore:
    ...
    QUEST = "Quest"

QUEST_STATUS = {"szkic", "gotowy", "w_toku", "domkniety", "porzucony"}
POLE_CEL = "Cel"
POLE_STAWKA = "Stawka"
POLE_STATUS = "Status"
POLE_KROKI = "Kroki"   # JSON array w cesze bąbla

# lore/adventure/models.py
dataclass QuestStep:
    id: str
    order: int
    title: str
    body: str
    place: Optional[str]      # nazwa Miejsca
    npcs: list[str]
    unlocks: list[str]        # nazwy questów / scen

dataclass QuestView:
    name: str
    status: str
    goal: str
    stakes: str
    notes: str
    steps: list[QuestStep]
    linked_characters: list[str]
    linked_places: list[str]
    linked_scenes: list[str]
    related_quests: list[str]

function parse_steps(raw: str|list) -> list[QuestStep]:
    if raw is list: data = raw
    else: data = json_parse(raw or "[]")
    return sort_by(data, key=order) mapped to QuestStep

function serialize_steps(steps: list[QuestStep]) -> str:
    return json_dump([{...} for s in steps])
```

### 7.2 Złożenie widoku z LoreStore

```pseudo
# lore/adventure/graph_query.py
function load_quest(store: LoreStore, name: str) -> QuestView:
    data = store.get_entity(name)   # istniejące API: cechy + typ
    assert data.typ == "Quest"

    neighbors = store.relations_of(name)  # lista (rel, other_name, other_typ)
    chars  = [n for (rel, n, t) in neighbors if t == "Postać"]
    places = [n for (rel, n, t) in neighbors if t == "Miejsce"]
    scenes = [n for (rel, n, t) in neighbors if t == "Scena"]
    quests = [n for (rel, n, t) in neighbors if t == "Quest" and n != name]

    return QuestView(
        name=name,
        status=data.get(POLE_STATUS, "szkic"),
        goal=data.get(POLE_CEL, ""),
        stakes=data.get(POLE_STAWKA, ""),
        notes=data.get(POLE_NOTATKA, "") or data.get(POLE_OPIS, ""),
        steps=parse_steps(data.get(POLE_KROKI)),
        linked_characters=chars,
        linked_places=places,
        linked_scenes=scenes,
        related_quests=quests,
    )

function subgraph_for_export(store, focus: str, radius: int = 1) -> CanonSlice:
    """
    focus = nazwa questa / lokacji / 'sesja'
    radius: 0 = tylko focus; 1 = sąsiedzi; 2 = sąsiedzi sąsiadów (ostrożnie z tokenami)
    """
    nodes = {focus: store.get_entity(focus)}
    edges = []
    frontier = [focus]
    for _ in range(radius):
        next_f = []
        for n in frontier:
            for rel, other, typ in store.relations_of(n):
                edges.append((n, rel, other))
                if other not in nodes:
                    nodes[other] = store.get_entity(other)
                    next_f.append(other)
        frontier = next_f
    return CanonSlice(nodes=nodes, edges=edges, focus=focus)
```

*Uwaga implementacyjna:* jeśli `LoreStore` nie ma jeszcze `get_entity` / `relations_of` pod tymi nazwami — dodać cienkie wrappery nad istniejącym API panelu (bez KarminQL w `adventure/`).

### 7.3 Kondensacja kanonu (limit tokenów)

```pseudo
# lore/adventure/condense.py
function condense(slice: CanonSlice, max_chars: int = 6000) -> str:
    lines = ["# CANON", f"focus: {slice.focus}", ""]
    # 1) focus pełniej
    lines += format_entity(slice.nodes[slice.focus], detail="full")
    # 2) reszta skrót
    for name, ent in slice.nodes.items():
        if name == slice.focus: continue
        lines += format_entity(ent, detail="short")  # typ + 1 zdanie
    lines += ["", "# RELATIONS"]
    for a, rel, b in slice.edges:
        lines.append(f"- {a} --{rel}--> {b}")
    text = join(lines)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n…[truncated for token budget]"
    return text

function format_entity(ent, detail):
    if detail == "full":
        return [
            f"## {ent.name} [{ent.typ}]",
            f"status: {ent.get(Status)}",
            f"goal: {ent.get(Cel)}",
            ent.get(Opis) or ent.get(Notatka) or "",
            ...
        ]
    else:
        one = first_sentence(ent.get(Opis) or ent.get(Notatka) or "")
        return [f"- {ent.name} [{ent.typ}]: {one}"]
```

### 7.4 Eksport Prompt pack

```pseudo
# lore/adventure/export_prompt.py
enum PromptTask:
    FILL_GAP          # "brakuje lokacji w regionie X"
    EXPAND_QUEST      # "dopisz kroki / side-questy"
    CONSISTENCY_CHECK # "wskaż sprzeczności"
    SESSION_HOOKS     # "3 otwarcia sesji"
    CUSTOM            # wolny tekst task

dataclass PromptExportOptions:
    focus: str
    task: PromptTask
    task_detail: str = ""
    radius: int = 1
    language: str = "pl"
    tone: str = ""
    hard_rules: list[str] = default_rules()
    output_format: str = "json_v1"   # lub markdown
    max_canon_chars: int = 6000

DEFAULT_HARD_RULES = [
    "Nie zmieniaj faktów z bloku CANON.",
    "Nie zabijaj postaci bez flagi allowed_death.",
    "Nie wprowadzaj nowych frakcji top-level bez oznaczenia [PROPOSAL].",
    "Oznacz domysły jako [PROPOSAL], kanon jako już dane.",
]

function build_prompt_pack(store, opt: PromptExportOptions) -> str:
    slice = subgraph_for_export(store, opt.focus, opt.radius)
    canon = condense(slice, opt.max_canon_chars)
    task_text = render_task(opt.task, opt.task_detail, opt.focus)
    fmt = render_format_spec(opt.output_format)

    return f"""
[ROLE]
Jesteś asystentem reżyserii CRPG / sesji TTRPG. Generujesz propozycje treści.
Szanujesz kanon. Nie nadpisujesz faktów.

[CANON]
{canon}

[SCOPE]
Wolno dodawać tylko oznaczone [PROPOSAL].
Focus: {opt.focus}
Język odpowiedzi: {opt.language}
Ton: {opt.tone or "zgodny z kanonem"}

[TASK]
{task_text}

[FORMAT]
{fmt}

[HARD_RULES]
{bullet(opt.hard_rules)}
""".strip()

function export_prompt_to_clipboard_or_file(store, opt, path: Optional[Path]):
    text = build_prompt_pack(store, opt)
    if path: write(path, text)
    else: clipboard_set(text)
    return text
```

**Przykład FORMAT `json_v1` (expand quest):**

```pseudo
function render_format_spec("json_v1"):
    return """
Zwróć wyłącznie JSON:
{
  "proposals": [
    {
      "kind": "quest_step" | "side_quest" | "location" | "npc_note",
      "title": string,
      "body": string,
      "links": [{"rel": string, "target": string}],
      "risk": "low"|"med"|"high"
    }
  ],
  "warnings": [string]
}
"""
```

### 7.5 Eksport Brief MG

```pseudo
# lore/adventure/export_gm.py
dataclass GmBriefOptions:
    focus: str                 # quest lub "sesja"
    include_secrets: bool = True
    include_clocks: bool = True
    language: str = "pl"

function build_gm_brief(store, opt: GmBriefOptions) -> str:
    q = load_quest(store, opt.focus)   # lub multi-quest session pack
    lines = []
    lines += [f"# {q.name}", f"**Status:** {q.status}", ""]
    lines += ["## Cel", q.goal or "—", ""]
    lines += ["## Stawka", q.stakes or "—", ""]
    lines += ["## Przebieg (dla MG)"]
    for s in q.steps:
        lines.append(f"### {s.order}. {s.title}")
        lines.append(s.body)
        if s.place: lines.append(f"- Miejsce: {s.place}")
        if s.npcs:  lines.append(f"- NPC: {', '.join(s.npcs)}")
        lines.append("")
    lines += ["## Postacie", *bullet(q.linked_characters)]
    lines += ["## Miejsca", *bullet(q.linked_places)]
    lines += ["## Sceny", *bullet(q.linked_scenes)]
    if opt.include_secrets:
        lines += ["## Sekrety / notatki reżysera", q.notes or "—", ""]
    if opt.include_clocks:
        lines += [
            "## Clock (jeśli gracze nic nie robią)",
            auto_or_manual_clock(q),  # z notatki lub szablon
            "",
        ]
    lines += ["## 3 hooki na stół", *session_hooks_stub(q)]
    return join(lines)

function export_gm_markdown(store, opt, path: Path):
    write(path, build_gm_brief(store, opt))
```

### 7.6 LLM draft (opcjonalnie, po eksporcie)

```pseudo
# lore/adventure/llm_draft.py
protocol LlmClient:
    function complete(messages, temperature=0.4, max_tokens=1024) -> str

function draft_from_prompt_pack(client: LlmClient, pack: str) -> DraftProposal:
    raw = client.complete([
        {"role": "system", "content": "Zwracaj tylko JSON wg FORMAT w prompcie."},
        {"role": "user", "content": pack},
    ])
    data = json_parse_lenient(raw)   # toleruj ```json fences
    return DraftProposal(raw=raw, parsed=data, status="pending_review")

# lore/adventure/accept_draft.py
function apply_draft(store, draft: DraftProposal, *, dry_run: bool) -> list[Mutation]:
    mutations = []
    for p in draft.parsed.proposals:
        mut = proposal_to_mutation(p)  # create entity / add step / add rel
        mutations.append(mut)
    if dry_run:
        return mutations
    for m in mutations:
        apply_mutation(store, m)   # store.ensure_entity, store.set_field, store.link
    store.mark_dirty()
    return mutations

# UI flow
function ui_fill_gap_clicked():
    pack = build_prompt_pack(store, options_from_dialog())
    if user wants only copy:
        clipboard(pack); return
    if no llm configured:
        show("Skopiowano prompt — wklej do worldgen"); return
    draft = draft_from_prompt_pack(llm, pack)
    show_diff_dialog(draft)   # human OK / edit / reject
    if user_accepted:
        apply_draft(store, draft, dry_run=False)
```

### 7.7 UI (szkic)

```pseudo
# Menu: Eksport
#   → Prompt pack…     (dialog: focus, task, radius, copy/save)
#   → Brief MG…        (dialog: focus, secrets on/off, save .md)
#   → Uzupełnij lukę…  (P5: pack → LLM → diff)

# Panel Lore: filtr typu Quest
# Dialog Quest:
#   Status | Cel | Stawka | Notatka
#   Lista kroków [+ / ↑ ↓ / usuń]
#   Przyciski: "Połącz postać" "Połącz miejsce" (reuse relation UI)
```

### 7.8 Testy (minimum)

```pseudo
test_condense_respects_max_chars()
test_build_prompt_pack_contains_canon_and_task()
test_build_gm_brief_has_steps_order()
test_parse_steps_roundtrip()
test_apply_draft_dry_run_no_store_write()
test_apply_draft_accept_creates_links()  # mock store
```

---

## 8. Kontrakty / config

```text
# opcjonalnie env (P5)
LORE_LLM_BACKEND=ollama|off
LORE_LLM_MODEL=gemma3:4b
LORE_LLM_BASE_URL=          # puste = http://localhost:11434/v1
LORE_EXPORT_MAX_CANON_CHARS=6000
```

Wersjonowanie eksportu silnika (P7):

```text
adventure_export_schema: 1
```

---

## 9. Anty-cele (nie robimy w tym planie)

- Auto-zapis generacji do kanonu bez UI akceptacji  
- Tilemap / mesh / pathfinding  
- Zastąpienie World Anvil feature-parity  
- Wymuszanie chmury (offline-first zostaje)  
- Mylenie z KarmazynOs runtime (to osobny tor)

---

## 10. Definition of Done — MVP (P1–P4)

1. Można utworzyć **Quest** z krokami i powiązać postać/miejsce.  
2. **Eksport Prompt pack** do schowka/pliku działa offline bez LLM.  
3. **Eksport Brief MG** generuje czytelny Markdown.  
4. Testy unit na condense + oba eksporty.  
5. README / F1: jedna sekcja „Adventure / Quest / Eksporty”.

---

## 11. Następny krok implementacyjny

Po akceptacji planu:

1. P1: `TypLore.QUEST` + pola w `types.py` / `panel.py` / locale.  
2. P3 równolegle szkic: `lore/adventure/export_*.py` na mock `CanonSlice` (TDD).  
3. P2 kroki JSON.  
4. P4 szablony.  
5. P5 LLM dopiero gdy eksporty są używane ręcznie.

---

*Dokument żywy — aktualizować przy domknięciu każdej fazy P#.*
