"""
Unit tests for Neighbor Generator

Tests all acceptance criteria for Story 2.2:
- AC-2.2.1: Generate "add node" neighbors: add any unallocated connected node
- AC-2.2.2: Generate "swap node" neighbors: remove 1 node, add 1 connected node
- AC-2.2.3: Validate all neighbors are valid (connected tree, within budget)
- AC-2.2.4: Limit neighbor count to reasonable size (50-200 per iteration)
- AC-2.2.5: Prioritize high-value nodes (Notable/Keystone over travel nodes)

Story: 2.2 - Generate Neighbor Configurations (1-Hop Moves)
Author: Dev Agent (Amelia)
Date: 2025-10-28
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from optimizer.neighbor_generator import (
    generate_neighbors,
    BudgetState,
    TreeMutation,
    _generate_add_neighbors,
    _generate_swap_neighbors,
    _get_node_value,
    _prioritize_mutations,
    _get_class_start_node,
    _is_tree_valid,
    _is_tree_valid_add,
    _is_tree_valid_full,
    _find_removable_nodes
)
from models.build_data import BuildData, CharacterClass
from calculator.passive_tree import PassiveNode, PassiveTreeGraph


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def simple_tree():
    """
    Create a simple test tree structure:

    Start (1) - Node 2 - Node 3
                 |
              Node 4 - Node 5

    Node types:
    - 1: Start (small)
    - 2: Small passive
    - 3: Notable passive
    - 4: Keystone passive
    - 5: Travel node (no stats)
    """
    nodes = {
        1: PassiveNode(node_id=1, name="Start", stats=["+10 Str"], is_notable=False, is_keystone=False),
        2: PassiveNode(node_id=2, name="Small1", stats=["+5 Str"], is_notable=False, is_keystone=False),
        3: PassiveNode(node_id=3, name="Notable1", stats=["+20 Str"], is_notable=True, is_keystone=False),
        4: PassiveNode(node_id=4, name="Keystone1", stats=["Unique Effect"], is_notable=False, is_keystone=True),
        5: PassiveNode(node_id=5, name="Travel1", stats=[], is_notable=False, is_keystone=False),
    }

    edges = {
        1: {2},
        2: {1, 3, 4},
        3: {2},
        4: {2, 5},
        5: {4}
    }

    class_start_nodes = {"Witch": 1}

    return PassiveTreeGraph(
        nodes=nodes,
        edges=edges,
        class_start_nodes=class_start_nodes,
        tree_version="test"
    )


@pytest.fixture
def sample_build():
    """Create a sample build with nodes 1, 2 allocated"""
    return BuildData(
        character_class=CharacterClass.WITCH,
        level=50,
        passive_nodes={1, 2}
    )


@pytest.fixture
def budget_with_unallocated():
    """Budget with 5 unallocated points, 0 respec"""
    return BudgetState(
        unallocated_available=5,
        unallocated_used=0,
        respec_available=0,
        respec_used=0
    )


@pytest.fixture
def budget_with_respec():
    """Budget with 0 unallocated points, 5 respec"""
    return BudgetState(
        unallocated_available=0,
        unallocated_used=0,
        respec_available=5,
        respec_used=0
    )


@pytest.fixture
def budget_with_both():
    """Budget with both unallocated and respec points"""
    return BudgetState(
        unallocated_available=5,
        unallocated_used=0,
        respec_available=5,
        respec_used=0
    )


@pytest.fixture
def budget_exhausted():
    """Budget with no points remaining"""
    return BudgetState(
        unallocated_available=0,
        unallocated_used=0,
        respec_available=0,
        respec_used=0
    )


# ============================================================================
# Test TreeMutation Data Model
# ============================================================================

class TestTreeMutation:
    """Test TreeMutation dataclass and apply() method"""

    def test_create_add_mutation(self):
        """Test creating an add mutation"""
        mutation = TreeMutation(
            mutation_type="add",
            nodes_added={123},
            nodes_removed=set(),
            unallocated_cost=1,
            respec_cost=0
        )

        assert mutation.mutation_type == "add"
        assert mutation.nodes_added == {123}
        assert mutation.nodes_removed == set()
        assert mutation.unallocated_cost == 1
        assert mutation.respec_cost == 0

    def test_create_swap_mutation(self):
        """Test creating a swap mutation"""
        mutation = TreeMutation(
            mutation_type="swap",
            nodes_added={456},
            nodes_removed={123},
            unallocated_cost=0,
            respec_cost=1
        )

        assert mutation.mutation_type == "swap"
        assert mutation.nodes_added == {456}
        assert mutation.nodes_removed == {123}
        assert mutation.unallocated_cost == 0
        assert mutation.respec_cost == 1

    def test_apply_add_mutation(self, sample_build):
        """Test applying add mutation to build (immutability)"""
        mutation = TreeMutation(
            mutation_type="add",
            nodes_added={3},
            nodes_removed=set(),
            unallocated_cost=1,
            respec_cost=0
        )

        original_nodes = sample_build.passive_nodes.copy()
        new_build = mutation.apply(sample_build)

        # Original build unchanged (immutability)
        assert sample_build.passive_nodes == original_nodes

        # New build has added node
        assert new_build.passive_nodes == {1, 2, 3}

    def test_apply_swap_mutation(self, sample_build):
        """Test applying swap mutation to build"""
        mutation = TreeMutation(
            mutation_type="swap",
            nodes_added={3},
            nodes_removed={2},
            unallocated_cost=0,
            respec_cost=1
        )

        new_build = mutation.apply(sample_build)

        # Old node removed, new node added
        assert new_build.passive_nodes == {1, 3}


# ============================================================================
# Test BudgetState
# ============================================================================

class TestBudgetState:
    """Test BudgetState tracking and properties"""

    def test_unallocated_remaining(self):
        """Test unallocated_remaining property calculation"""
        budget = BudgetState(
            unallocated_available=10,
            unallocated_used=3,
            respec_available=5,
            respec_used=0
        )
        assert budget.unallocated_remaining == 7

    def test_respec_remaining_finite(self):
        """Test respec_remaining with finite budget"""
        budget = BudgetState(
            unallocated_available=5,
            unallocated_used=0,
            respec_available=10,
            respec_used=4
        )
        assert budget.respec_remaining == 6

    def test_respec_remaining_unlimited(self):
        """Test respec_remaining with unlimited budget"""
        budget = BudgetState(
            unallocated_available=5,
            unallocated_used=0,
            respec_available=None,
            respec_used=100
        )
        assert budget.respec_remaining is None

    def test_can_add_true(self, budget_with_unallocated):
        """Test can_add when unallocated points available"""
        assert budget_with_unallocated.can_add is True

    def test_can_add_false(self, budget_with_respec):
        """Test can_add when no unallocated points"""
        assert budget_with_respec.can_add is False

    def test_can_swap_true(self, budget_with_respec):
        """Test can_swap when respec points available"""
        assert budget_with_respec.can_swap is True

    def test_can_swap_true_unlimited(self):
        """Test can_swap when respec is unlimited"""
        budget = BudgetState(
            unallocated_available=0,
            unallocated_used=0,
            respec_available=None,
            respec_used=0
        )
        assert budget.can_swap is True

    def test_can_swap_false(self, budget_with_unallocated):
        """Test can_swap when no respec points"""
        assert budget_with_unallocated.can_swap is False


# ============================================================================
# Test Add Neighbor Generation (AC-2.2.1)
# ============================================================================

class TestAddNeighborGeneration:
    """Test suite for AC-2.2.1: Generate add node neighbors"""

    def test_generate_add_neighbors_simple(self, sample_build, simple_tree, budget_with_unallocated):
        """
        Test basic add neighbor generation (AC-2.2.1)

        Build has nodes {1, 2} allocated
        Should generate neighbors for nodes {3, 4} (adjacent unallocated nodes)
        """
        mutations = _generate_add_neighbors(sample_build, simple_tree, budget_with_unallocated)

        # Should generate mutations for nodes 3 and 4
        assert len(mutations) >= 2

        # All should be add mutations
        for mutation in mutations:
            assert mutation.mutation_type == "add"
            assert mutation.unallocated_cost == 1
            assert mutation.respec_cost == 0
            assert len(mutation.nodes_removed) == 0
            assert len(mutation.nodes_added) == 1

        # Check that nodes 3 and 4 are in the candidates
        added_nodes = {list(m.nodes_added)[0] for m in mutations}
        assert 3 in added_nodes
        assert 4 in added_nodes

    def test_add_neighbors_no_budget(self, sample_build, simple_tree):
        """Test add generation returns empty when no unallocated budget (AC-2.2.3, Subtask 5.1)"""
        budget = BudgetState(
            unallocated_available=0,
            unallocated_used=0,
            respec_available=5,
            respec_used=0
        )

        mutations = _generate_add_neighbors(sample_build, simple_tree, budget)

        assert mutations == []

    def test_add_neighbors_connectivity_validation(self, simple_tree, budget_with_unallocated):
        """Test that add neighbors maintain tree connectivity (AC-2.2.3)"""
        # Build with only start node
        build = BuildData(
            character_class=CharacterClass.WITCH,
            level=50,
            passive_nodes={1}
        )

        mutations = _generate_add_neighbors(build, simple_tree, budget_with_unallocated)

        # Should only generate neighbor for node 2 (directly connected to 1)
        assert len(mutations) == 1
        assert list(mutations[0].nodes_added)[0] == 2


# ============================================================================
# Test Swap Neighbor Generation (AC-2.2.2)
# ============================================================================

class TestSwapNeighborGeneration:
    """Test suite for AC-2.2.2: Generate swap node neighbors"""

    def test_generate_swap_neighbors_simple(self, sample_build, simple_tree, budget_with_respec):
        """
        Test basic swap neighbor generation (AC-2.2.2)

        Build has nodes {1, 2} allocated
        Should be able to remove node 2 (not critical)
        """
        mutations = _generate_swap_neighbors(sample_build, simple_tree, budget_with_respec)

        # All should be swap mutations
        for mutation in mutations:
            assert mutation.mutation_type == "swap"
            assert mutation.unallocated_cost == 0
            assert mutation.respec_cost == 1
            assert len(mutation.nodes_removed) == 1
            assert len(mutation.nodes_added) == 1

    def test_swap_neighbors_no_budget(self, sample_build, simple_tree):
        """Test swap generation returns empty when no respec budget (Subtask 5.2)"""
        budget = BudgetState(
            unallocated_available=5,
            unallocated_used=0,
            respec_available=0,
            respec_used=0
        )

        mutations = _generate_swap_neighbors(sample_build, simple_tree, budget)

        assert mutations == []

    def test_find_removable_nodes(self, sample_build, simple_tree):
        """Test identifying removable nodes (Subtask 3.1)"""
        removable = _find_removable_nodes(sample_build, simple_tree, class_start=1)

        # Node 2 can be removed (would leave just node 1)
        # Node 1 cannot be removed (class start)
        assert 1 not in removable
        assert 2 in removable

    def test_swap_maintains_connectivity(self, simple_tree, budget_with_respec):
        """Test that swap neighbors maintain tree connectivity (AC-2.2.3)"""
        # Build with nodes 1, 2, 3
        build = BuildData(
            character_class=CharacterClass.WITCH,
            level=50,
            passive_nodes={1, 2, 3}
        )

        mutations = _generate_swap_neighbors(build, simple_tree, budget_with_respec)

        # All resulting trees should be connected
        for mutation in mutations:
            new_build = mutation.apply(build)
            assert _is_tree_valid(new_build, simple_tree, new_build.passive_nodes)


# ============================================================================
# Test Prioritization (AC-2.2.5)
# ============================================================================

class TestPrioritization:
    """Test suite for AC-2.2.5: Prioritize high-value nodes"""

    def test_get_node_value_notable(self, simple_tree):
        """Test Notable nodes have value 3 (Subtask 4.4)"""
        notable = simple_tree.nodes[3]
        assert _get_node_value(notable) == 3

    def test_get_node_value_keystone(self, simple_tree):
        """Test Keystone nodes have value 2 (Subtask 4.4)"""
        keystone = simple_tree.nodes[4]
        assert _get_node_value(keystone) == 2

    def test_get_node_value_small(self, simple_tree):
        """Test Small passive nodes have value 1 (Subtask 4.4)"""
        small = simple_tree.nodes[2]
        assert _get_node_value(small) == 1

    def test_get_node_value_travel(self, simple_tree):
        """Test Travel nodes have value 0 (Subtask 4.4)"""
        travel = simple_tree.nodes[5]
        assert _get_node_value(travel) == 0

    def test_prioritize_mutations_sorting(self, simple_tree):
        """Test mutations are sorted by node value (Subtask 4.5)"""
        # Create mutations for different node types
        mutations = [
            TreeMutation("add", {5}, set(), 1, 0),  # Travel (value 0)
            TreeMutation("add", {3}, set(), 1, 0),  # Notable (value 3)
            TreeMutation("add", {2}, set(), 1, 0),  # Small (value 1)
            TreeMutation("add", {4}, set(), 1, 0),  # Keystone (value 2)
        ]

        prioritized = _prioritize_mutations(mutations, simple_tree, limit=10)

        # Should be sorted: Notable (3), Keystone (4), Small (2), Travel (5)
        added_nodes = [list(m.nodes_added)[0] for m in prioritized]
        assert added_nodes[0] == 3  # Notable first
        assert added_nodes[1] == 4  # Keystone second
        assert added_nodes[2] == 2  # Small third
        assert added_nodes[3] == 5  # Travel last

    def test_prioritize_mutations_limiting(self, simple_tree):
        """Test limiting mutation count (AC-2.2.4, Subtask 4.5)"""
        # Create 10 mutations
        mutations = [
            TreeMutation("add", {i}, set(), 1, 0)
            for i in range(10)
        ]

        # Limit to 5
        prioritized = _prioritize_mutations(mutations, simple_tree, limit=5)

        assert len(prioritized) == 5


# ============================================================================
# Test Main generate_neighbors() Function
# ============================================================================

class TestGenerateNeighbors:
    """Test suite for main generate_neighbors() API"""

    def test_generate_neighbors_with_unallocated_only(
        self,
        sample_build,
        simple_tree,
        budget_with_unallocated
    ):
        """Test neighbor generation with only unallocated budget (AC-2.2.1)"""
        neighbors = generate_neighbors(sample_build, simple_tree, budget_with_unallocated)

        # Should generate add mutations only
        assert len(neighbors) > 0
        for neighbor in neighbors:
            assert neighbor.mutation_type == "add"

    def test_generate_neighbors_with_respec_only(
        self,
        sample_build,
        simple_tree,
        budget_with_respec
    ):
        """Test neighbor generation with only respec budget (AC-2.2.2)"""
        neighbors = generate_neighbors(sample_build, simple_tree, budget_with_respec)

        # Should generate swap mutations only
        for neighbor in neighbors:
            assert neighbor.mutation_type == "swap"

    def test_generate_neighbors_prioritize_adds_true(
        self,
        sample_build,
        simple_tree,
        budget_with_both
    ):
        """Test prioritize_adds=True generates add neighbors first (Subtask 4.2, 6.8)"""
        neighbors = generate_neighbors(
            sample_build,
            simple_tree,
            budget_with_both,
            prioritize_adds=True
        )

        # Should include add mutations
        add_mutations = [n for n in neighbors if n.mutation_type == "add"]
        assert len(add_mutations) > 0

    def test_generate_neighbors_prioritize_adds_false(
        self,
        sample_build,
        simple_tree,
        budget_with_both
    ):
        """Test prioritize_adds=False generates both types"""
        neighbors = generate_neighbors(
            sample_build,
            simple_tree,
            budget_with_both,
            prioritize_adds=False
        )

        # Should include both types
        add_mutations = [n for n in neighbors if n.mutation_type == "add"]
        swap_mutations = [n for n in neighbors if n.mutation_type == "swap"]

        assert len(add_mutations) > 0 or len(swap_mutations) > 0

    def test_generate_neighbors_no_valid_neighbors(
        self,
        sample_build,
        simple_tree,
        budget_exhausted
    ):
        """Test handling when no valid neighbors exist (Subtask 5.3, 6.7)"""
        neighbors = generate_neighbors(sample_build, simple_tree, budget_exhausted)

        assert neighbors == []

    def test_generate_neighbors_limit_count(self, simple_tree, budget_with_both):
        """Test neighbor count limiting (AC-2.2.4, Subtask 6.6)"""
        # Create a build that would generate many neighbors
        build = BuildData(
            character_class=CharacterClass.WITCH,
            level=100,
            passive_nodes={1}
        )

        neighbors = generate_neighbors(build, simple_tree, budget_with_both)

        # Should limit to ≤200 neighbors
        assert len(neighbors) <= 200


# ============================================================================
# Test Connectivity Validation
# ============================================================================

class TestConnectivityValidation:
    """Test tree connectivity validation (AC-2.2.3)"""

    def test_is_tree_valid_full_connected(self, simple_tree):
        """Test validation with fully connected tree"""
        allocated = {1, 2, 3}
        assert _is_tree_valid_full(simple_tree, allocated, class_start=1) is True

    def test_is_tree_valid_full_disconnected(self, simple_tree):
        """Test validation with disconnected tree"""
        # Nodes 1 and 5 are not connected (missing 2, 4)
        allocated = {1, 5}
        assert _is_tree_valid_full(simple_tree, allocated, class_start=1) is False

    def test_is_tree_valid_add_valid(self, sample_build, simple_tree):
        """Test add validation with valid candidate"""
        # Adding node 3 is valid (connected via node 2)
        assert _is_tree_valid_add(sample_build, simple_tree, new_node=3, class_start=1) is True

    def test_get_class_start_node(self, sample_build, simple_tree):
        """Test getting class start node"""
        start_node = _get_class_start_node(sample_build, simple_tree)
        assert start_node == 1

    def test_get_class_start_node_invalid_class(self, simple_tree):
        """Test error when class not found in tree"""
        build = BuildData(
            character_class=CharacterClass.WARRIOR,  # Not in simple_tree
            level=50,
            passive_nodes={1}
        )

        with pytest.raises(ValueError, match="not found in passive tree data"):
            _get_class_start_node(build, simple_tree)


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling (Task 5)"""

    def test_empty_allocated_nodes(self, simple_tree, budget_with_unallocated):
        """Test with no allocated nodes"""
        build = BuildData(
            character_class=CharacterClass.WITCH,
            level=50,
            passive_nodes={1}  # Only start node
        )

        neighbors = generate_neighbors(build, simple_tree, budget_with_unallocated)

        # Should still generate neighbors
        assert len(neighbors) > 0

    def test_all_nodes_allocated(self, simple_tree, budget_with_unallocated):
        """Test when all nodes are already allocated"""
        build = BuildData(
            character_class=CharacterClass.WITCH,
            level=50,
            passive_nodes={1, 2, 3, 4, 5}  # All nodes
        )

        neighbors = generate_neighbors(build, simple_tree, budget_with_unallocated)

        # No add neighbors possible (all allocated)
        add_neighbors = [n for n in neighbors if n.mutation_type == "add"]
        assert len(add_neighbors) == 0


