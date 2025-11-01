"""Quick cProfile run to identify remaining bottleneck."""
import cProfile
import pstats
from src.models.build_data import BuildData, CharacterClass
from src.calculator.build_calculator import calculate_build_stats

build = BuildData(
    character_class=CharacterClass.WITCH,
    level=90,
    passive_nodes=set(),
    items=[],
    skills=[]
)

# Warm up
calculate_build_stats(build)

# Profile 100 calculations (not 1000 - too slow)
def run_batch():
    for _ in range(100):
        calculate_build_stats(build)

profiler = cProfile.Profile()
profiler.enable()
run_batch()
profiler.disable()

# Print top 20 time consumers
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
print("\nTop 20 functions by cumulative time:")
stats.print_stats(20)

stats.sort_stats('tottime')
print("\nTop 20 functions by self time:")
stats.print_stats(20)
