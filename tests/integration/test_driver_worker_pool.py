"""Story 4.2 -- WorkerPool e2e over real (embedded-lane) DriverWorkers (AC-4.2.3/5).

Two REAL worker processes boot the PoB engine; the pool acquires/releases them,
reports aggregate memory, and calculates the deadeye baseline through
`pool.calculate`. Uses the RAW baseline XML (not re-serialized) so this isolates
POOL correctness from the patch/serialization seam (which test_full_calc_engine.py
covers separately).

gui_parity+slow, `pytest -n 1` (ADR-003).
"""

from pathlib import Path

import pytest

from src.calculator.worker_pool import WorkerPool

pytestmark = [pytest.mark.gui_parity, pytest.mark.slow]

XML_DIR = Path(__file__).parent.parent / "fixtures" / "gui_baselines" / "xml"
DEADEYE = "deadeye_lightning_arrow_76"
DEADEYE_ANCHOR = 23003.185361227
TOLERANCE_PERCENT = 0.1


@pytest.fixture
def pool():
    p = WorkerPool(size=2)
    try:
        yield p
    finally:
        p.shutdown()


def _deadeye_xml():
    return (XML_DIR / f"{DEADEYE}.xml").read_text(encoding="utf-8")


def test_pool_calculates_deadeye_parity(pool):
    stats = pool.calculate(_deadeye_xml(), name=DEADEYE, stats=["TotalDPS"])
    got = float(stats["TotalDPS"])
    err = abs(got - DEADEYE_ANCHOR) / DEADEYE_ANCHOR * 100.0
    assert err <= TOLERANCE_PERCENT, f"pool deadeye {got} vs {DEADEYE_ANCHOR} = {err:.4f}%"


def test_pool_acquires_two_distinct_workers_and_reports_memory(pool):
    # Boot both workers by acquiring/pinging; confirm they are distinct processes.
    with pool.acquire() as w1:
        assert w1.ping().get("ok")
        with pool.acquire() as w2:
            assert w2.ping().get("ok")
            assert w1 is not w2  # a 2-worker pool hands out two distinct workers
    mb = pool.memory_mb()
    assert mb is not None and mb > 0.0  # aggregate RSS reported (risk #9 sizing)


def test_pool_reuses_worker_across_sequential_calls(pool):
    s1 = pool.calculate(_deadeye_xml(), name=DEADEYE, stats=["TotalDPS"])
    s2 = pool.calculate(_deadeye_xml(), name=DEADEYE, stats=["TotalDPS"])
    assert float(s1["TotalDPS"]) == pytest.approx(float(s2["TotalDPS"]), rel=1e-6)
