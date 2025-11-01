"""Unit tests for budget tracking module

Tests dual budget constraint enforcement (unallocated + respec points)
with comprehensive coverage of boundary conditions, unlimited mode,
and fail-fast validation.

Story: 2.4 - Implement Dual Budget Constraint Tracking
Coverage Target: 80%+ line coverage

Test Organization:
    - TestBudgetState: Data model validation and boundary conditions
    - TestBudgetTracker: Budget enforcement and mutation application
    - TestBudgetReporting: Display formatting and progress data
"""

import pytest
from dataclasses import dataclass
from typing import Set

from src.optimizer.budget_tracker import (
    BudgetState,
    BudgetTracker,
    create_budget_progress_data
)


# ============================================================================
# Test Fixtures and Helpers
# ============================================================================

@dataclass
class MockTreeMutation:
    """Mock TreeMutation for testing (avoids circular import)"""
    mutation_type: str
    nodes_added: Set[int]
    nodes_removed: Set[int]
    unallocated_cost: int
    respec_cost: int


@pytest.fixture
def limited_budget_state():
    """BudgetState with limited budgets for both types"""
    return BudgetState(
        unallocated_available=10,
        unallocated_used=5,
        respec_available=8,
        respec_used=3
    )


@pytest.fixture
def unlimited_respec_state():
    """BudgetState with unlimited respec budget"""
    return BudgetState(
        unallocated_available=10,
        unallocated_used=5,
        respec_available=None,  # unlimited
        respec_used=100
    )


@pytest.fixture
def budget_tracker():
    """BudgetTracker with limited budgets"""
    return BudgetTracker(
        unallocated_available=15,
        respec_available=12
    )


@pytest.fixture
def unlimited_tracker():
    """BudgetTracker with unlimited respec"""
    return BudgetTracker(
        unallocated_available=10,
        respec_available=None
    )


# ============================================================================
# TestBudgetState - Data Model Validation
# ============================================================================

