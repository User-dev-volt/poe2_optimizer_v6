# Sprint Change Proposal — PEBO Master Plan Adoption, M0 Gate Disposition, and Epic 3.5 Insertion

**Date:** 2026-07-02
**Author:** Scrum Master (correct-course workflow, non-interactive batch mode)
**Workflow:** Correct Course — Sprint Change Management (`_bmad/bmm/workflows/4-implementation/correct-course/`)
**Status:** APPROVED IN PART — Alec pre-authorized applying (a) the Epic 3.5 story drafts and (b) the sprint-status.yaml reality refresh; both are APPLIED with this proposal. **Every other artifact edit in this document is PROPOSED only** and awaits explicit approval.
**Format precedent:** `docs/sprint-change-proposal-2025-11-29.md`

---

## Executive Summary

**Trigger:** Adoption of `docs/pebo-master-plan.md` (2026-07-01, commit `0b8ca40`) — a strategic re-scope from the documented "3-epic passive-tree tuner" to the PoB-satellite roadmap (M0 → E3.5 Substrate & Trust → E4 Truth Engine = v1 → E5 Visual Tree → E6 Advisor = v2 → E7 Editors → E8 Distribution) — plus the M0 corpus-gate result: **median improvement 46.03% (gate ≥5%: PASS)** and **success rate 66.67% (gate ≥70%: MISS by one build)**, with five builds reporting 0.0% improvement.

**Findings:** Four parallel conflict analyses (PRD/product scope; epics & tech specs; stories & sprint tracking; architecture & ADRs) confirm that every pre-plan planning artifact still self-presents as current, none carries a supersession marker, and the operational tracker (`docs/sprint-status.yaml`) contradicts shipped reality — Epic 3's thin slice (stories 3.1–3.7) is built and polished (commits `537d796`, `bc4e8e6`) yet marked entirely `backlog`.

**Decision (recommended and executed where pre-approved):**
1. **M0 gate: CONDITIONAL PASS — proceed to Epic 3.5**, with mandatory riders (triage the five 0.0% builds; full two-threshold gate re-run at Epic 4 item 6). Rationale in Section 5.
2. **Direct Adjustment path:** insert Epic 3.5 (five stories, drafted, ~25–35h) and re-scope Epic 4+ per the master plan. `docs/epics.md` / `docs/PRD.md` remain the historical record of Epics 1–3, to be marked with supersession banners (PROPOSED).
3. **Sprint-status refresh APPLIED:** Epic 3 dispositions corrected (3.1–3.7 done, 3.9 done-by-delegation, 3.8/3.10/3.11 partial fold-ins with remainders re-routed, 3.12 superseded), 2-9-2 closed on M0 evidence, Epic 3.5 inserted, Epic 4–8 placeholders added.

**Parallel work note:** a forensics kick-off run (the diff half of story 3.5.1) is executing in parallel with this proposal; its report will land at `docs/forensics/pob-engine-forensics-2026-07-02.md`.

---

## 1. Issue Summary (Change Context and Trigger)

### 1.1 What changed

On 2026-07-01 the project adopted `docs/pebo-master-plan.md` as the planning baseline (commit `0b8ca40`). The plan's own header states it "supersedes the 3-epic scope in `docs/epics.md` / `docs/PRD.md` for everything after Epic 3; those documents remain the record of Epics 1–3." The plan re-frames PEBO as a **PoB satellite** delivering the loop *paste → trusted optimization → visual tree → gear wishlist → lossless export*, and re-sequences all future work:

| Milestone | Scope | Ships |
|---|---|---|
| M0 | Corpus gate re-run (post no-op fix) | evidence |
| Epic 3.5 | Substrate & Trust (lite): submodule forensics/repair, generated `POB_VERSION.txt`, `setup_pob.py`, conftest enforcement, GUI baseline harvesting | v0.9 (internal) |
| Epic 4 | Truth Engine: drive PoB's real calc pipeline headlessly | **v1** |
| Epic 5 | Visual tree canvas + workspace shell (5A–5D) | v1.1 / v1.2 |
| Epic 6 | Advisor: optimizer expansion + gear wishlist + trade links | **v2** |
| Epic 7 | Full editors | post-demand |
| Epic 8 | Distribution & AI polish | stretch |

Simultaneously, the M0 gate (plan section 6) was executed and produced a split result (Section 5 below) that the plan's decision rule does not literally cover, requiring adjudication.

### 1.2 Why this needs correct-course

The adoption is one-directional: the plan says it supersedes the old documents, but **no old document says it is superseded**. Concretely:

- Any BMAD workflow (`create-story`, `sprint-planning`, `check-implementation-readiness`, this one) that loads `docs/PRD.md` or `docs/epics.md` as requirements source will plan against the dead 3-epic, tree-only scope. `docs/PRD.md:21` still self-declares "APPROVED — Ready for Architecture Phase"; `docs/epic-alignment-matrix.md:500` still declares "Overall Readiness: 100% - ALL EPICS READY".
- `docs/sprint-status.yaml:68-81` marks epic-3 and all twelve 3-x stories `backlog` although stories 3.1–3.7 shipped in commits `537d796` + `bc4e8e6` (`src/web/` Flask + vanilla JS, verified in-repo). Master plan section 9 item 6 explicitly orders this fix.
- The new epics (E3.5–E8) exist only as master-plan prose — no BMAD-format epic/story definitions, no tracking keys — so the implementation workflows have no valid source for the adopted roadmap.
- Story 2-9-2 has sat in `review` since ~2025-12 with stale evidence; the M0 re-run now supplies the validation it was waiting for.

### 1.3 Evidence base

- `docs/pebo-master-plan.md` (364 lines, read in full) — adopted baseline with file-level evidence appendix.
- `docs/validation/realistic-validation-results.json` (2026-07-02T00:09) — M0 gate result, 15-build corpus.
- Four parallel conflict analyses covering: (1) PRD & product scope, (2) epics & tech specs, (3) stories & sprint tracking, (4) architecture & ADRs. All line citations were verified against the artifacts; the load-bearing code claims were re-verified while drafting this proposal (`src/web/routes.py:50,67,193`; `src/web/config.py:15`; `src/web/app.py:46`; `src/web/optimization_runner.py:161`; zero files under `tests/` import `src.web`; `external/patches/` contains only `global-lua-nil-safety.patch`).

---

## 2. Change Analysis Checklist Results

Executed per `_bmad/bmm/workflows/4-implementation/correct-course/checklist.md` in batch mode.

