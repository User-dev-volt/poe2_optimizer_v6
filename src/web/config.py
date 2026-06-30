"""Static configuration constants for the web layer.

A plain module of literals only. No external config files and no PyYAML — these
values are imported directly by the Flask app, routes, and optimization runner.
"""

# --- Server bind address -------------------------------------------------
HOST = "127.0.0.1"
PORT = 5000

# --- Optimizer limits applied to web-initiated runs ----------------------
# These cap how long / how hard a single browser-triggered optimization runs.
# They are passed into OptimizationConfiguration by the route/runner layer.
MAX_ITERATIONS = 200
TIMEOUT_SECONDS = 300
CONVERGENCE_PATIENCE = 5

# --- Input guard ---------------------------------------------------------
# Reject PoB import codes longer than this many characters before parsing.
MAX_POB_CODE_LEN = 100000
