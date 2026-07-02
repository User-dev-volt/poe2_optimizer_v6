"""HTTP routes for the PoE2 Build Optimizer web layer.

Implements the five-endpoint contract that the browser front-end talks to:

* ``GET  /``                    -> render the single-page UI.
* ``POST /optimize``           -> validate + parse a PoB code, reject
  unsupported build types, then spawn a worker thread and return a session id.
* ``GET  /progress/<id>``      -> Server-Sent Events stream of progress.
* ``GET  /result/<id>``        -> poll terminal status / result / error.
* ``GET  /export/<id>``        -> re-encode the optimized tree into a PoB code.

The request handlers never run LuaJIT; :func:`run_optimization` does that on a
daemon worker thread. Handlers only validate input, manage sessions, and stream
events from the shared :data:`sse_manager`.
"""

from __future__ import annotations

import gc  # noqa: F401 - part of the shared web-layer import surface
import json
import logging
import queue
import re
import threading
from typing import Optional

from flask import Response, jsonify, render_template, request

from src.web.app import session_manager, sse_manager
from src.web.config import (
    MAX_POB_CODE_LEN,
    MAX_ITERATIONS,
    TIMEOUT_SECONDS,
    CONVERGENCE_PATIENCE,
)
from src.web.optimization_runner import run_optimization
from src.models.optimization_config import OptimizationConfiguration
from src.parsers.pob_parser import parse_pob_code, encode_pob_code, _is_minion_skill
from src.parsers.exceptions import (
    PoBParseError,
    InvalidFormatError,
    UnsupportedVersionError,
)

logger = logging.getLogger(__name__)

# Front-end copy for FR-1.6 (detect-and-reject unsupported build types). The
# em-dash is intentional and must match the UI string exactly.
UNSUPPORTED_BUILD_MESSAGE = (
    "Build Type Not Supported (Yet!) — Coming in V2: Minion builds, "
    "Totems, traps, mines, Trigger-based builds."
)

# FR-1.6 unsupported-build classifier patterns. We classify by the MAIN skill
# ONLY (its human name + skill_id) to avoid false positives: the previous naive
# substring scan across support-gem names wrongly flagged e.g.
# "SupportRapidAttacksPlayer" (contains "...porTRAPid..." -> matched "trap").
# The human-readable name uses word boundaries; the skill_id uses case-sensitive
# CamelCase type tokens so "Trap"/"Mine"/"Totem" cannot match inside
# "Rapid"/"Determination"/etc. Minion still defers to the parser's
# _is_minion_skill. Trigger builds are intentionally NOT gated in this MVP
# (they are support-gem-driven and too false-positive-prone to detect safely).
_NAME_UNSUPPORTED = re.compile(r"\b(totem|ballista|trap|mine)\b", re.IGNORECASE)
_ID_UNSUPPORTED = re.compile(r"(Totem|Ballista|Trap|Mine)")  # case-sensitive


def detect_unsupported_build_type(build) -> Optional[str]:
    """Best-effort classifier for unsupported (V2) build types.

    Classifies by the *resolved main skill only* (its human name + skill_id),
    flagging minion / totem / trap / mine builds. Pure string heuristics -- it
    never runs LuaJIT -- so it is safe to call from the Flask request thread.

    Note: the parser strips minion *active* gems during extraction
    (``_extract_skills`` skips ``_is_minion_skill`` gems), so a pure-minion
    build arrives here with an empty ``skills`` list; that empty list is itself
    treated as a minion build. Trigger builds are not detected in this MVP gate.

    Args:
        build: A parsed :class:`BuildData`.

    Returns:
        The V2 "not supported" message if the build is unsupported, else None.
    """
    skills = getattr(build, "skills", None) or []

    # Pure-minion builds lose all their active gems at parse time -> no skills.
    if not skills:
        return UNSUPPORTED_BUILD_MESSAGE

    # Resolve the main skill by the file's 1-indexed main_socket_group; fall
    # back to the first skill when the index is missing or out of range.
    idx = getattr(build, "main_socket_group", 1) or 1
    if not 1 <= idx <= len(skills):
        idx = 1
    main = skills[idx - 1]

    skill_id = getattr(main, "skill_id", "") or ""
    name = getattr(main, "name", "") or ""

    if _is_minion_skill(skill_id):
        return UNSUPPORTED_BUILD_MESSAGE
    if _NAME_UNSUPPORTED.search(name) or _ID_UNSUPPORTED.search(skill_id):
        return UNSUPPORTED_BUILD_MESSAGE

    return None


def _build_summary(build) -> dict:
    """Compact, display-ready identity for a parsed build (never runs LuaJIT).

    Pure read of already-parsed :class:`BuildData` so the UI can show real
    context (class / level / ascendancy / main skill) the moment a code is
    accepted, before the optimizer finishes.
    """

    def _class_name(cls):
        for attr in ("value", "name"):
            v = getattr(cls, attr, None)
            if isinstance(v, str) and v:
                return v
        return str(cls) if cls is not None else None

    skills = getattr(build, "skills", None) or []
    idx = getattr(build, "main_socket_group", 1) or 1
    if not 1 <= idx <= len(skills):
        idx = 1
    main_skill = getattr(skills[idx - 1], "name", None) if skills else None

    return {
        "class": _class_name(getattr(build, "character_class", None)),
        "level": getattr(build, "level", None),
        "ascendancy": getattr(build, "ascendancy", None),
        "main_skill": main_skill,
    }


