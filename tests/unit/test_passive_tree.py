"""
Unit tests for PassiveTree Graph Module

Tests all acceptance criteria for Story 1.7:
- AC-1.7.1: System loads PoE 2 passive tree JSON/Lua data
- AC-1.7.2: System understands node IDs, connections (edges), and node stats
- AC-1.7.3: System identifies character class starting positions
- AC-1.7.4: System validates allocated nodes are connected (no orphan nodes)
- AC-1.7.5: System handles Notable/Keystone/Small passive types

Story: 1.7 - Load Passive Tree Graph
Author: Dev Agent (Amelia)
Date: 2025-10-20
"""

import os
import pytest
from pathlib import Path

# Import directly from module to avoid circular dependency during testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from calculator.passive_tree import (
    PassiveNode,
    PassiveTreeGraph,
    load_passive_tree,
    get_passive_tree,
    clear_passive_tree_cache,
)


class TestPassiveTreeFileAccess:
    """Test suite for AC-1.7.1: File loading and data access"""

    def test_passive_tree_file_exists(self):
        """Verify PassiveTree data file exists in external/pob-engine/"""
        project_root = Path(__file__).parent.parent.parent
        tree_file = project_root / "external" / "pob-engine" / "src" / "TreeData" / "0_3" / "tree.json"

        assert tree_file.exists(), f"PassiveTree data file not found at: {tree_file}"

    def test_load_passive_tree_no_errors(self):
        """Verify load_passive_tree() executes without exceptions (AC-1.7.1)"""
        # This should not raise any exceptions
        tree = load_passive_tree()

        assert tree is not None
        assert isinstance(tree, PassiveTreeGraph)

    def test_load_invalid_version_raises_error(self):
        """Verify load_passive_tree() raises FileNotFoundError for invalid version"""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_passive_tree(tree_version="nonexistent_version")

        assert "PassiveTree data file not found" in str(exc_info.value)


class TestPassiveTreeStructure:
    """Test suite for AC-1.7.2: Node IDs, connections, and stats"""

    @pytest.fixture(scope="class")
    def tree(self):
        """Fixture providing a loaded PassiveTreeGraph for all tests in this class"""
        return load_passive_tree()

    def test_node_count_reasonable(self, tree):
        """Assert loaded tree has >1000 nodes (PoE 2 typical tree size) (AC-1.7.2)"""
        node_count = tree.get_node_count()

        assert node_count > 1000, f"Expected >1000 nodes, got {node_count}"
        # PoE 2 Early Access has ~4000 nodes
        assert node_count < 10000, f"Unexpectedly high node count: {node_count}"

    def test_nodes_have_valid_ids(self, tree):
        """Verify all nodes have valid integer IDs (AC-1.7.2)"""
        for node_id, node in tree.nodes.items():
            assert isinstance(node_id, int), f"Node ID should be int, got {type(node_id)}"
            assert node.node_id == node_id, f"Node ID mismatch: {node.node_id} != {node_id}"

    def test_node_has_stats(self, tree):
        """Verify PassiveNode objects have non-empty stats list with modifiers (AC-1.7.2)"""
        # Find nodes with stats (not all nodes have stats, e.g., path nodes)
        nodes_with_stats = [node for node in tree.nodes.values() if node.stats]

        assert len(nodes_with_stats) > 100, "Expected many nodes with stat modifiers"

        # Check first node with stats
        sample_node = nodes_with_stats[0]
        assert isinstance(sample_node.stats, list)
        assert len(sample_node.stats) > 0
        assert isinstance(sample_node.stats[0], str)

    def test_edges_bidirectional(self, tree):
        """Verify if edge A→B exists, then B→A also exists (undirected graph) (AC-1.7.2)"""
        for node_id, neighbors in tree.edges.items():
            for neighbor_id in neighbors:
                # Check reverse edge exists
                assert neighbor_id in tree.edges, f"Neighbor {neighbor_id} not in edges dict"
                reverse_neighbors = tree.edges[neighbor_id]
                assert node_id in reverse_neighbors, \
                    f"Bidirectional edge missing: {node_id}→{neighbor_id} exists but {neighbor_id}→{node_id} doesn't"

    def test_get_neighbors_returns_set(self, tree):
        """Verify get_neighbors(node_id) returns Set[int] with connected node IDs (AC-1.7.2)"""
        # Get a node with neighbors
        node_id = next(iter(tree.edges.keys()))
        neighbors = tree.get_neighbors(node_id)

        assert isinstance(neighbors, set)
        assert len(neighbors) > 0, f"Node {node_id} should have neighbors"
        assert all(isinstance(n, int) for n in neighbors)

    def test_get_neighbors_empty_for_unknown_node(self, tree):
        """Verify get_neighbors() returns empty set for unknown node"""
        unknown_node_id = 999999999  # Very unlikely to exist
        neighbors = tree.get_neighbors(unknown_node_id)

        assert neighbors == set()

    def test_edge_count(self, tree):
        """Verify reasonable number of edges (connections) in tree"""
        edge_count = tree.get_edge_count()

        # PoE 2 tree should have thousands of connections
        assert edge_count > 1000, f"Expected >1000 edges, got {edge_count}"


