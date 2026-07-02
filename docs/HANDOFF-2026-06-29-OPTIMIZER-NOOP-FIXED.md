# Handoff — Optimizer no-op root-caused & fixed; validation test wired

**Date:** 2026-06-29
**Session focus:** Why every Epic 2 validation showed 0% improvement → fixed → proved the optimizer works → added a real validation test.

---

## TL;DR

The optimizer had been a **structural no-op**: passive-node allocation had **zero
effect** on calculated DPS/Life, so every hill-climb neighbor tied the baseline →
0% improvement on every build, regardless of corpus or budget. Root cause was a
one-line bug. After fixing it (and a second budget bug it exposed), the optimizer
demonstrably improves a real build: **deadeye_lightning_arrow DPS 793.7 → 1471.4 (+85%)**.

⚠️ **Do NOT assume Epic 2 is validated yet.** The optimizer now finds *a* gain, but
the corpus-wide median and accuracy (parity) are still unmeasured. See Open Items.

---

## Bugs fixed

### 1. Passive mods filtered out of the calc (the no-op) — `src/calculator/MinimalCalc.lua:972`
Each allocated node object was built with `allocMode = "NORMAL"` (a string). PoB
`CalcSetup.lua:205-214` treats any `allocMode ~= 0` as a weapon-set restriction and
tags every node mod with `Condition "WeaponSet"..allocMode` → `"WeaponSetNORMAL"`,
a condition never active in the calc env, so `ModDB:Sum` discarded **all** passive
mods. Nodes were parsed (132 mods/build) and stored, then dropped at summation.
**Fix:** `allocMode = 0` (number; 0 = allocated in all weapon sets, no condition).

Verified node-sensitivity after fix (full parser, real skills/items), DPS empty→half→full:
- warrior_earthquake 1446 → 1734 → 2577; Life 1114 → 1423 → 1613
- deadeye_lightning_arrow 464 → 687 → 794
- witch_essence_drain 408 → 713 → 1276

### 2. Dual-budget swap mis-accounting — `src/optimizer/hill_climbing.py:226`
Every added node was charged to the unallocated pool, including swaps. A swap
(add 1 + remove 1) reuses the freed slot, so it should cost a **respec**, not an
unallocated point. Once the free pool hit 0, the next swap drove
`unallocated_remaining` to −1 → `unallocated_used (16) > available (15)` crash
(`budget_tracker.py:109`). This had been flagged Nov-16 but only surfaced once the
calc fix made the optimizer actually move. **Fix:** net-new adds draw from
unallocated; each removal draws from respec — matching the neighbor generator's
`can_add`/`can_swap` model.

### 3. Standalone harness stripped items/skills — `scripts/run_epic2_validation_isolated.py`
Loaded builds with `items=[], skills=[]` → degenerate ~1.5 DPS baseline → meaningless
results. **Fix:** now uses `pob_parser._extract_items/_extract_skills`. (The pytest
`tests/integration/test_epic2_validation.py` already loaded them correctly.)

---

## New test

`tests/integration/optimizer/test_optimizer_finds_improvement.py` — loads a real
build (items+skills), runs `optimize_build`, and **asserts DPS improves** (> 0,
optimized > baseline, nodes added, budget respected). This is the assertion Epic 2
never had. **Passing** (`1 passed in 160.79s` for deadeye).

Run: `pytest tests/integration/optimizer/test_optimizer_finds_improvement.py -n 1 -v -s`

---

## State

- Changes are **uncommitted** in the working tree (4 files: the 3 fixes above + new test).
- Unit suite unchanged: **7 failed / 245 passed** (the 7 are pre-existing parser /
  `_select_best_neighbor` test drift — unrelated to this work).

---

## Open items / resume here

1. **Run the full corpus** for the real Epic 2 number:
   `pytest tests/integration/test_epic2_validation.py -n 1`
   (~2-3 min/build in-process; spell/DOT route through subprocess and are slower).
   Compute median improvement vs the **≥5%** target.
2. **Re-check parity** (`pytest -m parity -n 1`): the calc fix changed DPS for any
   build with nodes, so baselines likely need re-basing against the real PoB GUI.
   Accuracy of the +85%-type numbers is unverified.
3. **Give `test_epic2_validation.py` teeth:** it still only asserts budget/time,
   never improvement — that toothlessness is how Epic 2 "passed" at 0%. Add an
   aggregate median-improvement assertion.
4. Remaining (pre-existing): 7 failing unit tests; spell builds depend on the fragile
   ADR-004 Global.lua submodule patch (`git submodule update` silently reverts it);
   Epic 3 (Flask UI) still 100% backlog.

Windows: integration tests need `pytest -n 1` (LuaJIT, ADR-003); the 0xe24c4a02
exception fires during teardown AFTER tests pass — benign. venv python:
`venv/Scripts/python.exe`.
