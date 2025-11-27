"""Test calculation with single skill."""

from src.models.build_data import BuildData, CharacterClass, Skill
from src.calculator.build_calculator import calculate_build_stats

# Build with one simple skill
build = BuildData(
    character_class=CharacterClass.RANGER,
    level=50,
    passive_nodes={26725, 26201},
    skills=[
        Skill(
            name="Lightning Arrow",
            level=20,
            quality=0,
            enabled=True,
            skill_id="LightningArrowPlayer",
            support_gems=[]  # No supports
        )
    ]
)

print("Testing build with single skill (no supports)...")
try:
    stats = calculate_build_stats(build)
    print(f"SUCCESS! DPS={stats.total_dps:.2f}, Life={stats.life}")
except Exception as e:
    print(f"FAILED: {e}")

    # Check if it's the same error
    if "pairs" in str(e) and "nil" in str(e):
        print("\n⚠️ Same error as complex build - issue is with skill processing itself")
    import traceback
    traceback.print_exc()