| Item | Status | Finding (one line) |
|---|---|---|
| 1.1 Triggering story | Done | Not a story — a planning-baseline adoption (`0b8ca40`) + M0 gate result; nearest story-level trigger is 2-9-2 (awaiting validation) and the un-tracked Epic 3 thin slice. |
| 1.2 Core problem | Done | Strategic pivot (adopted) with zero back-references from superseded artifacts + a gate result the plan's wording doesn't adjudicate. |
| 1.3 Evidence | Done | Section 1.3 above; Sections 4–5 below. |
| 2.1 Current epic viability | Done | Epic 3 is *de facto* closed as a thin slice; cannot "complete as planned" (3.8–3.12 are partially folded in or superseded). Dispositions in Section 4.2. |
| 2.2 Epic-level changes | Done | Add Epic 3.5; re-scope Epic 4+ to master-plan structure; close Epic 2 validation question via M0 disposition. |
| 2.3 Future epic review | Done | Old stories 3.8–3.12 re-dispositioned (Section 4.2); backlog-triage's competing "Epic 4: Technical Debt & Polish" label retired (Section 6.4). |
| 2.4 Invalidated/new epics | Done | New: E3.5–E8 per plan. Invalidated as future work: 3.12, remainder of 3.10; tech-specs-summary's Epic 3 architecture. |
| 2.5 Order/priority | Done | Plan section 6 order adopted: E3.5 → E4 (v1) → 5A → 5B–5D → E6 (v2) → E7 → E8. |
| 3.1 PRD conflicts | Done | 20 conflicts catalogued; Section 4.3.1 + proposed edits Section 7.1. |
| 3.2 Architecture conflicts | Done | 10 conflicts; Section 4.3.3 + proposed edits Section 7.3. |
| 3.3 UI/UX conflicts | Done | PRD personas/Journey 2/UX Principle 3 vs PRODUCT.md brand; FR-1.6 rejection UX vs Truth Engine acceptance; Section 4.3.1. |
| 3.4 Other artifacts | Done | sprint-status.yaml, thin-slice plan, backlog-triage, CLAUDE.md, validation harness; Sections 4.2, 4.4, 7.4–7.6. |
| 4.1 Direct Adjustment | Viable | **Selected.** Effort: Low (tracking + story drafting now; doc banners ~1h later). Risk: Low. |
| 4.2 Rollback | Not viable | Nothing to roll back — shipped work is good; the pivot builds on it. |
| 4.3 MVP review | Done (absorbed) | The master plan *is* the MVP redefinition (v1 moves from Epic 3 to Epic 4); no further scope cut needed here. |
| 4.4 Path selected | Done | Direct Adjustment; rationale Section 6. |
| 5.1–5.5 Proposal components | Done | This document. |
| 6.1–6.3 Review & approval | Done | Batch mode: pre-approved subset applied; the rest gated on Alec's review of this document. |
| 6.4 sprint-status.yaml update | Done | APPLIED — exact edit list in Section 8.2. |
| 6.5 Handoff | Done | Section 9. |

---

## 3. Impact Analysis — Epics

### 3.1 Old → new epic mapping

| Old | Status of record | Disposition under the plan |
|---|---|---|
| Epic 1 Foundation (1.1–1.8, done) | CLOSED, but `docs/tech-spec-epic-1.md` records the *unbuilt* HeadlessWrapper design; Story 1.4 pivoted to MinimalCalc mid-epic and the spec was never revised | Goal re-opened as **Epic 4 Truth Engine** under a different architecture (XML-direct `driver.lua` in respawnable worker processes). The "architecturally impossible" verdict is overturned by plan section 3 (upstream CI boots the full engine headlessly; `package.loaded` pre-stub fix known — `docs/stories/story-1.4.md:965-967`). |
| Epic 2 Core Optimization (2.1–2.9.2) | Algorithm design record STAYS AUTHORITATIVE (hill climbing, dual budget, free-first, convergence, progress) | Validation re-scoped: M0 adjudicated here (Section 5); final re-run at Epic 4 item 6. Evaluation loop rewired in E4 (batched `EVAL_NEIGHBORS`, modKey caching, cancel flag). Story 2.9's hybrid MinimalCalc/subprocess routing is ENTIRELY SUPERSEDED (MinimalCalc retires to test fixture; `subprocess_calculator.py` misnomer cleanup — its subprocess paths raise `NotImplementedError` at lines 162/191/220). |
| Epic 3 UX & Reliability (3.1–3.12) | SPLIT — see Section 4.2 | 3.1–3.7 built (record: `docs/epic-3-thin-slice-plan.md` + commits); 3.9 done by delegation; 3.8/3.10/3.11 partial fold-ins; 3.12 superseded. Vanilla UI remains the default shell; Epic 4 extends it (MVP config, cancel); SPA is Epic 5. |
| — (no counterpart) | — | **M0** and **Epic 3.5** are new; E3.5 absorbs Epic-1-era substrate debt (submodule forensics/repair, generated POB_VERSION, setup script, conftest enforcement, baseline harvesting) that no old epic owned. |
| — | — | **E5 Visual Tree, E6 Advisor (v2), E7 Editors, E8 Distribution/AI** — new, per plan section 6. |

### 3.2 Epic numbering hazards (resolved by this proposal)

- `docs/backlog-triage-2025-10-27.md:144` proposed a different "Epic 4: Technical Debt & Polish" — that label is retired (PROPOSED annotation, Section 7.4); numbers M0/E3.5/E4–E8 are reserved exclusively for the master-plan structure.
- Epic 3.5 tracking keys use the `3.5-N-slug` / `epic-3.5` convention specifically to avoid colliding with epic-3 keys (`3-5-optimization-progress-display-real-time` exists).

---

## 4. Impact Analysis — Stories and Artifacts

### 4.1 Delivered-but-untracked work (Epic 3 thin slice)

Verified in-repo: `src/web/` (app.py + factory, routes.py, sse_manager.py, session_manager.py, optimization_runner.py, templates/index.html, static/js/main.js + sse_client.js, static/css/styles.css), `main.py`, `encode_pob_code` in `src/parsers/pob_parser.py` with unit test `tests/unit/test_encode_pob_code.py`. Commits `537d796` (thin slice 3.1–3.7) and `bc4e8e6` (polish: WCAG AA contrast, reduced-motion, Mana reliability). The working tree additionally carries uncommitted polish to `src/web/routes.py`, `styles.css`, `main.js`, `index.html` on branch `feat/epic3-ui`.

**Known debt:** zero automated tests import `src.web` — thin-slice plan step 10 (1–2 Flask test-client smoke tests) was never fulfilled. Tracked as an Epic 3.5 rider (Section 8.3).

### 4.2 Story dispositions (APPLIED to sprint-status.yaml)

Every old Epic 3 story ID now maps to exactly one of {done, done-by-delegation, partial-fold-in, superseded}:

| Story | Disposition | Evidence |
|---|---|---|
| 3-1 Flask server | **done** | `src/web/app.py` + `main.py` (`537d796`) |
| 3-2 PoB input & validation UI | **done** | client checks + server parse + unsupported-build gate (`routes.py:67` `detect_unsupported_build_type`) |
| 3-3 Budget input (dual fields) | **done** | `templates/index.html` |
| 3-4 Metric selection | **done** | metric select wired to `OptimizationConfiguration` |
| 3-5 Progress display (SSE) | **done** | queue-per-session `sse_manager.py`, 5-kwarg progress callback |
| 3-6 Results before/after | **done** | `static/js/main.js` |
| 3-7 Export optimized code | **done** | `encode_pob_code`; unit test `tests/unit/test_encode_pob_code.py` |
| 3-8 Structured errors | **partial fold-in; remainder open** | shipped: error_type/reason 400/500 mapping + terminal SSE error events (`routes.py`, `optimization_runner._fail`). Full FR-1.4 4-field format not built → E3.5 hardening window or Epic 5 error UX. |
| 3-9 Timeout hard-stop | **done by delegation** | `TIMEOUT_SECONDS = 300` (`src/web/config.py:15`) → `max_time_seconds`; partial result via `convergence_reason=timeout`; no Flask watchdog by design |
| 3-10 Resource cleanup | **partial fold-in; remainder superseded** | shipped: `del result` + `gc.collect()` in worker `finally` (`optimization_runner.py:161`). Structural fix = Epic 4 respawnable worker pool; do not build in-process Lua cleanup. |
| 3-11 File logging | **partial fold-in; remainder parked** | shipped: `logging.basicConfig(INFO)` to stderr (`app.py:46`). `logs/optimizer.log` RotatingFileHandler not built → E3.5 hardening or Epic 8 packaging. |
| 3-12 Perf tuning | **superseded — do not build** | premise (MinimalCalc 1000-calc/s NFR) conflicts with Story 2.9 routing and is retired by Epic 4's optimizer rewire. |

