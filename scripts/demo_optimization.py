"""Epic 2 Demo Script - Optimization Showcase

This script demonstrates the hill climbing optimizer functionality by:
1. Loading test builds from fixtures
2. Running optimize_build() with configurable parameters
3. Displaying detailed before/after stats and improvement metrics

Usage:
    python scripts/demo_optimization.py [--metric {dps,ehp,balanced}] [--build BUILD_NAME]

Examples:
    python scripts/demo_optimization.py
    python scripts/demo_optimization.py --metric dps --build build_01_witch_90
    python scripts/demo_optimization.py --metric balanced --build build_02_warrior_75

Reference: docs/retrospectives/epic-002-retro-2025-10-31.md lines 422-428
"""

import sys
from pathlib import Path

# Add project root to path to enable imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

import argparse
import logging
from typing import Set, List, Optional

from src.models.build_data import BuildData, CharacterClass, Item, Skill
from src.models.optimization_config import OptimizationConfiguration
from src.optimizer.hill_climbing import optimize_build
from src.parsers.xml_utils import parse_xml


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_build_from_xml_file(xml_path: Path) -> BuildData:
    """Load BuildData directly from XML file.

    Args:
        xml_path: Path to PoB XML file

    Returns:
        BuildData object

    Raises:
        FileNotFoundError: If XML file doesn't exist
        Exception: If parsing fails
    """
    if not xml_path.exists():
        raise FileNotFoundError(f"Build file not found: {xml_path}")

    # Read and parse XML
    xml_str = xml_path.read_text(encoding='utf-8')
    data = parse_xml(xml_str)

    # Extract build data (same logic as pob_parser.py but without Base64/zlib)
    pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
    if not pob_root:
        raise ValueError("Missing PathOfBuilding or PathOfBuilding2 root element")

    build_section = pob_root.get("Build")
    if not build_section:
        raise ValueError("Missing Build section in PoB XML")

    # Extract character data
    class_name = build_section.get("@className")
    character_class = CharacterClass(class_name) if class_name else CharacterClass.WITCH

    level_str = build_section.get("@level", "90")
    level = int(level_str)

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

    # Create BuildData
    return BuildData(
        character_class=character_class,
        level=level,
        ascendancy=ascendancy,
        passive_nodes=passive_nodes,
        tree_version=build_section.get("@targetVersion", "0_1"),
        build_name=build_section.get("@buildName"),
        items=[],  # Items not needed for demo
        skills=[]  # Skills not needed for demo
    )


def print_separator(char="=", length=80):
    """Print a visual separator line."""
    print(char * length)


def print_build_info(build: BuildData):
    """Print build information."""
    print(f"Class:       {build.character_class.value}")
    print(f"Level:       {build.level}")
    print(f"Ascendancy:  {build.ascendancy or 'None'}")
    print(f"Allocated:   {build.allocated_point_count} passive points")
    print(f"Unallocated: {build.unallocated_points} points available")


def print_stats(stats, label="Stats"):
    """Print build statistics."""
    print(f"\n{label}:")
    print(f"  DPS:  {stats.total_dps:,.2f}")
    print(f"  Life: {stats.life:,}")
    print(f"  EHP:  {stats.effective_hp:,.2f}")


def print_result(result):
    """Print optimization result details."""
    print_separator()
    print("OPTIMIZATION RESULTS")
    print_separator()

    # Stats comparison
    print_stats(result.baseline_stats, "BEFORE Optimization")
    print_stats(result.optimized_stats, "AFTER Optimization")

    # Improvement
    print(f"\nImprovement: {result.improvement_pct:+.2f}%")

    # Budget usage
    print_separator("-")
    print("Budget Usage:")
    print(f"  Unallocated points used: {result.unallocated_used}")
    print(f"  Respec points used:      {result.respec_used}")

    # Node changes
    print_separator("-")
    print("Node Changes:")
    print(f"  Nodes added:   {len(result.nodes_added)} nodes")
    print(f"  Nodes removed: {len(result.nodes_removed)} nodes")
    print(f"  Swaps:         {result.nodes_swapped}")

    # Convergence
    print_separator("-")
    print("Convergence:")
    print(f"  Reason:     {result.convergence_reason}")
    print(f"  Iterations: {result.iterations_run}")
    print(f"  Time:       {result.time_elapsed_seconds:.2f} seconds")

    print_separator()


