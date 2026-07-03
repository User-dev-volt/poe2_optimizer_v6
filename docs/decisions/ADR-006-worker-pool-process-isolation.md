# ADR-006: Truth Engine worker — process isolation + JSON command protocol + lane choice

## Status
Proposed (Epic 4) — STUB drafted from the Story 4.1 spike. Ratify at Epic 4 item 4.

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

## Consequences / open items

- The `luajit.exe` binary was **not staged in the spike** (none vendored; this
  environment has no C compiler to build a byte-matching LuaJIT 2.1). This is the
  one AC-4.1.5 item left open — **de-risked** because the embedded lane works.
  Epic 4 stages the binary only if a fallback is ever needed (bounded: MSVC +
  LuaJIT source at lupa's revision).
- Cooperative cancel + the `EVAL_NEIGHBORS` batch protocol are Epic 4 item 2/4.

[Source: docs/stories/4-1-truth-engine-driver-spike.md (Tasks 4/6/7);
 src/calculator/driver_worker.py; docs/pebo-master-plan.md:323,331 (risks #1/#9)]
