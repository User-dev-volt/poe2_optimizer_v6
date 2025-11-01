"""
Performance profiling for PassiveTreeGraph.is_connected() method.

Story 2.2 will call is_connected() potentially 100,000+ times during optimization.
Target: <0.5ms per call to ensure 5-10 second optimization times.

Test scenarios:
1. Small allocated set (50 nodes) - early game builds
2. Medium allocated set (100 nodes) - mid-game builds
3. Large allocated set (150 nodes) - endgame builds
4. Worst case (200+ nodes) - fully optimized builds

Author: Bob (Scrum Master) - Prep Sprint Task #1
Date: 2025-10-27
"""

import sys
from pathlib import Path

# Add src to path for standalone execution
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
import random
from collections import defaultdict
from typing import Dict, List, Set

from calculator.passive_tree import get_passive_tree, PassiveTreeGraph


def generate_connected_subgraph(
    tree: PassiveTreeGraph,
    start_node: int,
    target_size: int
) -> Set[int]:
    """
    Generate a connected subgraph starting from start_node with target_size nodes.

    Uses BFS to gradually expand the allocated set, ensuring all nodes remain connected.
    This simulates a realistic passive tree allocation pattern.

    Args:
        tree: PassiveTreeGraph instance
        start_node: Starting node ID (class start)
        target_size: Number of nodes to allocate

    Returns:
        Set of allocated node IDs (connected subgraph)
    """
    allocated = {start_node}
    frontier = list(tree.get_neighbors(start_node))

    while len(allocated) < target_size and frontier:
        # Pick a random frontier node to allocate
        next_node = random.choice(frontier)
        allocated.add(next_node)
        frontier.remove(next_node)

        # Add new neighbors to frontier
        for neighbor in tree.get_neighbors(next_node):
            if neighbor not in allocated and neighbor not in frontier:
                frontier.append(neighbor)

    return allocated


