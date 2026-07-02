"""Regression test: the optimizer must actually IMPROVE a real build.

This is the test Epic 2 never had. The optimizer was silently a no-op for months
because passive-node mods were filtered out of the calc (allocMode="NORMAL" tagged
every node mod with a never-active WeaponSet condition); every neighbor scored
identically to baseline, so optimization "converged" at 0% improvement on every
build and the existing validation suite still passed (it only checked budget/time,
never improvement).

These tests load a realistic build WITH its items and skills (so the calc is
meaningful), run the optimizer with real budget, and assert that DPS genuinely
improves and that node changes were made within budget.

Run (Windows / LuaJIT, ADR-003):
    pytest tests/integration/optimizer/test_optimizer_finds_improvement.py -n 1 -v -s
"""

from pathlib import Path
from typing import Set

import pytest

from src.models.build_data import BuildData, CharacterClass
from src.models.optimization_config import OptimizationConfiguration
from src.optimizer.hill_climbing import optimize_build
from src.parsers.xml_utils import parse_xml
import src.parsers.pob_parser as pob_parser


CORPUS_DIR = Path("tests/fixtures/realistic_builds")

# Attack builds use the fast in-process MinimalCalc path; keep the budget modest so
# the test stays well under the 5-minute cap while still exercising real moves.
UNALLOCATED_BUDGET = 10
MAX_ITERATIONS = 40
MAX_TIME_SECONDS = 280


def load_full_build(xml_path: Path) -> BuildData:
    """Load a BuildData with passive nodes, items AND skills from a PoB XML fixture."""
    data = parse_xml(xml_path.read_text(encoding="utf-8"))
    pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
    build_section = pob_root["Build"]

    class_name = build_section.get("@className")
    character_class = CharacterClass(class_name) if class_name else CharacterClass.WITCH
    level = int(build_section.get("@level", "90"))
    ascendancy = build_section.get("@ascendClassName")
    if ascendancy == "None":
        ascendancy = None

    spec = (pob_root.get("Tree", {}) or {}).get("Spec", {}) or {}
    nodes_str = spec.get("@nodes", "") if isinstance(spec, dict) else ""
    passive_nodes: Set[int] = set()
    if nodes_str:
        try:
            passive_nodes = {int(n) for n in nodes_str.split(",") if n.strip()}
        except ValueError:
            pass

    return BuildData(
        character_class=character_class,
        level=level,
        ascendancy=ascendancy,
        passive_nodes=passive_nodes,
        tree_version=build_section.get("@targetVersion", "0_1"),
        build_name=xml_path.stem,
        items=pob_parser._extract_items(pob_root),
        skills=pob_parser._extract_skills(pob_root),
        config={"input": {}, "placeholder": {}},
    )


@pytest.mark.slow
@pytest.mark.parametrize("build_name", ["deadeye_lightning_arrow_76", "warrior_earthquake_89"])
def test_optimizer_improves_real_build(build_name: str):
    """Optimizer must raise DPS on a real (items+skills) build given free points."""
    xml_path = CORPUS_DIR / f"{build_name}.xml"
    if not xml_path.exists():
        pytest.skip(f"fixture missing: {xml_path}")

    build = load_full_build(xml_path)
    # Sanity: the build must actually have a skill, or DPS is meaningless.
    assert build.skills, f"{build_name} loaded with no skills"

    config = OptimizationConfiguration(
        build=build,
        metric="dps",
        unallocated_points=UNALLOCATED_BUDGET,
        respec_points=None,  # unlimited swaps
        max_iterations=MAX_ITERATIONS,
        max_time_seconds=MAX_TIME_SECONDS,
        convergence_patience=4,
    )

    result = optimize_build(config)

    baseline = result.baseline_stats.total_dps
    optimized = result.optimized_stats.total_dps
    print(
        f"\n[{build_name}] DPS {baseline:,.1f} -> {optimized:,.1f} "
        f"({result.improvement_pct:+.2f}%), +{len(result.nodes_added)} nodes, "
        f"-{len(result.nodes_removed)} nodes, {result.iterations_run} iters, "
        f"used {result.unallocated_used}/{UNALLOCATED_BUDGET} unalloc"
    )

    # Core claim: passive allocation drives the calc and the optimizer finds gains.
    assert baseline > 0, "baseline DPS is zero (calc not producing damage)"
    assert optimized > baseline, (
        f"optimizer found no improvement: {baseline:.1f} -> {optimized:.1f}. "
        "If this regresses to equality, the calc is likely ignoring passive nodes again."
    )
    assert result.improvement_pct > 0
    assert result.nodes_added, "no nodes were added despite available budget"

    # Budget must be respected (the dual-budget swap-accounting fix).
    assert result.unallocated_used <= UNALLOCATED_BUDGET, (
        f"budget violation: used {result.unallocated_used} > {UNALLOCATED_BUDGET}"
    )
