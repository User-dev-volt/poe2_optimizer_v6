"""
Fetch and decode Path of Building builds from pobb.in

This script:
1. Fetches pobb.in build pages
2. Extracts the base64-encoded build data
3. Decodes base64 + decompresses zlib
4. Saves as XML files

Usage:
    python scripts/fetch_pobb_in_builds.py
"""

import base64
import zlib
import re
import requests
from pathlib import Path
from typing import Optional


def fetch_pobb_in_build(code: str) -> Optional[str]:
    """
    Fetch a build from pobb.in and decode it to XML.

    Args:
        code: The pobb.in short code (e.g., "hRn2ApGTu-5z")

    Returns:
        XML string of the build, or None if fetch failed
    """
    # Use the /raw endpoint to get base64 data directly
    url = f"https://pobb.in/{code}/raw"
    headers = {
        "User-Agent": "poe2-optimizer/1.0 github.com/alec (testing build fetcher)"
    }

    try:
        # Fetch the raw base64 data
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        base64_data = response.text.strip()

        # Decode base64
        try:
            decoded_bytes = base64.b64decode(base64_data)
        except Exception as e:
            print(f"[FAIL] Base64 decode failed for {code}: {e}")
            return None

        # Decompress with zlib
        try:
            xml_bytes = zlib.decompress(decoded_bytes)
        except Exception as e:
            print(f"[FAIL] Zlib decompress failed for {code}: {e}")
            return None

        # Convert to string
        xml_string = xml_bytes.decode('utf-8')

        return xml_string

    except requests.RequestException as e:
        print(f"[FAIL] Failed to fetch {url}: {e}")
        return None


def save_build_xml(xml_string: str, filename: str, output_dir: Path):
    """Save XML string to file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(xml_string)

    print(f"[OK] Saved: {filepath}")


def main():
    """Fetch multiple builds from pobb.in."""

    # List of PoE2 builds to fetch
    builds = [
        {"code": "hRn2ApGTu-5z", "name": "deadeye_lightning_arrow_76.xml"},
        {"code": "GuDgEpyRo_QD", "name": "warrior_earthquake_smithofkitava_89.xml"},
        {"code": "wi9u7RMj3_fP", "name": "titan_perfect_strike_99.xml"},
        {"code": "LRXLB9bFzLei", "name": "titan_falling_thunder_crit_99.xml"},
        {"code": "RxdRlfNGHT3v", "name": "titan_ancestral_warrior_totem_90.xml"},
        {"code": "akBSH9LatODe", "name": "titan_infernal_cry_72.xml"},
        {"code": "wWJzVb-UYZZR", "name": "warrior_artillery_ballista_93.xml"},
        {"code": "-IfmuJcREOfd", "name": "warrior_explosive_spear_71.xml"},
        {"code": "y8H_ndDMCBRt", "name": "warrior_explosive_spear_45.xml"},
    ]

    output_dir = Path(__file__).parent.parent / "tests/fixtures/realistic_builds"

    print(f"Fetching {len(builds)} builds from pobb.in...")
    print(f"Output directory: {output_dir}\n")

    successful = 0
    failed = 0

    for build in builds:
        print(f"Fetching {build['code']} ({build['name']})...")
        xml = fetch_pobb_in_build(build['code'])

        if xml:
            save_build_xml(xml, build['name'], output_dir)
            successful += 1
        else:
            failed += 1

        print()

    print(f"\n{'='*60}")
    print(f"[OK] Successfully fetched: {successful}/{len(builds)}")
    if failed > 0:
        print(f"[FAIL] Failed: {failed}/{len(builds)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
