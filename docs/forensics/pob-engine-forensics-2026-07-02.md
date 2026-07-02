# pob-engine Forensics Report — diff-before-destroy

- **Date:** 2026-07-02
- **Scope:** `external/pob-engine` (vendored Path of Building PoE2 engine), read-only forensics. Nothing under `external/` was modified.
- **Executes:** Epic 3.5 item 1 / story 3.5.1 ("Submodule forensics before anything else", `docs/pebo-master-plan.md:169-172`) — the first half of plan Risk #2's mitigation ("Diff-before-destroy vs clean upstream 0.15.0; every hunk becomes a patch file or a conscious rejection", `docs/pebo-master-plan.md:313`).
- **Evidence captured at:** superproject HEAD `0b8ca40bbd8357393ed58a4a6faf3189aa54805b`, branch `feat/epic3-ui`.
- **Method:** four read-only probes (A: local state; B: patch audit; C: upstream clone + EOL-controlled diff; D: provenance timeline), synthesized here. All diffs run with `git -c core.autocrlf=false` and `--ignore-cr-at-eol` per the plan's Windows CRLF guidance.

---

## 1. Executive summary

- **The vendored tree actually IS upstream release v0.15.0** (tag commit `3e1b71c92dc5f7c295031700746a418558117b06`, "Release 0.15.0", 2026-01-13T13:25:31Z) **plus exactly 3 hand-patched Lua files** — total delta 3 files / +41 / −29 lines; the file set matches v0.15.0's tracked set exactly (0 added, 0 deleted, 0 generated extras). `manifest.xml:3` (`<Version number="0.15.0" />`) tells the truth.
- **The "four-way version drift" collapses to stale metadata:** the gitlink `4cf3563f62...` is a **phantom** (absent locally *and* upstream — GitHub API HTTP 422; `git fetch` "not our ref"), `POB_VERSION.txt` is 754 files / +266,986 / −72,798 away from reality, and the GUI-0.12.2 parity baselines are now the *stale* side of the drift, not the tree.
- **All 3 local edits are deliberate nil-safety fixes** (ADR-004 + Story 2.9.2 spell-build crashes). Only `Global.lua` had a patch file; the `ModStore.lua` and `CalcOffence.lua` edits existed **only as live edits in an untracked tree** — one re-vendor away from silently regressing spell builds.
- **Diff-before-destroy is COMPLETE and closed:** every hunk is now a draft patch under `docs/forensics/proposed-patches/`, and the three patches were verified to rebuild the live vendored files **byte-for-byte** from clean v0.15.0 blobs. Zero unexplained edits remain. Classification: 3 KEEP-AS-PATCH, 0 REJECT, 0 GENERATED, 1,067 EOL-NOISE.
- **Verdict: REPAIRABLE, low risk.** Safe repair = pin submodule/vendor to `3e1b71c9` (v0.15.0), apply the 3 patches, regenerate `POB_VERSION.txt` from the pin. No content is lost; behavior is provably unchanged (byte-identical reconstruction).

---

## 2. The four versions, reconciled

### 2.1 Version table (full SHAs)

| # | Source of claim | Full SHA | Date | What it actually represents |
|---|---|---|---|---|
| 1 | `POB_VERSION.txt` (repo root, lines 4-7) | `69b825bda1733288a3ea3b1018a1c328900a4924` | upstream commit 2025-10-10 ("Weekly beta release"); "Date Pinned: 2025-10-12" | v0.12.2-61-g69b825bda. **Stale metadata** — matches only the original 2025-10-10 gitlink; never updated across two later pin changes. Exists upstream (GitHub API HTTP 200). |
| 2 | Parent gitlink (`git ls-files -s external/pob-engine` → `160000 4cf3563f... 0`) | `4cf3563f621163cda591d9e903576dc1f0a0ae6b` | recorded 2026-01-14 (superproject commit `69a63cdb8a...` "Last changes") | **PHANTOM.** Absent from the local object store (`git cat-file -t` → fatal) and from upstream (GitHub API HTTP 422 for short and full SHA; `git fetch origin <sha>` → "not our ref"). Almost certainly a local commit inside a submodule `.git` destroyed by the 2026-01-26 re-clone. |
| 3 | Working tree `external/pob-engine/` (`manifest.xml:3`, `changelog.txt:1`, EOL-controlled diff) | `3e1b71c92dc5f7c295031700746a418558117b06` (tag `v0.15.0`) | tag commit 2026-01-13T13:25:31Z ("Release 0.15.0"; changelog dated 2026/01/14); materialized on disk 2026-01-30 (file mtimes) | **The real engine:** release v0.15.0 content + exactly 3 hand-patched Lua files. Not a git repo (no `.git`; 1,615 files, ~326 MB, invisible to `git status`). |
| 4 | Parity baselines (`tests/fixtures/parity_builds/gui_baseline_stats.json` `_metadata`: `pob_version: "0.12.2"`, `date_recorded: "2025-10-21"`) | tag `v0.12.2` = `e73e9976b35262fe41473a653e6d3498ac09b276` | released 2025-09-16 | GUI 0.12.2 stats captured 2025-10-21. **Now the stale side:** the engine on disk is 0.15.0, so baselines lag the tree, not vice versa. |

