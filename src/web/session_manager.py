"""In-memory store for optimization sessions.

A single :class:`SessionManager` holds one :class:`OptimizationSession` per
optimization run, keyed by a generated session id. All reads and writes are
guarded by one ``threading.Lock`` so the Flask request thread and the optimizer
worker thread can share the store safely.

The store is intentionally process-local and non-persistent: this is a
single-user desktop MVP, so sessions live only for the lifetime of the process.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Optional, Set

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids import at runtime
    from src.models.optimization_config import OptimizationConfiguration


@dataclass
class OptimizationSession:
    """State for a single optimization run.

    Fields:
        session_id: Unique id (uuid4 hex) assigned at creation.
        status: Lifecycle state, one of ``pending`` / ``running`` /
            ``complete`` / ``error`` / ``cancelling`` / ``cancelled``. Starts as
            ``pending``.
        config: The :class:`OptimizationConfiguration` driving the run. Held as
            the live dataclass instance (never a dict).
        original_code: The raw PoB import code the user submitted.
        result: ``OptimizationResult.to_dict()`` payload once finished, else
            ``None``.
        error: Human-readable error reason if the run failed, else ``None``.
        optimized_nodes: Final allocated passive node ids (``Set[int]``) once
            available, else ``None``.
        progress: Latest progress snapshot dict (iteration, best_metric, etc.).
        cancel_event: Story 4.2 cooperative-cancel token. LIVE from creation
            (NON-Optional, ``default_factory=threading.Event``) -- a defaulted
            ``None`` would ``AttributeError`` on ``.set()`` the moment ``POST
            /cancel`` fires, AND ``update()`` rejects unknown fields so it MUST be
            a declared field, not an ad-hoc attribute. The optimizer worker binds
            ``config.cancel_check = session.cancel_event.is_set``.
    """

    session_id: str = ""
    status: str = "pending"
    config: Optional["OptimizationConfiguration"] = None
    original_code: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None
    optimized_nodes: Optional[Set[int]] = None
    progress: dict = field(default_factory=dict)
    cancel_event: threading.Event = field(default_factory=threading.Event)


class SessionManager:
    """Thread-safe in-memory registry of :class:`OptimizationSession` objects."""

    def __init__(self) -> None:
        self._sessions: Dict[str, OptimizationSession] = {}
        self._lock = threading.Lock()

    def create(self, config, original_code: str) -> str:
        """Create a new session in ``pending`` state and return its id.

        Args:
            config: The OptimizationConfiguration for this run.
            original_code: The raw PoB import code submitted by the user.

        Returns:
            The newly generated session id (uuid4 hex).
        """
        session_id = uuid.uuid4().hex
        session = OptimizationSession(
            session_id=session_id,
            status="pending",
            config=config,
            original_code=original_code,
        )
        with self._lock:
            self._sessions[session_id] = session
        return session_id

    def get(self, session_id: str) -> Optional[OptimizationSession]:
        """Return the session for ``session_id``, or ``None`` if unknown."""
        with self._lock:
            return self._sessions.get(session_id)

    def update(self, session_id: str, **kwargs) -> Optional[OptimizationSession]:
        """Mutate fields on an existing session.

        Args:
            session_id: Id of the session to update.
            **kwargs: Field name -> new value. Each key must be a real field on
                :class:`OptimizationSession`.

        Returns:
            The updated session, or ``None`` if no such session exists.

        Raises:
            AttributeError: If a kwarg does not name a real session field
                (surfaces contract violations early rather than silently
                dropping the write).
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            for key, value in kwargs.items():
                if not hasattr(session, key):
                    raise AttributeError(
                        f"OptimizationSession has no field '{key}'"
                    )
                setattr(session, key, value)
            return session

    def set_status(self, session_id: str, new_status: str) -> Optional[str]:
        """Atomically transition a session's ``status`` under the store lock.

        Enforces the invariants a bare ``update(status=...)`` violates under
        concurrency (both the Flask request thread and the optimizer worker
        thread write ``status``):

          * a TERMINAL status (``complete``/``error``/``cancelled``) is never
            overwritten -- a late ``POST /cancel`` cannot revert a finished run
            to ``cancelling``;
          * ``cancelling`` is not clobbered back to ``running``/``pending`` -- a
            cancel landing in the pending window is not lost when the worker
            thread starts.

        Returns the resulting status, or ``None`` for an unknown session.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            current = session.status
            if current in ("complete", "error", "cancelled"):
                return current
            if current == "cancelling" and new_status in ("running", "pending"):
                return current
            session.status = new_status
            return session.status
