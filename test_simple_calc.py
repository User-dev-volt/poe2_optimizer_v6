"""Test calculation with minimal build."""

from src.models.build_data import BuildData, CharacterClass
from src.calculator.build_calculator import calculate_build_stats

# Minimal build
build = BuildData(
    character_class=CharacterClass.RANGER,
    level=50,
    passive_nodes={26725, 26201, 48271}  # Some real passive node IDs from tree
)

print("Testing minimal build (no skills, no items)...")
try:
    stats = calculate_build_stats(build)
    print(f"SUCCESS! DPS={stats.total_dps:.2f}, Life={stats.life}")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
