# Story 4.1: Truth Engine Spike — Headless driver.lua Boot and Go/No-Go Lane Decision

Status: done

**Epic:** 4 — Truth Engine → **v1 ships here** [Source: docs/pebo-master-plan.md:192-224]
**Tracking key:** `4-1-truth-engine-driver-spike` (add under the epic-4 block in docs/sprint-status.yaml:104) [Source: docs/sprint-status.yaml:104]
**Effort:** 2-week hard timebox — the whole spike is framed as "2 weeks hard" [Source: docs/pebo-master-plan.md:193]
**Dependencies:** Epic 3.5 complete — real submodule pinned at v0.15.0 `3e1b71c9`, generated `external/POB_VERSION.txt`, `pob_env.verify()` autouse guard, 6 committed Tier-A GUI baselines [Source: external/POB_VERSION.txt; tests/fixtures/gui_baselines/; docs/stories/story-3.5.5-gui-baseline-harvest.md]

## Story

As the **PEBO Truth-Engine dev**,
I want **a headless `driver.lua` that boots PoB's REAL Launch→Main→Data calculation chain under embedded Lupa inside a respawnable worker process, reproduces the pinned v0.15.0 GUI DPS within ±0.1%, and produces the pre-committed go/no-go decision evidence (embedded-Lupa vs `luajit.exe` subprocess lane, ADR-004 patch necessity, the v0.22.0 jump attempt, and the five M0 no_valid_neighbors triage)**,
so that **Epic 4 can commit to a lane and an architecture for the Truth Engine on hard evidence instead of the disproven "architecturally impossible" verdict, closing the ~4%-of-GUI-DPS MinimalCalc coverage gap**.

## Acceptance Criteria

1. **AC-4.1.1: driver.lua boots the REAL full engine under Lupa in a worker process (no boot-time SEH).**
   - `driver.lua` (modeled on `HeadlessWrapper.lua`) runs the full `dofile("Launch.lua")` → `runCallback("OnInit")` → `runCallback("OnFrame")` → `build = mainObject.main.modes["BUILD"]` chain under embedded `lupa.luajit21` inside a separate (respawnable) worker process. [Source: external/pob-engine/src/HeadlessWrapper.lua:183,190-191,201]
   - Boot completes without a **boot-time** SEH `0xe24c4a02`; a **teardown** SEH after success is benign and MUST NOT be scored as a boot failure. [Source: docs/decisions/ADR-003-windows-luajit-cleanup-mitigation.md; CLAUDE.md]
   - The engine drives the REAL `Modules/ModParser` + `CalcSetup/CalcPerform/CalcOffence/CalcDefence` pipeline — NOT MinimalCalc's stubbed ModParser. [Source: src/calculator/MinimalCalc.lua:46-56,511-521]
   - The **minimal native-module `package.loaded` pre-stub set** that yields a clean boot is recorded (known: `lua-utf8`, `lcurl.safe`). [Source: external/pob-engine/src/Modules/Common.lua:25,29; docs/stories/story-1.4.md:947-967]

2. **AC-4.1.2: ±0.1% TotalDPS parity on the geared deadeye anchor at the v0.15.0 pin.**
   - Feeding `tests/fixtures/gui_baselines/xml/deadeye_lightning_arrow_76.xml` through `LOAD_BUILD`, the driver's output stat read via `GET_STATS` matches the paired baseline `stats.TotalDPS = 23003.185361227` within **±0.1%**, measured across the worker-process boundary. [Source: tests/fixtures/gui_baselines/deadeye_lightning_arrow_76.baseline.json:20]
   - The stale corpus value **18097.067904221** (`tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml:11`, pobb.in provenance) is explicitly NOT used as the target; the master-plan Appendix-A citation of 18097 is stale post-3.5.5. [Source: tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml:11; docs/stories/story-3.5.5-gui-baseline-harvest.md]

3. **AC-4.1.3: Archetype-aware ±0.1% parity across the three v1 archetypes.**
   - Parity holds on ≥1 build per archetype using the archetype-correct stat: attack/spell-hit → `TotalDPS`; DoT → `TotalDot`. [Source: tests/fixtures/gui_baselines/witch_essence_drain_86.baseline.json]
   - DoT anchor: `witch_essence_drain_86` — GUI `TotalDPS = 0`, `FullDPS = 0`, `TotalDot = 23752.222654477`; a naive `TotalDPS` assertion passes 0≈0 vacuously and proves nothing, so the metric MUST branch on `_metadata.archetype` (`attack`|`spell-hit`|`dot`). [Source: tests/fixtures/gui_baselines/xml/witch_essence_drain_86.xml:11-12,100]

