"""Aggregate Epic 2 Validation Results

Collects individual test results from pytest-xdist execution and generates
the final validation report with success criteria analysis.

Task 6 Success Criteria:
- Success rate >= 70%
- Median improvement >= 5%
- All completions < 5 minutes
- Zero budget violations

Usage:
    python scripts/aggregate_epic2_results.py <results_dir>

Author: Amelia (Dev Agent)
Date: 2025-11-26
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from statistics import median, mean
from typing import List, Dict, Any


def load_results(results_dir: Path) -> List[Dict[str, Any]]:
    """Load all individual result JSON files."""
    results = []

    if not results_dir.exists():
        print(f"ERROR: Results directory not found: {results_dir}")
        return results

    json_files = list(results_dir.glob("*.json"))

    if not json_files:
        print(f"WARNING: No result files found in {results_dir}")
        return results

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                result = json.load(f)
                results.append(result)
        except Exception as e:
            print(f"WARNING: Failed to load {json_file}: {e}")

    return results


def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze results and calculate summary statistics."""

    if not results:
        return {
            "error": "No results to analyze",
            "successful": 0,
            "errors": 0,
            "total": 0
        }

    # Separate successful vs error results
    successful = [r for r in results if r["status"] == "success"]
    errors = [r for r in results if r["status"] == "error"]

    # Calculate statistics for successful builds
    summary = {
        "total_builds": len(results),
        "successful": len(successful),
        "errors": len(errors),
        "success_rate_pct": 0,
        "median_improvement_pct": 0,
        "mean_improvement_pct": 0,
        "max_time_seconds": 0,
        "mean_time_seconds": 0,
        "budget_violations": 0,
        "total_nodes_allocated": 0,
        "median_nodes_added": 0,
        "builds_with_dps_improvement": 0,
        "builds_with_life_improvement": 0,
        "builds_with_mana_improvement": 0,
        "total_dps_gain": 0,
        "total_life_gain": 0,
        "total_mana_gain": 0,
        "task6_criteria": {
            "success_rate_70": False,
            "median_improvement_5": False,
            "all_under_5min": False,
            "zero_budget_violations": False,
            "overall_pass": False
        }
    }

    if not successful:
        return summary

    # DPS improvements
    improvements = [r["improvement_pct"] for r in successful]
    dps_improvements = [r for r in successful if r["improvement_pct"] > 0]
    life_improvements = [r for r in successful if r["life_change"] > 0]
    mana_improvements = [r for r in successful if r["mana_change"] > 0]

    # Time statistics
    times = [r["time_seconds"] for r in successful]

    # Node statistics
    nodes_added = [r["nodes_added"] for r in successful]

    # Budget violations (should be 0)
    budget_violations = len([r for r in successful if r["unallocated_used"] > 20])

    # DPS/Life/Mana gains
    total_dps_gain = sum(r["optimized_dps"] - r["baseline_dps"] for r in successful)
    total_life_gain = sum(r["life_change"] for r in successful)
    total_mana_gain = sum(r["mana_change"] for r in successful)

    # Populate summary
    summary["success_rate_pct"] = (len(dps_improvements) / len(successful) * 100) if successful else 0
    summary["median_improvement_pct"] = median(improvements) if improvements else 0
    summary["mean_improvement_pct"] = mean(improvements) if improvements else 0
    summary["max_time_seconds"] = max(times) if times else 0
    summary["mean_time_seconds"] = mean(times) if times else 0
    summary["budget_violations"] = budget_violations
    summary["total_nodes_allocated"] = sum(nodes_added)
    summary["median_nodes_added"] = median(nodes_added) if nodes_added else 0
    summary["builds_with_dps_improvement"] = len(dps_improvements)
    summary["builds_with_life_improvement"] = len(life_improvements)
    summary["builds_with_mana_improvement"] = len(mana_improvements)
    summary["total_dps_gain"] = total_dps_gain
    summary["total_life_gain"] = total_life_gain
    summary["total_mana_gain"] = total_mana_gain

    # Task 6 Acceptance Criteria
    success_rate_70 = summary["success_rate_pct"] >= 70
    median_improvement_5 = summary["median_improvement_pct"] >= 5
    all_under_5min = summary["max_time_seconds"] < 300
    zero_budget_violations = summary["budget_violations"] == 0

    summary["task6_criteria"] = {
        "success_rate_70": success_rate_70,
        "median_improvement_5": median_improvement_5,
        "all_under_5min": all_under_5min,
        "zero_budget_violations": zero_budget_violations,
        "overall_pass": all([success_rate_70, median_improvement_5, all_under_5min, zero_budget_violations])
    }

    return summary