def list_available_builds(parity_builds_path: Path) -> List[str]:
    """List all available build XML files."""
    xml_files = list(parity_builds_path.glob("*.xml"))
    return sorted([f.stem for f in xml_files])


def main():
    """Main demo script entry point."""
    parser = argparse.ArgumentParser(
        description="Epic 2 Optimizer Demo - Showcase hill climbing optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--metric",
        choices=["dps", "ehp", "balanced"],
        default="dps",
        help="Optimization metric (default: dps)"
    )
    parser.add_argument(
        "--build",
        type=str,
        default="build_01_witch_90",
        help="Build name from tests/fixtures/parity_builds/ (without .xml extension)"
    )
    parser.add_argument(
        "--unallocated",
        type=int,
        help="Override unallocated points budget (default: use build's available points)"
    )
    parser.add_argument(
        "--respec",
        type=int,
        help="Respec points budget (default: None = unlimited)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=600,
        help="Maximum optimization iterations (default: 600)"
    )
    parser.add_argument(
        "--list-builds",
        action="store_true",
        help="List all available builds and exit"
    )

    args = parser.parse_args()

    # Setup paths
    parity_builds_path = Path("tests/fixtures/parity_builds")
    if not parity_builds_path.exists():
        print(f"ERROR: Parity builds directory not found: {parity_builds_path}")
        return 1

    # List builds if requested
    if args.list_builds:
        print("Available builds:")
        for build_name in list_available_builds(parity_builds_path):
            print(f"  - {build_name}")
        return 0

    # Load build
    build_path = parity_builds_path / f"{args.build}.xml"

    print_separator()
    print("EPIC 2 OPTIMIZER DEMO")
    print_separator()
    print(f"Build file: {build_path.name}")
    print(f"Metric:     {args.metric}")
    print_separator()

    try:
        build = load_build_from_xml_file(build_path)
    except Exception as e:
        print(f"\nERROR: Failed to load build: {e}")
        print(f"\nRun with --list-builds to see available builds")
        return 1

    # Print build info
    print("\nBuild Information:")
    print_build_info(build)

    # Determine budget
    unallocated_budget = args.unallocated if args.unallocated is not None else build.unallocated_points
    if unallocated_budget <= 0:
        print(f"\nWARNING: Build has no unallocated points available!")
        print(f"Consider using --unallocated to override, or choosing a different build.")
        return 1

    # Create optimization configuration
    config = OptimizationConfiguration(
        build=build,
        metric=args.metric,
        unallocated_points=unallocated_budget,
        respec_points=args.respec,
        max_iterations=args.max_iterations
    )

    print(f"\nOptimization Parameters:")
    print(f"  Metric:            {config.metric}")
    print(f"  Unallocated:       {config.unallocated_points} points")
    print(f"  Respec:            {config.respec_points if config.respec_points is not None else 'unlimited'}")
    print(f"  Max iterations:    {config.max_iterations}")
    print(f"  Timeout:           {config.max_time_seconds}s")

    # Run optimization
    print("\n" + "=" * 80)
    print("Running optimization...")
    print("=" * 80 + "\n")

    try:
        result = optimize_build(config)
    except Exception as e:
        print(f"\nERROR: Optimization failed: {e}")
        logger.exception("Optimization error details:")
        return 1

    # Print results
    print_result(result)

    # Success message
    if result.convergence_reason == "converged":
        print("\n[SUCCESS] Optimization completed successfully!")
    elif result.convergence_reason == "no_valid_neighbors":
        print("\n[SUCCESS] Optimization complete (no further improvements possible)")
    elif result.convergence_reason == "max_iterations":
        print("\n[WARN] Optimization stopped at maximum iterations")
    elif result.convergence_reason == "timeout":
        print("\n[WARN] Optimization stopped due to timeout")

    return 0


if __name__ == "__main__":
    exit(main())
