"""Neighbor generation for hill climbing optimization

This module implements tree mutation strategies to generate valid neighbor
configurations from the current passive tree state. Supports two strategies:
1. Add Node: Allocate any unallocated node adjacent to current tree
2. Swap Node: Deallocate one node, allocate one new connected node

Neighbors are prioritized by node value (Notable > Keystone > Small > Travel)
and validated for tree connectivity before inclusion.

Performance:
    - Target: 20ms total per generate_neighbors() call
    - Budget: 100-1000 is_connected() checks (0.02ms each = 2-20ms)
    - Limit: 50-200 neighbors returned per iteration

References:
    - Tech Spec Epic 2 - Section 7.3: Neighbor Generation API
    - Tech Spec Epic 2 - Section 7.4: Neighbor generation workflow
    - Story 2.2: Generate neighbor configurations (1-hop moves)
"""

import logging
from dataclasses import dataclass, replace
from typing import List, Set, Optional

from src.models.build_data import BuildData
from src.calculator.passive_tree import PassiveTreeGraph, PassiveNode

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class BudgetState:
    """
    Budget constraint tracking for optimization.

    Tracks two budget types:
    - Unallocated points: Free passive points (from leveling + quest rewards)
    - Respec points: Points for reallocating existing passives

    Note: Full implementation in Story 2.4 (budget_tracker.py).
    This is a simplified version for Story 2.2 compatibility.

    Attributes:
        unallocated_available: Total free points available
        unallocated_used: Free points already consumed
        respec_available: Total respec points (None = unlimited)
        respec_used: Respec points already consumed
    """
    unallocated_available: int
    unallocated_used: int
    respec_available: Optional[int]  # None = unlimited
    respec_used: int

    @property
    def unallocated_remaining(self) -> int:
        """Remaining free points"""
        return max(0, self.unallocated_available - self.unallocated_used)

    @property
    def respec_remaining(self) -> Optional[int]:
        """Remaining respec points (None = unlimited)"""
        if self.respec_available is None:
            return None
        return max(0, self.respec_available - self.respec_used)

    @property
    def can_add(self) -> bool:
        """Check if add mutations are allowed"""
        return self.unallocated_remaining > 0

    @property
    def can_swap(self) -> bool:
        """Check if swap mutations are allowed"""
        return self.respec_remaining is None or (self.respec_remaining > 0)

    def can_allocate(self, count: int) -> bool:
        """
        Check if count unallocated points are available.

        Added in Story 2.4 for budget validation filtering.
        Compatible with full BudgetState in budget_tracker.py.

        Args:
            count: Number of unallocated points needed

        Returns:
            True if unallocated_used + count <= unallocated_available
        """
        return self.unallocated_used + count <= self.unallocated_available

    def can_respec(self, count: int) -> bool:
        """
        Check if count respec points are available.

        Supports unlimited respec mode (respec_available=None).
        Added in Story 2.4 for budget validation filtering.
        Compatible with full BudgetState in budget_tracker.py.

        Args:
            count: Number of respec points needed

        Returns:
            True if respec_available is None (unlimited) or
            respec_used + count <= respec_available
        """
        if self.respec_available is None:
            return True
        return self.respec_used + count <= self.respec_available


@dataclass
class TreeMutation:
    """
    Represents a single tree modification (add or swap node).

    All mutations are validated for tree connectivity before creation.
    Mutations are immutable and can be applied to BuildData to produce
    a new build configuration.

    Attributes:
        mutation_type: "add" or "swap"
        nodes_added: Node IDs to allocate (typically 1 node)
        nodes_removed: Node IDs to deallocate (empty for "add", 1 for "swap")
        unallocated_cost: Free points consumed (1 for "add", 0 for "swap")
        respec_cost: Respec points consumed (0 for "add", 1 for "swap")

    Example:
        >>> # Add node mutation
        >>> mutation = TreeMutation(
        ...     mutation_type="add",
        ...     nodes_added={12345},
        ...     nodes_removed=set(),
        ...     unallocated_cost=1,
        ...     respec_cost=0
        ... )
        >>> new_build = mutation.apply(current_build)
    """
    mutation_type: str  # "add" | "swap"
    nodes_added: Set[int]
    nodes_removed: Set[int]
    unallocated_cost: int
    respec_cost: int

    def apply(self, build: BuildData) -> BuildData:
        """
        Apply mutation to build, return new BuildData.

        Uses immutable pattern: creates new BuildData instance with
        modified passive_nodes set. Original build is unchanged.

        Args:
            build: Current BuildData configuration

        Returns:
            New BuildData with mutation applied

        Example:
            >>> current = BuildData(passive_nodes={1, 2, 3}, ...)
            >>> mutation = TreeMutation("add", {4}, set(), 1, 0)
            >>> updated = mutation.apply(current)
            >>> assert updated.passive_nodes == {1, 2, 3, 4}
            >>> assert current.passive_nodes == {1, 2, 3}  # Unchanged
        """
        new_passive_nodes = build.passive_nodes.copy()
        new_passive_nodes -= self.nodes_removed
        new_passive_nodes |= self.nodes_added
        return replace(build, passive_nodes=new_passive_nodes)


