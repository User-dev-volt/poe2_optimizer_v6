"""Flask smoke tests for src.web (story 3.5.4 AC-3.5.4.6).

The first automated tests importing src.web — closing the Epic 3 thin-slice
step-10 debt: POST /optimize happy path on a small attack build runs to a
successful terminal event, and the export round-trip yields a code that
re-parses via parse_pob_code.

MUST run under ``pytest -n 1`` (ADR-003): the happy path drives the real
optimizer, whose worker thread owns a LuaJIT engine — Windows SEH cleanup
requires process isolation.

Deliberately NOT parity-marked: the PoB environment guard (tests/conftest.py)
must not gate these — they exercise the web layer, not parity evidence.
"""

import base64
import time
import zlib
from pathlib import Path

import pytest

from src.parsers.pob_parser import parse_pob_code
from src.web.app import create_app

# Known-good ATTACK build (Lightning Arrow -> MinimalCalc fast path); the
# parity_builds/*.txt codes carry zero skills and are rejected by the
# unsupported-build gate, so the realistic-corpus deadeye is the smallest
# fixture that traverses the full pipeline.
FIXTURE_XML = (
    Path(__file__).resolve().parents[1]
    / "fixtures" / "realistic_builds" / "deadeye_lightning_arrow_76.xml"
)


def _pob_code() -> str:
    """Encode the raw XML fixture into a PoB import code (base64+zlib)."""
    xml = FIXTURE_XML.read_text(encoding="utf-8")
    return base64.b64encode(zlib.compress(xml.encode("utf-8"), 9)).decode("ascii")


@pytest.fixture
def client(monkeypatch):
    # routes.py imports the config caps BY NAME, so patch its module globals
    # (patching src.web.config would not be seen). Tiny budget: 2 iterations
    # keeps the run ~15-30s (most of it one-time engine init).
    monkeypatch.setattr("src.web.routes.MAX_ITERATIONS", 2)
    monkeypatch.setattr("src.web.routes.TIMEOUT_SECONDS", 120)
    monkeypatch.setattr("src.web.routes.CONVERGENCE_PATIENCE", 1)
    app = create_app()
    return app.test_client()


@pytest.mark.slow
def test_optimize_happy_path_and_export_roundtrip(client):
    code = _pob_code()

    resp = client.post(
        "/optimize",
        json={"pob_code": code, "metric": "dps", "unallocated_points": 2},
    )
    assert resp.status_code == 200, resp.get_data(as_text=True)
    body = resp.get_json()
    session_id = body["session_id"]
    assert body["build"]["main_skill"] == "Lightning Arrow"

    # Optimization runs in a background worker thread; poll /result until a
    # terminal state (generous ceiling for cold LuaJIT/engine init).
    deadline = time.time() + 300
    payload = None
    while time.time() < deadline:
        payload = client.get(f"/result/{session_id}").get_json()
        if payload["status"] in ("complete", "error"):
            break
        time.sleep(0.5)

    assert payload is not None and payload["status"] == "complete", (
        f"no successful terminal event: {payload}"
    )
    result = payload["result"]
    assert result["convergence"]["iterations_run"] >= 1
    assert "improvement_pct" in result

    # Export round-trip (AC: the exported code re-parses via parse_pob_code)
    exp = client.get(f"/export/{session_id}")
    assert exp.status_code == 200, exp.get_data(as_text=True)
    exported = exp.get_json()["pob_code"]

    rebuilt = parse_pob_code(exported)
    original = parse_pob_code(code)
    added = set(result["node_changes"]["added"])
    removed = set(result["node_changes"]["removed"])
    assert added.issubset(rebuilt.passive_nodes)
    assert not (removed & rebuilt.passive_nodes)
    assert len(rebuilt.passive_nodes) >= len(original.passive_nodes) - len(removed)


def test_optimize_rejects_garbage_code(client):
    # Cheap negative path: the web layer's structured 400, no LuaJIT cost.
    resp = client.post("/optimize", json={"pob_code": "not-a-real-code"})
    assert resp.status_code == 400
    assert resp.get_json()["error_type"] in ("parse_error", "unsupported_version")
