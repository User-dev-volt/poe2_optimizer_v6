# Story 4.9: Retire the FR-1.6 Unsupported-Build Rejection Gate

Status: drafted

> **⛔ BLOCKED — PRE-FILED, NOT ready-for-dev.** This is the sibling "parallel story" the Epic 4 entry checklist calls out. It is authored NOW (while the coupling is fresh) but MUST NOT be built until its dependencies land — retiring the gate before the Truth Engine actually optimizes minion/totem/trap builds **in production** would be strictly worse than the honest rejection. [Source: docs/sprint-status.yaml:106]

**Epic:** 4 — Truth Engine [Source: docs/pebo-master-plan.md:192-224]
**Tracking key:** `4-9-retire-unsupported-build-gate` (numbered after the 8 plan items; add under the epic-4 block in docs/sprint-status.yaml:106-107)
**Effort:** small (~4–8h) — a web-layer + parser un-gating with tests; the hard work is done by the engine items it depends on.
**Dependencies (ALL required before ready-for-dev):**
- **Story 4.2** — `FullCalcEngine` behind `build_calculator.py` (routes builds through the real engine). [Source: docs/stories/4-2-fullcalcengine-worker-pool-cooperative-cancel.md]
- **Epic 4 item 4** — FullCalc SEARCH (the `EVAL_NEIGHBORS` batch), so minion/totem builds are actually OPTIMIZED, not just reported; 4.2's two-track keeps MinimalCalc in the hot loop, and MinimalCalc cannot calc these archetypes. [Source: docs/pebo-master-plan.md:210-212]
- **Epic 4 item 6** — parity/trust for minion/totem/trap archetypes (mass baseline capture "incl. minion/totem/trap now that they calc"). [Source: docs/pebo-master-plan.md:215-219]
- **Lift the parser minion-strip** — `_extract_skills` currently SKIPS minion active gems (`pob_parser.py:648-651`, a Story 2.9 workaround), so a pure-minion build arrives with empty `skills`; that strip must be removed or the build still has nothing to calc. [Source: src/parsers/pob_parser.py:549-556,648-651]

## Story

As a **PoE2 build owner with a minion / totem / trap / mine build**,
I want **the optimizer to accept and optimize my build instead of rejecting it at import**,
so that **the Truth Engine's native support for these archetypes (which Epic 4 makes calc-correct) actually reaches me, instead of a "Not Supported (Yet!)" wall that the master plan says is obsolete once the real engine drives the pipeline**.

## Background

The FR-1.6 gate was a v1-MVP honesty measure: MinimalCalc's stubbed ModParser cannot calc minions/totems/traps, so the UI rejects them up front rather than returning garbage. The master plan §3 states that driving PoB's real engine gives **"minions, totems, traps/mines, triggers (all currently rejected at the UI)"** for free — so once FullCalc routes these archetypes in production, the gate is dead weight and should be retired. [Source: docs/pebo-master-plan.md:93-96; src/web/routes.py:47-64]

## Acceptance Criteria