def profile_is_connected(
    tree: PassiveTreeGraph,
    allocated_nodes: Set[int],
    start_node: int,
    num_checks: int = 1000
) -> Dict[str, float]:
    """
    Profile is_connected() performance with realistic workload.

    Simulates Story 2.2 neighbor generation checking connectivity:
    - Check if random nodes are reachable from start (typical optimization check)
    - Measure average, median, min, max times

    Args:
        tree: PassiveTreeGraph instance
        allocated_nodes: Set of allocated node IDs
        start_node: Starting node (class start)
        num_checks: Number of is_connected() calls to profile

    Returns:
        Dict with performance metrics (times in milliseconds)
    """
    # Generate random target nodes to check
    allocated_list = list(allocated_nodes)
    test_targets = [random.choice(allocated_list) for _ in range(num_checks)]

    # Warmup (1 call to ensure cache is primed)
    tree.is_connected(start_node, test_targets[0], allocated_nodes)

    # Actual profiling
    times = []
    for target in test_targets:
        start_time = time.perf_counter()
        result = tree.is_connected(start_node, target, allocated_nodes)
        end_time = time.perf_counter()
        times.append((end_time - start_time) * 1000)  # Convert to milliseconds

    # Calculate statistics
    times.sort()
    avg_time = sum(times) / len(times)
    median_time = times[len(times) // 2]
    min_time = times[0]
    max_time = times[-1]
    p95_time = times[int(len(times) * 0.95)]
    p99_time = times[int(len(times) * 0.99)]

    return {
        "avg_ms": avg_time,
        "median_ms": median_time,
        "min_ms": min_time,
        "max_ms": max_time,
        "p95_ms": p95_time,
        "p99_ms": p99_time,
        "total_calls": num_checks,
        "total_time_s": sum(times) / 1000,
    }


def estimate_optimization_time(checks_per_ms: float) -> Dict[str, float]:
    """
    Estimate Story 2.2 optimization time based on is_connected() performance.

    Story 2.2 will:
    - Generate 50-200 neighbors per iteration
    - Each neighbor requires 1-5 is_connected() checks
    - Run for 100-1000 iterations (depending on convergence)

    Estimate scenarios:
    - Optimistic: 100 iterations × 50 neighbors × 1 check = 5,000 checks
    - Typical: 300 iterations × 100 neighbors × 2 checks = 60,000 checks
    - Pessimistic: 1000 iterations × 200 neighbors × 5 checks = 1,000,000 checks

    Args:
        checks_per_ms: Average checks per millisecond

    Returns:
        Dict with estimated optimization times in seconds
    """
    optimistic_checks = 5_000
    typical_checks = 60_000
    pessimistic_checks = 1_000_000

    return {
        "optimistic_s": (optimistic_checks / checks_per_ms) / 1000,
        "typical_s": (typical_checks / checks_per_ms) / 1000,
        "pessimistic_s": (pessimistic_checks / checks_per_ms) / 1000,
    }


def main():
    """Run comprehensive performance profiling"""
    print("=" * 80)
    print("PassiveTreeGraph.is_connected() Performance Profile")
    print("=" * 80)
    print()

    # Load passive tree
    print("Loading passive tree...")
    tree = get_passive_tree()
    print(f"[OK] Loaded {tree.get_node_count()} nodes, {tree.get_edge_count()} edges")
    print()

    # Use Witch starting node for tests
    start_node = tree.class_start_nodes.get("Witch")
    if not start_node:
        print("ERROR: Could not find Witch starting node")
        return

    print(f"Using Witch starting node: {start_node}")
    print()

    # Test scenarios
    scenarios = [
        ("Small Build (50 nodes)", 50),
        ("Medium Build (100 nodes)", 100),
        ("Large Build (150 nodes)", 150),
        ("Endgame Build (200 nodes)", 200),
        ("Worst Case (300 nodes)", 300),
    ]

    results: List[Dict] = []

    for scenario_name, node_count in scenarios:
        print(f"Scenario: {scenario_name}")
        print("-" * 80)

        # Generate connected subgraph
        allocated = generate_connected_subgraph(tree, start_node, node_count)
        print(f"  Generated {len(allocated)} allocated nodes")

        # Profile is_connected()
        metrics = profile_is_connected(tree, allocated, start_node, num_checks=1000)

        print(f"  Average:   {metrics['avg_ms']:.4f} ms")
        print(f"  Median:    {metrics['median_ms']:.4f} ms")
        print(f"  Min:       {metrics['min_ms']:.4f} ms")
        print(f"  Max:       {metrics['max_ms']:.4f} ms")
        print(f"  P95:       {metrics['p95_ms']:.4f} ms")
        print(f"  P99:       {metrics['p99_ms']:.4f} ms")

        # Check against target (<0.5ms)
        if metrics['avg_ms'] < 0.5:
            status = "[PASS]"
        elif metrics['avg_ms'] < 1.0:
            status = "[MARGINAL]"
        else:
            status = "[FAIL]"

        print(f"  Status:    {status} (Target: <0.5ms avg)")
        print()

        results.append({
            "scenario": scenario_name,
            "node_count": len(allocated),
            "metrics": metrics,
        })

    # Summary and optimization impact
    print("=" * 80)
    print("Summary & Optimization Impact")
    print("=" * 80)
    print()

    # Use medium build (100 nodes) as representative
    medium_result = next(r for r in results if "Medium" in r["scenario"])
    avg_time_ms = medium_result["metrics"]["avg_ms"]
    checks_per_ms = 1 / avg_time_ms if avg_time_ms > 0 else 0

    print(f"Representative Performance (Medium Build, 100 nodes):")
    print(f"  Average time per check: {avg_time_ms:.4f} ms")
    print(f"  Checks per second: {checks_per_ms * 1000:.0f}")
    print()

    # Estimate Story 2.2 optimization times
    estimates = estimate_optimization_time(checks_per_ms)
    print("Estimated Story 2.2 Optimization Times:")
    print(f"  Optimistic (5K checks):     {estimates['optimistic_s']:.1f}s")
    print(f"  Typical (60K checks):       {estimates['typical_s']:.1f}s")
    print(f"  Pessimistic (1M checks):    {estimates['pessimistic_s']:.1f}s")
    print()

    # Recommendations
    print("=" * 80)
    print("Recommendations")
    print("=" * 80)
    print()

    if avg_time_ms < 0.5:
        print("[OK] Performance is EXCELLENT. Current BFS implementation sufficient.")
        print("  No optimization needed for Story 2.2.")
    elif avg_time_ms < 1.0:
        print("[WARNING] Performance is MARGINAL. Consider optimization for Story 2.2.")
        print("  Recommended: Implement memoization cache for frequently checked paths.")
    else:
        print("[CRITICAL] Performance is INSUFFICIENT. Optimization REQUIRED for Story 2.2.")
        print("  Options:")
        print("    A. Memoization: Cache reachable nodes from start (O(1) lookups)")
        print("    B. Union-Find: Pre-compute connected components")
        print("    C. Distance Matrix: Pre-compute all-pairs connectivity")
        print()
        print("  Recommended: Option A (memoization) - simplest, most effective")

    print()
    print("=" * 80)


if __name__ == "__main__":
    random.seed(42)  # Reproducible results
    main()