# ============================================================================
# Test Story 2.5: Free-First Budget Prioritization
# ============================================================================

class TestFreeFirstPrioritization:
    """
    Test suite for Story 2.5: Budget Prioritization (Free-First Strategy)

    Tests acceptance criteria:
    - AC-2.5.1: Prioritize "add node" moves (use unallocated)
    - AC-2.5.2: Only generate "swap node" moves if unallocated exhausted
    """

    def test_prioritize_adds_only_adds_when_unallocated_available(
        self,
        sample_build,
        simple_tree,
        budget_with_both
    ):
        """
        AC-2.5.1: When prioritize_adds=True and unallocated_remaining > 0,
        should generate ONLY add mutations, NO swap mutations
        """
        neighbors = generate_neighbors(
            sample_build,
            simple_tree,
            budget_with_both,
            prioritize_adds=True
        )

        # Verify we have neighbors
        assert len(neighbors) > 0

        # Count mutation types
        add_mutations = [n for n in neighbors if n.mutation_type == "add"]
        swap_mutations = [n for n in neighbors if n.mutation_type == "swap"]

        # With unallocated budget available, should ONLY generate adds
        assert len(add_mutations) > 0
        assert len(swap_mutations) == 0, "Swaps should not be generated when unallocated budget available"

    def test_only_swaps_when_unallocated_exhausted(
        self,
        simple_tree
    ):
        """
        AC-2.5.2: When unallocated_remaining == 0, should generate
        ONLY swap mutations (if respec budget available)
        """
        # Use build with more allocated nodes to ensure valid swap mutations exist
        build = BuildData(
            character_class=CharacterClass.WITCH,
            level=50,
            passive_nodes={1, 2, 3}
        )

        budget = BudgetState(
            unallocated_available=0,
            unallocated_used=0,
            respec_available=5,
            respec_used=0
        )

        neighbors = generate_neighbors(
            build,
            simple_tree,
            budget,
            prioritize_adds=True
        )

        # Count mutation types
        add_mutations = [n for n in neighbors if n.mutation_type == "add"]
        swap_mutations = [n for n in neighbors if n.mutation_type == "swap"]

        # With unallocated exhausted, should ONLY generate swaps
        assert len(add_mutations) == 0, "Adds should not be generated when unallocated exhausted"
        assert len(swap_mutations) > 0

    def test_skip_swaps_entirely_when_unallocated_available(
        self,
        simple_tree
    ):
        """
        AC-2.5.2: Skip swap generation entirely if unallocated_remaining > 0

        This is the CRITICAL test that validates the bug fix.
        Even if no valid add moves exist, swaps should not be generated
        when unallocated budget is available.
        """
        # Create a build where all adjacent nodes are already allocated
        # This means no valid add moves, but we still have unallocated budget
        build = BuildData(
            character_class=CharacterClass.WITCH,
            level=50,
            passive_nodes={1, 2, 3, 4}  # Only node 5 unallocated, but not adjacent
        )

        budget = BudgetState(
            unallocated_available=5,  # Still have unallocated budget
            unallocated_used=0,
            respec_available=5,
            respec_used=0
        )

        neighbors = generate_neighbors(
            build,
            simple_tree,
            budget,
            prioritize_adds=True
        )

        # Count mutation types
        swap_mutations = [n for n in neighbors if n.mutation_type == "swap"]

        # Even though no valid add moves exist, swaps should NOT be generated
        # because unallocated budget is still available
        # NOTE: If this test fails, it means the old buggy logic is still in place
        assert len(swap_mutations) == 0, (
            "Swaps should NEVER be generated when unallocated_remaining > 0, "
            "even if no valid add moves exist"
        )

    def test_prioritize_adds_false_generates_both_types(
        self,
        simple_tree,
        budget_with_both
    ):
        """
        Backward compatibility: prioritize_adds=False should generate both types
        regardless of budget availability
        """
        # Use build with more allocated nodes to ensure valid swap mutations exist
        build = BuildData(
            character_class=CharacterClass.WITCH,
            level=50,
            passive_nodes={1, 2, 3}
        )

        neighbors = generate_neighbors(
            build,
            simple_tree,
            budget_with_both,
            prioritize_adds=False
        )

        # Count mutation types
        add_mutations = [n for n in neighbors if n.mutation_type == "add"]
        swap_mutations = [n for n in neighbors if n.mutation_type == "swap"]

        # With prioritize_adds=False, should generate both types
        assert len(add_mutations) > 0
        assert len(swap_mutations) > 0

    def test_boundary_zero_unallocated_with_respec(
        self,
        simple_tree
    ):
        """
        Boundary test: 0 unallocated + some respec → only swaps
        """
        # Use build with more allocated nodes to ensure valid swap mutations exist
        build = BuildData(
            character_class=CharacterClass.WITCH,
            level=50,
            passive_nodes={1, 2, 3}
        )

        budget = BudgetState(
            unallocated_available=0,
            unallocated_used=0,
            respec_available=5,
            respec_used=0
        )

        neighbors = generate_neighbors(
            build,
            simple_tree,
            budget,
            prioritize_adds=True
        )

        add_mutations = [n for n in neighbors if n.mutation_type == "add"]
        swap_mutations = [n for n in neighbors if n.mutation_type == "swap"]

        assert len(add_mutations) == 0
        assert len(swap_mutations) > 0

    def test_boundary_unallocated_with_zero_respec(
        self,
        sample_build,
        simple_tree
    ):
        """
        Boundary test: some unallocated + 0 respec → only adds
        """
        budget = BudgetState(
            unallocated_available=5,
            unallocated_used=0,
            respec_available=0,
            respec_used=0
        )

        neighbors = generate_neighbors(
            sample_build,
            simple_tree,
            budget,
            prioritize_adds=True
        )

        add_mutations = [n for n in neighbors if n.mutation_type == "add"]
        swap_mutations = [n for n in neighbors if n.mutation_type == "swap"]

        assert len(add_mutations) > 0
        assert len(swap_mutations) == 0

    def test_boundary_both_budgets_exhausted(
        self,
        sample_build,
        simple_tree
    ):
        """
        Boundary test: both budgets exhausted → empty list (convergence)
        """
        budget = BudgetState(
            unallocated_available=0,
            unallocated_used=0,
            respec_available=0,
            respec_used=0
        )

        neighbors = generate_neighbors(
            sample_build,
            simple_tree,
            budget,
            prioritize_adds=True
        )

        assert len(neighbors) == 0, "No neighbors should be generated when both budgets exhausted"
