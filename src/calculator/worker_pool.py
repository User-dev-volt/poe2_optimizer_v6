"""Respawnable worker-process pool for the Truth Engine (Story 4.2 item 2).

Wraps N :class:`~src.calculator.driver_worker.DriverWorker` child processes (the
real PoB engine, one OS process each) behind a small pool API so a native SEH
fault (``0xe24c4a02``) in any worker is contained as a recoverable
:class:`WorkerCrash` and the pool respawns a fresh worker without taking down the
parent.

Design (AC-4.2.3/4/5):
  * **Module singleton** (:func:`get_worker_pool`) — one pool per process.
  * **Lazy spawn** — no worker boots until the first :meth:`acquire`, so
    MinimalCalc-only runs never pay the ~0.7s LuaJIT boot.
  * **Bounded idle queue** — ``queue.Queue(size)`` of idle workers; ``acquire``
    is a context manager with ``finally``-guaranteed release.
  * **Health-check + respawn-before-handout** — ``is_alive()`` + a cheap ``PING``
    before a worker is handed out; a dead worker is respawned first.
  * **Pool-owned, bounded respawn** — a respawn budget (max 5 / 60s) FAILS the
    run with the captured ``stderr_tail`` on a deterministic-SEH build instead of
    respawn-looping. A benign teardown SEH after ``SHUTDOWN`` (ADR-003) is
    EXCLUDED from the budget via ``_shutting_down``.
  * **One-retry-then-CalculationError; NEVER a sentinel** — a mid-calc
    :class:`WorkerCrash` is retried exactly once on a fresh worker; a still-failing
    crash raises :class:`CalculationError`. The pool never returns a zero/sentinel
    ``BuildStats`` — that guarantee is what makes the item-2 reporting fallback
    safe and is the forward-looking invariant for item 4 (search on FullCalc),
    where a large sentinel would win ``_select_best_neighbor``'s ``max()``.
  * **Process-based, NOT thread-local** — workers are OS processes and the run is
    single-threaded under ``optimization_lock``; ``build_calculator``'s
    ``threading.local()`` MinimalCalc/Subprocess engines are untouched.

``cancel_inflight()`` is the pool's ONLY cross-thread entry (the Flask request
thread calls it via ``POST /cancel``); it locks its in-flight bookkeeping and
hard-stops the checked-out worker so a wedged FullCalc reporting call unblocks.

[Source: src/calculator/driver_worker.py (DriverWorker lifecycle, WorkerCrash,
 ProtocolError); docs/decisions/ADR-006-worker-pool-process-isolation.md;
 docs/decisions/ADR-003-windows-luajit-cleanup-mitigation.md; docs/pebo-master-plan.md:331]
"""

from __future__ import annotations

import logging
import os
import queue
import threading
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional

from .driver_worker import DriverWorker, ProtocolError, WorkerCrash
from .exceptions import CalculationError

logger = logging.getLogger(__name__)

# Defaults tuned from ADR-006 measurements (worker RSS ~293MB; boot ~0.7s).
DEFAULT_POOL_SIZE = 2
_RESPAWN_MAX = 5            # respawns allowed within the window before failing
_RESPAWN_WINDOW_S = 60.0
# Recycle a worker whose RSS exceeds this many MB (risk #9: 200-400MB/worker,
# baseline ~293MB -- the cap only fires on a genuine leak, not steady state).
_DEFAULT_MEM_CAP_MB = 1200.0


def _default_worker_factory() -> DriverWorker:
    return DriverWorker(lane="embedded")


def _safe_stderr_tail(worker: Any) -> str:
    try:
        return worker._stderr_tail()
    except Exception:
        return ""


