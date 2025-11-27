"""Generate Baseline Stats for Epic 2 Validation

This script implements Task 5 from prep-sprint-status.yaml:
- Loads all builds from the optimization corpus
- Calculates baseline stats using Epic 1 calculator
- Records DPS, Life, EHP, allocated points, unallocated points
- Generates corpus-level statistics
- Saves to tests/fixtures/optimization_corpus/baseline_stats.json

Reference: docs/retrospectives/epic-002-retro-2025-10-31.md lines 453-457
"""

import sys
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

import json
import logging
from typing import Set, Dict, Any, List
from statistics import mean, median, stdev

from src.models.build_data import BuildData, CharacterClass
from src.calculator.build_calculator import calculate_build_stats
from src.parsers.xml_utils import parse_xml

# Configure logging - suppress MinimalCalc debug output
logging.basicConfig(
    level=logging.WARNING,  # Suppress INFO from other modules
    format='%(levelname)s: %(message)s'
)
# But enable INFO for this script only
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add console handler with INFO level for our logger
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(console)
logger.propagate = False  # Don't propagate to root logger


def load_build_from_xml_file(xml_path: Path) -> BuildData:
    """Load BuildData directly from XML file.

    Args:
        xml_path: Path to PoB XML file

    Returns:
        BuildData object

    Raises:
        FileNotFoundError: If XML file doesn't exist
        Exception: If parsing fails
    """
    if not xml_path.exists():
        raise FileNotFoundError(f"Build file not found: {xml_path}")

    # Read and parse XML
    xml_str = xml_path.read_text(encoding='utf-8')
    data = parse_xml(xml_str)

    # Extract build data
    pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
    if not pob_root:
        raise ValueError("Missing PathOfBuilding or PathOfBuilding2 root element")

    build_section = pob_root.get("Build")
    if not build_section:
        raise ValueError("Missing Build section in PoB XML")

    # Extract character data
    class_name = build_section.get("@className")
    character_class = CharacterClass(class_name) if class_name else CharacterClass.WITCH

    level_str = build_section.get("@level", "90")
    level = int(level_str)

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

    # Create BuildData
    return BuildData(
        character_class=character_class,
        level=level,
        ascendancy=ascendancy,
        passive_nodes=passive_nodes,
        tree_version=build_section.get("@targetVersion", "0_1"),
        build_name=build_section.get("@buildName"),
        items=[],
        skills=[]
    )


