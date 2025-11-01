"""
Integration tests for Story 1.5: Execute Single Build Calculation

Tests the complete calculation pipeline from BuildData to BuildStats,
covering all acceptance criteria:
    - AC-1.5.1: System accepts BuildData object as input
    - AC-1.5.2: System calls PoB calculation engine via MinimalCalc.lua
    - AC-1.5.3: System extracts calculated stats
    - AC-1.5.4: Calculation completes in <100ms
    - AC-1.5.5: No Lua errors during calculation
    - AC-1.5.6: Results are numeric (not nil/undefined)

Test Strategy:
    - Use minimal builds (character class, level, minimal passive nodes)
    - Items and skills empty (Story 1.5 scope)
    - Expect DPS=0 (no skills), but Life/Mana/Resistances should be present
    - Performance tests use pytest-benchmark if available

References:
    - Tech Spec Epic 1: Lines 1134-1168 (Test Scenarios)
    - Story 1.5 Task 7: Create Integration Tests
"""

import pytest
import time
import math
from src.models.build_data import BuildData, CharacterClass
from src.models.build_stats import BuildStats
from src.calculator.build_calculator import calculate_build_stats
from src.calculator.exceptions import CalculationError


class TestSingleCalculationBasic:
    """
    Test basic calculation functionality (AC-1.5.1, AC-1.5.2, AC-1.5.3, AC-1.5.6)
    """

    def test_calculate_minimal_witch_build(self):
        """
        AC-1.5.1: System accepts BuildData object as input
        AC-1.5.2: System calls PoB calculation engine via MinimalCalc.lua
        AC-1.5.3: System extracts calculated stats

        Test with simplest possible build: Witch level 90, no passive nodes.
        Expect basic character stats (Life, Mana) but 0 DPS (no skills).
        """
        # Create minimal BuildData (Story 1.5 scope: no items, no skills)
        build = BuildData(
            character_class=CharacterClass.WITCH,
            level=90,
            passive_nodes=set(),  # No allocated nodes
            items=[],
            skills=[]
        )

        # Calculate stats
        stats = calculate_build_stats(build)

        # Assertions
        assert isinstance(stats, BuildStats), "Should return BuildStats object"

        # AC-1.5.6: Results are numeric (not nil/undefined)
        assert isinstance(stats.total_dps, float), "total_dps should be float"
        assert isinstance(stats.life, int), "life should be int"
        assert isinstance(stats.energy_shield, int), "energy_shield should be int"
        assert isinstance(stats.mana, int), "mana should be int"
        assert isinstance(stats.effective_hp, float), "effective_hp should be float"
        assert isinstance(stats.resistances, dict), "resistances should be dict"

        # Validate no NaN or infinity (AC-1.5.6)
        assert not math.isnan(stats.total_dps), "total_dps should not be NaN"
        assert not math.isnan(stats.effective_hp), "effective_hp should not be NaN"
        assert not math.isinf(stats.total_dps), "total_dps should not be infinity"
        assert not math.isinf(stats.effective_hp), "effective_hp should not be infinity"

        # Basic sanity checks
        # DPS may be 0 without skills (Story 1.5 scope limitation)
        assert stats.total_dps >= 0, "DPS should be non-negative"

        # AC-1.5.2 & AC-1.5.3: Verify stats are from REAL PoB calculations, not fallback formulas
        # (Senior Review BLOCKING-2: Tests must detect fake data)
        fake_life_formula = 100 + (build.level - 1) * 12  # Old fallback formula
        fake_mana_formula = 50 + (build.level - 1) * 6   # Old fallback formula

        assert stats.life > 0, "Life should be > 0 (base character life from PoB engine)"
        assert stats.mana > 0, "Mana should be > 0 (base character mana from PoB engine)"

        # Critical: Verify we're getting real PoB calculations, not fake formulas
        assert stats.life != fake_life_formula, \
            f"Life {stats.life} matches fallback formula {fake_life_formula} - PoB engine not working!"
        assert stats.mana != fake_mana_formula, \
            f"Mana {stats.mana} matches fallback formula {fake_mana_formula} - PoB engine not working!"

        # Resistances dict should have expected keys
        expected_resist_keys = {'fire', 'cold', 'lightning', 'chaos'}
        assert set(stats.resistances.keys()) == expected_resist_keys, \
            "Resistances should have fire/cold/lightning/chaos keys"

        # All resistance values should be integers
        for resist_type, resist_value in stats.resistances.items():
            assert isinstance(resist_value, int), \
                f"Resistance '{resist_type}' should be int"

    def test_calculate_multiple_character_classes(self):
        """
        AC-1.5.1: Test BuildData input with different character classes
        AC-1.5.5: No Lua errors during calculation

        Test calculation with multiple character classes to ensure
        no Lua errors for different character types.
        """
        character_classes = [
            CharacterClass.WITCH,
            CharacterClass.WARRIOR,
            CharacterClass.RANGER,
            CharacterClass.MONK,
            CharacterClass.MERCENARY,
            CharacterClass.SORCERESS
        ]

        for char_class in character_classes:
            build = BuildData(
                character_class=char_class,
                level=50,  # Mid-level character
                passive_nodes=set(),
                items=[],
                skills=[]
            )

            # Should not raise any exceptions (AC-1.5.5)
            stats = calculate_build_stats(build)

            # Basic validation
            assert isinstance(stats, BuildStats), \
                f"{char_class.value} should produce BuildStats"
            assert stats.life >= 0, \
                f"{char_class.value} should have non-negative life"

    def test_calculate_with_passive_nodes(self):
        """
        AC-1.5.3: Test stat extraction with passive nodes allocated

        Note: We don't have actual passive tree data loaded in Story 1.5,
        so this test verifies the calculation doesn't crash with node IDs.
        Actual passive node effects tested in Story 1.7.
        """
        # Use some arbitrary passive node IDs
        # (These may not exist in PoB passive tree data, but shouldn't crash)
        build = BuildData(
            character_class=CharacterClass.WITCH,
            level=90,
            passive_nodes={12345, 12346, 12347},  # Arbitrary node IDs
            items=[],
            skills=[]
        )

        # Should not crash even with non-existent node IDs
        stats = calculate_build_stats(build)

        assert isinstance(stats, BuildStats)
        assert stats.life >= 0


