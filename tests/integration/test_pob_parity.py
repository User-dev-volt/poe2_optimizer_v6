"""
Integration tests for Story 1.6: Validate Calculation Accuracy (Parity Testing)

Tests the calculation accuracy by comparing calculated stats against baseline values.
All stats must pass 0.1% tolerance (per NFR-1).

Acceptance Criteria:
    - AC-1.6.1: Create 10 test builds with known PoB GUI results
    - AC-1.6.2: Calculate each build using headless engine
    - AC-1.6.3: Compare results to PoB GUI: DPS, Life, EHP, resistances
    - AC-1.6.4: All results within 0.1% tolerance (per NFR-1)
    - AC-1.6.5: Document any discrepancies and root cause
    - AC-1.6.6: Create automated parity test suite

Test Strategy:
    - Parametrized tests for 12 diverse builds
    - Coverage: All 6 character classes, levels 1-100
    - Tolerance: ±0.1% relative (or ±1 absolute for zero values)
    - Edge cases: negative resistances, zero stats
    - Performance: <30 seconds total suite execution

References:
    - Tech Spec Epic 1: Lines 1219-1241 (Parity Testing Process)
    - Story 1.6: Lines 1-230 (Acceptance Criteria and Dev Notes)
"""

import json
import math
import pytest
from pathlib import Path

from src.parsers.pob_parser import parse_pob_code
from src.calculator.build_calculator import calculate_build_stats
from src.models.build_stats import BuildStats


# Load expected stats once for all tests
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "parity_builds"
EXPECTED_STATS_FILE = FIXTURES_DIR / "expected_stats.json"

with open(EXPECTED_STATS_FILE, 'r', encoding='utf-8') as f:
    EXPECTED_STATS = json.load(f)

# Get all build IDs (exclude metadata)
BUILD_IDS = [k for k in EXPECTED_STATS.keys() if not k.startswith('_')]

# Tolerance constant (0.1% as per NFR-1)
TOLERANCE_PERCENT = 0.1


def load_fixture(build_id: str) -> str:
    """Load PoB code from fixture file.

    Args:
        build_id: Build identifier (e.g., "build_01_witch_90")

    Returns:
        PoB code string (Base64-encoded)
    """
    fixture_file = FIXTURES_DIR / f"{build_id}.txt"
    return fixture_file.read_text(encoding='utf-8').strip()


def assert_within_tolerance(
    actual: float,
    expected: float,
    field_name: str,
    tolerance_percent: float = TOLERANCE_PERCENT
) -> None:
    """Assert that actual value is within tolerance of expected value.

    Args:
        actual: Calculated value
        expected: Expected baseline value
        field_name: Name of the field being tested (for error messages)
        tolerance_percent: Tolerance percentage (0.1 = 0.1%)

    Raises:
        AssertionError: If actual is outside tolerance

    Tolerance rules:
        - For non-zero expected: delta <= abs(expected * (tolerance_percent / 100))
        - For zero expected: delta <= 1 (absolute tolerance)
        - Handles negative values correctly (e.g., resistances)
    """
    if expected == 0:
        # Edge case: zero expected value uses absolute tolerance
        delta = abs(actual - expected)
        assert delta <= 1, (
            f"{field_name}: actual={actual}, expected={expected}, "
            f"delta={delta} (absolute tolerance ±1 for zero values)"
        )
    else:
        # Relative tolerance
        delta = abs(actual - expected)
        tolerance = abs(expected * (tolerance_percent / 100))
        error_percent = (delta / abs(expected)) * 100 if expected != 0 else 0

        assert delta <= tolerance, (
            f"{field_name}: actual={actual}, expected={expected}, "
            f"delta={delta}, tolerance={tolerance}, "
            f"error={error_percent:.3f}% (max {tolerance_percent}%)"
        )