Bonus (closes a probe-A/D open question): the **intermediate** gitlink `153245c53b0a36da593398de65c6c4a76529c10b` (recorded 2025-10-31 in `220718fc0a...` "Big Commit"; verified via `git rev-parse 220718f:external/pob-engine`) is **also a phantom** — GitHub API HTTP 422 (control: `69b825bda...` returns 200). Both post-original pins are unreproducible; the gitlink history carries no usable version information beyond the first pin.

### 2.2 Distance table (vendored working tree vs ref; EOL-controlled)

| Compared against | files changed | insertions | deletions | Verdict |
|---|---|---|---|---|
| `v0.15.0` tag `3e1b71c92dc5f7c295031700746a418558117b06` | **3** | **41** | **29** | **MATCH** — tree = v0.15.0 + 3 patched files (scratch `diff-stat.txt`) |
| gitlink `4cf3563f621163cda591d9e903576dc1f0a0ae6b` | n/a | n/a | n/a | Unfetchable phantom — cannot diff |
| `POB_VERSION.txt` pin `69b825bda1733288a3ea3b1018a1c328900a4924` | 754 | 266,986 | 72,798 | Nowhere close (scratch `diff-stat-vs-69b825bda.txt`) |

File-set census vs v0.15.0 (`git status --porcelain -uall`, also with `--ignored=matching`): **1,070 ' M' entries, 0 deleted, 0 untracked, 0 ignored extras** — of which 1,067 are pure EOL phantoms (see section 4) and 3 are the real edits.

---

## 3. Provenance timeline

All superproject SHAs verified locally; gitlink values via `git rev-parse <commit>:external/pob-engine`.

