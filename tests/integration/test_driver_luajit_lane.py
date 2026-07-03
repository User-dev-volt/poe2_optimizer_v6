"""Story 4.2 -- luajit.exe fallback lane, MODULE-LEVEL skip-gated on POB_LUAJIT_EXE.

The `luajit.exe` binary is still UNSTAGED (Story 4.1 AC-4.1.5: no byte-matching
LuaJIT 2.1 vendored; the embedded-Lupa lane is primary per ADR-006). This test is
coded-and-ready and runs ONLY when POB_LUAJIT_EXE points at a compatible binary,
so CI/dev without it collects a single skipped test rather than a failure.

    set POB_LUAJIT_EXE=C:\\path\\to\\luajit.exe && pytest -n 1 tests/integration/test_driver_luajit_lane.py
"""

import os

import pytest

from src.calculator.driver_worker import DriverWorker

_LUAJIT_EXE = os.environ.get("POB_LUAJIT_EXE")

pytestmark = [
    pytest.mark.gui_parity,
    pytest.mark.slow,
    pytest.mark.skipif(
        not _LUAJIT_EXE,
        reason="POB_LUAJIT_EXE not set (luajit.exe binary unstaged per Story 4.1 AC-4.1.5)",
    ),
]


def test_luajit_lane_boots_and_pings():
    w = DriverWorker(lane="luajit", luajit_exe=_LUAJIT_EXE)
    try:
        info = w.start()
        assert info.get("ready"), f"luajit lane failed to boot: {info}"
        assert info.get("lane") == "luajit.exe"
        assert w.ping().get("ok")
    finally:
        w.shutdown()
