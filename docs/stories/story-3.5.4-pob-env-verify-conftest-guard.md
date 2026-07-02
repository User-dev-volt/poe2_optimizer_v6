# Story 3.5.4: pob_env.verify() — Autouse Conftest Enforcement (FAIL, not skip)

Status: review  <!-- executed 2026-07-02; awaiting SM review. Guard verifies GREEN on today's repo; red-not-skip proven end-to-end against the real conftest -->


Epic: 3.5 — Substrate & Trust (lite) (`docs/pebo-master-plan.md:168`)
Sprint key: `3.5-4-pob-env-verify-conftest-guard`
Depends on: Story 3.5.2 (real submodule + generated `POB_VERSION.txt` + stale-flagged baselines), Story 3.5.3 (`scripts/setup_pob.py` + patch auto-apply primitive)
Estimated effort: 6–8h (4–6h guard + ~2h Flask smoke-test rider folded in per the 2026-07-02 decision — see AC-3.5.4.6)

## Story

As the **maintainer of parity evidence**,
I want **an importable `pob_env.verify()` check and an autouse conftest guard that FAILS parity/corpus tests whenever the PoB environment is wrong (fake submodule, version drift, hand-edited pin, missing patches)**,
so that **parity evidence can never again be produced against a drifted engine — enforcement that cannot be forgotten**.

## Acceptance Criteria

1. **AC-3.5.4.1:** `pob_env.verify()` is importable and checks the five environment invariants
   - (a) `external/pob-engine` is a real git repo (resolvable `.git` — gitfile or directory)
   - (b) submodule HEAD == parent gitlink (`git -C external/pob-engine rev-parse HEAD` vs the gitlink from `git ls-tree HEAD external/pob-engine`)
   - (c) `POB_VERSION.txt` carries Story 3.5.2's generation marker (hand-edits detectable) and its recorded commit matches the gitlink
   - (d) baseline metadata versions match the pinned version or are explicitly stale-flagged; a version mismatch without a stale flag — or missing version metadata — is a violation (today's source: `tests/fixtures/parity_builds/gui_baseline_stats.json` `_metadata.pob_version`; Story 3.5.5's harvested fixtures adopt the same metadata contract)
   - (e) every patch in `external/patches/*.patch` is applied to the submodule working tree
   - Returns a structured result — `ok: bool` plus an ordered list of violations, each with an actionable message (which invariant, observed vs expected, and the fix — normally `python scripts/setup_pob.py`) — so callers choose fail/report behavior

2. **AC-3.5.4.2:** Patch verification is data-driven from the patch set
   - Iterate `external/patches/*.patch` (sorted); one applied-check per patch file (e.g. `git apply --reverse --check`, the Story 3.5.3 skip-if-applied primitive)
   - No hardcoded patch filename or content marker anywhere — specifically NOT ADR-004's grep-marker method — so removing ADR-004's patch after the Epic 4 spike (`docs/pebo-master-plan.md:190-191`) is a one-edit change: delete the `.patch` file
   - An empty patch directory passes check (e) trivially

3. **AC-3.5.4.3:** Autouse fixture FAILS (not skip) the guarded paths; unmarked tests unaffected
   - Autouse fixture in `tests/conftest.py` (the repo currently has no conftest.py anywhere), marker-dispatched: verification applies to tests marked `parity` / `gui_parity` (pytest.ini:12-13), runs verify once per session (cached), and goes red on failure via `pytest.fail(..., pytrace=False)` carrying the verifier's actionable message — failed/errored-at-setup, never `pytest.skip`, never silently green
   - The corpus-validation entry path is guarded identically: `scripts/run_epic2_validation_isolated.py` calls the same `verify()` at startup and exits nonzero listing violations before spending corpus machine time
   - Unmarked tests unaffected: plain `pytest tests/unit/` runs incur no verification subprocess cost (cheap no-op) and gain no new failure mode

4. **AC-3.5.4.4:** Negative test proves the guard
   - With a deliberately broken environment (e.g. stale/hand-edited `POB_VERSION.txt` in a tmp-dir env double), the parity-marked test path demonstrably goes red with the expected violation message
   - The test asserts the outcome is failed/errored — explicitly NOT skipped

5. **AC-3.5.4.5:** Verification reusable by scripts unchanged
   - `scripts/setup_pob.py` (Story 3.5.3) can call it as a post-setup check, and the future `release_gate.py` (Epic 4 item 6, `docs/pebo-master-plan.md:204-208`) can import it unchanged
   - The verifier module has no pytest dependency (pure repo-state function; stdlib + git subprocess only) and accepts an explicit repo-root parameter (default: project root) so tests and tools can point it at env doubles

