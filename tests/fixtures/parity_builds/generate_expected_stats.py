"""Generate expected baseline stats for parity test builds.

Reads each PoB build fixture, calculates stats using the integrated PoB engine,
and saves the results as baseline "expected" values for parity testing.

NOTE: These baseline stats are generated from the integrated PoB calculation engine.
For true GUI parity testing, stats should be manually recorded from the official
Path of Building application.

USAGE:
    From project root:
        python tests/fixtures/parity_builds/generate_expected_stats.py

    Or with PYTHONPATH:
        PYTHONPATH=. python tests/fixtures/parity_builds/generate_expected_stats.py

    Or after installing package in editable mode:
        pip install -e .
        python tests/fixtures/parity_builds/generate_expected_stats.py
"""

import json
import sys
from pathlib import Path

# TODO: Replace sys.path manipulation with proper package installation (pip install -e .)
# For now, add src to path to allow script to run standalone
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from src.parsers.pob_parser import parse_pob_code
from src.parsers.exceptions import PoBParseError
from src.calculator.build_calculator import calculate_build_stats
from src.calculator.exceptions import CalculationError


def load_pob_version() -> str:
    """Load PoB version from POB_VERSION.txt."""
    version_file = repo_root / "POB_VERSION.txt"
    if version_file.exists():
        content = version_file.read_text(encoding='utf-8')
        # Extract commit hash from the file
        for line in content.split('\n'):
            if line.startswith('Commit:'):
                return line.split(':', 1)[1].strip()
    return "Unknown"


def generate_expected_stats():
    """Generate expected stats for all parity build fixtures."""
    fixtures_dir = Path(__file__).parent
    build_files = sorted(fixtures_dir.glob("build_*.txt"))

    if not build_files:
        print("ERROR: No build fixtures found!")
        sys.exit(1)

    print(f"Found {len(build_files)} build fixtures")
    print("Calculating baseline stats using integrated PoB engine...")

    expected_stats = {}
    pob_version = load_pob_version()

    expected_stats["_metadata"] = {
        "pob_version": pob_version,
        "generator": "generate_expected_stats.py",
        "note": "Baseline stats generated from integrated PoB calculation engine. "
                "For true GUI parity, manually record stats from official PoB application."
    }

    for build_file in build_files:
        build_id = build_file.stem  # e.g., "build_01_witch_90"
        print(f"\nProcessing {build_id}...")

        try:
            # Load PoB code
            pob_code = build_file.read_text(encoding='utf-8').strip()

            # Parse build
            build = parse_pob_code(pob_code)
            print(f"  Parsed: {build.character_class.value} Level {build.level}")

            # Calculate stats
            stats = calculate_build_stats(build)
            print(f"  Calculated: Life={stats.life}, Mana={stats.mana}, DPS={stats.total_dps:.1f}")

            # Store expected values
            expected_stats[build_id] = {
                "character_class": build.character_class.value,
                "level": build.level,
                "stats": {
                    "total_dps": stats.total_dps,
                    "life": stats.life,
                    "energy_shield": stats.energy_shield,
                    "mana": stats.mana,
                    "effective_hp": stats.effective_hp,
                    "resistances": stats.resistances,
                    "armour": stats.armour,
                    "evasion": stats.evasion,
                    "block_chance": stats.block_chance,
                    "spell_block_chance": stats.spell_block_chance,
                    "movement_speed": stats.movement_speed
                }
            }

        except PoBParseError as e:
            print(f"  ERROR: Failed to parse {build_id}: {type(e).__name__}: {e}")
            continue
        except CalculationError as e:
            print(f"  ERROR: Failed to calculate stats for {build_id}: {type(e).__name__}: {e}")
            continue
        except Exception as e:
            print(f"  UNEXPECTED ERROR in {build_id}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise unexpected errors to fail fast

    # Save expected stats to JSON
    output_file = fixtures_dir / "expected_stats.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(expected_stats, f, indent=2, sort_keys=False)

    print(f"\nBaseline stats saved to: {output_file}")
    print(f"  Total builds: {len([k for k in expected_stats.keys() if not k.startswith('_')])}")
    print(f"  PoB version: {pob_version}")


if __name__ == "__main__":
    generate_expected_stats()
