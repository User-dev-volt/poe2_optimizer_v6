# Story 3.5.1: Submodule Forensics and Local-Edit Inventory

Status: done

## Story

As a **developer**,
I want **a complete, dispositioned inventory of every local edit in the untracked `external/pob-engine` working tree, produced by diffing it against a clean upstream 0.15.0 checkout**,
so that **the submodule repair in story 3.5.2 cannot clobber unknown hand-edits — closing master-plan risk #2 (CRITICAL) before anything destructive touches that tree**.

## Context

- **Epic:** 3.5 — Substrate & Trust (lite) → v0.9 (internal). **Tracking key:** `3.5-1-pob-engine-forensics`. **Effort:** 4–6h. **Dependencies:** none — first story of the epic; story 3.5.2 (submodule repair and pin) depends on this inventory and MUST NOT start without it.
- `external/pob-engine` has no `.git` file and no `.git/modules` entry — it is an unverifiable vendored blob, invisible to `git status` [Source: docs/pebo-master-plan.md section 2 item 4, lines 55-59].
- Version drift is four-way: `POB_VERSION.txt` pins `69b825bda`/v0.12.2, the parent gitlink records `4cf3563f6`, the working tree is 0.15.0 (`manifest.xml`), and parity baselines were captured from GUI 0.12.2 [Source: docs/pebo-master-plan.md Appendix A, lines 355-356].
- Documented-but-unpatched edits exist: `docs/architecture/pob-engine-dependencies.md` records `ModStore.lua:444/464` nil guards (lines 509-513, 766-769) and a project-authored `src/Export/stub_functions.lua` (line 734), yet `external/patches/` holds ONLY `global-lua-nil-safety.patch` [Source: docs/sprint-change-proposal-2026-07-02.md section 4.3.3].
- **A kick-off run of the diff half executed in parallel with the 2026-07-02 sprint change proposal; its report has landed at `docs/forensics/pob-engine-forensics-2026-07-02.md`. This story completes and ratifies that report against the acceptance criteria below — it does not start from zero, and it does not rubber-stamp either** (at least one AC element is known to be missing from the landed report; see Dev Notes).

## Acceptance Criteria

1. **AC-3.5.1.1:** Clean upstream PoB2 checkout at the 0.15.0 release commit obtained
   - Upstream is the PoE2 fork remote recorded in `.gitmodules` (PathOfBuildingCommunity/PathOfBuilding-PoE2)
   - Checkout lands in a scratch location OUTSIDE this repo (never under `external/`)
   - The exact upstream commit hash AND the `manifest.xml` version string are recorded in the report's evidence header, with the clone command for reproducibility

2. **AC-3.5.1.2:** Full recursive diff vs `external/pob-engine` captured
   - `--stat` surface bounded first, then full hunks
   - Runtime/generated artifacts (e.g. `ModCache`) classified separately from source edits
   - File census covers added/deleted/extra files, not only modified ones
   - Windows EOL noise is controlled (EOL-only churn must not drown or masquerade as real edits)

3. **AC-3.5.1.3:** Every differing source hunk dispositioned in `docs/forensics/pob-engine-forensics-2026-07-02.md`
   - Exactly one disposition per hunk: **adopt-as-patch** (becomes `external/patches/*.patch` in 3.5.2), **reject** (restore upstream in 3.5.2), or **generated-artifact** (ignore)
   - Unknown-origin hunks default to reject-with-note — a conscious rejection, per plan risk #2's "every hunk becomes a patch file or a conscious rejection"
   - Zero un-dispositioned hunks remain

4. **AC-3.5.1.4:** The three documented-but-unpatched edits explicitly dispositioned by name
   - `Global.lua` nil-safety — existing patch `external/patches/global-lua-nil-safety.patch`: verify the working tree matches the patch
   - `ModStore.lua:444/464` nil guards (docs/architecture/pob-engine-dependencies.md:509-513, 766-769)
   - `src/Export/stub_functions.lua` (docs/architecture/pob-engine-dependencies.md:734) — dispositioned by name even if the verdict is "absent from current tree"

5. **AC-3.5.1.5:** `external/pob-engine` NOT modified by this story
   - Read-only forensics; destructive repair happens only in 3.5.2 with this inventory in hand
   - Any draft patch files are staged outside `external/patches/` (promotion into `external/patches/` is a 3.5.2 decision)
   - The report states the read-only guarantee explicitly

## Tasks / Subtasks

- [x] Task 1: Confirm upstream remote and the 0.15.0 release commit (AC: 3.5.1.1)
  - [x] Subtask 1.1: Read the working tree's `external/pob-engine/manifest.xml` version string; confirm the upstream remote from `.gitmodules`
  - [x] Subtask 1.2: Resolve the release tag/commit matching that manifest version; record the full SHA
  - [x] Subtask 1.3: Clone upstream at that commit to a scratch directory outside the repo; record the exact clone command + commit in the report

