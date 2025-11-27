"""Validate Epic 2 Success Criteria on Degraded Corpus

This script runs the optimizer on degraded builds to validate Epic 2 success criteria.

Success Criteria (from prep-sprint-status.yaml task-6):
- Success rate ≥ 70% (builds showing improvement)
- Median improvement ≥ 5%
- ALL completions < 300s (5 minutes)
- Budget constraints never violated
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

from src.models.build_data import BuildData, CharacterClass
from src.models.optimization_config import OptimizationConfiguration
from src.optimizer.hill_climbing import optimize_build
from src.parsers.xml_utils import parse_xml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_build_from_xml(xml_path: Path) -> BuildData:
    """Load BuildData from PoB XML file"""
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
        skills=[],
        tree_version="0_1"
    )


@dataclass
class ValidationMetrics:
    """Metrics for a single build optimization"""
    build_id: str
    difficulty: str

    # Baseline
    baseline_dps: float
    baseline_life: float
    baseline_ehp: float
    allocated_nodes: int
    unallocated_points: int

    # Optimization results
    found_improvement: bool
    improvement_pct: float
    optimized_dps: float
    optimized_life: float
    optimized_ehp: float

    # Performance
    completion_time_sec: float
    iterations_run: int
    convergence_reason: str

    # Budget
    unallocated_used: int
    respec_used: int
    budget_violated: bool

    # Changes
    nodes_added: int
    nodes_removed: int

    # Status
    success: bool
    error: str = ""


def validate_build(xml_path: Path, difficulty: str) -> ValidationMetrics:
    """Validate a single degraded build"""
    build_id = xml_path.stem

    try:
        # Parse build
        logger.info(f"  Parsing {build_id}...")
        build_data = load_build_from_xml(xml_path)

        allocated = len(build_data.passive_nodes)
        unallocated = max(0, build_data.level - 1 - allocated)

        # Configure optimization
        config = OptimizationConfiguration(
            build=build_data,
            metric="dps",
            unallocated_points=unallocated,
            respec_points=None,  # Unlimited respec
            max_iterations=100,
            max_time_seconds=300,
            convergence_patience=3
        )

        # Run optimization (this also calculates baseline stats)
        logger.info(f"    Running optimizer (baseline + optimization)...")
        start_time = time.time()
        result = optimize_build(config)
        completion_time = time.time() - start_time

        # Extract baseline stats from result
        baseline_stats = result.baseline_stats

        logger.info(f"    Baseline: DPS={baseline_stats.total_dps:.1f}, Life={baseline_stats.life:.0f}, "
                   f"EHP={baseline_stats.effective_hp:.0f}, Allocated={allocated}, Unallocated={unallocated}")

        # Check for improvement
        found_improvement = result.improvement_pct > 0.1  # >0.1% counts as improvement

        # Check budget violation
        budget_violated = (
            result.unallocated_used > unallocated or
            (result.respec_used > 0 and unallocated == 0)  # Used respec when no unallocated available
        )

        logger.info(f"    ✓ Complete: {result.improvement_pct:+.1f}% improvement in {completion_time:.1f}s "
                   f"({result.iterations_run} iter, {result.convergence_reason})")

        return ValidationMetrics(
            build_id=build_id,
            difficulty=difficulty,

            baseline_dps=baseline_stats.total_dps,
            baseline_life=baseline_stats.life,
            baseline_ehp=baseline_stats.effective_hp,
            allocated_nodes=allocated,
            unallocated_points=unallocated,

            found_improvement=found_improvement,
            improvement_pct=result.improvement_pct,
            optimized_dps=result.optimized_stats.total_dps,
            optimized_life=result.optimized_stats.life,
            optimized_ehp=result.optimized_stats.effective_hp,

            completion_time_sec=completion_time,
            iterations_run=result.iterations_run,
            convergence_reason=result.convergence_reason,

            unallocated_used=result.unallocated_used,
            respec_used=result.respec_used,
            budget_violated=budget_violated,

            nodes_added=len(result.nodes_added),
            nodes_removed=len(result.nodes_removed),

            success=True
        )

    except Exception as e:
        logger.error(f"    ✗ Failed: {e}", exc_info=True)
        return ValidationMetrics(
            build_id=build_id,
            difficulty=difficulty,
            baseline_dps=0, baseline_life=0, baseline_ehp=0,
            allocated_nodes=0, unallocated_points=0,
            found_improvement=False, improvement_pct=0,
            optimized_dps=0, optimized_life=0, optimized_ehp=0,
            completion_time_sec=0, iterations_run=0,
            convergence_reason="error",
            unallocated_used=0, respec_used=0, budget_violated=False,
            nodes_added=0, nodes_removed=0,
            success=False,
            error=str(e)
        )


def calculate_aggregates(metrics: List[ValidationMetrics]) -> Dict[str, Any]:
    """Calculate aggregate statistics"""
    total = len(metrics)
    successful = [m for m in metrics if m.success]
    successful_count = len(successful)

    if not successful:
        return {
            "total_builds": total,
            "successful_runs": 0,
            "failed_runs": total,
            "error": "All validations failed"
        }

    # Success rate: % with improvement
    with_improvement = [m for m in successful if m.found_improvement]
    success_rate_pct = (len(with_improvement) / successful_count * 100) if successful_count > 0 else 0

    # Improvement stats
    if with_improvement:
        improvements = sorted([m.improvement_pct for m in with_improvement])
        median_improvement = improvements[len(improvements) // 2]
        mean_improvement = sum(improvements) / len(improvements)
    else:
        median_improvement = 0
        mean_improvement = 0

    # Timing stats
    times = [m.completion_time_sec for m in successful]
    max_time = max(times) if times else 0
    mean_time = sum(times) / len(times) if times else 0

    # Budget violations
    budget_violations = sum(1 for m in successful if m.budget_violated)

    # Success criteria checks
    criteria_met = {
        "success_rate_70pct": success_rate_pct >= 70.0,
        "median_improvement_5pct": median_improvement >= 5.0,
        "all_under_300s": max_time < 300.0,
        "zero_budget_violations": budget_violations == 0
    }

    all_criteria_met = all(criteria_met.values())

    return {
        "total_builds": total,
        "successful_runs": successful_count,
        "failed_runs": total - successful_count,

        "success_rate_pct": round(success_rate_pct, 1),
        "builds_with_improvement": len(with_improvement),
        "builds_without_improvement": successful_count - len(with_improvement),

        "median_improvement_pct": round(median_improvement, 2),
        "mean_improvement_pct": round(mean_improvement, 2),

        "max_completion_time_sec": round(max_time, 1),
        "mean_completion_time_sec": round(mean_time, 1),

        "budget_violations": budget_violations,

        "criteria_met": criteria_met,
        "all_criteria_met": all_criteria_met
    }


def main():
    """Main validation execution"""
    degraded_dir = repo_root / "tests" / "fixtures" / "optimization_corpus" / "degraded"
    output_dir = repo_root / "docs" / "validation"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load manifest
    manifest_path = degraded_dir / "degraded_manifest.json"
    logger.info(f"Loading degraded corpus manifest: {manifest_path}")

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    logger.info(f"\nDegraded Corpus: {manifest['total_builds']} builds")
    logger.info(f"  HIP: {manifest['difficulty_distribution']['HIP']} builds")
    logger.info(f"  MIP: {manifest['difficulty_distribution']['MIP']} builds")
    logger.info(f"  LIP: {manifest['difficulty_distribution']['LIP']} builds")
    logger.info(f"\n{'='*60}")
    logger.info("VALIDATING EPIC 2 SUCCESS CRITERIA")
    logger.info(f"{'='*60}\n")

    # Run validation on each build
    all_metrics = []

    for build_info in manifest["builds"]:
        xml_path = degraded_dir / build_info["filename"]
        metrics = validate_build(xml_path, build_info["difficulty"])
        all_metrics.append(metrics)

    # Calculate aggregates
    logger.info(f"\n{'='*60}")
    logger.info("AGGREGATE RESULTS")
    logger.info(f"{'='*60}\n")

    aggregates = calculate_aggregates(all_metrics)

    # Print results
    logger.info(f"Total Builds: {aggregates['total_builds']}")
    logger.info(f"Successful Runs: {aggregates['successful_runs']}")
    logger.info(f"Failed Runs: {aggregates['failed_runs']}\n")

    # Check if all validations failed
    if aggregates.get('error'):
        logger.error(f"ERROR: {aggregates['error']}")
        logger.error("All validation runs failed. Check logs above for errors.")
        return 1

    logger.info(f"Success Rate: {aggregates['success_rate_pct']}% (target: ≥70%)")
    logger.info(f"  Builds with improvement: {aggregates['builds_with_improvement']}")
    logger.info(f"  Builds without improvement: {aggregates['builds_without_improvement']}\n")

    logger.info(f"Median Improvement: {aggregates['median_improvement_pct']}% (target: ≥5%)")
    logger.info(f"Mean Improvement: {aggregates['mean_improvement_pct']}%\n")

    logger.info(f"Max Completion Time: {aggregates['max_completion_time_sec']}s (target: <300s)")
    logger.info(f"Mean Completion Time: {aggregates['mean_completion_time_sec']}s\n")

    logger.info(f"Budget Violations: {aggregates['budget_violations']} (target: 0)\n")

    logger.info(f"{'='*60}")
    logger.info("SUCCESS CRITERIA")
    logger.info(f"{'='*60}\n")

    for criterion, met in aggregates['criteria_met'].items():
        status = "✓ PASS" if met else "✗ FAIL"
        logger.info(f"  {status} - {criterion}")

    logger.info(f"\n{'='*60}")
    if aggregates['all_criteria_met']:
        logger.info("✓ ALL SUCCESS CRITERIA MET - EPIC 2 VALIDATED")
    else:
        logger.info("✗ SOME CRITERIA NOT MET - REVIEW RESULTS")
    logger.info(f"{'='*60}\n")

    # Save results
    timestamp = datetime.now().strftime("%Y-%m-%d")
    results_file = output_dir / f"degraded-corpus-validation-{timestamp}.json"

    results = {
        "timestamp": datetime.now().isoformat(),
        "corpus": "degraded",
        "manifest": manifest,
        "individual_results": [asdict(m) for m in all_metrics],
        "aggregates": aggregates
    }

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to: {results_file}")

    return 0 if aggregates['all_criteria_met'] else 1


if __name__ == "__main__":
    sys.exit(main())
