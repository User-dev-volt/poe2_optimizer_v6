"""Fast/unmarked driver_worker hardening tests (Story 4.2 AC-4.2.6 a/d/e, T8).

NO LuaJIT / no child process: the protocol methods are exercised with a
monkeypatched ``_send`` (or a fake stdout line) so we can assert the hardening
contract without booting the real engine (crash-survival lives in the gui_parity
integration test). ``stderr_path`` is provided so ``__init__`` never mkstemp's an
orphan temp file.
"""

import json

import pytest

from src.calculator.driver_worker import DriverWorker, WorkerCrash, ProtocolError


def _worker(tmp_path):
    # explicit stderr_path -> not owned, no mkstemp temp-file side effect.
    return DriverWorker(lane="embedded", stderr_path=str(tmp_path / "stderr.log"))


# ----- (d) get_stats RAISES on an {ok:false} envelope --------------------- #
def test_get_stats_raises_protocol_error_on_not_ok(tmp_path, monkeypatch):
    w = _worker(tmp_path)
    monkeypatch.setattr(w, "_send", lambda obj: {"ok": False, "error": "mainOutput unavailable"})
    with pytest.raises(ProtocolError):
        w.get_stats(["TotalDPS"])


def test_get_stats_returns_stats_on_ok(tmp_path, monkeypatch):
    w = _worker(tmp_path)
    monkeypatch.setattr(w, "_send", lambda obj: {"ok": True, "stats": {"TotalDPS": 5.0}})
    assert w.get_stats() == {"TotalDPS": 5.0}


# ----- (e) cmd set LAST so a payload key cannot clobber it ----------------- #
def test_eval_neighbors_sets_cmd_last(tmp_path, monkeypatch):
    w = _worker(tmp_path)
    sent = {}

    def fake_send(obj):
        sent.update(obj)
        return {"ok": True}

    monkeypatch.setattr(w, "_send", fake_send)
    w.eval_neighbors({"cmd": "HACK", "foo": 1})
    assert sent["cmd"] == "EVAL_NEIGHBORS"  # payload's "cmd" did NOT win
    assert sent["foo"] == 1


def test_apply_move_sets_cmd_last(tmp_path, monkeypatch):
    w = _worker(tmp_path)
    sent = {}
    monkeypatch.setattr(w, "_send", lambda obj: (sent.update(obj), {"ok": True})[1])
    w.apply_move({"cmd": "HACK"})
    assert sent["cmd"] == "APPLY_MOVE"


# ----- (a) malformed protocol line -> WorkerCrash, not a bare JSONDecodeError #
class _FakeStdin:
    def write(self, s):
        pass

    def flush(self):
        pass


class _FakeProc:
    def __init__(self):
        self.stdin = _FakeStdin()
        self.stdout = object()

    def poll(self):
        return None


def test_send_malformed_line_raises_workercrash(tmp_path, monkeypatch):
    w = _worker(tmp_path)
    w.proc = _FakeProc()
    monkeypatch.setattr(w, "is_alive", lambda: True)
    monkeypatch.setattr(w, "_readline_with_timeout", lambda timeout, phase="read": "not-json{")
    monkeypatch.setattr(w, "_die", lambda: None)
    monkeypatch.setattr(w, "_stderr_tail", lambda n=4000: "tail")
    with pytest.raises(WorkerCrash):
        w._send({"cmd": "PING"})


def test_send_valid_line_parses(tmp_path, monkeypatch):
    w = _worker(tmp_path)
    w.proc = _FakeProc()
    monkeypatch.setattr(w, "is_alive", lambda: True)
    monkeypatch.setattr(
        w, "_readline_with_timeout",
        lambda timeout, phase="read": json.dumps({"ok": True, "pong": True}),
    )
    assert w._send({"cmd": "PING"}) == {"ok": True, "pong": True}


# ----- (c) default per-worker stderr capture ------------------------------ #
def test_default_stderr_capture_owns_temp_file():
    # With no stderr_path, the worker owns a private capture file (so
    # _stderr_tail is never blank on a crash) and cleans it up on stop().
    import os

    w = DriverWorker(lane="embedded")
    try:
        assert w._owns_stderr is True
        assert w.stderr_path and os.path.exists(w.stderr_path)
    finally:
        w.stop()
    assert not os.path.exists(w.stderr_path)  # removed on stop()
