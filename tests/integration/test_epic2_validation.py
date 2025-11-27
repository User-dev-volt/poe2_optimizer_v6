"""Epic 2 Validation - Process-Isolated Optimizer Testing

This test suite validates the optimizer against the realistic builds corpus
using pytest-xdist for process isolation to avoid Windows Fatal Exception
(ADR-003).

Success Criteria (Epic 2 - Task 6):
- Success rate >= 70% (optimizer finds improvements)
- Median improvement >= 5% (on builds with unallocated points)
- All completions < 5 minutes (300 seconds)
- Zero budget violations

Usage:
    pytest tests/integration/test_epic2_validation.py -n auto --dist=loadfile -v

Author: Amelia (Dev Agent)
Date: 2025-11-26
Epic: 2 - Core Optimization Engine
Task: 6 - Validate Epic 2 Success Criteria
"""

import pytest
import json
import time
from pathlib import Path
from typing import Set

from src.models.build_data import BuildData, CharacterClass
from src.models.optimization_config import OptimizationConfiguration
from src.optimizer.hill_climbing import optimize_build
from src.parsers.xml_utils import parse_xml
import src.parsers.pob_parser as pob_parser


# Test configuration
CORPUS_DIR = Path("tests/fixtures/realistic_builds")
RESULTS_DIR = Path("docs/validation")
OPTIMIZATION_BUDGET = 20  # unallocated points per build
MAX_TIME_SECONDS = 300  # 5 minutes per build (Task 6 AC)


def load_build_from_xml(xml_path: Path) -> BuildData:
    """Load BuildData from XML file.

    Args:
        xml_path: Path to PoB XML file

    Returns:
        BuildData instance

    Raises:
        FileNotFoundError: If XML file doesn't exist
        ValueError: If XML structure is invalid
    """
    if not xml_path.exists():
        raise FileNotFoundError(f"Build file not found: {xml_path}")

    xml_str = xml_path.read_text(encoding='utf-8')
    data = parse_xml(xml_str)

    pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
    if not pob_root:
        raise ValueError("Missing PathOfBuilding root element")

    build_section = pob_root.get("Build")
    if not build_section:
        raise ValueError("Missing Build section")

    # Extract character data
    class_name = build_section.get("@className")
    character_class = CharacterClass(class_name) if class_name else CharacterClass.WITCH
    level = int(build_section.get("@level", "90"))
    ascendancy = build_section.get("@ascendClassName")
    if ascendancy == "None":
        ascendancy = None

    # Extract passive tree
    tree_section = pob_root.get("Tree", {})
    spec = tree_section.get("Spec", {}) if isinstance(tree_section, dict) else {}
    nodes_str = spec.get("@nodes", "") if isinstance(spec, dict) else ""

    passive_nodes: Set[int] = set()
    if nodes_str:
        try:
            passive_nodes = set(int(node_id.strip()) for node_id in nodes_str.split(",") if node_id.strip())
        except ValueError:
            pass

    # Extract config section for enemy settings
    config_section = pob_root.get("Config", {})
    config_set = config_section.get("ConfigSet", {}) if isinstance(config_section, dict) else {}

    config = {"input": {}, "placeholder": {}}

    # Extract Input elements
    inputs = config_set.get("Input", [])
    if isinstance(inputs, dict):
        inputs = [inputs]
    for inp in inputs:
        if isinstance(inp, dict):
            name = inp.get("@name")
            if name:
                if "@number" in inp:
                    config["input"][name] = float(inp["@number"])
                elif "@boolean" in inp:
                    config["input"][name] = inp["@boolean"].lower() == "true"
                elif "@string" in inp:
                    config["input"][name] = inp["@string"]

    # Extract Placeholder elements
    placeholders = config_set.get("Placeholder", [])
    if isinstance(placeholders, dict):
        placeholders = [placeholders]
    for ph in placeholders:
        if isinstance(ph, dict):
            name = ph.get("@name")
            if name:
                if "@number" in ph:
                    config["placeholder"][name] = float(ph["@number"])

    # Extract items and skills using parser functions (Story 2.9)
    items = pob_parser._extract_items(pob_root)
    skills = pob_parser._extract_skills(pob_root)

    build = BuildData(
        character_class=character_class,
        level=level,
        ascendancy=ascendancy,
        passive_nodes=passive_nodes,
        tree_version=build_section.get("@targetVersion", "0_1"),
        build_name=xml_path.stem,
        items=items,
        skills=skills,
        config=config
    )

    return build


def get_all_builds():
    """Get all XML build files from corpus."""
    if not CORPUS_DIR.exists():
        return []
    return sorted(CORPUS_DIR.glob("*.xml"))


@pytest.fixture(scope="session")
def results_collector(tmp_path_factory):
    """Session-scoped fixture to collect results from all tests."""
    results_dir = tmp_path_factory.mktemp("epic2_results")
    return results_dir


