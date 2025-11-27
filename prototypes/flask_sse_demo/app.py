"""
Flask + SSE Prototype
Demonstrates Server-Sent Events for real-time progress streaming.
De-risks Story 3.5 (highest technical complexity in Epic 3).
"""
from flask import Flask, render_template, Response, jsonify
import time
import threading
import queue
import json
from datetime import datetime

app = Flask(__name__)

# Simulated optimization sessions
sessions = {}
sse_queues = {}


class SimulatedOptimization:
    """Simulates a long-running optimization task."""

    def __init__(self, session_id):
        self.session_id = session_id
        self.max_iterations = 600
        self.running = True

    def run(self):
        """Simulate optimization progress with updates every 100ms."""
        for iteration in range(1, self.max_iterations + 1):
            if not self.running:
                self._send_event('cancelled', {'message': 'Optimization cancelled'})
                break

            # Simulate some work
            time.sleep(0.1)  # 100ms per iteration

            # Send progress update every 100 iterations
            if iteration % 100 == 0 or iteration == 1:
                improvement_pct = (iteration / self.max_iterations) * 15.0  # Simulate up to 15% improvement
                self._send_event('progress', {
                    'iteration': iteration,
                    'max_iterations': self.max_iterations,
                    'improvement_pct': round(improvement_pct, 1),
                    'best_metric': 125000 + (iteration * 50),  # Simulated DPS growth
                    'budget_used': {
                        'unallocated': min(15, iteration // 40),
                        'respec': min(12, iteration // 50)
                    },
                    'budget_total': {
                        'unallocated': 15,
                        'respec': 12
                    },
                    'time_elapsed': round(iteration * 0.1, 1),
                    'metric': 'DPS'
                })

        # Send completion event
        if self.running:
            self._send_event('complete', {
                'final_iteration': self.max_iterations,
                'improvement_pct': 15.2,
                'completion_time': round(self.max_iterations * 0.1, 1),
                'message': 'Optimization completed successfully!'
            })

    def _send_event(self, event_type, data):
        """Send SSE event to the queue."""
        if self.session_id in sse_queues:
            try:
                sse_queues[self.session_id].put_nowait({
                    'event': event_type,
                    'data': data
                })
            except queue.Full:
                pass  # Drop message if queue full


@app.route('/')
def index():
    """Serve main UI."""
    return render_template('index.html')


@app.route('/start', methods=['POST'])
def start_optimization():
    """Start a simulated optimization."""
    session_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"

    # Create SSE queue for this session
    sse_queues[session_id] = queue.Queue(maxsize=100)

    # Create and start optimization thread
    optimization = SimulatedOptimization(session_id)
    sessions[session_id] = optimization

    thread = threading.Thread(target=optimization.run, daemon=True)
    thread.start()

    return jsonify({
        'session_id': session_id,
        'status': 'started'
    })


@app.route('/progress/<session_id>')
def progress_stream(session_id):
    """SSE endpoint for streaming optimization progress."""

    # Create queue if it doesn't exist
    if session_id not in sse_queues:
        sse_queues[session_id] = queue.Queue(maxsize=100)

    q = sse_queues[session_id]

    def event_stream():
        """Generator yielding SSE-formatted messages."""
        try:
            while True:
                try:
                    # Block until message available (1 second timeout)
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

                # Close stream after 'complete', 'error', or 'cancelled'
                if event_type in ('complete', 'error', 'cancelled'):
                    break

        finally:
            # Cleanup: Remove queue
            if session_id in sse_queues:
                del sse_queues[session_id]

    # Return SSE response
    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Disable nginx buffering
            'Connection': 'keep-alive'
        }
    )


@app.route('/cancel/<session_id>', methods=['POST'])
def cancel_optimization(session_id):
    """Cancel a running optimization."""
    if session_id in sessions:
        sessions[session_id].running = False
        return jsonify({'status': 'cancelled'})
    return jsonify({'error': 'Session not found'}), 404


if __name__ == '__main__':
    print("=" * 60)
    print("Flask + SSE Prototype")
    print("=" * 60)
    print("")
    print("Server running at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("")
    print("This prototype demonstrates Server-Sent Events (SSE)")
    print("for real-time progress streaming without page refresh.")
    print("")

    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=True
    )
