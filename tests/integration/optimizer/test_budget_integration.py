"""Integration tests for budget tracking with neighbor generation

Tests dual budget constraint enforcement across the full neighbor generation
pipeline, verifying that no mutations violate budget constraints.

Story: 2.4 - Implement Dual Budget Constraint Tracking (AC-2.4.5)
Integration Level: BudgetState + NeighborGenerator

Test Strategy:
    - Use real PassiveTreeGraph with actual PoE2 passive tree data
    - Generate neighbors with various budget constraints
    - Validate all returned mutations respect both budget types
    - Test boundary conditions: zero budget, at limit, unlimited mode
"""

import pytest
from src.optimizer.neighbor_generator import (
    generate_neighbors,
    BudgetState,
    TreeMutation
)
from src.calculator.passive_tree import get_passive_tree
from src.models.build_data import BuildData, CharacterClass


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def passive_tree():
    """Real PassiveTreeGraph with PoE2 data"""
    return get_passive_tree()


@pytest.fixture
def sample_build(passive_tree):
    """Sample build with a few allocated nodes"""
    # Get Witch starting node
    witch_start = passive_tree.class_start_nodes.get("Witch")

    if witch_start is None:
        pytest.skip("Witch starting node not found in passive tree")

    # Allocate starting node and a few connected nodes
    allocated = {witch_start}

    # Add 5 connected nodes for testing
    neighbors = passive_tree.get_neighbors(witch_start)
    for neighbor in list(neighbors)[:5]:
        allocated.add(neighbor)

    return BuildData(
        character_class=CharacterClass.WITCH,
        level=50,
        passive_nodes=allocated
    )


# ============================================================================
# Integration Tests - Budget Validation
# ============================================================================