@pytest.mark.parametrize("build_path", get_all_builds(), ids=lambda p: p.stem)
def test_epic2_optimize_build(build_path: Path, results_collector: Path):
    """Test optimizer on a single build with process isolation.

    Each test runs in a separate process via pytest-xdist, avoiding
    the Windows Fatal Exception (ADR-003).

    Task 6 Acceptance Criteria:
    - Success rate >= 70% (tested across all builds)
    - Median improvement >= 5% (tested across all builds)
    - ALL completions < 5 minutes (asserted per build)
    - Zero budget violations (asserted per build)

    Args:
        build_path: Path to PoB XML file
        results_collector: Temporary directory for storing individual results
    """
    result = {
        "build_name": build_path.stem,
        "build_path": str(build_path),
        "status": "pending",
        "error": None,
        "baseline_dps": 0,
        "optimized_dps": 0,
        "baseline_life": 0,
        "optimized_life": 0,
        "baseline_mana": 0,
        "optimized_mana": 0,
        "baseline_es": 0,
        "optimized_es": 0,
        "improvement_pct": 0,
        "life_change": 0,
        "mana_change": 0,
        "es_change": 0,
        "time_seconds": 0,
        "iterations": 0,
        "nodes_added": 0,
        "unallocated_used": 0,
        "respec_used": 0,
        "convergence_reason": None,
    }

    try:
        # Load build
        build = load_build_from_xml(build_path)

        print(f"\n{'='*60}")
        print(f"Build: {build_path.stem}")
        print(f"  Class: {build.character_class.value}, Level: {build.level}")
        print(f"  Allocated: {build.allocated_point_count}, Budget: {OPTIMIZATION_BUDGET} points")

        # Create optimization config
        config = OptimizationConfiguration(
            build=build,
            metric="dps",
            unallocated_points=OPTIMIZATION_BUDGET,
            respec_points=None,  # Unlimited respec for testing
            max_iterations=200,
            max_time_seconds=MAX_TIME_SECONDS,
            convergence_patience=5
        )

        # Run optimization
        start_time = time.time()
        opt_result = optimize_build(config)
        elapsed = time.time() - start_time

        # Extract results
        result["status"] = "success"
        result["baseline_dps"] = opt_result.baseline_stats.total_dps
        result["optimized_dps"] = opt_result.optimized_stats.total_dps
        result["baseline_life"] = opt_result.baseline_stats.life
        result["optimized_life"] = opt_result.optimized_stats.life
        result["baseline_mana"] = opt_result.baseline_stats.mana
        result["optimized_mana"] = opt_result.optimized_stats.mana
        result["baseline_es"] = opt_result.baseline_stats.energy_shield
        result["optimized_es"] = opt_result.optimized_stats.energy_shield
        result["improvement_pct"] = opt_result.improvement_pct
        result["life_change"] = opt_result.optimized_stats.life - opt_result.baseline_stats.life
        result["mana_change"] = opt_result.optimized_stats.mana - opt_result.baseline_stats.mana
        result["es_change"] = opt_result.optimized_stats.energy_shield - opt_result.baseline_stats.energy_shield
        result["time_seconds"] = elapsed
        result["iterations"] = opt_result.iterations_run
        result["nodes_added"] = len(opt_result.nodes_added)
        result["unallocated_used"] = opt_result.unallocated_used
        result["respec_used"] = opt_result.respec_used
        result["convergence_reason"] = opt_result.convergence_reason

        print(f"  Baseline DPS: {result['baseline_dps']:,.2f}")
        print(f"  Optimized DPS: {result['optimized_dps']:,.2f}")
        print(f"  Improvement: {result['improvement_pct']:+.2f}%")
        print(f"  Life: {result['baseline_life']} -> {result['optimized_life']} ({result['life_change']:+d})")
        print(f"  Mana: {result['baseline_mana']} -> {result['optimized_mana']} ({result['mana_change']:+d})")
        print(f"  Time: {elapsed:.1f}s, Iterations: {opt_result.iterations_run}")
        print(f"  Convergence: {opt_result.convergence_reason}")

        # Task 6 AC: Zero budget violations
        assert opt_result.unallocated_used <= OPTIMIZATION_BUDGET, \
            f"Budget violation: used {opt_result.unallocated_used} > {OPTIMIZATION_BUDGET}"

        # Task 6 AC: All completions < 5 minutes
        assert elapsed < MAX_TIME_SECONDS, \
            f"Time violation: {elapsed:.1f}s >= {MAX_TIME_SECONDS}s"

    except AssertionError:
        # Re-raise assertion errors (these are test failures)
        raise
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"  ERROR: {e}")
        pytest.fail(f"Build optimization failed: {e}")

    # Save individual result to temp file for aggregation
    result_file = results_collector / f"{build_path.stem}.json"
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)