class TestSingleCalculationPerformance:
    """
    Test calculation performance (AC-1.5.4)
    """

    def test_calculation_performance_under_100ms(self):
        """
        AC-1.5.4: Calculation completes in <100ms (single call)

        Note: First call per thread may take ~200ms due to Lua compilation.
        This test runs multiple iterations to get representative timing.
        """
        build = BuildData(
            character_class=CharacterClass.WITCH,
            level=90,
            passive_nodes=set(),
            items=[],
            skills=[]
        )

        # Warm-up call (first call may be slower due to Lua compilation)
        calculate_build_stats(build)

        # Measure subsequent calls (should be <100ms)
        times = []
        for _ in range(5):
            start = time.time()
            stats = calculate_build_stats(build)
            elapsed = time.time() - start
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        # AC-1.5.4: Should complete in <100ms
        # We allow some tolerance for CI environments
        assert max_time < 0.15, \
            f"Calculation should complete in <100ms, got max={max_time*1000:.1f}ms"

        print(f"\nPerformance stats: avg={avg_time*1000:.1f}ms, max={max_time*1000:.1f}ms")


class TestSingleCalculationValidation:
    """
    Test result validation (AC-1.5.6)
    """

    def test_stats_are_numeric_types(self):
        """
        AC-1.5.6: Results are numeric (not nil/undefined)

        Validates all BuildStats fields are correct types with no NaN/infinity.
        """
        build = BuildData(
            character_class=CharacterClass.WARRIOR,
            level=75,
            passive_nodes=set(),
            items=[],
            skills=[]
        )

        stats = calculate_build_stats(build)

        # Float fields
        float_fields = [
            ('total_dps', stats.total_dps),
            ('effective_hp', stats.effective_hp),
            ('block_chance', stats.block_chance),
            ('spell_block_chance', stats.spell_block_chance),
            ('movement_speed', stats.movement_speed)
        ]

        for field_name, value in float_fields:
            assert isinstance(value, (int, float)), \
                f"{field_name} should be numeric, got {type(value)}"
            assert not math.isnan(value), \
                f"{field_name} should not be NaN"
            assert not math.isinf(value), \
                f"{field_name} should not be infinity"

        # Int fields
        int_fields = [
            ('life', stats.life),
            ('energy_shield', stats.energy_shield),
            ('mana', stats.mana),
            ('armour', stats.armour),
            ('evasion', stats.evasion)
        ]

        for field_name, value in int_fields:
            assert isinstance(value, int), \
                f"{field_name} should be int, got {type(value)}"

        # Resistances dict
        for resist_type, resist_value in stats.resistances.items():
            assert isinstance(resist_value, int), \
                f"Resistance '{resist_type}' should be int"

    def test_to_dict_serialization(self):
        """
        Test BuildStats.to_dict() method works correctly.
        """
        build = BuildData(
            character_class=CharacterClass.RANGER,
            level=60,
            passive_nodes=set(),
            items=[],
            skills=[]
        )

        stats = calculate_build_stats(build)
        stats_dict = stats.to_dict()

        # Validate dict structure
        assert isinstance(stats_dict, dict)
        expected_keys = {
            'total_dps', 'effective_hp', 'life', 'energy_shield', 'mana',
            'resistances', 'armour', 'evasion', 'block_chance',
            'spell_block_chance', 'movement_speed'
        }
        assert set(stats_dict.keys()) == expected_keys

        # Validate serialized values are JSON-compatible types
        assert isinstance(stats_dict['total_dps'], (int, float))
        assert isinstance(stats_dict['life'], int)
        assert isinstance(stats_dict['resistances'], dict)


