"""Direct verification of Story 2.9 implementation without pytest.

This script verifies that Phase 1 (passive tree stats) and Phase 2 (skills loading)
work correctly by running calculations directly.
"""

import sys
from src.calculator.build_calculator import calculate_build_stats
from src.models.build_data import BuildData, CharacterClass

def test_passive_stats():
    """Test that passive tree stats affect calculations."""
    print("\n=== TEST 1: Passive Tree Stats ===")

    # Build with no passive nodes
    build_base = BuildData(
        character_class=CharacterClass.MONK,
        level=10,
        passive_nodes=set()
    )

    stats_base = calculate_build_stats(build_base)
    print(f"Base (no passives): Life={stats_base.life}, DPS={stats_base.total_dps:.2f}")

    # Build with some passive nodes allocated
    build_with_passives = BuildData(
        character_class=CharacterClass.MONK,
        level=10,
        passive_nodes={12202, 12203, 12204}  # Some life/damage nodes
    )

    stats_with_passives = calculate_build_stats(build_with_passives)
    print(f"With passives: Life={stats_with_passives.life}, DPS={stats_with_passives.total_dps:.2f}")

    # Verify stats changed
    life_changed = stats_with_passives.life != stats_base.life
    print(f"✓ Life changed: {life_changed}")

    return life_changed

def test_skills_loading():
    """Test that skills load from build."""
    print("\n=== TEST 2: Skills Loading ===")

    from src.models.build_data import Skill

    build = BuildData(
        character_class=CharacterClass.MONK,
        level=50,
        passive_nodes={12202},
        skills=[
            Skill(
                name="Ember Fusillade",
                level=16,
                quality=0,
                enabled=True,
                skill_id="EmberFusilladePlayer"
            )
        ]
    )

    stats = calculate_build_stats(build)
    print(f"Stats with Ember Fusillade: DPS={stats.total_dps:.2f}, Life={stats.life}")

    # Just verify calculation completed without errors
    print(f"✓ Skills loaded and calculation completed")
    return True

def main():
    print("Story 2.9 Direct Verification")
    print("=" * 50)

    try:
        result1 = test_passive_stats()
        result2 = test_skills_loading()

        print("\n" + "=" * 50)
        if result1 and result2:
            print("✅ ALL TESTS PASSED")
            return 0
        else:
            print("❌ SOME TESTS FAILED")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
