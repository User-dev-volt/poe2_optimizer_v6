# Flask + SSE Prototype

## Purpose

This prototype demonstrates **Server-Sent Events (SSE)** for real-time progress streaming without page refresh. It de-risks **Story 3.5** (Real-Time Progress Display), which is the highest technical complexity story in Epic 3.

## What It Demonstrates

1. **Flask web server** running on localhost:5000
2. **SSE endpoint** (`/progress/<session_id>`) that streams progress updates
3. **Client-side EventSource API** for consuming SSE events
4. **Real-time UI updates** showing:
   - Progress bar (0-100%)
   - Iteration count
   - Improvement percentage
   - Simulated metrics (DPS)
   - Time elapsed
5. **Connection status indicator** (connecting/connected)
6. **Event log** showing all SSE messages received
7. **Cancel functionality** to stop optimization early

## Architecture

### Server-Side (Python/Flask)

- **`app.py`**: Flask application with:
  - `/` - Serves main UI
  - `/start` - Starts simulated optimization
  - `/progress/<session_id>` - SSE stream endpoint
  - `/cancel/<session_id>` - Cancel endpoint
- **SSE Manager**: Uses `queue.Queue` for thread-safe message broadcasting
- **Background thread**: Simulates optimization with progress updates every 100 iterations

### Client-Side (HTML/JavaScript)

- **`templates/index.html`**: Single-page UI with:
  - Start/Cancel buttons
  - Progress bar
  - Metrics cards
  - Connection status indicator
  - Event log
- **EventSource API**: Native browser SSE client
- **Event handlers**: `progress`, `complete`, `cancelled`, `error`

## How to Run

### 1. Install Flask (if not already installed)

```bash
pip install Flask
```

### 2. Run the prototype

```bash
cd prototypes/flask_sse_demo
python app.py
```

### 3. Open in browser

Navigate to: http://localhost:5000

### 4. Test SSE streaming

1. Click **"Start Optimization"**
2. Watch real-time progress updates (no page refresh!)
3. Observe:
   - Connection status changes to green (connected)
   - Progress bar fills up
   - Metrics update every 100 iterations
   - Event log shows all SSE messages
4. Try clicking **"Cancel"** to test early termination

## Expected Behavior

- **SSE connection** establishes immediately
- **Progress updates** arrive every ~10 seconds (100 iterations × 0.1s)
- **Keepalive comments** sent every 1 second to prevent timeout
- **Completion event** received after 600 iterations (~60 seconds)
- **Connection closes** gracefully after completion

## Key Learnings for Epic 3

### What Works Well

✅ SSE is **simple to implement** - just `Response(generator, mimetype='text/event-stream')`
✅ Browser **EventSource API** handles reconnection automatically
✅ **Real-time updates** feel responsive and professional
✅ **No polling overhead** - server pushes updates only when data available
✅ **Thread-safe** - `queue.Queue` handles concurrent access

### Challenges Addressed

✅ **Connection stability** - Keepalive comments prevent timeout
✅ **Queue management** - Bounded queue with drop-oldest policy
✅ **Graceful cleanup** - Stream closes after completion
✅ **Error handling** - Client detects disconnects and handles gracefully

### Ready for Story 3.5 Implementation

This prototype proves SSE architecture is viable for Story 3.5. The core patterns are:

1. **Session-based streams** - Each optimization gets unique session ID
2. **Message queue** - Thread-safe communication between optimization thread and SSE stream
3. **Event types** - `progress`, `complete`, `error` for different states
4. **UI updates** - JavaScript updates DOM elements based on SSE events

## Acceptance Criteria Met

✅ **SSE endpoint streams progress updates to browser without refresh** ✓
✅ **Client receives updates in real-time** ✓
✅ **Connection remains stable during long-running task (60+ seconds)** ✓
✅ **Graceful completion and error handling** ✓

## Next Steps

1. ✅ Prototype validates SSE architecture
2. ➡️ Proceed with Story 3.5 implementation
3. ➡️ Integrate with Epic 2's `optimize_build()` progress callback
4. ➡️ Add production error handling and resource cleanup

## References

- Architecture Document: `docs/architecture/epic-3-web-architecture.md` (lines 304-641)
- Epic 002 Retrospective: `docs/retrospectives/epic-002-retro-2025-10-31.md` (lines 436-441)
- Prep Sprint Status: `docs/prep-sprint-status.yaml` (task-3-flask-sse-prototype)
