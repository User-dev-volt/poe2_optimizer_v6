"""Get the actual progression values for spell stats"""

import sys
sys.path.insert(0, str(__file__).replace('scripts\\get_stat_progression.py', ''))

from src.calculator.pob_engine import PoBCalculationEngine

# Initialize engine
engine = PoBCalculationEngine()
engine._ensure_initialized()
lua = engine._lua

# Get the skillStatMap
stat_map = lua.globals().data.skillStatMap

# Check spell_minimum_base_lightning_damage
stat_name = 'spell_minimum_base_lightning_damage'
stat_data = stat_map[stat_name][1]  # Version 1 (PoE 2)

print("="*80)
print(f"Stat: {stat_name}")
print("="*80)
print(f"name: {stat_data.name}")
print(f"flags: {stat_data.flags}")
print(f"type: {stat_data.type}")
print(f"keywordFlags: {stat_data.keywordFlags}")

# Get the value table (progression values)
value_table = stat_data.value

print(f"\nValue table type: {type(value_table).__name__}")
print(f"Value table keys:")
try:
    for key in list(value_table.keys())[:30]:  # First 30 keys
        print(f"  Level {key}: {value_table[key]}")
except Exception as e:
    print(f"  Error: {e}")

# Also check max damage
print("\n" + "="*80)
stat_name_max = 'spell_maximum_base_lightning_damage'
stat_data_max = stat_map[stat_name_max][1]

print(f"Stat: {stat_name_max}")
print("="*80)
print(f"name: {stat_data_max.name}")

value_table_max = stat_data_max.value
print(f"\nMax damage progression:")
try:
    for key in list(value_table_max.keys())[:30]:
        min_val = value_table[key] if key in value_table else "N/A"
        max_val = value_table_max[key]
        print(f"  Level {key}: {min_val}-{max_val}")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "="*80)