**2-9-2 (spell/DOT MinimalCalc enhancement): CLOSED as done on M0 evidence.** All 15/15 corpus builds execute with 0 errors; spell/DOT baselines nonzero through the 2-9-2 path (bloodmage_remnants 2324 DPS, witch_essence_drain 1275, lich_frost_mage 109); corpus median improvement 46.03%. The residual accuracy gap (MinimalCalc ≈4% of GUI DPS on geared builds; lich_storm_mage_90 0-DPS main skill) is out of 2-9-2's scope and structurally superseded — Epic 4 retires MinimalCalc entirely. Holding the story in `review` bought nothing.

**No retroactive 3-x story files are backfilled** (wasted effort). `docs/epic-3-thin-slice-plan.md` is named in the tracker as the de-facto epic context and as-built record; the process deviation (no story files, no SM review) should be captured in the optional epic-3 retrospective before E3.5 kickoff.

### 4.3 Artifact conflicts (summary; full proposed-edit list in Section 7)

#### 4.3.1 PRD & product scope

`docs/PRD.md` is internally coherent but frozen at the 2025-10 tree-only thesis and contains zero acknowledgment of the supersession. Headline conflicts (of 20 catalogued):

- **FR-1.6 (`docs/PRD.md:267-295`) — CRITICAL, has live code surface.** Mandates detect-and-reject of minion/totem/trap/trigger builds with "Coming in V2" messaging — enforced today at `src/web/routes.py:47-104` (copy at line 50, gate at line 67). The plan makes those archetypes the core Truth Engine payoff (section 3) arriving at **v1/Epic 4**, not V2; Journey 3 (`PRD.md:1494-1548`) is built on the rejection flow. An Epic 4 story to retire the gate is pre-filed (Section 7.1, item E).
- **Supersession banner missing (`PRD.md:21, 2214-2241`)** — the single highest-leverage edit; neutralizes most low-severity drift (December-2025 dates, "1,500-node tree" vs actual 4,701, 8-week plan) without rewriting history.
- **"ONE thing perfectly" scope thesis (`PRD.md:33,157`; UX Principle 3 at `1606-1622`)** — forbids exactly what the plan schedules (gear wishlist E6, visual tree E5, editors E7). What survives: no full build-generation-from-scratch; simplicity principle.
- **"100% accuracy guarantee" (`PRD.md:35,153,1863`)** vs the adopted trust doctrine (parity-evidenced tiers, never asserted — `PRODUCT.md:33-36`, plan Epic 4 item 6); the PRD even self-contradicts at `1633/1840`.
- **Uniform ±0.1% parity (FR-3.2, `PRD.md:403`)** vs the two-tier model (Tier A hard-gated ±0.1%; Tier B ratcheted then promoted). Current ±0.1% evidence is naked-build-only and "proves nothing" (plan section 2 item 5; geared deadeye reads ~4% of GUI DPS).
- **Competing corpus gates (`PRD.md:73-78`, Epic-2 criteria `1910-1914`)** — 8% median / 95% completion / 80% improved vs the plan's ≥5% / ≥70%. Adjudicated in Section 5: plan section 6 thresholds govern.
- **Multi-user/VPS requirements (FR-3.5 `434-460`, FR-3.3 `409-425`, NFR-1 `1035-1040`)** vs local personal tool + Epic 4 worker-pool concurrency; PRD's own Out of Scope (`2002`) already contradicts FR-3.5.
- **Two trust vocabularies (FR-4.5 `544-552` High/Medium/Low confidence)** vs adopted reliable/approx/estimate tiers from parity artifacts. Decision needed before Epic 4's `trust_tiers.json` generator: PRODUCT.md vocabulary is user-facing; FR-4.5 re-verification demotes to an internal sanity check.
- **Manual pin procedure (`PRD.md:677-689`)** — `git checkout <hash>` + `echo > POB_VERSION.txt` is the documented anti-pattern behind the four-way version drift; superseded by E3.5 stories 3.5.2/3.5.3.
- Also: public-launch Goals 2–5 (`170-206`) incl. a GA4-vs-NFR-8 self-contradiction and phantom FR-6.1/6.2 labels (`926-936`); Epic 1 record misstatement (`1859-1885` claims HeadlessWrapper + 100-build parity; reality = MinimalCalc + naked-build baselines); stale performance targets (FR-3.3 `407`); personas/voice (`37`, Journey 2 `1365-1491`) vs PRODUCT.md's hardcore-theorycrafter brand; V2 deferral list (`2008-2024`) items now scheduled (visual tree → 5A, save/load → 5B, item recommendation → E6, dark mode obsolete); "no AI chatbot ever" (`2030`) vs Epic 8's narration-only LLM layer; "no React" anti-pattern (`1835`) vs Epic 5 stack.

`PRODUCT.md` needs only a one-sentence phasing note (its Product Purpose describes the end-state in present tense; v1 ships in the vanilla UI). The 2025-10-08 product brief needs a one-line historical banner.

#### 4.3.2 Epics & tech specs

- **Zero supersession markers** across `docs/epics.md`, `tech-spec-epic-1.md`, `tech-spec-epic-2.md`, `tech-specs-summary.md`, `epic-alignment-matrix.md`; each still self-presents as current/actionable (`epics.md:1-33` "Proceed to architecture phase"; `tech-spec-epic-1.md:1218-1220` "COMPLETE / Epic 2 begins"; `tech-specs-summary.md:746` "Ready for Implementation"; `epic-alignment-matrix.md:500` "100% READY").
- **`tech-spec-epic-1.md` is doubly wrong as a record:** its Detailed Design (`95-510`) was never built (Story 1.4 pivot), and its impossibility verdict is now overturned. `epics.md:478` cites a nonexistent "Epic 1 ADR" — repaired by proposed ADR-005 (Section 7.3).
- **`tech-spec-epic-2.md`:** module design stays authoritative; its calculation contract (2ms/call, 0% error, frozen Epic 1 APIs, no cancellation, `599-611` deferral list) is superseded by Epic 4/6.
- **`tech-specs-summary.md` is triple-stale** (describes a never-built Epic 3 architecture with crash-prone samples; contradicts shipped algorithm parameters — patience=3 not 50, 600 not 1000 iterations, 0.6/0.4 not 0.7/0.3; references three nonexistent documents). Archive candidate.
- **`epic-alignment-matrix.md`:** phantom E*-S* story taxonomy that never matched `docs/stories/` or sprint-status keys; FR-4.6 cancellation mis-routed to Epic 3 (lands in Epic 4 step 2). Archive candidate.
- **`docs/epic-3-thin-slice-plan.md`** is the de-facto Epic 3 record but nothing points to it, and its section 8 open questions read as unresolved though the implementation answered them (cancel omitted → E4; `encode_pob_code(original_code, optimized_nodes)` adopted; hardcoded `src/web/config.py`; `debug=False`). AS-BUILT note proposed.
- **Internal consistency of `epics.md`:** summary counts predate Story 2.9 (`12,488,812-819`); 2.9.1/2.9.2 appear nowhere in it.

#### 4.3.3 Architecture & ADRs