- [x] Task 2: Capture the full recursive diff (AC: 3.5.1.2)
  - [x] Subtask 2.1: `git diff --no-index --stat` (or equivalent) first to bound the surface, then full hunks
  - [x] Subtask 2.2: Run EOL-controlled (`git -c core.autocrlf=false ... --ignore-cr-at-eol`) so CRLF phantoms are separated from content changes
  - [x] Subtask 2.3: Bucket results: source edits vs runtime/generated artifacts (ModCache etc.) vs EOL-noise; census added/deleted/ignored-extra files against the upstream tracked set

- [x] Task 3: Disposition every source hunk (AC: 3.5.1.3)
  - [x] Subtask 3.1: Cross-check every hunk against `docs/architecture/pob-engine-dependencies.md` documented edits and `external/patches/README.md`
  - [x] Subtask 3.2: Assign exactly one disposition per hunk (adopt-as-patch / reject / generated-artifact) with a one-line justification each
  - [x] Subtask 3.3: Flag any hunk whose purpose is unknown for explicit decision — default reject-with-note (conscious rejection per plan)

- [x] Task 4: Explicitly disposition the three documented edits by name (AC: 3.5.1.4)
  - [x] Subtask 4.1: `Global.lua` nil-safety — verify tree matches the existing patch: grep sentinel `or 0  -- Handle nil arguments` (grep by content, not line number — README's cited lines 117/146/175 have drifted in the 0.15.0 tree) plus an EOL-safe reverse-apply check
  - [x] Subtask 4.2: `ModStore.lua` nil guards — locate the documented 444/464 edits in the current tree (line numbers may have drifted since the doc), confirm content, disposition
  - [x] Subtask 4.3: `src/Export/stub_functions.lua` — verify existence and disposition by name (verified ABSENT from the tree on 2026-07-02; see Dev Notes — the report must still record this verdict explicitly)

- [x] Task 5: Write/complete the forensics report (AC: 3.5.1.1, 3.5.1.2, 3.5.1.3, 3.5.1.4)
  - [x] Subtask 5.1: Ratify/complete the landed kick-off report at `docs/forensics/pob-engine-forensics-2026-07-02.md` — verify each AC-required element is present and correct rather than re-running blindly; re-run only what fails verification
  - [x] Subtask 5.2: Evidence header complete: upstream commit hash, `manifest.xml` version string, superproject HEAD, date, method (per AC-3.5.1.1)
  - [x] Subtask 5.3: Per-file disposition table with justifications; any adopt-as-patch draft files staged under `docs/forensics/proposed-patches/` (NOT `external/patches/`)

- [x] Task 6: Verify the read-only guarantee (AC: 3.5.1.5)
  - [x] Subtask 6.1: Confirm no writes occurred under `external/pob-engine/` during this story (superproject `git status`, spot mtime checks) and state the guarantee in the report

## Dev Notes

- Relevant architecture patterns and constraints
  - **Diff-before-destroy is the mitigation for master-plan risk #2 (CRITICAL):** "Submodule repair clobbers unknown local edits (tree is git-untracked)" → "Diff-before-destroy vs clean upstream 0.15.0; every hunk becomes a patch file or a conscious rejection" [Source: docs/pebo-master-plan.md section 8, line 313]
  - This story is plan section 6, Epic 3.5 item 1 verbatim: "Submodule forensics before anything else … *(Critical: today there is no record of what was hand-edited in that tree.)*" [Source: docs/pebo-master-plan.md lines 169-172] and plan section 9 immediate action 2 [lines 329-330]
  - `external/pob-engine` is a plain directory, not a git repo — use `git diff --no-index`; `git status` cannot see inside it
  - **Strictly read-only.** The story boundary is: 3.5.1 inventories and dispositions; 3.5.2 repairs/pins and promotes patches; 3.5.3 automates setup; 3.5.4 enforces via conftest; 3.5.5 harvests baselines [Source: docs/sprint-change-proposal-2026-07-02.md section 8.1 story table]
  - **Kick-off report has landed** (`docs/forensics/pob-engine-forensics-2026-07-02.md`): it resolves upstream to tag v0.15.0 = `3e1b71c92dc5f7c295031700746a418558117b06`, finds the tree = clean v0.15.0 + exactly 3 hand-patched Lua files (`Global.lua`, `ModStore.lua`, `CalcOffence.lua`; classification 3 KEEP-AS-PATCH / 0 REJECT / 0 GENERATED / 1,067 EOL-NOISE), and stages byte-identical-verified draft patches under `docs/forensics/proposed-patches/`. **Ratify these findings, do not assume them.**
  - **Known gap in the landed report (why this story exists beyond the kick-off):** it does not disposition `src/Export/stub_functions.lua` by name, which AC-3.5.1.4 requires. Verified 2026-07-02: the file is ABSENT from `external/pob-engine/src/Export/` (the directory exists with upstream content only) — consistent with the report's file census (0 added files vs v0.15.0). Likely lost in the 2026-01-30 re-vendor; the report must record the verdict explicitly (e.g. "absent from current tree — historical doc reference, no hunk to adopt; MinimalCalc no longer depends on it, or the dependency is itself stale") so the by-name checklist is complete.
  - **Windows/EOL hazard:** upstream `.gitattributes` is `* text=auto`, so naive diffs report ~1,067 CRLF-phantom modifications and the existing patch file itself false-negatives a naive `git apply --check`. Always run diffs and apply-checks EOL-controlled; prefer `--stat` first to bound the surface.

- Source tree components to touch
  - READ ONLY: `external/pob-engine/**` (never write), `external/patches/README.md` + `global-lua-nil-safety.patch`, `docs/architecture/pob-engine-dependencies.md`, `POB_VERSION.txt`, `.gitmodules`
  - WRITE: `docs/forensics/pob-engine-forensics-2026-07-02.md` (complete/ratify), `docs/forensics/proposed-patches/*` (draft patches + `.gitattributes` `*.patch -text`)
  - SCRATCH (outside repo): clean upstream clone at the pinned commit

- Testing standards summary
  - No product code changes; the deliverable is evidence. Verification bar: every disposition claim carries a reproducible command + hash; every adopt-as-patch draft forward-applies cleanly to clean 0.15.0 blobs AND reconstructs the live vendored file byte-identically (`cmp`); reverse-apply `--check` passes against the live tree
  - No pytest suites are added or modified in this story; environment enforcement (autouse conftest guard) is story 3.5.4

### Project Structure Notes

- Report path is fixed by the proposal: `docs/forensics/pob-engine-forensics-2026-07-02.md` [Source: docs/sprint-change-proposal-2026-07-02.md Executive Summary + section 9 handoff]
- Tracking key `3.5-1-pob-engine-forensics` under `epic-3.5` in `docs/sprint-status.yaml`; the `3.5-N-slug` convention deliberately avoids collision with epic-3 keys (`3-5-optimization-progress-display-real-time` exists) [Source: docs/sprint-change-proposal-2026-07-02.md section 3.2]
- Draft patches stay under `docs/forensics/proposed-patches/` as the immutable forensic record (v0.15.0-targeted). **Update 2026-07-02: promotion happened** — Alec approved and `external/patches/` now holds `0001..0003` (stale 0.12.2 patch retired). After the same-day v0.22.0 jump-and-fallback, 0001 is the v0.15.0-targeted patch; the v0.22.0 variant is parked in this directory as `0001-global-lua-nil-safety-v0220.patch`. This story's remaining job is ratification of the inventory, not promotion.
- Out of scope — do not creep: re-vendor/pin (3.5.2 — now targeting v0.22.0 per the 2026-07-02 decision), `scripts/setup_pob.py` (3.5.3), conftest guard (3.5.4), baseline harvest/re-capture (3.5.5), further upstream bumps beyond the decided pin (patch-day survival workstream, plan section 6), known-gaps ratchet + trust-tier generator (deferred to Epic 4 per plan Epic 3.5 item 6). Nothing here touches the v1 NOT-list surface (plan section 5) — this is substrate work only. The 0.15.0 diff base remains this story's forensic reference point even though the repair pin moved to v0.22.0.

### References

- [Source: docs/pebo-master-plan.md#6 Roadmap — Epic 3.5 item 1, lines 169-172] — forensics mandate: diff untracked tree vs clean upstream 0.15.0; every local edit becomes a patch or a conscious rejection
- [Source: docs/pebo-master-plan.md#8 Top risks — risk #2, line 313] — CRITICAL severity; diff-before-destroy mitigation this story implements
- [Source: docs/pebo-master-plan.md#9 Immediate next actions — item 2, lines 329-330] — "clone upstream 0.15.0 to scratch; diff against external/pob-engine; inventory local edits"
- [Source: docs/pebo-master-plan.md#2 Where we actually are — item 4, lines 55-59; Appendix A lines 355-356] — no `.git` in external/pob-engine; four-way version drift evidence
- [Source: docs/sprint-change-proposal-2026-07-02.md#8.1] — Epic 3.5 story breakdown, this story's spec, key/effort/dependency table
- [Source: docs/sprint-change-proposal-2026-07-02.md#4.3.3] — documented hand-edits have no corresponding patch files; "the concrete form of plan risk #2 … a direct input to story 3.5.1"
- [Source: docs/architecture/pob-engine-dependencies.md:509-513, 766-769] — `ModStore.lua:444/464` nil-guard pattern (`value = (value or 0) * mult + (tag.base or 0)`)
- [Source: docs/architecture/pob-engine-dependencies.md:734] — `src/Export/stub_functions.lua` reference (verified absent from tree 2026-07-02)
- [Source: external/patches/README.md] — patch inventory (rewritten 2026-07-02: promoted set `0001..0003`; grep sentinels per patch)
- [Source: docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md] — provenance of the Global.lua nil-safety patch
- [Source: docs/forensics/pob-engine-forensics-2026-07-02.md] — landed kick-off report this story completes/ratifies

## Dev Agent Record

### Context Reference

- Ratification input: story ACs vs the landed kick-off report `docs/forensics/pob-engine-forensics-2026-07-02.md`; fresh read-only evidence gathered 2026-07-02 (Test-Path / directory listings only).

### Agent Model Used

claude-fable-5

### Debug Log References

- None — no code executed beyond read-only filesystem checks (`Test-Path`, `Get-ChildItem`, grep over docs).

### Completion Notes List

- **Ratification, not a re-run.** The landed kick-off report already satisfied AC-3.5.1.2, AC-3.5.1.3, and AC-3.5.1.5 in full (EOL-controlled `--stat`-first diff, complete census 0 added/0 deleted/0 extras, exactly one disposition per hunk with byte-identical reconstruction proof, explicit read-only guarantee). Only what failed verification was completed, per Subtask 5.1 — via a dated ratification addendum (report section 8), no forensics re-run needed.
- **AC-3.5.1.4 gap closed (the story's known gap):** `src/Export/stub_functions.lua` was never dispositioned by name in the landed report (grep for "stub" = 0 hits). Addendum 8.1 records the verdict: ABSENT FROM CURRENT TREE — historical doc reference only (pob-engine-dependencies.md:734, loader call at :342), no hunk to adopt/reject, likely lost in the 2026-01-30 re-vendor; fresh evidence (Test-Path False; Export/ holds upstream v0.15.0 content only) plus the report's own 0-added-files census corroborate. Classification totals unchanged (3 KEEP-AS-PATCH / 0 REJECT / 0 GENERATED / 1,067 EOL-NOISE).
- **AC-3.5.1.1 minor gap closed:** the exact scratch clone command was absent from the evidence header (an equivalent appeared only as S6 remediation guidance); addendum 8.2 restates it explicitly for reproducibility.
- **Fresh cross-check (addendum 8.3):** `docs/forensics/proposed-patches/` contents (0001, parked 0001-v0220, 0002, 0003, `.gitattributes`) match report S5 + S7-answer-3 claims exactly; no unexplained files.
- Report terminology KEEP-AS-PATCH treated as equivalent to the AC's adopt-as-patch. Nothing under `external/` was read-modified or written during ratification; per-AC verdicts in addendum 8.4 — all five ACs PASS.

### File List

- `docs/forensics/pob-engine-forensics-2026-07-02.md` (modified — section 8 ratification addendum appended before the Appendix)
- `docs/stories/story-3.5.1-pob-engine-forensics.md` (modified — status, task checkboxes, Dev Agent Record, Change Log)

## Change Log

**2026-07-02** - Story created via correct-course sprint change proposal
- Derived 1:1 from `docs/pebo-master-plan.md` section 6, Epic 3.5 item 1, per `docs/sprint-change-proposal-2026-07-02.md` section 8.1 (Epic 3.5 insertion, pre-approved)
- Supersedes the lightweight draft written alongside the proposal; kick-off diff report noted as landed
- Status: drafted

**2026-07-02 (later)** — Decisions recorded: patches promoted (0001 regenerated for v0.22.0), pin retargeted to v0.22.0
- Promotion executed same-day (was 3.5.2 scope); this story's remaining scope = ratify the inventory + close the stub_functions.lua disposition gap (AC-3.5.1.4)

**2026-07-02** — Story closed: ratified the landed kick-off report against AC-3.5.1.1..5
- Ratification addendum (report section 8) appended: closed the AC-3.5.1.4 gap with the by-name `src/Export/stub_functions.lua` disposition (ABSENT FROM CURRENT TREE, fresh read-only evidence); restated the scratch clone command for AC-3.5.1.1 reproducibility; cross-checked `docs/forensics/proposed-patches/` contents against report claims
- All five ACs PASS (addendum 8.4); ratification pass was read-only w.r.t. `external/`
- Status: done