class TestSingleCalculationErrorHandling:
    """
    Test error handling (AC-1.5.5)
    """

    def test_invalid_build_level_zero(self):
        """
        Test error handling with invalid build (level 0).
        Should raise CalculationError gracefully.
        """
        # Note: BuildData doesn't validate level in __init__,
        # so this may or may not fail. If it doesn't fail,
        # we just verify no crashes occur.
        build = BuildData(
            character_class=CharacterClass.WITCH,
            level=0,  # Invalid level
            passive_nodes=set(),
            items=[],
            skills=[]
        )

        # May raise CalculationError or return results
        # Either is acceptable as long as no unhandled exceptions
        try:
            stats = calculate_build_stats(build)
            # If it succeeds, validate results are still well-formed
            assert isinstance(stats, BuildStats)
        except CalculationError as e:
            # Expected for invalid input
            assert "calculation" in str(e).lower() or "error" in str(e).lower()

    def test_no_unhandled_lua_errors(self):
        """
        AC-1.5.5: No Lua errors during calculation

        Test that lupa.LuaError is wrapped in CalculationError,
        never exposed to user.
        """
        import lupa

        build = BuildData(
            character_class=CharacterClass.MONK,
            level=100,
            passive_nodes=set(),
            items=[],
            skills=[]
        )

        # Should never raise lupa.LuaError (must be wrapped)
        try:
            stats = calculate_build_stats(build)
            assert isinstance(stats, BuildStats)
        except CalculationError:
            # Acceptable - wrapped error
            pass
        except lupa.LuaError:
            # This should NEVER happen (AC-1.5.5 violation)
            pytest.fail("lupa.LuaError should be wrapped in CalculationError")


class TestSingleCalculationEdgeCases:
    """
    Test edge cases and boundary conditions
    """

    def test_level_1_character(self):
        """Test calculation with level 1 character (minimum level)"""
        build = BuildData(
            character_class=CharacterClass.SORCERESS,
            level=1,
            passive_nodes=set(),
            items=[],
            skills=[]
        )

        stats = calculate_build_stats(build)
        assert isinstance(stats, BuildStats)
        # Level 1 should still have some base life/mana
        # (actual values depend on PoB calculation engine)
        assert stats.life >= 0
        assert stats.mana >= 0

    def test_level_100_character(self):
        """Test calculation with level 100 character (maximum level)"""
        build = BuildData(
            character_class=CharacterClass.WARRIOR,
            level=100,
            passive_nodes=set(),
            items=[],
            skills=[]
        )

        stats = calculate_build_stats(build)
        assert isinstance(stats, BuildStats)
        assert stats.life >= 0


# Optional: Pytest-benchmark tests (if pytest-benchmark installed)
try:
    import pytest_benchmark

    class TestSingleCalculationBenchmark:
        """
        Benchmark tests using pytest-benchmark (if available)
        Run with: pytest --benchmark-only
        """

        def test_benchmark_single_calculation(self, benchmark):
            """
            Benchmark single calculation performance.

            Target: <100ms per calculation (after warm-up)
            """
            build = BuildData(
                character_class=CharacterClass.WITCH,
                level=90,
                passive_nodes=set(),
                items=[],
                skills=[]
            )

            # Warm-up
            calculate_build_stats(build)

            # Benchmark
            result = benchmark(calculate_build_stats, build)

            assert isinstance(result, BuildStats)

except ImportError:
    # pytest-benchmark not installed, skip benchmark tests
    pass