- **`docs/architecture/pob-engine-dependencies.md` ("Production Reference", line 5)** enshrines the overturned verdict, including a hard "DO NOT LOAD: Launch.lua, HeadlessWrapper.lua" table (`390-402`) that Epic 4 violates by design. Its documented hand-edits — `ModStore.lua:444/464` nil guards (`509-513,766-769`) and a project-authored `src/Export/stub_functions.lua` (`734`) — have **no corresponding patch files** (`external/patches/` holds only `global-lua-nil-safety.patch`). This is the concrete form of plan risk #2 (CRITICAL) and a direct input to story 3.5.1.
- **ADR registry gap:** `docs/decisions/` holds only ADR-003, ADR-004, and a story-2.8 scope note. Neither the MinimalCalc pivot nor hybrid routing was ever ADR'd; the plan's root reversal has no decision record outside the plan. Four new ADRs proposed (005 Truth Engine, 006 worker pool, 007 XML-direct loading, 008 tree 0_4 bump) + amendments to ADR-003 (fix `-n auto` vs CLAUDE.md `-n 1` contradiction; crash posture superseded-in-part by worker isolation) and ADR-004 (status "under re-evaluation; supersession trigger = E4 spike"; reapplication section → `setup_pob.py`).
- **ADR numbering collision:** `solution-architecture.md:1417-1541` embeds inline ADR-001..004 with different subjects than the `docs/decisions/` files, and `:1681-1686` references a never-created `docs/ADRs/` directory including a phantom ADR-005. `docs/decisions/` is declared canonical before new ADRs are numbered.
- **`docs/solution-architecture.md`** conflicts with the plan's root decision on five counts (in-process/no-subprocess `207,279`; thread-local engines `723-725`; 10 optimization threads `815-819`; <100MB/session `223` vs plan risk #9's 200–400MB/worker; BuildData-centric flow `922-936`; FR-3.1 still says HeadlessWrapper `122`). Banner, don't rewrite.
- **`docs/architecture/epic-2-optimizer-design.md`** (`344-347,541-545,596-616,713`): per-neighbor eval, no caching, ~2ms budget, future multi-threading, no cancellation — all superseded by the Epic 4 delta (batched `EVAL_NEIGHBORS`, modKey caching, processes-not-threads, cooperative cancel).
- **`docs/architecture/epic-3-web-architecture.md`** (`181-211`): the global `optimization_lock` premise becomes vestigial when the engine moves to worker processes; remove the lock in the same change that swaps the engine.
- **`CLAUDE.md` Critical Constraints:** two claims are false today regardless of the plan — the tree is loaded from `TreeData/0_3/tree.json` (`passive_tree.py:267`), not "pre-built from PassiveTree.lua", and the Story 2.9 "subprocess (accurate)" path is in-process (NotImplementedError at `subprocess_calculator.py:162/191/220`). Fix now (PROPOSED); stage the full constraints rewrite as an Epic 4 item-8 checklist entry.

### 4.4 Technical impact

- **Live rejection gate:** `src/web/routes.py:47-104` must eventually be retired (Epic 4 story pre-filed, Section 7.1-E) — until then, E3.5 baseline harvesting for minion/totem/trap archetypes cannot enter via the UI; use the parser/fixture path (and per the plan they wait for the spike verdict anyway — attack, spell-hit, DoT first).
- **Version drift is four-way** (`POB_VERSION.txt` 69b825bda/v0.12.2 vs gitlink `4cf3563f6` vs working tree 0.15.0 vs baselines from GUI 0.12.2) and `external/pob-engine` is not a git repo locally — Epic 3.5's entire reason to exist.
- **Dirty working tree:** `docs/sprint-status.yaml` + four `src/web` files are modified-uncommitted on `feat/epic3-ui` (plus `docs/HANDOFF-2026-06-29-OPTIMIZER-NOOP-FIXED.md` untracked). Recommendation: commit this proposal, the story files, the sprint-status refresh, and the pending web polish together (or in immediate sequence) on `feat/epic3-ui`, then merge to `main` so tracking, code, and the adopted plan coexist.
- **Validation harness wart:** the summary block reports `successful: 15 / errors: 0` next to `success_rate_pct: 66.67` — two different definitions of "success" in one block. Fix: separate `ran_without_error` from `improved` (PROPOSED, Section 7.6).

---

## 5. M0 Gate Disposition

### 5.1 The result (docs/validation/realistic-validation-results.json, 2026-07-02)

- **Median improvement: 46.03%** — gate ≥5%: **PASS** (9x the bar). The median is computed over all 15 builds *including* the five zeros (46.03 is the 8th sorted value), so the pass is not an artifact of excluding failures.
- **Success rate: 66.67% (10/15)** — gate ≥70% (needs 11/15): **MISS by exactly one build.**
- 10 builds improved 7.98%–161.61%; 0 errors; 0 budget violations; max runtime 152s < 300s budget.

### 5.2 The gap in the gate wording

Plan section 6 M0 defines two branches: "median ≥5% AND success ≥70% → proceed" and "near 0% → next epic is fix-the-optimizer, everything waits." The actual result satisfies neither literally. Honesty requires stating this plainly: **the gate, as written, was missed** — one threshold passed decisively, the other failed by one build.

### 5.3 Failure signature of the five 0.0% builds