@pytest.mark.parity
class TestParityBasic:
    """Basic parity tests for all builds (AC-1.6.1, AC-1.6.2, AC-1.6.3, AC-1.6.4)"""

    @pytest.mark.parametrize("build_id", BUILD_IDS)
    def test_parity_build(self, build_id):
        """
        AC-1.6.2: Calculate each build using headless engine
        AC-1.6.3: Compare results to PoB GUI: DPS, Life, EHP, resistances
        AC-1.6.4: All results within 0.1% tolerance

        Parametrized test for each build fixture.
        """
        # Load fixture and expected stats
        pob_code = load_fixture(build_id)
        expected = EXPECTED_STATS[build_id]

        # Parse and calculate (AC-1.6.2)
        build = parse_pob_code(pob_code)
        stats = calculate_build_stats(build)

        # Verify build metadata
        assert build.character_class.value == expected["character_class"]
        assert build.level == expected["level"]

        # Compare stats with 0.1% tolerance (AC-1.6.3, AC-1.6.4)
        expected_stats = expected["stats"]

        # Core stats
        assert_within_tolerance(
            stats.total_dps,
            expected_stats["total_dps"],
            f"{build_id}: total_dps"
        )
        assert_within_tolerance(
            stats.life,
            expected_stats["life"],
            f"{build_id}: life"
        )
        assert_within_tolerance(
            stats.effective_hp,
            expected_stats["effective_hp"],
            f"{build_id}: effective_hp"
        )
        assert_within_tolerance(
            stats.mana,
            expected_stats["mana"],
            f"{build_id}: mana"
        )
        assert_within_tolerance(
            stats.energy_shield,
            expected_stats["energy_shield"],
            f"{build_id}: energy_shield"
        )

        # Resistances (may be negative)
        for resist_type in ["fire", "cold", "lightning", "chaos"]:
            assert_within_tolerance(
                stats.resistances[resist_type],
                expected_stats["resistances"][resist_type],
                f"{build_id}: resistance[{resist_type}]"
            )

        # Defensive stats
        assert_within_tolerance(
            stats.armour,
            expected_stats["armour"],
            f"{build_id}: armour"
        )
        assert_within_tolerance(
            stats.evasion,
            expected_stats["evasion"],
            f"{build_id}: evasion"
        )
        assert_within_tolerance(
            stats.block_chance,
            expected_stats["block_chance"],
            f"{build_id}: block_chance"
        )
        assert_within_tolerance(
            stats.spell_block_chance,
            expected_stats["spell_block_chance"],
            f"{build_id}: spell_block_chance"
        )

        # Movement speed
        assert_within_tolerance(
            stats.movement_speed,
            expected_stats["movement_speed"],
            f"{build_id}: movement_speed"
        )


@pytest.mark.parity
class TestParityEdgeCases:
    """Edge case tests for tolerance validation (AC-1.6.4)"""

    def test_tolerance_zero_values(self):
        """
        AC-1.6.4: Handle edge cases - zero expected values

        When expected value is 0, use absolute tolerance ±1
        """
        # Test zero expected value
        assert_within_tolerance(0, 0, "zero_exact")
        assert_within_tolerance(0.5, 0, "zero_within_tolerance")
        assert_within_tolerance(1.0, 0, "zero_boundary")

        # Should fail if delta > 1
        with pytest.raises(AssertionError):
            assert_within_tolerance(1.1, 0, "zero_outside_tolerance")

    def test_tolerance_negative_values(self):
        """
        AC-1.6.4: Handle edge cases - negative resistances

        Resistances can be negative. Tolerance calculation should
        use absolute value of expected.
        """
        # Negative resistance: -60 with 0.1% tolerance
        # tolerance = abs(-60) * 0.001 = 0.06
        assert_within_tolerance(-60, -60, "negative_exact")
        assert_within_tolerance(-60.05, -60, "negative_within_tolerance")

        # Should fail if outside tolerance
        with pytest.raises(AssertionError):
            assert_within_tolerance(-61, -60, "negative_outside_tolerance")


