"""Analyze cProfile output to identify performance bottlenecks."""

import pstats
from pstats import SortKey

# Load profile stats
stats = pstats.Stats('profile.stats')

# Sort by cumulative time and show top 30 functions
print("=" * 80)
print("TOP 30 FUNCTIONS BY CUMULATIVE TIME")
print("=" * 80)
stats.sort_stats(SortKey.CUMULATIVE)
stats.print_stats(30)

print("\n" + "=" * 80)
print("TOP 30 FUNCTIONS BY TOTAL TIME (self time)")
print("=" * 80)
stats.sort_stats(SortKey.TIME)
stats.print_stats(30)

print("\n" + "=" * 80)
print("TOP 20 FUNCTIONS BY CALL COUNT")
print("=" * 80)
stats.sort_stats(SortKey.CALLS)
stats.print_stats(20)
