"""
Passive Tree Graph Loader and Data Model

This module provides functionality to load and navigate the Path of Exile 2 passive skill tree.
It loads tree data from PoB engine JSON files and provides a graph structure for optimization algorithms.

Story: 1.7 - Load Passive Tree Graph
Author: Dev Agent (Amelia)
Date: 2025-10-20
"""

import json
import logging
import os
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# Module-level cache for singleton pattern
_PASSIVE_TREE_CACHE: Optional['PassiveTreeGraph'] = None


@dataclass
class PassiveNode:
    """
    Single passive skill node in the tree.

    Attributes:
        node_id: Unique identifier for this node
        name: Display name of the passive skill
        stats: List of stat modifiers this node provides (e.g., "+10 to Strength")
        is_keystone: True if this is a Keystone passive (major unique mechanic)
        is_notable: True if this is a Notable passive (medium-sized passive)
        is_mastery: True if this is a Mastery node (currently unused in PoE 2)
        position: (x, y) coordinates for visualization
        icon: Icon file path for UI display
        orbit: Orbit ring number (distance from group center)
        orbit_index: Position within the orbit
        group_id: ID of the visual group this node belongs to
    """
    node_id: int
    name: str
    stats: List[str]
    is_keystone: bool = False
    is_notable: bool = False
    is_mastery: bool = False
    position: Tuple[float, float] = (0.0, 0.0)
    icon: str = ""
    orbit: int = 0
    orbit_index: int = 0
    group_id: Optional[int] = None

    def __repr__(self) -> str:
        node_type = "Keystone" if self.is_keystone else "Notable" if self.is_notable else "Small"
        return f"PassiveNode({self.node_id}, '{self.name}', {node_type})"


