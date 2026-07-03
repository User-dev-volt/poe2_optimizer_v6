"""Story 4.2 -- FullCalcEngine seam parity (deadeye 23003.185361227 +/-0.1%).

Exercises the WHOLE item-2 reporting seam end-to-end: BuildData.source_xml ->
patch_passive_nodes_to_xml (writing @nodes AND @mainSocketGroup, re-serialized
through xmltodict) -> WorkerPool (respawnable child process) -> driver.lua real
PoB chain -> GET_STATS dict -> BuildStats map. Asserts the geared deadeye headline
DPS is within +/-0.1% of the v0.15.0 GUI baseline THROUGH the seam (AC-4.2.8).

Marked gui_parity so it INHERITS the tests/conftest.py pob_env guard (FAILS, never
skips, on a drifted engine). MUST run under `pytest -n 1` (LuaJIT not thread-safe;
teardown SEH 0xe24c4a02 after "N passed" is benign per ADR-003).

    pytest -n 1 tests/integration/test_full_calc_engine.py -v
"""

import base64
import zlib
from pathlib import Path

import pytest

from src.calculator.build_calculator import calculate_build_stats
from src.calculator.full_calc_engine import FullCalcEngine
from src.calculator.worker_pool import reset_worker_pool_for_tests
from src.parsers.pob_parser import parse_pob_code

pytestmark = [pytest.mark.gui_parity, pytest.mark.slow]

XML_DIR = Path(__file__).parent.parent / "fixtures" / "gui_baselines" / "xml"
DEADEYE = "deadeye_lightning_arrow_76"
DEADEYE_ANCHOR = 23003.185361227
TOLERANCE_PERCENT = 0.1


@pytest.fixture(autouse=True)
def _clean_pool():
    """Isolate the module-singleton pool for each test (spawn fresh, shut down)."""
    reset_worker_pool_for_tests()
    yield
    reset_worker_pool_for_tests()


def _build_from_baseline_xml(name: str):
    xml = (XML_DIR / f"{name}.xml").read_text(encoding="utf-8")
    # Round-trip through a PoB code so parse_pob_code stamps source_xml exactly as
    # the web path does (base64+zlib is byte-lossless, so source_xml == this xml).
    code = base64.b64encode(zlib.compress(xml.encode("utf-8"), 9)).decode("ascii")
    return parse_pob_code(code)


def _assert_within_tolerance(got: float, target: float, label: str):
    err_pct = abs(got - target) / abs(target) * 100.0
    assert err_pct <= TOLERANCE_PERCENT, (
        f"{label}: got={got}, target={target} (v0.15.0 GUI), "
        f"error={err_pct:.4f}% (max {TOLERANCE_PERCENT}%)"
    )


def test_full_calc_engine_deadeye_seam_parity():
    build = _build_from_baseline_xml(DEADEYE)
    assert not build.is_multi_spec, "deadeye baseline should be single-<Spec>"
    assert build.source_xml is not None
    stats = FullCalcEngine().calculate(build)
    _assert_within_tolerance(stats.total_dps, DEADEYE_ANCHOR, "FullCalcEngine deadeye seam")


def test_engine_full_selector_routes_through_seam():
    """calculate_build_stats(build, engine='full') reaches the same GUI number."""
    build = _build_from_baseline_xml(DEADEYE)
    stats = calculate_build_stats(build, engine="full")
    _assert_within_tolerance(stats.total_dps, DEADEYE_ANCHOR, "engine='full' selector deadeye")