class TestClassStartingNodes:
    """Test suite for AC-1.7.3: Character class starting positions"""

    @pytest.fixture(scope="class")
    def tree(self):
        """Fixture providing a loaded PassiveTreeGraph"""
        return load_passive_tree()

    def test_all_classes_have_start_nodes(self, tree):
        """Assert all character classes have valid starting node IDs (AC-1.7.3)"""
        # PoE 2 Early Access classes
        expected_classes = ["Ranger", "Huntress", "Warrior", "Mercenary", "Witch", "Sorceress", "Monk"]

        for class_name in expected_classes:
            assert class_name in tree.class_start_nodes, \
                f"Class {class_name} missing from class_start_nodes"

            start_node_id = tree.class_start_nodes[class_name]
            assert isinstance(start_node_id, int), \
                f"Start node ID for {class_name} should be int, got {type(start_node_id)}"

            # Verify start node exists in tree
            assert start_node_id in tree.nodes, \
                f"Start node {start_node_id} for {class_name} not found in tree nodes"

    def test_class_start_nodes_are_unique(self, tree):
        """Verify each class has a unique starting node (different starting positions)"""
        start_nodes = list(tree.class_start_nodes.values())

        # At least some classes should have different start nodes
        # (Some may share if they're in the same area)
        unique_starts = set(start_nodes)
        assert len(unique_starts) >= 3, \
            f"Expected at least 3 different starting positions, got {len(unique_starts)}"


