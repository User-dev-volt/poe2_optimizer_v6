# Story 3.5.5: GUI Baseline Harvester + 6–8 Geared Tier-A Baselines (attack, spell-hit, DoT first)

Status: done

**Epic:** 3.5 — Substrate & Trust (lite) → milestone v0.9 (internal) [Source: docs/pebo-master-plan.md:168-184]
**Tracking key:** `3.5-5-gui-baseline-harvest` (docs/sprint-status.yaml:98)
**Effort:** 7–10h [Source: docs/sprint-change-proposal-2026-07-02.md section 8.1]
**Dependencies:** 3.5.2 (pinned submodule + *generated* `POB_VERSION.txt` — the harvester reads it for baseline metadata; active pin = **v0.15.0 `3e1b71c9`** after the 2026-07-02 v0.22.0 jump-and-fallback — always capture at whatever `POB_VERSION.txt` says at capture time). Harvester implementation and the golden test (Tasks 1–3) may start in parallel with 3.5.3/3.5.4; committing Tier-A fixtures (Task 4) requires 3.5.2 done. Story 3.5.4 consumes this story's metadata convention (see AC-3.5.5.5).

## Story

As the **owner of PEBO's parity evidence**,
I want **`scripts/harvest_gui_baselines.py` to extract every GUI-computed `<PlayerStat>` value (102 stats incl. TotalDPS) from PoB-GUI-saved build XML with zero manual transcription, and a first committed set of 6–8 geared baselines covering the attack, spell-hit, and DoT archetypes**,
so that **Epic 4's parity work starts against real geared-build truth instead of the current naked-build baselines that "prove nothing" (naked DPS ≈ 0.18–1.46; on the geared deadeye fixture our engine reports ~4% of the GUI's DPS — 793.7 vs 18097)**.

## Acceptance Criteria

1. **AC-3.5.5.1:** Harvester emits baseline fixtures with embedded metadata
   - `scripts/harvest_gui_baselines.py` parses all `<PlayerStat stat="..." value="..."/>` elements from a GUI-saved build XML and emits one fixture (JSON) per build: a stats map (raw stat name → numeric value; names copied verbatim, incl. colon-named stats such as `Spec:LifeInc`) plus a metadata block
   - Metadata contains at minimum: PoB version (commit hash + human-readable version, read from the *generated* `POB_VERSION.txt` of stories 3.5.2/3.5.3 — never typed by hand), capture date, source XML path, source XML SHA-256, archetype tag, stale flag (see schema sketch in Dev Notes)
   - Zero manual transcription: no stat renaming, no curated subset, no hand-copied numbers (contrast the predecessor `tests/fixtures/parity_builds/gui_baseline_stats.json`: a hand-curated ~12-stat snake_case subset, `pob_version: "0.12.2"`, recorded 2025-10-21)

2. **AC-3.5.5.2:** Correctness proof — golden test on the deadeye fixture
   - Harvested `TotalDPS` for `tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml` equals the known GUI value 18097.07 — asserted against the raw XML value `18097.067904221` (deadeye_lightning_arrow_76.xml:11) so the test proves exact value round-trip, not just 2-dp agreement
   - 2–3 additional spot-checked stats match the XML verbatim, e.g. `Life` = 1059 (:49), `CritChance` = 5.5 (:8), `AverageDamage` = 9426.49885 (:4)
   - The stats map contains exactly the fixture's 102 `<PlayerStat>` entries (count asserted; duplicate stat names rejected or flagged)

