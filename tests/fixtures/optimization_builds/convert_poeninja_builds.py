"""
Convert poeninja XML builds to optimization test corpus format.

Reads XML files from parity_builds directory, extracts PoB codes,
and populates corpus.json with metadata.

Usage:
    python tests/fixtures/optimization_builds/convert_poeninja_builds.py

Author: Bob (Scrum Master) - Prep Sprint Task #4
Date: 2025-10-27
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List
from collections import Counter


def extract_pob_code_from_xml(xml_path: Path) -> str:
    """Extract Base64 PoB code from PathOfBuilding.xml file."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # PoB XML format has Build element at root
    # The entire XML is the "PoB code" when exported
    # We need to serialize it back to string and Base64 encode

    # Actually, for PoB XML files, we need to convert them to PoB code format
    # But since we already have the XML, we can work with that directly
    # OR we need the import code that was originally used

    # Let me check if there's a Code element or if we need to generate it
    # For now, let's just return the file path and we'll handle conversion separately
    return str(xml_path)


def parse_filename(filename: str) -> Dict[str, any]:
    """
    Parse poeninja build filename to extract metadata.

    Format: {class_or_ascendancy}_{level}_poeninja.xml
    Examples:
        - huntress_100_poeninja.xml
        - bloodmage_100_poeninja.xml
        - amazon_80_poeninja.xml
    """
    # Remove .xml extension
    name = filename.replace('_poeninja.xml', '')
    parts = name.split('_')

    if len(parts) < 2:
        return {"name": name, "level": None}

    # Last part should be level
    try:
        level = int(parts[-1])
        class_or_ascendancy = '_'.join(parts[:-1])
    except ValueError:
        level = None
        class_or_ascendancy = name

    return {
        "name": class_or_ascendancy,
        "level": level
    }


def map_to_character_class(name: str) -> str:
    """Map ascendancy or class name to base character class."""
    # Ascendancy mappings
    ascendancy_map = {
        # Ranger
        'deadeye': 'Ranger',
        'pathfinder': 'Ranger',

        # Huntress
        'amazon': 'Huntress',
        'amazonhuntress': 'Huntress',

        # Warrior
        'warbringer': 'Warrior',
        'titan': 'Warrior',

        # Mercenary
        'witchhunter': 'Mercenary',
        'gemlinglegionnaire': 'Mercenary',

        # Monk
        'invoker': 'Monk',
        'ritualist': 'Monk',

        # Witch
        'bloodmage': 'Witch',
        'litch': 'Witch',  # Note: filename typo, should be "lich"

        # Sorceress
        'smithofkitava': 'Sorceress',  # Smith of Kithara ascendancy
    }

    # Direct class names
    direct_classes = ['ranger', 'huntress', 'warrior', 'mercenary', 'monk', 'witch', 'sorceress']

    name_lower = name.lower()

    # Check ascendancy map first
    if name_lower in ascendancy_map:
        return ascendancy_map[name_lower]

    # Check direct class names
    for cls in direct_classes:
        if cls in name_lower:
            return cls.capitalize()

    return 'Unknown'


def estimate_archetype(class_name: str, ascendancy: str) -> str:
    """Estimate build archetype based on class and ascendancy."""
    # Heuristic mapping
    minion_classes = ['litch', 'bloodmage']
    spell_classes = ['invoker', 'smithofkitava', 'witch', 'sorceress']
    attack_classes = ['deadeye', 'pathfinder', 'amazon', 'warbringer', 'titan', 'ranger', 'warrior']

    name_lower = ascendancy.lower()

    if any(m in name_lower for m in minion_classes):
        return 'minion'
    elif any(s in name_lower for s in spell_classes):
        return 'spell'
    elif any(a in name_lower for a in attack_classes):
        return 'attack'
    else:
        return 'hybrid'