@dataclass
class PassiveTreeGraph:
    """
    Complete passive tree graph structure.

    Provides a graph representation of the passive skill tree with nodes and edges,
    enabling pathfinding, connectivity validation, and tree navigation for optimization.

    Attributes:
        nodes: Mapping from node_id to PassiveNode objects
        edges: Adjacency list mapping node_id to set of connected node_ids
        class_start_nodes: Mapping from class name to starting node_id
        tree_version: Version string of the loaded tree data (e.g., "0_3")
    """
    nodes: Dict[int, PassiveNode] = field(default_factory=dict)
    edges: Dict[int, Set[int]] = field(default_factory=dict)
    class_start_nodes: Dict[str, int] = field(default_factory=dict)
    tree_version: str = "unknown"

    def get_neighbors(self, node_id: int) -> Set[int]:
        """
        Get all node IDs directly connected to the given node.

        Args:
            node_id: The node to query

        Returns:
            Set of node IDs connected to this node (empty set if node not found)
        """
        return self.edges.get(node_id, set())

    def is_connected(self, from_node: int, to_node: int, allocated: Set[int]) -> bool:
        """
        Check if path exists from from_node to to_node using only allocated nodes.

        Uses Breadth-First Search (BFS) to determine connectivity. This is essential
        for validating that allocated passive nodes form a valid connected tree from
        the class starting position (no orphan nodes).

        Args:
            from_node: Starting node ID (usually class starting position)
            to_node: Target node ID to check connectivity
            allocated: Set of allocated node IDs (path must use only these)

        Returns:
            True if connected path exists, False otherwise

        Example:
            >>> tree = get_passive_tree()
            >>> allocated = {1000, 1001, 1002, 1003}
            >>> tree.is_connected(1000, 1003, allocated)
            True
        """
        # Trivial case: same node
        if from_node == to_node:
            return True

        # Check that both nodes exist and are in allocated set
        if from_node not in allocated or to_node not in allocated:
            return False

        # BFS implementation
        visited: Set[int] = {from_node}
        queue: deque = deque([from_node])

        while queue:
            current = queue.popleft()

            # Check all neighbors of current node
            for neighbor in self.get_neighbors(current):
                # Only traverse through allocated nodes
                if neighbor in allocated and neighbor not in visited:
                    if neighbor == to_node:
                        return True
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False

    def validate_tree_connectivity(self, allocated_nodes: Set[int], class_name: str) -> bool:
        """
        Validate that all allocated nodes are connected to the class starting position.

        Args:
            allocated_nodes: Set of allocated node IDs to validate
            class_name: Character class name (e.g., "Witch", "Warrior")

        Returns:
            True if all nodes are connected, False if any orphan nodes exist

        Raises:
            ValueError: If class_name is not recognized or has no starting node
        """
        if class_name not in self.class_start_nodes:
            raise ValueError(f"Unknown class: {class_name}. Available classes: {list(self.class_start_nodes.keys())}")

        start_node = self.class_start_nodes[class_name]

        # Verify start node is in allocated set
        if start_node not in allocated_nodes:
            logger.warning(f"Class starting node {start_node} not in allocated set for {class_name}")
            return False

        # Check connectivity for each allocated node
        for node_id in allocated_nodes:
            if not self.is_connected(start_node, node_id, allocated_nodes):
                logger.warning(f"Orphan node detected: {node_id} is not connected to start node {start_node}")
                return False

        return True

    def to_lua_table(self) -> Dict:
        """
        Convert PassiveTreeGraph to Lua-compatible table format for PoB engine.

        This method provides the data structure required by Story 1.5 (Build Calculation)
        for PoB engine initialization via build.spec.tree parameter.

        Returns:
            Dictionary representing Lua table structure compatible with PoB engine

        Example:
            >>> tree = get_passive_tree()
            >>> lua_data = tree.to_lua_table()
            >>> # Pass to PoB: build.spec.tree = lua_data
        """
        # Convert nodes to Lua-compatible format
        lua_nodes = {}
        for node_id, node in self.nodes.items():
            lua_nodes[str(node_id)] = {
                "name": node.name,
                "stats": node.stats,
                "isKeystone": node.is_keystone,
                "isNotable": node.is_notable,
                "isMastery": node.is_mastery,
                "icon": node.icon,
                "group": node.group_id,
                "orbit": node.orbit,
                "orbitIndex": node.orbit_index,
            }

        # Convert edges to Lua-compatible format (array of connections)
        lua_edges = {}
        for node_id, neighbors in self.edges.items():
            lua_edges[str(node_id)] = [{"id": neighbor} for neighbor in neighbors]

        # Add character class base stats (required by PoB CalcSetup.lua:591)
        # IMPORTANT: PoB uses NUMERIC indices (0-based) to access classes, matching XML classId
        # These values come from PoE 2 tree.lua classes definitions (base stats at level 1)
        character_classes = {
            0: {"base_str": 7, "base_dex": 15, "base_int": 7, "name": "Ranger"},  # Ranger: DEX-focused
            1: {"base_str": 7, "base_dex": 11, "base_int": 11, "name": "Huntress"},  # Huntress: DEX/INT hybrid
            2: {"base_str": 15, "base_dex": 7, "base_int": 7, "name": "Warrior"},  # Warrior: STR-focused
            3: {"base_str": 11, "base_dex": 11, "base_int": 7, "name": "Mercenary"},  # Mercenary: STR/DEX hybrid
            4: {"base_str": 7, "base_dex": 7, "base_int": 15, "name": "Witch"},  # Witch: INT-focused
            5: {"base_str": 7, "base_dex": 7, "base_int": 15, "name": "Sorceress"},  # Sorceress: INT-focused
            6: {"base_str": 11, "base_dex": 7, "base_int": 11, "name": "Monk"}  # Monk: STR/INT hybrid
        }

        return {
            "nodes": lua_nodes,
            "edges": lua_edges,
            "classStartNodes": self.class_start_nodes,
            "classes": character_classes,
            "version": self.tree_version,
        }

    def get_node_count(self) -> int:
        """Get total number of nodes in the tree."""
        return len(self.nodes)

    def get_edge_count(self) -> int:
        """Get total number of edges (connections) in the tree."""
        return sum(len(neighbors) for neighbors in self.edges.values()) // 2  # Divide by 2 for undirected graph

    def __repr__(self) -> str:
        return f"PassiveTreeGraph(nodes={len(self.nodes)}, edges={self.get_edge_count()}, version='{self.tree_version}')"