class TestBudgetState:
    """
    Test BudgetState data model and validation.

    Covers:
        - AC-2.4.1: Track unallocated_available and unallocated_used
        - AC-2.4.2: Track respec_available and respec_used (with None support)
    """

    # AC-2.4.1: Track unallocated budget
    def test_unallocated_tracking_initialization(self):
        """Test unallocated budget initializes correctly"""
        state = BudgetState(
            unallocated_available=15,
            unallocated_used=8
        )
        assert state.unallocated_available == 15
        assert state.unallocated_used == 8
        assert state.unallocated_remaining == 7

    def test_unallocated_default_used_zero(self):
        """Test unallocated_used defaults to 0"""
        state = BudgetState(unallocated_available=10)
        assert state.unallocated_used == 0
        assert state.unallocated_remaining == 10

    def test_unallocated_negative_available_rejected(self):
        """Test negative unallocated_available raises ValueError"""
        with pytest.raises(ValueError, match="unallocated_available must be >= 0"):
            BudgetState(unallocated_available=-1)

    def test_unallocated_negative_used_rejected(self):
        """Test negative unallocated_used raises ValueError"""
        with pytest.raises(ValueError, match="unallocated_used must be >= 0"):
            BudgetState(
                unallocated_available=10,
                unallocated_used=-1
            )

    def test_unallocated_overrun_rejected(self):
        """Test unallocated_used > available raises ValueError"""
        with pytest.raises(ValueError, match="unallocated_used.*exceeds"):
            BudgetState(
                unallocated_available=10,
                unallocated_used=11
            )

    # AC-2.4.2: Track respec budget with unlimited support
    def test_respec_tracking_initialization(self):
        """Test respec budget initializes correctly"""
        state = BudgetState(
            unallocated_available=10,
            respec_available=12,
            respec_used=5
        )
        assert state.respec_available == 12
        assert state.respec_used == 5
        assert state.respec_remaining == 7

    def test_respec_default_used_zero(self):
        """Test respec_used defaults to 0"""
        state = BudgetState(
            unallocated_available=10,
            respec_available=12
        )
        assert state.respec_used == 0
        assert state.respec_remaining == 12

    def test_respec_unlimited_mode(self):
        """Test respec_available=None enables unlimited mode"""
        state = BudgetState(
            unallocated_available=10,
            respec_available=None,
            respec_used=999
        )
        assert state.respec_available is None
        assert state.respec_used == 999
        assert state.respec_remaining is None

    def test_respec_negative_available_rejected(self):
        """Test negative respec_available raises ValueError"""
        with pytest.raises(ValueError, match="respec_available must be >= 0"):
            BudgetState(
                unallocated_available=10,
                respec_available=-1
            )

    def test_respec_negative_used_rejected(self):
        """Test negative respec_used raises ValueError"""
        with pytest.raises(ValueError, match="respec_used must be >= 0"):
            BudgetState(
                unallocated_available=10,
                respec_available=10,
                respec_used=-1
            )

    def test_respec_overrun_rejected(self):
        """Test respec_used > available raises ValueError"""
        with pytest.raises(ValueError, match="respec_used.*exceeds"):
            BudgetState(
                unallocated_available=10,
                respec_available=10,
                respec_used=11
            )

    # AC-2.4.3: Enforce unallocated constraint
    def test_can_allocate_boundary_conditions(self, limited_budget_state):
        """Test can_allocate() boundary: 0, available, available+1"""
        state = limited_budget_state  # 5/10 used

        # Can allocate 0 (trivial)
        assert state.can_allocate(0) is True

        # Can allocate up to remaining (5)
        assert state.can_allocate(1) is True
        assert state.can_allocate(4) is True
        assert state.can_allocate(5) is True  # exactly at limit

        # Cannot exceed remaining
        assert state.can_allocate(6) is False
        assert state.can_allocate(100) is False

    def test_can_allocate_at_limit(self):
        """Test can_allocate() when budget fully consumed"""
        state = BudgetState(
            unallocated_available=10,
            unallocated_used=10
        )
        assert state.can_allocate(0) is True
        assert state.can_allocate(1) is False

    def test_can_allocate_negative_count_rejected(self, limited_budget_state):
        """Test can_allocate() rejects negative count"""
        with pytest.raises(ValueError, match="count must be >= 0"):
            limited_budget_state.can_allocate(-1)

    # AC-2.4.4: Enforce respec constraint with unlimited mode
    def test_can_respec_boundary_conditions(self, limited_budget_state):
        """Test can_respec() boundary: 0, available, available+1"""
        state = limited_budget_state  # 3/8 used

        # Can respec 0 (trivial)
        assert state.can_respec(0) is True

        # Can respec up to remaining (5)
        assert state.can_respec(1) is True
        assert state.can_respec(4) is True
        assert state.can_respec(5) is True  # exactly at limit

        # Cannot exceed remaining
        assert state.can_respec(6) is False
        assert state.can_respec(100) is False

    def test_can_respec_unlimited_mode(self, unlimited_respec_state):
        """Test can_respec() always True in unlimited mode"""
        state = unlimited_respec_state
        assert state.can_respec(0) is True
        assert state.can_respec(1) is True
        assert state.can_respec(999999) is True

    def test_can_respec_at_limit(self):
        """Test can_respec() when budget fully consumed"""
        state = BudgetState(
            unallocated_available=10,
            respec_available=10,
            respec_used=10
        )
        assert state.can_respec(0) is True
        assert state.can_respec(1) is False

    def test_can_respec_negative_count_rejected(self, limited_budget_state):
        """Test can_respec() rejects negative count"""
        with pytest.raises(ValueError, match="count must be >= 0"):
            limited_budget_state.can_respec(-1)


# ============================================================================
# TestBudgetTracker - Budget Enforcement
# ============================================================================