# ============================================================================
# Main API
# ============================================================================

def generate_neighbors(
    build: BuildData,
    tree: PassiveTreeGraph,
    budget: BudgetState,
    prioritize_adds: bool = True
) -> List[TreeMutation]:
    """
    Generate valid neighbor configurations from current build.

    Implements two mutation strategies:
    1. Add Node: Allocate any unallocated connected node (uses unallocated budget)
    2. Swap Node: Remove 1 node, add 1 connected node (uses respec budget)

    Prioritization (if prioritize_adds=True):
    - Generate ALL "add node" neighbors first (free budget)
    - Only generate "swap node" neighbors if unallocated exhausted
    - Prefer high-value nodes: Notable > Keystone > Small > Travel

    All neighbors are validated for tree connectivity before inclusion.
    Results are limited to top 100 by value to control PoB calculation overhead.

    Args:
        build: Current build configuration
        tree: PassiveTreeGraph for connectivity validation
        budget: Current budget state (unallocated + respec points)
        prioritize_adds: If True, prefer free allocations over swaps

    Returns:
        List of valid TreeMutation objects (limit: Top 100 by value)
        Returns empty list if no valid neighbors exist (convergence signal)

    Performance:
        - Target: ~20ms total per call
        - Connectivity checks: 0.02ms each (100-1000 calls = 2-20ms)

    References:
        - Tech Spec Epic 2 - Section 7.3: generate_neighbors() API
        - Story 2.2 AC #1-5: Acceptance criteria

    Example:
        >>> budget = BudgetState(
        ...     unallocated_available=15,
        ...     unallocated_used=0,
        ...     respec_available=10,
        ...     respec_used=0
        ... )
        >>> neighbors = generate_neighbors(build, tree, budget)
        >>> print(f"Generated {len(neighbors)} valid neighbors")
    """
    logger.debug(
        "Generating neighbors: allocated=%d, unallocated_remaining=%d, respec_remaining=%s, prioritize_adds=%s",
        len(build.passive_nodes),
        budget.unallocated_remaining,
        budget.respec_remaining,
        prioritize_adds
    )

    all_mutations = []

    # Task 4: Budget-aware prioritization strategy
    if prioritize_adds:
        # Subtask 4.2: Generate all add neighbors first
        if budget.can_add:
            add_mutations = _generate_add_neighbors(build, tree, budget)
            all_mutations.extend(add_mutations)
            logger.debug("Generated %d add mutations (prioritize_adds=True)", len(add_mutations))

        # Subtask 4.3: Only generate swap neighbors if unallocated budget exhausted
        # AC-2.5.2: Skip swap generation entirely if unallocated_remaining > 0
        if not budget.can_add:
            if budget.can_swap:
                swap_mutations = _generate_swap_neighbors(build, tree, budget)
                all_mutations.extend(swap_mutations)
                logger.debug("Generated %d swap mutations (unallocated exhausted)", len(swap_mutations))
    else:
        # Non-prioritized mode: generate both types
        if budget.can_add:
            add_mutations = _generate_add_neighbors(build, tree, budget)
            all_mutations.extend(add_mutations)

        if budget.can_swap:
            swap_mutations = _generate_swap_neighbors(build, tree, budget)
            all_mutations.extend(swap_mutations)

        logger.debug(
            "Generated %d add + %d swap mutations (prioritize_adds=False)",
            len([m for m in all_mutations if m.mutation_type == "add"]),
            len([m for m in all_mutations if m.mutation_type == "swap"])
        )

    # Task 5: Edge case handling
    # Subtask 5.3: Handle case where no valid neighbors exist
    if len(all_mutations) == 0:
        # Subtask 5.5: Log warning if neighbor generation produces 0 neighbors
        logger.warning(
            "No valid neighbors found (convergence indicator): "
            "allocated=%d, can_add=%s, can_swap=%s",
            len(build.passive_nodes),
            budget.can_add,
            budget.can_swap
        )
        return []

    # AC #4: Limit neighbor count to reasonable size (50-200 per iteration)
    # Final prioritization across all mutation types
    final_mutations = _prioritize_mutations(all_mutations, tree, limit=200)

    # Story 2.4 AC-2.4.5: Explicit budget validation (defense-in-depth)
    # Filter out any mutations that would exceed budget constraints
    # This is a safety check - mutations should already be valid from generation
    validated_mutations = [
        m for m in final_mutations
        if budget.can_allocate(m.unallocated_cost) and budget.can_respec(m.respec_cost)
    ]

    if len(validated_mutations) < len(final_mutations):
        logger.warning(
            "Budget validation filtered %d mutations that would exceed constraints",
            len(final_mutations) - len(validated_mutations)
        )

    logger.info(
        "Generated %d total neighbors (%d add, %d swap) from %d candidates",
        len(validated_mutations),
        len([m for m in validated_mutations if m.mutation_type == "add"]),
        len([m for m in validated_mutations if m.mutation_type == "swap"]),
        len(all_mutations)
    )

    # Subtask 5.4: Validate that all returned mutations respect budget constraints
    # Defense-in-depth: validated at generation time AND final filtering above

    return validated_mutations


