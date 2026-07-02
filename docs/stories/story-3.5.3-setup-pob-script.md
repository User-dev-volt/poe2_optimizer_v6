# Story 3.5.3: scripts/setup_pob.py — Idempotent Setup + Patch Auto-Apply (the ONE setup command)

Status: drafted

- **Epic:** 3.5 — Substrate & Trust (lite) → v0.9 (internal) [Source: docs/pebo-master-plan.md:168]
- **Tracking key:** `3.5-3-setup-pob-script` [Source: docs/sprint-status.yaml:96]
- **Effort:** 4–5h (inside the Epic 3.5 envelope of 25–35h) [Source: docs/sprint-change-proposal-2026-07-02.md:316; docs/pebo-master-plan.md:288]
- **Dependencies:** Story 3.5.2 (`3.5-2-submodule-repair-and-pin`) — needs the real submodule, the ratified patch set in `external/patches/`, and the `POB_VERSION.txt` generator to exist. Story 3.5.4 depends on this story (its verify branches on this script's behavior and exit codes).
- **Source:** `docs/pebo-master-plan.md` section 6, Epic 3.5 item 3; `docs/sprint-change-proposal-2026-07-02.md` section 8.1

## Story

As **any developer or agent setting up this repo (fresh clone or existing checkout)**,
I want **ONE idempotent setup command that initializes/updates the submodule to the pinned gitlink, auto-applies every patch in `external/patches/`, and regenerates `POB_VERSION.txt`**,
so that **a correct PoB engine environment is a single command — not the manual checkout/echo procedure that produced the four-way version drift**.

Plan charter: "`scripts/setup_pob.py` (idempotent): submodule init/update + auto-apply all patches (`git apply --check --reverse` skip-if-applied); the ONE setup command in README." [Source: docs/pebo-master-plan.md:175-176]

## Acceptance Criteria

1. **AC-3.5.3.1:** `python scripts/setup_pob.py` performs git submodule init + update (to the pinned gitlink), then applies every patch in `external/patches/*.patch` in deterministic order
   - Submodule step targets `external/pob-engine` per `.gitmodules` (`git submodule update --init` semantics — checks out the parent gitlink commit; never `--remote`)
   - Patch set is discovered by globbing `external/patches/*.patch` — patch filenames are NEVER hardcoded
   - Patches apply in sorted-filename order (deterministic across platforms)
   - Patches apply from the submodule root with paths relative to it, matching the ADR-004 convention (`cd external/pob-engine && git apply ../../external/patches/<name>.patch`) [Source: docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md:197-207]
   - Per-patch outcome is reported: `applied` / `skipped (already applied)` / `FAILED`

2. **AC-3.5.3.2:** Idempotent via skip-if-applied logic; a second consecutive run succeeds with zero changes
   - Decision per patch: `git apply --check` succeeds → apply it; else `git apply --reverse --check` succeeds → already applied, skip; else → conflict, error (see AC-3.5.3.5) [Source: docs/pebo-master-plan.md:175-176]
   - Second consecutive run exits 0, reports every patch as skipped, and modifies no file (submodule working tree and `POB_VERSION.txt` byte-identical to the first run)
   - Proven by an automated test OR a recorded double-run transcript in this story's Completion Notes

3. **AC-3.5.3.3:** Every run regenerates `POB_VERSION.txt` from the gitlink so the file can never drift silently
   - Uses the SAME generator implementation delivered in Story 3.5.2 (imported or folded in — exactly one implementation in the codebase, no duplicate) [Source: docs/stories/story-3.5.2-submodule-repair-and-pin.md AC3, Task 5]
   - Generator output is a pure function of gitlink commit + manifest version (no timestamps), so regenerating on an unchanged pin is byte-identical — this is what keeps AC-3.5.3.2's zero-change property true
   - A hand-edited `POB_VERSION.txt` is overwritten on the next run; hand-editing cannot survive the ONE setup command [Source: docs/pebo-master-plan.md:173-174]

4. **AC-3.5.3.4:** README setup section replaced with the single command; old manual procedure removed from README
   - README Setup (`README.md:12-23`) documents `python scripts/setup_pob.py` as the ONE setup command (after clone + `pip install -r requirements.txt`)
   - README's manual PoB update guidance — `git pull origin main` + "Update POB_VERSION.txt with new commit hash" (`README.md:113-118`) — is removed/replaced with the script invocation
   - No remaining README text contradicts the single-command flow (sweep the whole file, including the monthly re-validation section at `README.md:102-157`)

5. **AC-3.5.3.5:** Loud, actionable failures with distinct nonzero exit codes
   - Missing/uninitialized submodule (no real git repo at `external/pob-engine` after the init/update attempt) → distinct exit code + remediation message
   - Patch conflict (neither `--check` nor `--reverse --check` passes) → distinct exit code; the message names the patch file AND the target file(s) it failed against
   - Gitlink/working-tree mismatch (submodule HEAD != parent gitlink) → distinct exit code + remediation message; the script must NOT destructively reset the submodule to "fix" it (plan risk #2 lesson: never destroy state the user hasn't dispositioned) [Source: docs/pebo-master-plan.md:313]
   - Exit codes are documented (module docstring and/or `--help`) and stable — Story 3.5.4's verify and future CI branch on them

## Tasks / Subtasks

- [ ] Task 1: Scaffold `scripts/setup_pob.py` (AC: 3.5.3.1, 3.5.3.5)
  - [ ] Subtask 1.1: stdlib only (`argparse`, `pathlib`, `subprocess`) — no new entries in `requirements.txt`
  - [ ] Subtask 1.2: All git calls via `subprocess` with list args and explicit `cwd`; never `shell=True` (Windows path-quoting hazard)
  - [ ] Subtask 1.3: `main()` flow: preflight (git on PATH, `.gitmodules` present) → submodule init/update → verify real repo + HEAD == gitlink → apply patches → regenerate `POB_VERSION.txt` → one-line summary
  - [ ] Subtask 1.4: Gitlink check: compare `git ls-files -s external/pob-engine` (parent gitlink) against `git -C external/pob-engine rev-parse HEAD`; mismatch → AC-3.5.3.5 exit

- [ ] Task 2: Patch discovery, deterministic ordering, per-patch reporting (AC: 3.5.3.1)
  - [ ] Subtask 2.1: Glob `external/patches/*.patch` with `sorted()` filenames; ignore non-patch files (the directory also holds `README.md`)
  - [ ] Subtask 2.2: Iterate the directory — never hardcode patch names (this is what makes dropping the ADR-004 patch after the Epic 4 spike a zero-edit change for this script) [Source: docs/sprint-change-proposal-2026-07-02.md:286]
  - [ ] Subtask 2.3: Emit one report line per patch (`applied` / `skipped (already applied)` / `FAILED: <patch> → <file(s)>`) plus a run summary

- [ ] Task 3: Skip-if-applied decision logic (AC: 3.5.3.2)
  - [ ] Subtask 3.1: Implement the decision as an importable pure function: (check_ok, reverse_check_ok) → {APPLY, SKIP, CONFLICT}
  - [ ] Subtask 3.2: Wire it: `git apply --check` → apply; else `git apply --reverse --check` → skip; else CONFLICT
  - [ ] Subtask 3.3: Run `git apply` from the submodule root (`cwd=external/pob-engine`, patch path relative), per the ADR-004 convention

- [ ] Task 4: `POB_VERSION.txt` regeneration via the shared 3.5.2 generator (AC: 3.5.3.3)
  - [ ] Subtask 4.1: Import (or fold in and delete the duplicate) the generator authored in Story 3.5.2 — one implementation total; 3.5.2 Task 5 anticipates it living "as the first piece of `scripts/setup_pob.py`"
  - [ ] Subtask 4.2: Confirm output is deterministic for an unchanged gitlink (no timestamps) and carries the 3.5.2 generation marker
  - [ ] Subtask 4.3: Regenerate unconditionally on every run (that is the anti-drift mechanism — not a skip-if-present)

- [ ] Task 5: Failure modes and distinct exit codes (AC: 3.5.3.5)
  - [ ] Subtask 5.1: Map the three failure classes (missing/uninitialized submodule; patch conflict; gitlink mismatch) to distinct nonzero exit codes; success (including all-skipped) = 0
  - [ ] Subtask 5.2: Each failure message states what is wrong AND the remediation command; patch-conflict message names patch + target file(s)
  - [ ] Subtask 5.3: Document the exit-code table in the module docstring / `--help` (consumed by 3.5.4 and future CI)

- [ ] Task 6: Tests (AC: 3.5.3.2)
  - [ ] Subtask 6.1: Unit-test the decision function in `tests/unit/` (pure function or mocked `subprocess` results — fast, no LuaJIT, no real git needed)
  - [ ] Subtask 6.2: Optional integration-style double-run test (real git); if environment-heavy, record an actual double-run transcript in Completion Notes instead (AC-3.5.3.2 allows either)

- [ ] Task 7: README update (AC: 3.5.3.4)
  - [ ] Subtask 7.1: Replace the Setup section's manual steps with: clone → `pip install -r requirements.txt` → `python scripts/setup_pob.py`
  - [ ] Subtask 7.2: Remove the manual `POB_VERSION.txt` hand-edit guidance from the monthly re-validation section (`README.md:113-118`); point PoB-update flows at the script
  - [ ] Subtask 7.3: Sweep README for any remaining contradiction with the single-command flow

## Dev Notes

- Relevant architecture patterns and constraints
  - This story implements plan section 6, Epic 3.5 item 3 verbatim [Source: docs/pebo-master-plan.md:175-176]; it is step 3 of the plan's "immediate next actions" item 3 ("repair the submodule, pin, `setup_pob.py`, conftest guard") [Source: docs/pebo-master-plan.md:331]
  - It replaces the documented drift anti-pattern: manual `git checkout <hash>` + `echo > POB_VERSION.txt` [Source: docs/PRD.md:677-689], the procedure behind the four-way version drift (POB_VERSION v0.12.2 pin / gitlink `4cf3563f6` / 0.15.0 working tree / 0.12.2 baselines) [Source: docs/pebo-master-plan.md:55-59]
  - It also automates ADR-004's manual reapplication instructions (detect-by-grep + manual `git apply` + CI snippet) [Source: docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md:178-232]
  - Keep the patch-application logic a reusable function: this script is the foundation of the standing patch-day workstream's `scripts/update_pob.py` (bump submodule → re-apply patches → regen artifacts → parity), budgeted ~2 days per league patch [Source: docs/pebo-master-plan.md:275-279,318]
  - Non-destructive by design: on gitlink/working-tree mismatch or patch conflict, fail loudly with remediation — never auto-reset the submodule tree (plan risk #2, CRITICAL) [Source: docs/pebo-master-plan.md:313]
  - As of 2026-07-02 `external/patches/` holds the promoted set of three: `0001` Global.lua (v0.15.0-targeted after the same-day jump-fallback; v0.22.0 variant parked under `docs/forensics/proposed-patches/`), `0002` ModStore.lua, `0003` CalcOffence.lua, plus `.gitattributes` (`*.patch -text`); the stale 0.12.2-cut `global-lua-nil-safety.patch` is retired (`stub_functions.lua` was found absent from the tree — not adopted) — the script must handle N patches without modification. NOTE: 3.5.2 executed — the submodule is real, pinned `3e1b71c9`, patches applied; `scripts/generate_pob_version.py` exists and IS the shared generator (import it, don't reimplement)
  - Forward pointer: Story 3.5.4's verification logic is designed to be importable by this script as an optional post-run check (`pob_env.verify()`); leave a seam, do not block on it — 3.5.4 depends on this story, so that wiring lands with 3.5.4 [Source: docs/sprint-change-proposal-2026-07-02.md:354]

- Scope boundaries (respect the v1 NOT-list and the correct-course split)
  - README is updated in THIS story (AC-3.5.3.4). Supersession annotations on `docs/PRD.md:677-689` (proposal edit 7.1-K) and the ADR-004 reapplication-section pointer (proposal edit 7.3-E) belong to the PROPOSED doc-status pass awaiting approval — do not edit those documents here [Source: docs/sprint-change-proposal-2026-07-02.md:265,286]
  - `scripts/update_pob.py` itself (submodule bump + artifact regen) is the standing workstream, NOT this story — this story only keeps the shared logic reusable
  - No CI pipeline scaffolding beyond stable, documented exit codes (CI work is out of Epic 3.5 scope)

- Testing standards summary
  - Unit tests: fast, no LuaJIT dependency, live under `tests/unit/` (plain `pytest tests/unit/`)
  - Any integration-style test that touches real git stays cheap and hermetic where possible; the full integration suite constraint (`pytest -n 1` on Windows per ADR-003/CLAUDE.md) applies only if a test imports the Lua stack — these tests should not
  - Idempotency evidence: automated test preferred; recorded double-run transcript acceptable per AC-3.5.3.2

### Project Structure Notes

- Alignment with unified project structure
  - `scripts/setup_pob.py` — new file in the existing flat `scripts/` directory (precedent: `scripts/run_epic2_validation_isolated.py`, `scripts/generate_baseline_stats.py`)
  - `scripts/` is not a package: keep logic in module-level importable functions with an `if __name__ == "__main__":` guard; the unit test may import via path insertion — no packaging changes
  - Test file: `tests/unit/test_setup_pob.py` (precedent: `tests/unit/test_encode_pob_code.py`)
  - Submodule identity comes from `.gitmodules` (`path = external/pob-engine`, `url = https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2.git`) — do not hardcode a second copy of the URL in the script

- Detected conflicts or variances (with rationale)
  - `external/patches/` contains a `README.md` alongside the patches — glob `*.patch` only, or the apply loop will feed markdown to `git apply`
  - The `POB_VERSION.txt` generator is authored in Story 3.5.2 and may already live inside `scripts/setup_pob.py` as its first piece (3.5.2 Task 5 allows this); if so, this story completes the script around it rather than creating a new file — either way the AC-3.5.3.3 single-implementation rule holds
  - Coordination hazard mirrored from proposal 7.3-E: just as 3.5.4 must not hardcode the nil-safety patch marker, this script must not hardcode patch names — the patch set is data, discovered at runtime [Source: docs/sprint-change-proposal-2026-07-02.md:286]

### References

- [Source: docs/pebo-master-plan.md:175-176] — Epic 3.5 item 3: the story's charter (idempotent setup, `--check --reverse` skip-if-applied, the ONE setup command in README)
- [Source: docs/pebo-master-plan.md:173-174] — Epic 3.5 item 2: `POB_VERSION.txt` generated from the gitlink, never hand-edited (shared 3.5.2 generator)
- [Source: docs/pebo-master-plan.md:275-279] — standing patch-day workstream (`update_pob.py`) that reuses this script's patch logic
- [Source: docs/pebo-master-plan.md:313,318] — risk #2 (never destroy un-dispositioned state) and risk #7 (patch-day churn)
- [Source: docs/pebo-master-plan.md:55-59] — the four-way version drift this command class ends
- [Source: docs/pebo-master-plan.md:331] — section 9 immediate actions, item 3
- [Source: docs/sprint-change-proposal-2026-07-02.md:338-345] — section 8.1 story 3.5.3 definition (goal + 5 ACs)
- [Source: docs/sprint-change-proposal-2026-07-02.md:265] — proposal edit 7.1-K: PRD setup block superseded by this script (doc pass PROPOSED, not this story)
- [Source: docs/sprint-change-proposal-2026-07-02.md:286] — proposal edit 7.3-E: ADR-004 reapplication → `setup_pob.py`; patch handling must be patch-set-driven, nothing hardcoded
- [Source: docs/PRD.md:677-689] — the manual checkout/echo procedure being replaced (the documented drift anti-pattern)
- [Source: docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md:178-232] — manual reapplication + CI-check instructions this script automates
- [Source: README.md:12-23,102-157] — README Setup section and monthly re-validation block touched by AC-3.5.3.4 (manual `POB_VERSION.txt` bump at README.md:113-118)
- [Source: docs/stories/story-3.5.2-submodule-repair-and-pin.md] — upstream dependency: real submodule, ratified patch set, `POB_VERSION.txt` generator (AC3, Task 5)
- [Source: docs/sprint-status.yaml:96] — tracking key `3.5-3-setup-pob-script: drafted`

## Dev Agent Record

### Context Reference

<!-- Populated by dev-story at implementation time -->

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

## Change Log

**2026-07-02** — Story created via correct-course sprint change proposal
- Drafted from `docs/pebo-master-plan.md` section 6 (Epic 3.5 item 3) per `docs/sprint-change-proposal-2026-07-02.md` section 8.1 (pre-approved story drafting)
- Status: drafted; depends on Story 3.5.2; Story 3.5.4 depends on this story

**2026-07-02 (later)** — Patch-set facts refreshed after promotion + v0.22.0 pin decision
- external/patches/ now holds promoted 0001..0003 (+.gitattributes); stale 0.12.2 patch retired; ADR-004 addendum landed (its README/ADR citations herein describe the pre-promotion state where marked)