3. **AC-3.5.5.3:** 6–8 geared Tier-A baselines captured and committed
   - Fixtures committed for 6–8 geared builds covering **at least** the attack, spell-hit, and DoT archetypes — one per v1-gated archetype first, then fill to 6–8 (plan wording: "one per v1-gated archetype: attack, spell-hit, DoT first")
   - Each source XML was **saved by PoB GUI at the same release as the ACTIVE 3.5.2 pin** (v0.15.0 after the 2026-07-02 fallback; confirm against the generated `POB_VERSION.txt` before capturing — if Epic 4's deferred v0.22.0 jump landed first, capture there) — mixing capture and pin versions recreates the four-way drift E3.5 exists to kill
   - Archetype is recorded in each fixture's metadata so Epic 4's Tier-A/B assignment is a lookup, not archaeology
   - Minion/totem/trap capture is explicitly deferred to Epic 4 item 6 mass capture (20–24 builds, after the spike verdict) with a written note in the fixtures directory README — do not capture them here

4. **AC-3.5.5.4:** Baselines enter via the parser/fixture path, not the web UI
   - The harvester is a CLI over saved `.xml` files — single file or directory — usable for any archetype; the web UI is not part of the flow (the FR-1.6 gate at `src/web/routes.py:47-104` rejects minion/totem/trap builds by design; its retirement is a pre-filed **Epic 4** story, not this one)
   - The harvester never imports `src.calculator` (engine-agnostic by construction — it reads GUI XML only; contrast `scripts/generate_baseline_stats.py`, which imports `src.calculator.build_calculator` to produce *engine-computed* corpus stats)

5. **AC-3.5.5.5:** Version-match / stale convention is machine-readable
   - Each baseline's metadata version either matches the pinned submodule version (gitlink / generated `POB_VERSION.txt`) or the fixture is explicitly marked `"stale": true`
   - The convention is consumable without parsing prose: 3.5.4's `pob_env.verify()` check (d) ("baseline metadata versions match or are explicitly stale-flagged") and the Epic 4 parity harness / `release_gate.py` (stale-artifact refusal) read the same fields
   - The stale semantics agree with 3.5.2 AC4 (0.12.2-era baselines flagged stale rather than silently reused)

## Tasks / Subtasks

- [x] Task 1: Implement harvester CLI (AC: 3.5.5.1, 3.5.5.4)
  - [x] Subtask 1.1: `scripts/harvest_gui_baselines.py` with argparse: positional input path(s) (XML file or directory), `--output-dir` (default: the gui-baselines fixture dir), `--archetype` (recorded in metadata), `--force`
  - [x] Subtask 1.2: Parse with stdlib `xml.etree.ElementTree` — flat attribute extraction of `<PlayerStat>`; values parsed as floats at full precision (see Project Structure Notes for the xmltodict variance rationale)
  - [x] Subtask 1.3: Read PoB version (commit + version string) from the generated `POB_VERSION.txt`; if the file is missing or lacks the 3.5.2 generation marker, refuse to stamp a version (harvest continues only with `--force`, emitting `"stale": true` + a warning)
  - [x] Subtask 1.4: Refuse to overwrite an existing fixture unless `--force`
  - [x] Subtask 1.5: Guard: no `src.calculator` (or Lua/lupa) imports anywhere in the script
- [x] Task 2: Define + document the baseline fixture JSON schema (AC: 3.5.5.1, 3.5.5.5)
  - [x] Subtask 2.1: Metadata block + stats map with a `schema_version` field (sketch in Dev Notes); one JSON file per build
  - [x] Subtask 2.2: Document the schema in the script docstring and in `tests/fixtures/gui_baselines/README.md` (incl. the minion/totem/trap deferral note per AC-3.5.5.3)
  - [x] Subtask 2.3: Agree field names with story 3.5.4 (verify reads them) and record the stale-flag semantics shared with 3.5.2 AC4
- [x] Task 3: Golden test on the deadeye fixture (AC: 3.5.5.2)
  - [x] Subtask 3.1: Unit test `tests/unit/test_harvest_gui_baselines.py`: harvest `deadeye_lightning_arrow_76.xml`; assert `TotalDPS == 18097.067904221`, spot-check `Life`/`CritChance`/`AverageDamage`, assert 102 stats total
  - [x] Subtask 3.2: Negative cases: XML without `<PlayerStat>` (clear error), duplicate stat name (rejected/flagged), overwrite without `--force` (refused)
  - [x] Subtask 3.3: Pure-Python test — no LuaJIT, runs under plain `pytest tests/unit/`
- [x] Task 4: Capture, harvest, and commit 6–8 geared baselines (AC: 3.5.5.3, 3.5.5.4)
  - [x] Subtask 4.1: Source candidate geared builds — own builds and/or community codes (e.g. via `scripts/fetch_pobb_in_builds.py`) covering attack, spell-hit, DoT first
  - [x] Subtask 4.2: Import each into PoB GUI **at the pinned release (v0.15.0 today — read `POB_VERSION.txt`, don't assume)**, let it recalculate, and SAVE the build XML from that GUI — the save is what stamps `<PlayerStat>` values at the pinned version (a pobb.in XML alone carries the *uploader's* unknown-version stats; see Dev Notes)
  - [x] Subtask 4.3: Run the harvester over the saved XMLs with `--archetype`; commit source XML + fixture JSON pairs
  - [x] Subtask 4.4: Write the deferral note (minion/totem/trap → Epic 4 mass capture) in the fixtures README
- [x] Task 5: Wire metadata into the stale-flag convention from 3.5.2/3.5.4 (AC: 3.5.5.5)
  - [x] Subtask 5.1: Confirm 3.5.4's `pob_env.verify()` can evaluate version-match/stale from the fixture files alone (no harvester import needed); adjust field names if 3.5.4 landed first
  - [x] Subtask 5.2: Test: a fixture whose metadata version ≠ current pin and lacking `"stale": true` is detectably invalid (the check itself may live in 3.5.4's suite — coordinate, don't duplicate)

## Dev Notes

- **The version-attestation problem is the core design constraint.** GUI-saved XML does NOT embed the app version that computed it: the root element is bare `<PathOfBuilding2>` (deadeye_lightning_arrow_76.xml:2) and `Build@targetVersion="0_1"` is the *passive-tree* version, not the app version. The harvester therefore stamps the pinned version from the generated `POB_VERSION.txt`, and the capture protocol (Task 4.2) is what makes that stamp true. Today's `POB_VERSION.txt` is the hand-written v0.12.2 pin (commit `69b825bda`, pinned 2025-10-12) — this story must consume the *generated* replacement from 3.5.2 AC3, which is why 3.5.2 is a hard dependency for Task 4.
- **Existing corpus XMLs are harvester food, not Tier-A truth.** All 15 files in `tests/fixtures/realistic_builds/` contain `<PlayerStat>` blocks, but their values were computed by whatever PoB version the original uploader ran (pobb.in provenance, pre-pin). They exercise the harvester (the deadeye golden test) — any fixture harvested from them must carry `"stale": true` (or simply not be committed as a baseline). The 6–8 committed Tier-A candidates come from fresh GUI saves at the pinned release only (v0.15.0 after the 2026-07-02 fallback).
- **Scope guards (v1 NOT-list and plan deferrals — do not invent scope):**
  - Mass capture (20–24 builds incl. minion/totem/trap) is Epic 4 item 6, after the spike verdict — not here
  - Known-gaps ratchet + trust-tier generator are explicitly deferred to Epic 4 (plan Epic 3.5 item 6: "they'd measure MinimalCalc, which Epic 4 deletes") — this story produces fixtures, not gates
  - No GGG character import (NOT-list), no web-UI ingestion path, no retirement of the FR-1.6 gate (pre-filed Epic 4 story per change proposal section 7.1-E)
  - `<MinionStat>` elements exist in the corpus (72 across files) — out of scope; the schema may reserve a key but the harvester emits `<PlayerStat>` only
- **Why this story exists (risk traceability):** plan risk #5 (geared parity fails → tolerance-loosening temptation) is mitigated by Tier-A hard-gating, which needs these geared baselines; risk #7 (patch churn invalidates baselines) requires artifacts to "embed version+hash" — exactly this metadata; the standing patch-day workstream's `update_pob.py` must be able to "print stale Tier-B baselines needing GUI re-capture", which is only possible if staleness is machine-readable (AC-3.5.5.5).
- **Fixture schema sketch** (finalize in Task 2; field names are the contract with 3.5.4):

  ```json
  {
    "schema_version": 1,
    "metadata": {
      "pob_version": {"commit": "<40-hex gitlink>", "version": "0.15.0"},
      "captured": "YYYY-MM-DD",
      "source_xml": "tests/fixtures/gui_baselines/xml/<name>.xml",
      "source_sha256": "<hex>",
      "archetype": "attack | spell-hit | dot",
      "stale": false
    },
    "stats": {"TotalDPS": 18097.067904221, "Life": 1059, "...": 0}
  }
  ```

- **Testing standards:** golden test is unit-tier (pure Python, no LuaJIT — no `-n 1` requirement); follow existing unit-test layout under `tests/unit/`. The committed baseline fixtures themselves are data, validated by 3.5.4's verify and consumed by the Epic 4 parity harness.

### Project Structure Notes

- New files: `scripts/harvest_gui_baselines.py`; `tests/fixtures/gui_baselines/` (one `<build>.baseline.json` per build + the committed source XML + `README.md` with schema and deferral note); `tests/unit/test_harvest_gui_baselines.py`
- One-JSON-per-build (vs the predecessor's monolithic `gui_baseline_stats.json`) so per-fixture stale flags and per-build Tier assignment stay trivial for 3.5.4 and the Epic 4 harness (which iterate a directory)
- **Detected variance (with rationale):** the change-proposal spec asks for "pure-stdlib XML parsing consistent with `src/parsers/`", but `src/parsers/xml_utils.py:6` actually uses third-party `xmltodict` (pinned at `requirements.txt:5`). Resolution: use stdlib `xml.etree.ElementTree` — the harvest is flat attribute extraction with no need for document round-tripping, and the script stays standalone-runnable; "consistent with `src/parsers/`" is read as consistency of convention (GUI XML is the source of truth), not of library
- The harvester is a script, not a `src/` module — it must stay importable-free of the calculator stack so it survives Epic 4's MinimalCalc retirement untouched

### References

- [Source: docs/pebo-master-plan.md:180-182 — Epic 3.5 item 5: harvest `<PlayerStat>` from GUI-saved XML (102 stats incl. TotalDPS, no manual transcription); capture 6–8 geared baselines, one per v1-gated archetype (attack, spell-hit, DoT first); mass capture waits for the spike verdict]
- [Source: docs/pebo-master-plan.md:60-62 — section 2 item 5: naked-build baselines "prove nothing"; geared deadeye reads ~4% of GUI DPS (793.7 vs `<PlayerStat>` TotalDPS 18097)]
- [Source: docs/pebo-master-plan.md:357-358 — Appendix A: PlayerStat harvesting evidence, deadeye fixture, 102 GUI-computed stats incl. TotalDPS 18097.07]
- [Source: docs/pebo-master-plan.md:177-179 — Epic 3.5 item 4: `pob_env.verify()` checks "HEAD == gitlink == POB_VERSION == baseline metadata version" — the consumer of AC-3.5.5.5]
- [Source: docs/pebo-master-plan.md:183-184 — Epic 3.5 item 6: ratchet + trust-tier generator deferred to Epic 4]
- [Source: docs/pebo-master-plan.md:204-208 — Epic 4 item 6: mass capture (20–24 builds incl. minion/totem/trap), parity v2 with Tier A hard-gated / Tier B ratcheted, `release_gate.py` stale-artifact refusal]
- [Source: docs/pebo-master-plan.md:310-321 — section 8 risks #5 (tolerance-loosening) and #7 (patch churn; artifacts embed version+hash); :275-279 standing patch-day workstream prints stale baselines needing GUI re-capture]
- [Source: docs/pebo-master-plan.md:332 — section 9 immediate action 4: "Harvest script + 6–8 geared Tier-A baselines"]
- [Source: docs/sprint-change-proposal-2026-07-02.md section 8.1 — story 3.5.5 definition, effort 7–10h, dependency on 3.5.2; section 4.4 — FR-1.6 gate blocks UI ingestion of some archetypes, use the parser/fixture path]
- [Source: tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml:11 — `<PlayerStat stat="TotalDPS" value="18097.067904221"/>`; :4 AverageDamage, :8 CritChance, :49 Life; 102 `<PlayerStat>` elements total; :2 bare `<PathOfBuilding2>` root (no app version attribute)]
- [Source: src/web/routes.py:47-104 — FR-1.6 detect-and-reject gate ("Coming in V2" copy at :49-52, classifier `detect_unsupported_build_type` at :67)]
- [Source: tests/fixtures/parity_builds/gui_baseline_stats.json — predecessor GUI baseline (0.12.2, 2025-10-21, hand-curated subset), stale-flagged by 3.5.2 AC4]
- [Source: scripts/generate_baseline_stats.py — engine-computed corpus baselines (imports `src.calculator.build_calculator`); the anti-pattern this harvester must not repeat]
- [Source: docs/stories/story-3.5.2-submodule-repair-and-pin.md — AC3 generated `POB_VERSION.txt` with generation marker; AC4 stale-flagging of 0.12.2 baselines]
- [Source: docs/stories/story-3.5.4-pob-env-verify-conftest-guard.md — AC1(d) baseline metadata version check; Dev Notes name this story's harvester as the metadata source]

## Dev Agent Record

### Context Reference

### Agent Model Used

claude-fable-5

### Debug Log References

### Completion Notes List

- Tasks 1, 2, 3 and 5 implemented; **Task 4 (GUI capture at the pinned release) is deliberately untouched** — it needs a human at the PoB PoE2 GUI v0.15.0 (`3e1b71c9`, per the generated `external/POB_VERSION.txt`). No baselines were fabricated; `tests/fixtures/gui_baselines/` currently holds only `README.md`.
- **Field-name contract (Subtask 2.3/5.1):** story 3.5.4 landed first, so the Dev Notes schema sketch was adjusted to what `src/pob_env.py` `verify()` check (d) actually reads: top-level `_metadata` (not `metadata`), `_metadata.pob_version` as a plain **string** exactly equal to the pinned manifest version (not the sketched `{"commit", "version"}` object — the commit moved to a sibling `_metadata.pob_commit`), and `_metadata.stale` as a JSON boolean. `stale_reason` accompanies every `stale: true` (3.5.2 AC4 convention; verify() does not parse it).
- Harvester is stdlib-only (argparse / xml.etree.ElementTree / hashlib / json / pathlib / re / datetime); its single project import is `src.pob_env` for the shared `GENERATED_MARKER` + `VERSION_FILE` constants (coordinate-don't-duplicate; the source-guard unit test proves no `src.calculator`/`lupa` imports via AST walk).
- `--force` carries both story meanings: overwrite an existing fixture, and harvest without a usable generated `POB_VERSION.txt` (fixture then gets `stale: true`, `pob_version`/`pob_commit` null — never fabricated — plus a warning). Added `--stale-reason TEXT` so corpus-provenance harvests (e.g. `realistic_builds/`) can be marked honestly stale per the Dev Notes requirement.
- Exit codes follow the `setup_pob.py` convention (documented in the module docstring): 0 ok, 1 internal, 2 usage (argparse), 3 input problem (missing path/no XML/malformed/zero `<PlayerStat>`/duplicate stat names/non-numeric value), 4 version attestation refused without `--force`, 5 output exists without `--force`. Exit 3 also covers non-finite (nan/inf) stat values and same-stem input collisions (post-review fix batch).
- Golden test proves exact round-trip: `TotalDPS == 18097.067904221` (raw digits also asserted verbatim in the serialized JSON), `Life`/`CritChance`/`AverageDamage` spot-checks, exactly 102 stats (count re-verified against the fixture), colon-named `Spec:LifeInc` kept verbatim, `<MinionStat>` ignored.
- Task 5 contract tests run the REAL `pob_env.verify()` against an env double with a freshly harvested fixture at the `BASELINE_METADATA_FILES[0]` path: fresh fixture GREEN, version-mismatch-without-stale RED on (d), stale-flagged mismatch GREEN, and a `--force` unversioned fixture shown to be un-committable (fails (d) even when stale). `BASELINE_METADATA_FILES` itself is NOT extended yet — that happens in Task 4 when real fixtures are committed (extending it to not-yet-existing files would turn the guard red repo-wide).
- Suite: `python -m pytest tests/unit/ -q` → 334 passed (303 pre-existing + 31 new).
- **Post-review fix batch (same day):** adversarial review (3 verifier agents, 0 blocker/major) surfaced 5 distinct minors; 4 applied — same-stem input collision now refused up front (`EXIT_INPUT`, was silent clobber under `--force`), non-finite stat values (nan/inf) rejected + `json.dumps(..., allow_nan=False)` belt (RFC 8259 strictness), `is_file()` filter so a directory named `*.xml` can't crash the reader, and a **ratchet test** (`test_every_committed_baseline_fixture_is_guarded`) that fails the suite if a committed `*.baseline.json` is missing from `pob_env.BASELINE_METADATA_FILES` — converting the Task-4 allowlist extension from a documented convention into an enforced one. Fifth minor (check (d) globbing the fixture dir itself) deferred as an Epic 4 hardening option.
- **Task 4 capture (2026-07-02 evening, by Alec):** official `PathOfBuildingCommunity-PoE2-Portable.zip` v0.15.0 (manifest `<Version number="0.15.0">`, GitHub release asset) installed to `D:\Tools\PoB2-0.15.0-official\` after two false starts (a straight file-move that bypassed the GUI — corpus files restored from git; and a 3 MB runtime-only extract that couldn't boot). Six corpus builds re-saved in that GUI (fresh `<PlayerStat>` stamps verified: every save differs from its pobb.in-provenance original) and harvested: deadeye_lightning_arrow_76 (attack, TotalDPS 23003.19), ritualist_lightning_spear_96 (attack, 407381.40), titan_falling_thunder_99 (attack, 13817.27 — first save had no main skill selected, re-saved), warrior_earthquake_89 (attack, 49262.05), bloodmage_remnants_95 (spell-hit, 6906.47 — first save had all-zero DPS, re-saved with main skill selected), witch_essence_drain_86 (dot, TotalDot 23752.22, TotalDPS 0 as expected for a DoT build). AC-3.5.5.3 count: 6 of 6–8, all three v1-gated archetypes covered. A 7th candidate (friend's Sorceress Chronomancer ignite import code) was skipped — built on a newer PoB, declined for 0.15.0 capture.
- **Archetype depth caveat for Epic 4:** spell-hit and dot are single-sample (bloodmage 6.9k DPS is a shallow spell-hit anchor). Epic 4 item 6 mass capture (20–24 builds) should deepen both before Tier-A hard-gating leans on them.
- `pob_env.BASELINE_METADATA_FILES` extended to all 7 baseline files; env doubles (test_pob_env.make_env_double) now stub non-subject allowlist entries stale-flagged — the only (d)-neutral state in manifest-less doubles — so future allowlist growth cannot break the doubles. Suite 334 green; live `verify()` GREEN across all seven.

### File List

- `scripts/harvest_gui_baselines.py` (new)
- `tests/fixtures/gui_baselines/README.md` (new)
- `tests/unit/test_harvest_gui_baselines.py` (new)
- `docs/stories/story-3.5.5-gui-baseline-harvest.md` (this file: status, task ticks, Dev Agent Record, Change Log)

## Change Log

**2026-07-02 (late)** — Task 4 complete: 6 Tier-A baselines captured at v0.15.0; story DONE
- Alec captured 6 geared builds in the official v0.15.0 portable GUI (attack ×4, spell-hit ×1, dot ×1); fixtures harvested, committed with source XMLs, and allowlisted in `pob_env.BASELINE_METADATA_FILES` (7 files total under check (d))
- Two captures required a second save (bloodmage: zero-DPS first save; titan_falling_thunder: no main skill selected) — final fixtures carry real DPS numbers
- Env doubles updated to stub non-subject allowlist entries (stale-flagged); suite 334 green, live verify() GREEN
- Status: in-progress -> done

**2026-07-02** — Tasks 1, 2, 3, 5 implemented (harvester + schema + golden/contract tests); Task 4 awaiting GUI capture
- `scripts/harvest_gui_baselines.py`: stdlib-only CLI harvesting every `<PlayerStat>` verbatim into one `<name>.baseline.json` per build; version attestation from the generated `POB_VERSION.txt` (refuses hand-written/missing without `--force`); dual-meaning `--force`; `--stale-reason` for corpus-provenance harvests; setup_pob-style exit codes
- Schema finalized against the SHIPPED 3.5.4 verifier: `_metadata` / string `pob_version` / boolean `stale` (+ `pob_commit`, `captured`, `source_xml`, `source_sha256`, `archetype`, `stale_reason`), documented in the script docstring and `tests/fixtures/gui_baselines/README.md` (incl. minion/totem/trap deferral note to Epic 4 item 6)
- `tests/unit/test_harvest_gui_baselines.py`: 31 pure-Python tests — deadeye golden round-trip (TotalDPS 18097.067904221 exact, 102 stats), negative cases, version-attestation cases, AST source guard, end-to-end `pob_env.verify()` check (d) contract tests via the shared env double, and the `BASELINE_METADATA_FILES` ratchet; full unit suite green (334 passed)
- Post-review fix batch: same-stem collision refusal, non-finite value rejection (`allow_nan=False`), `is_file()` glob filter, ratchet test (4 minors from the adversarial verify pass; 0 blockers/majors found)
- **Task 4 NOT started**: 6-8 Tier-A baselines require a human capturing fresh GUI saves at the pinned release v0.15.0 (`3e1b71c9`); no fixtures committed, `BASELINE_METADATA_FILES` unextended until they exist
- Status: drafted -> in-progress

**2026-07-02** — Story created via correct-course sprint change proposal
- Drafted from `docs/pebo-master-plan.md` section 6 (Epic 3.5, item 5) per `docs/sprint-change-proposal-2026-07-02.md` section 8.1 (correct-course workflow, batch mode)
- Supersedes the compact proposal-stage draft of this file; expanded to the house BMAD story format with AC-mapped tasks and verified file:line references
- Status: drafted