6. **AC-3.5.4.6:** Flask smoke tests close the `src.web` test-debt (rider folded in 2026-07-02 — proposal section 7.6 / sprint-status known-debt note)
   - 1–2 Flask test-client tests exist (e.g. `tests/integration/test_web_smoke.py`): `POST /optimize` happy path on a small fixture runs to a successful terminal event, and the export round-trip yields a code that re-parses via `parse_pob_code`
   - These are the first automated tests importing `src.web` (today: zero — the thin-slice step-10 debt)
   - Run under `pytest -n 1` (they drive the real optimizer → ADR-003 LuaJIT constraint applies); NOT parity-marked — the env guard must not gate them

## Tasks / Subtasks

- [x] Task 1: Implement `pob_env.verify()` (AC: 3.5.4.1, 3.5.4.2, 3.5.4.5)
  - [x] Subtask 1.1: Create `src/pob_env.py` with `verify(repo_root=None) -> PobEnvResult` (`PobEnvResult`: `ok`, `violations` list, human-readable `summary()`)
  - [x] Subtask 1.2: Implement checks (a)–(d): real-repo, HEAD==gitlink, `POB_VERSION.txt` marker + commit match, baseline metadata match-or-stale-flag
  - [x] Subtask 1.3: Implement check (e) by iterating `external/patches/*.patch` with `git apply --reverse --check` per patch (absolute paths, explicit `cwd`, no `shell=True`)
  - [x] Subtask 1.4: Actionable violation messages: name the invariant, observed vs expected values, and the fix command
- [x] Task 2: Wire the autouse conftest guard (AC: 3.5.4.3)
  - [x] Subtask 2.1: New `tests/conftest.py`: session-cached verify result + autouse fixture dispatching on `request.node.get_closest_marker("parity")` / `("gui_parity")`
  - [x] Subtask 2.2: `pytest.fail(result.summary(), pytrace=False)` on violation; strict no-op (no subprocess spawned) when the item carries neither marker
  - [x] Subtask 2.3: Keep the guarded path fast (<200ms target): one lazy verify per session, triggered by the first marked test, result reused by all others
- [x] Task 3: Fail-fast the corpus entry path (AC: 3.5.4.3)
  - [x] Subtask 3.1: In `scripts/run_epic2_validation_isolated.py` `main()` (scripts/run_epic2_validation_isolated.py:232), call `verify()` before any corpus work; print violations and exit nonzero with a distinct exit code (Story 3.5.3 dev notes reserve distinct codes for exactly this branching)
- [x] Task 4: Negative-path tests with tmp-dir env doubles (AC: 3.5.4.4; positive coverage of AC 3.5.4.1–3.5.4.2)
  - [x] Subtask 4.1: Unit tests for `verify()` against fabricated env doubles in `tmp_path`: missing `.git`, gitlink mismatch, marker-less/hand-edited `POB_VERSION.txt`, unflagged stale baseline metadata, unapplied patch — each yields its expected violation
  - [x] Subtask 4.2: Guard-level negative test: run a parity-marked dummy test against a broken env double (pytester, or a subprocess pytest run with the verify root overridden) and assert red-not-skip with the expected message
  - [x] Subtask 4.3: Positive path: with a well-formed env double (all invariants hold), `verify()` returns ok and the marked dummy test passes
- [x] Task 5: Document the guard (AC: 3.5.4.3)
  - [x] Subtask 5.1: One paragraph in README's testing section plus a note beside CLAUDE.md's Test Markers list: what the guard checks, that parity/corpus runs FAIL (not skip) on a bad environment, and that `python scripts/setup_pob.py` is the fix
- [x] Task 6: Flask smoke tests — the folded-in rider (AC: 3.5.4.6)
  - [x] Subtask 6.1: `tests/integration/test_web_smoke.py` using Flask's test client: `POST /optimize` happy path on the smallest working corpus fixture with a tiny iteration budget → successful terminal event; assert the export code re-parses via `parse_pob_code` (round-trip)
  - [x] Subtask 6.2: Keep them unmarked-for-parity (guard no-op applies) and document the `-n 1` requirement in the module docstring

## Dev Notes