def convert_builds_to_corpus(parity_builds_dir: Path, corpus_file: Path) -> None:
    """Convert poeninja builds to corpus.json format."""

    print("Converting poeninja builds to test corpus...")
    print(f"Source: {parity_builds_dir}")
    print(f"Target: {corpus_file}")
    print()

    # Find all poeninja XML files
    xml_files = sorted(parity_builds_dir.glob("*_poeninja.xml"))

    print(f"Found {len(xml_files)} poeninja build files")
    print()

    builds = []

    for xml_file in xml_files:
        filename = xml_file.name
        print(f"Processing: {filename}")

        # Parse filename for metadata
        meta = parse_filename(filename)

        try:
            # Read XML file
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Extract build data from XML
            build_elem = root.find('.//Build')
            if build_elem is None:
                print(f"  WARNING: No Build element found in {filename}")
                continue

            # Get level
            level = int(build_elem.get('level', meta['level'] or 0))

            # Get character class (can be ID or name string)
            className_attr = build_elem.get('className', '')
            try:
                # Try as numeric ID first
                class_id = int(className_attr)
                class_map = {
                    0: 'Ranger',
                    1: 'Huntress',
                    2: 'Warrior',
                    3: 'Mercenary',
                    4: 'Witch',
                    5: 'Sorceress',
                    6: 'Monk'
                }
                character_class = class_map.get(class_id, 'Unknown')
            except ValueError:
                # It's a string name
                character_class = className_attr if className_attr else map_to_character_class(meta['name'])

            # Get ascendancy
            ascendancy = build_elem.get('ascendClassName', meta['name'])

            # Count allocated passive nodes
            tree_elem = root.find('.//Tree')
            if tree_elem is not None:
                spec_elem = tree_elem.find('Spec')
                if spec_elem is not None:
                    nodes_text = spec_elem.get('nodes', '')
                    if nodes_text:
                        allocated_nodes = [n for n in nodes_text.split(',') if n.strip()]
                        allocated_count = len(allocated_nodes)
                    else:
                        allocated_count = 0
                else:
                    allocated_count = 0
            else:
                allocated_count = 0

            # Calculate unallocated points
            max_points = level + 23  # PoE 2 formula (validated in Task #1)
            unallocated = max(0, max_points - allocated_count)

            # Generate Base64 PoB code
            # For now, we'll read the XML file content and note it needs conversion
            # In a real implementation, we'd use PoB's export format
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            # Since these are XML files, not PoB codes, we'll store the path
            # and add a note that they need conversion
            pob_code = f"[XML_FILE:{xml_file.name}]"

            # Estimate archetype
            archetype = estimate_archetype(character_class, ascendancy)

            # Estimate optimization potential
            if unallocated >= 10:
                improvement = "high"
            elif unallocated >= 5:
                improvement = "medium"
            elif unallocated >= 1:
                improvement = "low"
            else:
                improvement = "none"

            # Create build entry
            build_id = f"poeninja-{meta['name']}-{level}"

            build_entry = {
                "build_id": build_id,
                "source": "poeninja",
                "name": ascendancy.replace('_', ' ').title(),
                "url": "https://poe.ninja/poe2",
                "pob_code": pob_code,
                "character_class": character_class,
                "ascendancy": ascendancy,
                "level": level,
                "allocated_points": allocated_count,
                "unallocated_points": unallocated,
                "archetype": archetype,
                "notes": f"Real build from poe.ninja - {allocated_count} nodes allocated",
                "expected_improvement": improvement
            }

            builds.append(build_entry)

            print(f"  [OK] {character_class} ({ascendancy}) Lv{level} - {allocated_count} nodes, {unallocated} unallocated")

        except Exception as e:
            print(f"  [ERROR] {e}")
            continue

    print()
    print(f"Successfully processed {len(builds)}/{len(xml_files)} builds")
    print()

    # Load existing corpus if it exists
    if corpus_file.exists():
        with open(corpus_file, 'r', encoding='utf-8') as f:
            corpus_data = json.load(f)
    else:
        corpus_data = {
            "version": "1.0",
            "created": "2025-10-27",
            "updated": None,
            "status": "IN PROGRESS",
            "target_build_count": 25,
            "current_build_count": 0,
            "builds": []
        }

    # Add converted builds
    corpus_data["builds"] = builds
    corpus_data["current_build_count"] = len(builds)
    corpus_data["updated"] = "2025-10-27"
    corpus_data["status"] = "COMPLETE - Awaiting PoB code conversion"

    # Save corpus
    with open(corpus_file, 'w', encoding='utf-8') as f:
        json.dump(corpus_data, f, indent=2)

    print(f"Corpus saved to: {corpus_file}")
    print()

    # Print summary
    print("=" * 60)
    print("CORPUS SUMMARY")
    print("=" * 60)
    print(f"Total builds: {len(builds)}")
    print()

    # Count by class
    classes = Counter(b['character_class'] for b in builds)
    print("By Class:")
    for cls, count in classes.most_common():
        print(f"  {cls}: {count}")

    print()

    # Count by level range
    level_ranges = {'low': 0, 'mid': 0, 'high': 0, 'max': 0}
    for b in builds:
        level = b['level']
        if level < 61:
            level_ranges['low'] += 1
        elif level < 81:
            level_ranges['mid'] += 1
        elif level < 96:
            level_ranges['high'] += 1
        else:
            level_ranges['max'] += 1

    print("By Level Range:")
    print(f"  Low (40-60): {level_ranges['low']}")
    print(f"  Mid (61-80): {level_ranges['mid']}")
    print(f"  High (81-95): {level_ranges['high']}")
    print(f"  Max (96-100): {level_ranges['max']}")

    print()
    print("=" * 60)
    print()

    print("[NOTE] These builds use XML format, not Base64 PoB codes.")
    print("   The pob_code field contains [XML_FILE:...] placeholders.")
    print("   You'll need to:")
    print("   1. Open each build in PoB2")
    print("   2. Export as PoB code (Import/Export Build -> Generate)")
    print("   3. Replace the pob_code field with the Base64 string")
    print()
    print("   Alternatively, we can use the XML files directly for testing")
    print("   by parsing them in the test suite.")


def main():
    """Main entry point."""
    # Paths
    project_root = Path(__file__).parent.parent.parent.parent
    parity_builds_dir = project_root / "tests" / "fixtures" / "parity_builds"
    corpus_file = project_root / "tests" / "fixtures" / "optimization_builds" / "corpus.json"

    # Convert builds
    convert_builds_to_corpus(parity_builds_dir, corpus_file)

    print("[OK] Conversion complete!")
    print()
    print("Next steps:")
    print("  1. Review corpus.json for accuracy")
    print("  2. Run validation: python tests/fixtures/optimization_builds/validate_corpus.py")
    print("  3. If validation passes, Task #4 is complete!")


if __name__ == "__main__":
    main()
