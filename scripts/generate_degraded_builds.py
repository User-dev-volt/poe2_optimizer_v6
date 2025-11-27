"""Generate Degraded Builds for Epic 2 Validation

This script creates builds with intentional optimization potential by:
1. Loading existing parity builds (poeninja builds with items/skills/real DPS)
2. Removing a subset of allocated nodes
3. Saving degraded builds that optimizer should improve

Approach (Option C - Hybrid from neighbor-generation-diagnosis):
- HIP (High Improvement Potential): Remove 15-20 nodes
- MIP (Medium Improvement Potential): Remove 8-12 nodes
- LIP (Low Improvement Potential): Remove 3-5 nodes

Reference: docs/validation/neighbor-generation-diagnosis-2025-11-01.md lines 199-222
"""

import sys
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

import json
import logging
import random
import xml.etree.ElementTree as ET
from typing import Set, Dict, Any, List, Tuple

from src.models.build_data import BuildData, CharacterClass
from src.parsers.xml_utils import parse_xml
from src.calculator.passive_tree import get_passive_tree

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def load_build_from_xml_file(xml_path: Path) -> Tuple[BuildData, str]:
    """Load BuildData and raw XML from file.

    Args:
        xml_path: Path to PoB XML file

    Returns:
        Tuple of (BuildData, raw_xml_string)
    """
    if not xml_path.exists():
        raise FileNotFoundError(f"Build file not found: {xml_path}")

    # Read raw XML
    xml_str = xml_path.read_text(encoding='utf-8')

    # Parse to BuildData
    data = parse_xml(xml_str)
    pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
    if not pob_root:
        raise ValueError("Missing PathOfBuilding root element")

    build_section = pob_root.get("Build")
    if not build_section:
        raise ValueError("Missing Build section")

    # Extract character data
    class_name = build_section.get("@className")
    character_class = CharacterClass(class_name) if class_name else CharacterClass.WITCH

    level = int(build_section.get("@level", "90"))

    ascendancy = build_section.get("@ascendClassName")
    if ascendancy == "None":
        ascendancy = None

    # Extract passive tree
    tree_section = pob_root.get("Tree", {})
    spec = tree_section.get("Spec", {}) if isinstance(tree_section, dict) else {}
    nodes_str = spec.get("@nodes", "") if isinstance(spec, dict) else ""

    passive_nodes: Set[int] = set()
    if nodes_str:
        try:
            passive_nodes = set(int(node_id.strip()) for node_id in nodes_str.split(",") if node_id.strip())
        except ValueError:
            pass

    build_data = BuildData(
        character_class=character_class,
        level=level,
        ascendancy=ascendancy,
        passive_nodes=passive_nodes,
        items=[],
        skills=[],
        tree_version="0_1"
    )

    return build_data, xml_str


def find_removable_nodes(build: BuildData, tree, class_start: int) -> Set[int]:
    """Find nodes that can be removed without breaking tree connectivity.

    This implements the same logic as neighbor_generator._find_removable_nodes
    but as a standalone function for build degradation.

    Args:
        build: BuildData object
        tree: PassiveTreeGraph
        class_start: Class starting node ID

    Returns:
        Set of removable node IDs
    """
    removable = set()

    for node in build.passive_nodes:
        if node == class_start:
            continue  # Never remove class start

        # Test: remove node, check if tree stays connected
        temp_allocated = build.passive_nodes - {node}

        # Check if all nodes still reachable from class_start
        if _is_tree_valid(tree, temp_allocated, class_start):
            removable.add(node)

    return removable


def _is_tree_valid(tree, allocated_nodes: Set[int], class_start: int) -> bool:
    """Check if all nodes are connected from class_start.

    Args:
        tree: PassiveTreeGraph
        allocated_nodes: Set of allocated node IDs
        class_start: Class starting node ID

    Returns:
        True if tree is valid (all nodes reachable from start)
    """
    if not allocated_nodes:
        return True

    if class_start not in allocated_nodes:
        return False

    # BFS to check connectivity
    visited = {class_start}
    queue = [class_start]

    while queue:
        current = queue.pop(0)
        neighbors = tree.get_neighbors(current)

        for neighbor in neighbors:
            if neighbor in allocated_nodes and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    # All allocated nodes must be visited
    return visited == allocated_nodes


def degrade_build(
    build: BuildData,
    xml_str: str,
    nodes_to_remove: int,
    tree,
    class_start: int
) -> str:
    """Remove nodes from build and return modified XML.

    Args:
        build: Original BuildData
        xml_str: Original XML string
        nodes_to_remove: Number of nodes to remove
        tree: PassiveTreeGraph
        class_start: Class starting node ID

    Returns:
        Modified XML string with nodes removed
    """
    # Find removable nodes
    removable = find_removable_nodes(build, tree, class_start)

    if len(removable) < nodes_to_remove:
        logger.warning(f"Only {len(removable)} removable nodes, requested {nodes_to_remove}")
        nodes_to_remove = len(removable)

    if nodes_to_remove == 0:
        logger.warning("No removable nodes found - returning original")
        return xml_str

    # Randomly select nodes to remove
    to_remove = set(random.sample(sorted(removable), nodes_to_remove))

    # Create new node set
    new_nodes = build.passive_nodes - to_remove

    # Convert to sorted comma-separated string
    new_nodes_str = ",".join(str(n) for n in sorted(new_nodes))

    # Parse XML and modify
    root = ET.fromstring(xml_str)

    # Find Tree/Spec element and update nodes attribute
    for tree_elem in root.findall(".//Tree/Spec"):
        tree_elem.set("nodes", new_nodes_str)

    # Convert back to string
    modified_xml = ET.tostring(root, encoding='unicode')

    # Add XML declaration
    if not modified_xml.startswith('<?xml'):
        modified_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + modified_xml

    return modified_xml


