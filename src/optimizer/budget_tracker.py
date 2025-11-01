"""Budget tracking for optimization with dual constraint enforcement

This module implements budget state management and constraint enforcement
for the hill climbing optimizer. It tracks two independent budget types:

1. Unallocated Points: Free passive points from leveling + quest rewards
   - Cost: 1 point per new node allocated
   - Budget enforcement: Hard limit, never exceeded

2. Respec Points: Cost to deallocate existing nodes for swaps
   - Cost: 1 point per node removed in swap operations
   - Budget enforcement: Hard limit or unlimited (None)

The module provides defense-in-depth budget validation:
- Budget checked at mutation generation time (neighbor_generator.py)
- Budget enforced before applying mutations (BudgetTracker.apply_mutation)
- Fail-fast with AssertionError on violations (indicates algorithm bug)

Architecture:
    - Pure state management module with zero external dependencies
    - Immutable TreeMutation objects (read-only cost fields)
    - BudgetState tracks current consumption
    - BudgetTracker provides validation and reporting

References:
    - Tech Spec Epic 2 - Section 4.3: Budget Tracker
    - Tech Spec Epic 2 - Section 3.3: Budget State Data Model
    - Story 2.4: Implement Dual Budget Constraint Tracking
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class BudgetState:
    """
    Dual budget constraint tracking for optimization.

    Tracks two independent budget types with hard enforcement:
    1. Unallocated points (free allocations): New nodes cost unallocated points
    2. Respec points (costly deallocations): Removing nodes costs respec points

    Invariants (enforced in __post_init__):
        - unallocated_used <= unallocated_available
        - respec_used <= respec_available (or unlimited if None)
        - All counters >= 0

    Attributes:
        unallocated_available: Total free points available
        unallocated_used: Free points already consumed
        respec_available: Total respec points (None = unlimited)
        respec_used: Respec points already consumed

    Example:
        >>> state = BudgetState(
        ...     unallocated_available=15,
        ...     unallocated_used=8,
        ...     respec_available=12,
        ...     respec_used=3
        ... )
        >>> state.can_allocate(7)  # True: 8 + 7 = 15 (at limit)
        >>> state.can_allocate(8)  # False: would exceed limit
        >>> state.can_respec(9)    # True: 3 + 9 = 12 (at limit)

        >>> # Unlimited respec mode
        >>> state = BudgetState(
        ...     unallocated_available=10,
        ...     unallocated_used=5,
        ...     respec_available=None,  # unlimited
        ...     respec_used=100
        ... )
        >>> state.can_respec(1000)  # True: unlimited mode
    """
    unallocated_available: int
    unallocated_used: int = 0
    respec_available: Optional[int] = None  # None = unlimited
    respec_used: int = 0

    def __post_init__(self):
        """Validate budget state invariants"""
        # Validate non-negative counters
        if self.unallocated_available < 0:
            raise ValueError(
                f"unallocated_available must be >= 0, got {self.unallocated_available}"
            )
        if self.unallocated_used < 0:
            raise ValueError(
                f"unallocated_used must be >= 0, got {self.unallocated_used}"
            )
        if self.respec_available is not None and self.respec_available < 0:
            raise ValueError(
                f"respec_available must be >= 0 or None, got {self.respec_available}"
            )
        if self.respec_used < 0:
            raise ValueError(
                f"respec_used must be >= 0, got {self.respec_used}"
            )

        # Validate budget constraints
        if self.unallocated_used > self.unallocated_available:
            raise ValueError(
                f"unallocated_used ({self.unallocated_used}) exceeds "
                f"unallocated_available ({self.unallocated_available})"
            )
        if self.respec_available is not None and self.respec_used > self.respec_available:
            raise ValueError(
                f"respec_used ({self.respec_used}) exceeds "
                f"respec_available ({self.respec_available})"
            )

    def can_allocate(self, count: int) -> bool:
        """
        Check if count unallocated points are available.

        Args:
            count: Number of unallocated points needed

        Returns:
            True if unallocated_used + count <= unallocated_available

        Example:
            >>> state = BudgetState(unallocated_available=10, unallocated_used=8)
            >>> state.can_allocate(1)  # True: 8 + 1 = 9 <= 10
            >>> state.can_allocate(2)  # True: 8 + 2 = 10 <= 10 (at limit)
            >>> state.can_allocate(3)  # False: 8 + 3 = 11 > 10
        """
        if count < 0:
            raise ValueError(f"count must be >= 0, got {count}")
        return self.unallocated_used + count <= self.unallocated_available

    def can_respec(self, count: int) -> bool:
        """
        Check if count respec points are available.

        Supports unlimited respec mode (respec_available=None).

        Args:
            count: Number of respec points needed

        Returns:
            True if respec_available is None (unlimited) or
            respec_used + count <= respec_available

        Example:
            >>> # Limited budget
            >>> state = BudgetState(
            ...     unallocated_available=10,
            ...     respec_available=12,
            ...     respec_used=10
            ... )
            >>> state.can_respec(1)  # True: 10 + 1 = 11 <= 12
            >>> state.can_respec(2)  # True: 10 + 2 = 12 <= 12 (at limit)
            >>> state.can_respec(3)  # False: 10 + 3 = 13 > 12

            >>> # Unlimited budget
            >>> state = BudgetState(unallocated_available=10, respec_available=None)
            >>> state.can_respec(999999)  # True: unlimited mode
        """
        if count < 0:
            raise ValueError(f"count must be >= 0, got {count}")

        # Unlimited respec mode
        if self.respec_available is None:
            return True

        # Limited respec mode
        return self.respec_used + count <= self.respec_available

    @property
    def unallocated_remaining(self) -> int:
        """Remaining free points"""
        return self.unallocated_available - self.unallocated_used

    @property
    def respec_remaining(self) -> Optional[int]:
        """Remaining respec points (None = unlimited)"""
        if self.respec_available is None:
            return None
        return self.respec_available - self.respec_used


# ============================================================================
# Budget Tracker
# ============================================================================

class BudgetTracker:
    """
    Budget constraint enforcement with dual tracking.

    Manages budget state and validates mutations against budget constraints
    before applying them. Provides defense-in-depth with fail-fast validation.

    Architecture:
        - Wraps BudgetState for mutation validation and updates
        - Validates TreeMutation cost fields against current budget
        - Updates budget counters after successful mutation application
        - Fail-fast with AssertionError on budget violations

    Usage:
        >>> from src.optimizer.neighbor_generator import TreeMutation
        >>> tracker = BudgetTracker(
        ...     unallocated_available=15,
        ...     respec_available=12
        ... )
        >>> mutation = TreeMutation(
        ...     mutation_type="add",
        ...     nodes_added={12345},
        ...     nodes_removed=set(),
        ...     unallocated_cost=1,
        ...     respec_cost=0
        ... )
        >>> if tracker.can_apply_mutation(mutation):
        ...     tracker.apply_mutation(mutation)
        ...     print(tracker.get_budget_summary())

    Attributes:
        _state: Internal BudgetState tracking consumption
    """

    def __init__(
        self,
        unallocated_available: int,
        respec_available: Optional[int] = None
    ):
        """
        Initialize budget tracker.

        Args:
            unallocated_available: Total free points available
            respec_available: Total respec points (None = unlimited)

        Raises:
            ValueError: If budget values are negative
        """
        self._state = BudgetState(
            unallocated_available=unallocated_available,
            unallocated_used=0,
            respec_available=respec_available,
            respec_used=0
        )
        logger.debug(
            f"BudgetTracker initialized: "
            f"unallocated={unallocated_available}, "
            f"respec={'unlimited' if respec_available is None else respec_available}"
        )

    def can_apply_mutation(self, mutation: Any) -> bool:
        """
        Check if mutation can be applied within budget constraints.

        Validates both unallocated and respec budgets. This method is
        designed to work with TreeMutation objects but uses Any type
        to avoid circular import dependencies.

        Args:
            mutation: TreeMutation with unallocated_cost and respec_cost fields

        Returns:
            True if both budget constraints allow the mutation

        Example:
            >>> mutation = TreeMutation(
            ...     mutation_type="add",
            ...     nodes_added={12345},
            ...     nodes_removed=set(),
            ...     unallocated_cost=1,
            ...     respec_cost=0
            ... )
            >>> tracker.can_apply_mutation(mutation)  # True if budget available
        """
        # Extract cost fields from mutation
        unallocated_cost = getattr(mutation, 'unallocated_cost', 0)
        respec_cost = getattr(mutation, 'respec_cost', 0)

        # Check both budget constraints
        can_afford_unallocated = self._state.can_allocate(unallocated_cost)
        can_afford_respec = self._state.can_respec(respec_cost)

        return can_afford_unallocated and can_afford_respec

    def apply_mutation(self, mutation: Any) -> None:
        """
        Apply mutation and update budget counters.

        Validates budget constraints before updating. Raises AssertionError
        on violations (fail-fast for algorithm bugs).

        Args:
            mutation: TreeMutation with unallocated_cost and respec_cost fields

        Raises:
            AssertionError: If mutation would exceed budget (algorithm bug)

        Example:
            >>> mutation = TreeMutation(mutation_type="add", ...)
            >>> tracker.apply_mutation(mutation)
            >>> summary = tracker.get_budget_summary()
            >>> print(f"Used: {summary['unallocated_used']}/{summary['unallocated_available']}")
        """
        # Extract cost fields
        unallocated_cost = getattr(mutation, 'unallocated_cost', 0)
        respec_cost = getattr(mutation, 'respec_cost', 0)

        # Fail-fast validation (defense-in-depth)
        assert self._state.can_allocate(unallocated_cost), (
            f"Budget violation: Attempted to allocate {unallocated_cost} points "
            f"but only {self._state.unallocated_remaining} remain "
            f"({self._state.unallocated_used}/{self._state.unallocated_available} used). "
            f"This indicates an algorithm bug - mutations should be pre-filtered."
        )
        assert self._state.can_respec(respec_cost), (
            f"Budget violation: Attempted to respec {respec_cost} points "
            f"but only {self._state.respec_remaining} remain "
            f"({self._state.respec_used}/{self._state.respec_available} used). "
            f"This indicates an algorithm bug - mutations should be pre-filtered."
        )

        # Update budget counters (create new state to maintain immutability)
        self._state = BudgetState(
            unallocated_available=self._state.unallocated_available,
            unallocated_used=self._state.unallocated_used + unallocated_cost,
            respec_available=self._state.respec_available,
            respec_used=self._state.respec_used + respec_cost
        )

        logger.debug(
            f"Applied mutation: unallocated_cost={unallocated_cost}, "
            f"respec_cost={respec_cost}. "
            f"New state: {self._state.unallocated_used}/{self._state.unallocated_available} "
            f"unallocated, {self._state.respec_used}/"
            f"{'unlimited' if self._state.respec_available is None else self._state.respec_available} respec"
        )

    def get_budget_summary(self) -> Dict[str, Any]:
        """
        Get current budget usage summary.

        Returns:
            Dict with keys:
                - unallocated_used: int
                - unallocated_available: int
                - unallocated_remaining: int
                - respec_used: int
                - respec_available: Optional[int] (None = unlimited)
                - respec_remaining: Optional[int] (None = unlimited)

        Example:
            >>> summary = tracker.get_budget_summary()
            >>> print(f"Budget: {summary['unallocated_used']}/{summary['unallocated_available']} "
            ...       f"unallocated, {summary['respec_used']}/"
            ...       f"{summary['respec_available'] or 'unlimited'} respec")
        """
        return {
            'unallocated_used': self._state.unallocated_used,
            'unallocated_available': self._state.unallocated_available,
            'unallocated_remaining': self._state.unallocated_remaining,
            'respec_used': self._state.respec_used,
            'respec_available': self._state.respec_available,
            'respec_remaining': self._state.respec_remaining
        }

    @property
    def state(self) -> BudgetState:
        """Get current budget state (read-only access)"""
        return self._state

    def format_budget_string(self) -> str:
        """
        Format budget usage as human-readable string.

        Returns:
            Formatted string showing budget consumption for both budgets

        Format:
            "Budget: {used}/{available} unallocated (FREE), {used}/{available|unlimited} respec"

        Example:
            >>> tracker = BudgetTracker(unallocated_available=15, respec_available=12)
            >>> # ... apply some mutations ...
            >>> print(tracker.format_budget_string())
            "Budget: 8/15 unallocated (FREE), 3/12 respec"

            >>> tracker_unlimited = BudgetTracker(unallocated_available=10, respec_available=None)
            >>> # ... apply some mutations ...
            >>> print(tracker_unlimited.format_budget_string())
            "Budget: 5/10 unallocated (FREE), 2/unlimited respec"
        """
        respec_display = (
            'unlimited'
            if self._state.respec_available is None
            else str(self._state.respec_available)
        )

        return (
            f"Budget: {self._state.unallocated_used}/{self._state.unallocated_available} "
            f"unallocated (FREE), {self._state.respec_used}/{respec_display} respec"
        )


# ============================================================================
# Helper Functions
# ============================================================================

def create_budget_progress_data(tracker: BudgetTracker) -> Dict[str, Any]:
    """
    Create budget data structure for progress callbacks.

    This function formats budget information for inclusion in optimization
    progress updates and final results. It provides both raw values and
    formatted display strings.

    Args:
        tracker: BudgetTracker instance with current budget state

    Returns:
        Dict with budget information suitable for progress callbacks:
            - summary: Dict with all budget values (from get_budget_summary)
            - display_string: Human-readable budget string
            - unallocated_used: int (for backward compatibility)
            - respec_used: int (for backward compatibility)

    Example:
        >>> tracker = BudgetTracker(unallocated_available=15, respec_available=12)
        >>> # ... optimization runs ...
        >>> progress_data = create_budget_progress_data(tracker)
        >>> print(progress_data['display_string'])
        "Budget: 8/15 unallocated (FREE), 3/12 respec"
        >>> print(f"Unallocated used: {progress_data['unallocated_used']}")
        "Unallocated used: 8"

    Integration:
        This function is called from hill_climbing.py progress callbacks:
        ```python
        progress_callback({
            'iteration': i,
            'current_score': score,
            'budget': create_budget_progress_data(budget_tracker),
            ...
        })
        ```
    """
    summary = tracker.get_budget_summary()

    return {
        'summary': summary,
        'display_string': tracker.format_budget_string(),
        # Backward compatibility: direct access to used counters
        'unallocated_used': summary['unallocated_used'],
        'respec_used': summary['respec_used']
    }