| When | Event | Evidence |
|---|---|---|
| 2025-10-10 | `89cd518768b6fd566db38b9fb7faf6b4529264e0` "Beginning": `.gitmodules` created (url = PathOfBuildingCommunity/PathOfBuilding-PoE2), gitlink added at `69b825bda1733288a3ea3b1018a1c328900a4924` | `git log -- external/pob-engine`; `git rev-parse 89cd518:external/pob-engine` |
| 2025-10-12 | `POB_VERSION.txt` authored pinning 69b825bda / v0.12.2-61 | `POB_VERSION.txt:4-7`; `docs/stories/story-1.4.md:906-907` |
| 2025-10-17 | MinimalCalc pivot: HeadlessWrapper abandoned (GUI-bound, 0xe24c4a02); vendored tree consumed file-by-file thereafter | `docs/stories/story-1.4.md` (~884-1018) |
| 2025-10-21 | GUI 0.12.2 parity baselines captured | `tests/fixtures/parity_builds/gui_baseline_stats.json` `_metadata`; `tests/integration/parity_analysis.md` |
| 2025-10-31 | `220718fc0adf531718aa476831ab1a4c9f8132d2` "Big Commit": gitlink bumped to `153245c53b0a36da593398de65c6c4a76529c10b` (now-phantom); `POB_VERSION.txt` committed in the same commit still pinning 69b825bda — stale from birth. No doc mentions 153245c anywhere | `git rev-parse 220718f:external/pob-engine`; GitHub API 422 |
| 2025-12-01..04 | Story 2.9.2 (spell/DOT): `Global.lua` hand-patched inside the then-real submodule; ADR-004 authored; `external/patches/` mechanism created | `docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md`; `docs/stories/2-9-2-spell-dot-minimalcalc-enhancement.md:346,545` |
| 2026-01-14 | `69a63cdb8a3898b77938cfa1190c23a91892ed98` "Last changes": gitlink bumped to `4cf3563f621163cda591d9e903576dc1f0a0ae6b` (phantom); ADR-004 + `external/patches/{README.md,global-lua-nil-safety.patch}` finally committed. Same day upstream released v0.15.0 (`changelog.txt:1` = `VERSION[0.15.0][2026/01/14]`; tag commit 2026-01-13T13:25:31Z) | `git rev-parse 69a63cd:external/pob-engine`; GitHub API |
| 2026-01-26 11:10 −0500 | **Repo re-cloned non-recursively** from `https://github.com/User-dev-volt/poe2_optimizer_v6.git` (reflog: `clone: from ...`); the submodule's `.git` / `.git/modules` — including both phantom commits — destroyed; gitlink left uninitialized (`git submodule status` → leading `-`) | reflog @ `cbb76bc`; `external/patches/*` mtimes = 2026-01-26 11:10 |
| 2026-01-30 00:26 | A v0.15.0 source tree manually dropped into `external/pob-engine` (no git metadata → unverifiable vendored blob) | file mtimes cluster 00:26-00:34; `manifest.xml:3` |
| 2026-01-30 00:37 | `src/Data/Global.lua` re-patched per ADR-004 | mtime; sentinel `or 0  -- Handle nil arguments` at `Global.lua:119,148,177` |
| 2026-01-30 09:27-09:28 | `src/Classes/ModStore.lua` and `src/Modules/CalcOffence.lua` hand-edited (Story 2.9.2 guards) — **never captured as patch files until this report** | mtimes; self-labeled comments `ModStore.lua:458`, `CalcOffence.lua:5007` |
| 2026-06-29 | Work resumes after 5-month gap; handoff warns the ADR-004 patch is fragile ("`git submodule update` silently reverts it") | `docs/HANDOFF-2026-06-29-OPTIMIZER-NOOP-FIXED.md:84-86` |
| 2026-07-01 | Master plan adopted; Risk #2 (CRITICAL) mandates diff-before-destroy | `docs/pebo-master-plan.md:169-172,313`; commit `0b8ca40` |
| 2026-07-02 | This forensics run: upstream v0.15.0 cloned to scratch, EOL-controlled diff, patch drafts + this report | probes A-D; `docs/forensics/proposed-patches/` |

---

## 4. Complete local-edit inventory vs clean v0.15.0

Diff basis: vendored working tree vs clean clone of tag `v0.15.0` (`3e1b71c9...`), `git -c core.autocrlf=false diff --ignore-cr-at-eol`. Totals: **3 files / +41 / −29** — nothing else differs in content.

| # | Path (submodule-relative) | Delta | Class | Justification |
|---|---|---|---|---|
| 1 | `src/Data/Global.lua` | +32/−27, 3 hunks (`OR64`/`AND64`/`XOR64` + `NOT64` head) | **KEEP-AS-PATCH** | ADR-004 nil-safety; spell builds crash without it ("arithmetic on a nil value", Global.lua:118). Clean v0.15.0 verifiably still lacks the guards (forward-apply succeeds on clean blobs), so the patch is NOT obsolete at 0.15.0. |
| 2 | `src/Classes/ModStore.lua` | +2/−1 in `EvalMod` (`value = (value or 0) * mult + (tag.base or 0)`) | **KEEP-AS-PATCH** | Story 2.9.2 nil-guard, self-labeled comment at line 458; existed ONLY as a live edit (repo-wide `**/*.patch` glob finds no patch for it) — capture or lose. |
| 3 | `src/Modules/CalcOffence.lua` | +7/−1 in ailment-buildup loop (`data.buildupTypes` guard + `::continue_ailment::` goto) | **KEEP-AS-PATCH** | Story 2.9.2 crash guard, self-labeled comment at line 5007; likewise never captured as a patch file. (Its other fix-comments at lines 2424/4157 are upstream 0.15.0 content — they do not appear in the diff.) |
| 4 | 1,067 other files reported ` M` by git-status-vs-clone | EOL only | **EOL-NOISE** | Empty diffs under `--ignore-cr-at-eol`; upstream `.gitattributes:4` is `* text=auto`, so a Windows/autocrlf checkout renders CRLF while the vendored tree is LF-normalized. Sampled files diff empty even without ignore flags (scratch `status-vs-0.15.0.txt`, `diff-stat.err` = 165 KB of pure CRLF warnings). |
| — | REJECT class | — | **0 entries** | No accidental or superseded edits found anywhere in the tree. |
| — | GENERATED class | — | **0 entries** | File census exactly matches v0.15.0's tracked set: 0 added, 0 deleted, 0 ignored extras — no regenerated ModCache variants, no `*.zst` leftovers, no build artifacts. |