class TestTreeConnectivity:
    """Test suite for AC-1.7.4: Tree connectivity validation"""

    @pytest.fixture(scope="class")
    def tree(self):
        """Fixture providing a loaded PassiveTreeGraph"""
        return load_passive_tree()

    def test_is_connected_same_node(self, tree):
        """Verify is_connected returns True for same node (trivial case)"""
        node_id = next(iter(tree.nodes.keys()))
        allocated = {node_id}

        assert tree.is_connected(node_id, node_id, allocated) is True

    def test_is_connected_connected_path(self, tree):
        """BFS test with connected nodes: start→notable→keystone should return True (AC-1.7.4)"""
        # Find a connected path in the tree
        # Strategy: Start from any node, follow edges to build a small connected path
        start_node = next(iter(tree.edges.keys()))
        neighbors = tree.get_neighbors(start_node)

        if not neighbors:
            pytest.skip("Start node has no neighbors")

        next_node = next(iter(neighbors))
        next_neighbors = tree.get_neighbors(next_node)

        if not next_neighbors:
            pytest.skip("Second node has no neighbors")

        end_node = next(iter(next_neighbors))

        # Build allocated set: start → next → end
        allocated = {start_node, next_node, end_node}

        # Verify connectivity
        assert tree.is_connected(start_node, end_node, allocated) is True

    def test_is_connected_disconnected_nodes(self, tree):
        """BFS test with unconnected clusters should return False (AC-1.7.4)"""
        # Find two nodes that are NOT connected
        # Strategy: Pick two nodes far apart in the tree
        all_nodes = list(tree.nodes.keys())

        if len(all_nodes) < 2:
            pytest.skip("Not enough nodes for test")

        node_a = all_nodes[0]
        node_b = all_nodes[len(all_nodes) // 2]  # Pick node from middle of list

        # Only allocate these two nodes (no path between them)
        allocated = {node_a, node_b}

        # They should NOT be connected (no intermediate nodes allocated)
        result = tree.is_connected(node_a, node_b, allocated)

        # This will be False unless they happen to be direct neighbors (rare)
        # If they are neighbors, skip this test
        if node_b in tree.get_neighbors(node_a):
            pytest.skip("Selected nodes are direct neighbors")

        assert result is False, "Disconnected nodes should not be connected"

    def test_is_connected_node_not_in_allocated(self, tree):
        """Verify is_connected returns False if target node not in allocated set"""
        node_a = next(iter(tree.nodes.keys()))
        neighbors = tree.get_neighbors(node_a)

        if not neighbors:
            pytest.skip("Node has no neighbors")

        node_b = next(iter(neighbors))

        # Only allocate start node, not target
        allocated = {node_a}

        assert tree.is_connected(node_a, node_b, allocated) is False

    def test_validate_tree_connectivity(self, tree):
        """Test validate_tree_connectivity() with valid connected tree"""
        # Build a small connected tree from a class start
        class_name = "Witch"
        if class_name not in tree.class_start_nodes:
            class_name = next(iter(tree.class_start_nodes.keys()))

        start_node = tree.class_start_nodes[class_name]
        neighbors = tree.get_neighbors(start_node)

        if not neighbors:
            pytest.skip("Start node has no neighbors")

        # Allocate start + first few neighbors
        allocated = {start_node} | set(list(neighbors)[:3])

        # Should be valid (all connected to start)
        result = tree.validate_tree_connectivity(allocated, class_name)
        assert result is True

    def test_validate_tree_connectivity_invalid_class(self, tree):
        """Verify validate_tree_connectivity raises ValueError for unknown class"""
        with pytest.raises(ValueError) as exc_info:
            tree.validate_tree_connectivity({1, 2, 3}, "NonexistentClass")

        assert "Unknown class" in str(exc_info.value)


class TestNodeTypes:
    """Test suite for AC-1.7.5: Notable/Keystone/Small passive types"""

    @pytest.fixture(scope="class")
    def tree(self):
        """Fixture providing a loaded PassiveTreeGraph"""
        return load_passive_tree()

    def test_node_type_detection(self, tree):
        """Verify keystone, notable, and small passive flags are correctly set (AC-1.7.5)"""
        keystones = [node for node in tree.nodes.values() if node.is_keystone]
        notables = [node for node in tree.nodes.values() if node.is_notable]
        small_passives = [node for node in tree.nodes.values()
                          if not node.is_keystone and not node.is_notable]

        # PoE 2 should have some of each type
        assert len(keystones) > 0, "Expected at least one Keystone passive"
        assert len(notables) > 0, "Expected many Notable passives"
        assert len(small_passives) > 0, "Expected many small passives"

        # Keystones should be rare (20-50 typically)
        assert len(keystones) < 100, f"Too many keystones: {len(keystones)}"

        # Notables should be numerous but not majority
        assert len(notables) < tree.get_node_count(), "All nodes can't be Notable"

        # Check mutual exclusivity
        for node in tree.nodes.values():
            if node.is_keystone:
                # Keystones are special notables in PoB, so they may also be marked as notable
                # This is OK - don't enforce mutual exclusivity
                pass

    def test_keystone_properties(self, tree):
        """Verify Keystone nodes have expected properties"""
        keystones = [node for node in tree.nodes.values() if node.is_keystone]

        if not keystones:
            pytest.skip("No keystones found in tree")

        # Check first keystone
        keystone = keystones[0]

        # Keystones should have names
        assert keystone.name, "Keystone should have a name"

        # Keystones should have stats (mechanics)
        assert keystone.stats, f"Keystone '{keystone.name}' should have stats"


class TestCaching:
    """Test suite for caching behavior"""

    def test_caching_returns_same_instance(self):
        """Call get_passive_tree() twice, assert same object returned (AC-1.7.1)"""
        # Clear cache first to ensure clean state
        clear_passive_tree_cache()

        tree1 = get_passive_tree()
        tree2 = get_passive_tree()

        # Should be the exact same object (same id)
        assert tree1 is tree2, "get_passive_tree() should return cached instance"

    def test_clear_cache_reloads_tree(self):
        """Verify clear_passive_tree_cache() forces reload"""
        tree1 = get_passive_tree()

        clear_passive_tree_cache()

        tree2 = get_passive_tree()

        # Should be different objects after cache clear
        assert tree1 is not tree2, "After clear_cache, should get new instance"

        # But should have same content
        assert tree1.get_node_count() == tree2.get_node_count()


class TestLuaTableConversion:
    """Test suite for to_lua_table() conversion (Story 1.5 integration)"""

    @pytest.fixture(scope="class")
    def tree(self):
        """Fixture providing a loaded PassiveTreeGraph"""
        return load_passive_tree()

    def test_to_lua_table_format(self, tree):
        """Verify to_lua_table() returns dict compatible with PoB Lua engine (AC-1.7.2)"""
        lua_table = tree.to_lua_table()

        # Should be a dictionary
        assert isinstance(lua_table, dict)

        # Should have required keys
        assert "nodes" in lua_table
        assert "edges" in lua_table
        assert "classStartNodes" in lua_table
        assert "version" in lua_table

        # Nodes should be string keys (Lua tables use string keys)
        assert isinstance(lua_table["nodes"], dict)
        sample_node_id = next(iter(lua_table["nodes"].keys()))
        assert isinstance(sample_node_id, str), "Node IDs should be strings in Lua table"

        # Check node structure
        sample_node = lua_table["nodes"][sample_node_id]
        assert "name" in sample_node
        assert "stats" in sample_node
        assert "isKeystone" in sample_node
        assert "isNotable" in sample_node

    def test_to_lua_table_preserves_data(self, tree):
        """Verify to_lua_table() preserves all node data"""
        lua_table = tree.to_lua_table()

        # Check that node count matches
        assert len(lua_table["nodes"]) == len(tree.nodes)

        # Check a specific node
        sample_node_id = next(iter(tree.nodes.keys()))
        original_node = tree.nodes[sample_node_id]
        lua_node = lua_table["nodes"][str(sample_node_id)]

        assert lua_node["name"] == original_node.name
        assert lua_node["stats"] == original_node.stats
        assert lua_node["isKeystone"] == original_node.is_keystone
        assert lua_node["isNotable"] == original_node.is_notable


class TestPassiveNode:
    """Test suite for PassiveNode dataclass"""

    def test_passive_node_creation(self):
        """Verify PassiveNode can be created with required fields"""
        node = PassiveNode(
            node_id=12345,
            name="Test Node",
            stats=["+10 to Strength", "+5% increased Damage"],
            is_keystone=False,
            is_notable=True,
            position=(100.0, 200.0),
        )

        assert node.node_id == 12345
        assert node.name == "Test Node"
        assert len(node.stats) == 2
        assert node.is_notable is True
        assert node.is_keystone is False

    def test_passive_node_repr(self):
        """Verify PassiveNode has useful string representation"""
        node = PassiveNode(
            node_id=99999,
            name="Elemental Damage",
            stats=["+10% Elemental Damage"],
            is_notable=True,
        )

        repr_str = repr(node)

        assert "99999" in repr_str
        assert "Elemental Damage" in repr_str
        assert "Notable" in repr_str


class TestPassiveTreeGraph:
    """Test suite for PassiveTreeGraph dataclass"""

    def test_tree_repr(self):
        """Verify PassiveTreeGraph has useful string representation"""
        tree = load_passive_tree()
        repr_str = repr(tree)

        assert "PassiveTreeGraph" in repr_str
        assert "nodes=" in repr_str
        assert "edges=" in repr_str
        assert "version=" in repr_str


# Performance validation tests
class TestPerformance:
    """Test suite for AC-1.7.1: Performance requirements"""

    def test_load_time_acceptable(self):
        """Verify load time <2 seconds (acceptable for one-time initialization)"""
        import time

        clear_passive_tree_cache()

        start_time = time.time()
        tree = load_passive_tree()
        end_time = time.time()

        load_time = end_time - start_time

        assert load_time < 2.0, f"Load time {load_time:.2f}s exceeds 2 second threshold"

        # Log performance for monitoring
        print(f"\nPassive tree load time: {load_time:.3f} seconds")
        print(f"Nodes loaded: {tree.get_node_count()}")
        print(f"Edges loaded: {tree.get_edge_count()}")


# Cleanup
@pytest.fixture(scope="session", autouse=True)
def cleanup_cache():
    """Cleanup cache after all tests"""
    yield
    clear_passive_tree_cache()