def register_routes(app) -> None:
    """Register all five HTTP endpoints on ``app``."""

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/optimize", methods=["POST"])
    def optimize():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return (
                jsonify(
                    {
                        "error_type": "invalid_request",
                        "reason": "Request body must be a JSON object.",
                    }
                ),
                400,
            )

        pob_code = data.get("pob_code")
        if not isinstance(pob_code, str) or not pob_code.strip():
            return (
                jsonify(
                    {
                        "error_type": "invalid_input",
                        "reason": "A non-empty 'pob_code' string is required.",
                    }
                ),
                400,
            )

        # Cheap length guard before any decode/parse work.
        if len(pob_code) > MAX_POB_CODE_LEN:
            return (
                jsonify(
                    {
                        "error_type": "code_too_large",
                        "reason": f"PoB code exceeds the maximum length of "
                        f"{MAX_POB_CODE_LEN} characters.",
                    }
                ),
                400,
            )

        # Parse the PoB code. Catch subclasses before the PoBParseError base.
        try:
            build = parse_pob_code(pob_code)
        except UnsupportedVersionError as exc:
            return jsonify({"error_type": "unsupported_version", "reason": str(exc)}), 400
        except (InvalidFormatError, PoBParseError) as exc:
            return jsonify({"error_type": "parse_error", "reason": str(exc)}), 400

        # FR-1.6: detect-and-reject unsupported build types.
        unsupported_reason = detect_unsupported_build_type(build)
        if unsupported_reason:
            return (
                jsonify(
                    {
                        "error_type": "unsupported_build_type",
                        "reason": unsupported_reason,
                    }
                ),
                400,
            )

        metric = data.get("metric") or "dps"

        # Budget params: unallocated defaults to the build's free points;
        # respec is None when blank/omitted (unlimited deallocation).
        raw_unalloc = data.get("unallocated_points")
        raw_respec = data.get("respec_points")
        try:
            if raw_unalloc is None or (
                isinstance(raw_unalloc, str) and not raw_unalloc.strip()
            ):
                unallocated_points = build.unallocated_points
            else:
                unallocated_points = int(raw_unalloc)

            if raw_respec is None or (
                isinstance(raw_respec, str) and not raw_respec.strip()
            ):
                respec_points = None
            else:
                respec_points = int(raw_respec)

            config = OptimizationConfiguration(
                build=build,
                metric=metric,
                unallocated_points=unallocated_points,
                respec_points=respec_points,
                max_iterations=MAX_ITERATIONS,
                max_time_seconds=TIMEOUT_SECONDS,
                convergence_patience=CONVERGENCE_PATIENCE,
            )
        except (ValueError, TypeError) as exc:
            return jsonify({"error_type": "invalid_configuration", "reason": str(exc)}), 400

        # Create the session and its SSE stream BEFORE spawning the worker so a
        # fast worker can never emit into a missing queue.
        session_id = session_manager.create(config, original_code=pob_code)
        sse_manager.create_stream(session_id)

        thread = threading.Thread(
            target=run_optimization,
            args=(session_id,),
            name=f"optimizer-{session_id[:8]}",
            daemon=True,
        )
        thread.start()

        return (
            jsonify(
                {
                    "session_id": session_id,
                    "status": "pending",
                    "build": _build_summary(build),
                }
            ),
            200,
        )

    @app.route("/progress/<session_id>", methods=["GET"])
    def progress(session_id):
        event_queue = sse_manager.get_queue(session_id)
        if event_queue is None:
            return (
                jsonify(
                    {
                        "error_type": "unknown_session",
                        "reason": "No optimization stream for that session id.",
                    }
                ),
                404,
            )

        def generate():
            while True:
                try:
                    message = event_queue.get(timeout=15)
                except queue.Empty:
                    # Idle keepalive comment so proxies/browsers hold the stream.
                    yield ": keepalive\n\n"
                    continue

                event_name = message["event"]
                payload = message["data"]
                yield f"event: {event_name}\n"
                yield f"data: {json.dumps(payload)}\n"
                yield "\n"

                if event_name in ("complete", "error"):
                    break

        headers = {
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
        return Response(generate(), mimetype="text/event-stream", headers=headers)

    @app.route("/result/<session_id>", methods=["GET"])
    def result(session_id):
        session = session_manager.get(session_id)
        if session is None:
            return (
                jsonify({"status": "unknown", "result": None, "error": "Unknown session"}),
                404,
            )
        return (
            jsonify(
                {
                    "status": session.status,
                    "result": session.result,
                    "error": session.error,
                }
            ),
            200,
        )

    @app.route("/export/<session_id>", methods=["GET"])
    def export(session_id):
        session = session_manager.get(session_id)
        if session is None:
            return (
                jsonify(
                    {
                        "error_type": "unknown_session",
                        "reason": "Unknown session id.",
                    }
                ),
                404,
            )

        if session.status != "complete" or session.optimized_nodes is None:
            return (
                jsonify(
                    {
                        "error_type": "not_ready",
                        "reason": "Optimization has not completed for this session yet.",
                    }
                ),
                400,
            )

        try:
            pob_code = encode_pob_code(session.original_code, session.optimized_nodes)
        except (InvalidFormatError, PoBParseError) as exc:
            return jsonify({"error_type": "export_failed", "reason": str(exc)}), 400

        return jsonify({"pob_code": pob_code, "status": "ok"}), 200
