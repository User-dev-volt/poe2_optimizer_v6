# ADR-008: Passive-tree version bump (0_3 → 0_4 → 0_5) + version assert

## Status
Proposed (Epic 4) — STUB drafted from the Story 4.1 spike. Ratify at Epic 4 item 3.

## Context

`src/calculator/passive_tree.py` hardcodes the default tree version `"0_3"`
(`load_passive_tree`). But builds carry their own `targetVersion`, and PoB's
PassiveSpec loads/migrates trees per-build: in Story 4.1 the real driver loaded
`0_4` (deadeye), `0_2` (others), and — at v0.22.0 — `0_5`, all while parity held.
The Python-side `0_3` default is therefore stale relative to what the engine
actually uses.

Two independent findings from Story 4.1:

1. **M0 triage (Task 10):** the five `no_valid_neighbors@iter0` builds are NOT a
   tree-version problem — `miss@0_3 == miss@0_4` for every build (a 0_3→0_4 bump
   recovers no nodes; the residual missing nodes are class-start/ascendancy nodes
   absent from the Python loader's graph in BOTH versions). Root cause is the
   `activeSpec` parse gap (ADR-007), not tree version.
2. **v0.22.0 boot (Task 9):** `860f4268` (v0.22.0) boots under the real driver,
   its `CalcSetup` satisfies `CollectGrantedPassiveNodesFromItems` (the exact
   blocker MinimalCalc could not), and `TreeData/0_5` loads. Cross-version DPS
   differs (deadeye 27607.88 vs v0.15.0 23003.19) — so **v0.22.0 parity requires
   fresh v0.22.0 GUI re-capture; v0.15.0 baselines must NOT be asserted against it.**

## Decision

- Bump the Python-side default tree version 0_3 → 0_4 now (matches what the
  engine loads at the v0.15.0 pin), and → 0_5 when the deferred v0.22.0 engine
  jump lands (Epic 4).
- Add a **version assert**: the tree version the Python side assumes must match
  `external/POB_VERSION.txt` / the version the engine actually loaded, failing
  loudly on mismatch (no silent 0_3 fallback).
- Prefer PoB's own PassiveSpec for node membership (ADR-007) over the standalone
  Python tree graph wherever possible.

## Consequences

- The v0.22.0 jump (already in submodule history at `860f4268`, ships `0_5`) is
  de-risked and can land in Epic 4 with a fresh GUI baseline re-capture.
- `passive_tree.py`'s standalone graph remains for read-only analysis (e.g.
  triage), with the version-assert guarding against drift.

[Source: docs/stories/4-1-truth-engine-driver-spike.md (Tasks 9/10);
 src/calculator/passive_tree.py:242,246-247,267; docs/sprint-change-proposal-2026-07-02.md:386-392]
