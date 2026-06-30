"""Web layer for the PoE2 Build Optimizer.

Contains the Flask application factory, in-memory session store, and the
Server-Sent Events (SSE) plumbing used to stream optimization progress to the
browser. LuaJIT calculation work never runs in the Flask request thread; it is
executed in dedicated worker threads (see the optimization runner).
"""
