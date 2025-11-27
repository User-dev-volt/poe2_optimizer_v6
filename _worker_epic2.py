
import sys
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.build_data import BuildData, CharacterClass
from src.models.optimization_config import OptimizationConfiguration
from src.optimizer.hill_climbing import optimize_build
from src.parsers.xml_utils import parse_xml


def load_build_from_xml(xml_path: Path) -> BuildData:
    """Load BuildData from XML file."""
    xml_str = xml_path.read_text(encoding='utf-8')
    data = parse_xml(xml_str)

    pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
    build_section = pob_root["Build"]

    character_class = CharacterClass(build_section.get("@className", "Witch"))
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
            passive_nodes = set(int(n.strip()) for n in nodes_str.split(",") if n.strip())
        except ValueError:
            pass

    config_section = pob_root.get("Config", {})
    config_set = config_section.get("ConfigSet", {}) if isinstance(config_section, dict) else {}
    config = {"input": {}, "placeholder": {}}

    inputs = config_set.get("Input", [])
    if isinstance(inputs, dict):
        inputs = [inputs]
    for inp in inputs:
        if isinstance(inp, dict):
            name = inp.get("@name")
            if name:
                if "@number" in inp:
                    config["input"][name] = float(inp["@number"])
                elif "@boolean" in inp:
                    config["input"][name] = inp["@boolean"].lower() == "true"
                elif "@string" in inp:
                    config["input"][name] = inp["@string"]

    placeholders = config_set.get("Placeholder", [])
    if isinstance(placeholders, dict):
        placeholders = [placeholders]
    for ph in placeholders:
        if isinstance(ph, dict):
            name = ph.get("@name")
            if name and "@number" in ph:
                config["placeholder"][name] = float(ph["@number"])

    return BuildData(
        character_class=character_class,
        level=level,
        ascendancy=ascendancy,
        passive_nodes=passive_nodes,
        tree_version=build_section.get("@targetVersion", "0_1"),
        build_name=xml_path.stem,
        items=[],
        skills=[],
        config=config
    )


if __name__ == "__main__":
    xml_path = Path(sys.argv[1])
    budget = int(sys.argv[2])
    max_time = int(sys.argv[3])

    result = {
        "build_name": xml_path.stem,
        "status": "pending",
        "error": None
    }

    try:
        build = load_build_from_xml(xml_path)

        config = OptimizationConfiguration(
            build=build,
            metric="dps",
            unallocated_points=budget,
            respec_points=None,
            max_iterations=200,
            max_time_seconds=max_time,
            convergence_patience=5
        )

        start_time = time.time()
        opt_result = optimize_build(config)
        elapsed = time.time() - start_time

        result["status"] = "success"
        result["baseline_dps"] = opt_result.baseline_stats.total_dps
        result["optimized_dps"] = opt_result.optimized_stats.total_dps
        result["baseline_life"] = opt_result.baseline_stats.life
        result["optimized_life"] = opt_result.optimized_stats.life
        result["baseline_mana"] = opt_result.baseline_stats.mana
        result["optimized_mana"] = opt_result.optimized_stats.mana
        result["improvement_pct"] = opt_result.improvement_pct
        result["life_change"] = opt_result.optimized_stats.life - opt_result.baseline_stats.life
        result["mana_change"] = opt_result.optimized_stats.mana - opt_result.baseline_stats.mana
        result["time_seconds"] = elapsed
        result["iterations"] = opt_result.iterations_run
        result["nodes_added"] = len(opt_result.nodes_added)
        result["unallocated_used"] = opt_result.unallocated_used
        result["respec_used"] = opt_result.respec_used
        result["convergence_reason"] = opt_result.convergence_reason

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    print(json.dumps(result))