def load_passive_tree(tree_version: str = "0_3") -> PassiveTreeGraph:
    """
    Load PoE 2 passive tree structure from PoB data files.

    Loads tree data from external/pob-engine/src/TreeData/{version}/tree.json
    and constructs a PassiveTreeGraph with nodes, edges, and class starting positions.

    Args:
        tree_version: Tree data version to load (default: "0_3" for latest PoE 2)

    Returns:
        PassiveTreeGraph with fully populated nodes, edges, and class starting data

    Raises:
        FileNotFoundError: If tree.json file not found at expected location
        json.JSONDecodeError: If tree.json file is corrupted or invalid
        ValueError: If tree data is missing required fields

    Example:
        >>> tree = load_passive_tree()
        >>> print(f"Loaded {tree.get_node_count()} nodes")
        Loaded 4118 nodes
    """
    # Determine tree data file path
    project_root = Path(__file__).parent.parent.parent
    tree_file = project_root / "external" / "pob-engine" / "src" / "TreeData" / tree_version / "tree.json"

    if not tree_file.exists():
        raise FileNotFoundError(
            f"PassiveTree data file not found: {tree_file}\n"
            f"Expected location: external/pob-engine/src/TreeData/{tree_version}/tree.json\n"
            "Ensure the pob-engine submodule is initialized: git submodule update --init"
        )

    logger.info(f"Loading passive tree data from: {tree_file}")

    # Load JSON data
    try:
        with open(tree_file, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Failed to parse tree.json: {e.msg}",
            e.doc,
            e.pos
        ) from e

    # Validate required fields
    if 'nodes' not in tree_data:
        raise ValueError("Tree data missing required 'nodes' field")
    if 'groups' not in tree_data:
        raise ValueError("Tree data missing required 'groups' field")

    # Extract node and group data
    raw_nodes = tree_data['nodes']
    raw_groups = tree_data['groups']

    logger.info(f"Found {len(raw_nodes)} nodes in tree data")

    # Build PassiveNode objects
    nodes: Dict[int, PassiveNode] = {}
    edges: Dict[int, Set[int]] = {}

    for node_id_str, node_data in raw_nodes.items():
        node_id = int(node_id_str)

        # Extract group position for node coordinates
        group_id = node_data.get('group')
        position = (0.0, 0.0)
        if group_id is not None and group_id < len(raw_groups) and raw_groups[group_id]:
            group = raw_groups[group_id]
            position = (group.get('x', 0.0), group.get('y', 0.0))

        # Create PassiveNode
        node = PassiveNode(
            node_id=node_id,
            name=node_data.get('name', ''),
            stats=node_data.get('stats', []),
            is_keystone=node_data.get('isKeystone', False),
            is_notable=node_data.get('isNotable', False),
            is_mastery=node_data.get('isMastery', False),
            position=position,
            icon=node_data.get('icon', ''),
            orbit=node_data.get('orbit', 0),
            orbit_index=node_data.get('orbitIndex', 0),
            group_id=group_id,
        )
        nodes[node_id] = node

        # Build edges (adjacency list)
        connections = node_data.get('connections', [])
        neighbors: Set[int] = set()
        for conn in connections:
            neighbor_id = conn.get('id')
            if neighbor_id is not None:
                neighbors.add(neighbor_id)
        edges[node_id] = neighbors

    # Ensure edges are bidirectional (undirected graph)
    for node_id, neighbors in list(edges.items()):
        for neighbor_id in neighbors:
            if neighbor_id not in edges:
                edges[neighbor_id] = set()
            edges[neighbor_id].add(node_id)

    # Extract class starting nodes
    # Note: PoE 2 class starts are determined by inspecting nodes near origin
    # or through ascendancy data. For now, we'll use a heuristic approach.
    class_start_nodes = _extract_class_starting_nodes(tree_data, nodes)

    logger.info(f"Loaded {len(nodes)} passive tree nodes, {sum(len(neighbors) for neighbors in edges.values()) // 2} connections")
    logger.info(f"Class starting nodes: {class_start_nodes}")

    # Log memory footprint
    try:
        size_mb = sys.getsizeof(nodes) / (1024 * 1024)
        logger.info(f"Passive tree cache size: {size_mb:.2f} MB (estimated)")
    except Exception:
        pass  # sys.getsizeof may not work on all platforms

    return PassiveTreeGraph(
        nodes=nodes,
        edges=edges,
        class_start_nodes=class_start_nodes,
        tree_version=tree_version
    )