class TestBudgetTracker:
    """
    Test BudgetTracker mutation validation and application.

    Covers:
        - AC-2.4.3: Enforce unallocated constraint
        - AC-2.4.4: Enforce respec constraint
        - AC-2.4.5: Prevent moves that exceed either budget
    """

    def test_initialization(self):
        """Test BudgetTracker initializes with correct state"""
        tracker = BudgetTracker(
            unallocated_available=15,
            respec_available=12
        )
        assert tracker.state.unallocated_available == 15
        assert tracker.state.unallocated_used == 0
        assert tracker.state.respec_available == 12
        assert tracker.state.respec_used == 0

    def test_initialization_unlimited_respec(self):
        """Test BudgetTracker supports unlimited respec mode"""
        tracker = BudgetTracker(
            unallocated_available=10,
            respec_available=None
        )
        assert tracker.state.respec_available is None

    # AC-2.4.5: Prevent moves that exceed either budget
    def test_can_apply_mutation_checks_both_budgets(self, budget_tracker):
        """Test can_apply_mutation() validates both budget constraints"""
        tracker = budget_tracker

        # Add mutation: costs unallocated only
        add_mutation = MockTreeMutation(
            mutation_type="add",
            nodes_added={12345},
            nodes_removed=set(),
            unallocated_cost=1,
            respec_cost=0
        )
        assert tracker.can_apply_mutation(add_mutation) is True

        # Swap mutation: costs respec only
        swap_mutation = MockTreeMutation(
            mutation_type="swap",
            nodes_added={12345},
            nodes_removed={67890},
            unallocated_cost=0,
            respec_cost=1
        )
        assert tracker.can_apply_mutation(swap_mutation) is True

    def test_can_apply_mutation_rejects_exceeding_unallocated(self, budget_tracker):
        """Test can_apply_mutation() rejects mutations exceeding unallocated budget"""
        tracker = budget_tracker  # 15 available

        # Exceed unallocated budget
        mutation = MockTreeMutation(
            mutation_type="add",
            nodes_added={12345},
            nodes_removed=set(),
            unallocated_cost=16,  # exceeds 15
            respec_cost=0
        )
        assert tracker.can_apply_mutation(mutation) is False

    def test_can_apply_mutation_rejects_exceeding_respec(self, budget_tracker):
        """Test can_apply_mutation() rejects mutations exceeding respec budget"""
        tracker = budget_tracker  # 12 respec available

        # Exceed respec budget
        mutation = MockTreeMutation(
            mutation_type="swap",
            nodes_added={12345},
            nodes_removed={67890},
            unallocated_cost=0,
            respec_cost=13,  # exceeds 12
        )
        assert tracker.can_apply_mutation(mutation) is False

    def test_can_apply_mutation_rejects_exceeding_either_budget(self, budget_tracker):
        """Test can_apply_mutation() rejects if either budget exceeded"""
        tracker = budget_tracker

        # Valid unallocated (5), invalid respec (13 > 12)
        mutation = MockTreeMutation(
            mutation_type="swap",
            nodes_added={12345},
            nodes_removed={67890},
            unallocated_cost=5,
            respec_cost=13
        )
        assert tracker.can_apply_mutation(mutation) is False

    # AC-2.4.4: Test apply_mutation updates counters correctly
    def test_apply_mutation_updates_unallocated(self, budget_tracker):
        """Test apply_mutation() correctly updates unallocated counter"""
        tracker = budget_tracker

        mutation = MockTreeMutation(
            mutation_type="add",
            nodes_added={12345},
            nodes_removed=set(),
            unallocated_cost=3,
            respec_cost=0
        )

        tracker.apply_mutation(mutation)

        assert tracker.state.unallocated_used == 3
        assert tracker.state.respec_used == 0

    def test_apply_mutation_updates_respec(self, budget_tracker):
        """Test apply_mutation() correctly updates respec counter"""
        tracker = budget_tracker

        mutation = MockTreeMutation(
            mutation_type="swap",
            nodes_added={12345},
            nodes_removed={67890},
            unallocated_cost=0,
            respec_cost=2
        )

        tracker.apply_mutation(mutation)

        assert tracker.state.unallocated_used == 0
        assert tracker.state.respec_used == 2

    def test_apply_mutation_updates_both_counters(self, budget_tracker):
        """Test apply_mutation() updates both counters for dual-cost mutations"""
        tracker = budget_tracker

        mutation = MockTreeMutation(
            mutation_type="swap",
            nodes_added={12345},
            nodes_removed={67890},
            unallocated_cost=1,
            respec_cost=1
        )

        tracker.apply_mutation(mutation)

        assert tracker.state.unallocated_used == 1
        assert tracker.state.respec_used == 1

    def test_apply_mutation_accumulates_costs(self, budget_tracker):
        """Test apply_mutation() accumulates costs across multiple mutations"""
        tracker = budget_tracker

        # Apply 3 add mutations
        for _ in range(3):
            mutation = MockTreeMutation(
                mutation_type="add",
                nodes_added={12345},
                nodes_removed=set(),
                unallocated_cost=2,
                respec_cost=0
            )
            tracker.apply_mutation(mutation)

        assert tracker.state.unallocated_used == 6
        assert tracker.state.respec_used == 0

    # AC-2.4.3 & AC-2.4.4: Fail-fast validation
    def test_apply_mutation_fails_fast_on_unallocated_overrun(self, budget_tracker):
        """Test apply_mutation() raises AssertionError on unallocated overrun"""
        tracker = budget_tracker

        mutation = MockTreeMutation(
            mutation_type="add",
            nodes_added={12345},
            nodes_removed=set(),
            unallocated_cost=16,  # exceeds 15
            respec_cost=0
        )

        with pytest.raises(AssertionError, match="Budget violation.*allocate"):
            tracker.apply_mutation(mutation)

    def test_apply_mutation_fails_fast_on_respec_overrun(self, budget_tracker):
        """Test apply_mutation() raises AssertionError on respec overrun"""
        tracker = budget_tracker

        mutation = MockTreeMutation(
            mutation_type="swap",
            nodes_added={12345},
            nodes_removed={67890},
            unallocated_cost=0,
            respec_cost=13  # exceeds 12
        )

        with pytest.raises(AssertionError, match="Budget violation.*respec"):
            tracker.apply_mutation(mutation)

    def test_apply_mutation_unlimited_respec_never_fails(self, unlimited_tracker):
        """Test apply_mutation() with unlimited respec never fails on respec"""
        tracker = unlimited_tracker

        # Apply large respec cost
        mutation = MockTreeMutation(
            mutation_type="swap",
            nodes_added={12345},
            nodes_removed={67890},
            unallocated_cost=0,
            respec_cost=999
        )

        tracker.apply_mutation(mutation)
        assert tracker.state.respec_used == 999