**Resolved anomaly — `src/Data/ModCache.lua` (probe A):** the working-tree file (content sha1 `97b9aa5d17...`) mismatches `manifest.xml:194`'s sha1 (`c753f138e6...`) but is **byte-identical to the v0.15.0 git blob modulo CRLF** — re-verified today: `git diff --no-index --ignore-cr-at-eol` vs the clone copy is EMPTY; the clone checkout is CRLF, the vendored file LF. `manifest.xml` sha1s describe the PoB updater's CRLF release rendering, not LF git blobs. **Not a local edit** — subsumed under EOL-NOISE.

**Cross-reference `external/patches/global-lua-nil-safety.patch`:** it IS represented in the delta — its content is exactly inventory entry #1 (reverse-check with `--ignore-whitespace` exits 0 against the live file), and it IS currently applied (sentinels at `Global.lua:119/148/177`). But it is stale in two ways: (a) cut against 0.12.2 — hunk headers `@@ -108/-136/-164` (patch lines 5/42/79) vs 0.15.0's actual `@@ -110/-138/-166` (+2-line upstream drift above `OR64`, confirmed as upstream — the regenerated 0.15.0 diff contains no other change there); (b) the patch file itself is CRLF in the working tree (index LF), so naive `git apply --check` gives a **false negative** on this checkout without `--ignore-whitespace`. Superseded by draft `0001` below. The README's grep sentinel remains the reliable applied-check.

---

## 5. Draft patches (KEEP-AS-PATCH deliverables)

Written under `docs/forensics/proposed-patches/` — **`external/patches/` was NOT touched**; promotion is Alec's call per the plan ("convert every local edit into `external/patches/*.patch` or consciously reject it", `docs/pebo-master-plan.md:170-171`).

| File | Covers | Origin |
|---|---|---|
| `docs/forensics/proposed-patches/0001-global-lua-nil-safety.patch` | `src/Data/Global.lua` (+32/−27) | ADR-004 / Story 2.9.2, regenerated against v0.15.0 (supersedes the stale 0.12.2 patch) |
| `docs/forensics/proposed-patches/0002-modstore-evalmod-nil-safety.patch` | `src/Classes/ModStore.lua` (+2/−1) | Story 2.9.2 — first-ever capture |
| `docs/forensics/proposed-patches/0003-calcoffence-ailment-buildup-nil-safety.patch` | `src/Modules/CalcOffence.lua` (+7/−1) | Story 2.9.2 — first-ever capture |
| `docs/forensics/proposed-patches/.gitattributes` | `*.patch -text` | Prevents the CRLF churn that broke naive apply-checks on the existing patch file |

Properties and verification (all runs 2026-07-02):

- Paths are repo-root-relative (`a/external/pob-engine/src/...`), LF line endings; hunk bodies are byte-exact copies of the EOL-controlled diff (headers rewritten only), preserving trailing-whitespace context.
- **Forward `git apply -p3 --check` against clean v0.15.0 LF blobs** (extracted by SHA from the tag: `7e8a1781f1...`, `6470f1b219...`, `eeab607887...`): PASS x3.
- **Real apply, then `cmp` vs the live vendored files: BYTE-IDENTICAL x3.** Clean v0.15.0 + these 3 patches reconstructs today's tree exactly — this simultaneously proves the inventory above is complete for content changes.
- **Reverse `git -c core.autocrlf=false apply --reverse --check` from repo root against the live tree: PASS x3** (and forward check from repo root fails with "patch does not apply", i.e., already applied — expected).
- Invocations: from repo root on the current/plain dir: `git -c core.autocrlf=false apply <patch>`; from inside a future real submodule checkout: `git -C external/pob-engine apply -p3 <patch>`.

---

## 6. Recommended remediation sequence (feeds story 3.5.2 = plan E3.5 items 2-4)

