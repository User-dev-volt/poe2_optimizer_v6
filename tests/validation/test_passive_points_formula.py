"""Validation tests for PoE 2 passive points formula.

This test validates the passive points formula against PoE 2 mechanics:
- Characters gain 1 point per level (levels 2-100 = 99 points)
- Campaign quests provide 24 points total
- Total at level 100: 123 points

Formula: level + 23 = (level - 1) + 24

References:
- Maxroll: https://maxroll.gg/poe2/getting-started/permanent-stats-from-campaign
- PoE2 Wiki: https://www.poewiki.net/wiki/poe2wiki:Passive_Skill_Tree
- Validated: 2025-10-27 (PoE 2 live)
"""

import pytest
from src.models.build_data import BuildData, CharacterClass


class TestPassivePointsFormula:
    """Test suite for passive points calculation"""

    def test_level_1_character(self):
        """Level 1 character should have 24 points available (quest points only)"""
        build = BuildData(character_class=CharacterClass.WITCH, level=1, passive_nodes=set())
        assert build.unallocated_points == 24  # 1 + 23 = 24

    def test_level_100_character(self):
        """Level 100 character should have 123 points total"""
        build = BuildData(character_class=CharacterClass.WARRIOR, level=100, passive_nodes=set())
        assert build.unallocated_points == 123  # 100 + 23 = 123

    def test_typical_endgame_level_85(self):
        """Level 85 character should have 108 points total"""
        build = BuildData(character_class=CharacterClass.RANGER, level=85, passive_nodes=set())
        assert build.unallocated_points == 108  # 85 + 23 = 108

    def test_with_allocated_nodes(self):
        """Unallocated points should account for allocated nodes"""
        build = BuildData(
            character_class=CharacterClass.MONK,
            level=85,
            passive_nodes={1, 2, 3, 4, 5}  # 5 nodes allocated
        )
        assert build.allocated_point_count == 5
        assert build.unallocated_points == 103  # 108 - 5 = 103

    def test_fully_allocated_build(self):
        """Build with all points allocated should have 0 unallocated"""
        allocated_nodes = set(range(1, 124))  # 123 nodes
        build = BuildData(
            character_class=CharacterClass.SORCERESS,
            level=100,
            passive_nodes=allocated_nodes
        )
        assert build.allocated_point_count == 123
        assert build.unallocated_points == 0

    def test_over_allocated_build(self):
        """Build with more points than available should show 0 (clamped)"""
        # This shouldn't happen in valid PoB builds, but test defensive behavior
        allocated_nodes = set(range(1, 131))  # 130 nodes (impossible but defensive)
        build = BuildData(
            character_class=CharacterClass.HUNTRESS,
            level=100,
            passive_nodes=allocated_nodes
        )
        assert build.unallocated_points == 0  # max(0, 123 - 130) = 0

    def test_formula_breakdown_level_50(self):
        """Verify formula breakdown at level 50"""
        build = BuildData(character_class=CharacterClass.MERCENARY, level=50, passive_nodes=set())
        expected_max = 50 + 23  # 73 points
        assert build.unallocated_points == expected_max
        # Breakdown: (50 - 1) = 49 from leveling + 24 from quests = 73 total

    def test_formula_consistency_across_classes(self):
        """Formula should be same for all character classes"""
        for char_class in CharacterClass:
            build = BuildData(character_class=char_class, level=85, passive_nodes=set())
            assert build.unallocated_points == 108


class TestKnownEdgeCases:
    """Test edge cases and known limitations"""

    def test_formula_assumes_all_quests_completed(self):
        """Formula assumes character has completed all quest rewards.

        Note: This is a reasonable assumption for builds exported from PoB,
        as most users have completed the campaign by the time they're
        optimizing their passive tree. If auto-detection is wrong, users
        can manually override in the UI (Story 2.3 AC).
        """
        # Level 30 character - may not have all 24 quest points yet
        build = BuildData(character_class=CharacterClass.WITCH, level=30, passive_nodes=set())
        calculated = build.unallocated_points  # 30 + 23 = 53

        # In reality, at level 30 (mid Act 2), they might only have ~8-10 quest points
        # But we use the upper bound (24) as a reasonable default
        assert calculated == 53  # Upper bound formula

    def test_ascendancy_bonus_points_not_included(self):
        """Pathfinder ascendancy can get +6 bonus points, not included in base formula.

        Note: The base formula (level + 23) gives 123 points at level 100.
        Pathfinders with Traveller's Wisdom can have up to 129 points.
        This is an edge case that can be handled via manual override in UI.
        """
        build = BuildData(
            character_class=CharacterClass.RANGER,
            level=100,
            ascendancy="Pathfinder",
            passive_nodes=set()
        )
        assert build.unallocated_points == 123  # Base formula
        # Pathfinder bonus (+6) would require special handling in future


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