# ============================================================================
# TestBudgetReporting - Display and Progress Data
# ============================================================================

class TestBudgetReporting:
    """
    Test budget reporting and display formatting.

    Covers:
        - AC-2.4.6: Log budget usage in optimization progress
    """

    def test_get_budget_summary_structure(self, budget_tracker):
        """Test get_budget_summary() returns correct structure"""
        tracker = budget_tracker
        summary = tracker.get_budget_summary()

        # Verify all required keys present
        assert 'unallocated_used' in summary
        assert 'unallocated_available' in summary
        assert 'unallocated_remaining' in summary
        assert 'respec_used' in summary
        assert 'respec_available' in summary
        assert 'respec_remaining' in summary

    def test_get_budget_summary_values(self, budget_tracker):
        """Test get_budget_summary() returns correct values"""
        tracker = budget_tracker

        # Apply some mutations
        mutation = MockTreeMutation(
            mutation_type="add",
            nodes_added={12345},
            nodes_removed=set(),
            unallocated_cost=5,
            respec_cost=3
        )
        tracker.apply_mutation(mutation)

        summary = tracker.get_budget_summary()
        assert summary['unallocated_used'] == 5
        assert summary['unallocated_available'] == 15
        assert summary['unallocated_remaining'] == 10
        assert summary['respec_used'] == 3
        assert summary['respec_available'] == 12
        assert summary['respec_remaining'] == 9

    # AC-2.4.6: Format budget display strings
    def test_format_budget_string_limited_budgets(self, budget_tracker):
        """Test format_budget_string() with limited budgets"""
        tracker = budget_tracker

        # Apply mutation
        mutation = MockTreeMutation(
            mutation_type="add",
            nodes_added={12345},
            nodes_removed=set(),
            unallocated_cost=8,
            respec_cost=3
        )
        tracker.apply_mutation(mutation)

        result = tracker.format_budget_string()
        assert result == "Budget: 8/15 unallocated (FREE), 3/12 respec"

    def test_format_budget_string_unlimited_respec(self, unlimited_tracker):
        """Test format_budget_string() with unlimited respec"""
        tracker = unlimited_tracker

        # Apply mutation
        mutation = MockTreeMutation(
            mutation_type="swap",
            nodes_added={12345},
            nodes_removed={67890},
            unallocated_cost=5,
            respec_cost=100
        )
        tracker.apply_mutation(mutation)

        result = tracker.format_budget_string()
        assert result == "Budget: 5/10 unallocated (FREE), 100/unlimited respec"

    def test_format_budget_string_zero_budgets(self):
        """Test format_budget_string() with zero budgets"""
        tracker = BudgetTracker(
            unallocated_available=0,
            respec_available=0
        )

        result = tracker.format_budget_string()
        assert result == "Budget: 0/0 unallocated (FREE), 0/0 respec"

    def test_create_budget_progress_data_structure(self, budget_tracker):
        """Test create_budget_progress_data() returns correct structure"""
        tracker = budget_tracker

        progress_data = create_budget_progress_data(tracker)

        # Verify structure
        assert 'summary' in progress_data
        assert 'display_string' in progress_data
        assert 'unallocated_used' in progress_data
        assert 'respec_used' in progress_data

    def test_create_budget_progress_data_values(self, budget_tracker):
        """Test create_budget_progress_data() returns correct values"""
        tracker = budget_tracker

        # Apply mutation
        mutation = MockTreeMutation(
            mutation_type="add",
            nodes_added={12345},
            nodes_removed=set(),
            unallocated_cost=8,
            respec_cost=3
        )
        tracker.apply_mutation(mutation)

        progress_data = create_budget_progress_data(tracker)

        assert progress_data['unallocated_used'] == 8
        assert progress_data['respec_used'] == 3
        assert progress_data['display_string'] == "Budget: 8/15 unallocated (FREE), 3/12 respec"
        assert progress_data['summary']['unallocated_remaining'] == 7


