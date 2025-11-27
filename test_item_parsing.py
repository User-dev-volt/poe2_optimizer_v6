"""Test item parsing from PoB XML."""

from src.parsers.xml_utils import parse_xml

# Load and parse build
with open("tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml", "r", encoding="utf-8") as f:
    xml_content = f.read()

pob_data = parse_xml(xml_content)

# Debug: Check structure
print("Top-level keys:", list(pob_data.keys()))
if "PathOfBuilding2" in pob_data:
    print("PathOfBuilding2 keys:", list(pob_data["PathOfBuilding2"].keys()) if isinstance(pob_data["PathOfBuilding2"], dict) else "NOT A DICT")
    if isinstance(pob_data["PathOfBuilding2"], dict) and "Build" in pob_data["PathOfBuilding2"]:
        build = pob_data["PathOfBuilding2"]["Build"]
        print("Build keys (first 20):", list(build.keys())[:20] if isinstance(build, dict) else "NOT A DICT")
        if isinstance(build, dict):
            print("Has 'Item' key:", "Item" in build)
            if "Item" in build:
                items_data = build["Item"]
                print(f"Item data type: {type(items_data)}")
                if isinstance(items_data, list):
                    print(f"Number of items: {len(items_data)}")
                    if items_data:
                        print(f"First item keys: {list(items_data[0].keys())}")

# Call _extract_items
from src.parsers.pob_parser import _extract_items
items = _extract_items(pob_data)

print(f"\nParsed {len(items)} items:")
for item in items[:3]:  # Show first 3
    print(f"\n  Slot: {item.slot}")
    print(f"  Name: {item.name}")
    print(f"  Rarity: {item.rarity}")
    print(f"  Stats: {item.stats}")
