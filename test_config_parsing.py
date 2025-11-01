"""Test config parsing for different builds"""
import sys
sys.path.insert(0, 'D:\\poe2_optimizer_v6')

from src.parsers.xml_utils import parse_xml
from src.parsers.pob_parser import _extract_config, _extract_character_class, _extract_level, _extract_passive_nodes, _extract_items, _extract_skills, _extract_tree_version
from src.models.build_data import BuildData
from src.calculator.build_calculator import calculate_build_stats

builds = [
    ("build_07_witch_01.xml", "Witch L1", {"enemyLevel": 82, "enemyEvasion": 1175}),
    ("build_02_warrior_75.xml", "Warrior L75", {"enemyLevel": 50, "enemyEvasion": 600}),
    ("build_03_ranger_60.xml", "Ranger L60", {"enemyLevel": 100, "enemyEvasion": 1500}),
]

for filename, desc, expected_config in builds:
    print(f"\n=== {desc} ({filename}) ===")

    # Read XML directly
    with open(f'tests/fixtures/parity_builds/{filename}', 'r', encoding='utf-8') as f:
        xml_str = f.read()

    # Parse XML
    data = parse_xml(xml_str)
    pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
    build_section = pob_root.get("Build")

    # Extract all components
    character_class = _extract_character_class(build_section)
    level = _extract_level(build_section)
    tree_version = _extract_tree_version(pob_root)
    passive_nodes = _extract_passive_nodes(pob_root)
    items = _extract_items(pob_root)
    skills = _extract_skills(pob_root)
    config = _extract_config(pob_root)

    # Build BuildData object
    build = BuildData(
        character_class=character_class,
        level=level,
        ascendancy=build_section.get("@ascendClassName"),
        passive_nodes=passive_nodes,
        items=items,
        skills=skills,
        tree_version=tree_version,
        build_name=build_section.get("@buildName"),
        notes=pob_root.get("Notes"),
        config=config
    )
    config_input = build.config.get('input', {})
    config_placeholder = build.config.get('placeholder', {})
    enemy_level = config_input.get('enemyLevel') or config_placeholder.get('enemyLevel')
    enemy_evasion = config_input.get('enemyEvasion') or config_placeholder.get('enemyEvasion')

    print(f"DEBUG - config_input keys: {list(config_input.keys())}")
    print(f"DEBUG - config_placeholder keys (first 5): {list(config_placeholder.keys())[:5]}")

    print(f"Parsed config Input: {len(config_input)} values, Placeholder: {len(config_placeholder)} values")
    print(f"  enemyLevel: {enemy_level} (expected: {expected_config['enemyLevel']})")
    print(f"  enemyEvasion: {enemy_evasion} (expected: {expected_config['enemyEvasion']})")

    # Quick calculation test
    stats = calculate_build_stats(build)
    print(f"  Calculated DPS: {stats.total_dps}")
