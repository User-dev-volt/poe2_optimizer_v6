"""Validate Epic 2 using tailored optimization corpus

Runs the same validation as validate_epic2_success.py but on Alec's tailored builds.

Usage:
    python scripts/validate_tailored_corpus.py [--metrics METRIC1,METRIC2]
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
    category: str  # HIP, MIP, LIP
    allocated_points: int

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
    respec_used: int

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
    """Load BuildData from XML file"""
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


def parse_filename(filename: str) -> str:
    """Extract category from filename"""
    parts = filename.replace('.xml', '').split('_')
    if len(parts) >= 2:
        category = parts[1].upper()  # hip, mip, lip
        return category
    return "UNKNOWN"


def validate_build(
    xml_path: Path,
    metric: str = "dps"
) -> ValidationMetrics:
    """Run optimizer on a single build and collect validation metrics"""
    filename = xml_path.name
    build_id = filename.replace('.xml', '')
    category = parse_filename(filename)

    logger.info(f"Validating {build_id} (category={category}, metric={metric})...")

    try:
        # Load build
        build = load_build_from_xml_file(xml_path)

        # For validation, use unlimited respec budget
        # This allows optimizer to try swapping nodes
        config = OptimizationConfiguration(
            build=build,
            metric=metric,
            unallocated_points=0,  # Assume no unallocated for now
            respec_points=None,  # Unlimited respec
            max_iterations=600,
            max_time_seconds=300,
            convergence_patience=3
        )

        # Run optimization
        from src.calculator.build_calculator import calculate_build_stats
        baseline_stats = calculate_build_stats(build)

        start_time = time.time()
        result: OptimizationResult = optimize_build(config)
        completion_time = time.time() - start_time

        # Determine if improvement was found
        found_improvement = result.improvement_pct > 0.0

        # Build validation metrics
        return ValidationMetrics(
            build_id=build_id,
            build_class=build.character_class.value,
            level=build.level,
            category=category,
            allocated_points=len(build.passive_nodes),

            baseline_dps=baseline_stats.total_dps,
            baseline_life=baseline_stats.life,
            baseline_ehp=baseline_stats.effective_hp,

            metric_used=metric,
            found_improvement=found_improvement,
            improvement_pct=result.improvement_pct,

            completion_time_sec=completion_time,
            iterations_run=result.iterations_run,
            convergence_reason=result.convergence_reason,

            unallocated_used=result.unallocated_used,
            respec_used=result.respec_used,

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

        return ValidationMetrics(
            build_id=build_id,
            build_class="Unknown",
            level=0,
            category=category,
            allocated_points=0,

            baseline_dps=0.0,
            baseline_life=0.0,
            baseline_ehp=0.0,

            metric_used=metric,
            found_improvement=False,
            improvement_pct=0.0,

            completion_time_sec=0.0,
            iterations_run=0,
            convergence_reason="error",

            unallocated_used=0,
            respec_used=0,

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
    """Calculate aggregate statistics"""
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

    # Success rate
    builds_with_improvement = [m for m in successful if m.found_improvement]
    success_rate_pct = (len(builds_with_improvement) / successful_builds * 100) if successful_builds > 0 else 0

    # Improvement statistics
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

    # Category breakdown
    category_stats = {}
    for category in ['HIP', 'MIP', 'LIP']:
        cat_builds = [m for m in successful if m.category == category]
        if cat_builds:
            cat_improvements = [m for m in cat_builds if m.found_improvement]
            cat_success_rate = (len(cat_improvements) / len(cat_builds) * 100) if cat_builds else 0
            cat_median = sorted([m.improvement_pct for m in cat_improvements])[len(cat_improvements)//2] if cat_improvements else 0
            category_stats[category] = {
                'total': len(cat_builds),
                'with_improvement': len(cat_improvements),
                'success_rate_pct': cat_success_rate,
                'median_improvement_pct': cat_median
            }

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
            "all_under_5_min": max_time < 300.0
        },

        "improvement_stats": {
            "builds_with_improvement": len(builds_with_improvement),
            "mean_improvement_pct": mean_improvement,
            "median_improvement_pct": median_improvement,
            "min_improvement_pct": min_improvement,
            "max_improvement_pct": max_improvement
        },

        "category_breakdown": category_stats,

        "overall_pass": (
            success_rate_pct >= 70.0 and
            median_improvement >= 5.0 and
            max_time < 300.0
        )
    }


def main():
    """Main validation execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate Epic 2 with tailored corpus")
    parser.add_argument("--metrics", default="dps", help="Comma-separated metrics (dps,ehp,balanced)")
    args = parser.parse_args()

    metrics_to_test = [m.strip() for m in args.metrics.split(",")]

    # Find tailored builds
    tailored_dir = repo_root / "tests" / "fixtures" / "parity_builds" / "tailored"

    if not tailored_dir.exists():
        logger.error(f"Tailored directory not found: {tailored_dir}")
        return

    xml_files = sorted(tailored_dir.glob("*.xml"))
    logger.info(f"Found {len(xml_files)} tailored builds")

    all_results = {}

    for metric in metrics_to_test:
        logger.info(f"\n{'='*60}")
        logger.info(f"VALIDATING WITH METRIC: {metric.upper()}")
        logger.info(f"{'='*60}\n")

        metrics_list = []

        for xml_path in xml_files:
            metrics = validate_build(xml_path, metric=metric)
            metrics_list.append(metrics)

            if metrics.success:
                improvement_str = f"+{metrics.improvement_pct:.1f}%" if metrics.found_improvement else "No improvement"
                logger.info(
                    f"  [{metrics.category}] {metrics.build_id}: {improvement_str} "
                    f"({metrics.completion_time_sec:.1f}s, {metrics.iterations_run} iter)"
                )
            else:
                logger.error(f"  [{metrics.category}] {metrics.build_id}: {metrics.error}")

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
        logger.info(f"Max time: {aggregates['success_criteria']['max_completion_time_sec']:.1f}s (target: <300s)")
        logger.info(f"Overall PASS: {aggregates['overall_pass']}")

        logger.info(f"\nBy Category:")
        for cat, stats in aggregates.get('category_breakdown', {}).items():
            logger.info(f"  {cat}: {stats['success_rate_pct']:.1f}% success, {stats['median_improvement_pct']:.1f}% median")

    # Save results
    timestamp = datetime.now().strftime("%Y-%m-%d")
    output_path = repo_root / "docs" / "validation" / f"tailored-corpus-validation-{timestamp}.json"

    output_data = {
        "validation_date": timestamp,
        "validation_time": datetime.now().isoformat(),
        "corpus_type": "tailored",
        "total_builds_tested": len(xml_files),
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
