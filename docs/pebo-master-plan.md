# PEBO Master Plan — Path of Exile Build Optimizer

**Date:** 2026-07-01
**Status:** Adopted planning baseline. Supersedes the 3-epic scope in `docs/epics.md` / `docs/PRD.md` for everything after Epic 3; those documents remain the record of Epics 1–3.
**How this was produced:** three deep exploration passes (LEBOv2 design system, this repo's true current state, the PoB PoE2 engine's full feature surface), six feasibility investigations verified against source (headless full-calc, tree rendering, gear/skill editing, UI migration, validation/trust, AI assist), and adversarial review from product-completeness and delivery-realism lenses. Key claims below carry file evidence.

---

## 1. Vision and product thesis

PEBO is a **PoB satellite, not a PoB replacement** — and that is the right target. The user
already lives in Path of Building. PEBO wins by doing the loop PoB cannot:

> **Paste PoB code → trusted, PoB-accurate optimization → see the better tree visually →
> trade-linked gear wishlist → lossless export back to PoB.**

Everything in this plan is sequenced so that loop ships first, and so the product is
strictly better at every milestone even if work stops there. Full editor parity
(crafting bench, gem editing, 200-option config) is catch-up scope PoB already does
better — it comes after the loop, not before.

The UI adopts the **LEBO design language** (see rewritten `PRODUCT.md`): three-panel
builder shell, dark `#0a0a0b` + gold `#C9A84C`, PixiJS WebGL tree canvas, right-panel
optimization intent + stat sheet. The reference implementation at `D:\Projects\LEBOv2\lebo\`
is a working component donor (React 19 + TS + Zustand + PixiJS 8 + Tailwind v4).

**AI doctrine (adopted from LEBO, with one correction):** deterministic engines compute
every suggestion and every number; the LLM only narrates. Note LEBO's shipped prompt spec
actually lets the LLM *choose* node changes — PEBO inverts that: the engine picks, the LLM
receives finished suggestions and returns `{id, narration}` only, enforced by a
numeric-grounding validator. "The algorithm is the magic."

---

## 2. Where we actually are (verified 2026-07-01)

What works today, end-to-end: paste PoB code → parsed build card → dual budget →
hill-climb optimization with SSE progress → before/after stats table → export code
(`src/web/`, Flask + vanilla JS, polished in commit `bc4e8e6`). Dual-budget logic,
BFS connectivity, parsing, and export round-trip are solid.

The hard truths:

1. **The documented product ends at a passive-tree tuner.** `docs/PRD.md:33` scopes to
   "ONE thing perfectly: passive tree optimization"; minions/totems/traps are rejected on
   input by design. The PEBO vision is a new, much larger product than any doc on disk.
2. **The calculator is a reimplementation, not PoB.** `src/calculator/MinimalCalc.lua`
   (1,844 lines) stubs ModParser entirely (`MinimalCalc.lua:46-56,511-521`) — that is the
   root cause of "estimate"-grade stats. `SubprocessCalculator` is a misnomer: it runs the
   same in-process engine (`subprocess_calculator.py:102-118`); its actual subprocess path
   raises `NotImplementedError`.
3. **Epic 2's core claim is unproven.** The optimizer was a structural no-op until the
   2026-06-29 `allocMode` fix, and the corpus improvement gate has not been re-run since
   (`docs/HANDOFF-2026-06-29-OPTIMIZER-NOOP-FIXED.md`: "Do NOT assume Epic 2 is validated yet").
4. **The PoB "submodule" is not a git repo locally.** `external/pob-engine` has no `.git`
   file and `.git/modules` is absent — it is an unverifiable vendored blob. Version drift is
   four-way: `POB_VERSION.txt` pins `69b825bda`/v0.12.2, the parent gitlink records
   `4cf3563f6`, the working tree is 0.15.0 (`manifest.xml`), and parity baselines were
   captured from GUI 0.12.2.
5. **Parity evidence is near-worthless today.** Baselines are naked builds with DPS ≈ 0.18–1.46;
   ±0.1% on those proves nothing. On the geared deadeye fixture, our engine reports ~4% of
   the GUI's DPS (793.7 vs `<PlayerStat>` TotalDPS 18097).
6. **The optimizer mutates passive nodes only** (`neighbor_generator.py:169-172`). No gear,
   no gems, no jewels, no cancellation (`hill_climbing.py` has no stop flag). No AI anywhere.
7. **Doc-vs-reality drift:** `sprint-status.yaml` marks Epic 3 fully `backlog` though
   `src/web/` is built and polished; zero tests import `src.web`.

**The good news that changes everything:** the PoB submodule ships *complete* data and a
*complete, working* calculation engine that we simply never drive:
tree with full render geometry (`TreeData/0_4/tree.json`: 4,701 nodes, polar coords,
sprite atlases), 1,186 item bases, 382 uniques, 901 gems, full affix pools with legality
data, ~150 sidebar stats, ~200 config options, and `Modules/ModParser.lua` (6,940 lines) +
`CalcSetup/CalcPerform/CalcOffence/CalcDefence`. **Nothing needs to be sourced; almost
everything needs to be *driven*.**

---

## 3. The root decision: drive PoB's real engine (the Truth Engine)

Epic 1 abandoned `HeadlessWrapper.lua` as "architecturally impossible" and built
MinimalCalc instead. **That verdict is wrong, and the vendored code proves it:**

- `HeadlessWrapper.lua` is 100% pure-Lua stubs — no DirectX, no windowing
  (`external/pob-engine/src/HeadlessWrapper.lua:6-171`).
- The submodule's own CI boots the ENTIRE engine headlessly on stock LuaJIT:
  `.busted` uses `helper = "HeadlessWrapper.lua"`, and the GitHub workflow runs
  `cd src; luajit HeadlessWrapper.lua` to regenerate ModCache.
- The real 2025 blocker was Lupa-specific: `require()` of native C modules (`lcurl`,
  `lua-utf8`) crashing with SEH `0xe24c4a02` — and Story 1.4 itself discovered the fix
  (`package.loaded` pre-stubs, `docs/stories/story-1.4.md:965-967`) but pivoted to
  MinimalCalc instead of applying it to the full launch flow.

Driving the real pipeline gives us, automatically, because PoB already computes it:
PoB-exact absolute stats (DPS/EHP/resists/ailments), **minions, totems, traps/mines,
triggers** (all currently rejected at the UI), the full config system, and — critically for
the optimizer — **PoB's own fast what-if calculators**:
`calcs.getNodeCalculator` / `getMiscCalculator` (`Modules/Calcs.lua:73-150`), the exact
mechanism PoB's GUI uses for interactive hover deltas and its PowerBuilder full-tree scan
(`CalcsTab.lua:521-612`, ~4.7k nodes in seconds with modKey caching). Expected neighbor-eval
cost ~1–10ms — the same order as MinimalCalc, but accurate.

**Architecture (one, not two):** the headless driver (`driver.lua`, ~250 lines modeled on
HeadlessWrapper) runs inside **respawnable worker processes** with a small command protocol
(`LOAD_BUILD / GET_STATS / EVAL_NEIGHBORS / APPLY_MOVE`). This isolates any residual SEH
crash, sidesteps LuaJIT's single-thread constraint, and serves *both* the optimizer and
interactive UI deltas — the two-thread design sketched for the UI is rejected; the process
pool is the engine API, and interactive calc is just another client with a latest-wins queue.
**Fallback lane (pre-committed):** the identical driver runs under stock `luajit.exe` as a
true subprocess — proven by upstream CI — if Lupa proves unstable with full `Data.lua`.
The spike decides the lane; the decision date is fixed in advance.

Builds are fed to the driver as **original PoB XML** (we already have it from
`parse_pob_code`), not the lossy BuildData re-encoding — that is what makes items, gems,
and config exact, and it routes imports through PoB's own `PassiveSpec` with `convert=true`,
which handles **tree-version migration, weapon-set points, and dual ascendancy for free**.

MinimalCalc is retired to a test fixture when parity passes.

---

## 4. Feasibility verdicts (all six investigated against source)

| Pillar | Verdict | Key proof | Honest effort* |
|---|---|---|---|
| Headless full calc | FEASIBLE w/ risks | Upstream CI runs full engine headlessly; `package.loaded` pre-stub fix already known | 80–140h |
| Visual tree (PixiJS) | FEASIBLE | Layout math extracted (`PassiveTree.lua:503-677`); **DDS→WebP transcode proven this session** (329-icon sheet → 1.78MB WebP in 3.1s; `zstandard`+`texture2ddecoder`+`Pillow` wheels verified) | 80–105h |
| Gear/skill editor + gear scan | FEASIBLE w/ risks | Item grammar fully documented (`Item.lua:277,1124`); crafting legality is a data lookup (`GetModSpawnWeight`); what-if via `calcFunc({repSlotName, repItem})` | 110–180h (editors) + 16–24h (scan) |
| UI migration (React SPA) | FEASIBLE | Backend already a clean 4-endpoint JSON+SSE API; LEBO shell ports near-verbatim; Tauri rejected (Python sidecar cost, zero benefit); SPA is Tauri-wrappable later | 80–110h parity slice **— cut**; SPA starts at tree canvas |
| Validation/trust | FEASIBLE | `<PlayerStat>` harvesting = scripted geared baselines for free; ratchet design prevents tolerance-loosening | 42–66h + corpus curation 20–40h |
| AI assist | FEASIBLE w/ risks | All LEBO patterns port; contract inverted (engine picks, LLM narrates); offline-complete by construction | 95–140h — **demoted to stretch** |

\* Includes the red team's corrections (Windows tax +15–25% on engine work, spike at 1–2
weeks not 2–4 days, affix picker realistically 60–100h).

---

## 5. v1 definition and the NOT-list

**v1 = "Trust the numbers."** Ships when a PoB power user can paste any real geared build
(any archetype, any tree version, weapon sets, dual ascendancy), get PoB-accurate stats
(parity-evidenced, boss-config included), run the optimizer and believe the improvement,
and export a lossless code back to PoB — **in the existing vanilla UI.** No SPA required.
Epic 4 alone flips the trust-tier table from "estimate" to "reliable" with zero frontend work.

**v1 ships WITHOUT (explicit NOT-list — every cut is recoverable, the design work is done):**
- No React SPA parity rebuild of the existing paste→optimize flow (never build the results-table twin)
- No AI/LLM narration (cards are 100% complete from engine data by design)
- No crafting bench / affix editing (the gear *wishlist* tells you what to chase; edit in PoB, re-import)
- No uniques browser, no runes picker, no skills editing (read-only display only)
- No GGG character import (needs POESESSID auth; PoB code paste covers the audience)
- No trade-site *search* (v1.2 emits trade *query links* — see Epic 6)
- No node icons (procedural circles à la LEBO; icon atlas is additive later)
- No ascendancy background art (34MB source asset — vector rings + dimming)
- No beam search / annealing (hill climbing first, measured)
- Config capped at the ~10–20 options that swing DPS (enemyIsBoss preset, charges,
  exposure/shock, enemy level) — not the 200-option tab
- No multi-loadout *editing* (but ALL sets are byte-preserved on round-trip — see gates)

---

## 6. Roadmap

### M0 — Prove the premise (NOW; half a day, mostly machine time)
Run `scripts/run_epic2_validation_isolated.py` (corpus median-improvement gate) — unmeasured
since the no-op fix. **Gate:** median ≥5% and success ≥70% → proceed. Near 0% → the next
epic is "fix the optimizer," and everything below waits.

### Epic 3.5 — Substrate & Trust (lite) (~25–35h) → v0.9 (internal)
1. **Submodule forensics before anything else:** diff the untracked `external/pob-engine`
   working tree against a clean upstream 0.15.0 checkout; convert every local edit into
   `external/patches/*.patch` or consciously reject it. *(Critical: today there is no record
   of what was hand-edited in that tree.)*
2. Re-establish the real submodule, pin to the 0.15.0 release commit; `POB_VERSION.txt`
   becomes *generated* from the gitlink, never hand-edited.
3. `scripts/setup_pob.py` (idempotent): submodule init/update + auto-apply all patches
   (`git apply --check --reverse` skip-if-applied); the ONE setup command in README.
4. Enforcement that cannot be forgotten: autouse conftest fixture `pob_env.verify()` —
   submodule is a real repo, HEAD == gitlink == POB_VERSION == baseline metadata version,
   nil-safety patch marker present. FAIL (not skip) for parity/corpus tests.
5. `scripts/harvest_gui_baselines.py`: parse `<PlayerStat>` from GUI-saved XML (102 stats
   incl. TotalDPS — no manual transcription) + capture **6–8 geared baselines** (one per
   v1-gated archetype: attack, spell-hit, DoT first). Mass capture waits for the spike verdict.
6. Defer: known-gaps ratchet + trust-tier generator land with Epic 4 (they'd measure
   MinimalCalc, which Epic 4 deletes).

### Epic 4 — Truth Engine (~80–140h) → **v1 ships here**
1. **Timeboxed spike (2 weeks hard, go/no-go pre-committed):** `driver.lua` boots the full
   Launch→Main→Data chain under Lupa in a worker process; loads a real geared PoB code;
   `output.TotalDPS` matches GUI 0.15.0 within ±0.1%. Boot crash → flip to the `luajit.exe`
   subprocess lane the same week (same driver file). Also answers: is the ADR-004 patch
   even needed under the real ModParser?
2. `FullCalcEngine` behind the existing `build_calculator.py` interface; XML-direct build
   loading; process-worker pool (2 workers default, respawn on crash); **cooperative cancel
   flag lands here** (same loop the batch-eval rewire touches).
3. **Tree 0_3→0_4 bump** in `passive_tree.py` + startup assert artifact-version ==
   calc-version; imports routed through `PassiveSpec` `convert=true`.
   **Acceptance criteria: weapon-set (allocMode) and dual-ascendancy nodes preserved and
   calc-correct on the corpus; optimizer treats them as frozen allocations in v1.**
4. Optimizer rewire: one `EVAL_NEIGHBORS` batch per iteration via `getMiscCalculator` with
   PowerBuilder-style modKey caching; `useFullDPS=false` during search, FullDPS on accepted
   states; BFS pre-filter stays Python-side.
5. **MVP config end-to-end:** enemyIsBoss (None/Boss/Pinnacle/Uber), charges, exposure,
   enemy level — wired into UI, API, and parity baselines.
6. Validation completes: mass geared-baseline capture (20–24 builds incl. minion/totem/trap
   now that they calc), parity v2 (end-to-end from code string → stats; Tier A hard-gated,
   Tier B ratcheted then promoted to ±0.5%→±0.1%), Epic 2 gate re-run on the full pipeline,
   trust tiers become *generated* from parity artifacts (`trust_tiers.json`), stale-artifact
   refusal in a `release_gate.py`.
7. **Round-trip gate (release-blocking, forever):** import → no-op → export → re-import in
   PoB GUI must preserve every XML section PEBO doesn't edit — all Specs, SkillSets,
   ItemSets, ModRanges, jewels. Multi-loadout fixtures added. One corrupted export kills
   trust with this audience permanently.
8. MinimalCalc retired to test fixture; `subprocess_calculator.py` misnomer cleaned up.

### Epic 5 — Visual Tree & Workspace Shell (~120–180h), value-ordered slices
- **5A (→ v1.1): read-only tree diff canvas.** `scripts/build_tree_data.py` compiles
  `TreeData/0_4/tree.json` → `tree-graph.json` (precomputed x/y + arc params; ~300KB gz)
  with a **CI parity test diffing Python-computed positions against Lua for all 4,353
  renderable nodes** before any frontend work. New `frontend/` (Vite+React19+TS+Tailwind
  v4+Zustand+PixiJS 8 — LEBO's stack minus Tauri), LEBO shell (AppHeader/LeftPanel/
  CenterCanvas/RightPanel/StatusBar port), tree canvas rendering the optimizer's
  before/after as a visual diff. Served at `/app`; **vanilla UI stays the default shell
  until the SPA is strictly better.** Pixi adaptations: static/dynamic layer split, one
  spatial-hash hit test (not 4.4k hit-area children), vector arcs via `Graphics.arc`
  (no texture kite-quads), zoom LOD.
- **5B (→ v1.2): interactive tree editing.** Client-side BFS path preview/alloc/dealloc/
  orphan-confirm (port LEBO's `nearestAllocatedPath`/`computeOrphanedNodes` + PoB's
  `PassiveSpec.lua:952-1012` rules incl. `unlockConstraint`, attribute/switchable pickers —
  note PoE2 0_4 has no PoE1-style masteries), search, tooltips (tree.json stats are already
  resolved English), debounced node-delta API against the Epic 4 worker pool, server-
  authoritative validation. Builds CRUD + on-disk persistence.
- **5C: read-only gear & skills display + loadout switcher.** Item cards with PoB coloring,
  socket groups, spirit budget bar; read-only set-switcher dropdowns (Spec/SkillSet/ItemSet)
  that re-run stats per active set.
- **5D: icon atlas + polish.** `build_tree_assets.py` (proven pipeline) → WebP sprite layer;
  keyboard shortcuts; a11y re-pass (the vanilla UI's WCAG work must be redone in React —
  budgeted, not assumed free).

### Epic 6 — Advisor: optimizer expansion + gear wishlist (~80–120h) → **v2**
*(Deliberately before full editors — this is why a PoB owner opens PEBO.)*
1. `intent.py` weight bands + de-hardcode `metrics.py`'s 0.6/0.4 composite (it's duplicated
   at lines 128/221/253/280 — consolidate); intent slider (Juggernaut↔Glass Cannon) wired
   to optimizer, suggestions, and score gauge from one source of truth.
2. **Tree suggestion engine** (`src/suggest/tree_scan.py`): multi-source BFS frontier,
   per-path delta via `getNodeCalculator`, efficiency = weighted delta/point, 0/1-DP
   knapsack under the dual budget, **post-DP re-validation of overlapping paths** (LEBO
   skips this; we won't), gold/silver tiers on the canvas.
3. **Gear wishlist scan** (`src/suggest/gear_scan.py`): two-phase LEBO pattern — per-affix-
   group weights once (~200–400 calls, tag-prefiltered), then top-K real `repItem` crafts
   per slot (~180 calls); total <700 calls ≈ 15–60s streamed per-slot over SSE; per-slot
   on-demand as default. Output: ranked wishlists ("Ring 1: T2→T1 phys% = +4.2% DPS")
   with satisfied flags + priority slot.
4. **Trade-query emission per wishlist entry** — `ModItem.lua` records already carry
   `tradeHash`; emit pathofexile.com/trade2 query JSON/URLs. Days of work, and it is the
   difference between a wishlist and a toy.
5. Flags engine (res overcap/uncapped, unspent points, missing supports) + suggestion cards
   in the right panel with canvas cross-highlight (LEBO `SuggestionsList` port).
6. Optional: beam width on the hill climb if corpus evidence shows local-optima losses.

### Epic 7 — Full editors (post-demand, ~120–180h)
Affix picker/crafting bench (mirror `UpdateAffixControl` semantics; realistically 60–100h
on its own), uniques browser, runes, skills editing with support-compat validation through
the real `canGrantedEffectSupportActiveSkill`, full config tab, set CRUD. Server-side Lua
`Item:Craft()`/`BuildRaw()` is the single source of truth for item text — never synthesize
item text in Python/JS.

### Epic 8 — Distribution & AI polish (stretch, ~60–100h)
- **Packaging (required before any public release):** PyInstaller one-dir bundle (LuaJIT
  DLL + patched pob-engine data snapshot + built frontend) auto-launching the browser, or
  the Tauri-sidecar wrap the SPA is already compatible with. Until this exists, PEBO is
  formally a personal tool — the current git+venv+patch setup is not something PoB users install.
- LLM narration layer per the inverted contract (numeric-grounding validator, button-gated,
  offline-complete without it), GGG character import, node-delta heatmap.

### Standing workstream — patch-day survival (starts in E3.5, grows with artifacts)
PoE2 ships balance patches every ~3–4 months; each invalidates tree artifacts, catalogs,
atlases, baselines, and the corpus. One pipeline: `scripts/update_pob.py` = bump submodule
→ re-apply patches → regen tree/catalog/atlas artifacts → run Tier-A parity → print stale
Tier-B baselines needing GUI re-capture. Budget ~2 days per league patch, explicitly.

---

## 7. Effort ledger (deduped, honest)

| Milestone | Scope | Hours | Cumulative |
|---|---|---|---|
| M0 | Corpus gate re-run | ~4h (machine) | — |
| E3.5 | Substrate & trust lite | 25–35 | ~30 |
| E4 | Truth Engine + validation completion + **v1** | 80–140 | ~170 |
| 5A | Tree diff canvas + shell (**v1.1**) | 50–70 | ~240 |
| 5B–5D | Interactive tree, read-only gear/skills, icons | 70–110 | ~350 |
| E6 | Advisor + trade links (**v2**) | 80–120 | ~470 |
| E7 | Full editors | 120–180 | ~650 |
| E8 | Packaging + AI narration + import | 60–100 | ~750 |

**v1 lands at ~170h of work; the loop that beats PoB (v2) at ~470h.** The previous implicit
plan front-loaded ~300–400h (SPA parity + editors) before any user-visible improvement —
that inversion is the single biggest change in this plan. Estimates include the Windows
iteration tax (+15–25% on engine work: `-n 1` serialization, SEH teardown noise,
process-spawn boot costs). Config tab full scope (30–50h) is in E7, not hidden in E5.

Velocity reality-check: the repo shows ~9 active commit-days in 9 months. At a sustained
15h/week, v1 is ~3 months and v2 is ~8 months. The milestone structure exists precisely so
that any stopping point still leaves a strictly-better product.

---

## 8. Top risks

| # | Risk | Sev | Mitigation |
|---|---|---|---|
| 1 | Lupa boot of full Launch chain crashes (SEH 0xe24c4a02 resurfaces) | HIGH | `package.loaded` pre-stubs (proven pattern); worker-process isolation; pre-committed `luajit.exe` fallback lane; 2-week spike timebox |
| 2 | Submodule repair clobbers unknown local edits (tree is git-untracked) | CRITICAL | Diff-before-destroy vs clean upstream 0.15.0; every hunk becomes a patch file or a conscious rejection |
| 3 | Round-trip export corrupts sections PEBO doesn't model (multi-loadout, jewels, ModRange) | CRITICAL | Byte-preservation of untouched XML; multi-set fixtures; import→no-op→export→GUI-re-import release gate |
| 4 | Inner-loop latency on FullDPS-heavy builds blows the 300s budget | MED | modKey caching, `useFullDPS=false` search mode, batched evals, 2-worker pool; benchmark in spike on corpus worst case |
| 5 | Pre-E4 geared parity fails catastrophically (~4% of GUI DPS) → tolerance-loosening temptation | HIGH | Tier A hard-gate + Tier B ratchet (`known_gaps.json`: error may never worsen); loosening is structurally impossible |
| 6 | Tree version schism (calc 0_3, render 0_4, imports 0_1–0_4) | HIGH | 0_4 bump + version assert in E4 *before* any artifact is built; `PassiveSpec convert=true` migration |
| 7 | Early-access churn: each PoE2 patch invalidates artifacts/baselines | MED | `update_pob.py` unified pipeline; ~2 days/league budgeted; artifacts embed version+hash |
| 8 | PoE2 fork's own incompleteness caps "PoB parity" (corruption crafting stubbed upstream, mechanics WIP) | MED | Parity target is *the pinned fork*, stated in the UI trust legend; upstream gaps documented in `known_gaps.json`, not silently absorbed |
| 9 | Worker memory (full Data.lua ≈ 200–400MB × workers) | LOW | Pool of 2 default, lazy spawn, `collectgarbage` between builds; measure in spike |
| 10 | Solo-dev scope collapse | HIGH | The NOT-list, milestone cut-lines, and per-epic "usable checkpoint" gates in §6 |

---

## 9. Immediate next actions (in order)

1. **M0:** run the Epic 2 corpus gate (`scripts/run_epic2_validation_isolated.py`) and read
   the median. *(Kicked off 2026-07-01.)*
2. E3.5 step 1: clone upstream 0.15.0 to scratch; diff against `external/pob-engine`;
   inventory local edits.
3. E3.5 steps 2–4: repair the submodule, pin, `setup_pob.py`, conftest guard.
4. Harvest script + 6–8 geared Tier-A baselines.
5. Epic 4 spike, week 1: `driver.lua` under Lupa in a worker process. Go/no-go at end of
   week 2 — embedded lane or `luajit.exe` lane.
6. Update `sprint-status.yaml` to reflect reality (Epic 3 built; this plan adopted).

---

## Appendix A — Key evidence index

- Headless disproof: `external/pob-engine/src/HeadlessWrapper.lua:6-171`, `.busted`,
  `.github/workflows` (`luajit HeadlessWrapper.lua`), `docs/stories/story-1.4.md:925-967`
- ModParser stub: `src/calculator/MinimalCalc.lua:46-56,511-521`
- Fast what-if calculators: `external/pob-engine/src/Modules/Calcs.lua:73-150`;
  PowerBuilder precedent `Classes/CalcsTab.lua:521-612`; GUI hover deltas
  `Classes/PassiveTreeView.lua:1568-1591`
- Tree layout math: `Classes/PassiveTree.lua:503-509` (position), `:563-677` (connectors),
  `:748-805` (node sizes); `TreeData/0_4/tree.json` (4,701 nodes; orbitAnglesByOrbit
  precomputed radians)
- DDS pipeline (proven): `skills_128_128_BC1.dds.zst` = zstd → DDS DX10 array (329×128px,
  BC1) → `texture2ddecoder` → 1.78MB WebP; ddsCoords are 1-based slice indices
- Item grammar: `Classes/Item.lua:277` (ParseRaw), `:1124` (BuildRaw), `:1105`
  (GetModSpawnWeight), `:1370` (Craft); affix pools `Data/ModItem.lua` (1,720 craftable)
- Support compatibility: `Modules/CalcTools.lua:85-110`
- Version drift: `POB_VERSION.txt` vs gitlink `4cf3563f6` vs `manifest.xml` 0.15.0 vs
  baseline metadata 0.12.2; no `.git` in `external/pob-engine`
- PlayerStat harvesting: `tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml`
  (102 GUI-computed stats incl. TotalDPS 18097.07 vs engine 793.7)
- Trade hashes for wishlist links: `Data/ModItem.lua` record field `tradeHash`;
  `Classes/TradeQueryRequests.lua:198,249` (api/trade2)
- Canonical PoE2 colors: `Data/Global.lua:7-81` (see `PRODUCT.md` tokens)
- LEBO donors: `D:\Projects\LEBOv2\lebo\src\features\{layout,skill-tree,optimization}\`,
  `src-tauri\scoring-core\src\{scan,gear,synergy}.rs`, `docs\claude-prompt-spec.md`