# ============================================================================
# Helper Functions (to be implemented in Tasks 2-5)
# ============================================================================

def _generate_add_neighbors(
    build: BuildData,
    tree: PassiveTreeGraph,
    budget: BudgetState
) -> List[TreeMutation]:
    """
    Generate all valid "add node" mutations (Task 2, AC #1, #3, #4, #5).

    Strategy:
    1. Find all unallocated nodes adjacent to current allocated nodes
    2. Validate each candidate maintains tree connectivity
    3. Check budget availability (unallocated_used + 1 <= unallocated_available)
    4. Create TreeMutation objects with mutation_type="add"
    5. Prioritize by node type (Notable > Keystone > Small > Travel)
    6. Limit to top 100-150 candidates

    Args:
        build: Current BuildData configuration
        tree: PassiveTreeGraph for connectivity validation
        budget: BudgetState for budget enforcement

    Returns:
        List of valid TreeMutation objects for add operations
    """
    # Subtask 2.1: Identify all unallocated nodes adjacent to allocated nodes
    candidates = set()
    for allocated_node in build.passive_nodes:
        neighbors = tree.get_neighbors(allocated_node)
        for neighbor in neighbors:
            # Only consider nodes that are not already allocated
            if neighbor not in build.passive_nodes:
                candidates.add(neighbor)

    logger.debug(
        "Add candidates: %d unallocated nodes adjacent to %d allocated nodes",
        len(candidates),
        len(build.passive_nodes)
    )

    # Subtask 2.3: Check budget availability
    if not budget.can_add:
        logger.debug("No unallocated budget remaining - skipping add neighbors")
        return []

    # Generate mutations for each candidate
    mutations = []
    class_start = _get_class_start_node(build, tree)

    for candidate_node in candidates:
        # Subtask 2.2: Validate tree connectivity
        # New tree = current_nodes ∪ {candidate_node}
        new_allocated = build.passive_nodes | {candidate_node}

        # Fast path: candidate must be connected to at least one allocated node
        # (already guaranteed by candidates generation logic above)

        # Verify the entire tree remains connected
        if not _is_tree_valid_add(build, tree, candidate_node, class_start):
            continue

        # Subtask 2.4: Create TreeMutation with mutation_type="add"
        mutation = TreeMutation(
            mutation_type="add",
            nodes_added={candidate_node},
            nodes_removed=set(),
            unallocated_cost=1,
            respec_cost=0
        )
        mutations.append(mutation)

    logger.debug("Generated %d valid add mutations", len(mutations))

    # Subtask 2.5 & 2.6: Prioritize and limit
    # Prioritize by node value, limit to top 100-150
    prioritized = _prioritize_mutations(mutations, tree, limit=150)

    return prioritized


