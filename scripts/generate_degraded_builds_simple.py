"""Generate Degraded Builds for Epic 2 Validation - Simple Approach

This script uses a simpler degradation strategy:
1. Load poeninja builds
2. Randomly remove N nodes (without checking connectivity)
3. Keep only the largest connected component from class start
4. Add unallocated points by keeping level same but with fewer nodes

This guarantees builds with optimization potential since we're intentionally
making them worse.

Reference: docs/validation/neighbor-generation-diagnosis-2025-11-01.md
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
    """Load BuildData and raw XML from file."""
    if not xml_path.exists():
        raise FileNotFoundError(f"Build file not found: {xml_path}")

    xml_str = xml_path.read_text(encoding='utf-8')
    data = parse_xml(xml_str)
    pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
    if not pob_root:
        raise ValueError("Missing PathOfBuilding root element")

    build_section = pob_root.get("Build")
    if not build_section:
        raise ValueError("Missing Build section")

    class_name = build_section.get("@className")
    character_class = CharacterClass(class_name) if class_name else CharacterClass.WITCH

    level = int(build_section.get("@level", "90"))

    ascendancy = build_section.get("@ascendClassName")
    if ascendancy == "None":
        ascendancy = None

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


def get_connected_component(nodes: Set[int], class_start: int, tree) -> Set[int]:
    """Get all nodes connected to class_start via BFS.

    Args:
        nodes: Set of node IDs
        class_start: Starting node ID
        tree: PassiveTreeGraph

    Returns:
        Set of nodes reachable from class_start
    """
    if class_start not in nodes:
        return set()

    visited = {class_start}
    queue = [class_start]

    while queue:
        current = queue.pop(0)
        neighbors = tree.get_neighbors(current)

        for neighbor in neighbors:
            if neighbor in nodes and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return visited


def degrade_build_simple(
    build: BuildData,
    xml_str: str,
    nodes_to_remove: int,
    tree,
    class_start: int
) -> Tuple[str, int]:
    """Remove random nodes and keep connected component.

    Args:
        build: Original BuildData
        xml_str: Original XML string
        nodes_to_remove: Number of nodes to attempt to remove
        tree: PassiveTreeGraph
        class_start: Class starting node ID

    Returns:
        Tuple of (modified XML, actual nodes removed)
    """
    # Start with all nodes except class start (never remove class start)
    removable_nodes = build.passive_nodes - {class_start}

    if len(removable_nodes) < nodes_to_remove:
        nodes_to_remove = len(removable_nodes)

    if nodes_to_remove == 0:
        logger.warning("No nodes to remove")
        return xml_str, 0

    # Randomly remove N nodes
    to_remove = set(random.sample(sorted(removable_nodes), nodes_to_remove))

    # Keep remaining nodes
    remaining = build.passive_nodes - to_remove

    # Get connected component from class start
    connected = get_connected_component(remaining, class_start, tree)

    # Final node set
    final_nodes = connected

    actual_removed = len(build.passive_nodes) - len(final_nodes)

    # Convert to sorted comma-separated string
    new_nodes_str = ",".join(str(n) for n in sorted(final_nodes))

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

    return modified_xml, actual_removed


def main():
    """Generate degraded builds from parity builds."""
    # Set random seed for reproducibility
    random.seed(42)

    # Paths
    parity_dir = repo_root / "tests" / "fixtures" / "parity_builds"
    output_dir = repo_root / "tests" / "fixtures" / "optimization_corpus" / "degraded"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load passive tree
    logger.info("Loading passive tree...")
    tree = get_passive_tree()

    # Find poeninja builds
    poeninja_builds = sorted(parity_dir.glob("*_poeninja.xml"))

    logger.info(f"Found {len(poeninja_builds)} poeninja builds")

    if len(poeninja_builds) == 0:
        logger.error("No poeninja builds found!")
        return

    degraded_builds = []

    # Degradation strategy - cycle through difficulties
    difficulty_cycle = ['HIP', 'MIP', 'LIP']

    for idx, parity_file in enumerate(poeninja_builds):
        try:
            logger.info(f"\nProcessing: {parity_file.name}")

            # Load build
            build, xml_str = load_build_from_xml_file(parity_file)

            logger.info(f"  Level {build.level}, {len(build.passive_nodes)} nodes allocated")

            # Get class start node
            class_start = tree.class_start_nodes.get(build.character_class.value)
            if class_start is None:
                logger.error(f"  ERROR: No class start for {build.character_class.value}")
                continue

            # Determine difficulty
            difficulty = difficulty_cycle[idx % len(difficulty_cycle)]

            # Set removal target based on difficulty
            if difficulty == 'HIP':
                removal_target = random.randint(15, 20)
            elif difficulty == 'MIP':
                removal_target = random.randint(8, 12)
            else:  # LIP
                removal_target = random.randint(3, 5)

            # Degrade build (simple approach)
            degraded_xml, actual_removed = degrade_build_simple(
                build, xml_str, removal_target, tree, class_start
            )

            if actual_removed == 0:
                logger.warning(f"  Skipping - could not remove any nodes")
                continue

            # Save degraded build
            base_name = parity_file.stem
            output_name = f"{base_name}_degraded_{difficulty.lower()}.xml"
            output_path = output_dir / output_name

            output_path.write_text(degraded_xml, encoding='utf-8')

            final_node_count = len(build.passive_nodes) - actual_removed
            unallocated = max(0, build.level - 1 - final_node_count)

            degraded_builds.append({
                "filename": output_name,
                "source": parity_file.name,
                "difficulty": difficulty,
                "original_nodes": len(build.passive_nodes),
                "nodes_removed": actual_removed,
                "degraded_nodes": final_node_count,
                "unallocated_points": unallocated,
                "level": build.level,
                "class": build.character_class.value
            })

            logger.info(f"  Created {difficulty} build: removed {actual_removed} nodes")
            logger.info(f"  Result: {final_node_count} nodes, ~{unallocated} unallocated points")
            logger.info(f"  Saved to: {output_path.name}")

        except Exception as e:
            logger.error(f"  ERROR processing {parity_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Save manifest
    manifest = {
        "version": "1.0",
        "created": "2025-11-01",
        "description": "Degraded builds for Epic 2 validation - simple random removal approach",
        "strategy": "Simple: Randomly remove N nodes, keep connected component from class start",
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
