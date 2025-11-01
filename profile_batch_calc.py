"""
Profile batch calculation to identify performance bottlenecks (Story 1.8 Task 1).

Usage:
    python -m cProfile -o profile.stats profile_batch_calc.py
    python -m pstats profile.stats

Then in pstats:
    sort cumtime
    stats 20
"""

from src.models.build_data import BuildData, CharacterClass
from src.calculator.build_calculator import calculate_build_stats

def main():
    # Create sample build
    build = BuildData(
        character_class=CharacterClass.WITCH,
        level=90,
        passive_nodes=set(),
        items=[],
        skills=[]
    )

    # Run batch of 100 calculations (enough to profile, faster than 1000)
    print("Running 100 calculations for profiling...")
    for i in range(100):
        stats = calculate_build_stats(build)
        if i % 10 == 0:
            print(f"  Iteration {i}: DPS={stats.total_dps:.2f}, Life={stats.life}")

    print("Profiling complete!")

if __name__ == "__main__":
    main()
