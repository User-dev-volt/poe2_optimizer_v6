# Story 4.2: FullCalcEngine Behind build_calculator.py — Respawnable 2-Worker Pool + Cooperative Cancel

Status: ready-for-dev

**Epic:** 4 — Truth Engine → **v1 ships here** [Source: docs/pebo-master-plan.md:192-224]
**Tracking key:** `4-2-fullcalcengine-worker-pool-cooperative-cancel` — the entry already exists at docs/sprint-status.yaml:108 (added at authoring as `ready-for-dev`); flip it to `in-progress` at dev start (T9). [Source: docs/sprint-status.yaml:108]
**Effort:** drawn from the Epic 4 shared envelope (~80–140h); item 2 is NOT independently timeboxed (unlike item-1's 2-week spike). [Source: docs/pebo-master-plan.md:192]
**Dependencies:**
- **Story 4.1 DONE** — ships the spike-grade `src/calculator/driver.lua` (JSON protocol; `LOAD_BUILD`/`GET_STATS`/`PING`/`GC`/`SHUTDOWN` live, `EVAL_NEIGHBORS`/`APPLY_MOVE` reachable stubs), the single-worker `src/calculator/driver_worker.py` (`DriverWorker`, bounded reads, `restart()`, `WorkerCrash`), `tests/integration/test_driver_parity.py` (gui_parity 10/10, deadeye 23003.185361227 ±0.000%), and ADR-005..008 stubs. Verdict: 🟢 GO, embedded-Lupa lane. [Source: docs/stories/4-1-truth-engine-driver-spike.md:242-266,268-279]
- **Item-3 `activeSpec` READ parse fix** (`_extract_passive_nodes` returns an EMPTY set for list-typed multi-`<Spec>` builds) is a CROSS-ITEM dependency for multi-spec FullCalc reporting — 4.2 FENCES FullCalc reporting to single-`<Spec>` builds until item 3 lands the read-side fix (the WRITE side already handles `activeSpec`). [Source: src/parsers/pob_parser.py:234-236,378; docs/stories/4-1-truth-engine-driver-spike.md:103,236]

## Story

As the **PEBO Truth-Engine dev**,
I want **the real PoB calculation lane (Story 4.1's `driver.lua`) graduated from a standalone spike into production: a `FullCalcEngine` reachable behind the existing `build_calculator.py` interface, driven by a respawnable 2-worker process pool that contains any native SEH as a recoverable `WorkerCrash`, fed by XML-direct build loading, with a cooperative cancel flag threaded through the optimizer loop and the web layer — while MinimalCalc keeps running the hot neighbor search (its speed rewire is item 4)**,
so that **the two numbers a user actually reads (baseline + optimized DPS/EHP) become GUI-accurate — closing the ~4%-of-GUI MinimalCalc reporting gap — a long optimization can be stopped on demand instead of only timing out, and the pool + seam + cancel loop are exactly the surfaces Epic 4 item 4 (the `EVAL_NEIGHBORS` batch rewire) extends without rework**.

## Context & Approach (READ FIRST)

**Item 2 = Truth-Engine REPORTING + the whole engine seam. Item 4 = Truth-Engine SEARCH.** This split is the load-bearing decision of the story (see Dev Notes → "Decisions taken at authoring"). A full `LOAD_BUILD` per neighbor is warm **0.24–0.53s** (4.1-measured) × 50–200 neighbors/iteration = **60–100s/iteration**, which blows `max_time_seconds=300`. The master plan already sequences search-speed machinery (one `EVAL_NEIGHBORS` batch/iteration via `getMiscCalculator`, `useFullDPS=false`, modKey caching) to **item 4**. Therefore item 2 keeps MinimalCalc in the hot neighbor loop as the ranking oracle and uses `FullCalcEngine` ONLY for the two reported numbers at the loop boundaries (+2 FullCalc calls/run, O(1), zero budget risk). [Source: docs/pebo-master-plan.md:210-212,326; docs/stories/4-1-truth-engine-driver-spike.md:234; src/models/optimization_config.py:61]

## Acceptance Criteria

1. **AC-4.2.1: `FullCalcEngine` sits BEHIND the existing interface (coexists with MinimalCalc).** A new class in `src/calculator/full_calc_engine.py` exposes `calculate(build: BuildData) -> BuildStats`, reachable via a keyword-only selector `calculate_build_stats(build, *, engine="auto"|"full")`. `engine="auto"` (default) leaves today's `is_attack_skill` MinimalCalc/Subprocess hybrid AND its fallback byte-identical; `engine="full"` routes to `get_full_calc_engine().calculate(build)` when `build.source_xml` is present, else falls through to the hybrid. This is a THIRD coexisting route — item 8 (NOT 4.2) retires MinimalCalc. [Source: docs/pebo-master-plan.md:200-202,224; src/calculator/build_calculator.py:98,154-185,196-221]

2. **AC-4.2.2: Worker stats → `BuildStats` mapping is correct and archetype-aware.** `FullCalcEngine` maps `GET_STATS` output to `BuildStats` by porting `full_pob_engine._extract_stats`' int-cast / `__post_init__`-safe shape, extended so the headline DPS = **first-nonzero(`TotalDPS`, `CombinedDPS`, `FullDPS`, `TotalDot`)** computed PYTHON-side (`driver.lua` stays a verbatim reader — do NOT add fallback logic in Lua); all fields `OptimizationResult.to_dict()` consumes are populated. Because `GET_STATS` returns a JSON **dict** (not a Lua table) and OMITS absent stats entirely, the port MUST read via dict-safe `.get(key, default)` and KEEP the `int(...)` casts — `BuildStats.__post_init__` hard-rejects non-int `life`/`energy_shield`/`mana`/`armour`/`evasion` and NaN/inf floats, so a verbatim Lua-table copy trips it. [Source: src/calculator/full_pob_engine.py:257-306; src/calculator/driver.lua:356-377; src/models/build_stats.py:86-103; src/models/optimization_config.py:245-263]

3. **AC-4.2.3: A respawnable 2-worker pool wraps `DriverWorker`.** `WorkerPool(size=2 default, override via `PEBO_WORKER_POOL_SIZE`)` is a MODULE SINGLETON in `src/calculator/worker_pool.py` wrapping N `DriverWorker` child processes: LAZY spawn (first `acquire`, so MinimalCalc-only runs never boot LuaJIT), a bounded `queue.Queue(size)` of idle workers, and a `with pool.acquire(timeout=1.0) as w:` context manager that HEALTH-CHECKS (`is_alive()` + a cheap `PING`) and respawns-if-dead BEFORE handing out, with `finally`-guaranteed `release()`. The pool is PROCESS-based, NOT thread-local (workers are OS processes; the run is single-threaded under `optimization_lock`), so `build_calculator`'s `threading.local()` MinimalCalc/Subprocess engines are untouched. Worker #2 is a WARM STANDBY / respawn target in item 2 (no cold ~0.7s boot mid-run); item 4 fans `_evaluate_neighbors` across both with no pool-API change. 2 × ~293MB ≈ 586MB stays inside risk #9's 200–400MB-per-worker envelope. [Source: src/calculator/driver_worker.py:128-160,316,355-358; src/web/optimization_runner.py:114; docs/pebo-master-plan.md:331; docs/decisions/ADR-006-worker-pool-process-isolation.md:22-24]

4. **AC-4.2.4: The POOL owns respawn — bounded, diagnostic, SEH-aware.** A `WorkerCrash` raised anywhere in `acquire`/health-check/calc CLOSES the dead worker's pipes and CAPTURES `stderr_tail` before `restart()`; a bounded `_respawn_budget` (e.g. max 5 / 60s) FAILS the run with the captured `stderr_tail` on a deterministic-SEH build rather than respawn-looping; a benign TEARDOWN SEH after `SHUTDOWN` (ADR-003, `0xe24c4a02`) is EXCLUDED from the budget via a `_shutting_down` flag. [Source: src/calculator/driver_worker.py:279-285,307-313,360-384; docs/decisions/ADR-003-windows-luajit-cleanup-mitigation.md]

5. **AC-4.2.5: A mid-calc crash maps to a clean error, NEVER a sentinel.** A mid-calc `WorkerCrash` maps to `CalculationError` with exactly ONE automatic retry on a fresh worker; the pool NEVER returns a zero/sentinel `BuildStats`. Item-2 landing zone: FullCalc runs ONLY at the two reporting boundaries, so a still-failing `CalculationError` is caught by the reporting guard (AC-4.2.11 / T7) which downgrades reporting to MinimalCalc — it does NOT reach `_evaluate_neighbors` or `resolve_main_socket_group` (those stay on the `engine="auto"` MinimalCalc path, which never touches the pool). The never-a-sentinel contract is what makes that fallback safe AND is the forward-looking guarantee that when item 4 moves the SEARCH onto FullCalc, a crash cannot WIN `_select_best_neighbor`'s `max()` (which does NOT compare against the incumbent, so a large sentinel would win outright). [Source: src/optimizer/hill_climbing.py:449-461,411-419; src/calculator/build_calculator.py:270-276]

6. **AC-4.2.6: The 4.1-deferred crash-survival cluster is closed as production fixes.** In `driver_worker.py`: **(a)** guard the `_send` `json.loads(line)` so a malformed protocol line raises `WorkerCrash`, not a bare `JSONDecodeError` (:286); **(b)** a `_die()` helper closes `stdin`/`stdout`(+`stderr`) before EVERY `WorkerCrash` raise, not only in `stop()` (:279-285 vs :372-377); **(c)** default per-worker `stderr` capture so `_stderr_tail()` is never blank when a crash occurs (:136,:168-172,:346-353); **(d)** `get_stats()` RAISES on an `{ok:false}` envelope instead of returning the raw dict as if it were stats (:294-296); **(e)** `eval_neighbors`/`apply_move` build the payload then set `cmd` LAST so a payload key cannot clobber it (:298-302). **(g)** `scripts/triage_m0_builds.py` gets a per-build `try/except` around the five-loop body so one bad build cannot abort the evidence table. [Source: src/calculator/driver_worker.py:136,286,294-302,346-353; scripts/triage_m0_builds.py; docs/stories/4-1-truth-engine-driver-spike.md:299]

7. **AC-4.2.7: `BuildData` carries its source XML; a reusable patch helper is extracted.** `BuildData` gains `source_xml: Optional[str] = None`, populated in `parse_pob_code` (which already holds the decoded `xml_str`); neighbors inherit it FOR FREE via `dataclasses.replace` (the optimizer mutates only `passive_nodes`). A helper `patch_passive_nodes_to_xml(source_xml, nodes, main_socket_group) -> str` is extracted from `encode_pob_code`'s guts, returning the raw patched XML (the `build_xml(data)` intermediate) BEFORE `zlib`/`base64`; `encode_pob_code` is REFACTORED to call the same primitive then compress+encode (single primitive, no fork). `source_xml=None` ⇒ FullCalc unavailable ⇒ `engine="full"` raises `CalculationError` (search unaffected; reporting falls back to MinimalCalc). [Source: src/parsers/pob_parser.py:25,74,156,199,252,259; src/models/build_data.py:44-66; src/optimizer/neighbor_generator.py:169-172 (the actual `replace(build, passive_nodes=...)`); src/optimizer/hill_climbing.py:195]

8. **AC-4.2.8: G2 (highest-correctness) — the patch helper ALSO writes `Build @mainSocketGroup`.** `encode_pob_code` today patches allocated nodes only and NEVER writes `@mainSocketGroup`, but `resolve_main_socket_group` MUTATES `build.main_socket_group` in Python and PoB reads `@mainSocketGroup` from the XML — so without also writing it the worker calcs the file's ORIGINAL main skill and the reported numbers diverge from the Python path. `patch_passive_nodes_to_xml` MUST write `Build @mainSocketGroup` from `build.main_socket_group`. Pin with a `gui_parity` test asserting deadeye `TotalDPS 23003.185361227` within ±0.1% THROUGH the `FullCalcEngine` seam. [Source: src/parsers/pob_parser.py:116,244-252; src/calculator/build_calculator.py:291; tests/integration/test_driver_parity.py]

9. **AC-4.2.9: Cooperative cancel token in the optimizer.** `OptimizationConfiguration` gains `cancel_check: Optional[Callable[[], bool]] = None` (beside `progress_callback`; NO `__post_init__` validation). It is checked (1) at the TOP of the main `while` loop, co-located with the `elapsed >= max_time_seconds` check, and (2) PER-NEIGHBOR inside `_evaluate_neighbors` (threaded in as a new param via the call site), which breaks the sweep early and returns partial evaluations. Cancellation sets a NEW terminal `convergence_reason="cancelled"` and returns best-so-far. A `Callable` (not a bare bool) is required because the daemon optimizer thread cannot be force-killed — cooperative is the only safe cancel — and it is test-friendly. [Source: src/models/optimization_config.py:65; src/optimizer/hill_climbing.py:167-173,209,411-421,296-299]

10. **AC-4.2.10: Web cancel wiring end-to-end.** A new `POST /cancel/<session_id>` sets a per-session `threading.Event`. Because `SessionManager.update()` REJECTS unknown fields AND `create()` never instantiates a defaulted `None`, the Event is a LIVE-from-creation field: `cancel_event: threading.Event = field(default_factory=threading.Event)` (NON-Optional — a defaulted `None` would `AttributeError` on `.set()`/`.is_set` the moment cancel is wired). A terminal `"cancelled"` status is added; `optimization_runner` binds `config.cancel_check = session.cancel_event.is_set` beside the `progress_callback` attach and emits a terminal `"cancelled"` SSE. In item 2 the SEARCH is in-process MinimalCalc, so cancel is served by the cooperative between-neighbor check (AC-4.2.9) within ~10ms; a worker is only in-flight during the ~1s FullCalc reporting windows, so `pool.cancel_inflight()` (kill checked-out worker → `_readline_with_timeout` EOF → `WorkerCrash`) is the pool's ONLY cross-thread entry: it MUST lock its in-flight bookkeeping (CLAUDE.md thread-safety) and hard-stop ONLY the actively-running session's worker (the pool is a module singleton shared across sessions; `optimization_lock` masks but does not remove the race). [Source: src/web/routes.py:242-260,262; src/web/optimization_runner.py:109-111; src/web/session_manager.py:42-49,59-78,85-111; src/calculator/driver_worker.py:193-236; CLAUDE.md]

11. **AC-4.2.11: TWO-TRACK — reporting on FullCalc, search on MinimalCalc.** The hill-climb SEARCH loop stays on `calculate_build_stats(engine="auto")` (MinimalCalc, UNCHANGED, ~10ms, within the 300s budget) as the argmax ranking oracle; `FullCalcEngine` computes ONLY the two REPORTED numbers — `baseline_report = calculate_build_stats(config.build, engine="full")` and `optimized_report = calculate_build_stats(best_build, engine="full")` — at the loop boundaries, and `improvement_pct` is FullCalc-over-FullCalc so both headline numbers share a scale (FullCalc ~23003 and MinimalCalc ~900 must NEVER meet inside one `max()` OR one ratio). **ATOMIC FALLBACK:** BOTH FullCalc reporting calls live in ONE `try/except`; on ANY failure BOTH downgrade to MinimalCalc together — never a FullCalc baseline against a MinimalCalc optimized (that mixed-scale pair yields a bogus ~−96% headline). **SIGN DIVERGENCE (report truth, don't fabricate):** because the search maximizes the MinimalCalc metric, the MinimalCalc-chosen `best_build` is NOT guaranteed to improve the FullCalc metric — `improvement_pct` can legitimately be ≤ 0; report the true FullCalc numbers regardless (a Truth Engine must not invent a gain), and treat a non-positive FullCalc improvement as the expected signal that MinimalCalc search diverged, which item 4 (search on FullCalc) closes. Moving the SEARCH onto FullCalc is EXPLICITLY item 4. [Source: src/optimizer/hill_climbing.py:114-122,160,209-213,318-323,411-421; docs/pebo-master-plan.md:210-212]

12. **AC-4.2.12 (hard constraint): scope fence (mirrors AC-4.1.10).** 4.2 does NOT build: the tree 0_3→0_4 bump / startup version assert / weapon-set+dual-ascendancy acceptance (item 3); the `EVAL_NEIGHBORS`/`APPLY_MOVE` batch or optimizer search rewire (item 4 — the `driver.lua` stubs at :392-397 STAY stubs; `driver.lua` is FROZEN); MVP config (item 5); parity v2 / mass baselines / `trust_tiers.json` / `release_gate.py` (item 6); the round-trip release gate (item 7); MinimalCalc retirement / `subprocess_calculator.py` rename (item 8). The FR-1.6 unsupported-build gate is the sibling pre-filed story `4-9-retire-unsupported-build-gate`, NOT 4.2. [Source: docs/pebo-master-plan.md:203-224; src/calculator/driver.lua:390-397; docs/sprint-status.yaml:106]

13. **AC-4.2.13 (hard constraint): test discipline split by whether LuaJIT boots.** UNMARKED/fast pure-Python tests (fake worker + monkeypatched `calculate_build_stats`) carry pool mechanics, protocol-hardening (a/d/e), and the cancel contract; `gui_parity`+`slow` tests under `pytest -n 1` carry crash-survival (kill worker mid-calc → `WorkerCrash` → pool respawns → next calc OK), the 2-worker pool e2e, and the `FullCalcEngine` seam parity (deadeye `23003.185361227` ±0.1%); the `luajit.exe` lane is a MODULE-LEVEL skip-gated test on `POB_LUAJIT_EXE` (binary still unstaged per 4.1). NO new pytest markers (`--strict-markers`); guarded markers inherit the `pob_env` autouse guard, so unmarked mechanics tests must NOT touch a drifted tree. `setup_pob.py` MUST exit 0 before close. [Source: tests/conftest.py:28-62; tests/integration/test_driver_parity.py; CLAUDE.md; docs/stories/4-1-truth-engine-driver-spike.md:238]

14. **AC-4.2.14: ADR housekeeping.** Ratify ADR-005 (driver) and ADR-006 (worker-pool process isolation + protocol + lane) and ADR-007 (XML-direct via PassiveSpec) `Proposed → Accepted` at item 2 (the pool is BUILT and test-pinned here); FOLD cooperative-cancel into ADR-006 and rewrite its "Ratify at Epic 4 item 4" / "cancel + EVAL_NEIGHBORS batch are item 2/4" lines to "pool ratified at item 2; the `EVAL_NEIGHBORS` batch CONSUMER is item 4"; ADD to ADR-007 a consequence documenting the mutated-`BuildData` → patched-XML seam (in-worker node-delta `APPLY_MOVE` deferred to item 4). ADR-008 (tree bump) STAYS `Proposed` (item 3). Keep the `luajit.exe` lane documented as "coded-and-ready, binary-unstaged, skip-gated". [Source: docs/decisions/ADR-005-truth-engine-driver-lua.md; docs/decisions/ADR-006-worker-pool-process-isolation.md:3-4,48; docs/decisions/ADR-007-xml-direct-passivespec-convert.md; docs/decisions/ADR-008-tree-version-bump-and-assert.md]

## Tasks / Subtasks

- [ ] **T1: `FullCalcEngine` + the `engine=` selector** (AC: 4.2.1, 4.2.2)
  - [ ] Create `src/calculator/full_calc_engine.py`: `FullCalcEngine` class + module-singleton `get_full_calc_engine()`; `calculate(build)` serializes via `patch_passive_nodes_to_xml` (T4) → `with pool.acquire() as w:` → `w.load_build(xml)` + `w.get_stats()` → maps to `BuildStats` via a `_stats_from_mainoutput()` ported from `full_pob_engine.py:257-306` with the first-nonzero DPS fallback. Read the JSON dict via dict-safe `.get(key, default)` (GET_STATS omits absent keys) and KEEP the `int(...)` casts so `BuildStats.__post_init__` doesn't reject the row.
  - [ ] Add the keyword-only `engine="auto"|"full"` selector to `calculate_build_stats` (`build_calculator.py:98`), routing `"full"` to `FullCalcEngine` when `build.source_xml` is present; leave the `"auto"` path (`:154-221`) byte-identical. `resolve_main_socket_group` stays on the default engine (it drives the MinimalCalc search). [Source: src/calculator/build_calculator.py:98,240-303]

- [ ] **T2: `WorkerPool` over `DriverWorker`** (AC: 4.2.3, 4.2.4, 4.2.5)
  - [ ] Create `src/calculator/worker_pool.py`: `WorkerPool(size=2)`, lazy spawn, bounded-`queue.Queue` `acquire()`/`release()` context manager, pool-owned health-check (`is_alive` + `PING`) + respawn-before-handout, bounded `_respawn_budget` failing with `stderr_tail`, benign-teardown-SEH exclusion (`_shutting_down`), `cancel_inflight()`, memory-cap recycle via `memory_mb()`.
  - [ ] One-retry-then-`CalculationError` on a mid-calc crash; NEVER a sentinel `BuildStats`. [Source: src/calculator/driver_worker.py:316,322-344,355-384]

- [ ] **T3: Close the 4.1 hardening cluster in `driver_worker.py`** (AC: 4.2.6)
  - [ ] (a) guard `json.loads` at `:286`; (b) add `_die()` and route all `WorkerCrash` raises (`:279-285`) through it to close pipes; (c) default per-worker `stderr` capture (`:136,:168-172,:346-353`); (d) raise in `get_stats` on `{ok:false}` (`:294-296`); (e) `cmd`-last payload merge in `eval_neighbors`/`apply_move` (`:298-302`).
  - [ ] (g) harden `scripts/triage_m0_builds.py` with a per-build `try/except`.

- [ ] **T4: `patch_passive_nodes_to_xml` + `source_xml` on `BuildData`** (AC: 4.2.7, 4.2.8)
  - [ ] Extract `patch_passive_nodes_to_xml(source_xml, nodes, main_socket_group)` from `encode_pob_code` (`pob_parser.py:156-260`), returning `patched_xml` (`:252`) before compress/base64 (`:259`); ADD `Build @mainSocketGroup` patching (**G2**); refactor `encode_pob_code` to call the primitive.
  - [ ] Add `source_xml: Optional[str] = None` to `src/models/build_data.py` (`:44-66`) and populate it in `parse_pob_code` from `xml_str` (`:74`).
  - [ ] FENCE FullCalc reporting to single-`<Spec>` builds AND detect multi-`<Spec>` explicitly (parser stamps a `BuildData.is_multi_spec` flag, or the engine checks for a list-typed `Tree>Spec`). G3: for a multi-`<Spec>` build `_extract_passive_nodes` returns an EMPTY set (`:391-393`), so the patch would write `@nodes=""` and FullCalc would report an UNALLOCATED tree — garbage presented as authoritative; the fence is MANDATORY, not optional. The read-side `activeSpec` fix is item 3. [Source: src/parsers/pob_parser.py:234-236,378,391-393]

- [ ] **T5: Cooperative cancel in the optimizer** (AC: 4.2.9)
  - [ ] Add `cancel_check` to `src/models/optimization_config.py` (`:65`, beside `progress_callback`, no validation).
  - [ ] In `hill_climbing.py`: add the cancel check at `:167-173`; thread `cancel_check` into `_evaluate_neighbors` (call at `:209`) with a per-neighbor check at `:411`; add `convergence_reason="cancelled"` returning best-so-far (respect the `else: max_iterations` terminal at `:296-299`).

- [ ] **T6: Web cancel wiring** (AC: 4.2.10)
  - [ ] `src/web/session_manager.py`: add a `cancel_event` field to `OptimizationSession` (`:42-49`) and a `"cancelling"`/`"cancelled"` status (`update()` enforces real fields — `:106-108`).
  - [ ] `src/web/optimization_runner.py`: bind `config.cancel_check = event.is_set` at `:109-111`; emit a terminal `"cancelled"` SSE (distinct from `error`).
  - [ ] `src/web/routes.py`: add `POST /cancel/<session_id>` (near the other `app.route` defs, `:262`); on the web request path `build.source_xml` is populated for free because `parse_pob_code` (`:186`) sets it. [Source: src/web/routes.py:184-260]

- [ ] **T7: Wire the two-track reporting** (AC: 4.2.11)
  - [ ] Keep the SEARCH loop on `calculate_build_stats(engine="auto")` (`hill_climbing.py:413`, unchanged); do NOT reassign the search's `baseline_stats`/`best_stats` LOCALS (they feed convergence at `:160`).
  - [ ] After the loop, inside ONE `try/except`, compute `baseline_report = calculate_build_stats(config.build, engine="full")` and `optimized_report = calculate_build_stats(best_build, engine="full")`; write all THREE result fields TOGETHER — `OptimizationResult.baseline_stats`, `optimized_stats`, and `improvement_pct` (`:319,:328-329`) — from these two numbers. On ANY exception, downgrade BOTH to MinimalCalc reporting together (never a mixed-scale pair). [Source: src/optimizer/hill_climbing.py:114-122,160,318-339]

- [ ] **T8: Tests** (AC: 4.2.13)
  - [ ] Fast/unmarked: `tests/unit/calculator/test_worker_pool_mechanics.py`, `tests/unit/optimizer/test_cooperative_cancel.py` (fake worker / monkeypatched calc).
  - [ ] `gui_parity`+`slow`, `-n 1`: `tests/integration/test_driver_worker_crash_survival.py`, `test_driver_worker_pool.py`, `test_full_calc_engine.py` (deadeye `23003.185361227` ±0.1% through the seam).
  - [ ] `tests/integration/test_driver_luajit_lane.py` — module-level skip-gated on `POB_LUAJIT_EXE`.

- [ ] **T9: ADRs + sprint-status** (AC: 4.2.14)
  - [ ] Ratify ADR-005/006/007 `Proposed → Accepted`; fold cooperative-cancel into ADR-006; add the mutated-`BuildData` → patched-XML consequence to ADR-007; leave ADR-008 `Proposed`.
  - [ ] Set `4-2-fullcalcengine-worker-pool-cooperative-cancel: in-progress` under the epic-4 block in `docs/sprint-status.yaml:106-107` at dev start.

- [ ] **T10: Close-out discipline** (AC: 4.2.12, 4.2.13)
  - [ ] Confirm `driver.lua` untouched (stubs at `:392-397` intact); `python scripts/setup_pob.py` exits 0; unit + `-n 1` integration green.

## Dev Notes

### Decisions taken at authoring (flag to flip before dev)

Three forks were resolved to the master-plan-consistent default. Each is reversible at story review:

1. **[D1 — per-neighbor speed] TWO-TRACK (search=MinimalCalc, reporting=FullCalc).** Chosen because a full `LOAD_BUILD` per neighbor (0.24–0.53s × 50–200) blows the 300s budget, and the plan explicitly assigns search-speed machinery (`EVAL_NEIGHBORS` batch, modKey caching, `useFullDPS=false`) to item 4. Item 2 ships GUI-correct HEADLINE numbers (the real user value) at +2 FullCalc calls/run; search QUALITY stays MinimalCalc-grade relative ordering until item 4. **Alternative (flip):** wholesale-swap the hot loop onto FullCalc behind `PEBO_FULLCALC_HOT_LOOP=false` for perf measurement — GUI-correct search but times out after ~3–5 iterations on heavy builds until item 4. [Source: docs/pebo-master-plan.md:210-212,326]
2. **[D2 — FR-1.6 story] Pre-file now as BLOCKED/backlog** (`4-9-retire-unsupported-build-gate`), NOT ready-for-dev and NOT built in 4.2. Retiring the gate before FullCalc actually ROUTES minion/totem builds in production would be strictly worse than the honest rejection. The epic-4 entry checklist already calls it a "pre-filed story". [Source: docs/sprint-status.yaml:106]
3. **[D3 — ADR-006 ratification] Ratify NOW at item 2** (the pool is built and test-pinned here), rewriting its "item 4" line; fold cancel in. **Alternative (flip):** leave `Proposed` until item 4. [Source: docs/decisions/ADR-006-worker-pool-process-isolation.md:3-4,48]

### The 4.1-deferred hardening cluster → production fixes (AC-4.2.6)

| # | Deferred symptom (4.1 review) | Current site | Production fix |
|---|---|---|---|
| a | `_send` unguarded `json.loads` throws bare | `driver_worker.py:286` | wrap → `WorkerCrash` |
| b | pipes leaked when `WorkerCrash` raised mid-protocol | raises at `:279-285`; only `stop()` closes (`:372-377`) | `_die()` closes pipes before every raise |
| c | blank `stderr_tail` (default `stderr_path=None`) | `:136,:346-353` | default per-worker stderr capture |
| d | `get_stats` returns raw `{ok:false}` envelope as "stats" | `:294-296` | RAISE instead |
| e | `EVAL_NEIGHBORS`/`APPLY_MOVE` payload can clobber `cmd` | `:298-302` | set `cmd` LAST (pre-hardens item 4; `driver.lua` handlers frozen → unexercised in item 2) |
| f | headline DPS needs `CombinedDPS`/`FullDPS`/`TotalDot` fallback | stats map (AC-4.2.2) | first-nonzero(`TotalDPS`,`CombinedDPS`,`FullDPS`,`TotalDot`) |
| g | triage aborts on one bad build | `scripts/triage_m0_builds.py` | per-build `try/except` |
| h | no crash-survival / luajit-lane test coverage | — | AC-4.2.13 tests |

### Key seams & gotchas

- **The interface the mandate names is the FREE FUNCTION `calculate_build_stats(build)`** — it receives ONLY a `BuildData`, so the source XML the worker needs must ride ON the `BuildData` (`source_xml`), NOT on `OptimizationConfiguration`; neighbors inherit it via `dataclasses.replace(build, passive_nodes=...)` for free. [Source: src/calculator/build_calculator.py:98; src/optimizer/hill_climbing.py:195]
- **G2 `@mainSocketGroup` is the subtlest correctness trap.** `@mainSocketGroup` is READ at `pob_parser.py:116` but NEVER WRITTEN by `encode_pob_code`; `resolve_main_socket_group` mutates `build.main_socket_group` in Python (`build_calculator.py:291`). The patch helper MUST write it, else the worker calcs a different skill than the Python search chose. Pin it with the deadeye seam-parity test.
- **Never let a sentinel into the argmax.** `_select_best_neighbor` uses `max(... key=_get_metric_value)` (`hill_climbing.py:453`) — a crash returning `BuildStats(total_dps=0)` would silently lose (fine) but a crash returning a HUGE sentinel would win (catastrophic). Map crashes to `CalculationError` and let the existing `except: skip` drop the neighbor. [Source: src/optimizer/hill_climbing.py:411-419,449-461]
- **Cancel must be a `Callable`, cross-thread.** The Flask request thread SETS a `threading.Event`; the daemon optimizer thread READS `event.is_set`. A daemon thread cannot be force-killed, so cancel is cooperative-only; a wedged worker is hard-stopped by killing the process (`pool.cancel_inflight()` → `_readline_with_timeout` EOF → `WorkerCrash`). [Source: src/calculator/driver_worker.py:193-236; src/web/optimization_runner.py:76-90]
- **`SessionManager.update()` rejects unknown fields** (`:106-108`) — the cancel `Event` MUST be a declared field on `OptimizationSession`, not an ad-hoc attribute.
- **Multi-`<Spec>` fence (G3).** `_extract_passive_nodes` (`:378`, list-empty at `:391-393`) returns EMPTY for list-typed `<Spec>`; the read-side `activeSpec` fix is item 3. Fence FullCalc reporting to single-spec builds (raise/fall-back) until then — the WRITE side already handles `activeSpec` (`:234-236`), so `patch_passive_nodes_to_xml` won't CRASH on a multi-`<Spec>` build, but it would write `@nodes=""` and report an unallocated tree, so the fence is MANDATORY, not a nicety.
- **Windows discipline.** `pytest -n 1` for all integration/parity; teardown SEH `0xe24c4a02` after "N passed" is BENIGN (ADR-003) and MUST be excluded from the pool's respawn budget; `driver.lua` routes all `print` to stderr so stdout carries only JSON frames. [Source: src/calculator/driver.lua:84-97; CLAUDE.md]
- **`driver.lua` is FROZEN.** Do NOT implement `EVAL_NEIGHBORS`/`APPLY_MOVE` (stubs at `:392-397`) — that is item 4, and editing files under `external/pob-engine/` trips `pob_env.verify()` (but `driver.lua` is OUTSIDE the submodule; the freeze is about scope, not the guard). [Source: src/calculator/driver.lua:390-397]

### Project Structure Notes

- **New files:** `src/calculator/full_calc_engine.py`, `src/calculator/worker_pool.py`, tests under `tests/unit/calculator/`, `tests/unit/optimizer/`, `tests/integration/` (crash-survival, pool e2e, full-calc seam, luajit-lane).
- **Modified:** `src/calculator/build_calculator.py` (`engine=` selector), `src/calculator/driver_worker.py` (hardening a–e), `src/parsers/pob_parser.py` (extract helper + G2), `src/models/build_data.py` (`source_xml`), `src/models/optimization_config.py` (`cancel_check`), `src/optimizer/hill_climbing.py` (cancel + two-track), `src/web/{routes,optimization_runner,session_manager}.py` (cancel wiring), `scripts/triage_m0_builds.py` (g), ADR-005/006/007, `docs/sprint-status.yaml`.
- **NOT touched:** `src/calculator/driver.lua` (frozen; stubs stay), `MinimalCalc.lua` / `subprocess_calculator.py` (item 8), `passive_tree.py` 0_3 default (item 3), `external/pob-engine/**` and `external/POB_VERSION.txt` (generated).
- **Reuse (audit before lifting):** `full_pob_engine.py:257-306` (`_extract_stats` shape) for the `BuildStats` map; `driver_worker.py` `DriverWorker` verbatim as the pool's per-worker handle; `encode_pob_code` guts for the patch primitive; `pob_engine.py`/`stub_functions.py` only if the pool needs boot recipes (it should not — `DriverWorker` already boots).

### References

- [Source: docs/pebo-master-plan.md:200-202 — Epic 4 item-2 mandate (the story charter)]
- [Source: docs/pebo-master-plan.md:203-224 — items 3-8 scope fences]
- [Source: docs/pebo-master-plan.md:210-212,326 — item-4 search rewire + risk #4 latency/300s budget (two-track rationale)]
- [Source: docs/pebo-master-plan.md:323,331 — risk #1 SEH boot, risk #9 worker memory 200-400MB]
- [Source: docs/stories/4-1-truth-engine-driver-spike.md:242-266,299 — GO verdict, measurements, deferred hardening cluster]
- [Source: src/calculator/driver_worker.py:128-160,193-236,279-386 — DriverWorker lifecycle, bounded reads, WorkerCrash, stop/close]
- [Source: src/calculator/driver.lua:84-97,328-397 — stdout discipline, DEFAULT_STATS, LOAD_BUILD/GET_STATS, EVAL/APPLY stubs (frozen)]
- [Source: src/calculator/build_calculator.py:98,154-221,240-303 — calculate_build_stats hybrid + resolve_main_socket_group (mutates main_socket_group)]
- [Source: src/optimizer/hill_climbing.py:114-122,167-173,195,209-213,318-339,411-461 — baseline calc, timeout check, neighbor apply, eval loop, result packaging, selection]
- [Source: src/models/optimization_config.py:51-65,245-263 — config fields (cancel_check home) + OptimizationResult.to_dict fields]
- [Source: src/models/build_data.py:44-66 — BuildData fields (no source_xml today)]
- [Source: src/parsers/pob_parser.py:25,74,116,156,199,234-236,252,259,378 — decode xml_str, @mainSocketGroup read, encode_pob_code guts, activeSpec, _extract_passive_nodes]
- [Source: src/web/routes.py:184-260,262 — /optimize parse+session+thread; where /cancel slots]
- [Source: src/web/optimization_runner.py:76-90,109-114,158-168 — daemon worker, progress attach, lock, _fail]
- [Source: src/web/session_manager.py:22-49,85-111 — OptimizationSession fields, update() field-guard]
- [Source: src/calculator/full_pob_engine.py:257-306 — _extract_stats shape to port]
- [Source: tests/conftest.py:28-62 — pob_env autouse guard, _GUARDED_MARKERS]
- [Source: tests/integration/test_driver_parity.py — gui_parity harness template]
- [Source: docs/decisions/ADR-003-windows-luajit-cleanup-mitigation.md — teardown SEH benign]
- [Source: docs/decisions/ADR-006-worker-pool-process-isolation.md:3-4,22-24,48 — pool ADR to ratify + fold cancel]
- [Source: docs/decisions/ADR-007-xml-direct-passivespec-convert.md — XML-direct seam consequence to add]

## Dev Agent Record

### Context Reference

- Authored via BMAD `create-story` (ultimate context engine) with an ultracode multi-agent analysis+design workflow (5 verified-citation analyzers → 3-lens integration design panel → judge synthesis), 2026-07-03. Pulls Story 4.1's Dev Agent Record + the code-review-deferred hardening cluster + luajit-lane coverage.
- CLAUDE.md project constraints (thread-safety, `pytest -n 1`, ADR-003 teardown-SEH-benign, submodule read-only).

### Agent Model Used

claude-opus-4-8 (Claude Code, BMAD create-story workflow)

### Debug Log References

### Completion Notes List

### File List

## Change Log

**2026-07-03** — Story created via BMAD create-story (ultimate context engine + ultracode design panel)
- Drafted from docs/pebo-master-plan.md §6 Epic 4 item 2; scope-fenced against items 3-8; pulls 4.1 dev record + deferred hardening cluster (4-1-...:299).
- Design synthesized by a 3-lens panel (reuse-first spine + two-track reporting + crash-survival rigor); load-bearing citations (G2 @mainSocketGroup, source_xml, session field-guard, cancel seam) independently verified against source.
- Three authoring decisions baked in with flip-alternatives: [D1] two-track reporting, [D2] pre-file FR-1.6 as blocked, [D3] ratify ADR-006 now.
- Adversarial review pass (3 parallel reviewers: citation audit / scope+completeness / dev-readiness): citations 100% confirmed, zero scope creep, zero completeness gaps. Applied 10 seam-hardening fixes — atomic reporting fallback (AC-4.2.11), AC-4.2.5 crash-landing re-scope, `cancel_event` live-from-creation (AC-4.2.10), mandatory multi-`<Spec>` fence + detection (T4), dict-safe stats accessor (AC-4.2.2/T1), `cancel_inflight` thread-safety + single-session scope (AC-4.2.10), sign-divergence honesty (AC-4.2.11), T7 no-local-reassign, deferred-table (f) row, citation precision (neighbor_generator.py:169-172).
- Status: ready-for-dev