def calculate_corpus_statistics(build_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aggregate statistics across all builds.

    Args:
        build_stats: List of build stat dictionaries

    Returns:
        Dictionary with corpus-level statistics
    """
    # Extract numeric values
    dps_values = [b['total_dps'] for b in build_stats if b['total_dps'] > 0]
    life_values = [b['life'] for b in build_stats if b['life'] > 0]
    ehp_values = [b['effective_hp'] for b in build_stats if b['effective_hp'] > 0]
    allocated_values = [b['allocated_points'] for b in build_stats]
    unallocated_values = [b['unallocated_points'] for b in build_stats]
    level_values = [b['level'] for b in build_stats]

    stats = {
        'total_builds': len(build_stats),
        'builds_with_dps': len(dps_values),
        'builds_with_zero_dps': len([b for b in build_stats if b['total_dps'] == 0]),
        'dps_stats': {
            'mean': mean(dps_values) if dps_values else 0,
            'median': median(dps_values) if dps_values else 0,
            'min': min(dps_values) if dps_values else 0,
            'max': max(dps_values) if dps_values else 0,
            'stdev': stdev(dps_values) if len(dps_values) > 1 else 0
        },
        'life_stats': {
            'mean': mean(life_values) if life_values else 0,
            'median': median(life_values) if life_values else 0,
            'min': min(life_values) if life_values else 0,
            'max': max(life_values) if life_values else 0,
            'stdev': stdev(life_values) if len(life_values) > 1 else 0
        },
        'ehp_stats': {
            'mean': mean(ehp_values) if ehp_values else 0,
            'median': median(ehp_values) if ehp_values else 0,
            'min': min(ehp_values) if ehp_values else 0,
            'max': max(ehp_values) if ehp_values else 0,
            'stdev': stdev(ehp_values) if len(ehp_values) > 1 else 0
        },
        'allocated_points_stats': {
            'mean': mean(allocated_values),
            'median': median(allocated_values),
            'min': min(allocated_values),
            'max': max(allocated_values)
        },
        'unallocated_points_stats': {
            'mean': mean(unallocated_values),
            'median': median(unallocated_values),
            'min': min(unallocated_values),
            'max': max(unallocated_values),
            'builds_with_unallocated': len([v for v in unallocated_values if v > 0])
        },
        'level_stats': {
            'mean': mean(level_values),
            'median': median(level_values),
            'min': min(level_values),
            'max': max(level_values)
        }
    }

    return stats


def main():
    """Main execution function."""
    logger.info("="*80)
    logger.info("Epic 2 Baseline Stats Generator - Task 5")
    logger.info("="*80)

    # Paths
    corpus_dir = repo_root / "tests" / "fixtures" / "optimization_corpus"
    builds_dir = repo_root / "tests" / "fixtures" / "parity_builds"
    manifest_path = corpus_dir / "corpus_manifest.json"
    output_path = corpus_dir / "baseline_stats.json"

    # Load corpus manifest
    logger.info(f"\nLoading corpus manifest from: {manifest_path}")
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    total_builds = manifest['total_builds']
    logger.info(f"Found {total_builds} builds in corpus")

    # Calculate baseline stats for each build
    logger.info(f"\nCalculating baseline stats for all {total_builds} builds...")
    logger.info("-"*80)

    build_stats = []
    successful = 0
    failed = 0

    for idx, build_entry in enumerate(manifest['builds'], 1):
        build_id = build_entry['build_id']
        filename = build_entry['filename']
        xml_path = builds_dir / filename

        logger.info(f"[{idx}/{total_builds}] Processing: {build_id}")

        try:
            # Load build from XML
            build = load_build_from_xml_file(xml_path)

            # Calculate stats using Epic 1 calculator
            stats = calculate_build_stats(build)

            # Record baseline stats
            total_points_available = build.level + 23  # PoE 2 formula
            build_stat = {
                'build_id': build_id,
                'filename': filename,
                'character_class': build.character_class.value,
                'level': build.level,
                'ascendancy': build.ascendancy,
                'allocated_points': build.allocated_point_count,
                'unallocated_points': build.unallocated_points,
                'total_points_available': total_points_available,
                'baseline_stats': {
                    'total_dps': stats.total_dps,
                    'life': stats.life,
                    'effective_hp': stats.effective_hp,
                    'energy_shield': stats.energy_shield,
                    'evasion': stats.evasion,
                    'armour': stats.armour,
                    'fire_res': stats.resistances.get('fire', 0),
                    'cold_res': stats.resistances.get('cold', 0),
                    'lightning_res': stats.resistances.get('lightning', 0),
                    'chaos_res': stats.resistances.get('chaos', 0)
                },
                # Flatten for easier stats calculation
                'total_dps': stats.total_dps,
                'life': stats.life,
                'effective_hp': stats.effective_hp
            }

            build_stats.append(build_stat)
            successful += 1

            logger.info(f"  ✓ DPS={stats.total_dps:,.0f}, Life={stats.life:,}, EHP={stats.effective_hp:,.0f}")

        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")
            failed += 1

    logger.info("-"*80)
    logger.info(f"Completed: {successful} successful, {failed} failed")

    if failed > 0:
        logger.warning(f"⚠ {failed} builds failed to calculate")

    # Calculate corpus statistics
    logger.info("\nCalculating corpus-level statistics...")
    corpus_stats = calculate_corpus_statistics(build_stats)

    # Print summary statistics
    logger.info("\nCORPUS STATISTICS:")
    logger.info("-"*80)
    logger.info(f"Total builds: {corpus_stats['total_builds']}")
    logger.info(f"Builds with DPS > 0: {corpus_stats['builds_with_dps']}")
    logger.info(f"Builds with zero DPS: {corpus_stats['builds_with_zero_dps']}")
    logger.info(f"\nDPS:  Mean={corpus_stats['dps_stats']['mean']:,.0f}, "
                f"Median={corpus_stats['dps_stats']['median']:,.0f}, "
                f"Range=[{corpus_stats['dps_stats']['min']:,.0f}, {corpus_stats['dps_stats']['max']:,.0f}]")
    logger.info(f"Life: Mean={corpus_stats['life_stats']['mean']:,.0f}, "
                f"Median={corpus_stats['life_stats']['median']:,.0f}, "
                f"Range=[{corpus_stats['life_stats']['min']:,}, {corpus_stats['life_stats']['max']:,}]")
    logger.info(f"EHP:  Mean={corpus_stats['ehp_stats']['mean']:,.0f}, "
                f"Median={corpus_stats['ehp_stats']['median']:,.0f}, "
                f"Range=[{corpus_stats['ehp_stats']['min']:,.0f}, {corpus_stats['ehp_stats']['max']:,.0f}]")
    logger.info(f"\nAllocated Points: Mean={corpus_stats['allocated_points_stats']['mean']:.1f}, "
                f"Median={corpus_stats['allocated_points_stats']['median']:.0f}, "
                f"Range=[{corpus_stats['allocated_points_stats']['min']}, {corpus_stats['allocated_points_stats']['max']}]")
    logger.info(f"Unallocated Points: Mean={corpus_stats['unallocated_points_stats']['mean']:.1f}, "
                f"Median={corpus_stats['unallocated_points_stats']['median']:.0f}, "
                f"Builds with unallocated: {corpus_stats['unallocated_points_stats']['builds_with_unallocated']}")
    logger.info(f"\nLevel: Mean={corpus_stats['level_stats']['mean']:.1f}, "
                f"Median={corpus_stats['level_stats']['median']:.0f}, "
                f"Range=[{corpus_stats['level_stats']['min']}, {corpus_stats['level_stats']['max']}]")

    # Prepare output
    output_data = {
        'version': '1.0',
        'created': '2025-11-01',
        'description': 'Epic 2 baseline stats for all corpus builds',
        'purpose': 'Task 5 deliverable - baseline stats for Epic 2 validation (Task 6)',
        'reference': 'docs/retrospectives/epic-002-retro-2025-10-31.md lines 453-457',
        'corpus_statistics': corpus_stats,
        'builds': build_stats
    }

    # Save to file
    logger.info(f"\nSaving baseline stats to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info("="*80)
    logger.info("✓ Task 5 Complete!")
    logger.info(f"Baseline stats saved to: {output_path}")
    logger.info(f"Next: Task 6 - Validate Epic 2 Success Criteria using these baselines")
    logger.info("="*80)


if __name__ == '__main__':
    main()
