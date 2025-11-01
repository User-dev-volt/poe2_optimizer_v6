"""Generate synthetic PoB build fixtures for parity testing.

Creates 10+ diverse builds covering:
- All 6 character classes
- Different level ranges (1, 30, 60, 90, 100)
- Various passive tree configurations

NOTE: These are synthetic builds generated programmatically.
True GUI parity testing requires manual PoB code export from the official application.
"""

import base64
import zlib
from pathlib import Path


def create_pob_xml(
    class_name: str,
    level: int,
    passive_nodes: str = "",
    build_name: str = "Test Build"
) -> str:
    """Create PoB XML for a build.

    Args:
        class_name: Character class (Witch, Warrior, Ranger, etc.)
        level: Character level (1-100)
        passive_nodes: Comma-separated passive node IDs
        build_name: Build name for identification

    Returns:
        PoB XML string
    """
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<PathOfBuilding>
<Build level="{level}" className="{class_name}" ascendClassName="" mainSocketGroup="1" buildName="{build_name}" viewMode="TREE"/>
<Tree activeSpec="3_24">
<Spec>
<URL>https://pobb.in/passive-tree</URL>
<Sockets/>
<EditedNodes/>
</Spec>
<Spec nodes="{passive_nodes}" treeVersion="3_24" masteryEffects="" classId="{get_class_id(class_name)}">
<URL>https://pobb.in/passive-tree</URL>
</Spec>
</Tree>
<Notes>
Synthetic build for parity testing - {class_name} Level {level}
</Notes>
<TreeView searchStr="" zoomY="-606.93109" zoomLevel="3" showHeatMap="false" zoomX="-689.26935"/>
<Items activeItemSet="1" useSecondWeaponSet="nil">
<ItemSet useSecondWeaponSet="nil" id="1"/>
</Items>
<Skills sortGemsByDPS="true" defaultGemQuality="nil" defaultGemLevel="nil" showSupportGemTypes="ALL" showAltQualityGems="false">
<Skill slot="Weapon 1" mainActiveSkill="1" enabled="true" includeInFullDPS="nil" skillId="1" label="">
<Gem enableGlobal2="nil" gemId="1" level="1" nameSpec="Default Attack" quality="0" enabled="true" enableGlobal1="nil" skillId="Attack"/>
</Skill>
</Skills>
<Calcs>
<Input name="enemySpeed" string="default"/>
<Input name="enemyLevel" number="83"/>
<Input name="enemyIsBoss" string="None"/>
<Section collapsed="nil" id="0"/>
</Calcs>
<Config>
<Input name="conditionStationary" boolean="false"/>
<Input name="buffOnslaught" boolean="false"/>
</Config>
</PathOfBuilding>'''
    return xml


def get_class_id(class_name: str) -> int:
    """Get numeric class ID for character class."""
    class_ids = {
        "Witch": 0,
        "Warrior": 1,
        "Ranger": 2,
        "Monk": 3,
        "Mercenary": 4,
        "Sorceress": 5
    }
    return class_ids.get(class_name, 0)


def encode_pob_code(xml: str) -> str:
    """Encode XML to PoB code format (Base64 of zlib-compressed XML).

    Args:
        xml: PoB XML string

    Returns:
        Base64-encoded PoB code
    """
    # Compress with zlib
    compressed = zlib.compress(xml.encode('utf-8'))

    # Encode to Base64
    encoded = base64.b64encode(compressed).decode('ascii')

    return encoded


def generate_build_fixtures():
    """Generate all parity test build fixtures.

    Passive Node Selection Criteria:
    - Level 1 builds: No passive nodes (starter builds, testing base stats)
    - Level 30 builds: 1 passive node (early game, minimal tree investment)
    - Level 60 builds: 2 passive nodes (mid-game, moderate tree investment)
    - Level 75 builds: 2 passive nodes (late-game progression)
    - Level 90 builds: 0-4 passive nodes (end-game, testing minimal vs optimized)
    - Level 100 builds: 3 passive nodes (max level, testing high tree investment)

    Node IDs are arbitrary but valid for PoE 2 passive tree (from tree.lua).
    The specific nodes chosen don't matter for parity testing - we're validating
    calculation consistency, not optimal passive tree paths.
    """
    builds = [
        # Build 1: Witch Level 90 (minimal passive nodes)
        # Node selection: Empty tree to test base stats without passive bonuses
        {
            "class_name": "Witch",
            "level": 90,
            "passive_nodes": "",
            "filename": "build_01_witch_90.txt",
            "build_name": "Parity Test: Witch L90 Minimal"
        },
        # Build 2: Warrior Level 75 (some passive nodes)
        # Node selection: 61834, 2142 - Sample STR-area nodes for testing stat scaling
        {
            "class_name": "Warrior",
            "level": 75,
            "passive_nodes": "61834,2142",
            "filename": "build_02_warrior_75.txt",
            "build_name": "Parity Test: Warrior L75"
        },
        # Build 3: Ranger Level 60 (mid-level)
        # Node selection: 50459, 36858 - Sample DEX-area nodes for mid-game testing
        {
            "class_name": "Ranger",
            "level": 60,
            "passive_nodes": "50459,36858",
            "filename": "build_03_ranger_60.txt",
            "build_name": "Parity Test: Ranger L60"
        },
        # Build 4: Monk Level 30 (early game)
        # Node selection: 33753 - Single node to test early-game stat calculations
        {
            "class_name": "Monk",
            "level": 30,
            "passive_nodes": "33753",
            "filename": "build_04_monk_30.txt",
            "build_name": "Parity Test: Monk L30 Early"
        },
        # Build 5: Mercenary Level 100 (max level)
        # Node selection: 6230, 48768, 61419 - Multiple nodes to test max-level calculations
        {
            "class_name": "Mercenary",
            "level": 100,
            "passive_nodes": "6230,48768,61419",
            "filename": "build_05_mercenary_100.txt",
            "build_name": "Parity Test: Mercenary L100 Max"
        },
        # Build 6: Sorceress Level 90
        # Node selection: 41263, 7960 - Sample INT-area nodes for testing spell-focused stats
        {
            "class_name": "Sorceress",
            "level": 90,
            "passive_nodes": "41263,7960",
            "filename": "build_06_sorceress_90.txt",
            "build_name": "Parity Test: Sorceress L90"
        },
        # Build 7: Witch Level 1 (minimum level)
        # Node selection: Empty tree to test absolute minimum (level 1, no passives)
        {
            "class_name": "Witch",
            "level": 1,
            "passive_nodes": "",
            "filename": "build_07_witch_01.txt",
            "build_name": "Parity Test: Witch L1 Starter"
        },
        # Build 8: Warrior Level 30
        # Node selection: 54127 - Single node for early-game STR build testing
        {
            "class_name": "Warrior",
            "level": 30,
            "passive_nodes": "54127",
            "filename": "build_08_warrior_30.txt",
            "build_name": "Parity Test: Warrior L30"
        },
        # Build 9: Ranger Level 90 (optimized)
        # Node selection: 27120, 5823, 26196, 61419 - More nodes to test optimized tree investment
        {
            "class_name": "Ranger",
            "level": 90,
            "passive_nodes": "27120,5823,26196,61419",
            "filename": "build_09_ranger_90.txt",
            "build_name": "Parity Test: Ranger L90 Optimized"
        },
        # Build 10: Monk Level 60
        # Node selection: 44169, 49080 - Sample hybrid STR/DEX nodes for mid-game Monk
        {
            "class_name": "Monk",
            "level": 60,
            "passive_nodes": "44169,49080",
            "filename": "build_10_monk_60.txt",
            "build_name": "Parity Test: Monk L60"
        },
        # Build 11: Mercenary Level 75
        # Node selection: 22748, 26196 - Sample DEX/INT nodes for hybrid build testing
        {
            "class_name": "Mercenary",
            "level": 75,
            "passive_nodes": "22748,26196",
            "filename": "build_11_mercenary_75.txt",
            "build_name": "Parity Test: Mercenary L75"
        },
        # Build 12: Sorceress Level 60
        # Node selection: 9408, 12613 - Sample INT nodes for mid-game Sorceress
        {
            "class_name": "Sorceress",
            "level": 60,
            "passive_nodes": "9408,12613",
            "filename": "build_12_sorceress_60.txt",
            "build_name": "Parity Test: Sorceress L60"
        },
    ]

    output_dir = Path(__file__).parent

    for build in builds:
        # Generate XML
        xml = create_pob_xml(
            class_name=build["class_name"],
            level=build["level"],
            passive_nodes=build["passive_nodes"],
            build_name=build["build_name"]
        )

        # Encode to PoB code
        pob_code = encode_pob_code(xml)

        # Save to file
        output_path = output_dir / build["filename"]
        output_path.write_text(pob_code, encoding='utf-8')
        print(f"Generated: {build['filename']} ({build['class_name']} L{build['level']})")

    print(f"\nTotal builds generated: {len(builds)}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    generate_build_fixtures()