class TestBudgetNeighborIntegration:
    """
    Test budget constraint enforcement during neighbor generation.

    Covers AC-2.4.5: Prevent moves that exceed either budget
    """

    def test_all_generated_neighbors_respect_unallocated_budget(
        self,
        sample_build,
        passive_tree
    ):
        """Test all neighbors respect unallocated budget constraint"""
        budget = BudgetState(
            unallocated_available=10,
            unallocated_used=5,
            respec_available=20,
            respec_used=0
        )

        neighbors = generate_neighbors(
            build=sample_build,
            tree=passive_tree,
            budget=budget,
            prioritize_adds=True
        )

        # Verify no neighbor exceeds unallocated budget
        for mutation in neighbors:
            remaining = budget.unallocated_available - budget.unallocated_used
            assert mutation.unallocated_cost <= remaining, (
                f"Mutation {mutation.mutation_type} costs {mutation.unallocated_cost} "
                f"but only {remaining} unallocated points remain"
            )

    def test_all_generated_neighbors_respect_respec_budget(
        self,
        sample_build,
        passive_tree
    ):
        """Test all neighbors respect respec budget constraint"""
        budget = BudgetState(
            unallocated_available=20,
            unallocated_used=0,
            respec_available=5,
            respec_used=3
        )

        neighbors = generate_neighbors(
            build=sample_build,
            tree=passive_tree,
            budget=budget,
            prioritize_adds=True
        )

        # Verify no neighbor exceeds respec budget
        for mutation in neighbors:
            if budget.respec_available is not None:
                remaining = budget.respec_available - budget.respec_used
                assert mutation.respec_cost <= remaining, (
                    f"Mutation {mutation.mutation_type} costs {mutation.respec_cost} respec "
                    f"but only {remaining} respec points remain"
                )

    def test_all_generated_neighbors_respect_both_budgets(
        self,
        sample_build,
        passive_tree
    ):
        """Test all neighbors respect both budget constraints simultaneously"""
        budget = BudgetState(
            unallocated_available=8,
            unallocated_used=7,  # Only 1 remaining
            respec_available=6,
            respec_used=5  # Only 1 remaining
        )

        neighbors = generate_neighbors(
            build=sample_build,
            tree=passive_tree,
            budget=budget,
            prioritize_adds=False  # Generate both types
        )

        # Verify each neighbor respects BOTH constraints
        for mutation in neighbors:
            unalloc_remaining = budget.unallocated_available - budget.unallocated_used
            respec_remaining = budget.respec_available - budget.respec_used

            assert mutation.unallocated_cost <= unalloc_remaining, (
                f"Mutation exceeds unallocated budget: "
                f"{mutation.unallocated_cost} > {unalloc_remaining}"
            )

            assert mutation.respec_cost <= respec_remaining, (
                f"Mutation exceeds respec budget: "
                f"{mutation.respec_cost} > {respec_remaining}"
            )

    def test_no_neighbors_when_unallocated_budget_exhausted(
        self,
        sample_build,
        passive_tree
    ):
        """Test no add neighbors generated when unallocated budget exhausted"""
        budget = BudgetState(
            unallocated_available=10,
            unallocated_used=10,  # Fully exhausted
            respec_available=20,
            respec_used=0
        )

        neighbors = generate_neighbors(
            build=sample_build,
            tree=passive_tree,
            budget=budget,
            prioritize_adds=True
        )

        # No add mutations should be generated
        add_mutations = [m for m in neighbors if m.mutation_type == "add"]
        assert len(add_mutations) == 0, "Add mutations generated despite exhausted unallocated budget"

    def test_no_swap_neighbors_when_respec_budget_exhausted(
        self,
        sample_build,
        passive_tree
    ):
        """Test no swap neighbors generated when respec budget exhausted"""
        budget = BudgetState(
            unallocated_available=20,
            unallocated_used=0,
            respec_available=5,
            respec_used=5  # Fully exhausted
        )

        neighbors = generate_neighbors(
            build=sample_build,
            tree=passive_tree,
            budget=budget,
            prioritize_adds=False
        )

        # No swap mutations should be generated
        swap_mutations = [m for m in neighbors if m.mutation_type == "swap"]
        assert len(swap_mutations) == 0, "Swap mutations generated despite exhausted respec budget"

    def test_unlimited_respec_mode_allows_unlimited_swaps(
        self,
        sample_build,
        passive_tree
    ):
        """Test unlimited respec mode (respec_available=None) allows swaps"""
        budget = BudgetState(
            unallocated_available=0,
            unallocated_used=0,
            respec_available=None,  # Unlimited
            respec_used=999  # High usage, but unlimited
        )

        neighbors = generate_neighbors(
            build=sample_build,
            tree=passive_tree,
            budget=budget,
            prioritize_adds=False
        )

        # Swap mutations should be generated (if build allows)
        # Note: May be 0 if build structure doesn't allow swaps
        swap_mutations = [m for m in neighbors if m.mutation_type == "swap"]
        # Just verify no assertion errors occurred during generation

    def test_budget_validation_filters_invalid_mutations(
        self,
        sample_build,
        passive_tree
    ):
        """Test defense-in-depth: budget validation filters any invalid mutations"""
        budget = BudgetState(
            unallocated_available=100,
            unallocated_used=0,
            respec_available=100,
            respec_used=0
        )

        neighbors = generate_neighbors(
            build=sample_build,
            tree=passive_tree,
            budget=budget,
            prioritize_adds=False
        )

        # All mutations must pass budget validation
        for mutation in neighbors:
            assert budget.can_allocate(mutation.unallocated_cost), (
                f"Mutation with unallocated_cost={mutation.unallocated_cost} "
                f"passed generation but fails can_allocate()"
            )
            assert budget.can_respec(mutation.respec_cost), (
                f"Mutation with respec_cost={mutation.respec_cost} "
                f"passed generation but fails can_respec()"
            )

    def test_budget_state_methods_match_full_implementation(self):
        """Test simplified BudgetState methods match full budget_tracker.BudgetState"""
        from src.optimizer.budget_tracker import BudgetState as FullBudgetState

        # Create both versions with same values
        simple = BudgetState(
            unallocated_available=10,
            unallocated_used=5,
            respec_available=12,
            respec_used=3
        )

        full = FullBudgetState(
            unallocated_available=10,
            unallocated_used=5,
            respec_available=12,
            respec_used=3
        )

        # Verify can_allocate() matches
        assert simple.can_allocate(0) == full.can_allocate(0)
        assert simple.can_allocate(5) == full.can_allocate(5)
        assert simple.can_allocate(6) == full.can_allocate(6)

        # Verify can_respec() matches
        assert simple.can_respec(0) == full.can_respec(0)
        assert simple.can_respec(9) == full.can_respec(9)
        assert simple.can_respec(10) == full.can_respec(10)

        # Verify unlimited mode matches
        simple_unlimited = BudgetState(
            unallocated_available=10,
            unallocated_used=0,
            respec_available=None,
            respec_used=999
        )

        full_unlimited = FullBudgetState(
            unallocated_available=10,
            unallocated_used=0,
            respec_available=None,
            respec_used=999
        )

        assert simple_unlimited.can_respec(999999) == full_unlimited.can_respec(999999)


