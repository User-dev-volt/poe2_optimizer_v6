"""Server-Sent Events (SSE) fan-out for optimization progress.

Each optimization session gets a bounded :class:`queue.Queue`. The optimizer
worker thread pushes events via :meth:`SSEManager.send`; the Flask SSE
generator drains them via the queue returned by :meth:`SSEManager.get_queue`.
The registry of queues is guarded by a ``threading.Lock``; the queues
themselves are already thread-safe, so queue operations run outside that lock.
"""

import queue
import threading
from typing import Any, Dict, Optional

# Per-session event buffer size. Bounded so a slow/disconnected browser cannot
# grow memory without limit; progress events may be dropped under backpressure,
# but terminal events ('complete'/'error') are protected (see send()).
_MAX_QUEUE_SIZE = 100

# Event types that must never be silently dropped.
_TERMINAL_EVENTS = ("complete", "error", "cancelled")


class SSEManager:
    """Thread-safe registry of per-session SSE event queues."""

    def __init__(self) -> None:
        self._streams: Dict[str, "queue.Queue[Dict[str, Any]]"] = {}
        self._lock = threading.Lock()

    def create_stream(self, session_id: str) -> "queue.Queue[Dict[str, Any]]":
        """Create (or replace) the event queue for ``session_id`` and return it."""
        q: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=_MAX_QUEUE_SIZE)
        with self._lock:
            self._streams[session_id] = q
        return q

    def send(self, session_id: str, event_type: str, data: Any) -> bool:
        """Enqueue an event for a session's SSE stream.

        Puts ``{'event': event_type, 'data': data}`` on the session queue.

        For terminal events ('complete'/'error'), if the queue is full one
        item is drained first so the terminal event is never the one dropped.
        Non-terminal events that hit a full queue are dropped (returns False).

        Returns:
            True if the event was enqueued, False if it was dropped or the
            session has no stream.
        """
        with self._lock:
            q = self._streams.get(session_id)
        if q is None:
            return False

        message = {"event": event_type, "data": data}
        try:
            q.put_nowait(message)
            return True
        except queue.Full:
            if event_type not in _TERMINAL_EVENTS:
                return False
            # Terminal event: make room by dropping one buffered item, then retry.
            try:
                q.get_nowait()
            except queue.Empty:
                pass
            try:
                q.put_nowait(message)
                return True
            except queue.Full:
                return False

    def get_queue(self, session_id: str) -> Optional["queue.Queue[Dict[str, Any]]"]:
        """Return the event queue for ``session_id``, or ``None`` if absent."""
        with self._lock:
            return self._streams.get(session_id)

    def close_stream(self, session_id: str) -> None:
        """Remove a session's stream and drain any buffered events."""
        with self._lock:
            q = self._streams.pop(session_id, None)
        if q is None:
            return
        try:
            while True:
                q.get_nowait()
        except queue.Empty:
            pass
