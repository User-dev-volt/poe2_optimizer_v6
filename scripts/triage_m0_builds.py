#!/usr/bin/env python3
"""Story 4.1 Task 10 -- M0 five-build no_valid_neighbors triage (read-only, no engine).

Tests the LEADING hypothesis first (AC-4.1.8): the five iterations==0
`no_valid_neighbors` builds fail because of the `activeSpec` PARSE GAP
(pob_parser._extract_passive_nodes at 391-393 ignores @activeSpec and returns an
EMPTY set for list-typed <Spec>), NOT a tree-version mismatch.

Evidence produced per build:
  * multi-<Spec> status + @activeSpec index (the five should be the ONLY multi-Spec
    builds in the corpus -- this script scans ALL of them to substantiate that).
  * BUGGY parse count (_extract_passive_nodes) -- expected 0 for multi-Spec builds
    -> optimizer sees zero allocated nodes -> zero neighbours -> terminates at
    iteration 0 with no_valid_neighbors.
  * CORRECT activeSpec-aware parse count (mirrors encode_pob_code:232-244).
  * SECONDARY / falsifying: set-diff the correctly-parsed nodes against
    load_passive_tree("0_3") vs "0_4" node membership. Expected: nodes present in
    BOTH graphs -> tree-version mismatch REFUTED. A contrary result is a genuine
    signal, not a confirmation to chase.
  * BFS connectivity from the class start (validate_tree_connectivity).

Exit codes (house convention): 0 ok / 1 internal / 3 input.
[Source: src/parsers/pob_parser.py:232-244,391-393; src/calculator/passive_tree.py:142-176,242]
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.parsers.pob_parser import _extract_passive_nodes  # the BUGGY one (evidence)
from src.parsers.xml_utils import parse_xml
from src.calculator.passive_tree import load_passive_tree

BUILDS_DIR = _ROOT / "tests" / "fixtures" / "realistic_builds"
FIVE = [
    "gemling_frost_mage_100", "lich_storm_mage_90", "titan_infernal_cry_72",
    "warrior_ballista_93", "witch_frost_mage_91",
]


def _pob_root(xml_text: str) -> dict:
    data = parse_xml(xml_text)
    return data.get("PathOfBuilding2") or data.get("PathOfBuilding") or {}


def _spec_info(pob_root: dict):
    """Return (is_multi, n_specs, active_index)."""
    tree = pob_root.get("Tree", {})
    spec = tree.get("Spec") if isinstance(tree, dict) else None
    if isinstance(spec, list):
        try:
            ai = int(tree.get("@activeSpec", 1))
        except (ValueError, TypeError):
            ai = 1
        if not 1 <= ai <= len(spec):
            ai = 1
        return True, len(spec), ai
    return False, (1 if isinstance(spec, dict) else 0), 1


def _correct_nodes(pob_root: dict) -> set[int]:
    """activeSpec-aware allocated-node parse (the FIX; mirrors encode_pob_code:232-244)."""
    tree = pob_root.get("Tree", {})
    spec = tree.get("Spec") if isinstance(tree, dict) else None
    if isinstance(spec, list):
        _, _, ai = _spec_info(pob_root)
        target = spec[ai - 1]
    elif isinstance(spec, dict):
        target = spec
    else:
        return set()
    nodes_str = target.get("@nodes", "") if isinstance(target, dict) else ""
    return {int(x) for x in nodes_str.split(",") if x.strip()}


def _class_name(pob_root: dict) -> str:
    b = pob_root.get("Build", {})
    return (b.get("@className") or b.get("@class") or "") if isinstance(b, dict) else ""


def _target_version(pob_root: dict) -> str:
    b = pob_root.get("Build", {})
    return (b.get("@targetVersion") or "") if isinstance(b, dict) else ""


def main() -> int:
    if not BUILDS_DIR.is_dir():
        print(f"ERROR: builds dir not found: {BUILDS_DIR}", file=sys.stderr)
        return 3

    # --- corpus-wide multi-Spec scan (substantiates "the five are the ONLY ones") ---
    multi = []
    for xmlf in sorted(BUILDS_DIR.glob("*.xml")):
        try:
            root = _pob_root(xmlf.read_text(encoding="utf-8"))
            is_multi, n, _ = _spec_info(root)
            if is_multi:
                multi.append((xmlf.stem, n))
        except Exception as e:
            print(f"  (skip {xmlf.name}: {e})", file=sys.stderr)
    print("== Corpus multi-<Spec> scan ==")
    print(f"multi-Spec builds ({len(multi)}): {[m[0] for m in multi]}")
    only_five = sorted(m[0] for m in multi) == sorted(FIVE)
    print(f"multi-Spec set == the five iterations==0 builds? {only_five}\n")

    # --- load tree graphs once (0_3 = current default, 0_4 = the bump target) ---
    trees = {}
    for v in ("0_3", "0_4"):
        try:
            trees[v] = load_passive_tree(v)
        except Exception as e:
            print(f"  (tree {v} load failed: {e})", file=sys.stderr)

    print("== Per-build triage ==")
    hdr = (f"{'build':<26}{'multiSpec':>10}{'active':>7}{'buggy':>7}{'correct':>8}"
           f"{'miss@0_3':>9}{'miss@0_4':>9}{'conn':>6}")
    print(hdr)
    print("-" * len(hdr))
    rc = 0
    for name in FIVE:
        xmlf = BUILDS_DIR / f"{name}.xml"
        if not xmlf.exists():
            print(f"{name:<26}  MISSING XML")
            rc = 1
            continue
        root = _pob_root(xmlf.read_text(encoding="utf-8"))
        is_multi, n_specs, active = _spec_info(root)
        buggy = _extract_passive_nodes(root)          # returns set() for multi-Spec
        correct = _correct_nodes(root)
        cls = _class_name(root)

        miss = {}
        for v, t in trees.items():
            present = set(t.nodes.keys())
            miss[v] = len(correct - present)

        conn = "?"
        try:
            if cls and "0_4" in trees:
                ok = trees["0_4"].validate_tree_connectivity(correct, cls)
                conn = "Y" if ok else "N"
        except Exception:
            conn = "err"

        print(f"{name:<26}{('Y('+str(n_specs)+')'):>10}{active:>7}{len(buggy):>7}"
              f"{len(correct):>8}{miss.get('0_3','-'):>9}{miss.get('0_4','-'):>9}{conn:>6}")

    print("\nInterpretation:")
    print("  buggy==0 on multi-Spec  -> root cause of no_valid_neighbors@iter0 (activeSpec parse gap).")
    print("  correct>0 & present in 0_3 AND 0_4 (miss==0) -> tree-version mismatch REFUTED.")
    print("  lich_storm_mage_90 0.0-DPS is a SEPARATE MinimalCalc gap (probed under the real driver).")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
