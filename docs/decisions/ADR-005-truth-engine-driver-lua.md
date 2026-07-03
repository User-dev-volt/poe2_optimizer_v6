# ADR-005: Truth Engine — headless `driver.lua` over PoB's real calc chain

## Status
Accepted (Epic 4 item 2, Story 4.2, 2026-07-03). The spike-grade `driver.lua`
graduated into production behind `FullCalcEngine` / `build_calculator.calculate_build_stats(engine="full")`;
the deadeye anchor `23003.185361227` is pinned ±0.1% THROUGH the FullCalcEngine
seam (`tests/integration/test_full_calc_engine.py`). `driver.lua` stays FROZEN
(the `EVAL_NEIGHBORS`/`APPLY_MOVE` stubs remain stubs; their batch consumer is
item 4).

## Context

MinimalCalc (`src/calculator/MinimalCalc.lua`) stubs PoB's `ModParser`, `xml`,
`base64`, and `sha1`, and consequently computes ~4% of GUI DPS on geared builds
(the coverage gap; see docs/validation/). Epic 4 replaces it with a **Truth
Engine** that drives PoB's REAL `Launch → Main → Data → ModParser → CalcSetup /
CalcPerform / CalcOffence / CalcDefence` pipeline headless.

Story 4.1 (the go/no-go spike) disproved the earlier "architecturally
impossible" verdict:

- **Boot:** `driver.lua` (modelled on `HeadlessWrapper.lua`, OUTSIDE the
  submodule) boots the full chain under embedded `lupa.luajit21` with **no
  boot-time SEH `0xe24c4a02`**. The fix is a native-module `package.loaded`
  pre-stub — the **minimal set is `{arg={}, lua-utf8 (with len), lcurl.safe}`**,
  determined empirically. `base64/sha1/xml/sha2/dkjson` are pure-Lua in
  `runtime/lua/` and MUST load REAL (the inverse-of-MinimalCalc rule; stubbing
  them reproduces the gap).
- **Parity:** all 6 Tier-A v0.15.0 GUI baselines match at **±0.000%** across the
  attack / spell-hit / DoT archetypes (deadeye 23003.185361227 exact), read from
  `build.calcsTab.mainOutput[stat]`.

## Decision

Ship the Truth Engine as a standalone `src/calculator/driver.lua` that MODELS
(does not fork/edit) `HeadlessWrapper.lua`, seeds the minimal native pre-stub
block before `dofile("Launch.lua")`, and exposes a small command surface
(`LOAD_BUILD`, `GET_STATS`, and — Epic 4 item 2/4 — `EVAL_NEIGHBORS`,
`APPLY_MOVE`). Read stats from `mainOutput`, branching the DPS metric on
archetype (attack/spell-hit → `TotalDPS`; DoT → `TotalDot`; minion/totem →
`FullDPS`). Retire MinimalCalc to a fixture (Epic 4 item 8).

## Consequences

- The engine tree stays read-only; `driver.lua` lives outside the submodule so
  `pob_env.verify()` invariant (e) is never tripped.
- `FullCalcEngine` sits behind `build_calculator.py` (Epic 4 item 2) — the spike
  keeps `driver.lua` standalone (AC-4.1.10).
- Lane decision: see ADR-006. Patch necessity: see ADR-004 (spike outcome =
  drop-candidate ×3). Tree/version: see ADR-008.

[Source: docs/stories/4-1-truth-engine-driver-spike.md; src/calculator/driver.lua;
 external/pob-engine/src/HeadlessWrapper.lua; docs/pebo-master-plan.md §3/§6]