def print_report(summary: Dict[str, Any], results: List[Dict[str, Any]]):
    """Print validation report to console."""
    print("\n" + "="*60)
    print("EPIC 2 VALIDATION REPORT")
    print("="*60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Corpus: tests/fixtures/realistic_builds/")
    print(f"Optimization Budget: 20 points per build")

    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    print(f"Total Builds: {summary['total_builds']}")
    print(f"Successful: {summary['successful']}")
    print(f"Errors: {summary['errors']}")

    if summary['successful'] > 0:
        print("\n" + "="*60)
        print("OPTIMIZATION STATISTICS")
        print("="*60)
        print(f"Success Rate: {summary['success_rate_pct']:.1f}% ({summary['builds_with_dps_improvement']}/{summary['successful']} builds improved)")
        print(f"Median Improvement: {summary['median_improvement_pct']:.2f}%")
        print(f"Mean Improvement: {summary['mean_improvement_pct']:.2f}%")
        print(f"\nNodes Allocated:")
        print(f"  Total: {summary['total_nodes_allocated']}")
        print(f"  Median per build: {summary['median_nodes_added']:.0f}")
        print(f"\nStat Improvements:")
        print(f"  DPS gains: {summary['builds_with_dps_improvement']} builds (+{summary['total_dps_gain']:,.1f} total)")
        print(f"  Life gains: {summary['builds_with_life_improvement']} builds (+{summary['total_life_gain']:,} total)")
        print(f"  Mana gains: {summary['builds_with_mana_improvement']} builds (+{summary['total_mana_gain']:,} total)")
        print(f"\nPerformance:")
        print(f"  Max time: {summary['max_time_seconds']:.1f}s (target: <300s)")
        print(f"  Mean time: {summary['mean_time_seconds']:.1f}s")
        print(f"  Budget violations: {summary['budget_violations']} (target: 0)")

    print("\n" + "="*60)
    print("TASK 6 ACCEPTANCE CRITERIA")
    print("="*60)

    criteria = summary['task6_criteria']

    def status_icon(passed): return "✅" if passed else "❌"

    print(f"{status_icon(criteria['success_rate_70'])} Success rate >= 70%: {summary['success_rate_pct']:.1f}%")
    print(f"{status_icon(criteria['median_improvement_5'])} Median improvement >= 5%: {summary['median_improvement_pct']:.2f}%")
    print(f"{status_icon(criteria['all_under_5min'])} All completions < 5 minutes: {summary['max_time_seconds']:.1f}s")
    print(f"{status_icon(criteria['zero_budget_violations'])} Zero budget violations: {summary['budget_violations']}")

    print("\n" + "="*60)
    if criteria['overall_pass']:
        print("✅ EPIC 2 VALIDATION: PASSED")
        print("All acceptance criteria met!")
    else:
        print("❌ EPIC 2 VALIDATION: FAILED")
        print("Some acceptance criteria not met (see above)")
    print("="*60 + "\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/aggregate_epic2_results.py <results_dir>")
        print("\nExample:")
        print("  python scripts/aggregate_epic2_results.py /tmp/pytest-of-user/pytest-current/epic2_results0")
        sys.exit(1)

    results_dir = Path(sys.argv[1])

    # Load results
    print(f"Loading results from: {results_dir}")
    results = load_results(results_dir)

    if not results:
        print("ERROR: No results found")
        sys.exit(1)

    print(f"Loaded {len(results)} result files")

    # Analyze
    summary = analyze_results(results)

    # Print report
    print_report(summary, results)

    # Save results
    output_file = Path("docs/validation/realistic-validation-results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "timestamp": datetime.now().isoformat(),
        "corpus": "tests/fixtures/realistic_builds/",
        "optimization_budget": 20,
        "max_time_seconds": 300,
        "summary": summary,
        "results": results
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Results saved to: {output_file}")

    # Exit code based on validation success
    exit_code = 0 if summary['task6_criteria']['overall_pass'] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