- Plan wording this story implements (`docs/pebo-master-plan.md:177-179`): "Enforcement that cannot be forgotten: autouse conftest fixture `pob_env.verify()` — submodule is a real repo, HEAD == gitlink == POB_VERSION == baseline metadata version, nil-safety patch marker present. FAIL (not skip) for parity/corpus tests." Ordered as immediate next action item 3 at `docs/pebo-master-plan.md:331`.
- FAIL-not-skip is the entire point: a skipped parity suite reads green in CI summaries and lets drift back in. Context: parity evidence is currently near-worthless partly because it was produced against an unverifiable engine — `external/pob-engine` has no `.git`, and version drift is four-way (`POB_VERSION.txt` pins `69b825bda`/v0.12.2, parent gitlink `4cf3563f6`, working tree 0.15.0, baselines from GUI 0.12.2) [`docs/pebo-master-plan.md:55-62`]. This guard closes plan risks #2 (unrecorded submodule edits), #5 (tolerance-loosening temptation), and #7 (patch-day churn silently invalidating artifacts) [`docs/pebo-master-plan.md:313,316,318`].
- **Coordination hazard (sprint change proposal section 7.3-E):** the Epic 4 spike may conclude ADR-004's nil-safety patch is unnecessary under the real ModParser (`docs/pebo-master-plan.md:190-191`). Hence AC-3.5.4.2: the plan's literal "nil-safety patch marker present" is implemented as "every patch present in `external/patches/` is applied". The grep-marker verification documented in `docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md:178-232` and `external/patches/README.md` is superseded by this data-driven check. As of 2026-07-02 the directory holds the promoted set `0001-global-lua-nil-safety.patch` (v0.15.0-targeted after the same-day jump-fallback), `0002-modstore-evalmod-nil-safety.patch`, `0003-calcoffence-ailment-buildup-nil-safety.patch` (+ `.gitattributes`); the stale 0.12.2 `global-lua-nil-safety.patch` is retired. Story 3.5.2 EXECUTED: the submodule is real (pinned `3e1b71c9`), all three patches applied — all three `--reverse --check`s pass on the live tree, and `scripts/generate_pob_version.py --check` is the ready-made hand-edit detector for check (c). The guard should verify GREEN against today's repo state.
- `pytest.fail()` raised from a fixture surfaces as a setup ERROR, not a test FAILURE — both are red and both satisfy the requirement; the AC-3.5.4.4 test should accept either outcome and reject only `skipped`/`passed`.
- Marker mechanics: `tests/integration/test_gui_parity.py:58` applies `parity` module-wide via `pytestmark`, with `gui_parity` added per-test (e.g. :116); `request.node.get_closest_marker()` sees both forms. `--strict-markers` is already enforced (pytest.ini:21). Do not gate `slow` or `performance` marked tests.
- Import convention: use `from src.pob_env import verify` — matching how tests already import production code (`tests/integration/test_gui_parity.py:36`) and how scripts import after inserting the project root (`scripts/run_epic2_validation_isolated.py:43`). One module, both entry points (AC-3.5.4.5).
- Sequencing reality: against today's pre-repair tree, `verify()` MUST report violations (no real repo, no generation marker, drifted versions). That is a built-in development sanity check — prove the guard red on the current broken state, then green after 3.5.2/3.5.3 land. Do not weaken checks to pass on the pre-repair tree.
- Stale-flag semantics: an explicit stale flag on a baseline (written by Story 3.5.2 AC4, carried forward by Story 3.5.5 AC5) is an honest state — verify passes it. The guard enforces environment honesty; what the parity suite does with stale baselines is the suite's (and Epic 4 validation's) concern, not this story's.
- Scope guard (v1 NOT-list, `docs/pebo-master-plan.md:145-158`): substrate/trust work only — no product surface, no new dependencies (stdlib + git subprocess). The known-gaps ratchet and trust-tier generator are explicitly deferred to Epic 4 (`docs/pebo-master-plan.md:183-184`) — do not build them here. The Flask smoke-test rider was FOLDED INTO this story on 2026-07-02 (AC-3.5.4.6 / Task 6, +~2h effort) — it now has a tracked home; keep it scoped to the 1–2 tests the proposal names.
- Windows: `subprocess` git calls with explicit `cwd` and absolute paths, no `shell=True`; integration runs stay `pytest -n 1` per ADR-003/CLAUDE.md. The guard itself spawns only git (no LuaJIT), so it is safe under xdist too.

### Project Structure Notes

