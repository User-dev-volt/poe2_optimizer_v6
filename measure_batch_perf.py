"""
Quick batch performance measurement after Tasks 2-3 optimizations.
Measures 1000 calculations to verify AC-1.8.1 target (<500ms).
"""
import time
from src.models.build_data import BuildData, CharacterClass
from src.calculator.build_calculator import calculate_build_stats

def measure_batch_performance():
    """Run 1000 calculations and measure total time."""
    # Create sample build (same as tests)
    build = BuildData(
        character_class=CharacterClass.WITCH,
        level=90,
        passive_nodes=set(),
        items=[],
        skills=[]
    )

    # Warm up (first call has compilation overhead)
    print("Warming up...")
    calculate_build_stats(build)
    print("Warm-up complete.\n")

    # Measure batch of 1000
    print("Running batch of 1000 calculations...")
    start = time.perf_counter()

    for i in range(1000):
        calculate_build_stats(build)
        if (i + 1) % 100 == 0:
            elapsed = time.perf_counter() - start
            print(f"  {i + 1} calculations: {elapsed*1000:.1f}ms ({elapsed*1000/(i+1):.3f}ms per calc)")

    total_time = time.perf_counter() - start
    print(f"\nTotal time: {total_time*1000:.1f}ms")
    print(f"Per-calculation: {total_time:.4f}ms")
    print(f"Target: <500ms for 1000 calculations")

    if total_time < 0.5:
        print(f"[PASS] MEETS TARGET! ({total_time*1000:.1f}ms < 500ms)")
    else:
        print(f"[FAIL] EXCEEDS TARGET ({total_time*1000:.1f}ms > 500ms)")
        print(f"       Need to optimize by {(total_time - 0.5)*1000:.1f}ms")

    return total_time

if __name__ == "__main__":
    measure_batch_performance()
