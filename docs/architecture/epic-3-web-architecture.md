# Epic 3: Flask Web Application Architecture

**Author:** Winston (Architect)
**Date:** November 1, 2025
**Epic:** Epic 3 - User Experience & Local Reliability
**Status:** Final Design
**Version:** 1.0

---

## Executive Summary

Epic 3 delivers a Flask-based web application that transforms the Epic 2 optimization engine into a polished, user-facing tool. This architecture addresses the three critical technical challenges identified in the Epic 002 retrospective:

1. **Thread Safety:** LuaRuntime is not thread-safe; Flask is multi-threaded by default
2. **Real-Time Progress:** SSE integration for live optimization updates without page refresh
3. **Resource Management:** Prevent memory leaks across 50+ consecutive optimizations

**Key Architectural Decisions:**
- **Request locking** for LuaRuntime thread safety (simpler than session isolation for single-user local MVP)
- **Server-Sent Events (SSE)** for real-time progress streaming (superior to AJAX polling for continuous updates)
- **In-memory session state** with unique session IDs (cleaner for background task coordination)
- **Explicit resource cleanup** after each optimization (prevent memory leaks)

**Architectural Principles:**
- **Simplicity over sophistication** - This is a local single-user MVP, not a production multi-tenant service
- **Boring technology wins** - Flask + SSE are proven, well-documented patterns
- **Defensive programming** - Assume LuaRuntime can fail; design for graceful degradation
- **User experience first** - Real-time progress and clear errors create confidence

---

## Table of Contents