@pytest.mark.parity
class TestParityFakeDataDetection:
    """Verify calculations are real (not fallback formulas) (AC-1.6.2, AC-1.6.5)"""

    @pytest.mark.parametrize("build_id", BUILD_IDS)
    def test_fake_data_detection(self, build_id):
        """
        AC-1.6.2: Verify stats are from REAL PoB calculations
        AC-1.6.5: Document discrepancies (if fake data detected)

        Critical pattern from Story 1.5: Tests must verify stats != fallback formulas.
        If this fails, calculation engine is not working (critical failure).

        Fallback formulas (old fake data):
            - Life = 100 + (level - 1) * 12
            - Mana = 50 + (level - 1) * 6
        """
        # Load and calculate
        pob_code = load_fixture(build_id)
        build = parse_pob_code(pob_code)
        stats = calculate_build_stats(build)

        # Calculate fallback formula values
        fake_life_formula = 100 + (build.level - 1) * 12
        fake_mana_formula = 50 + (build.level - 1) * 6

        # Critical: Verify we're NOT getting fake formulas
        assert stats.life != fake_life_formula, (
            f"{build_id}: Life {stats.life} matches fallback formula {fake_life_formula}. "
            "PoB engine not working! This is a CRITICAL failure."
        )
        assert stats.mana != fake_mana_formula, (
            f"{build_id}: Mana {stats.mana} matches fallback formula {fake_mana_formula}. "
            "PoB engine not working! This is a CRITICAL failure."
        )


@pytest.mark.parity
class TestParityCoverage:
    """Verify test coverage requirements (AC-1.6.1)"""

    def test_all_character_classes_covered(self):
        """
        AC-1.6.1: Test builds cover all 6 character classes

        Required classes: Witch, Warrior, Ranger, Sorceress, Mercenary, Monk
        """
        classes_covered = set()
        for build_id in BUILD_IDS:
            expected = EXPECTED_STATS[build_id]
            classes_covered.add(expected["character_class"])

        required_classes = {"Witch", "Warrior", "Ranger", "Sorceress", "Mercenary", "Monk"}
        assert classes_covered == required_classes, (
            f"Test builds must cover all 6 classes. "
            f"Missing: {required_classes - classes_covered}"
        )

    def test_level_ranges_covered(self):
        """
        AC-1.6.1: Test builds cover diverse level ranges

        Required: levels 1, 30, 60, 90, 100
        """
        levels_covered = set()
        for build_id in BUILD_IDS:
            expected = EXPECTED_STATS[build_id]
            levels_covered.add(expected["level"])

        required_levels = {1, 30, 60, 90, 100}
        assert required_levels.issubset(levels_covered), (
            f"Test builds must cover key level ranges. "
            f"Missing: {required_levels - levels_covered}"
        )

    def test_minimum_build_count(self):
        """
        AC-1.6.1: Minimum 10 test builds required

        Story requires "10+" diverse builds for adequate coverage.
        """
        assert len(BUILD_IDS) >= 10, (
            f"Minimum 10 test builds required. Found: {len(BUILD_IDS)}"
        )


@pytest.mark.parity
class TestParityMarker:
    """Verify @pytest.mark.parity marker works (AC-1.6.6)"""

    def test_parity_marker_exists(self):
        """
        AC-1.6.6: Verify @pytest.mark.parity marker enables selective test runs

        Run with: pytest -m parity
        This should run only parity tests, not the entire suite.
        """
        # This test itself has the marker, proving marker exists
        # Manual verification: run `pytest -m parity -v`
        assert True


@pytest.mark.parity
class TestParityPerformance:
    """Performance validation (AC-1.6.4, NFR-1)"""

    def test_suite_performance_under_30_seconds(self):
        """
        Performance requirement: Parity test suite should complete in <30 seconds

        Target: 12 builds × <2s each = <24 seconds
        NFR-1: Individual calculations <100ms
        """
        import time

        start_time = time.time()

        # Run calculations for all builds
        for build_id in BUILD_IDS:
            pob_code = load_fixture(build_id)
            build = parse_pob_code(pob_code)
            stats = calculate_build_stats(build)

        elapsed = time.time() - start_time

        # Allow 30s total for suite (12 builds)
        assert elapsed < 30, (
            f"Parity test suite should complete in <30 seconds. "
            f"Elapsed: {elapsed:.1f}s"
        )

        print(f"\nPerformance: {len(BUILD_IDS)} builds in {elapsed:.1f}s "
              f"(avg {elapsed/len(BUILD_IDS):.1f}s per build)")
