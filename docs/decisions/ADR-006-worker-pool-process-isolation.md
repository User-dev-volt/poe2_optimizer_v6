# ADR-006: Truth Engine worker — process isolation + JSON command protocol + lane choice

## Status
Accepted (Epic 4 item 2, Story 4.2, 2026-07-03). The respawnable 2-worker pool
is BUILT (`src/calculator/worker_pool.py`, module singleton) and test-pinned
(`tests/unit/calculator/test_worker_pool_mechanics.py` +
`tests/integration/test_driver_worker_pool.py` +
`test_driver_worker_crash_survival.py`). Cooperative cancel is FOLDED IN here (it
ships alongside the pool at item 2). The pool ratified at item 2; the
`EVAL_NEIGHBORS` batch CONSUMER (fanning `_evaluate_neighbors` across both
workers) is item 4 — no pool-API change required.

## Context

LuaJIT is not thread-safe (CLAUDE.md), and the embedded engine can raise a
native SEH `0xe24c4a02`. The optimizer needs many calculations per second across
neighbour evaluations, and a crash in one calc must not take down the parent.

Story 4.1 built and proved a **respawnable worker-process host**
(`src/calculator/driver_worker.py`, `DriverWorker`):

- **Isolation:** the worker is a separate OS **process** (not a thread). A child
  SEH surfaces to the parent as EOF → `WorkerCrash`; the parent survives and can
  `restart()` (proven — respawn yields a fresh pid, PING ok).
- **Protocol:** line-delimited JSON over stdin/stdout. `LOAD_BUILD`, `GET_STATS`,
  `PING`, `GC`, `SHUTDOWN` are live; `EVAL_NEIGHBORS` / `APPLY_MOVE` are wired,
  reachable STUBS (the optimizer rewire is Epic 4 item 2/4). `print` is routed to
  stderr so stdout carries only protocol frames.
- **Measurements (feed pool sizing):** boot ≈0.7s (embedded); worker RSS ≈**293MB**
  (Lua heap ≈128–171MB) — within risk-#9's 200–400MB envelope; cold first-build
  load ≈0.9s, warm loads 0.24–0.53s, `GET_STATS` ~0.15ms.

### Lane decision (AC-4.1.4, pre-committed go/no-go)

Two lanes were pre-committed, running the SAME `driver.lua`:
(a) **embedded** `lupa.luajit21` inside the worker, and
(b) **`luajit.exe` subprocess** fallback (`Driver.serve()` Lua loop).

## Decision

Adopt lane **(a) embedded-Lupa** as the primary Truth-Engine lane: it boots with
no boot-time SEH and hits ±0.000% parity, so the fallback is not required for
correctness. Keep lane (b) as a coded-and-ready safety net (`lane="luajit"`);
its shared protocol code (`Driver.handle_command`) is already proven by the
embedded lane. Epic 4 sizes a small (~2) respawnable worker pool from the
memory/latency numbers above.

### Pool shape (built at item 2)

`WorkerPool(size=2, PEBO_WORKER_POOL_SIZE override)` — module singleton, LAZY
spawn (no LuaJIT boot on MinimalCalc-only runs), bounded `queue.Queue` of idle
workers, `with pool.acquire()` context manager that HEALTH-CHECKS (`is_alive` +
`PING`) and respawns-if-dead BEFORE handout with `finally`-guaranteed release. The
pool OWNS respawn: a bounded budget (5 / 60s) FAILS the run with the captured
`stderr_tail` rather than respawn-looping on a deterministic-SEH build; a benign
teardown SEH after `SHUTDOWN` (ADR-003, `0xe24c4a02`) is excluded via a
`_shutting_down` flag. A mid-calc `WorkerCrash` maps to `CalculationError` after
exactly ONE retry on a fresh worker; the pool NEVER returns a zero/sentinel
`BuildStats` (the invariant that makes the item-2 reporting fallback safe AND
stops a crash-sentinel from winning `_select_best_neighbor`'s `max()` once item 4
moves the SEARCH onto FullCalc). The pool is PROCESS-based, NOT thread-local, so
`build_calculator`'s `threading.local()` MinimalCalc/Subprocess engines are
untouched.

### Cooperative cancel (folded in at item 2)

`OptimizationConfiguration.cancel_check: Optional[Callable[[], bool]]` is checked
at the top of the hill-climb loop and per-neighbor inside `_evaluate_neighbors`;
cancellation returns best-so-far under `convergence_reason="cancelled"`. The web
layer binds it to a per-session `threading.Event.is_set` (`POST /cancel/<id>`). A
`Callable` (not a bare bool) is required because the daemon optimizer thread
cannot be force-killed — cooperative is the only safe cancel. `pool.cancel_inflight()`
is the pool's ONLY cross-thread entry: it locks its in-flight bookkeeping and
hard-stops the checked-out worker (kill → `_readline_with_timeout` EOF →
`WorkerCrash`) so a wedged ~1s FullCalc reporting call unblocks; during the
MinimalCalc search no worker is in flight, so the cooperative between-neighbor
check serves cancel within ~10ms.

## Consequences / open items

- The `luajit.exe` binary was **not staged in the spike** (none vendored; this
  environment has no C compiler to build a byte-matching LuaJIT 2.1). This is the
  one AC-4.1.5 item left open — **de-risked** because the embedded lane works.
  Epic 4 stages the binary only if a fallback is ever needed (bounded: MSVC +
  LuaJIT source at lupa's revision).
- Cooperative cancel LANDED at item 2 (folded in above). The `EVAL_NEIGHBORS`
  batch CONSUMER is Epic 4 item 4 — it fans `_evaluate_neighbors` across both
  workers with no pool-API change; `driver.lua`'s `EVAL_NEIGHBORS`/`APPLY_MOVE`
  handlers stay frozen stubs until then.

[Source: docs/stories/4-1-truth-engine-driver-spike.md (Tasks 4/6/7);
 src/calculator/driver_worker.py; docs/pebo-master-plan.md:323,331 (risks #1/#9)]
