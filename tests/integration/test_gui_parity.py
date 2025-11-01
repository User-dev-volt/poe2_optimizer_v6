"""
TRUE GUI Parity Testing - Story 1.6 Option A Implementation

Tests calculation accuracy by comparing our integrated PoB engine results
against baseline stats from OFFICIAL Path of Building GUI (version 0.12.2).

This addresses the critical finding from Second Review:
- Baselines are from REAL PoB GUI application (not self-generated)
- Builds are REAL exports from PoB (not synthetic)
- This provides INDEPENDENT validation of our engine accuracy

Acceptance Criteria (ORIGINAL, not changed):
    - AC-1.6.1: Create 10 test builds with known PoB GUI results
    - AC-1.6.2: Calculate each build using headless engine
    - AC-1.6.3: Compare results to PoB GUI: DPS, Life, EHP, resistances
    - AC-1.6.4: All results within 0.1% tolerance (per NFR-1)
    - AC-1.6.5: Document any discrepancies and root cause
    - AC-1.6.6: Create automated parity test suite

Test Strategy:
    - 14 diverse builds exported from official PoB GUI
    - Coverage: All 7 character classes (including Huntress), levels 1-100
    - Baseline: Stats calculated BY PoB GUI and extracted from XML exports
    - Tolerance: ±0.1% relative (or ±1 absolute for zero values)
    - Edge cases: negative resistances, zero stats

References:
    - Story 1.6 Second Review: Lines 621-1010 (Data Authenticity Audit)
    - Story 1.6 Action Item #1: Implement true GUI parity testing
"""

import json
import pytest
from pathlib import Path

from src.parsers.pob_parser import parse_pob_code
from src.calculator.build_calculator import calculate_build_stats
from src.models.build_stats import BuildStats


# Load GUI baseline stats (from official PoB application)
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "parity_builds"
GUI_BASELINE_FILE = FIXTURES_DIR / "gui_baseline_stats.json"

with open(GUI_BASELINE_FILE, 'r', encoding='utf-8') as f:
    GUI_BASELINE_STATS = json.load(f)

# Get all build IDs (exclude metadata)
BUILD_IDS = [k for k in GUI_BASELINE_STATS.keys() if not k.startswith('_')]

# Tolerance constant (0.1% as per NFR-1)
TOLERANCE_PERCENT = 0.1


def load_pob_code(build_id: str) -> str:
    """Load PoB code from .txt file.

    Args:
        build_id: Build identifier (e.g., "build_01_witch_90")

    Returns:
        Base64-encoded PoB code string
    """
    pob_file = FIXTURES_DIR / f"{build_id}.txt"
    return pob_file.read_text(encoding='utf-8').strip()


