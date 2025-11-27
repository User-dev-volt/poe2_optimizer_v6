"""Quick test to verify neighbor generation is working after fix"""

import sys
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

import logging
from src.models.build_data import BuildData, CharacterClass
from src.models.optimization_config import OptimizationConfiguration
from src.optimizer.hill_climbing import optimize_build
from src.parsers.xml_utils import parse_xml

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_build_from_xml_file(xml_path: Path) -> BuildData:
    """Load BuildData from XML file"""
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

    passive_nodes = set()
    if nodes_str:
        try:
            passive_nodes = set(int(node_id.strip()) for node_id in nodes_str.split(",") if node_id.strip())
        except ValueError:
            pass

    return BuildData(
        character_class=character_class,
        level=level,
        ascendancy=ascendancy,
        passive_nodes=passive_nodes,
        items=[],
        skills=[]
    )


# Test with one tailored build
tailored_dir = repo_root / "tests" / "fixtures" / "parity_builds" / "tailored"
test_file = tailored_dir / "mercenary_hip_88_10points.xml"

logger.info(f"Testing neighbor generation with: {test_file.name}")

# Load build
build = load_build_from_xml_file(test_file)
logger.info(f"Loaded build: {build.character_class.value}, level {build.level}, {len(build.passive_nodes)} nodes allocated")

# Run optimizer with unlimited respec
config = OptimizationConfiguration(
    build=build,
    metric="dps",
    unallocated_points=0,
    respec_points=None,  # Unlimited
    max_iterations=5,  # Just a few iterations to test
    max_time_seconds=60,
    convergence_patience=3
)

logger.info("Running optimizer (max 5 iterations)...")
result = optimize_build(config)

logger.info(f"\nRESULTS:")
logger.info(f"  Iterations run: {result.iterations_run}")
logger.info(f"  Convergence reason: {result.convergence_reason}")
logger.info(f"  Improvement: {result.improvement_pct:.2f}%")
logger.info(f"  Nodes added: {len(result.nodes_added)}")
logger.info(f"  Nodes removed: {len(result.nodes_removed)}")
logger.info(f"  Swaps: {result.nodes_swapped}")

if result.iterations_run > 0:
    logger.info("\n SUCCESS! Neighbor generation is working!")
else:
    logger.error("\n FAILED! Still getting 0 iterations (no neighbors)")
