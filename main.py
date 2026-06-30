"""Entry point for the PoE2 Build Optimizer web app.

Run with:

    python main.py

The Flask application factory lives in ``src.web.app`` (created by the routes
layer). ``app`` is exposed at module level so a WSGI server can import it as
``main:app`` if desired. The development server is started only when this
module is run directly, with the reloader disabled (debug=False) because it
would orphan the optimizer worker threads.
"""

from src.web.app import create_app

app = create_app()


if __name__ == "__main__":
    print("Optimizer running at http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