1. **AC-4.9.1: The rejection gate is removed (or flag-gated OFF).** `detect_unsupported_build_type` no longer blocks the formerly-unsupported archetypes in the `POST /optimize` flow; the `unsupported_build_type` 400 path is removed or gated behind a config flag that is OFF once the dependencies are met. [Source: src/web/routes.py:67-106,192-203]
2. **AC-4.9.2: The parser minion-strip is lifted.** `_extract_skills` no longer drops `_is_minion_skill` active gems, so minion builds arrive with their real skill list; verify no downstream `KeyError`/empty-skills assumption breaks (e.g. `detect_unsupported_build_type`'s "empty skills ⇒ minion" branch is removed with the gate). [Source: src/parsers/pob_parser.py:648-651; src/web/routes.py:85-89]
3. **AC-4.9.3: UI copy is updated.** The front-end "Build Type Not Supported (Yet!)" string and its handling in `static/js/main.js` are removed/updated so a formerly-rejected build now shows the normal optimize flow. [Source: src/web/routes.py:47-52; src/web/static/js/main.js]
4. **AC-4.9.4: A formerly-rejected build now optimizes end-to-end.** Add a test (there is currently NONE asserting this path) that a minion (and a totem) build imports, optimizes, and returns a result with GUI-accurate reported stats — the inverse of the old rejection. [Source: src/web/routes.py:192-203; tests/ (no existing rejection-assertion test found)]
5. **AC-4.9.5 (hard constraint): dependency gate honored.** This story is NOT started until 4.2 + item 4 + item 6 + the parser-strip lift are in place; retiring the gate earlier routes these builds into a search path that cannot calc them. [Source: docs/pebo-master-plan.md:210-219; docs/sprint-status.yaml:106]

## Tasks / Subtasks

- [ ] **T1 (AC-4.9.1):** Remove/flag-gate the `unsupported_build_type` branch in `routes.py` (`:192-203`) and retire `detect_unsupported_build_type` + the `_NAME_UNSUPPORTED`/`_ID_UNSUPPORTED` regexes (`:63-106`) once no caller remains.
- [ ] **T2 (AC-4.9.2):** Lift the minion-strip in `pob_parser._extract_skills` (`:648-651`); re-test parse round-trip on minion fixtures.
- [ ] **T3 (AC-4.9.3):** Update `static/js/main.js` copy/handling; remove the `UNSUPPORTED_BUILD_MESSAGE` string.
- [ ] **T4 (AC-4.9.4):** Add `tests/` coverage: a minion + a totem build optimize end-to-end (Flask test-client + engine), asserting a result (not a 400).
- [ ] **T5 (AC-4.9.5):** Confirm dependencies are merged; `setup_pob.py` exit 0; unit + `-n 1` integration green.

## Dev Notes

- **Do NOT resume as Epic 3.** This is Epic 4 scope — it is a direct consequence of the Truth Engine, and only makes sense once the engine calcs these archetypes.
- **Trigger builds were never gated** (support-gem-driven, too false-positive-prone), so nothing changes for them. [Source: src/web/routes.py:60-64]
- **Watch the empty-skills coupling:** the gate treats an empty `skills` list as a minion build (`routes.py:85-89`) precisely because the parser strips minion gems. Removing the strip (T2) and the gate (T1) must happen together, or a minion build slips through with no skills and computes nothing.
- **Round-trip/export:** confirm minion/totem builds export a lossless PoB code (the item-7 round-trip gate covers this generally, but spot-check here).

### References

- [Source: docs/pebo-master-plan.md:93-96 — real engine calcs minions/totems/traps/triggers "all currently rejected at the UI"]
- [Source: docs/pebo-master-plan.md:210-219 — item 4 (FullCalc search) + item 6 (archetype parity) dependencies]
- [Source: src/web/routes.py:47-106,192-203 — the FR-1.6 gate to retire]
- [Source: src/web/static/js/main.js — front-end unsupported-build copy/handling]
- [Source: src/parsers/pob_parser.py:549-556,648-651 — minion-strip workaround to lift]
- [Source: docs/sprint-status.yaml:106 — epic-4 entry checklist "pre-filed story to retire the FR-1.6 rejection gate"]

## Dev Agent Record

### Context Reference

- Pre-filed alongside Story 4.2 via BMAD create-story (ultracode), 2026-07-03, from the epic-4 entry checklist. Held at `drafted` (BLOCKED) until its engine dependencies land.

### Agent Model Used

claude-opus-4-8 (Claude Code, BMAD create-story workflow)

### Completion Notes List

### File List

## Change Log

**2026-07-03** — Story pre-filed (BLOCKED/drafted) via BMAD create-story (ultracode)
- Captures the routes.py:47-106 gate ↔ main.js copy ↔ pob_parser.py:648-651 minion-strip coupling while fresh.
- Dependency-gated behind 4.2 + item 4 + item 6 + parser-strip lift; NOT ready-for-dev.
