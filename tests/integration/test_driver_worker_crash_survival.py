"""Story 4.2 -- crash survival (AC-4.2.13): a native crash is a recoverable
WorkerCrash, and the pool respawns a fresh worker before the next calc.

Kills the child PROCESS mid-life to simulate the SEH 0xe24c4a02 that Story 4.1
proved is contained by process isolation, then asserts: (1) a bare DriverWorker
surfaces the death as WorkerCrash and can restart(); (2) the pool health-check
respawns a dead worker before handout so the NEXT pool.calculate still succeeds.

gui_parity+slow, `pytest -n 1` (ADR-003).
"""

from pathlib import Path

import pytest

from src.calculator.driver_worker import DriverWorker, WorkerCrash
from src.calculator.worker_pool import WorkerPool

pytestmark = [pytest.mark.gui_parity, pytest.mark.slow]

XML_DIR = Path(__file__).parent.parent / "fixtures" / "gui_baselines" / "xml"
DEADEYE = "deadeye_lightning_arrow_76"
DEADEYE_ANCHOR = 23003.185361227


def _deadeye_xml():
    return (XML_DIR / f"{DEADEYE}.xml").read_text(encoding="utf-8")


def test_bare_worker_crash_then_restart():
    w = DriverWorker(lane="embedded")
    w.start()
    try:
        assert w.is_alive()
        assert w.ping().get("ok")

        # Simulate a hard crash (SEH-equivalent): kill the child process.
        w.proc.kill()
        w.proc.wait()

        # The next command must surface the death as a catchable WorkerCrash,
        # never a hang or a bare exception.
        with pytest.raises(WorkerCrash):
            w.ping()

        # ...and the worker is respawnable to a fresh, healthy process.
        w.restart()
        assert w.is_alive()
        assert w.ping().get("ok")
    finally:
        w.shutdown()


def test_pool_respawns_dead_worker_before_next_calc():
    pool = WorkerPool(size=1)
    try:
        # Boot + one good calc.
        s1 = pool.calculate(_deadeye_xml(), name=DEADEYE, stats=["TotalDPS"])
        assert float(s1["TotalDPS"]) > 0

        # Kill the (now idle) worker out from under the pool.
        with pool._lock:
            workers = list(pool._all)
        assert workers, "pool should own a worker after the first calc"
        workers[0].proc.kill()
        workers[0].proc.wait()

        # Next calc: acquire's health-check finds the corpse, respawns before
        # handout, and the calc still lands the baseline.
        s2 = pool.calculate(_deadeye_xml(), name=DEADEYE, stats=["TotalDPS"])
        err = abs(float(s2["TotalDPS"]) - DEADEYE_ANCHOR) / DEADEYE_ANCHOR * 100.0
        assert err <= 0.1
    finally:
        pool.shutdown()
