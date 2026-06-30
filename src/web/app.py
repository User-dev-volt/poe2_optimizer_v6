"""Flask application factory and shared web-layer singletons.

This module owns the three process-global objects the web layer shares between
the Flask request threads and the optimizer worker threads:

* ``session_manager`` -- in-memory registry of optimization sessions.
* ``sse_manager`` -- per-session Server-Sent Events queues.
* ``optimization_lock`` -- a single mutex that serializes optimize runs so only
  one LuaJIT optimization executes at a time (LuaJIT is not thread-safe).

``routes.py`` and ``optimization_runner.py`` import THESE SAME instances, so the
request handlers and the worker threads operate on one shared store.

Circular-import note: ``routes`` and ``optimization_runner`` both import the
globals defined here, and ``create_app`` needs ``register_routes`` from
``routes``. To break the cycle, the globals are module-level (defined before any
factory runs) and the ``routes`` import is deferred into :func:`create_app`. By
the time the factory runs, this module is fully initialized, so the child
modules resolve the globals cleanly regardless of import order.
"""

from __future__ import annotations

import logging
import threading

from flask import Flask

from src.web.session_manager import SessionManager
from src.web.sse_manager import SSEManager

# --- Shared module-global singletons -------------------------------------
# Defined at import time, BEFORE create_app() runs, so routes.py and
# optimization_runner.py can `from src.web.app import ...` these exact objects.
session_manager = SessionManager()
sse_manager = SSEManager()
optimization_lock = threading.Lock()


def create_app() -> Flask:
    """Build and configure the Flask application.

    Returns:
        A configured :class:`flask.Flask` instance with all routes registered.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Deferred import: register_routes -> routes.py imports the globals above.
    # Importing here (not at module top) avoids a circular import, since this
    # module is fully loaded by the time create_app() is invoked.
    from src.web.routes import register_routes

    register_routes(app)
    logging.getLogger(__name__).info("Flask app created and routes registered")
    return app


if __name__ == "__main__":  # pragma: no cover - manual local launch only
    from src.web.config import HOST, PORT

    # debug=False is REQUIRED: the reloader spawns a second process and orphans
    # the optimizer worker threads. threaded=True lets SSE streams block their
    # own request thread without stalling the whole server.
    create_app().run(host=HOST, port=PORT, debug=False, threaded=True)
