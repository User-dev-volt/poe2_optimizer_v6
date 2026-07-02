# Story 3.5.2: Re-establish Real Submodule Pinned to v0.22.0; Generated POB_VERSION.txt

> **Retargeted 2026-07-02:** Alec's decision (`docs/sprint-change-proposal-2026-07-02.md`, Decisions) moved the pin from the forensics-recommended v0.15.0 to **v0.22.0** (latest upstream release) and pre-approved patch promotion — which was **executed the same day**: `external/patches/` now holds `0001` (regenerated + verified against v0.22.0), `0002`/`0003` (verified on both tags), `.gitattributes`, and a rewritten README; the stale 0.12.2 patch is retired. This story text was amended accordingly; v0.15.0 references remain only where they describe the *current* tree or the forensic diff base.
>
> **⚠ FALLBACK EXECUTED (same day, later):** the v0.22.0 jump was attempted and **rolled back per AC-3.5.2.5's pre-committed fallback lane**. MinimalCalc cannot boot v0.22.0's `CalcSetup` (`:875 env.spec:CollectGrantedPassiveNodesFromItems` — a new granted-passive-nodes + weapon-slot-keystone API our `spec`/`itemsTab` doubles don't implement); canary 18/18 failed, full integration 119 failed / 125 passed. **The story landed at pin v0.15.0 `3e1b71c9`** — real submodule, same mechanics, all patches applied, tree content-identical to the pre-repair backup (EOL-controlled diff: 0 entries). The jump re-lands with Epic 4's Truth Engine (which deletes MinimalCalc); the v0.22.0 patch variant is parked at `docs/forensics/proposed-patches/0001-global-lua-nil-safety-v0220.patch`, and the submodule's git history already contains v0.22.0 (no re-clone needed). Read the ACs below through that lens: every mechanical AC holds at the v0.15.0 pin.

Status: done  <!-- marked done 2026-07-02 after merge of feat/story-3.5.2-submodule-repair to main (e7f7edd) -->

**Epic:** 3.5 — Substrate & Trust (lite) → v0.9 (internal)
**Tracking key:** `3.5-2-submodule-repair-and-pin` (`docs/sprint-status.yaml:95`)
**Effort:** 6–8h
**Dependencies:** 3.5.1 (`3.5-1-pob-engine-forensics`) — the forensics inventory MUST be ratified before any destructive step; repairing without it clobbers unknown edits (plan risk #2, CRITICAL, `docs/pebo-master-plan.md:313`). The 3.5.1 kick-off run has landed: `docs/forensics/pob-engine-forensics-2026-07-02.md`.
**Blocks:** 3.5.3 (`setup_pob.py` wraps this story's generator), 3.5.4 (conftest verify consumes the generated `POB_VERSION.txt`), 3.5.5 (baseline metadata must reference the pinned version).

## Story

As the **PEBO maintainer**,
I want **`external/pob-engine` converted from an unverifiable vendored blob back into a real git submodule pinned to the v0.22.0 release commit (`860f4268`), with every adopted local edit preserved as `external/patches/*.patch` and `POB_VERSION.txt` generated from the gitlink — never hand-edited**,
so that **the engine version is verifiable by tooling, the four-way version drift (v0.12.2 pin / phantom gitlink `4cf3563f6` / 0.15.0 tree / GUI-0.12.2 baselines) is resolved, and no future re-clone or hand-edit can silently regress the nil-safety fixes spell builds depend on**.

## Acceptance Criteria

1. **AC-3.5.2.1:** `external/pob-engine` is a real git submodule pinned to the v0.22.0 release commit
   - `.git` link file present in `external/pob-engine/` and a corresponding `.git/modules/` entry exists in the superproject (today: neither exists — the tree is 1,615 files invisible to `git status`)
   - `git submodule status` reports clean (no `-` uninitialized prefix, no `+` drift)
   - Submodule HEAD == parent gitlink == `860f4268299739ce9df87c4f373abe35824101cf` (tag `v0.22.0`, "Release 0.22.0" — the pin decided 2026-07-02, superseding the forensics diff base `3e1b71c9`/v0.15.0)
   - The phantom gitlink `4cf3563f621163cda591d9e903576dc1f0a0ae6b` (unfetchable — absent locally and upstream) is replaced in the parent index

2. **AC-3.5.2.2:** Working tree == pinned commit + applied `external/patches/*.patch` and nothing else
   - Every 3.5.1 **adopt-as-patch** disposition exists as a patch file in `external/patches/`. Per the ratified forensics inventory (section 4: 3 KEEP-AS-PATCH, 0 REJECT, 0 GENERATED) that set is exactly: `src/Data/Global.lua` (ADR-004 nil-safety), `src/Classes/ModStore.lua` EvalMod nil-guard, and `src/Modules/CalcOffence.lua` ailment-buildup guard. **Already satisfied 2026-07-02:** promoted as `external/patches/0001..0003` (0001 regenerated against v0.22.0 — upstream still lacks the guards; 0002/0003 apply-verified on both v0.15.0 and v0.22.0); the v0.15.0-targeted drafts remain under `docs/forensics/proposed-patches/` as the forensic record
   - The conditional adopts named in the change proposal are resolved on forensics evidence: `ModStore.lua` **is** adopted (draft 0002, first-ever capture); `src/Export/stub_functions.lua` is **not present** in the vendored tree (file census: 0 added files) despite being documented at `docs/architecture/pob-engine-dependencies.md:734` — record this disposition, nothing to patch
   - Every **reject** disposition is restored to upstream (forensics found 0 — the repaired tree must confirm none appear)
   - EOL-controlled diff of the repaired tree vs the pre-repair backup shows **exactly the upstream v0.15.0→v0.22.0 delta and nothing else**: no local edit other than the 3 patches may survive, and all 3 patch sentinels must be present. (The forensics byte-identical guarantee — clean v0.15.0 + 3 patches == live tree — pins the *edit inventory*; the version jump means the whole-tree diff vs backup is upstream churn, not emptiness. Equivalent mechanical check: repaired tree == clean `860f4268` checkout + `external/patches/0001..0003`, byte-for-byte)
   - `external/patches/README.md` lists the full patch set — **already satisfied 2026-07-02** (rewritten: 0001..0003 with sentinels, provenance, LF/apply discipline; stale 0.12.2 patch retired); this story re-verifies it matches reality post-repair

3. **AC-3.5.2.3:** `POB_VERSION.txt` is generated by script from the gitlink — hand-editing detectable
   - Generator derives content from the parent gitlink (commit hash) plus the human-readable version from `external/pob-engine/manifest.xml` (today `<Version number="0.15.0" />` at `manifest.xml:3`; reads `0.22.0` after this story's checkout — verified in the v0.22.0 tag); never typed by hand
   - File carries a generation marker so 3.5.4's `pob_env.verify()` and 3.5.3's `setup_pob.py` can detect a stale or hand-edited file
   - The stale content is gone: today's file pins `69b825bda` / v0.12.2-61 (`POB_VERSION.txt:4-7`) and advises `git submodule update --remote` (`POB_VERSION.txt:17`) — the exact reversion hazard `docs/HANDOFF-2026-06-29-OPTIMIZER-NOOP-FIXED.md:84-86` warns about

4. **AC-3.5.2.4:** Existing GUI-0.12.2 parity baselines are flagged stale, not silently reused
   - `tests/fixtures/parity_builds/gui_baseline_stats.json` `_metadata` (`pob_version: "0.12.2"`, `date_recorded: "2025-10-21"`) gains an explicit stale flag — or a stale-baseline manifest is added — machine-readable by 3.5.4's verify
   - The flag states why: baselines were captured from GUI 0.12.2; the pinned engine is now v0.22.0, so every parity comparison crosses engine versions until re-capture
   - Re-capturing baselines is explicitly OUT of scope here (3.5.5 harvests 6–8 geared Tier-A baselines; mass capture is Epic 4 item 6)

5. **AC-3.5.2.5:** Test suites pass after repair — no silent dependency on a rejected edit, no jump regression
   - `pytest tests/unit/` passes
   - `pytest -n 1 tests/integration/` passes (`-n 1` is mandatory on Windows — CLAUDE.md constraint, ADR-003)
   - Spell/DOT integration tests (e.g. `tests/integration/test_story_2_9_2_spell_builds.py`) pass — these exercise all three patched files and are the canary for a lost patch
   - Parity tests that fail or skip **because** their baselines are stale-flagged per AC-3.5.2.4 count as a pass condition for this story, not a failure
   - **Jump caveat (v0.15.0→v0.22.0):** absolute numbers may legitimately shift with the engine version — a changed value alone is not a failure; a crash, a lost-sentinel, or a build that stops calculating is. If v0.22.0 regressions block the suites and can't be triaged quickly, the pre-committed fallback is the same mechanics pinned at `3e1b71c9` (v0.15.0) — record the fallback in the proposal if taken

## Tasks / Subtasks

- [ ] Task 1: Back up the current `external/pob-engine` tree before any destructive step (AC: precondition for all — plan risk #2 mitigation)
  - [ ] Subtask 1.1: Confirm the 3.5.1 forensics report and the three draft patches under `docs/forensics/proposed-patches/` are committed — until then they are the only durable record of the two never-captured edits (forensics section 6 step 1)
  - [ ] Subtask 1.2: Copy/move `external/pob-engine` → `external/pob-engine.pre-repair-2026-07-02` (~326 MB, 1,615 files); retain until Task 6 is green (forensics section 6 step 3)

- [x] Task 2: Promote/author patch files for every adopt disposition — **EXECUTED 2026-07-02** per the Decisions pre-approval (AC: 3.5.2.2); at story kickoff only re-verify
  - [x] Subtask 2.1: Drafts promoted into `external/patches/` as `0001..0003`; stale 0.12.2-cut `global-lua-nil-safety.patch` retired (`git rm`). `0001` was **regenerated against v0.22.0** (the v0.15.0 draft fails on context drift there; upstream v0.22.0 verified to still lack the guards — only the `#args<2` early-return is nil-safe)
  - [x] Subtask 2.2: `*.patch -text` `.gitattributes` added to `external/patches/`
  - [x] Subtask 2.3: Verified: `0001` forward-applies clean on a v0.22.0 checkout (sentinel ×3, LuaJIT compile check passed); `0002`/`0003` forward-apply clean on **both** v0.15.0 and v0.22.0 and reverse-check PASS against the live tree (edits present)
  - [x] Subtask 2.4: `external/patches/README.md` rewritten (sentinels, provenance, LF/apply discipline, skip-if-applied rule); ADR-004 gained a 2026-07-02 addendum. stub_functions.lua not-present disposition recorded in the forensics report
  - [ ] Subtask 2.5 (at kickoff): re-run the three `git apply --check` verifications against the freshly cloned v0.22.0 checkout before Task 4 — guards against bit-rot between now and execution

- [ ] Task 3: Re-establish the submodule; check out the release commit; update the parent gitlink (AC: 3.5.2.1)
  - [ ] Subtask 3.1: Verify `.gitmodules` URL is already correct (`https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2.git`) — it is; no edit expected
  - [ ] Subtask 3.2: Do NOT run plain `git submodule update --init` — it would try to check out the phantom `4cf3563f6` and fail (forensics section 6 step 4). Instead: fresh clone with `git -c core.autocrlf=false -c core.eol=lf clone <url> external/pob-engine`, then `git -C external/pob-engine checkout --detach 860f4268299739ce9df87c4f373abe35824101cf` (LF working tree matches the runtime-tested EOL convention; upstream `.gitattributes` is `* text=auto`. Note: v0.22.0 is a version JUMP, not today's runtime-tested content — Task 6 is the acceptance gate)
  - [ ] Subtask 3.3: `git submodule absorbgitdirs external/pob-engine`, then `git add external/pob-engine` to replace the phantom gitlink with the real `860f4268...`
  - [ ] Subtask 3.4: Verify AC-3.5.2.1 mechanically: `.git` link file present, `.git/modules` entry exists, `git submodule status` clean, `git ls-tree HEAD external/pob-engine` == submodule HEAD == `860f4268...`

- [ ] Task 4: Apply the full patch set; diff result vs backup (AC: 3.5.2.2)
  - [ ] Subtask 4.1: Apply patches in order 0001→0003 (independent; numbered for determinism) from repo root with `git -c core.autocrlf=false apply` (or `git -C external/pob-engine apply -p3` inside the submodule)
  - [ ] Subtask 4.2: Verify the grep sentinels **by content, not line number** (v0.22.0 lines differ from the 0.15.0-era citations): `Global.lua` `or 0  -- Handle nil arguments` ×3, `ModStore.lua` `Nil-safety patch (Story 2.9.2)` ×1, `CalcOffence.lua` `continue_ailment` ×2
  - [ ] Subtask 4.3: EOL-controlled diff repaired tree vs backup (`git -c core.autocrlf=false diff --no-index --ignore-cr-at-eol`): expected content = **upstream v0.15.0→v0.22.0 churn only**. Spot-verify the three patched files: each must differ from backup by upstream changes at most, with all sentinels present; any NON-upstream delta (a fourth local edit surviving, or a lost patch) is a defect. Mechanical equivalent: `cmp` the repaired tree against clean `860f4268` + patches applied

- [ ] Task 5: Write the `POB_VERSION.txt` generator and generate the file (AC: 3.5.2.3)
  - [ ] Subtask 5.1: Implement the generator (in `scripts/`) reading the parent gitlink commit + `manifest.xml` version; design it as the piece 3.5.3's `setup_pob.py` will call on every run ("shared with 3.5.3" — one implementation, two entry points)
  - [ ] Subtask 5.2: Emit a generation marker (e.g. generated-by line + source gitlink echo) sufficient for 3.5.4 to detect hand-edits/staleness by regenerating and comparing
  - [ ] Subtask 5.3: Generate, replacing the stale v0.12.2 file; the `git submodule update --remote` advice must not survive
  - [ ] Subtask 5.4: Include the applied-patch list in the generated content (forensics section 6 step 6) so version + patch state travel together

- [ ] Task 6: Mark 0.12.2 baseline metadata stale; run the unit + integration suites (AC: 3.5.2.4, 3.5.2.5)
  - [ ] Subtask 6.1: Flag `tests/fixtures/parity_builds/gui_baseline_stats.json` `_metadata` stale (e.g. `stale: true` + reason + engine-now vs captured-from versions), or add a stale-baseline manifest — whichever 3.5.4's verify can consume as data
  - [ ] Subtask 6.2: `pytest tests/unit/` — green
  - [ ] Subtask 6.3: `pytest -n 1 tests/integration/` — green, explicitly including the Story 2.9.2 spell-build tests (canary for all three patches). Numbers are NOT expected bit-identical (engine jumped v0.15.0→v0.22.0): triage failures as (a) lost patch — sentinel check, (b) upstream behavior change — compare against the v0.15.0 fallback lane, (c) genuine breakage. Blocking regressions → fall back to pin `3e1b71c9` (identical mechanics, AC-3.5.2.5 jump caveat)
  - [ ] Subtask 6.4: Record the AC4 stale-flag pass condition for any parity test that now refuses stale baselines; only after green may the Task 1 backup be deleted

## Dev Notes

- Relevant architecture patterns and constraints
  - **Diff-before-destroy is already complete.** 3.5.1's forensics proved the vendored tree == upstream v0.15.0 (`3e1b71c9...`) + exactly 3 hand-patched Lua files (+41/−29), with byte-identical reconstruction from clean blobs + the 3 draft patches verified (forensics sections 1, 4, 5). This story's repair is therefore content-preserving *by construction*: any post-repair content deviation from the backup is a defect, not a judgment call.
  - **The recorded gitlink is a phantom.** `4cf3563f621163cda591d9e903576dc1f0a0ae6b` exists neither locally nor upstream (GitHub API 422; `git fetch` "not our ref") — it died with the submodule's `.git` in the 2026-01-26 non-recursive re-clone (forensics sections 2.1, 3). Consequence: the standard `git submodule update --init` path is a trap; the re-init must clone + detach-checkout the release commit, then `absorbgitdirs` + re-add (Task 3).
  - **LF policy.** Upstream `.gitattributes` is `* text=auto`; a default Windows checkout renders CRLF while the vendored (runtime-tested) tree is LF — the source of 1,067 phantom `M` entries and false-negative `git apply --check` runs (forensics section 4). Engine clone must use `core.autocrlf=false` (+ `core.eol=lf`); patch files carry `*.patch -text`.
  - **Generated, never hand-edited.** Plan Epic 3.5 item 2 (`docs/pebo-master-plan.md:173-174`): "`POB_VERSION.txt` becomes *generated* from the gitlink, never hand-edited." The manual procedure that produced the drift (`git checkout <hash>` + `echo > POB_VERSION.txt`, `docs/PRD.md:677-689`) is the documented anti-pattern this story retires (change proposal section 7.1-K).
  - **Scope boundaries (respect the story split and the v1 NOT-list, plan section 5):** the idempotent `setup_pob.py` wrapper is 3.5.3; the autouse conftest `pob_env.verify()` enforcement is 3.5.4; baseline re-capture is 3.5.5 (mass capture Epic 4 item 6). The 2026-07-02 jump decision folds the FIRST version bump (→v0.22.0) into this story; subsequent bumps remain the standing patch-day workstream (`docs/pebo-master-plan.md:275-279`). ADR-004 got its addendum 2026-07-02; remaining doc banners stay PROPOSED-only in the change proposal (section 7.3-E).
  - **Jump ripple — tree data:** v0.22.0 ships `TreeData/0_5/` (verified in the tag; the 0.15.0-era tree tops out at `0_4`). The master plan's Epic 4 item 3 "tree 0_3→0_4 bump" and Epic 5A artifacts (`TreeData/0_4/tree.json`) therefore target **0_5** under this pin — recorded as a plan amendment; nothing in THIS story touches `passive_tree.py` (its `0_3` default is Epic 4 scope).
  - **Alec decision gate — RESOLVED 2026-07-02** (`docs/sprint-change-proposal-2026-07-02.md`, Decisions): Q1 promote the 3 drafts = APPROVED and executed same day; Q2 pin target = **v0.22.0** `860f4268` (overriding the forensics' 0.15.0-first recommendation; forensics section 6 step 10's "evaluate v0.22.0 later" is accelerated into this story); Q3 = real submodule per plan wording ("convert every local edit into `external/patches/*.patch` or consciously reject it", `docs/pebo-master-plan.md:169-172`). No open gate remains before Task 3; the only kickoff check is Subtask 2.5 re-verification.

- Source tree components to touch
  - `external/pob-engine/` — re-established as a real submodule (destructive; backed up first)
  - `.gitmodules` — verify only (URL already correct)
  - Parent gitlink for `external/pob-engine` — updated `4cf3563f6...` (phantom) → `860f4268...` (v0.22.0)
  - `external/patches/` — DONE 2026-07-02: `0001`/`0002`/`0003` promoted in (0001 regenerated for v0.22.0); stale `global-lua-nil-safety.patch` retired; `README.md` rewritten; `.gitattributes` (`*.patch -text`) added. This story only re-verifies
  - `POB_VERSION.txt` — regenerated by the new script
  - `scripts/` — new generator module (first piece of 3.5.3's `setup_pob.py`)
  - `tests/fixtures/parity_builds/gui_baseline_stats.json` — `_metadata` stale flag (or new stale-baseline manifest)

- Testing standards summary
  - Integration tests MUST run `pytest -n 1` on Windows (LuaJIT SEH cleanup, exception `0xe24c4a02` is normal — CLAUDE.md, ADR-003)
  - Gate before deleting the backup: unit + integration green, spell-build tests included (they exercise all three patched files)
  - Parity marker tests (`-m parity` / `gui_parity`): stale-flagged-by-AC4 outcomes count as pass for this story; hard enforcement (FAIL-not-skip) arrives with 3.5.4

### Project Structure Notes

- Alignment with unified project structure
  - Tracking key `3.5-2-submodule-repair-and-pin` under `epic-3.5` in `docs/sprint-status.yaml:95`; the `3.5-N-slug` convention avoids collision with epic-3 `3-N-...` keys (change proposal section 3.2)
  - Story filename `story-3.5.2-submodule-repair-and-pin.md` per change proposal section 8.1
  - Extends the existing `external/patches/` mechanism established by ADR-004 — same directory, same apply-verify discipline, now with numbered patches and an LF gitattribute
- Detected conflicts or variances (with rationale)
  - The change proposal's AC2 wording anticipated patches "incl. ModStore.lua and stub_functions.lua if adopted"; the forensics run resolved both conditionals with evidence (ModStore.lua adopted as draft 0002; stub_functions.lua absent from the tree — census 0 added files, direct check confirms). The story adopts the forensics-ratified set of exactly three patches.
  - `docs/architecture/pob-engine-dependencies.md:509-513,734,766-769` documents the ModStore edit at lines 444/464 and a stub_functions.lua; the live tree has the ModStore guard near line 458 (0.15.0 drift) and no stub file. The forensics report, not the architecture doc, is authoritative for current tree state; the doc's supersession banner is a PROPOSED edit in the change proposal (section 7.3-A), out of this story's scope.

### References

- [Source: docs/pebo-master-plan.md#6 Epic 3.5 item 2 (lines 173-174)] — the story's mandate: real submodule, pinned release commit, generated POB_VERSION.txt (plan text says 0.15.0; pin amended to v0.22.0 by the 2026-07-02 decision — see the plan's amendment note and the proposal Decisions section)
- [Source: docs/pebo-master-plan.md#6 Epic 3.5 items 1,3,4 (lines 169-172,175-179)] — forensics precondition; setup_pob.py (3.5.3) and conftest verify (3.5.4) as the consumers of this story's outputs
- [Source: docs/pebo-master-plan.md#8 risk #2 (line 313)] — CRITICAL: repair clobbers unknown local edits; mitigation = diff-before-destroy, every hunk a patch file or conscious rejection
- [Source: docs/pebo-master-plan.md#9 items 2-3 (lines 329-331)] — immediate-actions sequence: forensics → repair/pin/setup/conftest
- [Source: docs/pebo-master-plan.md#2 item 4 (lines 55-59); Appendix A (lines 355-356)] — the four-way drift evidence this story resolves
- [Source: docs/pebo-master-plan.md#Standing workstream (lines 275-279)] — future engine bumps (`update_pob.py`) are out of this story
- [Source: docs/sprint-change-proposal-2026-07-02.md#8.1 Story 3.5.2] — canonical story definition, ACs, effort, dependency
- [Source: docs/forensics/pob-engine-forensics-2026-07-02.md#2 (version table), #4 (edit inventory), #5 (draft patches + byte-identical verification), #6 (remediation sequence steps 1-8), #7 (open questions)] — the 3.5.1 deliverable this story executes against
- [Source: POB_VERSION.txt:4-7,17] — stale pin (`69b825bda`, v0.12.2-61, "Date Pinned: 2025-10-12") and the hazardous `--remote` update advice
- [Source: external/pob-engine/manifest.xml:3] — `<Version number="0.15.0" />` today; reads `0.22.0` post-checkout (verified in the v0.22.0 tag) — the human-readable version input to the generator
- [Source: tests/fixtures/parity_builds/gui_baseline_stats.json (`_metadata`)] — `pob_version: "0.12.2"`, `date_recorded: "2025-10-21"`: the baselines AC4 flags stale
- [Source: external/patches/README.md; docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md incl. 2026-07-02 addendum] — patch mechanism; README now lists the promoted 0001..0003 set
- [Source: docs/architecture/pob-engine-dependencies.md:509-513,734,766-769] — the documented-but-unpatched edits that triggered the forensics mandate
- [Source: docs/HANDOFF-2026-06-29-OPTIMIZER-NOOP-FIXED.md:84-86] — prior warning that `git submodule update` silently reverts the nil-safety patch
- [Source: CLAUDE.md#Windows LuaJIT; docs/decisions/ADR-003-windows-luajit-cleanup-mitigation.md] — `pytest -n 1` integration constraint

## Dev Agent Record

### Context Reference

Executed directly from this story + `docs/forensics/pob-engine-forensics-2026-07-02.md` + proposal §8.4 decisions (no separate context XML; the forensics report IS the context).

### Agent Model Used

claude-fable-5 (Claude Code, session 2026-07-02)

### Debug Log References

- Pre-flight: `git apply --check` ×3 PASS on fresh v0.22.0 checkout (Subtask 2.5)
- `git submodule status` → ` 860f4268... external/pob-engine (v0.22.0)` (clean, tag resolved)
- Sentinels post-apply: Global 3 / ModStore 1 / CalcOffence 2; backup tree also 3/1/2 (fix continuity across the jump)
- `generate_pob_version.py` double-run md5-identical: `7ae23140e099bb14c35ad64aec6026a4`; `--check` mode green

### Completion Notes List

1. **Task 1** — backup by move (instant, same volume): `external/pob-engine.pre-repair-2026-07-02/`; gitignored via new `.gitignore` pattern `external/pob-engine.pre-repair-*/`. Retain until Task 6 gate confirmed + soak (do NOT delete this session).
2. **Task 2** — promotion had been executed earlier the same day (proposal §8.4); Subtask 2.5 re-verification: all three patches apply-check PASS against the fresh clone at `860f4268`.
3. **Task 3** — full clone (1.9 GB incl. history), `checkout --detach 860f4268299739ce9df87c4f373abe35824101cf`, `git submodule init` + `absorbgitdirs` (gitdir migrated to `.git/modules/external/pob-engine`, `.git` gitfile left in place), `git add` replaced the phantom gitlink. `manifest.xml` reads `0.22.0`.
4. **EOL deviation (documented, accepted):** upstream v0.22.0 **blobs are CRLF in-repo** — `* text=auto` skips eol conversion for already-CRLF blobs, so the faithful checkout is CRLF regardless of `core.eol=lf`. The story's "LF working tree" wording assumed LF blobs (true of the 0.15.0-era vendored tree, not of v0.22.0 upstream). Actions: repo-local `core.autocrlf=false` + `core.eol=lf` set as policy; patches (LF, `-text`-protected) apply cleanly via git's attribute-aware matching; `git status` clean pre-patch; runtime is EOL-neutral for Lua. 3.5.3/3.5.4 must use `git apply`-based checks (already the design), not byte comparisons, for applied-state.
5. **Task 4** — applied 0001→0003 from repo root; submodule shows exactly the 3 patched files modified (+26/−14); AC-3.5.2.2's mechanical equivalent holds by construction (fresh tag checkout + verified patches; nothing else differs).
6. **Task 5** — `scripts/generate_pob_version.py` (importable; `generate(repo_root, check_only)`); output is a pure function of gitlink + manifest + patch states (timestamp-free per 3.5.3 reconciliation); refuses to stamp when submodule HEAD ≠ gitlink; URL read from `.gitmodules` (no second hardcoded copy); `--check` mode = the 3.5.4 hand-edit detection primitive. `external/POB_VERSION.txt` regenerated (previously untracked + hand-written; now tracked + generated; the hazardous `git submodule update --remote` advice is gone).
7. **Task 6** — `gui_baseline_stats.json` `_metadata` gained `stale: true` + machine-readable reason + recapture pointer (AC-3.5.2.4). Unit suite: **262 passed** (baseline 252 + newer tests). Integration: v0.22.0 attempt **119F/125P** (blocked, see note 8); fallback pin canary **18/18 passed**; full-suite result on the fallback pin recorded in the Change Log.
8. **AC-3.5.2.5 fallback exercised** — v0.22.0's `CalcSetup.lua:875` calls `env.spec:CollectGrantedPassiveNodesFromItems` (+ `SetGrantedPassiveNodes`/`UpdateSockets`/`ValidateWeaponSlots` behind it): new API contracts MinimalCalc's doubles don't satisfy. Triage verdict: stub-whack-a-mole against code Epic 4 deletes, with unvalidatable 0.22.0 semantics — fell back to `3e1b71c9` (v0.15.0) as pre-committed. Post-fallback: sentinels 3/1/2, gitlink re-pinned, `POB_VERSION.txt` regenerated (0.15.0), **EOL-controlled diff vs pre-repair backup = 0 entries** (the forensics byte-identical guarantee held). v0.22.0 objects remain in the submodule's history for the Epic 4 jump.

### File List

- `external/pob-engine` — gitlink `4cf3563f6` (phantom) → `860f4268` (v0.22.0); real submodule re-established
- `external/POB_VERSION.txt` — regenerated (first time tracked)
- `scripts/generate_pob_version.py` — new (shared generator, 3.5.3 consumes)
- `tests/fixtures/parity_builds/gui_baseline_stats.json` — `_metadata` stale flag
- `.gitignore` — backup-dir pattern
- `docs/stories/story-3.5.2-submodule-repair-and-pin.md` — this record

## Change Log

**2026-07-02** — Story created via correct-course sprint change proposal
- Drafted per `docs/sprint-change-proposal-2026-07-02.md` section 8.1 (Epic 3.5 insertion, derived 1:1 from `docs/pebo-master-plan.md` section 6, Epic 3.5 item 2)
- Acceptance criteria and tasks grounded in the ratified 3.5.1 forensics inventory (`docs/forensics/pob-engine-forensics-2026-07-02.md`)
- Status: drafted; blocked by 3.5.1 ratification (Alec decision gate on patch promotion)

**2026-07-02 (later)** — Retargeted to v0.22.0; promotion executed
- Alec decisions (proposal Decisions section): promote patches ✓ (executed — Task 2 marked done, verify-only at kickoff), pin = v0.22.0 `860f4268` (jump, superseding 0.15.0), real submodule ✓
- 0001 regenerated + verified against v0.22.0 (upstream still unguarded); 0002/0003 verified on both tags; jump caveat added to AC5; TreeData 0_5 ripple noted; decision gate resolved

**2026-07-02 (execution)** — Story EXECUTED; v0.22.0 jump attempted → AC5 fallback to v0.15.0
- Backup by move → fresh full clone (1.9 GB) → detach `860f4268` → absorbgitdirs → patches → generator: all mechanics green at v0.22.0, but MinimalCalc cannot boot the v0.22.0 `CalcSetup` API (canary 18/18 F, integration 119F/125P) → **fallback executed**: detach `3e1b71c9` (v0.15.0), 0001 swapped to the v0.15.0 variant (v0.22.0 variant parked as `...-v0220.patch`), patches re-applied (sentinels 3/1/2), gitlink re-pinned, `POB_VERSION.txt` regenerated (0.15.0, deterministic, `--check` green)
- Validation: EOL-controlled diff vs pre-repair backup = **0 entries**; unit **262 passed**; canary **18/18 passed**; full integration on fallback pin = **14 failed / 231 passed / 2 xfailed in 23:06** — the 14 verified to be exactly `tests/integration/test_gui_parity.py`'s tracked calc-gap reds (module re-run: 14F/21P; the deliberately-kept GUI-truth tracker per the 2026-06-29 baseline, now also stale-flagged per AC4). **Zero unexpected failures → AC-3.5.2.5 PASS.**
- EOL finding: upstream blobs are CRLF in-repo (`text=auto` skips converted-checkout for them) — LF config retained as policy, applied-state checks must stay `git apply`-based (they are)
- Status → review (SM: verify AC1-AC4 mechanically; AC5 via the suite results; backup dir retained pending soak)
