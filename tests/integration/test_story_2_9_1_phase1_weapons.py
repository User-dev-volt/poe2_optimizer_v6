"""Story 2.9.1 Phase 1: Weapon Base Data Loading Tests

Tests that PoB weapon data is loaded correctly and weapon builds produce DPS > 0.

AC-2.9.1.4: Weapon build validation
- warrior_earthquake_89 (Mace Strike) produces DPS > 0
- warrior_spear_45 (Explosive Spear L45) produces DPS > 0
- warrior_spear_71 (Explosive Spear L71) produces DPS > 0
- No regressions: deadeye_lightning_arrow_76 still produces ~311 DPS
"""

import pytest
from pathlib import Path
from typing import Set

from src.models.build_data import BuildData, CharacterClass
from src.parsers.xml_utils import parse_xml
import src.parsers.pob_parser as pob_parser
from src.calculator.build_calculator import calculate_build_stats


def load_build_from_xml(xml_path: Path) -> BuildData:
    """Load BuildData from XML file."""
    xml_str = xml_path.read_text(encoding='utf-8')
    data = parse_xml(xml_str)

    pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
    build_section = pob_root.get("Build")

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

    # Extract config
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

    # Extract items and skills
    items = pob_parser._extract_items(pob_root)
    skills = pob_parser._extract_skills(pob_root)

    build = BuildData(
        character_class=character_class,
        level=level,
        ascendancy=ascendancy,
        passive_nodes=passive_nodes,
        tree_version=build_section.get("@targetVersion", "0_1"),
        build_name=xml_path.stem,
        items=items,
        skills=skills,
        config=config
    )

    return build


# Fixture paths
FIXTURES_DIR = Path("tests/fixtures/realistic_builds")


class TestPhase1WeaponBuilds:
    """Test Phase 1: PoB weapon data loading and weapon build DPS."""

    def test_mace_build_warrior_earthquake_89(self):
        """AC-2.9.1.4: warrior_earthquake_89 (Mace Strike) produces DPS > 0."""
        xml_path = FIXTURES_DIR / "warrior_earthquake_89.xml"
        assert xml_path.exists(), f"Build file not found: {xml_path}"

        build = load_build_from_xml(xml_path)
        stats = calculate_build_stats(build)

        print(f"\n[warrior_earthquake_89] DPS: {stats.total_dps:.2f}")
        assert stats.total_dps > 0, "Mace build should produce DPS > 0"

    def test_spear_build_warrior_spear_45(self):
        """AC-2.9.1.4: warrior_spear_45 (Explosive Spear L45) produces DPS > 0."""
        xml_path = FIXTURES_DIR / "warrior_spear_45.xml"
        assert xml_path.exists(), f"Build file not found: {xml_path}"

        build = load_build_from_xml(xml_path)
        stats = calculate_build_stats(build)

        print(f"\n[warrior_spear_45] DPS: {stats.total_dps:.2f}")
        assert stats.total_dps > 0, "Spear L45 build should produce DPS > 0"

    def test_spear_build_warrior_spear_71(self):
        """AC-2.9.1.4: warrior_spear_71 (Explosive Spear L71) produces DPS > 0."""
        xml_path = FIXTURES_DIR / "warrior_spear_71.xml"
        assert xml_path.exists(), f"Build file not found: {xml_path}"

        build = load_build_from_xml(xml_path)
        stats = calculate_build_stats(build)

        print(f"\n[warrior_spear_71] DPS: {stats.total_dps:.2f}")
        assert stats.total_dps > 0, "Spear L71 build should produce DPS > 0"

    def test_regression_deadeye_lightning_arrow_76(self):
        """AC-2.9.1.4: Regression test - deadeye_lightning_arrow_76 still produces ~311 DPS."""
        xml_path = FIXTURES_DIR / "deadeye_lightning_arrow_76.xml"
        assert xml_path.exists(), f"Build file not found: {xml_path}"

        build = load_build_from_xml(xml_path)
        stats = calculate_build_stats(build)

        print(f"\n[deadeye_lightning_arrow_76] DPS: {stats.total_dps:.2f}")
        assert stats.total_dps > 0, "Lightning Arrow build should produce DPS > 0"

        # Regression check: Should still be around 311 DPS (allow ±20% tolerance for minor changes)
        expected_dps = 311.7
        tolerance = 0.20
        assert abs(stats.total_dps - expected_dps) / expected_dps < tolerance, \
            f"DPS regression: Expected ~{expected_dps:.1f}, got {stats.total_dps:.2f}"
