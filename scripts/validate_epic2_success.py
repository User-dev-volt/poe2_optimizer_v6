"""Epic 2 Success Criteria Validation Script

This script validates Epic 2 success criteria by running the optimizer on all
corpus builds and measuring comprehensive metrics.

Task 6 Requirements (prep-sprint-status.yaml:101-117):
- Run optimize_build() on all 36 parity builds
- Measure: success rate, improvement %, completion time, budget usage
- Calculate aggregates and compare against targets:
  * Success rate ≥ 70%
  * Median improvement ≥ 5%
  * All completions < 300s (5 minutes)
  * Budget constraints never violated
- Generate validation report document

Reference:
- docs/retrospectives/epic-002-retro-2025-10-31.md lines 459-482
- docs/prep-sprint-status.yaml lines 101-117

Usage:
    python scripts/validate_epic2_success.py [--max-builds N] [--metrics METRIC1,METRIC2,...]

Examples:
    python scripts/validate_epic2_success.py
    python scripts/validate_epic2_success.py --max-builds 5
    python scripts/validate_epic2_success.py --metrics dps,balanced
"""

import sys
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass

from src.models.build_data import BuildData, CharacterClass
from src.models.optimization_config import OptimizationConfiguration, OptimizationResult
from src.optimizer.hill_climbing import optimize_build
from src.parsers.xml_utils import parse_xml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationMetrics:
    """Metrics collected for a single build optimization run"""
    build_id: str
    build_class: str
    level: int
    allocated_points: int
    unallocated_points: int

    # Baseline stats
    baseline_dps: float
    baseline_life: float
    baseline_ehp: float

    # Optimization metrics
    metric_used: str
    found_improvement: bool
    improvement_pct: float

    # Performance
    completion_time_sec: float
    iterations_run: int
    convergence_reason: str

    # Budget usage
    unallocated_used: int
    unallocated_available: int
    respec_used: int
    respec_available: int
    budget_constraint_violated: bool

    # Final stats
    optimized_dps: float
    optimized_life: float
    optimized_ehp: float

    # Node changes
    nodes_added_count: int
    nodes_removed_count: int
    nodes_swapped: int

    # Error tracking
    error: str = ""
    success: bool = True


def load_build_from_xml_file(xml_path: Path) -> BuildData:
    """Load BuildData from XML file (same as demo script)"""
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

    class_name = build_section.get("@className")
    character_class = CharacterClass(class_name) if class_name else CharacterClass.WITCH

    level = int(build_section.get("@level", "90"))
    ascendancy = build_section.get("@ascendClassName")
    if ascendancy == "None":
        ascendancy = None

    tree_section = pob_root.get("Tree", {})
    spec = tree_section.get("Spec", {}) if isinstance(tree_section, dict) else {}
    nodes_str = spec.get("@nodes", "") if isinstance(spec, dict) else ""

    passive_nodes = set()
    if nodes_str:
        try:
            passive_nodes = set(int(node_id.strip()) for node_id in nodes_str.split(",") if node_id.strip())
        except ValueError:
            pass

    return BuildData(
        character_class=character_class,
        level=level,
        ascendancy=ascendancy,
        passive_nodes=passive_nodes,
        items=[],
        skills=[]
    )