- New module `src/pob_env.py` beside the existing packages (`calculator/`, `models/`, `optimizer/`, `parsers/`, `web/`) — the first top-level utility module in `src/`. Chosen because test code and scripts must import one implementation unchanged (AC-3.5.4.5); `tests/support/` was rejected because scripts do not import from `tests/`.
- New `tests/conftest.py` — the repository currently has no conftest.py; with `testpaths = tests` (pytest.ini:34) this single file covers the whole suite.
- Modifies `scripts/run_epic2_validation_isolated.py` startup only — no behavior change to the corpus run itself, which is the M0 / Epic 4 item 6 gate entry (`docs/pebo-master-plan.md:163-166`).
- New tests under `tests/unit/` (verify unit tests and the pytester-based guard test are fast and LuaJIT-free — no `-n 1` constraint).

### References

- [Source: docs/pebo-master-plan.md:177-179] — Epic 3.5 item 4: the enforcement requirement (autouse `pob_env.verify()`, FAIL not skip)
- [Source: docs/pebo-master-plan.md:55-62] — section 2 items 4–5: four-way version drift; parity evidence near-worthless against an unverifiable engine
- [Source: docs/pebo-master-plan.md:313,316,318] — section 8 risks #2, #5, #7: the failure modes this guard structurally closes
- [Source: docs/pebo-master-plan.md:331] — section 9 item 3: "repair the submodule, pin, `setup_pob.py`, conftest guard"
- [Source: docs/pebo-master-plan.md:190-191] — Epic 4 spike answers whether ADR-004's patch is still needed (why AC-3.5.4.2 is data-driven)
- [Source: docs/pebo-master-plan.md:204-208] — Epic 4 item 6: `release_gate.py` + stale-artifact refusal — the second script consumer of `verify()`
- [Source: docs/sprint-change-proposal-2026-07-02.md section 8.1] — story spec, dependencies (3.5.2, 3.5.3), 4–6h envelope
- [Source: docs/sprint-change-proposal-2026-07-02.md section 7.3-E] — coordination hazard: patch checks must be patch-set-driven, no hardcoded nil-safety marker
- [Source: docs/stories/story-3.5.2-submodule-repair-and-pin.md AC3–AC4] — generated `POB_VERSION.txt` with generation marker; stale-flagged 0.12.2 baselines (inputs to checks (c)–(d))
- [Source: docs/stories/story-3.5.3-setup-pob-script.md AC1–AC2, Dev Notes] — `git apply --check` / `--reverse --check` skip-if-applied primitive; distinct exit codes reserved for this story's branching
- [Source: pytest.ini:10-14,21,34,37] — `parity` / `gui_parity` marker definitions, `--strict-markers`, `testpaths`, `pythonpath = src`
- [Source: tests/integration/test_gui_parity.py:58,116] — module-level `pytestmark = pytest.mark.parity`; per-test `@pytest.mark.gui_parity`
- [Source: tests/fixtures/parity_builds/gui_baseline_stats.json] — `_metadata.pob_version: "0.12.2"` — today's baseline-metadata source for check (d)
- [Source: POB_VERSION.txt] — current hand-written pin (commit `69b825bda...`, v0.12.2-61) including the `--remote` update anti-pattern the guard makes impossible to reintroduce silently
- [Source: external/patches/] — promoted set `0001..0003` + `.gitattributes` (2026-07-02); README.md documents the skip-if-applied discipline AC-3.5.4.2 mechanizes
- [Source: docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md:178-232] — manual reapplication/verification instructions this story mechanizes
- [Source: scripts/run_epic2_validation_isolated.py:232] — `main()`: the corpus-validation entry point to guard

## Dev Agent Record

### Context Reference

- Executed 2026-07-02 on branch `feat/story-3.5.3-3.5.4-setup-and-guard`, immediately after story 3.5.3 (same session). Scouts pre-mapped: web API contract (verified end-to-end incl. a live tiny-budget optimize run), pytest/marker infrastructure, baseline metadata shape, patch-check convention.

### Agent Model Used

claude-fable-5 (Claude Code, ultracode session)

### Debug Log References

