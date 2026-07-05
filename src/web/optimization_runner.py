"""Optimizer worker plumbing for the web layer.

The Flask request thread NEVER runs the optimizer (LuaJIT is thread-local and
not thread-safe). Instead, :func:`run_optimization` executes in a dedicated
daemon worker thread that owns its own LuaJIT engine, guarded by the shared
:data:`optimization_lock` so only one run touches LuaJIT at a time.

Progress flows out over Server-Sent Events: :func:`make_progress_callback`
builds the 5-keyword-argument callback that PoB's ``ProgressTracker`` invokes,
translating its budget dict into the compact wire shape the browser expects.
"""

from __future__ import annotations

import gc
import logging

from src.web.app import session_manager, sse_manager, optimization_lock
from src.web.config import MAX_ITERATIONS
from src.optimizer.hill_climbing import optimize_build
from src.parsers.exceptions import (
    PoBParseError,
    InvalidFormatError,
    UnsupportedVersionError,
)
from src.calculator.exceptions import CalculationError, CalculationTimeout

logger = logging.getLogger(__name__)


def make_progress_callback(session_id: str):
    """Return the progress callback bound to ``session_id``.

    The returned callable matches the EXACT signature PoB's ``ProgressTracker``
    invokes -- five keyword arguments, never three positional:

        cb(iteration, best_metric, improvement_pct, budget_used, time_elapsed)

    where ``budget_used`` is a dict with keys ``unallocated_used``,
    ``unallocated_available``, ``respec_used`` and ``respec_available``. The
    callback maps that dict down to the ``{unallocated, respec}`` wire shape and
    pushes a ``progress`` SSE event.
    """

    def _callback(iteration, best_metric, improvement_pct, budget_used, time_elapsed):
        session = session_manager.get(session_id)
        max_iterations = (
            session.config.max_iterations
            if session is not None and session.config is not None
            else MAX_ITERATIONS
        )

        data = {
            "iteration": iteration,
            "max_iterations": max_iterations,
            "best_metric": best_metric,
            "improvement_pct": improvement_pct,
            "budget_used": {
                "unallocated": budget_used.get("unallocated_used", 0),
                "respec": budget_used.get("respec_used", 0),
            },
            "time_elapsed": time_elapsed,
        }

        # Persist the latest snapshot so a late-joining /progress client or a
        # /result poll still sees current state even if the SSE event is dropped
        # under queue backpressure.
        if session is not None:
            session_manager.update(session_id, progress=data)

        sse_manager.send(session_id, "progress", data)

    return _callback


def run_optimization(session_id: str) -> None:
    """Run one optimization for ``session_id`` inside a worker thread.

    Lifecycle:
        1. Mark the session ``running`` and attach the progress callback.
        2. Acquire the global optimizer lock (1s timeout). If another run holds
           it, emit an ``error`` event ('Optimizer busy') and return.
        3. Run :func:`optimize_build` (blocks up to ``max_time_seconds``).
        4. On success: store ``result.to_dict()`` + sorted optimized node ids on
           the session and emit a ``complete`` event with the to_dict payload.
        5. On parse/calc/value error: store the reason and emit an ``error``
           event.
        6. Always release the lock, drop the result, and run ``gc.collect()`` to
           reclaim the LuaJIT-heavy object graph promptly.
    """
    session = session_manager.get(session_id)
    if session is None:
        logger.error("run_optimization: unknown session_id %s", session_id)
        return

    config = session.config
    if config is None:
        logger.error("run_optimization: session %s has no config", session_id)
        session_manager.update(
            session_id, status="error", error="Internal error: missing optimization config"
        )
        sse_manager.send(
            session_id,
            "error",
            {"error_type": "internal_error", "reason": "Missing optimization config."},
        )
        return

    # Attach the SSE progress callback to the live config dataclass.
    config.progress_callback = make_progress_callback(session_id)
    # Story 4.2: bind the cooperative-cancel token. The Flask request thread sets
    # session.cancel_event via POST /cancel; the optimizer reads it as a Callable
    # (a daemon thread cannot be force-killed, so cancel is cooperative-only).
    config.cancel_check = session.cancel_event.is_set
    # set_status (not update): if a POST /cancel already moved this session to
    # 'cancelling' in the pending window, do NOT regress it to 'running' -- the
    # run will observe the sticky cancel_event and exit 'cancelled'.
    session_manager.set_status(session_id, "running")

    # Serialize optimize runs: only one LuaJIT optimization at a time.
    if not optimization_lock.acquire(timeout=1.0):
        logger.warning("run_optimization: optimizer busy, rejecting session %s", session_id)
        session_manager.update(session_id, status="error", error="Optimizer busy")
        sse_manager.send(
            session_id,
            "error",
            {
                "error_type": "optimizer_busy",
                "reason": "Optimizer busy: another optimization is already running. "
                "Please wait for it to finish and try again.",
            },
        )
        return

    result = None
    try:
        logger.info("run_optimization: starting optimize_build for session %s", session_id)
        result = optimize_build(config)

        payload = result.to_dict()
        optimized_nodes = sorted(result.optimized_build.passive_nodes)
        # Story 4.2: a cancelled run returns best-so-far under a DISTINCT terminal
        # status + SSE event (NOT "error"): the result is valid, just stopped early.
        cancelled = result.convergence_reason == "cancelled"
        terminal_status = "cancelled" if cancelled else "complete"
        session_manager.update(
            session_id,
            status=terminal_status,
            result=payload,
            optimized_nodes=optimized_nodes,
        )
        sse_manager.send(session_id, terminal_status, payload)
        logger.info(
            "run_optimization: session %s %s (%.2f%% improvement)",
            session_id,
            terminal_status,
            payload.get("improvement_pct", 0.0),
        )

    except (InvalidFormatError, UnsupportedVersionError, PoBParseError) as exc:
        _fail(session_id, "parse_error", str(exc))
    except (CalculationTimeout, CalculationError) as exc:
        _fail(session_id, "calculation_error", str(exc))
    except ValueError as exc:
        _fail(session_id, "invalid_configuration", str(exc))
    except Exception as exc:  # noqa: BLE001 - worker thread must never die silently
        logger.exception("run_optimization: unexpected failure for session %s", session_id)
        _fail(session_id, "optimization_error", f"Unexpected optimizer error: {exc}")

    finally:
        optimization_lock.release()
        del result
        gc.collect()


def _fail(session_id: str, error_type: str, reason: str) -> None:
    """Record a failure on the session and emit a terminal ``error`` event."""
    logger.warning("run_optimization: session %s failed (%s): %s", session_id, error_type, reason)
    session_manager.update(session_id, status="error", error=reason)
    sse_manager.send(session_id, "error", {"error_type": error_type, "reason": reason})