def get_class_start_node(character_class: CharacterClass, tree) -> int:
    """Get starting node ID for character class from passive tree.

    Args:
        character_class: CharacterClass enum
        tree: PassiveTreeGraph with class_start_nodes

    Returns:
        Starting node ID
    """
    # Get from tree's class_start_nodes dictionary
    return tree.class_start_nodes.get(character_class.value, 59822)


def main():
    """Generate degraded builds from parity builds."""
    # Paths
    parity_dir = repo_root / "tests" / "fixtures" / "parity_builds"
    output_dir = repo_root / "tests" / "fixtures" / "optimization_corpus" / "degraded"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load passive tree
    logger.info("Loading passive tree...")
    tree = get_passive_tree()

    # Find poeninja builds (the ones with items/skills/real DPS)
    poeninja_builds = sorted(parity_dir.glob("*_poeninja.xml"))

    logger.info(f"Found {len(poeninja_builds)} poeninja builds")

    if len(poeninja_builds) == 0:
        logger.error("No poeninja builds found!")
        return

    # Degradation strategy
    # Target: ~20 builds total (Alec said max 20)
    # From each poeninja build, create degraded versions

    degraded_builds = []

    # For each poeninja build, create 1 degraded version
    # Vary the difficulty to get a good distribution
    difficulty_cycle = ['HIP', 'MIP', 'LIP']  # Cycle through difficulties

    for idx, parity_file in enumerate(poeninja_builds):
        try:
            logger.info(f"\nProcessing: {parity_file.name}")

            # Load build
            build, xml_str = load_build_from_xml_file(parity_file)

            logger.info(f"  Level {build.level}, {len(build.passive_nodes)} nodes allocated")

            # Get class start node
            class_start = get_class_start_node(build.character_class, tree)

            # Determine difficulty for this build
            difficulty = difficulty_cycle[idx % len(difficulty_cycle)]

            # Set removal count based on difficulty
            if difficulty == 'HIP':
                nodes_to_remove = random.randint(15, 20)
            elif difficulty == 'MIP':
                nodes_to_remove = random.randint(8, 12)
            else:  # LIP
                nodes_to_remove = random.randint(3, 5)

            # Degrade build
            degraded_xml = degrade_build(build, xml_str, nodes_to_remove, tree, class_start)

            # Save degraded build
            base_name = parity_file.stem  # e.g., "ritualist_68_poeninja"
            output_name = f"{base_name}_degraded_{difficulty.lower()}.xml"
            output_path = output_dir / output_name

            output_path.write_text(degraded_xml, encoding='utf-8')

            degraded_builds.append({
                "filename": output_name,
                "source": parity_file.name,
                "difficulty": difficulty,
                "nodes_removed": nodes_to_remove,
                "original_nodes": len(build.passive_nodes),
                "degraded_nodes": len(build.passive_nodes) - nodes_to_remove,
                "level": build.level,
                "class": build.character_class.value
            })

            logger.info(f"  Created {difficulty} build: removed {nodes_to_remove} nodes")
            logger.info(f"  Saved to: {output_path.name}")

        except Exception as e:
            logger.error(f"  ERROR processing {parity_file.name}: {e}")
            continue

    # Save manifest
    manifest = {
        "version": "1.0",
        "created": "2025-11-01",
        "description": "Degraded builds for Epic 2 validation - optimizer should restore to near-original performance",
        "strategy": "Hybrid (Option C): Take poeninja builds, remove nodes, verify optimizer restores",
        "total_builds": len(degraded_builds),
        "difficulty_distribution": {
            "HIP": len([b for b in degraded_builds if b["difficulty"] == "HIP"]),
            "MIP": len([b for b in degraded_builds if b["difficulty"] == "MIP"]),
            "LIP": len([b for b in degraded_builds if b["difficulty"] == "LIP"])
        },
        "builds": degraded_builds
    }

    manifest_path = output_dir / "degraded_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')

    logger.info(f"\n{'='*60}")
    logger.info(f"SUCCESS: Generated {len(degraded_builds)} degraded builds")
    logger.info(f"  HIP: {manifest['difficulty_distribution']['HIP']} builds")
    logger.info(f"  MIP: {manifest['difficulty_distribution']['MIP']} builds")
    logger.info(f"  LIP: {manifest['difficulty_distribution']['LIP']} builds")
    logger.info(f"\nBuilds saved to: {output_dir}")
    logger.info(f"Manifest: {manifest_path}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