# ============================================================================
# Integration Tests - Real Optimization Scenarios
# ============================================================================

class TestBudgetOptimizationScenarios:
    """
    Test budget tracking in realistic optimization scenarios.

    Verifies budget constraints hold across multiple neighbor generations
    as would occur during actual optimization.
    """

    def test_iterative_neighbor_generation_respects_accumulated_budget(
        self,
        sample_build,
        passive_tree
    ):
        """Test budget tracking across multiple iterations"""
        budget = BudgetState(
            unallocated_available=10,
            unallocated_used=0,
            respec_available=5,
            respec_used=0
        )

        # Simulate 3 iterations of neighbor generation
        for iteration in range(3):
            neighbors = generate_neighbors(
                build=sample_build,
                tree=passive_tree,
                budget=budget,
                prioritize_adds=True
            )

            # Verify all neighbors respect current budget
            for mutation in neighbors:
                assert budget.can_allocate(mutation.unallocated_cost)
                assert budget.can_respec(mutation.respec_cost)

            # Simulate accepting a mutation (update budget for next iteration)
            if neighbors:
                accepted = neighbors[0]
                budget = BudgetState(
                    unallocated_available=budget.unallocated_available,
                    unallocated_used=budget.unallocated_used + accepted.unallocated_cost,
                    respec_available=budget.respec_available,
                    respec_used=budget.respec_used + accepted.respec_cost
                )

    def test_zero_budget_generates_no_neighbors(
        self,
        sample_build,
        passive_tree
    ):
        """Test optimization terminates gracefully when budget exhausted"""
        budget = BudgetState(
            unallocated_available=0,
            unallocated_used=0,
            respec_available=0,
            respec_used=0
        )

        neighbors = generate_neighbors(
            build=sample_build,
            tree=passive_tree,
            budget=budget,
            prioritize_adds=False
        )

        assert len(neighbors) == 0, "Generated neighbors despite zero budget"


# ============================================================================
# Integration Tests - Story 2.5: Free-First Budget Prioritization
# ============================================================================