> **2026-07-02 update (same day, post-decisions):** steps 1–2 are DONE — this report is being committed together with the executed promotion (`external/patches/0001..0003` + README + ADR-004 addendum). The pin decision came back **v0.22.0, not v0.15.0** (see §7 answers): step 4's checkout SHA becomes `860f4268...`, step 8's "bit-identical numbers" expectation no longer holds (engine version jump — see story 3.5.2 AC5's triage rule), and step 10's v0.22.0 evaluation was pulled forward and completed (upstream still lacks all three nil fixes; 0001 regenerated for v0.22.0, 0002/0003 apply clean there).

1. **Commit this report + the 3 draft patches** (they are the only durable record of the two never-captured edits; until committed, one aggressive clean wipes the evidence).
2. **Alec decision gate:** approve promoting the 3 drafts into `external/patches/` (retiring the stale 0.12.2 `global-lua-nil-safety.patch`), update `external/patches/README.md` + an ADR-004 addendum to cover all three files, and carry the `*.patch -text` gitattribute. **Do not start any re-vendor before this lands.**
3. **Back up the live tree:** move/copy `external/pob-engine` to `external/pob-engine.pre-repair-2026-07-02` (326 MB) and keep it until step 8 passes.
4. **Re-establish the engine at the exact pin `3e1b71c92dc5f7c295031700746a418558117b06` (tag v0.15.0):** clone with `git -c core.autocrlf=false -c core.eol=lf clone https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2.git external/pob-engine && git -C external/pob-engine checkout --detach 3e1b71c9...` (LF working tree = today's runtime-tested state; upstream `.gitattributes` is `* text=auto`, so autocrlf must stay off). If keeping submodule-ism: `git submodule absorbgitdirs external/pob-engine`, then `git add external/pob-engine` to replace the phantom gitlink `4cf3563f6...` with the real `3e1b71c9...`. (A plain `git submodule update --init` CANNOT work — it would try to check out the phantom.)
5. **Apply the 3 promoted patches** (order 0001→0003; independent, numbered for determinism) and verify via the grep sentinels (`Global.lua` x3, `ModStore.lua` comment, `continue_ailment` x2).
6. **Regenerate `POB_VERSION.txt` from the pin** (plan E3.5 item 2: generated, never hand-edited): v0.15.0 / `3e1b71c9...` / date / applied-patch list. Today's file (69b825bda, "git submodule update --remote" advice) is factually wrong and its advice is exactly the reversion hazard HANDOFF-2026-06-29 warns about.
7. **`scripts/setup_pob.py` (plan E3.5 item 3):** idempotent init/pin/patch — use `git apply --reverse --check` (with LF enforcement) as skip-if-applied; this run demonstrated naive checks false-negative under CRLF.
8. **Test gate before deleting the backup:** `pytest -n 1 tests/integration/` (esp. `test_story_2_9_2_spell_builds.py`) + `pytest -m parity`; numbers should be bit-identical to pre-repair since the tree content is byte-identical by construction.
9. **conftest guard (plan E3.5 item 4):** autouse fixture asserting engine-is-real-repo, HEAD == gitlink == POB_VERSION == baseline metadata version, patch sentinels present; FAIL (not skip) for parity/corpus tests. (No `conftest.py` exists anywhere today; the CI check recommended by ADR-004 and the patches README was never implemented.)
10. **Follow-ups (separate from 3.5.2):** re-baseline parity against GUI 0.15.0 (the 0.12.2 baselines are the stale corner now; plan E3.5 item 5's harvest script); evaluate the jump to v0.22.0 (`860f4268299739ce9df87c4f373abe35824101cf`, 2026-06-30, current PoE2 patch) under the patch-day-survival workstream — first checking whether upstream has since fixed the three nil-safety issues; align `src/calculator/passive_tree.py`'s hardcoded `tree_version='0_3'` default (lines 246, 267-273) with the 0.15.0-era `0_4` TreeData.

## 7. Open questions for Alec

1. **Promote the 3 drafts to `external/patches/` and retire the stale 0.12.2 patch?** (Required before any repair; the plan reserves this promotion/rejection call for you.)
2. **Real submodule vs plain pinned vendor + setup script?** The plan assumes a real submodule, but the 2026-01-26 non-recursive re-clone is precisely how the submodule died; whichever you pick, `setup_pob.py` + the conftest guard are the actual safety net.
3. **Repair at v0.15.0 (recommended: zero behavior change, byte-identical reconstruction proven) and bump to v0.22.0 later — or jump straight to 0.22.0** (bigger bang: current game patch, but invalidates the byte-identical guarantee and requires re-checking whether the 3 patches are still needed/still apply)?
4. **When to re-baseline parity fixtures against GUI 0.15.0?** The baselines (GUI 0.12.2, captured 2025-10-21) are now the stale side of the drift; every parity claim currently compares across engine versions.
5. **Hunt for the pre-2026-01-26 original working copy?** It held the real submodule `.git` containing both phantom commits (`153245c5...`, `4cf3563f6...`). Content-wise there is nothing left to recover (the tree is fully explained), so this is archaeology-only — recommend dropping it and repointing to `3e1b71c9...`.
6. **Confirm the LF policy:** engine checkout with `core.autocrlf=false` (+ `core.eol=lf`) and `*.patch -text` gitattributes — matches the runtime-tested state and kills the CRLF false-negative class permanently.

### Answers — decided by Alec 2026-07-02 (recorded in sprint-change-proposal-2026-07-02.md §8.4)

1. **Promote + retire: YES — executed same day.** `external/patches/0001..0003` + `.gitattributes` landed; stale 0.12.2 patch `git rm`'d; README rewritten; ADR-004 addendum added. Drafts here stay as the forensic record.
2. **Real submodule** (plan wording stands); `setup_pob.py` + conftest guard remain the safety net (3.5.3/3.5.4).
3. **JUMP straight to v0.22.0** (`860f4268...`). Pre-ruling verification: upstream v0.22.0 still lacks all three nil fixes; `0001` regenerated against v0.22.0 (apply-check PASS, sentinel ×3, LuaJIT compile OK); `0002`/`0003` apply clean on both tags. The byte-identical-to-live guarantee is consciously traded for the current game patch; fallback lane = `3e1b71c9` (v0.15.0), same mechanics. New ripple found during verification: v0.22.0 ships `TreeData/0_5/` (plan E4/E5 tree targets amended 0_4 → 0_5).
   **Execution outcome (same day):** the jump was attempted and the **fallback lane was taken** — MinimalCalc cannot boot v0.22.0's `CalcSetup` (`:875` `env.spec:CollectGrantedPassiveNodesFromItems` et al.; 119 integration failures). Active pin = **v0.15.0 `3e1b71c9`** as this report originally recommended; post-fallback tree diffs **empty** vs the pre-repair backup (EOL-controlled) — the §5 byte-identical guarantee held in practice. v0.22.0 re-lands at the Epic 4 spike; the v0.22.0 patch variant is parked in this directory as `0001-global-lua-nil-safety-v0220.patch`.
4. **Re-baseline at the pin:** story 3.5.5 captures directly from GUI v0.22.0 (no interim 0.15.0 baselines); 0.12.2 baselines stale-flagged by 3.5.2 AC4.
5. **Archaeology dropped** — phantom gitlinks repointed by the repair; nothing content-wise to recover.
6. **LF policy confirmed** (`core.autocrlf=false` + `core.eol=lf` checkout; `*.patch -text`).

---

## 8. Ratification addendum — story 3.5.1 closeout (2026-07-02)

Ratified against story 3.5.1 AC-3.5.1.1 .. AC-3.5.1.5 (`docs/stories/story-3.5.1-pob-engine-forensics.md`). One AC element was missing from the report as landed and is closed here; everything else verified present. No file under `external/` was modified during ratification — fresh evidence below is read-only directory listings.

### 8.1 Closing the AC-3.5.1.4 gap: `src/Export/stub_functions.lua` dispositioned by name

- **Disposition: ABSENT FROM CURRENT TREE — historical documentation reference only; no hunk exists to adopt or reject.**
- `docs/architecture/pob-engine-dependencies.md:734` records a project-authored `external/pob-engine/src/Export/stub_functions.lua`, and the same doc's line 342 shows the historical loader call (`dofile(pobPath .. "/src/Export/stub_functions.lua") -- Headless stubs`). The file does not exist in today's vendored tree, and the section 2.2 file census independently corroborates this: 0 added files vs the clean v0.15.0 tracked set — a project-authored file would have appeared as an untracked extra.
- Most likely lost in the 2026-01-30 re-vendor (section 3 timeline: v0.15.0 source tree manually dropped in at 00:26, only Global.lua / ModStore.lua / CalcOffence.lua re-patched afterward). Per story 3.5.1 Dev Notes, the MinimalCalc dependency on this file is itself stale — either MinimalCalc no longer depends on it, or the architecture doc's reference needs updating; the pipeline has been running without the file since 2026-01-30.
- Consequence for the inventory: classification totals are unchanged (3 KEEP-AS-PATCH / 0 REJECT / 0 GENERATED / 1,067 EOL-NOISE). There is nothing to draft as a patch and nothing for 3.5.2-style repair to preserve. If a headless-stub file is ever needed again it is a new authored artifact, not a recovered local edit.

**Fresh evidence (2026-07-02, read-only):**

```
PS> Test-Path external\pob-engine\src\Export\stub_functions.lua
False
PS> Get-ChildItem external\pob-engine\src\Export | Select-Object Name
Bases  Classes  Enemies  ggpk  Minions  Scripts  Skills  Tree  Uniques
browse.lua  Launch.lua  Main.lua  passives.lua  spec.lua  statdesc.lua
```

Directory contains upstream v0.15.0 content only — `stub_functions.lua` is absent.

### 8.2 AC-3.5.1.1 completion note — scratch clone command

The evidence header records method and commit but not the exact scratch clone command. For reproducibility, the clean reference checkout used by probe C is reproduced by:

```
git -c core.autocrlf=false -c core.eol=lf clone https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2.git <scratch>/pob-0.15.0
git -C <scratch>/pob-0.15.0 checkout --detach 3e1b71c92dc5f7c295031700746a418558117b06
```

(`<scratch>` = session scratchpad, outside this repo; matches the Appendix's `pob-0.15.0/` at HEAD `3e1b71c9...` and the remote recorded in `.gitmodules`.)

### 8.3 Fresh cross-check — `docs/forensics/proposed-patches/` contents vs report claims

Directory listing (2026-07-02): `.gitattributes` (14 B), `0001-global-lua-nil-safety.patch` (4,318 B), `0001-global-lua-nil-safety-v0220.patch` (3,966 B), `0002-modstore-evalmod-nil-safety.patch` (1,474 B), `0003-calcoffence-ailment-buildup-nil-safety.patch` (2,557 B). This matches section 5's four staged deliverables plus the parked v0.22.0 variant of 0001 recorded in section 7 answer 3 after the same-day jump-and-fallback. Consistent; no unexplained files.

### 8.4 Ratification statement per AC

| AC | Verdict | Basis |
|---|---|---|
| AC-3.5.1.1 | PASS (with 8.2 note) | Hash `3e1b71c9...` + `manifest.xml:3` version in header/S1-S2; scratch clone outside repo (Appendix); clone command completed in 8.2 |
| AC-3.5.1.2 | PASS | `--stat` first (S2.2 / diff-stat.txt), full hunks (161-line diff + per-file hunks), EOL-controlled throughout, ModCache/generated classified separately (S4), census covers added/deleted/extras (S2.2: 0/0/0) |
| AC-3.5.1.3 | PASS | S4: exactly one disposition per hunk; 3 KEEP-AS-PATCH (= adopt-as-patch), 0 REJECT, 0 GENERATED; completeness proven by byte-identical reconstruction (S5); zero undispositioned |
| AC-3.5.1.4 | PASS (as of this addendum) | Global.lua dispositioned by name incl. verification vs the pre-existing patch (S4 cross-reference); ModStore.lua guards dispositioned by name (S4 #2, doc 444/464 -> live 458 drift acknowledged); stub_functions.lua dispositioned by name in 8.1: ABSENT |
| AC-3.5.1.5 | PASS | Read-only guarantee stated in header and S5; drafts staged under `docs/forensics/proposed-patches/`, never `external/patches/`; this ratification pass was likewise read-only |

**Story 3.5.1 is ratified complete.** The inventory stands as the authoritative diff-before-destroy record for plan risk #2; the only correction needed was the by-name stub_functions.lua verdict recorded above.

---

## Appendix — scratch artifacts (session-local, not committed)

Probe C's raw evidence lives under the session scratchpad `.../scratchpad/forensics/`: `diff-stat.txt`, `diff-vs-0.15.0.patch` (161 lines), `status-vs-0.15.0.txt` (1,070 ` M`), `diff-stat-vs-69b825bda.txt` (754-file distance), `ls-remote-tags.txt`, per-file `hunks/`, and the clean clone `pob-0.15.0/` (HEAD `3e1b71c9...`). Everything durable from them is embodied in section 4 and the committed draft patches; the scratchpad is disposable.