1. [System Context](#system-context)
2. [Module Structure](#module-structure)
3. [Thread Safety Architecture](#thread-safety-architecture)
4. [SSE Progress Streaming](#sse-progress-streaming)
5. [Session State Management](#session-state-management)
6. [API Design](#api-design)
7. [Error Handling Strategy](#error-handling-strategy)
8. [Resource Cleanup](#resource-cleanup)
9. [Deployment & Configuration](#deployment--configuration)
10. [Testing Strategy](#testing-strategy)
11. [Risks & Mitigations](#risks--mitigations)

---

## System Context

### Epic 3 Position in System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER (Web Browser)                        │
│              http://localhost:5000                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTP + SSE
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  EPIC 3: Flask Web Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Routes     │  │     SSE      │  │   Session    │      │
│  │  (HTTP API)  │  │  Streaming   │  │    State     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                  ┌─────────▼─────────┐                      │
│                  │  Request Lock     │                      │
│                  │  (Thread Safety)  │                      │
│                  └─────────┬─────────┘                      │
└────────────────────────────┼──────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│              EPIC 2: Optimization Engine                      │
│         optimize_build(config) → OptimizationResult           │
└────────────────────────────┬──────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│              EPIC 1: PoB Calculation Engine                   │
│        calculate_build_stats(build) → BuildStats              │
│             (LuaRuntime - NOT thread-safe)                    │
└───────────────────────────────────────────────────────────────┘
```

### User Journey (Happy Path)

1. User navigates to `http://localhost:5000`
2. User pastes PoB code into textarea
3. System auto-detects unallocated points, user enters respec budget
4. User selects optimization metric (DPS/EHP/Balanced)
5. User clicks "Optimize"
6. **SSE stream opens** - Real-time progress updates every 100 iterations
7. Optimization completes - Results displayed (before/after comparison)
8. User exports optimized PoB code to clipboard
9. User imports code into PoB GUI to verify

### Dependencies on Epic 1 & Epic 2

**Epic 1 APIs (Calculation Layer):**
- `src/parser/pob_parser.py::parse_pob_code(code_str)` - Parse Base64 PoB codes
- `src/parser/pob_parser.py::encode_pob_code(build_data)` - Export optimized builds
- `src/calculator/calculator.py::calculate_build_stats(build)` - PoB calculations
- `src/calculator/passive_tree.py::PassiveTreeGraph` - Tree structure

**Epic 2 APIs (Optimization Layer):**
- `src/optimizer/hill_climbing.py::optimize_build(config)` - Main entry point
- `OptimizationConfiguration` - Input model
- `OptimizationResult` - Output model with before/after stats
- Progress callback signature from Story 2.8

**Critical Constraint:** LuaRuntime (used by Epic 1 calculator) is **NOT thread-safe**. Flask is multi-threaded by default. This is the primary architectural challenge for Epic 3.

---

## Module Structure

### Directory Layout

```
src/
├── web/                          # Epic 3: Flask application (NEW)
│   ├── __init__.py               # Flask app factory
│   ├── app.py                    # Main application entry point
│   ├── routes.py                 # HTTP endpoint handlers
│   ├── sse_manager.py            # Server-Sent Events coordination
│   ├── session_manager.py        # Session state tracking
│   ├── optimization_runner.py    # Background optimization executor
│   ├── thread_lock.py            # LuaRuntime thread safety
│   ├── templates/
│   │   └── index.html            # Main UI (single-page app)
│   └── static/
│       ├── css/
│       │   └── styles.css        # Application styles
│       ├── js/
│       │   ├── main.js           # UI interaction logic
│       │   └── sse_client.js     # SSE connection handler
│       └── images/
│           └── logo.png          # (optional)
│
├── optimizer/                    # Epic 2: Optimization engine (EXISTING)
│   ├── hill_climbing.py
│   ├── neighbor_generator.py
│   ├── metrics.py
│   └── ...
│
├── calculator/                   # Epic 1: PoB calculations (EXISTING)
│   ├── calculator.py
│   ├── passive_tree.py
│   └── ...
│
└── parser/                       # Epic 1: PoB code parsing (EXISTING)
    ├── pob_parser.py
    └── ...

main.py                           # Application entry point (runs Flask server)
config.yaml                       # Application configuration
```

### Module Responsibilities

| Module | Responsibility | Key APIs | Dependencies |
|--------|----------------|----------|--------------|
| `app.py` | Flask application initialization, config loading | `create_app()` | Flask, config.yaml |
| `routes.py` | HTTP endpoint handlers (GET /, POST /optimize, etc.) | `index()`, `optimize()`, `progress_stream()` | Flask, session_manager, optimization_runner |
| `sse_manager.py` | Coordinate SSE connections and message broadcasting | `SSEManager.send_progress()`, `SSEManager.close()` | threading.Queue |
| `session_manager.py` | Track optimization sessions (status, results, progress) | `SessionManager.create()`, `SessionManager.get()` | uuid, threading.Lock |
| `optimization_runner.py` | Execute optimization in background, invoke callbacks | `run_optimization(session_id, config)` | Epic 2 APIs, sse_manager |
| `thread_lock.py` | Global request lock for LuaRuntime thread safety | `optimization_lock` (threading.Lock) | threading.Lock |
| `templates/index.html` | Main UI template (form inputs, results display) | Jinja2 rendering | None |
| `static/js/sse_client.js` | Client-side SSE connection management | `connectSSE()`, event handlers | Browser EventSource API |

---

## Thread Safety Architecture

### Problem Statement

**Core Issue:** LuaRuntime (used by Epic 1's PoB calculation engine) is **not thread-safe**. Flask uses multi-threading by default (Werkzeug development server spawns thread per request).

**Failure Mode Without Mitigation:**
```
Thread 1: User A submits optimization → LuaRuntime executes
Thread 2: User B submits optimization → LuaRuntime executes (concurrent)
Result: Lua state corruption, crashes, incorrect calculations
```

### Solution: Request-Level Mutex

**Design Decision:** Implement a **global request lock** that ensures only one optimization runs at a time.

**Rationale:**
- **Simpler** than session-based LuaRuntime isolation (no per-session Lua state management)
- **Acceptable** for local single-user MVP (one user, sequential optimizations)
- **Proven pattern** for serializing access to non-thread-safe resources
- **Low overhead** - Lock acquisition is microseconds when uncontended

**Implementation:**

#### `src/web/thread_lock.py`
```python
"""
Global lock for LuaRuntime thread safety.
Ensures only one optimization runs at a time.
"""
import threading

# Global lock - shared across all requests
optimization_lock = threading.Lock()

def acquire_optimization_lock(timeout=1.0):
    """
    Acquire lock with timeout to prevent indefinite blocking.

    Args:
        timeout: Seconds to wait for lock (default: 1 second)

    Returns:
        bool: True if lock acquired, False if timeout
    """
    return optimization_lock.acquire(timeout=timeout)

def release_optimization_lock():
    """Release the optimization lock."""
    optimization_lock.release()
```

#### Usage in `optimization_runner.py`
```python
from src.web.thread_lock import acquire_optimization_lock, release_optimization_lock

def run_optimization(session_id: str, config: OptimizationConfiguration):
    """
    Execute optimization with thread safety.
    """
    # Try to acquire lock (1 second timeout)
    if not acquire_optimization_lock(timeout=1.0):
        # Lock held by another request - should never happen for single user
        # but defensive programming
        raise RuntimeError("Optimization already in progress. Please wait.")

    try:
        # Run optimization (Epic 2 API call)
        result = optimize_build(config)

        # Store result in session
        session_manager.update(session_id, status='completed', result=result)

    except Exception as e:
        # Store error in session
        session_manager.update(session_id, status='failed', error=str(e))
        raise

    finally:
        # CRITICAL: Always release lock, even on error
        release_optimization_lock()
```

### Alternative Considered: Session-Based LuaRuntime Isolation

**Approach:** Create one LuaRuntime instance per session, isolated in thread-local storage.

**Rejected Because:**
- **Complexity:** Requires managing LuaRuntime lifecycle (init, cleanup) per session
- **Memory overhead:** Each LuaRuntime instance ~45MB (from Epic 1)
- **Overkill:** Local single-user MVP doesn't need concurrent optimization support
- **Resource cleanup risk:** Harder to guarantee cleanup if session expires mid-optimization

**Future Consideration:** If multi-user concurrent optimization becomes a requirement (post-MVP), revisit session-based isolation.

### Concurrency Model

```
┌─────────────────────────────────────────────────────────┐
│  Request 1 (User submits optimization)                  │
│  ┌────────────────────────────────────────────┐         │
│  │ routes.py::optimize()                      │         │
│  │   └─> optimization_runner.run()            │         │
│  │        └─> acquire_lock()                  │  LOCK   │
│  │             └─> optimize_build() [Epic 2]  │ ACQUIRED│
│  │                  └─> calculate_stats()     │  HELD   │
│  │                       [Epic 1 LuaRuntime]  │         │
│  │                  └─> release_lock()        │ RELEASED│
│  └────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Request 2 (User requests progress via SSE)             │
│  ┌────────────────────────────────────────────┐         │
│  │ routes.py::progress_stream()               │         │
│  │   └─> sse_manager.stream(session_id)       │   NO    │
│  │        └─> session_manager.get_progress()  │  LOCK   │
│  │             [Read-only, no LuaRuntime]     │  NEEDED │
│  └────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

**Key Insight:** Only optimization execution needs the lock. Progress queries, result retrieval, and UI rendering are read-only operations on session state (thread-safe with session_manager's internal locks).

---

## SSE Progress Streaming

### Requirements (Story 3.5)

- Real-time progress updates **without page refresh**
- Updates every 100 iterations
- Display: iteration count, best metric, improvement %, budget used, time elapsed
- Cancel button to stop optimization early

### SSE vs AJAX Polling Comparison

| Criterion | SSE (Server-Sent Events) | AJAX Polling |
|-----------|-------------------------|--------------|
| **Latency** | Instant (server push) | Poll interval delay (500ms-2s) |
| **Efficiency** | Single persistent connection | N connections per minute |
| **Complexity** | Medium (EventSource API) | Low (XMLHttpRequest/fetch) |
| **Browser Support** | All modern browsers | Universal |
| **Use Case Fit** | Perfect for continuous updates | Better for occasional checks |

**Decision:** Use **Server-Sent Events (SSE)** - Superior for continuous progress streaming.

### SSE Architecture

#### Client-Side: EventSource API

**File:** `src/web/static/js/sse_client.js`
```javascript
/**
 * Connect to SSE stream for optimization progress updates.
 * @param {string} sessionId - Unique session identifier
 */
function connectSSE(sessionId) {
    const eventSource = new EventSource(`/progress/${sessionId}`);

    // Handle progress updates
    eventSource.addEventListener('progress', function(event) {
        const data = JSON.parse(event.data);
        updateProgressUI(data);  // Update UI elements
    });

    // Handle completion
    eventSource.addEventListener('complete', function(event) {
        const result = JSON.parse(event.data);
        displayResults(result);
        eventSource.close();  // Close connection
    });

    // Handle errors
    eventSource.addEventListener('error', function(event) {
        const error = JSON.parse(event.data);
        displayError(error);
        eventSource.close();
    });

    // Connection errors
    eventSource.onerror = function(err) {
        console.error('SSE connection error:', err);
        eventSource.close();
    };

    return eventSource;
}

function updateProgressUI(data) {
    document.getElementById('iteration-count').textContent =
        `Iteration ${data.iteration}/${data.max_iterations}`;
    document.getElementById('best-metric').textContent =
        `Best found: +${data.improvement_pct.toFixed(1)}% ${data.metric}`;
    document.getElementById('budget-used').textContent =
        `Budget: ${data.budget_used.unallocated}/${data.budget_total.unallocated} unallocated, ` +
        `${data.budget_used.respec}/${data.budget_total.respec} respec`;
    document.getElementById('time-elapsed').textContent =
        `Running for ${formatTime(data.time_elapsed)}`;

    // Update progress bar
    const progressPct = (data.iteration / data.max_iterations) * 100;
    document.getElementById('progress-bar').style.width = `${progressPct}%`;
}
```

#### Server-Side: SSE Manager

**File:** `src/web/sse_manager.py`
```python
"""
Server-Sent Events (SSE) manager for real-time progress streaming.
Coordinates message broadcasting to connected clients.
"""
import queue
import threading
from typing import Dict, Optional

class SSEManager:
    """Manages SSE connections and message broadcasting."""

    def __init__(self):
        # session_id -> queue.Queue mapping
        self._queues: Dict[str, queue.Queue] = {}
        self._lock = threading.Lock()

    def create_stream(self, session_id: str) -> queue.Queue:
        """
        Create a new SSE stream for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            queue.Queue for receiving SSE messages
        """
        with self._lock:
            if session_id in self._queues:
                # Close existing stream
                self.close_stream(session_id)

            # Create new queue for this session
            q = queue.Queue(maxsize=100)  # Limit buffering
            self._queues[session_id] = q
            return q

    def send_progress(self, session_id: str, event_type: str, data: dict):
        """
        Send SSE message to a session's stream.

        Args:
            session_id: Target session
            event_type: SSE event type ('progress', 'complete', 'error')
            data: Event data (will be JSON-serialized)
        """
        with self._lock:
            if session_id not in self._queues:
                return  # Stream closed or doesn't exist

            q = self._queues[session_id]

        try:
            # Non-blocking put (drop if queue full)
            q.put_nowait({'event': event_type, 'data': data})
        except queue.Full:
            # Queue full - drop oldest message and retry
            try:
                q.get_nowait()  # Discard oldest
                q.put_nowait({'event': event_type, 'data': data})
            except (queue.Empty, queue.Full):
                pass  # Give up if still can't insert

    def close_stream(self, session_id: str):
        """
        Close SSE stream for a session.

        Args:
            session_id: Session to close
        """
        with self._lock:
            if session_id in self._queues:
                del self._queues[session_id]

# Global SSE manager instance
sse_manager = SSEManager()
```

#### Server-Side: SSE Route Handler

**File:** `src/web/routes.py` (excerpt)
```python
import json
from flask import Response, stream_with_context
from src.web.sse_manager import sse_manager

@app.route('/progress/<session_id>')
def progress_stream(session_id):
    """
    SSE endpoint for streaming optimization progress.

    Args:
        session_id: Session identifier from /optimize response

    Returns:
        SSE stream (text/event-stream)
    """
    # Create SSE queue for this session
    q = sse_manager.create_stream(session_id)

    def event_stream():
        """Generator yielding SSE-formatted messages."""
        try:
            while True:
                # Block until message available (1 second timeout)
                try:
                    msg = q.get(timeout=1.0)
                except queue.Empty:
                    # Send keepalive comment (prevent connection timeout)
                    yield ': keepalive\n\n'
                    continue

                # Format as SSE message
                event_type = msg['event']
                data = json.dumps(msg['data'])

                yield f'event: {event_type}\n'
                yield f'data: {data}\n\n'

                # Close stream after 'complete' or 'error'
                if event_type in ('complete', 'error'):
                    break

        finally:
            # Cleanup: Close stream
            sse_manager.close_stream(session_id)

    # Return SSE response
    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )
```

#### Integration with Optimization Runner

**File:** `src/web/optimization_runner.py` (excerpt)
```python
from src.web.sse_manager import sse_manager

def create_progress_callback(session_id: str, config: OptimizationConfiguration):
    """
    Create progress callback that broadcasts via SSE.

    Args:
        session_id: Session receiving updates
        config: Optimization configuration (for max_iterations, budgets)

    Returns:
        Callable progress callback for Epic 2 optimize_build()
    """
    def progress_callback(iteration, best_metric, improvement_pct, budget_used, time_elapsed):
        """Called by Epic 2 every 100 iterations."""
        sse_manager.send_progress(session_id, 'progress', {
            'iteration': iteration,
            'max_iterations': config.max_iterations,
            'best_metric': best_metric,
            'improvement_pct': improvement_pct,
            'budget_used': {
                'unallocated': budget_used['unallocated_used'],
                'respec': budget_used['respec_used']
            },
            'budget_total': {
                'unallocated': config.unallocated_points,
                'respec': config.respec_points or 'Unlimited'
            },
            'time_elapsed': time_elapsed,
            'metric': config.metric.upper()
        })

    return progress_callback

def run_optimization(session_id: str, config: OptimizationConfiguration):
    """Execute optimization with SSE progress updates."""
    # Create progress callback
    callback = create_progress_callback(session_id, config)

    # Add callback to config
    config_with_callback = replace(config, progress_callback=callback)

    # Acquire lock and run
    if not acquire_optimization_lock(timeout=1.0):
        sse_manager.send_progress(session_id, 'error', {
            'error': 'Optimization already in progress'
        })
        return

    try:
        # Run optimization (Epic 2)
        result = optimize_build(config_with_callback)

        # Broadcast completion
        sse_manager.send_progress(session_id, 'complete', {
            'result': result.to_dict()  # Serialize OptimizationResult
        })

    except Exception as e:
        # Broadcast error
        sse_manager.send_progress(session_id, 'error', {
            'error': str(e),
            'error_type': type(e).__name__
        })

    finally:
        release_optimization_lock()
```

### SSE Sequence Diagram

```
User                 Browser              Flask Routes       SSE Manager    Optimization Runner
 |                      |                       |                  |                 |
 | Click "Optimize"     |                       |                  |                 |
 |--------------------->|                       |                  |                 |
 |                      | POST /optimize        |                  |                 |
 |                      |---------------------->|                  |                 |
 |                      |                       | create_session() |                 |
 |                      |                       |----------------->|                 |
 |                      |                       |  session_id      |                 |
 |                      |                       |<-----------------|                 |
 |                      |                       | spawn_thread()   |                 |
 |                      |                       |------------------------------------>|
 |                      |  200 {session_id}     |                  |                 |
 |                      |<----------------------|                  |                 |
 |                      |                       |                  |  optimize()     |
 |                      |                       |                  |  [BACKGROUND]   |
 |                      | EventSource connect   |                  |                 |
 |                      | /progress/{session}   |                  |                 |
 |                      |---------------------->|                  |                 |
 |                      |                       | create_stream()  |                 |
 |                      |                       |----------------->|                 |
 |                      |                       | [STREAMING]      |                 |
 |                      |                       |<================>|  send_progress()|
 |                      |  event: progress      |                  |<----------------|
 |                      |  data: {iteration:..} |                  |  [every 100]    |
 |                      |<----------------------|                  |                 |
 | Update UI            |                       |                  |                 |
 |<---------------------|                       |                  |                 |
 |                      |  event: progress      |                  |                 |
 |                      |  data: {iteration:..} |                  |                 |
 |                      |<----------------------|                  |                 |
 | Update UI            |                       |                  |                 |
 |<---------------------|                       |                  |  [Complete]     |
 |                      |                       |                  |  send_complete()|
 |                      |  event: complete      |                  |<----------------|
 |                      |  data: {result:...}   |                  |                 |
 |                      |<----------------------|                  |                 |
 |                      | [Close EventSource]   |                  |                 |
 | Display Results      |                       |                  |                 |
 |<---------------------|                       |                  |                 |
```

---

## Session State Management

### Requirements

- Track optimization status: 'pending', 'running', 'completed', 'failed'
- Store optimization results for retrieval
- Store progress data for SSE broadcasting
- Support session expiration/cleanup (prevent memory leaks)

### Session State Model

**File:** `src/web/session_manager.py`
```python
"""
Session state management for tracking optimization sessions.
Thread-safe in-memory storage with expiration.
"""
import uuid
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime, timedelta

@dataclass
class OptimizationSession:
    """Represents an optimization session."""
    session_id: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    created_at: datetime
    updated_at: datetime

    # Input
    config: Optional[dict] = None  # Serialized OptimizationConfiguration

    # Output
    result: Optional[dict] = None  # Serialized OptimizationResult
    error: Optional[str] = None

    # Progress tracking
    progress: dict = field(default_factory=dict)

class SessionManager:
    """
    Thread-safe session state manager.
    Manages in-memory sessions with automatic expiration.
    """

    def __init__(self, expiration_hours=24):
        self._sessions: Dict[str, OptimizationSession] = {}
        self._lock = threading.Lock()
        self._expiration_delta = timedelta(hours=expiration_hours)

    def create(self, config: dict) -> str:
        """
        Create new optimization session.

        Args:
            config: Serialized OptimizationConfiguration

        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        now = datetime.now()

        session = OptimizationSession(
            session_id=session_id,
            status='pending',
            created_at=now,
            updated_at=now,
            config=config
        )

        with self._lock:
            self._sessions[session_id] = session

        return session_id

    def get(self, session_id: str) -> Optional[OptimizationSession]:
        """
        Retrieve session by ID.

        Args:
            session_id: Session identifier

        Returns:
            OptimizationSession or None if not found
        """
        with self._lock:
            return self._sessions.get(session_id)

    def update(self, session_id: str, **kwargs):
        """
        Update session fields.

        Args:
            session_id: Session identifier
            **kwargs: Fields to update (status, result, error, progress)
        """
        with self._lock:
            if session_id not in self._sessions:
                return

            session = self._sessions[session_id]
            session.updated_at = datetime.now()

            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)

    def delete(self, session_id: str):
        """Delete session."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]

    def cleanup_expired(self):
        """
        Remove expired sessions (older than expiration_hours).
        Should be called periodically (e.g., every hour).
        """
        now = datetime.now()
        cutoff = now - self._expiration_delta

        with self._lock:
            expired = [
                sid for sid, session in self._sessions.items()
                if session.updated_at < cutoff
            ]

            for sid in expired:
                del self._sessions[sid]

        return len(expired)  # Return count for logging

# Global session manager instance
session_manager = SessionManager(expiration_hours=24)
```

### Session Cleanup Background Task

**File:** `src/web/app.py` (excerpt)
```python
import threading
import time
from src.web.session_manager import session_manager

def session_cleanup_worker():
    """Background thread to cleanup expired sessions."""
    while True:
        time.sleep(3600)  # Run every hour
        count = session_manager.cleanup_expired()
        if count > 0:
            print(f"[Session Cleanup] Removed {count} expired sessions")

# Start cleanup thread when app starts
cleanup_thread = threading.Thread(target=session_cleanup_worker, daemon=True)
cleanup_thread.start()
```

---

## API Design

### HTTP Endpoints

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|--------------|----------|
| GET | `/` | Serve main UI | None | HTML page |
| POST | `/optimize` | Submit optimization request | `{pob_code, metric, unallocated_points, respec_points}` | `{session_id}` |
| GET | `/progress/<session_id>` | SSE stream for progress | None | SSE stream |
| GET | `/result/<session_id>` | Retrieve optimization result | None | `{status, result, error}` |
| POST | `/cancel/<session_id>` | Cancel running optimization | None | `{success}` |
| GET | `/export/<session_id>` | Export optimized PoB code | None | `{pob_code}` |

### API Specification

#### POST /optimize

**Purpose:** Submit PoB code for optimization

**Request:**
```json
{
  "pob_code": "eNqdVt1u2zYU...",
  "metric": "dps",
  "unallocated_points": 15,
  "respec_points": 12
}
```

**Validation:**
- `pob_code`: Required, Base64 string, max 100KB
- `metric`: Required, one of ["dps", "ehp", "balanced"]
- `unallocated_points`: Required, non-negative integer
- `respec_points`: Optional, non-negative integer or null (unlimited)

**Response (Success):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

**Response (Error):**
```json
{
  "error": "Invalid PoB code format",
  "error_type": "ValidationError",
  "details": "Failed to decode Base64"
}
```

**Processing:**
1. Validate request parameters
2. Parse PoB code (Epic 1 parser)
3. Create session
4. Spawn background optimization thread
5. Return session_id immediately (don't block)

#### GET /progress/\<session_id\>

**Purpose:** Stream real-time optimization progress

**Response:** SSE stream (text/event-stream)

**Events:**

**Event: progress** (every 100 iterations)
```
event: progress
data: {"iteration": 300, "max_iterations": 600, "best_metric": 125432.5, "improvement_pct": 12.3, "budget_used": {...}, "time_elapsed": 85.2}
```

**Event: complete** (optimization finished)
```
event: complete
data: {"result": {...}}
```

**Event: error** (optimization failed)
```
event: error
data: {"error": "Calculation timeout", "error_type": "TimeoutError"}
```

#### GET /result/\<session_id\>

**Purpose:** Retrieve optimization result (alternative to SSE for clients that don't support EventSource)

**Response (Running):**
```json
{
  "status": "running",
  "progress": {
    "iteration": 300,
    "improvement_pct": 12.3
  }
}
```

**Response (Completed):**
```json
{
  "status": "completed",
  "result": {
    "baseline_stats": {...},
    "optimized_stats": {...},
    "improvement_pct": 15.7,
    "nodes_added": [123, 456, ...],
    "nodes_removed": [789],
    "budget_used": {...}
  }
}
```

**Response (Failed):**
```json
{
  "status": "failed",
  "error": "Build uses unsupported features",
  "error_type": "UnsupportedBuildError"
}
```

#### GET /export/\<session_id\>

**Purpose:** Export optimized build as PoB code

**Response:**
```json
{
  "pob_code": "eNqdVt1u2zYU...",
  "status": "success"
}
```

**Error (Session Not Found):**
```json
{
  "error": "Session not found or expired",
  "status": "error"
}
```

**Processing:**
1. Retrieve session
2. Check status == 'completed'
3. Get optimized BuildData from result
4. Encode as PoB code (Epic 1 encoder)
5. Return code

---

## Error Handling Strategy

### Error Categories (from Story 3.8)

1. **Input Validation Errors** - Invalid PoB code, bad parameters
2. **Unsupported Build Errors** - PoE 1 code, unique jewels, cluster jewels
3. **Calculation Errors** - LuaRuntime failures, PoB engine crashes
4. **Timeout Errors** - Optimization exceeds 5 minutes
5. **Resource Errors** - Memory exhaustion, lock acquisition timeout

### Structured Error Response Format

**Template:**
```json
{
  "error_type": "UnsupportedBuildError",
  "reason": "This build uses unsupported features",
  "details": "Cluster jewel sockets detected: [Socket 1, Socket 2]",
  "action": "Remove cluster jewels and try again, or use a PoE 2 build without unique mechanics",
  "session_id": "550e8400-..."
}
```

### Error Handling Implementation

**File:** `src/web/error_handler.py`
```python
"""
Structured error handling for Flask application.
"""
from flask import jsonify
from typing import Optional

class OptimizerError(Exception):
    """Base exception for optimizer errors."""
    def __init__(self, reason: str, details: Optional[str] = None, action: Optional[str] = None):
        self.reason = reason
        self.details = details
        self.action = action
        super().__init__(reason)

class ValidationError(OptimizerError):
    """Input validation failed."""
    pass

class UnsupportedBuildError(OptimizerError):
    """Build uses unsupported features."""
    pass

class CalculationError(OptimizerError):
    """PoB calculation failed."""
    pass

class TimeoutError(OptimizerError):
    """Optimization exceeded timeout."""
    pass

def format_error_response(error: Exception, session_id: Optional[str] = None) -> dict:
    """
    Format exception as structured error response.

    Args:
        error: Exception instance
        session_id: Associated session (if any)

    Returns:
        dict: Error response matching template
    """
    if isinstance(error, OptimizerError):
        return {
            'error_type': type(error).__name__,
            'reason': error.reason,
            'details': error.details,
            'action': error.action,
            'session_id': session_id
        }
    else:
        # Generic error
        return {
            'error_type': type(error).__name__,
            'reason': str(error),
            'details': None,
            'action': 'Please try again or contact support if the issue persists',
            'session_id': session_id
        }

def register_error_handlers(app):
    """Register Flask error handlers."""

    @app.errorhandler(OptimizerError)
    def handle_optimizer_error(error):
        response = format_error_response(error)
        return jsonify(response), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({
            'error_type': 'NotFoundError',
            'reason': 'Endpoint not found',
            'action': 'Check the API documentation'
        }), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        # Log full stack trace server-side
        app.logger.error(f'Internal error: {error}', exc_info=True)

        # Return generic error to client
        return jsonify({
            'error_type': 'InternalError',
            'reason': 'An unexpected error occurred',
            'action': 'Please try again. If the issue persists, check logs/optimizer.log'
        }), 500
```

### Error Propagation Pattern

**Route Handler:**
```python
@app.route('/optimize', methods=['POST'])
def optimize():
    try:
        # Validate input
        data = request.get_json()
        pob_code = data.get('pob_code')

        if not pob_code:
            raise ValidationError(
                reason='Missing required parameter',
                details='pob_code is required',
                action='Include pob_code in request body'
            )

        # Parse PoB code
        try:
            build = parse_pob_code(pob_code)
        except Exception as e:
            raise ValidationError(
                reason='Invalid PoB code format',
                details=str(e),
                action='Verify your PoB code is valid by importing it into Path of Building'
            )

        # Check for unsupported features
        if has_cluster_jewels(build):
            raise UnsupportedBuildError(
                reason='This build uses unsupported features',
                details='Cluster jewel sockets detected',
                action='Remove cluster jewels and try again'
            )

        # Create session and spawn optimization
        session_id = session_manager.create(config)
        spawn_optimization(session_id, config)

        return jsonify({'session_id': session_id, 'status': 'pending'}), 200

    except OptimizerError:
        raise  # Let error handler catch
    except Exception as e:
        # Unexpected error - log and wrap
        app.logger.error(f'Unexpected error in /optimize: {e}', exc_info=True)
        raise OptimizerError(
            reason='An unexpected error occurred during optimization',
            details=str(e)
        )
```

---

## Resource Cleanup

### Problem: Memory Leaks (Story 3.10)

**Requirement:** Run 50+ consecutive optimizations without memory growth.

**Sources of Memory Leaks:**
1. **LuaRuntime state** - Lua objects not garbage collected
2. **Session state** - Old sessions accumulating in memory
3. **SSE queues** - Abandoned connections holding message buffers
4. **Python circular references** - BuildData/OptimizationResult cross-references

### Cleanup Strategy

#### 1. Explicit LuaRuntime Cleanup

**Problem:** Epic 1's LuaRuntime may accumulate state across calculations.

**Solution:** Invoke cleanup after each optimization.

**File:** `src/calculator/calculator.py` (Epic 1 enhancement)
```python
def cleanup_lua_runtime():
    """
    Clean up Lua runtime state to prevent memory leaks.
    Called after each optimization completes.
    """
    global _lua_runtime

    if _lua_runtime is not None:
        # Collect Lua garbage
        _lua_runtime.eval('collectgarbage("collect")')

        # Optional: Recreate runtime if memory still high
        # (Trade performance for guaranteed cleanup)
        # del _lua_runtime
        # _lua_runtime = None
```

**Usage in optimization_runner.py:**
```python
def run_optimization(session_id, config):
    try:
        result = optimize_build(config)
        session_manager.update(session_id, status='completed', result=result)
    finally:
        # CRITICAL: Cleanup Lua state
        cleanup_lua_runtime()
        release_optimization_lock()
```

#### 2. Session Expiration

Already addressed in Session Manager (cleanup_expired every hour).

#### 3. SSE Queue Cleanup

**File:** `src/web/sse_manager.py` (enhanced)
```python
def close_stream(self, session_id: str):
    """Close SSE stream and free queue memory."""
    with self._lock:
        if session_id in self._queues:
            q = self._queues[session_id]

            # Drain queue to release references
            try:
                while not q.empty():
                    q.get_nowait()
            except queue.Empty:
                pass

            del self._queues[session_id]
```

#### 4. Python Garbage Collection

**File:** `src/web/optimization_runner.py` (enhanced)
```python
import gc

def run_optimization(session_id, config):
    try:
        result = optimize_build(config)
        session_manager.update(session_id, status='completed', result=result.to_dict())

        # Explicitly delete large objects
        del result

    finally:
        cleanup_lua_runtime()
        release_optimization_lock()

        # Force garbage collection (optional - use sparingly)
        gc.collect()
```

### Memory Monitoring

**Testing:** Monitor memory usage during 50 consecutive optimizations.

**Tool:** `psutil` library
```python
import psutil
import os

def log_memory_usage():
    """Log current process memory usage."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    print(f"Memory: {mem_info.rss / 1024 / 1024:.1f} MB")
```

**Test Script:** `tests/performance/memory_leak_test.py`
```python
import time
from src.web.routes import optimize

def test_memory_leak():
    """Run 50 optimizations and verify memory returns to baseline."""
    baseline = get_memory_usage()

    for i in range(50):
        session_id = run_optimization(sample_build)
        wait_for_completion(session_id)

        if i % 10 == 0:
            current = get_memory_usage()
            print(f"Iteration {i}: {current} MB (baseline: {baseline} MB)")

    final = get_memory_usage()
    growth = final - baseline

    assert growth < 50, f"Memory leak detected: {growth} MB growth"
```

---

## Deployment & Configuration

### Application Entry Point

**File:** `main.py`
```python
"""
PoE 2 Passive Tree Optimizer - Main entry point
Starts Flask web server on localhost:5000
"""
from src.web.app import create_app

if __name__ == '__main__':
    app = create_app()

    print("=" * 60)
    print("PoE 2 Passive Tree Optimizer")
    print("=" * 60)
    print("")
    print("Server running at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("")

    # Run Flask development server
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,  # Enable auto-reload during development
        threaded=True  # Enable multi-threading (handled by request lock)
    )
```

### Configuration File

**File:** `config.yaml`
```yaml
# Flask Web Application Configuration

app:
  host: 127.0.0.1
  port: 5000
  debug: true
  secret_key: "dev-secret-key-change-for-production"

optimization:
  max_iterations: 600
  timeout_seconds: 300
  convergence_patience: 3

session:
  expiration_hours: 24
  cleanup_interval_seconds: 3600

logging:
  level: INFO
  file: logs/optimizer.log
  max_bytes: 10485760  # 10MB
  backup_count: 5

pob:
  max_code_size_kb: 100
  engine_path: external/pob-engine
```

### Environment Setup

**Requirements:** `requirements.txt` (Epic 3 additions)
```
# Epic 1 & 2 dependencies (existing)
lupa>=2.0
xmltodict==0.13.0
pytest>=7.4.0
pytest-cov>=4.1.0

# Epic 3 dependencies (new)
Flask==3.0.0
Flask-Cors==4.0.0  # If frontend develops separately
psutil>=5.9.0      # Memory monitoring
PyYAML>=6.0        # Config file parsing
```

### Startup Sequence

1. Load `config.yaml`
2. Initialize Flask app
3. Register routes and error handlers
4. Initialize global managers (session_manager, sse_manager)
5. Start session cleanup background thread
6. Load passive tree data (Epic 1 - cached)
7. Run Flask development server

---

## Testing Strategy

### Test Levels

#### Unit Tests

**Target:** Individual components in isolation

**Coverage:**
- `sse_manager.py` - Message broadcasting, queue management
- `session_manager.py` - CRUD operations, expiration
- `error_handler.py` - Error formatting

**Tools:** pytest, mocking

**Example:**
```python
def test_sse_manager_send_progress():
    manager = SSEManager()
    session_id = 'test-session'

    q = manager.create_stream(session_id)
    manager.send_progress(session_id, 'progress', {'iteration': 100})

    msg = q.get(timeout=1.0)
    assert msg['event'] == 'progress'
    assert msg['data']['iteration'] == 100
```

#### Integration Tests

**Target:** HTTP endpoints with mocked Epic 1/2

**Coverage:**
- POST /optimize - Request validation, session creation
- GET /progress/\<id\> - SSE streaming
- GET /result/\<id\> - Result retrieval
- Error handling flows

**Tools:** pytest, Flask test client

**Example:**
```python
def test_optimize_endpoint(client):
    response = client.post('/optimize', json={
        'pob_code': 'valid_code_here',
        'metric': 'dps',
        'unallocated_points': 15,
        'respec_points': 12
    })

    assert response.status_code == 200
    data = response.get_json()
    assert 'session_id' in data
    assert data['status'] == 'pending'
```

#### End-to-End Tests

**Target:** Full user workflow with real Epic 1/2

**Coverage:**
- Submit optimization → Receive progress → Get results → Export code
- Round-trip validation (exported code imports to PoB)

**Tools:** Manual testing (Alec validates), automated with Selenium (future)

#### Performance Tests

**Target:** Memory leaks, SSE performance

**Coverage:**
- 50 consecutive optimizations (memory growth < 50MB)
- SSE stream latency (progress updates arrive < 100ms)

**Tools:** psutil, time.perf_counter()

### Test Data

**Fixtures:**
- `tests/fixtures/parity_builds/` - Real PoB codes from Epic 1
- `tests/fixtures/invalid_builds/` - Malformed codes, unsupported features
- `tests/fixtures/expected_errors/` - Error response templates

---

## Risks & Mitigations

### RISK-3.1: SSE Connection Stability

**Risk:** SSE connection drops during long optimizations (5 minutes), user loses progress visibility.

**Probability:** Medium
**Impact:** Medium (UX degradation, user thinks app crashed)

**Mitigations:**
1. **Keepalive comments** - Send `: keepalive\n\n` every 1 second to prevent timeout
2. **Auto-reconnect** - Client-side EventSource reconnects automatically on disconnect
3. **Progress polling fallback** - If SSE unavailable, poll GET /result/\<id\> every 2 seconds
4. **Session persistence** - Progress stored in session even if SSE disconnects

**Status:** Mitigated

---

### RISK-3.2: LuaRuntime Crash During Optimization

**Risk:** PoB calculation engine crashes mid-optimization, leaves lock held, blocks future requests.

**Probability:** Low
**Impact:** High (app becomes unusable until restart)

**Mitigations:**
1. **try/finally lock release** - Lock always released even on exception
2. **Lock timeout** - acquire_lock(timeout=1.0) prevents indefinite blocking
3. **Error broadcasting** - SSE sends 'error' event to client, UI shows actionable message
4. **Session recovery** - Session marked 'failed', partial results preserved

**Status:** Mitigated

---

### RISK-3.3: Memory Leak in Long-Running Server

**Risk:** Memory accumulates over days/weeks of use, server becomes slow or crashes.

**Probability:** Medium
**Impact:** Medium (requires restart, annoying for long-term use)

**Mitigations:**
1. **Explicit cleanup** - cleanup_lua_runtime() after each optimization
2. **Session expiration** - Old sessions deleted after 24 hours
3. **SSE queue draining** - Queue memory freed when connection closes
4. **Performance testing** - Automated test validates 50 runs without leak
5. **Memory monitoring** - Log warnings if memory exceeds 500MB

**Status:** Mitigated, requires validation testing

---

### RISK-3.4: Flask Development Server Not Production-Ready

**Risk:** Werkzeug development server not suitable for production, but we're using it for local MVP.

**Probability:** N/A (known limitation)
**Impact:** Low (acceptable for local single-user)

**Mitigations:**
1. **Document limitation** - README warns "for local use only"
2. **Future migration path** - Switch to Gunicorn/uWSGI if multi-user needed
3. **Current usage acceptable** - Local MVP on localhost:5000 is safe

**Status:** Accepted (intentional trade-off for simplicity)

---

## Appendix A: Flask App Factory Pattern

**File:** `src/web/app.py`
```python
"""
Flask application factory.
Creates and configures Flask app instance.
"""
from flask import Flask
import yaml
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_path='config.yaml'):
    """
    Create and configure Flask application.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Flask: Configured application instance
    """
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Load configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    app.config['SECRET_KEY'] = config['app']['secret_key']
    app.config['DEBUG'] = config['app']['debug']
    app.config['OPTIMIZER_CONFIG'] = config['optimization']
    app.config['SESSION_CONFIG'] = config['session']

    # Setup logging
    setup_logging(app, config['logging'])

    # Register routes
    from src.web.routes import register_routes
    register_routes(app)

    # Register error handlers
    from src.web.error_handler import register_error_handlers
    register_error_handlers(app)

    # Start background cleanup thread
    from src.web.session_manager import start_cleanup_thread
    start_cleanup_thread(config['session']['cleanup_interval_seconds'])

    return app

def setup_logging(app, log_config):
    """Configure file-based logging."""
    os.makedirs('logs', exist_ok=True)

    handler = RotatingFileHandler(
        log_config['file'],
        maxBytes=log_config['max_bytes'],
        backupCount=log_config['backup_count']
    )

    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s'
    ))

    handler.setLevel(getattr(logging, log_config['level']))
    app.logger.addHandler(handler)
    app.logger.setLevel(getattr(logging, log_config['level']))
```

---

## Appendix B: Route Registration

**File:** `src/web/routes.py`
```python
"""
Flask route handlers.
"""
from flask import render_template, request, jsonify, Response, stream_with_context
import threading

from src.web.session_manager import session_manager
from src.web.sse_manager import sse_manager
from src.web.optimization_runner import run_optimization
from src.web.error_handler import ValidationError, UnsupportedBuildError
from src.parser.pob_parser import parse_pob_code, encode_pob_code

def register_routes(app):
    """Register all HTTP endpoints."""

    @app.route('/')
    def index():
        """Serve main UI."""
        return render_template('index.html')

    @app.route('/optimize', methods=['POST'])
    def optimize():
        """Submit optimization request."""
        data = request.get_json()

        # Validate inputs
        pob_code = data.get('pob_code')
        metric = data.get('metric')
        unallocated = data.get('unallocated_points')
        respec = data.get('respec_points')

        if not pob_code:
            raise ValidationError('Missing required parameter: pob_code')

        if metric not in ['dps', 'ehp', 'balanced']:
            raise ValidationError(f'Invalid metric: {metric}',
                                  action='Choose one of: dps, ehp, balanced')

        # Parse PoB code
        try:
            build = parse_pob_code(pob_code)
        except Exception as e:
            raise ValidationError('Invalid PoB code', details=str(e))

        # Create optimization config
        config = {
            'build': build,
            'metric': metric,
            'unallocated_points': unallocated,
            'respec_points': respec,
            'max_iterations': app.config['OPTIMIZER_CONFIG']['max_iterations'],
            'max_time_seconds': app.config['OPTIMIZER_CONFIG']['timeout_seconds']
        }

        # Create session
        session_id = session_manager.create(config)

        # Spawn optimization thread
        thread = threading.Thread(
            target=run_optimization,
            args=(session_id, config),
            daemon=True
        )
        thread.start()

        return jsonify({'session_id': session_id, 'status': 'pending'})

    @app.route('/progress/<session_id>')
    def progress_stream(session_id):
        """SSE endpoint for real-time progress."""
        q = sse_manager.create_stream(session_id)

        def event_stream():
            try:
                while True:
                    try:
                        msg = q.get(timeout=1.0)
                    except queue.Empty:
                        yield ': keepalive\n\n'
                        continue

                    yield f"event: {msg['event']}\n"
                    yield f"data: {json.dumps(msg['data'])}\n\n"

                    if msg['event'] in ('complete', 'error'):
                        break
            finally:
                sse_manager.close_stream(session_id)

        return Response(
            stream_with_context(event_stream()),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache'}
        )

    @app.route('/result/<session_id>')
    def get_result(session_id):
        """Retrieve optimization result."""
        session = session_manager.get(session_id)

        if not session:
            return jsonify({'error': 'Session not found'}), 404

        return jsonify({
            'status': session.status,
            'result': session.result,
            'error': session.error,
            'progress': session.progress
        })

    @app.route('/export/<session_id>')
    def export_code(session_id):
        """Export optimized PoB code."""
        session = session_manager.get(session_id)

        if not session or session.status != 'completed':
            return jsonify({'error': 'Optimization not complete'}), 400

        # Encode optimized build
        optimized_build = session.result['optimized_build']
        pob_code = encode_pob_code(optimized_build)

        return jsonify({'pob_code': pob_code, 'status': 'success'})
```

---

## Conclusion

This architecture delivers a robust, user-friendly Flask web application for Epic 3 while addressing the three critical technical challenges:

1. **Thread Safety:** Request-level mutex ensures LuaRuntime never accessed concurrently
2. **Real-Time Progress:** SSE provides instant progress updates without polling overhead
3. **Resource Management:** Explicit cleanup prevents memory leaks across repeated use

The design prioritizes **simplicity and pragmatism** for a local single-user MVP while maintaining **clean architectural boundaries** for future enhancements. All Epic 3 stories (3.1-3.12) can be implemented using this architecture without requiring fundamental redesign.

**Next Steps:**
1. Implement Task 3 (Flask + SSE Prototype) to validate SSE architecture
2. Begin Story 3.1 implementation (Flask Web Server Setup)
3. Iterate on UI/UX based on Alec's feedback during development

---

**Document Status:** Final
**Review Required:** Alec (Product Owner), Amelia (Developer), Murat (TEA)
**Implementation Ready:** Yes
**Epic 3 Blocker Resolved:** Yes (architecture defined, Task 2 complete)
