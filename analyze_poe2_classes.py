#!/usr/bin/env python3
"""Extract PoE 2 class ID mappings from tree.lua"""

import re

tree_file = "D:/poe2_optimizer_v6/external/pob-engine/src/TreeData/0_3/tree.lua"

with open(tree_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the classes section
in_classes = False
class_level = 0
current_class_id = None
class_mappings = {}

for i, line in enumerate(lines):
    if 'classes={' in line and not in_classes:
        in_classes = True
        continue

    if not in_classes:
        continue

    # Count braces to track nesting level
    open_braces = line.count('{')
    close_braces = line.count('}')

    # Check for main class entry (level 1: [N]={)
    if class_level == 0:
        match = re.match(r'\s*\[(\d+)\]=\{', line)
        if match:
            current_class_id = int(match.group(1))
            class_level = 1

    # Look for name= at the right nesting level (after ascendancies, at class level)
    if current_class_id is not None and class_level > 0:
        if 'name="' in line and 'ascend' not in line.lower():
            match = re.search(r'name="([^"]+)"', line)
            if match:
                name = match.group(1)
                # Check if this is the main class name (not an ascendancy)
                # Main class names come after the ascendancies block
                if name not in ['Deadeye', 'Pathfinder', 'Amazon', 'Ritualist',
                               'Titan', 'Warbringer', 'Smith of Kitava',
                               'Tactician', 'Witchhunter', 'Gemling Legionnaire',
                               'Infernalist', 'Blood Mage', 'Lich', 'Abyssal Lich',
                               'Stormweaver', 'Chronomancer']:
                    if current_class_id not in class_mappings:
                        class_mappings[current_class_id] = name
                        print(f"[{current_class_id}] = {name}")
                        current_class_id = None
                        class_level = 0

    # Update nesting level
    class_level += open_braces - close_braces

    if class_level < 0:
        break

print("\nClass ID Mapping Summary:")
for class_id in sorted(class_mappings.keys()):
    print(f"  {class_id}: {class_mappings[class_id]}")