def _extract_class_starting_nodes(tree_data: Dict, nodes: Dict[int, PassiveNode]) -> Dict[str, int]:
    """
    Extract class starting node positions from tree data.

    This is a helper function to determine where each character class begins in the tree.
    PoE 2 uses ascendancy starting nodes to determine class positions.

    Args:
        tree_data: Raw tree JSON data
        nodes: Parsed PassiveNode dictionary

    Returns:
        Dictionary mapping class names to starting node IDs
    """
    class_starts: Dict[str, int] = {}

    # Strategy 1: Look for ascendancy start nodes
    # Each class has ascendancy nodes that indicate their starting area
    ascendancy_starts = {}
    for node_id, node in nodes.items():
        # Check if this is an ascendancy start node
        if hasattr(node, 'is_ascendancy_start') or 'ascendancystart' in node.name.lower():
            ascendancy_starts[node_id] = node.name

    # Strategy 2: Use predefined class-to-ascendancy mapping
    # Based on PoE 2 Early Access class structure
    class_ascendancy_map = {
        "Ranger": ["Deadeye", "Pathfinder"],
        "Huntress": ["Amazon"],
        "Warrior": ["Titan", "Brute"],
        "Mercenary": ["Witchhunter", "Gambler"],
        "Witch": ["Blood Mage", "Infernalist"],
        "Sorceress": ["Stormweaver", "Master of the Elements"],
        "Monk": ["Acolyte of Chayula", "Ritualist"],
    }

    # Find nodes that match ascendancy names
    for node_id, node in nodes.items():
        for class_name, ascendancy_names in class_ascendancy_map.items():
            if node.name in ascendancy_names:
                # This is an ascendancy start node - use a nearby node as class start
                # For now, use the ascendancy node itself as a placeholder
                if class_name not in class_starts:
                    class_starts[class_name] = node_id
                    logger.debug(f"Found class start for {class_name}: node {node_id} ({node.name})")

    # Strategy 3: Fallback to hardcoded positions if needed
    # These are approximate starting node IDs based on tree analysis
    # TODO: Replace with actual class starting nodes from PoB source
    if not class_starts:
        logger.warning("Could not auto-detect class starting nodes, using fallback values")
        class_starts = {
            "Ranger": 46990,  # Deadeye start
            "Huntress": 41736,  # Amazon start
            "Warrior": 32534,  # Titan start
            "Mercenary": 7120,  # Witchhunter start
            "Witch": 59822,  # Blood Mage start
            "Sorceress": 9994,  # Master of Elements start
            "Monk": 74,  # Acolyte of Chayula start
        }

    return class_starts


def get_passive_tree(tree_version: str = "0_3") -> PassiveTreeGraph:
    """
    Get cached PassiveTreeGraph instance, loading on first call.

    Implements singleton pattern to ensure passive tree is only loaded once
    per application lifetime. Subsequent calls return the cached instance.

    Args:
        tree_version: Tree data version to load (default: "0_3")

    Returns:
        Cached PassiveTreeGraph instance

    Example:
        >>> tree1 = get_passive_tree()
        >>> tree2 = get_passive_tree()
        >>> assert tree1 is tree2  # Same instance
    """
    global _PASSIVE_TREE_CACHE

    if _PASSIVE_TREE_CACHE is None:
        logger.info("Loading passive tree data (first call)")
        _PASSIVE_TREE_CACHE = load_passive_tree(tree_version)

    return _PASSIVE_TREE_CACHE


def clear_passive_tree_cache() -> None:
    """
    Clear the passive tree cache.

    Useful for testing or when switching between tree versions.
    The next call to get_passive_tree() will reload from disk.
    """
    global _PASSIVE_TREE_CACHE
    _PASSIVE_TREE_CACHE = None
    logger.info("Passive tree cache cleared")


# Convenience exports
__all__ = [
    'PassiveNode',
    'PassiveTreeGraph',
    'load_passive_tree',
    'get_passive_tree',
    'clear_passive_tree_cache',
]