# ============================================================================
# Test Story 2.5: Free-First Budget Reporting
# ============================================================================

class TestFreeFirstBudgetReporting:
    """
    Test suite for Story 2.5: Budget reporting with "FREE" indicator

    Tests acceptance criteria:
    - AC-2.5.3: Result breakdown shows "Used X of Y unallocated (FREE), Z of W respec"
    """

    def test_format_includes_free_label_with_usage(self):
        """AC-2.5.3: Budget string includes (FREE) label for unallocated budget"""
        tracker = BudgetTracker(
            unallocated_available=15,
            respec_available=12
        )

        # Apply mutation using unallocated budget
        mutation = MockTreeMutation(
            mutation_type="add",
            nodes_added={123},
            nodes_removed=set(),
            unallocated_cost=5,
            respec_cost=0
        )
        tracker.apply_mutation(mutation)

        result = tracker.format_budget_string()

        # Verify (FREE) label is present
        assert "(FREE)" in result
        assert result == "Budget: 5/15 unallocated (FREE), 0/12 respec"

    def test_format_includes_free_label_zero_unallocated(self):
        """AC-2.5.3: (FREE) label included even when unallocated budget is 0/0"""
        tracker = BudgetTracker(
            unallocated_available=0,
            respec_available=12
        )

        # Apply mutation using respec budget
        mutation = MockTreeMutation(
            mutation_type="swap",
            nodes_added={456},
            nodes_removed={123},
            unallocated_cost=0,
            respec_cost=8
        )
        tracker.apply_mutation(mutation)

        result = tracker.format_budget_string()

        # Verify (FREE) label is present even with 0/0
        assert "(FREE)" in result
        assert result == "Budget: 0/0 unallocated (FREE), 8/12 respec"

    def test_format_includes_free_label_with_unlimited_respec(self):
        """AC-2.5.3: (FREE) label works with unlimited respec mode"""
        tracker = BudgetTracker(
            unallocated_available=10,
            respec_available=None  # unlimited
        )

        # Apply mutation using both budgets
        mutation = MockTreeMutation(
            mutation_type="add",
            nodes_added={789},
            nodes_removed=set(),
            unallocated_cost=10,
            respec_cost=5
        )
        tracker.apply_mutation(mutation)

        result = tracker.format_budget_string()

        # Verify (FREE) label is present with unlimited respec
        assert "(FREE)" in result
        assert result == "Budget: 10/10 unallocated (FREE), 5/unlimited respec"

    def test_progress_data_includes_free_label(self):
        """AC-2.5.3: Progress callback data includes (FREE) in display_string"""
        tracker = BudgetTracker(
            unallocated_available=15,
            respec_available=12
        )

        # Apply mutation
        mutation = MockTreeMutation(
            mutation_type="add",
            nodes_added={123},
            nodes_removed=set(),
            unallocated_cost=8,
            respec_cost=4
        )
        tracker.apply_mutation(mutation)

        progress_data = create_budget_progress_data(tracker)

        # Verify (FREE) label in display_string
        assert "(FREE)" in progress_data['display_string']
        assert progress_data['display_string'] == "Budget: 8/15 unallocated (FREE), 4/12 respec"

    def test_free_label_format_consistency(self):
        """AC-2.5.3: (FREE) label format is consistent across all budget states"""
        # Test Case 1: Fully consumed unallocated, partial respec
        tracker1 = BudgetTracker(unallocated_available=15, respec_available=12)
        mutation1 = MockTreeMutation("add", {1}, set(), 15, 4)
        tracker1.apply_mutation(mutation1)
        assert tracker1.format_budget_string() == "Budget: 15/15 unallocated (FREE), 4/12 respec"

        # Test Case 2: Zero unallocated budget, partial respec
        tracker2 = BudgetTracker(unallocated_available=0, respec_available=12)
        mutation2 = MockTreeMutation("swap", {2}, {1}, 0, 8)
        tracker2.apply_mutation(mutation2)
        assert tracker2.format_budget_string() == "Budget: 0/0 unallocated (FREE), 8/12 respec"

        # Test Case 3: Partial unallocated, unlimited respec
        tracker3 = BudgetTracker(unallocated_available=10, respec_available=None)
        mutation3 = MockTreeMutation("add", {3}, set(), 5, 5)
        tracker3.apply_mutation(mutation3)
        assert tracker3.format_budget_string() == "Budget: 5/10 unallocated (FREE), 5/unlimited respec"

        # Test Case 4: No usage yet, zero respec
        tracker4 = BudgetTracker(unallocated_available=20, respec_available=10)
        assert tracker4.format_budget_string() == "Budget: 0/20 unallocated (FREE), 0/10 respec"

        # Verify (FREE) label present in all cases
        for tracker in [tracker1, tracker2, tracker3, tracker4]:
            assert "(FREE)" in tracker.format_budget_string()