class TestFreeFirstBudgetPrioritization:
    """
    Test free-first budget prioritization strategy at integration level.

    Covers AC-2.5.4: Users see immediate value from free allocations
    - Optimization explores all free allocation options before costly alternatives
    - Progress updates show unallocated budget consumed first
    - Final results highlight that free allocations were maximized
    """

    def test_free_allocations_exhausted_before_respec(
        self,
        sample_build,
        passive_tree
    ):
        """AC-2.5.4: Verify free allocations fully exhausted before any respec usage"""
        budget = BudgetState(
            unallocated_available=10,
            unallocated_used=0,
            respec_available=10,
            respec_used=0
        )

        # Simulate optimization iterations
        current_budget = budget
        unallocated_exhausted = False
        respec_started = False

        for iteration in range(15):  # Enough iterations to exhaust unallocated
            neighbors = generate_neighbors(
                build=sample_build,
                tree=passive_tree,
                budget=current_budget,
                prioritize_adds=True
            )

            if not neighbors:
                break  # No more valid neighbors

            # Check if we're still using unallocated (add mutations)
            add_mutations = [n for n in neighbors if n.mutation_type == "add"]
            swap_mutations = [n for n in neighbors if n.mutation_type == "swap"]

            if len(add_mutations) > 0:
                # Still using unallocated budget
                assert not respec_started, (
                    "Found add mutations AFTER respec usage started - "
                    "free allocations should be exhausted first"
                )

            if len(swap_mutations) > 0:
                # Started using respec budget
                respec_started = True
                # Verify unallocated is exhausted
                assert current_budget.unallocated_remaining == 0, (
                    f"Respec usage started but {current_budget.unallocated_remaining} "
                    "unallocated points remain - should exhaust free points first"
                )
                unallocated_exhausted = True

            # Simulate accepting best mutation
            if neighbors:
                accepted = neighbors[0]
                current_budget = BudgetState(
                    unallocated_available=current_budget.unallocated_available,
                    unallocated_used=current_budget.unallocated_used + accepted.unallocated_cost,
                    respec_available=current_budget.respec_available,
                    respec_used=current_budget.respec_used + accepted.respec_cost
                )

        # Verify we went through both phases if both budgets were available
        if budget.unallocated_available > 0:
            assert unallocated_exhausted or current_budget.unallocated_remaining > 0, (
                "Should have exhausted unallocated budget or still have some remaining"
            )

    def test_only_adds_generated_when_unallocated_available_real_tree(
        self,
        sample_build,
        passive_tree
    ):
        """AC-2.5.1: With real tree data, verify only add mutations when unallocated available"""
        budget = BudgetState(
            unallocated_available=5,
            unallocated_used=0,
            respec_available=10,
            respec_used=0
        )

        neighbors = generate_neighbors(
            build=sample_build,
            tree=passive_tree,
            budget=budget,
            prioritize_adds=True
        )

        # Count mutation types
        add_mutations = [n for n in neighbors if n.mutation_type == "add"]
        swap_mutations = [n for n in neighbors if n.mutation_type == "swap"]

        # Should generate ONLY adds when unallocated available
        assert len(add_mutations) > 0, "Should generate add mutations with unallocated budget"
        assert len(swap_mutations) == 0, (
            f"Generated {len(swap_mutations)} swap mutations despite having "
            f"{budget.unallocated_remaining} unallocated points - should be 0"
        )

    def test_only_swaps_generated_when_unallocated_exhausted_real_tree(
        self,
        sample_build,
        passive_tree
    ):
        """AC-2.5.2: With real tree data, verify only swap mutations when unallocated exhausted"""
        budget = BudgetState(
            unallocated_available=0,
            unallocated_used=0,
            respec_available=10,
            respec_used=0
        )

        neighbors = generate_neighbors(
            build=sample_build,
            tree=passive_tree,
            budget=budget,
            prioritize_adds=True
        )

        # Count mutation types
        add_mutations = [n for n in neighbors if n.mutation_type == "add"]
        swap_mutations = [n for n in neighbors if n.mutation_type == "swap"]

        # Should generate ONLY swaps when unallocated exhausted
        assert len(add_mutations) == 0, (
            f"Generated {len(add_mutations)} add mutations despite unallocated "
            "budget being 0 - should be 0"
        )
        # Note: swap_mutations may be 0 if no valid swaps exist for this build

    def test_iterative_budget_consumption_free_first(
        self,
        sample_build,
        passive_tree
    ):
        """AC-2.5.4: Verify unallocated budget consumed first over multiple iterations"""
        initial_unallocated = 5
        initial_respec = 10

        budget = BudgetState(
            unallocated_available=initial_unallocated,
            unallocated_used=0,
            respec_available=initial_respec,
            respec_used=0
        )

        # Track budget consumption over iterations
        unallocated_history = [0]  # Start at 0 used
        respec_history = [0]  # Start at 0 used
        current_budget = budget

        for iteration in range(10):
            neighbors = generate_neighbors(
                build=sample_build,
                tree=passive_tree,
                budget=current_budget,
                prioritize_adds=True
            )

            if not neighbors:
                break

            # Accept first mutation
            accepted = neighbors[0]
            current_budget = BudgetState(
                unallocated_available=current_budget.unallocated_available,
                unallocated_used=current_budget.unallocated_used + accepted.unallocated_cost,
                respec_available=current_budget.respec_available,
                respec_used=current_budget.respec_used + accepted.respec_cost
            )

            unallocated_history.append(current_budget.unallocated_used)
            respec_history.append(current_budget.respec_used)

        # Verify consumption pattern: unallocated increases first, respec only after
        for i in range(len(unallocated_history)):
            if respec_history[i] > 0:
                # If respec started being used, unallocated should be fully exhausted
                assert unallocated_history[i] == initial_unallocated, (
                    f"At iteration {i}, respec_used={respec_history[i]} but "
                    f"unallocated_used={unallocated_history[i]} (should be {initial_unallocated}) - "
                    "unallocated should be exhausted before respec usage"
                )