class WorkerPool:
    """A respawnable pool of ``size`` :class:`DriverWorker` child processes."""

    def __init__(
        self,
        size: Optional[int] = None,
        worker_factory: Callable[[], Any] = _default_worker_factory,
        acquire_timeout: float = 30.0,
        mem_cap_mb: Optional[float] = None,
    ) -> None:
        if size is None:
            try:
                size = int(os.environ.get("PEBO_WORKER_POOL_SIZE", DEFAULT_POOL_SIZE))
            except (TypeError, ValueError):
                size = DEFAULT_POOL_SIZE
        self.size = max(1, size)
        self._factory = worker_factory
        self._acquire_timeout = acquire_timeout
        if mem_cap_mb is None:
            try:
                mem_cap_mb = float(os.environ.get("PEBO_WORKER_MEM_CAP_MB", _DEFAULT_MEM_CAP_MB))
            except (TypeError, ValueError):
                mem_cap_mb = _DEFAULT_MEM_CAP_MB
        self._mem_cap_mb = mem_cap_mb

        self._idle: "queue.Queue[Any]" = queue.Queue(maxsize=self.size)
        self._all: List[Any] = []          # every worker handle the pool owns
        self._inflight: set = set()        # checked-out workers (cancel bookkeeping)
        self._respawns: List[float] = []   # monotonic timestamps of recent respawns
        self._lock = threading.Lock()
        self._spawned = False
        self._shutting_down = False

    # ----- lifecycle ----------------------------------------------------- #
    def _ensure_spawned(self) -> None:
        with self._lock:
            if self._spawned:
                return
            logger.info("WorkerPool: lazy-spawning %d worker(s)", self.size)
            for _ in range(self.size):
                w = self._factory()
                w.start()
                self._all.append(w)
                self._idle.put_nowait(w)
            self._spawned = True

    @contextmanager
    def acquire(self, timeout: Optional[float] = None):
        """Yield a HEALTHY worker; guarantee its release back to the idle pool.

        Health-checks (``is_alive`` + ``PING``) and respawns-if-dead BEFORE
        handing out. Raises :class:`CalculationError` on acquire timeout or a
        blown respawn budget.
        """
        self._ensure_spawned()
        timeout = self._acquire_timeout if timeout is None else timeout
        try:
            w = self._idle.get(timeout=timeout)
        except queue.Empty:
            raise CalculationError(
                f"WorkerPool.acquire timed out after {timeout:.1f}s (all "
                f"{self.size} workers busy)"
            )
        try:
            w = self._healthy_or_respawn(w)
        except BaseException:
            # Keep the pool population stable: put the (dead) handle back so a
            # later acquire re-heals it rather than shrinking the pool.
            self._idle.put(w)
            raise
        with self._lock:
            self._inflight.add(w)
        try:
            yield w
        finally:
            with self._lock:
                self._inflight.discard(w)
            self._recycle_if_oversized(w)
            self._idle.put(w)

    def _healthy_or_respawn(self, w: Any) -> Any:
        alive = False
        try:
            if w.is_alive():
                resp = w.ping()
                alive = bool(resp.get("ok") or resp.get("pong"))
        except WorkerCrash:
            alive = False
        if alive:
            return w
        return self._respawn(w)

    def _respawn(self, w: Any) -> Any:
        # A benign teardown SEH after SHUTDOWN (ADR-003) must NOT consume the
        # budget -- only real mid-run failures do.
        if not self._shutting_down:
            now = time.monotonic()
            with self._lock:
                self._respawns = [t for t in self._respawns if now - t < _RESPAWN_WINDOW_S]
                if len(self._respawns) >= _RESPAWN_MAX:
                    tail = _safe_stderr_tail(w)
                    raise CalculationError(
                        f"WorkerPool respawn budget exceeded "
                        f"({_RESPAWN_MAX} in {_RESPAWN_WINDOW_S:.0f}s) -- treating "
                        f"as a deterministic worker crash rather than respawn-looping."
                        + (f"\nLast worker stderr:\n{tail}" if tail else "")
                    )
                self._respawns.append(now)
        try:
            w.restart()
        except WorkerCrash as exc:
            raise CalculationError(
                f"WorkerPool respawn failed: {exc}"
            ) from exc
        return w

    def _recycle_if_oversized(self, w: Any) -> None:
        if self._shutting_down:
            return
        try:
            mb = w.memory_mb()
        except Exception:
            mb = None
        if mb is not None and mb > self._mem_cap_mb:
            logger.warning(
                "WorkerPool: recycling worker over memory cap (%.0fMB > %.0fMB)",
                mb, self._mem_cap_mb,
            )
            try:
                w.restart()  # if this crashes, next acquire's health check re-heals it
            except WorkerCrash:
                logger.warning("WorkerPool: memory-cap recycle restart crashed; "
                               "will re-heal on next acquire")

    # ----- high-level calc ----------------------------------------------- #
    def calculate(
        self,
        xml: str,
        name: str = "fullcalc",
        stats: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Load ``xml`` into a worker and return its ``GET_STATS`` dict.

        Exactly ONE automatic retry on a fresh worker for a mid-calc
        :class:`WorkerCrash`; a deterministic :class:`ProtocolError` (a live
        worker's ``{ok:false}``) is NOT retried. Never returns a sentinel dict --
        a persistent failure raises :class:`CalculationError`.
        """
        last_crash: Optional[WorkerCrash] = None
        for attempt in (1, 2):
            try:
                with self.acquire() as w:
                    load = w.load_build(xml, name)
                    if not load.get("ok"):
                        raise ProtocolError(f"LOAD_BUILD not ok: {load.get('error', load)}")
                    return w.get_stats(stats)  # ProtocolError on {ok:false}, WorkerCrash on death
            except WorkerCrash as exc:
                last_crash = exc
                logger.warning("FullCalc worker crash (attempt %d/2): %s", attempt, exc)
                continue  # retry once on a fresh worker (acquire respawns the dead one)
            except ProtocolError as exc:
                # A live worker returned a deterministic logical error -- retrying
                # the same input on another worker would fail identically.
                raise CalculationError(f"FullCalc protocol error: {exc}") from exc
        tail = getattr(last_crash, "stderr_tail", "") or ""
        raise CalculationError(
            f"FullCalc worker crashed on both attempts: {last_crash}"
            + (f"\nWorker stderr:\n{tail}" if tail else "")
        ) from last_crash

    # ----- cancel (cross-thread) ----------------------------------------- #
    def cancel_inflight(self) -> int:
        """Hard-stop every currently checked-out worker (cross-thread cancel).

        Kills the OS process so an in-flight ``get_stats`` read unblocks on EOF
        and raises :class:`WorkerCrash`. The pool is a module singleton shared
        across sessions, but ``optimization_lock`` serializes runs, so the
        in-flight set only ever holds the actively-running session's worker(s).
        Returns the number of workers signalled. Safe to call when nothing is in
        flight (a MinimalCalc-only run) -- it is then a no-op.
        """
        with self._lock:
            workers = list(self._inflight)
        for w in workers:
            try:
                w.kill()
            except Exception:
                logger.debug("cancel_inflight: kill failed", exc_info=True)
        if workers:
            logger.info("WorkerPool.cancel_inflight hard-stopped %d worker(s)", len(workers))
        return len(workers)

    # ----- measurement / teardown ---------------------------------------- #
    def memory_mb(self) -> Optional[float]:
        """Total RSS of all owned workers in MB, or ``None`` if none report."""
        with self._lock:
            workers = list(self._all)
        total, any_reported = 0.0, False
        for w in workers:
            try:
                mb = w.memory_mb()
            except Exception:
                mb = None
            if mb is not None:
                total += mb
                any_reported = True
        return total if any_reported else None

    def shutdown(self) -> None:
        """Shut down every worker (idempotent). Sets ``_shutting_down`` so a
        benign teardown SEH is excluded from the respawn budget."""
        self._shutting_down = True
        with self._lock:
            workers = list(self._all)
            self._all.clear()
            self._inflight.clear()
            self._spawned = False
        for w in workers:
            try:
                w.shutdown()
            except Exception:
                pass
        # Drain any handles still sitting in the idle queue.
        while True:
            try:
                self._idle.get_nowait()
            except queue.Empty:
                break
        self._shutting_down = False


# =========================================================================== #
# Module singleton
# =========================================================================== #
_pool_lock = threading.Lock()
_pool: Optional[WorkerPool] = None


def get_worker_pool() -> WorkerPool:
    """Return the process-wide :class:`WorkerPool` singleton (created on demand;
    workers do NOT spawn until the first :meth:`WorkerPool.acquire`)."""
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = WorkerPool()
        return _pool


def reset_worker_pool_for_tests() -> None:
    """Shut down and clear the module singleton (test isolation only)."""
    global _pool
    with _pool_lock:
        if _pool is not None:
            try:
                _pool.shutdown()
            except Exception:
                pass
        _pool = None