4. **AC-4.1.4: Pre-committed go/no-go verdict recorded at a fixed date.**
   - A verdict is recorded at a DATE fixed in advance — anchored relationally as **end of week 2 from spike start** (the 2-week hard timebox per Effort) so the gate can't be silently dropped; SM/PO stamps the concrete calendar date at scheduling: **embedded-Lupa lane vs `luajit.exe` subprocess fallback lane**, both running the SAME `driver.lua` file. [Source: docs/pebo-master-plan.md:104-110,193-199]
   - The verdict cites the evidence behind it: boot result, parity delta, per-build boot + per-GET_STATS latency, and worker memory footprint. [Source: docs/pebo-master-plan.md:323,331 (risk #1/#9)]

5. **AC-4.1.5: The `luajit.exe` subprocess fallback lane is proven executable the same week.**
   - A LuaJIT 2.1 binary (NOT vendored in the repo) is staged, and the identical `driver.lua` runs as a TRUE subprocess under `luajit.exe` achieving the same `LOAD_BUILD`+`GET_STATS` parity — so a boot crash on the embedded lane is a same-week flip, not a re-scope. [Source: external/pob-engine/.github/workflows/test.yml:16,32; external/pob-engine/runtime/ (no luajit*.exe)]

6. **AC-4.1.6: Keep-or-drop verdict per ADR-004 nil-safety patch under the REAL ModParser.**
   - The real-ModParser driver is booted on the spell build (`ritualist_lightning_spear_96` — the build ADR-004 names) and a DoT build with patches `0001`/`0002`/`0003` reverted; per-site evidence records whether "arithmetic on a nil value" reproduces at `Global.lua:118` / `ModStore.lua:458` / `CalcOffence.lua:5007`. [Source: docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md:237,290-292]
   - A per-patch keep/drop verdict (a split verdict is allowed) is recorded; the reverted-patch experiment is UNMARKED (see AC-4.1.11) and the env is restored to `setup_pob.py` exit 0 before close. [Source: external/patches/README.md:44-60]

7. **AC-4.1.7: v0.22.0 jump attempted AFTER v0.15.0 parity passes — boot/tree-load evidence only.**
   - AFTER AC-4.1.2/3 pass, the submodule is checked out to `860f4268` (already in history, no re-clone), the parked `docs/forensics/proposed-patches/0001-global-lua-nil-safety-v0220.patch` is swapped for `0001` (0002/0003 unchanged), and the driver is booted. [Source: docs/sprint-change-proposal-2026-07-02.md:391-392]
   - Records whether the REAL driver boots v0.22.0's `CalcSetup` API (`env.spec:CollectGrantedPassiveNodesFromItems` — the exact blocker MinimalCalc could not satisfy) and loads `TreeData/0_5`. v0.22.0 **parity** requires fresh v0.22.0 GUI re-capture and is EXPLICITLY DEFERRED (do NOT assert v0.22.0 output against v0.15.0 baselines). [Source: docs/stories/story-3.5.2-submodule-repair-and-pin.md:5; external/pob-engine/src/Modules/CalcSetup.lua:203-228]

8. **AC-4.1.8: The five iterations==0 M0 no_valid_neighbors builds are triaged as acceptance evidence.**
   - The five are selected by `iterations==0` (NOT by `convergence_reason` alone — ten builds report `no_valid_neighbors`, five of them converged normally at iterations=20): `gemling_frost_mage_100`, `lich_storm_mage_90`, `titan_infernal_cry_72`, `warrior_ballista_93`, `witch_frost_mage_91`. [Source: docs/validation/realistic-validation-results.json:57-74,96-115,155-175,196-215,296-315]
   - Per-build evidence tests the LEADING hypothesis FIRST: these five are the ONLY multi-`<Spec>` builds, so the likely root cause is the `activeSpec` parse gap, **NOT** tree-version. Parse allocated nodes via the `activeSpec`-aware pattern (pob_parser.py:232-244) and report the count. Node-presence in `TreeData/0_3` vs `0_4`/`0_5` is SECONDARY / falsifying evidence — expected finding: nodes are present in BOTH graphs → tree-version mismatch is REFUTED (a contrary result is a genuine signal, not a confirmation to chase). Separately confirm `lich_storm_mage_90` (0.0 MinimalCalc baseline) calcs nonzero DPS under the real driver. [Source: src/parsers/pob_parser.py:232-244,391-393; docs/sprint-change-proposal-2026-07-02.md:200-202]

9. **AC-4.1.9 (hard constraint): XML-direct loading only.** Builds are fed to the driver as ORIGINAL PoB XML read directly from the saved `.xml`, never via `parse_pob_code`/`BuildData` re-encoding — routing imports through PoB's own `PassiveSpec` (`convert=true`) for free tree-migration/weapon-set/dual-ascendancy handling. [Source: src/parsers/pob_parser.py:25,72-74; docs/pebo-master-plan.md:112-116]

10. **AC-4.1.10 (hard constraint): spike scope only — decision evidence, not shipped feature.** The story does NOT ship `FullCalcEngine`, the 2-worker pool, the optimizer `EVAL_NEIGHBORS` rewire, cooperative cancel, MVP config, parity v2, or MinimalCalc deletion — those are Epic 4 items 2-8. `driver.lua` remains standalone (NOT wired behind `build_calculator.py`). [Source: docs/pebo-master-plan.md:200-224]

11. **AC-4.1.11 (hard constraint): Windows/guard discipline.** All integration/parity execution uses `pytest -n 1`; the parity assertion carries a guarded marker (`parity`/`gui_parity`) so it inherits the `pob_env` autouse guard; the deliberately-unpatched (AC-4.1.6) and v0.22.0 (AC-4.1.7) experiments are UNMARKED or standalone scripts (a marked test on a drifted tree FAILS at setup). `python scripts/setup_pob.py` MUST exit 0 ("ratified-state reconciliation clean") before close. [Source: tests/conftest.py:28-62; scripts/setup_pob.py]

## Tasks / Subtasks

- [x] **Task 1: Establish the prior-art boot baseline before writing anything** (AC: 4.1.1)
  - [x] Run `pytest -n 1 tests/integration/test_full_pob_engine.py -v`. `src/calculator/full_pob_engine.py` is an ORPHANED Story-2.9 attempt that already boots `HeadlessWrapper.lua` in-process with a `package.loaded` stub set + `working_directory(pob_src)` cwd fix + `mainOutput` extraction. If it boots, risk #1 is largely retired — BUT booting proves boot-SURVIVABILITY, NOT stat correctness: `full_pob_engine.py` itself carries the MinimalCalc anti-pattern (identity `base64`/`sha1` stubs at :153-160), so it can boot AND return coverage-gap DPS. Do NOT harvest its `package.loaded` block wholesale — audit it against the inverse-of-MinimalCalc rule (Task 2) first: KEEP `arg={}` (:139), `lua-utf8` incl. `len` (:142-148), `lcurl.safe` (:151); DROP `base64` (:153-157) + `sha1` (:159-160). [Source: src/calculator/full_pob_engine.py:137-161,257-306]
  - [x] Record pass/fail as the first spike evidence artifact.

- [x] **Task 2: Author `driver.lua`** (AC: 4.1.1, 4.1.9)
  - [x] Create `src/calculator/driver.lua` (OUTSIDE the submodule — a file added inside `external/pob-engine/` trips `pob_env.verify()` invariant (e) "unrecorded engine edit" and FAILS every parity test). [Source: src/pob_env.py:264-287]
  - [x] Copy `HeadlessWrapper.lua`'s pure-Lua GUI/render/image stub surface (lines 6-171) as the foundation; do NOT reinvent. [Source: external/pob-engine/src/HeadlessWrapper.lua:6-171]
  - [x] Seed BEFORE `dofile("Launch.lua")` by copying the PROVEN block verbatim (`full_pob_engine.py:137-161` **minus** base64/sha1): the global `arg = {}` (Main.lua:58 expects it — REQUIRED, not optional), `package.loaded["lua-utf8"] = utf8 or {reverse=..., gsub=string.gsub, find=string.find, sub=string.sub, len=function(s) return #s end}` (include `len` — the proven block has it; omitting it SEH-crashes if boot touches `utf8.len`), and `package.loaded["lcurl.safe"] = {}`. Use `package.loaded`, NOT `package.preload` (preload still dlopens → SEH). Do NOT stub `xml`/`base64`/`sha1`/`sha2`/`dkjson` — they are pure-Lua in `runtime/lua/` and must load REAL. [Source: src/calculator/full_pob_engine.py:137-161; src/calculator/MinimalCalc.lua:120,137-142; docs/stories/story-1.4.md:965-967]
  - [x] Determine the minimal native pre-stub set empirically (this is the spike's central engineering question) and record it.
  - [x] Expose `build = mainObject.main.modes["BUILD"]` and a `loadBuildFromXML(xmlText,name)` path (`main:SetMode("BUILD",false,name,xmlText)` + one `OnFrame` pump). [Source: external/pob-engine/src/HeadlessWrapper.lua:208-211; external/pob-engine/src/Modules/Main.lua:354-365,507-510]

- [x] **Task 3: Reuse the proven GUI-stat accessor** (AC: 4.1.2, 4.1.3)
  - [x] REUSE the already-proven read path (do NOT re-derive it): `build.calcsTab.mainOutput[stat]` (== `mainEnv.player.output[stat]`), exactly as `full_pob_engine.py:231,349` + `_extract_stats` already do. `CalcsTab:BuildOutput()` sets `mainOutput = mainEnv.player.output`, and `<PlayerStat>` is written verbatim from `calcsTab.mainOutput[stat]`, so identity with the baseline JSON holds by construction. Do NOT assume a global `output`. [Source: src/calculator/full_pob_engine.py:231,349; external/pob-engine/src/Classes/CalcsTab.lua:484-485; external/pob-engine/src/Modules/Build.lua:666-667,1020,1028-1030]
  - [x] Confirm one `OnFrame` after `loadBuildFromXML` is sufficient to populate `TotalDPS` (Build:Init runs first calc at Build.lua:666-667); pump a second `OnFrame` to guarantee settle. [Source: external/pob-engine/src/Modules/Build.lua:666-667,1144-1152]

- [x] **Task 4: Minimal respawnable worker-process host** (AC: 4.1.1, 4.1.4)
  - [x] Build a Python parent ↔ Lua child host that sets cwd = `external/pob-engine/src` (Launch.lua:46 loads `manifest.xml` via `../manifest.xml` relative to cwd; upstream CI does `cd src`), boots `driver.lua` by ABSOLUTE path under `lupa.luajit21`, and survives/reports an SEH crash instead of dying with the parent. Reuse the `package.path` recipe from `pob_engine.py:564-579` verbatim (already includes `runtime/lua/?.lua`). [Source: src/calculator/pob_engine.py:564-579; external/pob-engine/src/Launch.lua:45-46]
  - [x] Implement a stdin/stdout command protocol with at least `LOAD_BUILD` and `GET_STATS`. Stub/prove-loadable `EVAL_NEIGHBORS`/`APPLY_MOVE` but do NOT build the full optimizer rewire (Epic 4 item 2/4). Worker = PROCESS not thread (LuaJIT is not thread-safe; process isolation contains the native-fault SEH). [Source: docs/pebo-master-plan.md:200-202; CLAUDE.md]
  - [x] `collectgarbage` between builds; measure per-process memory (200-400MB per full-Data.lua worker, risk #9). [Source: docs/pebo-master-plan.md:331]

- [x] **Task 5: v0.15.0 parity harness** (AC: 4.1.2, 4.1.3, 4.1.11)
  - [x] Add an integration/parity test marked `@pytest.mark.gui_parity`, run under `pytest -n 1`, that feeds each of the 6 `tests/fixtures/gui_baselines/xml/*.xml` builds via `LOAD_BUILD`, reads the archetype-correct stat from `_metadata.archetype` (attack/spell-hit → TotalDPS; dot → TotalDot), and asserts ±0.1% relative (±1 absolute for zero) against the paired `*.baseline.json`. [Source: tests/fixtures/gui_baselines/]
  - [x] Primary proof build = `deadeye_lightning_arrow_76` (23003.185361227). Siblings: `ritualist_lightning_spear_96` (407381.39953906), `titan_falling_thunder_99` (13817.274690059), `warrior_earthquake_89` (49262.048339828) (attack); `bloodmage_remnants_95` (6906.4652250384, spell-hit); `witch_essence_drain_86` (TotalDot 23752.222654477, dot).
  - [x] Tolerate the teardown SEH after "N passed"; do not count it as a failure.

- [~] **Task 6: Stage LuaJIT 2.1 + the subprocess fallback lane** (AC: 4.1.5) — **PARTIAL (honest): lane CODE-READY + protocol proven; binary NOT staged (no compiler in this env; embedded lane works → off critical path). See Completion Notes Task 6.**
  - [ ] **Front-load this in week 1 — it is a timebox risk.** Obtain/build a LuaJIT 2.1 `luajit.exe` matching lupa's embedded 2.1 (NONE is vendored — `runtime/` has the GUI exe + `Update.exe` + `lua51.dll` only; lupa embeds LuaJIT as a C-extension). Sourcing/building a byte-matching LuaJIT 2.1 Windows binary is unbounded-effort work that can consume the whole 2-week timebox before the fallback lane is even testable — stage it in week 1 so a boot-crash flip is genuinely same-week, not a re-scope. [Source: external/pob-engine/runtime/; requirements.txt:10] — **BLOCKED: no luajit.exe vendored; no gcc/cc/cl/make in this environment to build a byte-matching binary; declined to download an arbitrary unvetted binary.**
  - [ ] Run the SAME `driver.lua` as a true subprocess under `luajit.exe` with real stdin/stdout framing (CI proves the boot half: `cd src; luajit HeadlessWrapper.lua`) and prove `LOAD_BUILD`+`GET_STATS` parity through it. [Source: external/pob-engine/.github/workflows/test.yml:32] — **DEFERRED: `driver.lua` `Driver.serve()` + `driver_worker.DriverWorker(lane="luajit")` are implemented and ready; the shared `handle_command` protocol is proven by the embedded lane; only the external binary spawn is unrun.**

- [x] **Task 7: Go/no-go decision + measurements** (AC: 4.1.4)
  - [x] Measure worker memory (full Data.lua footprint) and per-build boot + per-`GET_STATS` latency on the corpus worst case (feeds Epic 4 pool-size + `useFullDPS`-search decisions). [Source: docs/pebo-master-plan.md:323,331]
  - [x] At the fixed date, record the lane verdict (embedded-Lupa vs luajit.exe) with boot/parity/latency/memory evidence in the Dev Agent Record.

- [x] **Task 8: ADR-004 patch-necessity experiment** (AC: 4.1.6, 4.1.11)
  - [x] In a scratch/detached state (or an UNMARKED standalone script), reverse-apply the guards: `git -c core.autocrlf=false apply --reverse external/patches/0001..0003` from repo ROOT, OR `git -C external/pob-engine checkout -- src/Data/Global.lua src/Classes/ModStore.lua src/Modules/CalcOffence.lua`. Do NOT mark this test `parity`/`gui_parity` (autouse guard FAILS it on the deliberately-drifted tree). [Source: external/patches/README.md:44-60; tests/conftest.py:40-67]
  - [x] Boot the real-ModParser driver on `ritualist_lightning_spear_96` (spell) + `witch_essence_drain_86` (DoT); instrument the three sites (`Global.lua:108-196`, `ModStore.lua:~455`, `CalcOffence.lua:~5003`) via pcall+traceback to capture WHETHER/WHERE nil arrives. [Source: external/pob-engine/src/Data/Global.lua:108-196; external/pob-engine/src/Classes/ModStore.lua:458; external/pob-engine/src/Modules/CalcOffence.lua:5007]
  - [x] Record per-patch keep/drop. If dropping: `git rm` the `.patch` + `git checkout` the one engine file to pristine (else invariant (e) byte-exact reconciliation fails) + re-run `setup_pob.py` (POB_VERSION.txt auto-regenerates without that entry) + update `external/patches/README.md` + ADR-004. Each patch = exactly one file: 0001=Global.lua, 0002=ModStore.lua, 0003=CalcOffence.lua. [Source: src/pob_env.py:182-287,382-388]
  - [x] Restore: `python scripts/setup_pob.py` MUST exit 0 before proceeding.

- [x] **Task 9: v0.22.0 jump attempt** (AC: 4.1.7, 4.1.11)
  - [x] ONLY after Task 5 passes. In a scratch/worktree (active pin stays v0.15.0), `git checkout 860f4268` in the submodule, swap in `docs/forensics/proposed-patches/0001-global-lua-nil-safety-v0220.patch` for 0001 (0002/0003 apply clean on both tags), boot `driver.lua`. [Source: docs/forensics/proposed-patches/0001-global-lua-nil-safety-v0220.patch]
  - [x] Record whether the real `CalcSetup` satisfies `CollectGrantedPassiveNodesFromItems` natively and `TreeData/0_5` loads. Do NOT assert ±0.1% here (cross-version) and do NOT re-pin the repo. Run OFF the `pob_env`-gated parity suite (the jump changes gitlink/manifest → invariants b/c/d go red). Restore to v0.15.0 + `setup_pob.py` exit 0. [Source: docs/sprint-change-proposal-2026-07-02.md:386-392]

- [x] **Task 10: M0 five-build triage** (AC: 4.1.8)
  - [x] Pure-Python read-only graph check first (no engine). **HARD CONSTRAINT — evidence-integrity:** parse allocated node IDs via the `activeSpec`-aware pattern (pob_parser.py:232-244), **NOT** the buggy `_extract_passive_nodes` (pob_parser.py:391-393), which ignores `activeSpec` and returns an EMPTY set for list-typed `<Spec>` — using it self-contaminates the triage (it would falsely "prove" zero nodes / tree mismatch on exactly these five multi-Spec builds). For each of the five (`gemling_frost_mage_100`, `lich_storm_mage_90`, `titan_infernal_cry_72`, `warrior_ballista_93`, `witch_frost_mage_91`) set-diff the correctly-parsed nodes against `load_passive_tree("0_3").nodes` vs `0_4`(/`0_5`), plus BFS connectivity from class start. Report per-build missing-node counts + connectivity + confirm multi-`<Spec>` status — not a guessed cause. [Source: src/parsers/pob_parser.py:232-244,391-393; src/calculator/passive_tree.py:242,246-247,267]
  - [x] Confirm `lich_storm_mage_90` calcs nonzero DPS under the real driver (its 0.0 is a separate MinimalCalc coverage gap). Keep the two probes separate. [Source: docs/validation/calculation-gap-REVISED-ANALYSIS-2025-11-29.md:80-102]
  - **DONE:** corpus scan → exactly the five are the only multi-`<Spec>` builds; buggy parse = 0 nodes for all five (root cause of no_valid_neighbors@iter0 = activeSpec parse gap); tree-version REFUTED (miss@0_3==miss@0_4 every build); real driver loads all five with correct node counts; `lich_storm_mage_90` = **188,475 FullDPS** (nonzero). See `scripts/triage_m0_builds.py`.

- [x] **Task 11: Record decision artifacts + draft ADR stubs** (AC: 4.1.4, 4.1.6, 4.1.7, 4.1.8, 4.1.10)
  - [x] Capture lane verdict, per-patch keep/drop, v0.22.0 boot result, triage table, memory/latency numbers in the Dev Agent Record.
  - [x] Apply the ADR-004 status edit to "Accepted — under re-evaluation; supersession trigger = Epic 4 spike outcome (fixed date)". [Source: docs/sprint-change-proposal-2026-07-02.md:286]
  - [x] Draft stubs: ADR-005 (Truth Engine / driver.lua), ADR-006 (worker-pool process isolation + 4-command protocol), ADR-007 (XML-direct via PassiveSpec convert=true), ADR-008 (tree 0_4/0_5 bump + version assert). Do NOT build the item-2 integration. [Source: docs/sprint-change-proposal-2026-07-02.md:284]

## Dev Notes

- **This is a SPIKE producing DECISION EVIDENCE, not a feature.** Phrase every outcome as "the spike DEMONSTRATES/RECORDS X", following the Story 3.5.2 AC5 pre-committed-fallback pattern. The full `FullCalcEngine`, 2-worker pool, optimizer `EVAL_NEIGHBORS` rewire, cooperative cancel, MVP config, parity v2, and MinimalCalc deletion are Epic 4 items 2-8 and are OUT of scope. [Source: docs/pebo-master-plan.md:192-224]

- **MODEL, don't fork.** `driver.lua` = HeadlessWrapper.lua's stub set (lines 6-171) + the `package.loaded` native pre-stub block + a thin stdin/stdout command loop. Target ~250 lines. Do NOT edit `HeadlessWrapper.lua` in the submodule (invariant e). [Source: external/pob-engine/src/HeadlessWrapper.lua:6-171]

- **The SEH fix (THE central risk).** Native C `require` (`lcurl.safe` at Common.lua:25, `lua-utf8` at Common.lua:29) dlopen-crashes under Lupa with `0xe24c4a02`. HeadlessWrapper's require-hack only covers `lcurl.safe` — `lua-utf8` is the uncovered trigger. Fix = pre-seed `package.loaded[name]` (NOT `package.preload`, which re-invokes the loader). `Main:DetectUnicodeSupport` only checks `type(_G.utf8)=="table"` — no second native dep hides behind it. [Source: external/pob-engine/src/Modules/Common.lua:25,29; external/pob-engine/src/Modules/Main.lua:52,284-290; docs/stories/story-1.4.md:947-967]

- **The inverse-of-MinimalCalc rule.** MinimalCalc STUBS `xml`/`base64`/`sha1` (MinimalCalc.lua:123-134) AND ModParser (returns empty mod list) — THAT is why it computes ~4% of GUI DPS. `driver.lua` must let those pure-Lua libs load REAL and drive the real ModParser. Copy-pasting MinimalCalc's xml/base64/sha1 stubs wholesale reproduces the coverage gap the spike exists to close. [Source: src/calculator/MinimalCalc.lua:46-56,123-134,511-521]

- **cwd GOTCHA.** HeadlessWrapper ends with relative `dofile("Launch.lua")`, LoadModule uses relative `loadfile`, and Launch.lua:46 reads `manifest.xml` via `../manifest.xml`. The worker MUST `os.chdir` to `external/pob-engine/src` before boot (Lupa inherits process cwd; `SetWorkDir` is a no-op stub). Mirrors CI's `cd src`. `full_pob_engine.py` solves this with a `working_directory` context manager. [Source: external/pob-engine/src/HeadlessWrapper.lua:121-131,183; external/pob-engine/.github/workflows/test.yml:32]

- **Parity anchor trap.** Two same-named deadeye XMLs exist. Feed `tests/fixtures/gui_baselines/xml/deadeye_lightning_arrow_76.xml` (v0.15.0 GUI-saved, target 23003.185361227), NOT `tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml` (pobb.in, 18097.067904221, unknown version). Comparing v0.15.0 output to 18097 guarantees a spurious ~21% miss. [Source: tests/fixtures/gui_baselines/deadeye_lightning_arrow_76.baseline.json:20; tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml:11]

- **DoT stat branch.** `witch_essence_drain_86` reports `TotalDPS=0`, `FullDPS=0`, real damage in `TotalDot`. Any parity harness keyed only on `TotalDPS` reads 0 for DoT and passes vacuously. Branch on `_metadata.archetype`. [Source: tests/fixtures/gui_baselines/xml/witch_essence_drain_86.xml:11-12,100]

- **ADR-004 experiment framing.** The three patches guard nils that arose because MinimalCalc's stubbed ModParser fed empty mod lists into `Global.lua` bitwise ops / `ModStore.EvalMod` / `CalcOffence` ailment loop. This spike is the FIRST time the real 6,940-line ModParser executes. Boot the spell/DoT builds with patches reverted; if the real pipeline never passes nil, the patches are MinimalCalc-only artifacts. A split verdict (e.g. drop 0001, keep 0003 as a genuine data gap) is allowed. Do the reverse-apply on a scratch tree or expect+explain the guard red; ALWAYS restore. [Source: docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md:270-292]

- **v0.22.0 ordering + failure signature.** v0.15.0 parity FIRST (baselines only exist at v0.15.0), THEN the jump. The 2026-07-02 v0.22.0 attempt failed ONLY because MinimalCalc's spec/itemsTab doubles couldn't satisfy `CalcSetup.lua:875 env.spec:CollectGrantedPassiveNodesFromItems` (canary 18/18 F, 119 integration F) — the real driver uses PoB's own CalcSetup, so that blocker should evaporate. v0.22.0 objects are already in submodule history (no re-clone); it ships `TreeData/0_5`. v0.22.0 is a BOOT-SUCCESS check, not parity. [Source: docs/stories/story-3.5.2-submodule-repair-and-pin.md:5; external/pob-engine/src/Modules/CalcSetup.lua:203-228]

- **M0 triage filter.** Select by `iterations==0` (not `convergence_reason`) — `no_valid_neighbors` is also the NORMAL terminal state for 10 builds including big winners (bloodmage +161%). The `targetVersion` shortcut is a trap (all five AND the healthy deadeye share `targetVersion="0_1"`); test per-NODE membership + connectivity empirically. The 0_3→0_4/0_5 tree bump itself is Epic 4 item 3, NOT spike scope — only the triage evidence is. [Source: docs/validation/realistic-validation-results.json:16-35; docs/pebo-master-plan.md:203-209]

- **Data-driven env guard.** `pob_env.verify()`/`conftest`/`setup_pob.py` discover patches by glob with ZERO hardcoded patch name/marker/count — dropping a patch is a one-file delete. Do NOT hardcode any nil-safety marker anywhere in spike tooling. Always apply/reverse with `git -c core.autocrlf=false` from repo ROOT (patches carry `external/pob-engine/...` paths); reverse-check BEFORE forward-check (patch 0002's EvalMod context repeats → forward-first double-applies). [Source: src/pob_env.py:173-179; scripts/setup_pob.py:99-118; external/patches/README.md:44-60]

- **House script convention.** stdlib-only, list-args subprocess with explicit cwd, never `shell=True`; `setup_pob`-style exit codes (0 ok / 1 internal / 2 usage / 3 input / 4 attestation / 5 gitlink-output / 6 conflict). [Source: docs/stories/story-3.5.3-setup-pob-script.md:155,163]

- **Windows discipline.** `pytest -n 1` for all integration/parity; teardown SEH `0xe24c4a02` after "N passed" is benign (ADR-003); `pytest.ini` already sets `-p no:faulthandler`. Distinguish a boot-time SEH (the risk-#1 signal) from a teardown SEH (benign). [Source: docs/decisions/ADR-003-windows-luajit-cleanup-mitigation.md; CLAUDE.md]

- **Ignore two false CLAUDE.md bullets.** "Passive Tree — Pre-built from PassiveTree.lua" is FALSE (loaded from `TreeData/{version}/tree.json` JSON, default `0_3`). "Spell/DOT → subprocess (accurate)" is FALSE (`subprocess_calculator.py` runs the SAME in-process engine; its real-subprocess methods raise `NotImplementedError` at :162/:191/:220). [Source: src/calculator/passive_tree.py:242,267; src/calculator/subprocess_calculator.py:102-118,162,191,220]

### Previous Story Intelligence (Epic 3.5)

- **3.5.5 (immediate predecessor) — GUI baseline harvest.** Captured the SIX v0.15.0 Tier-A baselines this spike parity-checks against (deadeye 23003.19 attack, ritualist 407381.40 attack, titan_falling_thunder 13817.27 attack, warrior_earthquake 49262.05 attack, bloodmage 6906.47 spell-hit, witch_essence_drain TotalDot 23752.22 dot). Each is an `xml/*.xml` + `*.baseline.json` pair. Caveat: spell-hit and dot are SINGLE-sample/shallow anchors until Epic 4 item 6 mass capture. This story is also the structural template (bold header block, AC-N.M numbering, AC-mapped task checkboxes, `[Source:]` References, Dev Agent Record, Change Log). [Source: docs/stories/story-3.5.5-gui-baseline-harvest.md:143-144]

- **3.5.2 — submodule repair + pin + v0.22.0 attempt.** Executed the v0.22.0 jump (`860f4268`) and rolled back to v0.15.0 `3e1b71c9` the same day; captured the exact failure signature (CalcSetup CollectGrantedPassiveNodesFromItems, canary 18/18 F, 119F/125P). Parked the v0.22.0 Global.lua patch variant at `docs/forensics/proposed-patches/`. Its AC5 (pre-committed go/no-go fallback) is the template for AC-4.1.4. [Source: docs/stories/story-3.5.2-submodule-repair-and-pin.md:5,168]

- **3.5.4 — pob_env.verify() + conftest guard.** Built the 5-invariant guard + autouse `_GUARDED_MARKERS=('parity','gui_parity')` that FAILS (never skips) on drift; data-driven patch discovery; `BASELINE_METADATA_FILES` allowlist ratchet. Any new baseline fixture must be allowlisted or the ratchet test reds the suite. [Source: docs/stories/story-3.5.4-pob-env-verify-conftest-guard.md:19-49]

- **3.5.3 — setup_pob.py.** THE idempotent setup/restore command with the exit-code convention reused here. [Source: docs/stories/story-3.5.3-setup-pob-script.md]

- **1.4 (Epic 1) — the disproven "impossible" verdict.** Pivoted to MinimalCalc but discovered the `package.loaded` pre-stub SEH fix (never applied to the full launch flow). This spike applies that exact fix to the real chain. [Source: docs/stories/story-1.4.md:947-967]

### Project Structure Notes

- **New files:** `src/calculator/driver.lua` (OUTSIDE the submodule — mandatory per invariant e), a Python worker-process host module (spike-grade, e.g. `src/calculator/`), a `gui_parity`-marked parity test under `tests/integration/`, a pure-Python triage script (scratchpad or `scripts/`), ADR-005..008 stubs under `docs/decisions/`.
- **Reuse (do not reinvent) — but AUDIT before lifting, never harvest wholesale:** `full_pob_engine.py` package.path recipe (121-133) + ONLY the native pre-stubs from its `package.loaded` block — `arg={}` (139), `lua-utf8` incl. `len` (142-148), `lcurl.safe` (151) — **NOT** its `base64` (153-157)/`sha1` (159-160) identity stubs (those are the MinimalCalc anti-pattern; `base64`/`sha1`/`xml`/`sha2`/`dkjson` must load REAL from `runtime/lua/`) + `_extract_stats` (257-306) + `working_directory` (41-49) + the `mainOutput` accessor (231,349); `pob_engine.py` package.path recipe (564-579) + stub registration (217-223); `stub_functions.py` Deflate/Inflate/ConPrintf/SpawnProcess/OpenURL; `pob_parser.py` base64→zlib→XML decode (74) for reading the XML string; `encode_pob_code` activeSpec-selection (232-244) for the triage parser fix.
- **NOT touched:** `build_calculator.py` (the item-2 integration point), the worker pool, `MinimalCalc.lua` (retired to a fixture by item 8, not this story), `external/POB_VERSION.txt` (generated — never hand-edit), `passive_tree.py` 0_3 default (item-3 bump).
- **Tracking:** add key `4-1-truth-engine-driver-spike` under the epic-4 block in `docs/sprint-status.yaml:104`.

### References

- [Source: docs/pebo-master-plan.md:78-118 — §3 Truth Engine root decision: driver.lua ~250 lines, respawnable workers, command protocol, XML-direct, fallback lane, MinimalCalc retirement]
- [Source: docs/pebo-master-plan.md:192-224 — §6 Epic 4 items 1-8; item 1 = the spike def at 192-199; item 3 = 0_3→0_4 bump + PassiveSpec convert=true]
- [Source: docs/pebo-master-plan.md:323,328,331 — risks #1 (SEH boot), #6 (tree schism), #9 (worker memory 200-400MB)]
- [Source: docs/sprint-change-proposal-2026-07-02.md:188-217 — §5 M0 disposition, five-build triage rider, iterations==0 signature]
- [Source: docs/sprint-change-proposal-2026-07-02.md:284,286 — §7.3 ADR-005..008 drafts + ADR-004 status wording]
- [Source: docs/sprint-change-proposal-2026-07-02.md:386-395 — §8.4 v0.22.0 decision/execution/rollback + parked patch + TreeData/0_5]
- [Source: external/pob-engine/src/HeadlessWrapper.lua:6-171,173-180,183,190-191,201,208-211 — driver.lua model: stubs, require-hack, boot sequence, build handle, loadBuildFromXML]
- [Source: external/pob-engine/src/Launch.lua:20-87 — OnInit: require('xml') :45, manifest ../manifest.xml :46, RenderInit :68, PLoadModule('Modules/Main') :71]
- [Source: external/pob-engine/src/Modules/Main.lua:51-55,284-290,354-365,507-510 — modes['BUILD'], DetectUnicodeSupport (no lua-utf8 dep), OnFrame CallMode('Init'), SetMode defer]
- [Source: external/pob-engine/src/Modules/Common.lua:25,29,741-755 — the two native requires (lcurl.safe, lua-utf8) + the 4 utf8 funcs actually used]
- [Source: external/pob-engine/src/Modules/Build.lua:666-667,1020,1028-1030,1144-1152 — first calc in Build:Init, PlayerStat written from calcsTab.mainOutput, buildFlag recalc gate]
- [Source: external/pob-engine/src/Classes/CalcsTab.lua:484-485 — mainEnv=calcs.buildOutput(build,'MAIN'); mainOutput=mainEnv.player.output]
- [Source: external/pob-engine/src/Modules/CalcSetup.lua:203-228 — v0.15.0 has allocMode/WeaponSet but NOT CollectGrantedPassiveNodesFromItems (v0.22.0-new API)]
- [Source: external/pob-engine/.github/workflows/test.yml:16,32 — busted --lua=luajit; `cd src; luajit HeadlessWrapper.lua` (fallback-lane proof)]
- [Source: external/pob-engine/runtime/ — no standalone luajit*.exe vendored; GUI exe + Update.exe + lua51.dll only]
- [Source: external/POB_VERSION.txt — active pin Commit 3e1b71c92dc5f7c295031700746a418558117b06, Version 0.15.0 (generated; never hand-edit)]
- [Source: tests/fixtures/gui_baselines/deadeye_lightning_arrow_76.baseline.json:20 — TotalDPS 23003.185361227, _metadata.pob_version 0.15.0, archetype attack]
- [Source: tests/fixtures/gui_baselines/xml/witch_essence_drain_86.xml:11-12,100 — DoT: TotalDPS 0 / TotalDot 23752.222654477]
- [Source: tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml:11 — stale corpus 18097.067904221 (do NOT target)]
- [Source: src/calculator/full_pob_engine.py:137-161,231,257-306,349 — orphaned in-process HeadlessWrapper boot; reuse ONLY native pre-stubs (arg/lua-utf8/lcurl) + _extract_stats + mainOutput accessor, NOT its base64/sha1 identity stubs at :153-160 (MinimalCalc anti-pattern)]
- [Source: tests/integration/test_full_pob_engine.py:35-60 — prior-art boot test, no skip markers; run FIRST under -n 1]
- [Source: src/calculator/pob_engine.py:203,217-223,564-579,581-637 — LuaRuntime, stub registration, package.path recipe, MinimalCalc load (not HeadlessWrapper)]
- [Source: src/calculator/MinimalCalc.lua:46-56,120,123-134,137-142,511-521 — ModParser stub (nil source) + the xml/base64/sha1 stub anti-pattern + the good lua-utf8/lcurl stubs]
- [Source: src/parsers/pob_parser.py:74,232-244,391-393 — base64→zlib→XML decode; correct activeSpec selection; buggy _extract_passive_nodes]
- [Source: src/calculator/passive_tree.py:242,246-247,267 — hardcoded tree_version '0_3' + TreeData/{version}/tree.json path]
- [Source: external/patches/0001-global-lua-nil-safety.patch, 0002-modstore-evalmod-nil-safety.patch, 0003-calcoffence-ailment-buildup-nil-safety.patch — the ADR-004 guards; live sentinels Global.lua:119/148/177, ModStore.lua:458, CalcOffence.lua:5007/5010/5052]
- [Source: external/patches/README.md:44-60,62-66 — repo-root LF apply, reverse-check-first, Story 2.9.2 regression gate]
- [Source: docs/forensics/proposed-patches/0001-global-lua-nil-safety-v0220.patch — parked v0.22.0 variant of 0001]
- [Source: docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md:237,270-292 — ritualist named crash build; addendum item 4 = the spike (c) open question]
- [Source: docs/decisions/ADR-003-windows-luajit-cleanup-mitigation.md — SEH 0xe24c4a02 teardown is benign; -n 1 process isolation]
- [Source: docs/validation/realistic-validation-results.json:57-74,96-115,155-175,196-215,296-315 — the five iterations==0 builds]
- [Source: docs/validation/calculation-gap-REVISED-ANALYSIS-2025-11-29.md:80-102 — lich_storm_mage_90 0.0 baseline = MinimalCalc spell-coverage gap]
- [Source: tests/conftest.py:28-62 — autouse pob_env_guard, _GUARDED_MARKERS=('parity','gui_parity'), FAILS never skips]
- [Source: src/pob_env.py:60-69,173-179,182-287,382-388,438-462 — BASELINE_METADATA_FILES, glob patch discovery, byte-exact reconciliation, invariants c/e]
- [Source: scripts/setup_pob.py:33-48,99-118,341-403 — exit codes, decide_patch_action reverse-first, reconcile+POB_VERSION regen]
- [Source: docs/stories/story-3.5.5-gui-baseline-harvest.md — format template + 6 baseline provenance + single-sample caveat]
- [Source: docs/stories/story-3.5.2-submodule-repair-and-pin.md:5,168 — v0.22.0 attempt+rollback, failure signature, AC5 fallback template]
- [Source: docs/stories/story-1.4.md:947-967 — package.loaded (not preload) SEH fix]
- [Source: docs/sprint-status.yaml:104 — epic-4 backlog placeholder; add tracking key here]

## Dev Agent Record

### Context Reference

- Executed via BMAD `dev-story` workflow, 2026-07-03. Spike run under `venv/Scripts/python.exe` (Python 3.14.3, lupa → LuaJIT 2.1.1760617492), PoB pinned v0.15.0 `3e1b71c9`, patches 0001/0002/0003 applied.
- CLAUDE.md project constraints (thread-safety, `pytest -n 1`, ADR-003 teardown-SEH-benign).

### Agent Model Used

claude-opus-4-8 (Claude Code, BMAD dev-story workflow)

### Debug Log References

- Task 1 boot baseline: `pytest -n 1 tests/integration/test_full_pob_engine.py -v` → **15 passed in 32.72s**, no boot-time SEH.
- Prior-art parity pre-check (scratch `probe_parity.py`): 6/6 GUI baselines at **±0.000%** in-process.
- Worker-boundary parity + latency + memory + respawn (scratch `worker_parity.py`): 6/6 ±0.000% across the process boundary.
- Task 5 harness: `pytest -n 1 tests/integration/test_driver_parity.py -v` → **8 passed in 4.66s** (guard inherited, teardown SEH benign).
- Task 10 triage: `python scripts/triage_m0_builds.py` (read-only) + real-driver nonzero probe.
- Regression: `pytest tests/unit/` → **334 passed**. `pytest -n 1 tests/integration/test_driver_parity.py` → **8 passed**. Env: `setup_pob.py` exit 0 (verified after Tasks 8 & 9).
- **NOT a regression:** `test_gui_parity.py` shows 14 pre-existing failures — the OLD MinimalCalc path (`calculate_build_stats`) vs `tests/fixtures/parity_builds/gui_baseline_stats.json` which is explicitly `"stale": true, "pob_version": "0.12.2"` (flagged by story 3.5.2). My spike touches none of that code path (git status: only new untracked files under src/). This is the exact MinimalCalc coverage gap the Truth Engine closes — my `test_driver_parity.py` passes the SAME archetypes at ±0.000% against the current 0.15.0 baselines.

### Completion Notes List

**Task 1 — prior-art boot baseline ✅.** `test_full_pob_engine.py` 15/15 pass in 32.7s. `full_pob_engine.py` boots PoB's REAL `Launch→OnInit→OnFrame→build` chain in-process under Lupa with **no boot-time SEH** → **risk #1 (SEH boot crash) is largely retired** before writing driver.lua. Booting proves survivability; the base64/sha1 identity stubs (:153-160) are the MinimalCalc anti-pattern and were NOT carried into driver.lua.

**Task 2 — driver.lua authored ✅.** `src/calculator/driver.lua` (OUTSIDE the submodule). Copies HeadlessWrapper's stub surface (6-180) verbatim; inserts the native pre-stub block BEFORE `dofile("Launch.lua")`. **Minimal native `package.loaded` pre-stub set determined empirically = `{arg={}, lua-utf8 (with len), lcurl.safe}`** — base64/sha1/xml/sha2/dkjson are NOT stubbed (pure-Lua in runtime/lua/, load REAL). Parity holds at ±0.000% WITHOUT the base64/sha1 stubs → **inverse-of-MinimalCalc rule confirmed** (AC-4.1.1). Deviations (documented in-file): `print`→stderr for a clean stdout JSON protocol; POB_SRC_DIR-driven package.path for the luajit.exe lane. XML-direct load via PoB's own PassiveSpec, no parse_pob_code (AC-4.1.9).

**Task 3 — GUI-stat accessor reused ✅.** `Driver.get_stats` reads `build.calcsTab.mainOutput[stat]` (== `mainEnv.player.output[stat]`), exactly the proven full_pob_engine path. One extra OnFrame pump after load to guarantee settle. Identity with baseline JSON holds by construction (AC-4.1.2/3).

**Task 4 — respawnable worker-process host ✅.** `src/calculator/driver_worker.py`: Python parent ↔ Lua child, PROCESS isolation (not thread — LuaJIT unsafe), cwd=POB_SRC, boots driver.lua by absolute path, survives child SEH (parent sees EOF → `WorkerCrash`, does not die). `LOAD_BUILD`/`GET_STATS`/`PING`/`GC`/`SHUTDOWN` live; `EVAL_NEIGHBORS`/`APPLY_MOVE` are reachable STUBS (Epic 4 item 2/4, not built). Respawn proven (`restart()` → new pid, PING ok). **Measurements:** boot ≈0.7s; worker RSS ≈**293MB** (tree summed — venv python.exe on E: is a redirector stub, real footprint is the grandchild), Lua heap `collectgarbage("count")` ≈128-171MB → within risk-#9's 200-400MB envelope.

**Task 5 — v0.15.0 parity harness ✅.** `tests/integration/test_driver_parity.py` (`@pytest.mark.gui_parity`, `-n 1`): **8 passed**. 6/6 baselines archetype-correct at **±0.000%** ACROSS THE WORKER PROCESS BOUNDARY (attack/spell-hit→TotalDPS, dot→TotalDot), + explicit deadeye anchor (23003.185361227) + non-vacuous DoT-branch test. Inherits the pob_env drift guard. Latency: cold first-build load ≈0.9s, warm loads 0.24-0.53s, `GET_STATS` sub-millisecond (~0.15ms). **AC-4.1.2 and AC-4.1.3 PASS.**

**Task 10 — M0 five-build triage ✅.** `scripts/triage_m0_builds.py` (read-only, no engine). Corpus scan: **exactly the five (`gemling_frost_mage_100`, `lich_storm_mage_90`, `titan_infernal_cry_72`, `warrior_ballista_93`, `witch_frost_mage_91`) are the ONLY multi-`<Spec>` builds.** LEADING hypothesis CONFIRMED: buggy `_extract_passive_nodes` (pob_parser.py:391-393) returns **0 nodes** for all five (list-typed `<Spec>` → empty set) → `no_valid_neighbors` at iteration 0; the activeSpec-aware parse recovers 109-133 nodes. **Tree-version REFUTED**: `miss@0_3 == miss@0_4` for every build (residual 0-5 nodes are class-start/ascendancy nodes absent from the Python loader's graph, identical across versions; a 0_3→0_4 bump recovers none). Under the REAL driver all five load with correct node counts and the damage-dealers calc nonzero via `FullDPS` — **`lich_storm_mage_90` = 188,475 FullDPS** (its MinimalCalc 0.0 is a separate coverage gap, now closed).

**Task 6 — luajit.exe subprocess fallback lane ⚠️ PARTIAL (honest).** Lane is CODE-READY: `driver.lua` `Driver.serve()` (io.lines JSON loop) + `driver_worker.DriverWorker(lane="luajit")` spawn the SAME driver.lua as a true subprocess; the shared protocol code (`Driver.handle_command`) is already proven by the embedded lane. BUT the **binary was not staged**: no `luajit.exe` is vendored (`runtime/` has `lua51.dll` = LuaJIT DLL + no frontend), and this environment has **no C compiler** (no gcc/cc/cl/make) to build a byte-matching LuaJIT 2.1 from lupa's source — exactly the "unbounded-effort" staging risk AC-4.1.5 flags. Downloading an arbitrary third-party binary was declined (wouldn't byte-match lupa's embedded 2.1; security-sensitive). **De-risked:** the embedded lane boots with NO boot-time SEH, so the fallback is off the go/no-go critical path — a boot crash is not the failure mode we must guard against. Epic 4 stages the binary only if ever needed (bounded: MSVC + LuaJIT at lupa's revision).

**Task 7 — go/no-go verdict + measurements ✅.**

> ### 🟢 GO/NO-GO VERDICT (Story 4.1) — **GO, embedded-Lupa lane**
> The "architecturally impossible" verdict is **disproven**. The embedded-Lupa lane
> is selected on evidence:
> - **Boot:** REAL `Launch→OnInit→OnFrame→build` chain boots under `lupa.luajit21`
>   in a respawnable worker PROCESS with **no boot-time SEH** (risk #1 retired).
>   Minimal native pre-stub set = `{arg, lua-utf8(+len), lcurl.safe}`; base64/sha1/
>   xml load REAL (inverse-of-MinimalCalc confirmed).
> - **Parity:** 6/6 Tier-A GUI baselines at **±0.000%** across attack/spell-hit/DoT,
>   across the worker process boundary (deadeye 23003.185361227 exact).
> - **Latency:** boot ≈0.7s; cold first-build load ≈0.9s; warm loads 0.24–0.53s;
>   `GET_STATS` ~0.15ms → ample headroom for EVAL_NEIGHBORS batching.
> - **Memory:** worker RSS ≈**293MB** (Lua heap ≈128–171MB) — within risk-#9's
>   200–400MB envelope; pool of ~2 is affordable.
> - **Fallback:** `luajit.exe` lane is code-ready but binary-unstaged (Task 6);
>   not required since the embedded lane has no boot crash.
> Recommend Epic 4 proceeds: FullCalcEngine behind build_calculator.py + ~2-worker
> respawnable pool (ADR-006), XML-direct via PassiveSpec (ADR-007), tree 0_4→0_5
> bump + assert (ADR-008), drop the 3 nil-safety patches at MinimalCalc retirement
> (ADR-004 outcome).

**Task 8 — ADR-004 patch-necessity ✅.** Reverse-applied all 3 patches (git checkout to unpatched), booted the real-ModParser driver: **all 6 Tier-A baselines ±0.000% with ZERO patches** (incl. the ADR-004-named `ritualist_lightning_spear_96` + a DoT build); no "arithmetic on nil" at any guarded site. Verdict = **drop-candidate ×3** (MinimalCalc-only artifacts); removal DEFERRED to Epic 4 item 8. Experiment UNMARKED; env restored (`setup_pob.py` exit 0). ADR-004 status edited.

**Task 9 — v0.22.0 jump ✅.** Disposable git worktree at `860f4268` (v0.22.0, active pin stayed v0.15.0 throughout), v0220 variant of patch 0001 + 0002/0003 applied cleanly. **driver.lua BOOTS v0.22.0** — real `CalcSetup` satisfies `CollectGrantedPassiveNodesFromItems` (the exact 2026-07-02 MinimalCalc blocker, canary 18/18 F), **`TreeData/0_5` loads**. Cross-version DPS differs (deadeye 27607.88 vs 23003.19) → NOT asserted; v0.22.0 parity needs fresh GUI re-capture. Worktree removed; pin intact; `setup_pob.py` exit 0.

**Task 11 — decision artifacts + ADR stubs ✅.** ADR-004 status → "under re-evaluation" + spike-outcome addendum. Drafted stubs ADR-005 (Truth Engine/driver.lua), ADR-006 (worker process isolation + JSON protocol + lane choice), ADR-007 (XML-direct via PassiveSpec convert=true), ADR-008 (tree 0_4/0_5 bump + version assert). Item-2 integration NOT built (spike scope, AC-4.1.10).

### File List

- `src/calculator/driver.lua` (NEW) — headless Truth-Engine driver, both lanes.
- `src/calculator/driver_worker.py` (NEW) — respawnable worker-process host + JSON protocol.
- `tests/integration/test_driver_parity.py` (NEW) — gui_parity harness (8 tests).
- `scripts/triage_m0_builds.py` (NEW) — M0 no_valid_neighbors read-only triage.
- `docs/decisions/ADR-005-truth-engine-driver-lua.md` (NEW) — stub.
- `docs/decisions/ADR-006-worker-pool-process-isolation.md` (NEW) — stub.
- `docs/decisions/ADR-007-xml-direct-passivespec-convert.md` (NEW) — stub.
- `docs/decisions/ADR-008-tree-version-bump-and-assert.md` (NEW) — stub.
- `docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md` (MODIFIED) — status → under re-evaluation + spike-outcome addendum.
- `docs/sprint-status.yaml` (MODIFIED) — 4-1 status ready-for-dev → in-progress → review.

## Change Log

**2026-07-03** — Story created via BMAD create-story (ultimate context engine)
- Drafted from docs/pebo-master-plan.md §3 + §6 Epic 4 item 1 + §8; scope per docs/sprint-change-proposal-2026-07-02.md §5 (M0 riders) + §8.4 (v0.22.0 decision)
- SPIKE with pre-committed go/no-go: ACs are decision evidence with objective pass/measure conditions, not shipped features
- Status: ready-for-dev

**2026-07-03** — Spike executed via BMAD dev-story workflow → **Status: review**
- **VERDICT: 🟢 GO, embedded-Lupa lane.** driver.lua boots PoB's real chain in a respawnable worker process with no boot-time SEH; 6/6 Tier-A GUI baselines parity at ±0.000% across the process boundary (attack/spell-hit/DoT); boot ~0.7s, warm load 0.24-0.53s, GET_STATS ~0.15ms, worker RSS ~293MB.
- AC-4.1.1/2/3 PASS; AC-4.1.4 verdict recorded; AC-4.1.6 patches = drop-candidate ×3 (zero nil repro under real ModParser), env restored; AC-4.1.7 v0.22.0 boots (CalcSetup satisfies CollectGrantedPassiveNodesFromItems, TreeData/0_5 loads); AC-4.1.8 M0 = activeSpec parse gap confirmed, tree-version refuted; AC-4.1.9/10/11 honored.
- **AC-4.1.5 PARTIAL:** luajit.exe fallback lane code-ready + protocol-proven, but the binary was not staged (no compiler in this env; off critical path since the embedded lane has no boot crash).
- New: src/calculator/driver.lua, src/calculator/driver_worker.py, tests/integration/test_driver_parity.py, scripts/triage_m0_builds.py, ADR-005..008. Modified: ADR-004 (status), docs/sprint-status.yaml.
- Regression: unit 334/334 pass; driver parity 8/8 pass; setup_pob.py exit 0. (test_gui_parity.py's 14 fails are the pre-existing stale-0.12.2 MinimalCalc gap, not a regression.)

**2026-07-03** — Code review + close-out → **Status: done**
- Reviewed via max-effort workflow code review (31 agents / 6 finder angles / 22 verifiers) over `git diff 1317ac5..HEAD`; 15 findings. The happy-path GO verdict is UNAFFECTED — all spike evidence was gathered on the embedded happy path, which works.
- Applied 5 high-priority fixes (committed 0c2b355): (1) `driver_worker.py` — replaced the two unbounded blocking `readline()` reads with a bounded, kill-on-timeout `_readline_with_timeout()` (boot + per-command; new `cmd_timeout`, default 60s) so a silent boot stall or a non-terminating calc fails as a `WorkerCrash` instead of hanging the `-n 1` suite forever; (2) `driver.lua` — `Driver.load_build` now validates `promptMsg`/`mainOutput` post-load and clears `promptMsg`, so a failed/incompatible load returns `{ok=false}` instead of reporting success with stale stats; (3) `test_driver_parity.py` — `_discover()` captures per-baseline parse errors, plus `EXPECTED_BUILDS` + two integrity guards, so a missing/malformed baseline is a RED test, not a silently-skipped green.
- Verified: `setup_pob.py` exit 0; driver parity **10/10** (8 + 2 new guards); unit **334/334**.
- DEFERRED to Epic 4 item 2 (where `driver_worker.py` graduates from spike script to a production pool): the crash-survival hardening cluster (`_send` unguarded `json.loads`, leaked pipes on `WorkerCrash`, empty `stderr_tail`, `get_stats` error-envelope leak), the `EVAL_NEIGHBORS`/`APPLY_MOVE` `cmd`-override, the `CombinedDPS`/`FullDPS` stat fallback, the triage per-build `try/except`, and automated crash-survival + `luajit.exe`-lane test coverage.
- Infra: the `[AutoSave]` Stop-hook had committed the dirty ADR-004 patches INSIDE `external/pob-engine` (submodule HEAD → `97f50b1a`, off the pin → `setup_pob.py` exit 5). Restored (`checkout --detach 3e1b71c9` + `setup_pob.py`) and guarded `auto_commit.py` to refuse the `--autosave` path inside any submodule.