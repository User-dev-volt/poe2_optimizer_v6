"""Process official PoB GUI builds and extract TRUE baseline stats.

This script:
1. Reads XML files exported from Path of Building GUI (PoE 2 version 0.12.2)
2. Extracts stats calculated BY the official PoB application
3. Converts XML to Base64-encoded PoB codes (.txt files)
4. Generates gui_baseline_stats.json with TRUE GUI parity baseline

These are REAL builds with stats calculated by the official PoB application,
NOT synthetic builds or self-generated baselines.
"""

import base64
import json
import zlib
import xml.etree.ElementTree as ET
from pathlib import Path


def extract_stats_from_xml(xml_path: Path) -> dict:
    """Extract PoB GUI calculated stats from XML file.

    Args:
        xml_path: Path to PoB XML file

    Returns:
        Dictionary with build metadata and stats
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Extract build metadata
    build_elem = root.find('Build')
    if build_elem is None:
        raise ValueError(f"No <Build> element found in {xml_path}")

    class_name = build_elem.get('className')
    level = int(build_elem.get('level'))

    # Extract stats from PlayerStat elements
    stats = {}
    stat_mapping = {
        'TotalDPS': 'total_dps',
        'Life': 'life',
        'EnergyShield': 'energy_shield',
        'Mana': 'mana',
        'TotalEHP': 'effective_hp',
        'FireResist': 'fire_resist',
        'ColdResist': 'cold_resist',
        'LightningResist': 'lightning_resist',
        'ChaosResist': 'chaos_resist',
        'Armour': 'armour',
        'Evasion': 'evasion',
        'EffectiveBlockChance': 'block_chance',
        'EffectiveSpellBlockChance': 'spell_block_chance',
        'EffectiveMovementSpeedMod': 'movement_speed'
    }

    for player_stat in root.findall('.//PlayerStat'):
        stat_name = player_stat.get('stat')
        stat_value = player_stat.get('value')

        if stat_name in stat_mapping:
            # Convert to appropriate type
            if stat_name in ['Life', 'Mana', 'EnergyShield', 'Armour', 'Evasion']:
                stats[stat_mapping[stat_name]] = int(float(stat_value))
            elif 'Resist' in stat_name:
                stats[stat_mapping[stat_name]] = int(float(stat_value))
            else:
                stats[stat_mapping[stat_name]] = float(stat_value)

    # Organize resistances
    resistances = {
        'fire': stats.pop('fire_resist'),
        'cold': stats.pop('cold_resist'),
        'lightning': stats.pop('lightning_resist'),
        'chaos': stats.pop('chaos_resist')
    }

    return {
        'character_class': class_name,
        'level': level,
        'stats': {
            **stats,
            'resistances': resistances
        }
    }


def xml_to_pob_code(xml_path: Path) -> str:
    """Convert XML file to Base64-encoded PoB code.

    Args:
        xml_path: Path to PoB XML file

    Returns:
        Base64-encoded PoB code string
    """
    # Read XML file
    xml_content = xml_path.read_text(encoding='utf-8')

    # Compress with zlib
    compressed = zlib.compress(xml_content.encode('utf-8'))

    # Encode to Base64
    encoded = base64.b64encode(compressed).decode('ascii')

    return encoded


def process_all_builds():
    """Process all PoB GUI builds and generate baseline stats."""
    fixtures_dir = Path(__file__).parent
    xml_files = sorted(fixtures_dir.glob("build_*.xml"))

    if not xml_files:
        print("ERROR: No build XML files found!")
        return

    print(f"Found {len(xml_files)} PoB GUI builds")
    print("=" * 60)

    baseline_stats = {
        "_metadata": {
            "pob_version": "0.12.2",
            "source": "Official Path of Building GUI (PoE 2)",
            "date_recorded": "2025-10-21",
            "note": "TRUE GUI parity baseline - stats calculated by official PoB application and extracted from exported XML files"
        }
    }

    for xml_path in xml_files:
        build_id = xml_path.stem  # e.g., "build_01_witch_90"
        print(f"\nProcessing {build_id}...")

        try:
            # Extract stats from XML (calculated by PoB GUI)
            build_data = extract_stats_from_xml(xml_path)
            print(f"  Class: {build_data['character_class']} Level {build_data['level']}")
            print(f"  Stats: Life={build_data['stats']['life']}, "
                  f"Mana={build_data['stats']['mana']}, "
                  f"DPS={build_data['stats']['total_dps']:.2f}")

            # Convert XML to Base64 PoB code
            pob_code = xml_to_pob_code(xml_path)
            print(f"  PoB code length: {len(pob_code)} chars")

            # Save PoB code to .txt file
            txt_path = xml_path.with_suffix('.txt')
            txt_path.write_text(pob_code, encoding='utf-8')
            print(f"  Saved to: {txt_path.name}")

            # Store baseline stats
            baseline_stats[build_id] = build_data

        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Save baseline stats to JSON
    output_file = fixtures_dir / "gui_baseline_stats.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(baseline_stats, f, indent=2, sort_keys=False)

    successful_builds = len([k for k in baseline_stats.keys() if not k.startswith('_')])
    print("\n" + "=" * 60)
    print(f"✓ Successfully processed {successful_builds} builds")
    print(f"✓ PoB codes saved to .txt files")
    print(f"✓ GUI baseline stats saved to: {output_file.name}")
    print("\nThese are TRUE GUI parity baselines!")


if __name__ == "__main__":
    process_all_builds()
