# ADR-007: XML-direct build loading via PoB's own PassiveSpec (`convert=true`)

## Status
Accepted (Epic 4 item 2, Story 4.2, 2026-07-03). `FullCalcEngine` loads builds
XML-direct into PoB's own PassiveSpec via the mutated-`BuildData` → patched-XML
seam below; the deadeye seam parity holds ±0.1%. (Multi-`<Spec>` reporting stays
FENCED off until the item-3 `activeSpec` READ fix — see Consequences.)

## Context

Builds can be fed to the engine two ways: (a) re-encoded through our
`parse_pob_code` / `BuildData` path, or (b) as the ORIGINAL PoB XML read straight
from the saved `.xml`, handed to PoB's own `main:SetMode("BUILD", …, xmlText)`.

Route (a) forces us to reimplement tree-version migration, weapon-set handling,
and dual-ascendancy parsing — and our own `_extract_passive_nodes`
(`pob_parser.py:391-393`) has an `activeSpec` bug that returns an EMPTY node set
for multi-`<Spec>` builds (the Story 4.1 Task 10 root cause of the five
`no_valid_neighbors`-at-iteration-0 builds).

Story 4.1 fed all builds as XML-direct (route b). PoB's own `PassiveSpec`
(`convert=true`) handled tree migration for free — the deadeye auto-loaded
`TreeData/0_4`, other builds `0_2`, and (at v0.22.0) `0_5` — while parity held at
±0.000%. The five multi-`<Spec>` builds that break our Python parser load
correctly through PoB's PassiveSpec (right node counts; `lich_storm_mage_90`
computes 188,475 FullDPS vs 0 under MinimalCalc).

## Decision

Load builds XML-direct through PoB's `PassiveSpec (convert=true)`. Do NOT route
imports through `parse_pob_code` / `BuildData` re-encoding for the Truth Engine.
Fix or retire the buggy `_extract_passive_nodes` where the Python side still
needs a node set (use the `activeSpec`-aware pattern at `pob_parser.py:232-244`).

## Consequences

- Free tree-migration / weapon-set / dual-ascendancy handling; no reimplementation.
- Eliminates the multi-`<Spec>` `no_valid_neighbors@iter0` class of failures.
- The Python `BuildData` model is no longer on the calc-load path (kept for UI /
  encode round-trip only).
- **Mutated-`BuildData` → patched-XML seam (added at item 2, Story 4.2).** The
  optimizer mutates only `BuildData.passive_nodes` (via `dataclasses.replace`), so
  the Truth Engine serializes each reported build back to XML with a single shared
  primitive `patch_passive_nodes_to_xml(source_xml, nodes, main_socket_group)`
  (extracted from `encode_pob_code`): it rewrites the active `Spec @nodes` AND —
  G2 — the `Build @mainSocketGroup` (which `resolve_main_socket_group` mutates in
  Python but `encode_pob_code` never wrote), then feeds the patched XML XML-direct
  to the worker. `BuildData` carries the original `source_xml` (stamped by
  `parse_pob_code`); neighbors inherit it for free. An IN-WORKER node-delta
  (`APPLY_MOVE`, avoiding a full `LOAD_BUILD` per neighbor) is DEFERRED to item 4 —
  item 2 only reports the two loop-boundary numbers, so a full patched-XML load per
  reported build is O(1) and acceptable.
- **Multi-`<Spec>` fence (G3).** Until the item-3 `activeSpec` READ fix lands,
  `_extract_passive_nodes` returns an EMPTY set for a list-typed `<Spec>`, so
  `BuildData.is_multi_spec` gates FullCalc OFF for those builds (else the patch
  would write `@nodes=""` and report an unallocated tree); reporting falls back to
  MinimalCalc. MANDATORY, not a nicety.

[Source: docs/stories/4-1-truth-engine-driver-spike.md (Tasks 9/10);
 src/parsers/pob_parser.py:232-244,391-393; docs/pebo-master-plan.md:112-116]