- Live `python -m src.pob_env` → "PoB environment OK (all five invariants hold)", exit 0 (the story's built-in sanity check, post-3.5.2/3.5.3 = GREEN as predicted)
- Guard red-not-skip subprocess evidence inside `tests/unit/test_pob_env.py::TestConftestGuard`
- `pytest -n 1 tests/integration/test_web_smoke.py` → 2 passed in 12.05s

### Completion Notes List

1. **AC-3.5.4.1:** `src/pob_env.py` — first top-level utility module in `src/` as planned. `verify(repo_root=None) -> PobEnvResult` (frozen dataclasses: `ok`, ordered `violations` tuple, human `summary()`); checks (a) resolvable `.git` + rev-parse probe, (b) submodule HEAD vs `git ls-tree HEAD` gitlink, (c) generation marker + `Commit:` line vs gitlink, (d) baseline `_metadata.pob_version` match-or-stale-flag (pinned version read from the submodule's `manifest.xml`; missing metadata/file = violation; `"stale": true` passes as the honest state), (e) per-patch `git -c core.autocrlf=false apply --reverse --check` from repo root. Every violation names the invariant, observed vs expected, and the fix (`python scripts/setup_pob.py`). Never raises on a bad env.
2. **AC-3.5.4.2:** patch verification iterates `external/patches/*.patch` sorted — no filename, count, or content marker hardcoded anywhere (ADR-004's grep-marker method superseded); empty/missing patch dir passes trivially. Retiring a patch = deleting its file.
3. **AC-3.5.4.3:** new `tests/conftest.py` (first conftest in the repo): autouse fixture dispatching on `request.node.get_closest_marker("parity"/"gui_parity")` (catches module-level `pytestmark` and per-test markers), lazy one-verify-per-session cache (per xdist worker), `pytest.fail(summary, pytrace=False)` → red as setup ERROR, never skip. Strict no-op for unmarked tests (returns before any subprocess). Corpus path guarded identically: `scripts/run_epic2_validation_isolated.py` calls the same `verify()` first thing in `main()` and exits **2** (distinct from its existing 0/1) printing the violation list; its docstring documents the code.
4. **AC-3.5.4.4:** negative proof runs the REAL conftest guard, not a replica: `tests/unit/test_pob_env.py::TestConftestGuard` drops a parity-marked dummy test under `tests/` (so the actual conftest chain loads) and runs pytest in a subprocess with `POB_ENV_GUARD_ROOT` pointing at a fabricated broken env double → asserts nonzero exit, the violation banner, "1 error"/"1 failed", and explicitly NOT skipped/passed. Positive twin: well-formed double → "1 passed". (Subprocess-pytest was chosen over pytester: `pytest_plugins` is only legal in a rootdir conftest, and the subprocess route exercises the genuine guard end-to-end — the story's sanctioned alternative.)
5. **AC-3.5.4.5:** verifier is stdlib + git subprocess only, zero pytest imports, explicit `repo_root` param; consumed unchanged by conftest and the corpus script; `python -m src.pob_env` CLI included. The `GENERATED_MARKER` literal is mirrored from `scripts/generate_pob_version.py` (src must not import scripts/) and a unit test pins the two constants equal.
6. **AC-3.5.4.6 (rider):** `tests/integration/test_web_smoke.py` — the first automated tests importing `src.web`. Happy path: `deadeye_lightning_arrow_76.xml` (attack build → MinimalCalc fast path; the parity_builds codes carry zero skills and are gate-rejected) encoded to a PoB code, caps monkeypatched on `src.web.routes` (MAX_ITERATIONS=2 — routes reads them by name, patching config would be invisible), POST `/optimize` → poll `/result` to `complete` → GET `/export` → exported code re-parses via `parse_pob_code` with node-change consistency asserted. Second test: garbage code → structured 400. NOT parity-marked (guard no-ops); `-n 1` requirement in the module docstring. Verified: 2 passed in 12.05s.
7. **Env doubles:** fabricated as REAL git repos in `tmp_path` — genuine mode-160000 gitlink via `git update-index --add --cacheinfo` (no clone/network), tiny submodule repo with manifest + patchable target file. 9 violation/positive unit tests, each isolating one invariant.
8. **Data correction:** `gui_baseline_stats.json` `_metadata.stale_reason` still claimed the pin was v0.22.0 `860f4268` (written before 3.5.2's AC5 fallback executed) — corrected to v0.15.0 `3e1b71c9`. The `stale: true` flag itself was already correct, so check (d) semantics are unchanged.
9. **Sequencing sanity check:** live verify is GREEN on today's repaired repo (as the dev notes demanded post-3.5.2/3.5.3); a real parity-marked test (`test_gui_parity_build[build_01_witch_90]`) executes through the guard and fails only on its pre-existing stale-baseline/MinimalCalc parity assertion — proving the guard neither blocks nor masks the suite. Full unit suite: 288 passed (262 pre-existing + 26 new).
10. **Docs:** README testing section gained the guard paragraph; CLAUDE.md gained the enforcement note beside Test Markers.
11. **Ultracode adversarial review round (same day, 61-agent panel, 22 confirmed findings across both stories) hardened the verifier:**
    - **(e) is now byte-exact:** `patched_tree_mismatches()` reconstructs "pristine pinned blobs + full patch set applied once" in a scratch repo and byte-compares (EOL-normalized — the live v0.15.0 checkout renders CRLF over LF blobs; git treats them identical) every patched file, and flags any OTHER tracked submodule file with local modifications. This closes the reviewer-reproduced blind spot where a double-applied 0002 still passes `--reverse --check`, and catches unrecorded engine edits (plan risk #2). Shared with `setup_pob.py` (single implementation).
    - **(c) strengthened:** also validates the `Version:` line against the pinned manifest and that every present patch has an entry line. Full regenerate-and-compare remains available as `generate_pob_version.py --check` for release gates (residual: a hand-edit forging exactly commit+version+patch lines in place passes (c) but cannot change what (e) byte-verifies).
    - **(b) pin source deviation (justified):** the gitlink is read from the **index** (`git ls-files -s`), not the AC's `git ls-tree HEAD` — setup_pob.py and generate_pob_version.py define "the pin" from the index, and one definition across all three tools prevents a staged-pin-bump from producing a contradictory "setup says OK / verify says drift / fix says run setup" loop. Unmerged gitlink stages are reported, never guessed.
    - **Never-raises belt:** decode/OS/JSON errors become violations; any internal crash returns an `(internal) verifier-error` violation instead of propagating — the corpus script's exit 2 can no longer collapse into a misclassified exit 1.
    - **Guard:** cache keyed by verified root; an active `POB_ENV_GUARD_ROOT` override is named in the failure banner. Probe files renamed to non-`test_*.py` (a leaked probe dir is inert for collection) and the broken-env run now ALSO proves an unmarked test passes in the same session (no over-gating) plus the violation-specific message reaching output. Corpus guard covered by a unit test (exit 2 + message).
    - Final counts: 303 unit tests pass (22 in test_pob_env.py, 19 in test_setup_pob.py); live verify GREEN; setup double-run still byte-identical.

### File List

- `src/pob_env.py` — new
- `tests/conftest.py` — new (first conftest in the repo)
- `tests/unit/test_pob_env.py` — new
- `tests/integration/test_web_smoke.py` — new
- `scripts/run_epic2_validation_isolated.py` — modified (env guard at `main()` start, exit 2; docstring exit-code table)
- `README.md` — modified (guard paragraph in Testing)
- `CLAUDE.md` — modified (guard note beside Test Markers)
- `tests/fixtures/parity_builds/gui_baseline_stats.json` — modified (`stale_reason` v0.22.0 → v0.15.0 correction)

## Change Log

**2026-07-02** — Story created via correct-course sprint change proposal
- Drafted per `docs/sprint-change-proposal-2026-07-02.md` section 8.1, implementing `docs/pebo-master-plan.md:177-179` (Epic 3.5 item 4); rewritten from the proposal's light draft into the house BMAD story format; status: drafted

**2026-07-02 (later)** — Flask smoke-test rider folded in; patch-set facts refreshed
- Alec decision: rider (proposal section 7.6, ~2h) becomes AC-3.5.4.6 / Task 6; effort 4–6h → 6–8h
- external/patches/ now holds the promoted 0001..0003 set (0001 targets the v0.22.0 pin); pre-repair guard-RED expectation documented

**2026-07-02 (execution)** — Story executed; status → review
- `src/pob_env.py` + `tests/conftest.py` guard + corpus fail-fast (exit 2) + unit tests + 2 Flask smoke tests delivered
- Guard GREEN on the repaired repo; red-not-skip proven against the real conftest via subprocess pytest with `POB_ENV_GUARD_ROOT` env doubles
- `gui_baseline_stats.json` stale_reason corrected (v0.22.0 → v0.15.0 `3e1b71c9`, the AC5 fallback reality)

**2026-07-02 (review hardening)** — Ultracode adversarial review round applied (Completion Note 11)
- (e) byte-exact ratified-state reconciliation + unrecorded-edit detection; (c) Version/patch-entry checks; pin read from index (one pin definition across tools); never-raises belt; guard cache keyed by root; inert-if-leaked probes; unmarked-unaffected + corpus-guard tests