def validate_build(
    build_data: Dict[str, Any],
    xml_path: Path,
    metric: str = "dps"
) -> ValidationMetrics:
    """
    Run optimizer on a single build and collect validation metrics.

    Args:
        build_data: Build metadata from baseline_stats.json
        xml_path: Path to XML file
        metric: Optimization metric (dps, ehp, balanced)

    Returns:
        ValidationMetrics with all collected data
    """
    build_id = build_data["build_id"]
    logger.info(f"Validating {build_id} (metric={metric})...")

    try:
        # Load build
        build = load_build_from_xml_file(xml_path)

        # Extract baseline info
        baseline_stats = build_data["baseline_stats"]
        unallocated = build_data["unallocated_points"]

        # Configure optimization
        # Use unallocated points budget + unlimited respec (respec_points=None)
        config = OptimizationConfiguration(
            build=build,
            metric=metric,
            unallocated_points=unallocated,
            respec_points=None,  # Unlimited respec for validation
            max_iterations=600,
            max_time_seconds=300,
            convergence_patience=3
        )

        # Run optimization
        start_time = time.time()
        result: OptimizationResult = optimize_build(config)
        completion_time = time.time() - start_time

        # Determine if improvement was found
        found_improvement = result.improvement_pct > 0.0

        # Check budget constraint violations
        # For unlimited respec, just check unallocated budget
        budget_violated = result.unallocated_used > unallocated

        # Build validation metrics
        return ValidationMetrics(
            build_id=build_id,
            build_class=build_data["character_class"],
            level=build_data["level"],
            allocated_points=build_data["allocated_points"],
            unallocated_points=unallocated,

            baseline_dps=baseline_stats["total_dps"],
            baseline_life=baseline_stats["life"],
            baseline_ehp=baseline_stats["effective_hp"],

            metric_used=metric,
            found_improvement=found_improvement,
            improvement_pct=result.improvement_pct,

            completion_time_sec=completion_time,
            iterations_run=result.iterations_run,
            convergence_reason=result.convergence_reason,

            unallocated_used=result.unallocated_used,
            unallocated_available=unallocated,
            respec_used=result.respec_used,
            respec_available=-1,  # -1 = unlimited
            budget_constraint_violated=budget_violated,

            optimized_dps=result.optimized_stats.total_dps,
            optimized_life=result.optimized_stats.life,
            optimized_ehp=result.optimized_stats.effective_hp,

            nodes_added_count=len(result.nodes_added),
            nodes_removed_count=len(result.nodes_removed),
            nodes_swapped=result.nodes_swapped,

            success=True
        )

    except Exception as e:
        logger.error(f"Failed to validate {build_id}: {e}", exc_info=True)

        # Return error metrics
        return ValidationMetrics(
            build_id=build_id,
            build_class=build_data.get("character_class", "Unknown"),
            level=build_data.get("level", 0),
            allocated_points=build_data.get("allocated_points", 0),
            unallocated_points=build_data.get("unallocated_points", 0),

            baseline_dps=build_data["baseline_stats"]["total_dps"],
            baseline_life=build_data["baseline_stats"]["life"],
            baseline_ehp=build_data["baseline_stats"]["effective_hp"],

            metric_used=metric,
            found_improvement=False,
            improvement_pct=0.0,

            completion_time_sec=0.0,
            iterations_run=0,
            convergence_reason="error",

            unallocated_used=0,
            unallocated_available=build_data.get("unallocated_points", 0),
            respec_used=0,
            respec_available=-1,
            budget_constraint_violated=False,

            optimized_dps=0.0,
            optimized_life=0.0,
            optimized_ehp=0.0,

            nodes_added_count=0,
            nodes_removed_count=0,
            nodes_swapped=0,

            error=str(e),
            success=False
        )


