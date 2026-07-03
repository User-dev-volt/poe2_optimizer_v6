"""Story 4.1 spike -- v0.15.0 GUI parity through the Truth-Engine driver worker.

Feeds each of the 6 Tier-A `tests/fixtures/gui_baselines/xml/*.xml` builds to the
REAL PoB engine via src/calculator/driver.lua running inside a respawnable Python
worker PROCESS (src/calculator/driver_worker.DriverWorker, embedded lane), reads
the archetype-correct stat from build.calcsTab.mainOutput across the process
boundary, and asserts +/-0.1% relative (or +/-1 absolute for zero) against the
paired `*.baseline.json` (AC-4.1.2 / AC-4.1.3 / AC-4.1.11).

Marked @pytest.mark.gui_parity so it INHERITS the tests/conftest.py autouse
pob_env guard -- on a drifted engine these tests FAIL at setup (never skip, never
falsely green). MUST run under `pytest -n 1` (LuaJIT is not thread-safe; the
teardown SEH 0xe24c4a02 after "N passed" is benign per ADR-003).

    pytest -n 1 tests/integration/test_driver_parity.py -v

[Source: tests/fixtures/gui_baselines/; docs/stories/4-1-truth-engine-driver-spike.md
         Task 5; src/calculator/driver_worker.py; tests/conftest.py:28-67]
"""

import json
from pathlib import Path

import pytest

from src.calculator.driver_worker import DriverWorker, WorkerCrash

pytestmark = [pytest.mark.gui_parity, pytest.mark.slow]

BASELINE_DIR = Path(__file__).parent.parent / "fixtures" / "gui_baselines"
XML_DIR = BASELINE_DIR / "xml"
TOLERANCE_PERCENT = 0.1

# The primary anchor (AC-4.1.2). The stale corpus value 18097.067904221 is
# explicitly NOT the target -- that XML lives in realistic_builds/, not here.
DEADEYE_ANCHOR = 23003.185361227


def _discover():
    """[(name, archetype, stat_key, target)] for every baseline json/xml pair."""
    cases = []
    for jpath in sorted(BASELINE_DIR.glob("*.baseline.json")):
        name = jpath.name.replace(".baseline.json", "")
        if not (XML_DIR / f"{name}.xml").exists():
            continue
        bj = json.loads(jpath.read_text(encoding="utf-8"))
        archetype = bj["_metadata"]["archetype"]
        # DoT builds report TotalDPS=0 with real damage in TotalDot -- a naive
        # TotalDPS assertion passes 0~=0 vacuously, so branch on archetype.
        stat_key = "TotalDot" if archetype == "dot" else "TotalDPS"
        cases.append((name, archetype, stat_key, float(bj["stats"][stat_key])))
    return cases


CASES = _discover()


@pytest.fixture(scope="module")
def worker():
    """One booted embedded worker for the whole module (boot ~0.7s)."""
    w = DriverWorker(lane="embedded")
    try:
        w.start()
    except WorkerCrash as e:  # boot-time SEH would surface here
        pytest.fail(f"driver worker failed to boot: {e}\n{e.stderr_tail}", pytrace=False)
    yield w
    w.shutdown()


def _assert_within_tolerance(got: float, target: float, label: str):
    if target == 0:
        assert abs(got) <= 1.0, f"{label}: got={got}, target=0 (abs tol +/-1)"
    else:
        err_pct = abs(got - target) / abs(target) * 100.0
        assert err_pct <= TOLERANCE_PERCENT, (
            f"{label}: got={got}, target={target} (v0.15.0 GUI), "
            f"error={err_pct:.4f}% (max {TOLERANCE_PERCENT}%)"
        )


@pytest.mark.parametrize("name,archetype,stat_key,target", CASES,
                         ids=[c[0] for c in CASES])
def test_driver_parity(worker, name, archetype, stat_key, target):
    """AC-4.1.2/4.1.3: archetype-correct +/-0.1% parity through the worker process."""
    xml = (XML_DIR / f"{name}.xml").read_text(encoding="utf-8")
    resp = worker.load_build(xml, name)
    assert resp.get("ok"), f"LOAD_BUILD failed for {name}: {resp}"

    stats = worker.get_stats([stat_key, "TotalDPS", "TotalDot"])
    assert stat_key in stats and stats[stat_key] is not None, \
        f"{name}: stat {stat_key} missing from worker output: {stats}"

    _assert_within_tolerance(float(stats[stat_key]), target,
                             f"{name}[{archetype}].{stat_key}")


def test_deadeye_primary_anchor(worker):
    """AC-4.1.2: the geared deadeye anchor is EXACT to the v0.15.0 GUI baseline."""
    xml = (XML_DIR / "deadeye_lightning_arrow_76.xml").read_text(encoding="utf-8")
    worker.load_build(xml, "deadeye_lightning_arrow_76")
    got = float(worker.get_stats(["TotalDPS"])["TotalDPS"])
    _assert_within_tolerance(got, DEADEYE_ANCHOR, "deadeye primary anchor")


def test_dot_branch_is_not_vacuous(worker):
    """AC-4.1.3: the DoT anchor's real damage is in TotalDot; TotalDPS is ~0.

    Guards against a parity harness that keys only on TotalDPS and passes 0~=0.
    """
    xml = (XML_DIR / "witch_essence_drain_86.xml").read_text(encoding="utf-8")
    worker.load_build(xml, "witch_essence_drain_86")
    stats = worker.get_stats(["TotalDPS", "TotalDot"])
    assert float(stats.get("TotalDPS") or 0.0) <= 1.0, \
        "DoT build should report ~0 TotalDPS (real damage lives in TotalDot)"
    _assert_within_tolerance(float(stats["TotalDot"]), 23752.222654477,
                             "witch_essence_drain_86 TotalDot")