def _is_tree_valid_add(
    build: BuildData,
    tree: PassiveTreeGraph,
    new_node: int,
    class_start: int
) -> bool:
    """
    Fast connectivity check for add mutations.

    For add mutations, we only need to check that the new node
    is connected to the class start via the existing tree.
    This is automatically true if the new node is adjacent to
    any allocated node in a connected tree.

    Args:
        build: Current BuildData
        tree: PassiveTreeGraph
        new_node: Node being added
        class_start: Class starting node

    Returns:
        True if adding node maintains connectivity
    """
    # New allocated set includes the candidate
    new_allocated = build.passive_nodes | {new_node}

    # Check if new_node is reachable from class start
    return tree.is_connected(class_start, new_node, new_allocated)


def _generate_swap_neighbors(
    build: BuildData,
    tree: PassiveTreeGraph,
    budget: BudgetState
) -> List[TreeMutation]:
    """
    Generate all valid "swap node" mutations (Task 3, AC #2, #3, #4, #5).

    Strategy:
    1. Identify all allocated nodes that can be removed (non-critical to connectivity)
    2. For each removable node, find unallocated nodes that become connectable
    3. Validate resulting tree connectivity after swap
    4. Check respec budget availability
    5. Create TreeMutation objects with mutation_type="swap"
    6. Prioritize by improvement potential (Notable → Notable > Travel → Notable)
    7. Limit to top 50-100 swaps

    Args:
        build: Current BuildData configuration
        tree: PassiveTreeGraph for connectivity validation
        budget: BudgetState for budget enforcement

    Returns:
        List of valid TreeMutation objects for swap operations
    """
    # Subtask 3.4: Check respec budget availability
    if not budget.can_swap:
        logger.debug("No respec budget remaining - skipping swap neighbors")
        return []

    mutations = []
    class_start = _get_class_start_node(build, tree)

    # Subtask 3.1: Identify all allocated nodes that can be removed
    removable_nodes = _find_removable_nodes(build, tree, class_start)

    logger.debug(
        "Swap candidates: %d removable nodes from %d allocated",
        len(removable_nodes),
        len(build.passive_nodes)
    )

    # Subtask 3.2: For each removable node, find unallocated nodes that become connectable
    for removable_node in removable_nodes:
        # Get potential nodes to add after removal
        # These are unallocated neighbors of the remaining allocated nodes
        temp_allocated = build.passive_nodes - {removable_node}

        # Find all unallocated nodes adjacent to the remaining tree
        add_candidates = set()
        for allocated_node in temp_allocated:
            neighbors = tree.get_neighbors(allocated_node)
            for neighbor in neighbors:
                if neighbor not in temp_allocated and neighbor != removable_node:
                    add_candidates.add(neighbor)

        # For each add candidate, validate the swap
        for add_node in add_candidates:
            # Subtask 3.3: Validate resulting tree connectivity after swap
            new_allocated = temp_allocated | {add_node}

            # Check if new tree is still connected
            if not _is_tree_valid_full(tree, new_allocated, class_start):
                continue

            # Subtask 3.5: Create TreeMutation with mutation_type="swap"
            mutation = TreeMutation(
                mutation_type="swap",
                nodes_added={add_node},
                nodes_removed={removable_node},
                unallocated_cost=0,
                respec_cost=1
            )
            mutations.append(mutation)

    logger.debug("Generated %d valid swap mutations", len(mutations))

    # Subtask 3.6 & 3.7: Prioritize and limit to top 50-100
    prioritized = _prioritize_mutations(mutations, tree, limit=100)

    return prioritized