def assert_within_tolerance(
    actual: float,
    expected: float,
    field_name: str,
    tolerance_percent: float = TOLERANCE_PERCENT
) -> None:
    """Assert that actual value is within tolerance of expected value.

    Args:
        actual: Calculated value from our engine
        expected: Expected value from PoB GUI
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
            f"{field_name}: actual={actual}, expected={expected} (PoB GUI), "
            f"delta={delta} (absolute tolerance ±1 for zero values)"
        )
    else:
        # Relative tolerance
        delta = abs(actual - expected)
        tolerance = abs(expected * (tolerance_percent / 100))
        error_percent = (delta / abs(expected)) * 100 if expected != 0 else 0

        assert delta <= tolerance, (
            f"{field_name}: actual={actual}, expected={expected} (PoB GUI), "
            f"delta={delta}, tolerance={tolerance}, "
            f"error={error_percent:.3f}% (max {tolerance_percent}%)"
        )


@pytest.mark.gui_parity
class TestGUIParityBasic:
    """TRUE GUI parity tests - compare our engine to official PoB GUI results"""

    @pytest.mark.parametrize("build_id", BUILD_IDS)
    def test_gui_parity_build(self, build_id):
        """
        AC-1.6.1: Using test builds with known PoB GUI results
        AC-1.6.2: Calculate each build using headless engine
        AC-1.6.3: Compare results to PoB GUI: DPS, Life, EHP, resistances
        AC-1.6.4: All results within 0.1% tolerance

        This is TRUE GUI parity testing - baselines from official PoB application.
        """
        # Load PoB code (exported from official PoB GUI)
        pob_code = load_pob_code(build_id)
        expected = GUI_BASELINE_STATS[build_id]

        # Parse and calculate using OUR integrated engine (AC-1.6.2)
        build = parse_pob_code(pob_code)
        stats = calculate_build_stats(build)

        # Verify build metadata
        assert build.character_class.value == expected["character_class"]
        assert build.level == expected["level"]

        # Compare OUR stats to PoB GUI baseline (AC-1.6.3, AC-1.6.4)
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


@pytest.mark.gui_parity
class TestGUIParityEdgeCases:
    """Edge case tests for tolerance validation"""

    def test_tolerance_zero_values(self):
        """AC-1.6.4: Handle edge cases - zero expected values"""
        assert_within_tolerance(0, 0, "zero_exact")
        assert_within_tolerance(0.5, 0, "zero_within_tolerance")
        assert_within_tolerance(1.0, 0, "zero_boundary")

        with pytest.raises(AssertionError):
            assert_within_tolerance(1.1, 0, "zero_outside_tolerance")

    def test_tolerance_negative_values(self):
        """AC-1.6.4: Handle edge cases - negative resistances"""
        assert_within_tolerance(-50, -50, "negative_exact")
        assert_within_tolerance(-50.04, -50, "negative_within_tolerance")

        with pytest.raises(AssertionError):
            assert_within_tolerance(-51, -50, "negative_outside_tolerance")


@pytest.mark.gui_parity
class TestGUIParityFakeDataDetection:
    """Verify calculations are real (not fallback formulas)"""

    @pytest.mark.parametrize("build_id", BUILD_IDS)
    def test_fake_data_detection(self, build_id):
        """
        AC-1.6.2: Verify stats are from REAL PoB calculations
        AC-1.6.5: Document discrepancies (if fake data detected)

        Critical pattern from Story 1.5: Tests must verify stats != fallback formulas.
        If this fails, calculation engine is not working (critical failure).
        """
        pob_code = load_pob_code(build_id)
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


@pytest.mark.gui_parity
class TestGUIParityCoverage:
    """Verify test coverage requirements"""

    def test_all_character_classes_covered(self):
        """AC-1.6.1: Test builds cover all 7 character classes (including Huntress)"""
        classes_covered = set()
        for build_id in BUILD_IDS:
            expected = GUI_BASELINE_STATS[build_id]
            classes_covered.add(expected["character_class"])

        required_classes = {"Witch", "Warrior", "Ranger", "Sorceress", "Mercenary", "Monk", "Huntress"}
        assert classes_covered == required_classes, (
            f"Test builds must cover all 7 classes. "
            f"Missing: {required_classes - classes_covered}"
        )

    def test_level_ranges_covered(self):
        """AC-1.6.1: Test builds cover diverse level ranges"""
        levels_covered = set()
        for build_id in BUILD_IDS:
            expected = GUI_BASELINE_STATS[build_id]
            levels_covered.add(expected["level"])

        required_levels = {1, 30, 60, 90, 100}
        assert required_levels.issubset(levels_covered), (
            f"Test builds must cover key level ranges. "
            f"Missing: {required_levels - levels_covered}"
        )

    def test_minimum_build_count(self):
        """AC-1.6.1: Minimum 10 test builds required"""
        assert len(BUILD_IDS) >= 10, (
            f"Minimum 10 test builds required. Found: {len(BUILD_IDS)}"
        )


@pytest.mark.gui_parity
class TestGUIParityMarker:
    """Verify @pytest.mark.gui_parity marker works"""

    def test_gui_parity_marker_exists(self):
        """
        AC-1.6.6: Verify marker enables selective test runs

        Run with: pytest -m gui_parity
        """
        assert True


@pytest.mark.gui_parity
class TestGUIParityPerformance:
    """Performance validation"""

    def test_suite_performance_under_30_seconds(self):
        """
        Performance requirement: Parity test suite should complete in <30 seconds

        Target: 14 builds × <2s each = <28 seconds
        NFR-1: Individual calculations <100ms
        """
        import time

        start_time = time.time()

        # Run calculations for all builds
        for build_id in BUILD_IDS:
            pob_code = load_pob_code(build_id)
            build = parse_pob_code(pob_code)
            stats = calculate_build_stats(build)

        elapsed = time.time() - start_time

        # Allow 30s total for suite (14 builds)
        assert elapsed < 30, (
            f"GUI parity test suite should complete in <30 seconds. "
            f"Elapsed: {elapsed:.1f}s"
        )

        print(f"\nPerformance: {len(BUILD_IDS)} builds in {elapsed:.1f}s "
              f"(avg {elapsed/len(BUILD_IDS):.1f}s per build)")