All five (gemling_frost_mage_100, lich_storm_mage_90, titan_infernal_cry_72, warrior_ballista_93, witch_frost_mage_91) failed **identically at iteration 0** with `convergence_reason=no_valid_neighbors` in <1s. Four of five have nonzero baseline DPS (465.0 / 78.54 / 79.8 / 206.325), so this is **not weak optimization** — the optimizer never got a move frontier. Leading hypothesis: allocated node IDs absent from the 0_3 tree graph (tree-version mismatch — plan risk #6), which Epic 4 item 3's 0_4 bump + `PassiveSpec convert=true` migration is already scheduled to fix. lich_storm_mage_90's 0.0 *baseline* is a MinimalCalc coverage gap that Epic 4 also removes.

### 5.4 Disposition: CONDITIONAL PASS — proceed to Epic 3.5 (recommended, and the basis on which E3.5 stories are drafted)

**Rationale:**
1. The gate's purpose was to prove the post-`allocMode`-fix optimizer genuinely improves builds and to catch a recurrence of the near-0% no-op regression. Both purposes are served: 10 builds improved 8–162%, and the near-0% failure mode is definitively excluded. The "fix the optimizer first, everything waits" branch targets a failure mode this result rules out — invoking it would be applying the letter of the gate against its intent.
2. The miss is one build wide, and the failure signature points at an *eligibility/frontier defect* (tree-version mismatch) that the adopted plan already schedules a structural fix for (Epic 4 item 3) — not at the optimization algorithm the gate was probing.
3. Epic 3.5 is substrate work (submodule repair, setup script, conftest enforcement, baseline harvesting) whose value is independent of optimizer quality; blocking it to investigate an evaluator Epic 4 replaces would idle the critical path for nothing.

**Mandatory riders (this disposition is conditional on them):**
1. **Triage the five no_valid_neighbors builds before or during the Epic 4 spike:** check whether their allocated node IDs exist in the 0_3 tree graph (frontier-empty hypothesis) and why lich_storm_mage_90 calcs 0 DPS. Feeds the spike's acceptance evidence.
2. **The full two-threshold gate (median ≥5% AND success ≥70%) MUST be re-run and PASS at Epic 4 item 6** on the Truth Engine pipeline. That re-run is already in the plan; this disposition does not waive it — it defers it to the pipeline that will actually ship.
3. **This document is the disposition record.** PROPOSED: add a one-line pointer next to the results JSON (`docs/validation/M0-gate-decision.md` or an amendment under plan section 6) so the recorded result and the gate wording stop conflicting (Section 7.6).
4. **Fix the harness summary** to distinguish `ran_without_error` (15/15) from `improved` (10/15) before the Epic 4 re-run.

**Superseded bars:** plan section 6 M0 thresholds (≥5% median / ≥70% success) supersede `docs/PRD.md:73-78` (8% median / 95% completion) and the Epic-2 criteria in `epics.md:268-272` / `tech-spec-epic-2.md:683-686` (80%+ builds improved). Three numeric bars must not stay live simultaneously; the banners in Section 7 record this.

---

## 6. Recommended Path Forward

### 6.1 Options evaluated

| Option | Verdict | Notes |
|---|---|---|
| 1. Direct Adjustment — insert Epic 3.5, re-scope E4+ per plan, banner old docs | **SELECTED** | Effort Low-Medium; Risk Low. The strategic replan already happened (plan adoption); this proposal is its mechanical propagation into BMAD artifacts. |
| 2. Rollback | Not viable | Nothing merits reverting: the thin slice, the no-op fix, and the harness hardening are all keepers; the pivot builds on them. |
| 3. MVP review | Absorbed | The master plan *is* the MVP redefinition: v1 ("Trust the numbers") moves from Epic 3 to Epic 4, with an explicit NOT-list. No additional scope decision is needed in this workflow. |

### 6.2 The adjustment, concretely

1. **Insert Epic 3.5 — Substrate & Trust (lite)** with five stories derived 1:1 from plan section 6 items 1–5 (item 6 is a deferral note, not a story). Stories DRAFTED (files in `docs/stories/`, keys in sprint-status) — APPLIED per pre-approval. Full breakdown in Section 8.1.
2. **Re-scope Epic 4+ as master-plan epics.** Tracking placeholders `epic-4`..`epic-8` added at `backlog` pointing at the plan — APPLIED. BMAD-format epic/story definitions for E4+ are authored at each epic's kickoff (via create-epics-and-stories or correct-course), carrying the plan's per-step acceptance criteria (e.g. E4 item 3's weapon-set/dual-ascendancy AC, item 7's round-trip release gate). This closes the "two implicitly open planning paths" gap: **E3.5 executes from the drafted stories; E4+ plans from the master plan at kickoff.**
3. **`docs/epics.md` and `docs/PRD.md` remain the record of Epics 1–3**, with supersession banners PROPOSED (not applied) per Section 7. Never rewrite history; banner-and-pointer only.
4. **Sprint-status refresh** — APPLIED (Section 8.2): reality-sync of Epic 3, closure of 2-9-2, Epic 3.5 insertion, E4–E8 placeholders, header pointer to the plan and this proposal.
5. **M0 conditional-pass** riders tracked: triage lands in the Epic 4 spike's entry checklist; the gate re-run is Epic 4 item 6 (already in plan); the harness fix and disposition pointer are PROPOSED edits (Section 7.6).

### 6.3 Effort / risk / timeline

- Applied portion: story drafting + tracker refresh (~2h, done with this proposal).
- Proposed doc-status pass (banners + ADR amendments + pointer notes): **~2–4h total**, bundleable with E3.5 as a "doc-status" work item.
- New ADRs 005–008: drafted at Epic 4 spike kickoff (~2–3h), finalized at the pre-committed go/no-go date.
- Risk of *not* doing the doc pass: any future agent or workflow ingests dead scope as current requirements — the exact failure mode that let sprint-status drift for six months.
- Timeline impact of the change itself: none negative — E3.5 (25–35h) is the plan's own next step; v1 lands at Epic 4 (~170h cumulative per plan section 7).

---

## 7. Detailed Proposed Edits (NOT applied — awaiting approval)

Everything in this section is PROPOSED only. Grouped per artifact; each edit is banner/pointer-style — no historical content is rewritten.

### 7.1 docs/PRD.md

- **(A) Supersession banner** immediately after the title: "STATUS (2026-07-01): Historical record of Epics 1–3 as designed. Superseded by `docs/pebo-master-plan.md` (adopted 2026-07-01, commit 0b8ca40) for all product scope, roadmap, and requirements after Epic 3. Do not derive new stories from this document." Add revision-history row 1.2 recording the supersession. (Covers the low-severity drift: December-2025 dates at 52-53/2160, node counts at 29/92, week plans.)
- **(B) FR-1.6 + Journey 3 annotation (`267-295`, `1494-1548`):** "SUPERSEDED at Epic 4 by pebo-master-plan sections 3/5 — rejection gate is Epics 1–3-era behavior; Truth Engine v1 accepts all archetypes, gated by parity-evidenced trust tiers instead of input rejection."
- **(C) Scope-thesis annotations (`33`, `157`, UX Principle 3 `1606-1622`, priority ranking `1811`):** boundary moved from "tree only" to "the loop"; full build-generation-from-scratch stays out; simplicity principle survives.
- **(D) Trust-language replacements (`35`, `153`, `1863`; FR-3.2 `403`; FR-4.5 `544-552`):** "parity-evidenced against the pinned PoB PoE2 fork; per-stat trust tiers (reliable/approx/estimate) generated from parity artifacts (`trust_tiers.json`)". Never "guarantee". FR-3.2 → tiered parity + ratchet model. FR-4.5 High/Medium/Low demoted to internal re-verification check; PRODUCT.md tier vocabulary is the single user-facing language.
- **(E) Pre-file Epic 4 story — retire the rejection gate:** remove `detect_unsupported_build_type()` and the "Coming in V2" copy (`src/web/routes.py:47-104`, copy at `:50`) when Truth Engine parity lands; acceptance = minion/totem/trap builds accepted and trust-tiered, not rejected. (Story to be drafted with the Epic 4 epic definition.)
- **(F) Gate supersession note (`73-78`, epic map `1963-1971`):** plan section 6 M0 thresholds supersede these; v1 lands at Epic 4, not Epic 3; link Section 5 of this proposal as the adjudication record.
- **(G) Goals 2–5 (`170-206`) marked pre-pivot aspirations** deferred until after Epic 8 packaging; resolve the GA4-vs-NFR-8 contradiction in favor of NFR-8 (`1220`, local-only, no analytics); fix/annotate phantom FR-6.1/6.2 labels in the Tier-5 matrix (`926-936`).
- **(H) FR-3.5 / FR-3.3 / NFR-1 concurrency clauses (`434-460`, `409-425`, `1035-1040`)** superseded: single-user, Epic 4 worker-pool architecture ("one Lua engine per worker process, respawn on crash").
- **(I) FR-3.3 performance targets (`407`)** re-baselined in the Epic 4 spike; binding metric = end-to-end optimization within the 300s budget on the corpus worst case (plan risk #4).
- **(J) Epic 1 as-built annotation (`1859-1885`):** delivered via MinimalCalc, not HeadlessWrapper (story-1.4, ADR-004); parity criteria met on naked-build baselines only; Epic 4 returns to the real engine.
- **(K) Setup block (`677-689`)** superseded by `scripts/setup_pob.py` (E3.5 stories 3.5.2–3.5.3); the manual `echo > POB_VERSION.txt` procedure is the documented drift anti-pattern.
- **(L) Personas/voice (`37`, Journey 2 `1365-1491`, plain-language principle `1843-1845`)** superseded by PRODUCT.md Users/Brand for post-Epic-3 UX work.
- **(M) V2 deferral list (`2008-2024`)** annotated with scheduled homes (visual tree → 5A, save/load → 5B, item recommendation → E6; dark mode obsolete under the dark-only design system; mobile stays out). **(N)** "AI chatbot ever" (`2030`) reworded to exclude AI-*chosen* build changes; narration-only LLM layer is Epic 8. **(O)** "No React" anti-pattern (`1835`) scoped to the Epics 1–3 vanilla UI. **(P)** NFR-7 monthly-test cadence (`1191-1196`) → `update_pob.py` per-league-patch workstream.

### 7.2 docs/epics.md, tech specs, matrix, thin-slice plan, PRODUCT.md, product brief

- **(A) Supersession banner** under the title of all five old planning docs (`epics.md`, `tech-spec-epic-1.md`, `tech-spec-epic-2.md`, `tech-specs-summary.md`, `epic-alignment-matrix.md`): "SUPERSEDED as planning baseline (2026-07-01): `docs/pebo-master-plan.md` (commit 0b8ca40) governs everything after Epic 3. This document remains the historical record of Epics 1–3 only — do not draft new stories or epics from it. Epic 3 as-built record: `docs/epic-3-thin-slice-plan.md`." Flip tech specs' `Status:` fields to "Superseded — historical record".
- **(B) tech-spec-epic-1.md three-fact banner:** (1) this design was NOT built — Epic 1 shipped MinimalCalc per story-1.4; (2) the "architecturally impossible" verdict is overturned by plan section 3; Epic 4 supersedes this spec's calculation design; (3) ±0.1% parity claims were met only against naked baselines.
- **(C) tech-spec-epic-2.md scoped banner:** module/dataclass design remains authoritative; calculation contract, perf numbers, frozen-API constraint, and out-of-scope list superseded by plan sections 3/6; 8%/80% acceptance bar superseded by the 5%/70% gate; final Epic-2 validation re-scoped into Epic 4 item 6.
- **(D) epics.md banner additions:** Story 3.8–3.12 disposition table (per Section 4.2); note that summary counts predate Story 2.9 and that 2.9.1/2.9.2 + Epic 3 thin-slice execution are recorded in `docs/stories/` and sprint-status; note the dangling "Epic 1 ADR" citation at `:478` resolves to proposed ADR-005.
- **(E) tech-specs-summary.md:** banner "superseded for all design purposes — do not implement from this document"; point Epic 3 as-built → thin-slice plan, future UI → plan Epic 5; note the three broken doc references. **Archive candidate** (`docs/archive/`), as is **epic-alignment-matrix.md** (banner: story IDs herein were never used; FR-4.6 cancellation re-routed to Epic 4).
- **(F) epic-3-thin-slice-plan.md AS-BUILT note:** 3.1–3.7 shipped in `537d796` + `bc4e8e6`; section 8 answers as implemented (cancel omitted → E4; `encode_pob_code(original_code, optimized_nodes)`; hardcoded `config.py`; `debug=False`); known gap: zero tests import `src.web`.
- **(G) PRODUCT.md one-sentence phasing note** in Product Purpose: "Delivery is phased per the master plan: v1 = Truth Engine in the existing vanilla UI; the shell described here is the Epic 5+ target."
- **(H) Product brief (2025-10-08) historical banner:** "Historical (2025-10-08) — product direction superseded by `docs/pebo-master-plan.md` (2026-07-01)."

### 7.3 Architecture docs & ADRs

- **(A) pob-engine-dependencies.md:** supersession banner; retract the DO-NOT-LOAD table (`390-402`) and the "failed due to GUI dependencies" root cause (replace with the Lupa native-C-module finding); re-scope as historical reference for the MinimalCalc test fixture.
- **(B) solution-architecture.md:** header banner marking sections 3/4/6/7/8 superseded by plan section 3 + future ADR-005..008 for post-Epic-3 work; note the memory (<100MB/session vs 200–400MB/worker) and concurrency (10 threads vs 2-worker pool) corrections; annotate sections 12/14.2 that embedded ADRs are historical inline decisions (relabel "SA-ADR-1..4") and `docs/ADRs/` never existed; declare `docs/decisions/` the canonical ADR registry.
- **(C) New ADRs (draft at Epic 4 spike kickoff; finalize at go/no-go):** ADR-005 Truth Engine (headless `driver.lua`; records disproof evidence, MinimalCalc retirement trigger, subprocess misnomer cleanup — also repairs `epics.md:478`); ADR-006 worker-pool process isolation (LOAD_BUILD/GET_STATS/EVAL_NEIGHBORS/APPLY_MOVE, pool=2, respawn, lane decision, latest-wins queue, rejection of the two-thread UI design); ADR-007 XML-direct build loading (PassiveSpec convert=true; BuildData demoted; byte-preservation round-trip gate); ADR-008 tree 0_4 bump + artifact-version==calc-version startup assert (`passive_tree.py:242/434` hardcode "0_3" today).
- **(D) ADR-003 amendment:** fix prescribed invocation to `-n 1` (matches CLAUDE.md and practice); add "superseded-in-part by worker-pool isolation (ADR-006)".
- **(E) ADR-004 amendment:** status "Accepted — under re-evaluation; supersession trigger = Epic 4 spike outcome (fixed date)"; reapplication section → pointer to `setup_pob.py`; conftest patch-marker check must be **patch-set-driven** (one marker per patch file) so dropping the patch, if the real ModParser never passes nil, is a one-edit change. (Coordination hazard: story 3.5.4 must NOT hardcode the nil-safety marker.)
- **(F) epic-2-optimizer-design.md "Epic 4 delta" note:** EVAL_NEIGHBORS batching + modKey caching replace per-neighbor calc; perf budget re-baselined in the spike; parallelism = worker processes not threads; cooperative cancel + per-iteration progress cadence added.
- **(G) epic-3-web-architecture.md forward-note:** the global `optimization_lock` and its rationale are superseded by ADR-006 when FullCalcEngine lands; remove the lock in the same change that swaps the engine.

### 7.4 docs/backlog-triage-2025-10-27.md

One-line annotation at `:144` retiring its "Epic 4: Technical Debt & Polish" label: superseded; that batch is unscheduled or folds into master-plan E7/E8 and the standing patch-day workstream. Numbers M0/E3.5/E4–E8 reserved for the master-plan structure.

### 7.5 CLAUDE.md

Fix the two already-false claims now: tree source = `external/pob-engine/src/TreeData/<ver>/tree.json` (`passive_tree.py:267`), not "pre-built from PassiveTree.lua"; label the Story 2.9 bullet's "subprocess (accurate)" as misnamed/in-process. Stage the full Critical Constraints rewrite (hybrid routing, "ADR-004 required", threading.local bullets → worker-pool / XML-direct / version-assert constraints) as an explicit Epic 4 item-8 checklist entry.

### 7.6 Validation artifacts

- Add `docs/validation/M0-gate-decision.md` (or an amendment under plan section 6): one page recording the numbers, the one-build miss, the failure signature, and the CONDITIONAL PASS disposition + riders (Section 5 of this proposal is the source text).
- Fix `scripts/run_epic2_validation_isolated.py` summary output to report `ran_without_error` and `improved` (and `improved_rate_pct`) as distinct fields before the Epic 4 item-6 re-run.
- Web smoke-test debt: add 1–2 Flask test-client tests (`POST /optimize` happy path; export round-trip; `pytest -n 1`) — unfulfilled thin-slice step 10; schedule inside E3.5's window as a rider (~2h) or alongside story 3.5.4's conftest work.

---

## 8. Applied Changes (pre-approved by Alec)

### 8.1 Epic 3.5 — Substrate & Trust (lite): story breakdown (DRAFTED)

Derived 1:1 from `docs/pebo-master-plan.md` section 6, Epic 3.5 items 1–5. Item 6 ("Defer: known-gaps ratchet + trust-tier generator land with Epic 4") is a deferral note, not a story — recorded here so it is not re-planned. Epic envelope: **25–35h** (story ranges below sum to 25–35). Epic milestone: **v0.9 (internal)**. Story files created in `docs/stories/`; tracking keys use `3.5-N-slug` (no collision with epic-3 `3-N-...` keys).

| ID | Key | Title | Effort | Depends on |
|---|---|---|---|---|
| 3.5.1 | `3.5-1-pob-engine-forensics` | Submodule forensics and local-edit inventory | 4–6h | — |
| 3.5.2 | `3.5-2-submodule-repair-and-pin` | Re-establish real submodule pinned to 0.15.0; POB_VERSION.txt generated from gitlink | 6–8h | 3.5.1 |
| 3.5.3 | `3.5-3-setup-pob-script` | scripts/setup_pob.py — idempotent setup + patch auto-apply (the ONE setup command) | 4–5h | 3.5.2 |
| 3.5.4 | `3.5-4-pob-env-verify-conftest-guard` | pob_env.verify() autouse conftest enforcement (FAIL, not skip) | 4–6h | 3.5.2, 3.5.3 |
| 3.5.5 | `3.5-5-gui-baseline-harvest` | scripts/harvest_gui_baselines.py + 6–8 geared Tier-A baselines | 7–10h | 3.5.2 |

**Story 3.5.1 — Submodule forensics and local-edit inventory** (`docs/stories/story-3.5.1-pob-engine-forensics.md`)
Goal: diff the untracked `external/pob-engine` working tree against a clean upstream 0.15.0 checkout and turn every local edit into an explicit disposition (patch candidate or conscious rejection), before anything destructive touches that tree. *A kick-off run of the diff half is executing in parallel with this proposal; report lands at `docs/forensics/pob-engine-forensics-2026-07-02.md` and the story completes/ratifies its dispositions.*
Acceptance criteria:
1. A clean upstream PoB2 checkout at the 0.15.0 release commit is obtained and the exact commit hash recorded.
2. Full recursive diff vs `external/pob-engine` captured, with runtime artifacts (e.g. ModCache) classified separately from source edits.
3. Every differing source hunk dispositioned in a forensics report: adopt-as-patch / reject (restore upstream) / generated-artifact.
4. The three documented-but-unpatched edits are explicitly dispositioned: `Global.lua` nil-safety (existing patch), `ModStore.lua:444/464` nil guards, `src/Export/stub_functions.lua` (`docs/architecture/pob-engine-dependencies.md:509-513,734,766-769`).
5. No modifications to `external/pob-engine` in this story (read-only; repair is 3.5.2).

**Story 3.5.2 — Re-establish real submodule pinned to 0.15.0** (`docs/stories/story-3.5.2-submodule-repair-and-pin.md`)
Goal: convert `external/pob-engine` from an unverifiable vendored blob back into a real git submodule pinned to the 0.15.0 release commit, with every adopted local edit preserved as a patch file and `POB_VERSION.txt` generated from the gitlink — never hand-edited.
Acceptance criteria:
1. `external/pob-engine` is a real git submodule (`.git` link present, `.git/modules` entry) with HEAD == parent gitlink == the 0.15.0 release commit.
2. Working tree == pinned commit + applied `external/patches/*.patch`, nothing else; every 3.5.1 "adopt" edit exists as a patch file; every "reject" is restored to upstream.
3. `POB_VERSION.txt` is generated from the gitlink (commit + version string) by script; hand-editing is detectable (generation marker) and the four-way drift (v0.12.2 pin / gitlink `4cf3563f6` / 0.15.0 tree / 0.12.2 baselines) is resolved.
4. Existing parity baselines captured from GUI 0.12.2 are flagged stale in their metadata (not silently reused).
5. `pytest tests/unit/` and `pytest -n 1 tests/integration/` pass after repair — proving no silent dependency on a rejected edit.

**Story 3.5.3 — scripts/setup_pob.py (idempotent)** (`docs/stories/story-3.5.3-setup-pob-script.md`)
Goal: one idempotent setup command — submodule init/update + auto-apply all patches + regenerate `POB_VERSION.txt` — replacing the manual procedure documented in `docs/PRD.md:677-689` (the drift anti-pattern). The ONE setup command in README.
Acceptance criteria:
1. `python scripts/setup_pob.py` performs submodule init/update and applies every patch in `external/patches/` with `git apply --check` / `--reverse` skip-if-applied logic.
2. Idempotent: a second consecutive run succeeds and changes nothing (covered by a test or a recorded double-run).
3. Regenerates `POB_VERSION.txt` from the gitlink on every run.
4. README setup section replaces the manual checkout/echo procedure with this single command.
5. Fails loudly with actionable messages on: missing submodule, patch conflict, version mismatch.

**Story 3.5.4 — pob_env.verify() conftest enforcement** (`docs/stories/story-3.5.4-pob-env-verify-conftest-guard.md`)
Goal: enforcement that cannot be forgotten — an autouse conftest fixture that verifies the PoB environment and FAILS (not skips) parity/corpus tests when it is wrong.
Acceptance criteria:
1. `pob_env.verify()` checks: submodule is a real git repo; HEAD == gitlink == `POB_VERSION.txt` == baseline metadata version; every patch in `external/patches/` is applied.
2. The patch-marker check is **data-driven from the patch set** (one marker per patch file) — no hardcoded nil-safety marker, so removing ADR-004's patch after the Epic 4 spike is a one-edit change.
3. Autouse fixture FAILS (not skip) tests marked `parity` / `gui_parity` / corpus-validation when verification fails; plain unit tests are unaffected.
4. Negative test: a deliberately broken env (e.g. stale `POB_VERSION.txt`) demonstrably fails the parity suite.
5. Verification logic is importable by scripts (`setup_pob.py` post-check; future `release_gate.py`).

**Story 3.5.5 — GUI baseline harvester + 6–8 geared Tier-A baselines** (`docs/stories/story-3.5.5-gui-baseline-harvest.md`)
Goal: `scripts/harvest_gui_baselines.py` parses `<PlayerStat>` values from GUI-saved build XML (102 stats incl. TotalDPS — no manual transcription) and captures 6–8 geared baselines, one per v1-gated archetype: attack, spell-hit, DoT first. Mass capture (incl. minion/totem/trap) waits for the Epic 4 spike verdict.
Acceptance criteria:
1. Harvester emits baseline fixtures (stat → value) from `<PlayerStat>` elements with embedded metadata: PoB version (from generated `POB_VERSION.txt`), capture date, source file.
2. Harvested TotalDPS for `tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml` equals the known GUI value 18097.07 — proving the right fields are read.
3. 6–8 geared baselines captured covering attack, spell-hit, and DoT archetypes (minion/totem/trap deferred to Epic 4 mass capture).
4. Baselines enter via the parser/fixture path, not the web UI (the FR-1.6 gate at `src/web/routes.py:47-104` rejects some archetypes).
5. Baseline metadata version matches the pinned submodule version, or the file is explicitly marked stale (consumable by 3.5.4's verify).

### 8.2 sprint-status.yaml refresh (APPLIED — exact edits)

Applied to `docs/sprint-status.yaml` in this order:
1. Header: added pointer comments after line 1 — updated 2026-07-02 via correct-course; post-Epic-3 scope governed by `docs/pebo-master-plan.md`; `epics.md`/`PRD.md` = Epics 1–3 record only; Epic 3 as-built record = `docs/epic-3-thin-slice-plan.md`.
2. `2-9-2-spell-dot-minimalcalc-enhancement`: `review` → `done` with M0-evidence closure comment (never regresses done work; this is a progression).
3. `epic-3`: `backlog` → `contexted`, with as-built comment block (commits, context doc, no per-story files, zero-src.web-tests debt note).
4. `3-1`..`3-7`: `backlog` → `done`, each with an evidence comment.
5. `3-9`: `backlog` → `done` (done by delegation to Epic 2 timeout pass-through).
6. `3-8`, `3-10`, `3-11`: remain `backlog` with PARTIAL-fold-in disposition comments stating exactly what shipped and where the remainder lands (E3.5 hardening / Epic 4 supersession / Epic 8).
7. `3-12`: remains `backlog` with SUPERSEDED — DO NOT BUILD comment.
8. `epic-3-retrospective`: `optional`, annotated "recommended before Epic 3.5 kickoff".
9. Inserted `epic-3.5: contexted` block + five stories at `drafted` + `epic-3.5-retrospective: optional`.
10. Inserted `epic-4`..`epic-8` placeholders at `backlog`, each with a one-line scope comment pointing at the master plan.

Statuses of done work were not regressed anywhere (all 1-x, 2-x `done` entries untouched; 2-9-2 advanced).

### 8.3 Commit guidance (recommendation, not applied)

Commit this proposal + the five story files + the sprint-status refresh together with (or immediately after) the pending uncommitted `src/web` polish on `feat/epic3-ui` — suggested message: "Correct course: adopt master-plan structure in tracking; draft Epic 3.5; close 2-9-2 on M0 evidence" — then merge `feat/epic3-ui` to `main` so the adopted plan (already on main at `0b8ca40`), the shipped UI, and the corrected tracking coexist. Note `docs/HANDOFF-2026-06-29-OPTIMIZER-NOOP-FIXED.md` is untracked and should be added.
*(Executed 2026-07-02 — the combined commit on `feat/epic3-ui` includes everything above plus the §8.4 decision artifacts.)*

### 8.4 Decisions — 2026-07-02 (Alec) — APPLIED

Ruling on the forensics report's §7 open questions and this proposal's riders, all executed same-day:

1. **Patch promotion: APPROVED & EXECUTED.** `external/patches/` now holds `0001-global-lua-nil-safety.patch`, `0002-modstore-evalmod-nil-safety.patch`, `0003-calcoffence-ailment-buildup-nil-safety.patch` + `.gitattributes` (`*.patch -text`); the stale 0.12.2-cut `global-lua-nil-safety.patch` is retired (`git rm`); `external/patches/README.md` rewritten; ADR-004 gained a dated addendum. The v0.15.0-targeted drafts remain under `docs/forensics/proposed-patches/` as the forensic record.
2. **Pin target: JUMP to v0.22.0** (`860f4268299739ce9df87c4f373abe35824101cf`, latest upstream release) — overriding the forensics' repair-at-0.15.0-first recommendation. Verification performed before ruling ripples: upstream v0.22.0 **still lacks** the Global.lua nil guards (only the `#args<2` early-return is safe), so `0001` was **regenerated against v0.22.0** (apply-check PASS, sentinel ×3, LuaJIT compile OK); `0002`/`0003` apply clean on **both** tags. Ripples applied: story 3.5.2 retargeted (title/ACs/tasks + jump caveat + fallback lane at `3e1b71c9`), story 3.5.5 capture protocol → GUI v0.22.0, plan amendments at E3.5 item 2 / E4 items 1 & 3. **Known ripple: v0.22.0 ships `TreeData/0_5/`** — the Epic 4 tree bump and Epic 5 artifacts target 0_5, not 0_4.
3. **Submodule form: real git submodule** (per plan wording; unchanged from recommendation).
4. **Flask smoke-test rider: FOLDED INTO story 3.5.4** as AC-3.5.4.6 / Task 6 (+~2h; story effort 4–6h → 6–8h; epic envelope ~25–35h → ~27–37h).

---

## 9. Implementation Handoff

**Change scope classification: MAJOR** (fundamental replan) — but the replan itself was adopted on 2026-07-01; this proposal executes its mechanical propagation, which is MODERATE (backlog reorganization + doc-status pass).

| Owner | Responsibility | When |
|---|---|---|
| Alec (PO) | Review this proposal; approve/adjust the PROPOSED edit sets (Sections 7.1–7.6); confirm the M0 conditional-pass disposition | Next session |
| SM agent | Execute the approved doc-status pass (banners, dispositions, archive moves) — ~2–4h, bundleable with E3.5; run the optional epic-3 retrospective before E3.5 kickoff | With E3.5 kickoff |
| Dev agent | Execute stories 3.5.1 → 3.5.5 (3.5.1's diff half landed: `docs/forensics/pob-engine-forensics-2026-07-02.md`; patch promotion already executed per §8.4); Flask smoke tests now live inside 3.5.4 (AC-3.5.4.6) | E3.5 window |
| Dev agent (Epic 4 kickoff) | Draft ADR-005..008; entry checklist includes the five 0.0%-build triage (Section 5 rider 1); author Epic 4 BMAD epic/story definitions from plan section 6 incl. the pre-filed rejection-gate-retirement story | E4 spike kickoff |
| TEA agent | Harness summary fix (`ran_without_error` vs `improved`); owns the Epic 4 item-6 full gate re-run (both thresholds must pass) | Before/at E4 item 6 |

**Success criteria for this change:**
1. No BMAD workflow can load a superseded document without hitting a supersession banner (after the doc pass is approved and applied).
2. `docs/sprint-status.yaml` matches repo reality (verifiable today) and carries the master-plan structure forward.
3. Epic 3.5 stories are executable as drafted; E3.5 completes within the 25–35h envelope; every old Epic-3 story ID maps to exactly one disposition.
4. The M0 disposition is recorded and its riders land where scheduled (triage at E4 spike; full gate re-run at E4 item 6).

---

## 10. References

- Adopted baseline: `docs/pebo-master-plan.md` (2026-07-01, commit `0b8ca40`)
- M0 result: `docs/validation/realistic-validation-results.json` (2026-07-02)
- Epic 3 as-built: `docs/epic-3-thin-slice-plan.md`; commits `537d796`, `bc4e8e6`
- Optimizer no-op fix context: `docs/HANDOFF-2026-06-29-OPTIMIZER-NOOP-FIXED.md`
- Format precedent: `docs/sprint-change-proposal-2025-11-29.md` (and 2025-11-22 pair)
- Superseded-but-record documents: `docs/PRD.md`, `docs/epics.md`, `docs/tech-spec-epic-1.md`, `docs/tech-spec-epic-2.md`, `docs/tech-specs-summary.md`, `docs/epic-alignment-matrix.md`, `docs/research/product-brief-poe2-passive-tree-optimizer-2025-10-08.md`
- Architecture/decision surface: `docs/solution-architecture.md`, `docs/architecture/pob-engine-dependencies.md`, `docs/architecture/epic-2-optimizer-design.md`, `docs/architecture/epic-3-web-architecture.md`, `docs/decisions/ADR-003-*.md`, `docs/decisions/ADR-004-*.md`, `external/patches/`
- New stories: `docs/stories/story-3.5.1-pob-engine-forensics.md` … `story-3.5.5-gui-baseline-harvest.md`
- Forensics kick-off (parallel): `docs/forensics/pob-engine-forensics-2026-07-02.md` (landing)

---

**End of Sprint Change Proposal** — Generated by the Correct Course workflow (batch mode), 2026-07-02.
