"""Generate Degraded Builds for Epic 2 Validation - BFS Truncation Approach

This script uses BFS to create degraded builds:
1. Load poeninja builds
2. Do BFS from class start through allocated nodes
3. Keep only first N nodes encountered (truncate the BFS traversal)
4. This guarantees connectivity while degrading the build

This creates builds that optimizer can improve by adding the missing nodes back.

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
from collections import deque

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


def bfs_truncate(nodes: Set[int], class_start: int, target_count: int, tree) -> Set[int]:
    """Use BFS to keep only first N nodes from class start.

    Args:
        nodes: Original allocated nodes
        class_start: Class starting node
        target_count: How many nodes to keep
        tree: PassiveTreeGraph

    Returns:
        Subset of nodes (connected from class start)
    """
    if class_start not in nodes:
        return set()

    visited = []
    visited_set = {class_start}
    queue = deque([class_start])

    # BFS traversal
    while queue and len(visited) < target_count:
        current = queue.popleft()
        visited.append(current)

        # Get neighbors that are in allocated set
        neighbors = [n for n in tree.get_neighbors(current) if n in nodes and n not in visited_set]

        # Randomize order to avoid always taking the same path
        random.shuffle(neighbors)

        for neighbor in neighbors:
            if len(visited) >= target_count:
                break
            visited_set.add(neighbor)
            queue.append(neighbor)

    return set(visited[:target_count])


def degrade_build_bfs(
    build: BuildData,
    xml_str: str,
    target_nodes: int,
    tree,
    class_start: int
) -> Tuple[str, int]:
    """Keep only first N nodes via BFS from class start.

    Args:
        build: Original BuildData
        xml_str: Original XML string
        target_nodes: Number of nodes to keep
        tree: PassiveTreeGraph
        class_start: Class starting node ID

    Returns:
        Tuple of (modified XML, nodes removed)
    """
    if target_nodes >= len(build.passive_nodes):
        logger.warning(f"Target {target_nodes} >= current {len(build.passive_nodes)}, no degradation")
        return xml_str, 0

    if target_nodes < 1:
        target_nodes = 1

    # BFS truncate to keep only target_nodes
    kept_nodes = bfs_truncate(build.passive_nodes, class_start, target_nodes, tree)

    if len(kept_nodes) == 0:
        logger.error("BFS resulted in 0 nodes!")
        return xml_str, 0

    actual_removed = len(build.passive_nodes) - len(kept_nodes)

    # Convert to sorted comma-separated string
    new_nodes_str = ",".join(str(n) for n in sorted(kept_nodes))

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

    # Degradation strategy - keep a percentage of nodes
    # HIP: Keep ~50-60% of nodes (remove 40-50%)
    # MIP: Keep ~70-80% of nodes (remove 20-30%)
    # LIP: Keep ~85-95% of nodes (remove 5-15%)

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

            # Calculate how many nodes to KEEP
            original_count = len(build.passive_nodes)

            if difficulty == 'HIP':
                # Keep 50-60% of nodes
                keep_pct = random.uniform(0.50, 0.60)
            elif difficulty == 'MIP':
                # Keep 70-80% of nodes
                keep_pct = random.uniform(0.70, 0.80)
            else:  # LIP
                # Keep 85-95% of nodes
                keep_pct = random.uniform(0.85, 0.95)

            target_nodes = max(1, int(original_count * keep_pct))

            # Degrade build via BFS truncation
            degraded_xml, actual_removed = degrade_build_bfs(
                build, xml_str, target_nodes, tree, class_start
            )

            if actual_removed == 0:
                logger.warning(f"  Skipping - could not degrade")
                continue

            # Save degraded build
            base_name = parity_file.stem
            output_name = f"{base_name}_degraded_{difficulty.lower()}.xml"
            output_path = output_dir / output_name

            output_path.write_text(degraded_xml, encoding='utf-8')

            final_node_count = original_count - actual_removed
            unallocated = max(0, build.level - 1 - final_node_count)

            degraded_builds.append({
                "filename": output_name,
                "source": parity_file.name,
                "difficulty": difficulty,
                "original_nodes": original_count,
                "nodes_removed": actual_removed,
                "degraded_nodes": final_node_count,
                "removal_pct": round(actual_removed / original_count * 100, 1),
                "unallocated_points": unallocated,
                "level": build.level,
                "class": build.character_class.value
            })

            logger.info(f"  Created {difficulty} build: kept {final_node_count}/{original_count} nodes ({actual_removed} removed, {round(actual_removed/original_count*100, 1)}%)")
            logger.info(f"  ~{unallocated} unallocated points available")
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
        "description": "Degraded builds for Epic 2 validation - BFS truncation approach",
        "strategy": "BFS from class start, keep first N nodes (HIP: 50-60%, MIP: 70-80%, LIP: 85-95%)",
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
    logger.info(f"  HIP: {manifest['difficulty_distribution']['HIP']} builds (50-60% nodes kept)")
    logger.info(f"  MIP: {manifest['difficulty_distribution']['MIP']} builds (70-80% nodes kept)")
    logger.info(f"  LIP: {manifest['difficulty_distribution']['LIP']} builds (85-95% nodes kept)")
    logger.info(f"\nBuilds saved to: {output_dir}")
    logger.info(f"Manifest: {manifest_path}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