def _find_removable_nodes(
    build: BuildData,
    tree: PassiveTreeGraph,
    class_start: int
) -> Set[int]:
    """
    Identify allocated nodes that can be removed without breaking connectivity.

    A node is removable if removing it doesn't create orphan nodes
    (all other allocated nodes remain connected to class start).

    Args:
        build: Current BuildData
        tree: PassiveTreeGraph
        class_start: Class starting node

    Returns:
        Set of node IDs that can be safely removed
    """
    removable = set()

    for node in build.passive_nodes:
        # Never remove the class start node
        if node == class_start:
            continue

        # Test removal: would remaining nodes stay connected?
        temp_allocated = build.passive_nodes - {node}

        # Check if all remaining nodes are still connected to class start
        if _is_tree_valid_full(tree, temp_allocated, class_start):
            removable.add(node)

    return removable


def _is_tree_valid_full(
    tree: PassiveTreeGraph,
    allocated: Set[int],
    class_start: int
) -> bool:
    """
    Validate that all allocated nodes form a connected tree.

    Uses BFS to check connectivity from class start node to all other nodes.

    Args:
        tree: PassiveTreeGraph
        allocated: Set of allocated node IDs
        class_start: Class starting node

    Returns:
        True if all nodes are connected to class start, False otherwise
    """
    if not allocated:
        return True

    if class_start not in allocated:
        return False

    # Check that all nodes are reachable from class start
    # We can do this efficiently with a single BFS traversal
    visited = {class_start}
    queue = [class_start]

    while queue:
        current = queue.pop(0)
        for neighbor in tree.get_neighbors(current):
            if neighbor in allocated and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    # All allocated nodes should be visited
    return visited == allocated


def _get_node_value(node: PassiveNode) -> int:
    """
    Calculate node priority value for sorting (Task 4, Subtask 4.4).

    Value scoring (from epic-2-optimizer-design.md Section 4.2):
    - Notable passive: 3
    - Keystone passive: 2
    - Small passive: 1
    - Travel node: 0

    Args:
        node: PassiveNode to score

    Returns:
        Integer value (0-3) for prioritization
    """
    if node.is_notable:
        return 3
    elif node.is_keystone:
        return 2
    elif node.stats:  # Has stats = small passive
        return 1
    else:  # No stats = travel node
        return 0


def _prioritize_mutations(
    mutations: List[TreeMutation],
    tree: PassiveTreeGraph,
    limit: int
) -> List[TreeMutation]:
    """
    Sort mutations by node value and limit count (Task 4, Subtask 4.5).

    Sorts mutations by the value of nodes being added (highest value first).
    For swap mutations, uses the value of the node being added.

    Args:
        mutations: List of TreeMutation objects to prioritize
        tree: PassiveTreeGraph for looking up node properties
        limit: Maximum number of mutations to return

    Returns:
        Top N mutations sorted by value (highest first)
    """
    # Calculate value for each mutation based on nodes being added
    def mutation_value(mutation: TreeMutation) -> int:
        total_value = 0
        for node_id in mutation.nodes_added:
            node = tree.nodes.get(node_id)
            if node:
                total_value += _get_node_value(node)
        return total_value

    # Sort by value descending
    sorted_mutations = sorted(mutations, key=mutation_value, reverse=True)

    # Limit to top N
    return sorted_mutations[:limit]


def _get_class_start_node(build: BuildData, tree: PassiveTreeGraph) -> int:
    """
    Get the starting node ID for the build's character class.

    Args:
        build: BuildData with character_class
        tree: PassiveTreeGraph with class_start_nodes mapping

    Returns:
        Starting node ID for connectivity validation

    Raises:
        ValueError: If class not found in tree data
    """
    class_name = build.character_class.value  # Convert enum to string
    start_node = tree.class_start_nodes.get(class_name)

    if start_node is None:
        raise ValueError(
            f"Class '{class_name}' not found in passive tree data. "
            f"Available classes: {list(tree.class_start_nodes.keys())}"
        )

    return start_node


def _is_tree_valid(
    build: BuildData,
    tree: PassiveTreeGraph,
    allocated_nodes: Set[int]
) -> bool:
    """
    Validate that allocated nodes form a connected tree.

    Args:
        build: BuildData for class start node
        tree: PassiveTreeGraph for connectivity check
        allocated_nodes: Set of node IDs to validate

    Returns:
        True if all nodes are connected to class start, False otherwise
    """
    class_start = _get_class_start_node(build, tree)
    return _is_tree_valid_full(tree, allocated_nodes, class_start)