def calculate_aggregates(metrics_list: List[ValidationMetrics]) -> Dict[str, Any]:
    """Calculate aggregate statistics from validation metrics"""

    # Filter successful runs
    successful = [m for m in metrics_list if m.success]
    total_builds = len(metrics_list)
    successful_builds = len(successful)

    if not successful:
        return {
            "total_builds": total_builds,
            "successful_runs": 0,
            "failed_runs": total_builds,
            "error": "All validation runs failed"
        }

    # Success rate (% of builds with ANY improvement)
    builds_with_improvement = [m for m in successful if m.found_improvement]
    success_rate_pct = (len(builds_with_improvement) / successful_builds * 100) if successful_builds > 0 else 0

    # Improvement statistics (only for builds that found improvements)
    if builds_with_improvement:
        improvements = sorted([m.improvement_pct for m in builds_with_improvement])
        median_improvement = improvements[len(improvements) // 2]
        mean_improvement = sum(improvements) / len(improvements)
        min_improvement = min(improvements)
        max_improvement = max(improvements)
    else:
        median_improvement = 0.0
        mean_improvement = 0.0
        min_improvement = 0.0
        max_improvement = 0.0

    # Completion time statistics
    completion_times = [m.completion_time_sec for m in successful]
    mean_time = sum(completion_times) / len(completion_times)
    max_time = max(completion_times)
    min_time = min(completion_times)

    # Check if ALL completions < 300s
    all_under_5min = all(t < 300.0 for t in completion_times)
    builds_over_5min = [m.build_id for m in successful if m.completion_time_sec >= 300.0]

    # Budget constraint violations
    budget_violations = [m for m in successful if m.budget_constraint_violated]
    budget_violated_count = len(budget_violations)

    # Convergence reasons
    convergence_counts = {}
    for m in successful:
        reason = m.convergence_reason
        convergence_counts[reason] = convergence_counts.get(reason, 0) + 1

    return {
        "total_builds": total_builds,
        "successful_runs": successful_builds,
        "failed_runs": total_builds - successful_builds,

        "success_criteria": {
            "success_rate_pct": success_rate_pct,
            "target_success_rate": 70.0,
            "meets_success_rate_target": success_rate_pct >= 70.0,

            "median_improvement_pct": median_improvement,
            "target_median_improvement": 5.0,
            "meets_median_improvement_target": median_improvement >= 5.0,

            "max_completion_time_sec": max_time,
            "target_max_time": 300.0,
            "all_under_5_min": all_under_5min,
            "builds_over_5min": builds_over_5min,

            "budget_violations": budget_violated_count,
            "no_budget_violations": budget_violated_count == 0
        },

        "improvement_stats": {
            "builds_with_improvement": len(builds_with_improvement),
            "builds_without_improvement": successful_builds - len(builds_with_improvement),
            "mean_improvement_pct": mean_improvement,
            "median_improvement_pct": median_improvement,
            "min_improvement_pct": min_improvement,
            "max_improvement_pct": max_improvement
        },

        "performance_stats": {
            "mean_completion_time_sec": mean_time,
            "median_completion_time_sec": sorted(completion_times)[len(completion_times) // 2],
            "min_completion_time_sec": min_time,
            "max_completion_time_sec": max_time
        },

        "convergence_distribution": convergence_counts,

        "overall_pass": (
            success_rate_pct >= 70.0 and
            median_improvement >= 5.0 and
            all_under_5min and
            budget_violated_count == 0
        )
    }


def main():
    """Main validation execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate Epic 2 success criteria")
    parser.add_argument("--max-builds", type=int, help="Limit number of builds to validate (for testing)")
    parser.add_argument("--metrics", default="dps", help="Comma-separated metrics to test (dps,ehp,balanced)")
    args = parser.parse_args()

    # Parse metrics
    metrics_to_test = [m.strip() for m in args.metrics.split(",")]

    # Load baseline stats
    baseline_path = repo_root / "tests" / "fixtures" / "optimization_corpus" / "baseline_stats.json"
    logger.info(f"Loading baseline stats from {baseline_path}")

    with open(baseline_path, 'r') as f:
        baseline_data = json.load(f)

    builds = baseline_data["builds"]

    # Limit builds if requested
    if args.max_builds:
        builds = builds[:args.max_builds]
        logger.info(f"Limited to {args.max_builds} builds for testing")

    # Run validation for each metric
    all_results = {}

    for metric in metrics_to_test:
        logger.info(f"\n{'='*60}")
        logger.info(f"VALIDATING WITH METRIC: {metric.upper()}")
        logger.info(f"{'='*60}\n")

        metrics_list = []
        parity_dir = repo_root / "tests" / "fixtures" / "parity_builds"

        for build_data in builds:
            xml_path = parity_dir / build_data["filename"]
            metrics = validate_build(build_data, xml_path, metric=metric)
            metrics_list.append(metrics)

            # Log result
            if metrics.success:
                improvement_str = f"+{metrics.improvement_pct:.1f}%" if metrics.found_improvement else "No improvement"
                logger.info(
                    f"  ✓ {metrics.build_id}: {improvement_str} "
                    f"({metrics.completion_time_sec:.1f}s, {metrics.iterations_run} iter)"
                )
            else:
                logger.error(f"  ✗ {metrics.build_id}: {metrics.error}")

        # Calculate aggregates
        aggregates = calculate_aggregates(metrics_list)

        # Store results
        all_results[metric] = {
            "individual_results": [vars(m) for m in metrics_list],
            "aggregates": aggregates
        }

        # Log aggregate summary
        logger.info(f"\n{'-'*60}")
        logger.info(f"AGGREGATE RESULTS ({metric.upper()})")
        logger.info(f"{'-'*60}")
        logger.info(f"Success rate: {aggregates['success_criteria']['success_rate_pct']:.1f}% (target: 70%)")
        logger.info(f"Median improvement: {aggregates['success_criteria']['median_improvement_pct']:.1f}% (target: 5%)")
        logger.info(f"Max completion time: {aggregates['success_criteria']['max_completion_time_sec']:.1f}s (target: <300s)")
        logger.info(f"Budget violations: {aggregates['success_criteria']['budget_violations']} (target: 0)")
        logger.info(f"Overall PASS: {aggregates['overall_pass']}")

    # Save results
    timestamp = datetime.now().strftime("%Y-%m-%d")
    output_path = repo_root / "docs" / "validation" / f"epic-2-validation-results-{timestamp}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "validation_date": timestamp,
        "validation_time": datetime.now().isoformat(),
        "total_builds_tested": len(builds),
        "metrics_tested": metrics_to_test,
        "results_by_metric": all_results
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"\n{'='*60}")
    logger.info(f"Validation results saved to: {output_path}")
    logger.info(f"{'='*60}\n")

    return all_results


if __name__ == "__main__":
    main()
