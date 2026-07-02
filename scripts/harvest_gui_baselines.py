"""Harvest GUI-computed <PlayerStat> baselines from PoB-GUI-saved build XML.

Story 3.5.5 (AC-3.5.5.1/2/4/5). Reads build XML files that the official
Path of Building (PoE 2) GUI saved, extracts EVERY ``<PlayerStat stat="..."
value="..."/>`` element verbatim (no renaming, no curated subset, no manual
transcription), and emits one baseline fixture JSON per build.

Engine-agnostic by construction: this script never imports src.calculator,
lupa, or anything Lua-adjacent (contrast scripts/generate_baseline_stats.py,
which computes "baselines" with the engine under test -- circular
self-validation this harvester exists to replace). The only project import
is src.pob_env, the story 3.5.4 environment verifier, for the shared
POB_VERSION.txt generation-marker constant.

Usage:
    python scripts/harvest_gui_baselines.py INPUT [INPUT ...] --archetype A
        [--output-dir DIR] [--force] [--stale-reason TEXT]

    INPUT           XML file(s) and/or directory(ies). A directory harvests
                    every *.xml directly inside it (non-recursive), sorted
                    by filename.
    --archetype     attack | spell-hit | dot  (recorded in metadata;
                    minion/totem/trap capture is deferred to Epic 4 item 6)
    --output-dir    default: tests/fixtures/gui_baselines under the repo
                    root. One ``<xml stem>.baseline.json`` per input build.
    --force         (a) allow overwriting an existing output fixture, and
                    (b) allow harvesting when the generated
                    external/POB_VERSION.txt is missing or lacks the story
                    3.5.2 generation marker -- the fixture is then emitted
                    with ``"stale": true`` and NO fabricated version
                    (pob_version/pob_commit null), with a warning.
    --stale-reason  mark the fixture ``"stale": true`` with this reason
                    (required honesty for XMLs of unknown GUI provenance,
                    e.g. the tests/fixtures/realistic_builds/ corpus).

Fixture schema (schema_version 1)
---------------------------------
One JSON document per build::

    {
      "schema_version": 1,
      "_metadata": {
        "pob_version": "0.15.0",        // string; MUST equal the pinned
                                        // manifest version, or null when
                                        // harvested --force without
                                        // attestation
        "pob_commit": "<40-hex>",       // submodule gitlink recorded in the
                                        // generated POB_VERSION.txt; null
                                        // when unattested
        "captured": "YYYY-MM-DD",       // harvest date (system date)
        "source_xml": "<repo-relative posix path>",  // absolute posix path
                                        // if the XML lives outside the repo
        "source_sha256": "<hex>",       // SHA-256 of the exact input bytes
        "archetype": "attack | spell-hit | dot",
        "stale": false,                 // JSON boolean; true exempts the
                                        // fixture from version matching
        "stale_reason": "..."           // present only when stale is true
      },
      "stats": {                        // EVERY <PlayerStat>, XML document
        "TotalDPS": 18097.067904221,    // order, stat names verbatim (incl.
        "Spec:LifeInc": 5.0,            // colon-named stats), values parsed
        "...": 0.0                      // as Python floats (json round-trip
      }                                 // preserves full precision)
    }

Contract with story 3.5.4 (AC-3.5.5.5): src.pob_env.verify() invariant (d)
reads exactly ``_metadata`` (top-level object), ``_metadata.pob_version``
(string, compared by EXACT equality against the pinned submodule
manifest.xml version) and ``_metadata.stale`` (must be JSON boolean true to
exempt). The story's draft sketch ("metadata" key, nested pob_version
object) was flattened to conform to the shipped 3.5.4 field names.
``<MinionStat>`` elements are ignored by design (Epic 4 mass capture).

Duplicate <PlayerStat> stat names in one build are a hard error (the
fixture would silently lose a value); zero <PlayerStat> elements likewise.

Exit codes:
    0  success (all requested fixtures written)
    1  unexpected internal error
    2  argparse usage error
    3  input problem: path missing, directory without *.xml, malformed
       XML, zero <PlayerStat> elements, duplicate stat names, a
       non-numeric or non-finite (nan/inf) stat value, or two inputs
       whose equal stems would collide on <stem>.baseline.json
    4  version attestation refused: external/POB_VERSION.txt missing or
       lacking the generation marker / Commit / Version lines, and no
       --force
    5  output fixture already exists and no --force

Processing is fail-fast: the first error stops the run; fixtures already
written in the same run are left in place.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_REPO_ROOT_DEFAULT = Path(__file__).resolve().parents[1]

# scripts/ is not a package; src/ is imported from the repo root (the same
# sibling-import pattern as scripts/setup_pob.py).
sys.path.insert(0, str(_REPO_ROOT_DEFAULT))
from src.pob_env import GENERATED_MARKER, VERSION_FILE  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_OUTPUT_DIR = "tests/fixtures/gui_baselines"
ARCHETYPES = ("attack", "spell-hit", "dot")

EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_USAGE = 2
EXIT_INPUT = 3
EXIT_VERSION = 4
EXIT_EXISTS = 5


class HarvestError(RuntimeError):
    """Expected failure; carries the exit code main() should return."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def read_pob_version(version_file: Path) -> tuple[str, str]:
    """(commit, version) from the GENERATED POB_VERSION.txt.

    Refuses (HarvestError, exit 4) if the file is missing, lacks the story
    3.5.2 generation marker, or lacks the Commit:/Version: lines -- a
    hand-written pin file must never stamp baseline metadata.
    """
    if not version_file.is_file():
        raise HarvestError(
            f"{version_file} is missing -- cannot attest the PoB version "
            "(run: python scripts/setup_pob.py), or pass --force to emit "
            "an unversioned stale fixture",
            EXIT_VERSION,
        )
    content = version_file.read_text(encoding="utf-8", errors="replace")
    if GENERATED_MARKER not in content:
        raise HarvestError(
            f"{version_file} lacks the generation marker "
            f"({GENERATED_MARKER!r}) -- hand-written pin files must never "
            "stamp baseline metadata (run: python scripts/setup_pob.py), "
            "or pass --force to emit an unversioned stale fixture",
            EXIT_VERSION,
        )
    commit_match = re.search(r"^Commit: ([0-9a-f]{40})$", content, re.M)
    version_match = re.search(r"^Version: (.+)$", content, re.M)
    if commit_match is None or version_match is None:
        raise HarvestError(
            f"{version_file} has no 'Commit: <sha>'/'Version: ...' lines "
            "-- regenerate it (python scripts/setup_pob.py), or pass "
            "--force to emit an unversioned stale fixture",
            EXIT_VERSION,
        )
    return commit_match.group(1), version_match.group(1).strip()


def harvest_stats(xml_path: Path) -> dict[str, float]:
    """Every <PlayerStat> as {verbatim stat name: float value}, in XML
    document order. <MinionStat> is ignored by design. Duplicate stat
    names and zero <PlayerStat> elements are hard errors."""
    try:
        root = ET.parse(str(xml_path)).getroot()
    except ET.ParseError as err:
        raise HarvestError(f"{xml_path}: malformed XML: {err}", EXIT_INPUT)

    stats: dict[str, float] = {}
    duplicates: list[str] = []
    for element in root.iter("PlayerStat"):
        name = element.get("stat")
        raw = element.get("value")
        if name is None or raw is None:
            raise HarvestError(
                f"{xml_path}: <PlayerStat> element without both 'stat' and "
                f"'value' attributes (stat={name!r}, value={raw!r})",
                EXIT_INPUT,
            )
        if name in stats:
            if name not in duplicates:
                duplicates.append(name)
            continue
        try:
            value = float(raw)
        except ValueError:
            raise HarvestError(
                f"{xml_path}: <PlayerStat stat={name!r}> has non-numeric "
                f"value {raw!r}",
                EXIT_INPUT,
            )
        if not math.isfinite(value):
            raise HarvestError(
                f"{xml_path}: <PlayerStat stat={name!r}> has non-finite "
                f"value {raw!r} -- nan/inf cannot be represented in strict "
                "(RFC 8259) JSON; refusing to harvest",
                EXIT_INPUT,
            )
        stats[name] = value
    if duplicates:
        raise HarvestError(
            f"{xml_path}: duplicate <PlayerStat> stat name(s): "
            f"{', '.join(duplicates)} -- a flat stats map would silently "
            "drop values; refusing to harvest",
            EXIT_INPUT,
        )
    if not stats:
        raise HarvestError(
            f"{xml_path}: no <PlayerStat> elements found -- not a "
            "PoB-GUI-saved build XML (or saved without calculated stats)",
            EXIT_INPUT,
        )
    return stats


def _source_xml_path(xml_path: Path, repo_root: Path) -> str:
    resolved = xml_path.resolve()
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()  # outside the repo: absolute posix


def build_fixture(
    xml_path: Path,
    repo_root: Path,
    archetype: str,
    version_info: tuple[str, str] | None,
    stale_reason: str | None,
) -> dict:
    """Assemble one schema_version-1 fixture document (see module docstring
    for the field contract with pob_env.verify() check (d))."""
    raw_bytes = xml_path.read_bytes()
    stats = harvest_stats(xml_path)

    stale = stale_reason is not None
    if version_info is None:
        commit, version = None, None
        stale = True
        auto = (
            "harvested without version attestation: the generated "
            f"{VERSION_FILE} was missing or unusable (--force)"
        )
        stale_reason = f"{stale_reason}; {auto}" if stale_reason else auto
    else:
        commit, version = version_info

    metadata: dict = {
        "pob_version": version,
        "pob_commit": commit,
        "captured": _dt.date.today().isoformat(),
        "source_xml": _source_xml_path(xml_path, repo_root),
        "source_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "archetype": archetype,
        "stale": stale,
    }
    if stale:
        metadata["stale_reason"] = stale_reason

    return {
        "schema_version": SCHEMA_VERSION,
        "_metadata": metadata,
        "stats": stats,
    }


def collect_inputs(inputs: list[str]) -> list[Path]:
    """Expand the positional args into a concrete XML file list."""
    xml_files: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_file():
            xml_files.append(path)
        elif path.is_dir():
            found = sorted(
                (p for p in path.glob("*.xml") if p.is_file()),
                key=lambda p: p.name,
            )
            if not found:
                raise HarvestError(
                    f"{path}: directory contains no *.xml files "
                    "(non-recursive scan)",
                    EXIT_INPUT,
                )
            xml_files.extend(found)
        else:
            raise HarvestError(
                f"{path}: no such file or directory", EXIT_INPUT
            )

    # Output names derive from the XML stem, so two inputs with the same
    # stem would write the same <stem>.baseline.json -- under --force the
    # second would silently clobber the first mid-run. Refuse up front.
    first_by_stem: dict[str, Path] = {}
    collisions: list[str] = []
    for xml_path in xml_files:
        prior = first_by_stem.setdefault(xml_path.stem, xml_path)
        if prior is not xml_path:
            collisions.append(f"{prior} vs {xml_path}")
    if collisions:
        raise HarvestError(
            "output filename collision -- these inputs map to the same "
            "<stem>.baseline.json: " + "; ".join(collisions),
            EXIT_INPUT,
        )
    return xml_files


def main(argv: list[str] | None = None,
         repo_root: Path | str | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="harvest_gui_baselines.py",
        description=(
            "Harvest every <PlayerStat> from PoB-GUI-saved build XML into "
            "baseline fixture JSON (story 3.5.5). Exit codes: 0 ok, 1 "
            "internal, 2 usage, 3 input problem, 4 version attestation "
            "refused (no --force), 5 output exists (no --force)."
        ),
    )
    parser.add_argument(
        "inputs", nargs="+", metavar="INPUT",
        help="build XML file(s) or directory(ies) of *.xml (non-recursive)",
    )
    parser.add_argument(
        "--archetype", required=True, choices=ARCHETYPES,
        help="v1-gated archetype recorded in fixture metadata",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help=f"fixture output directory (default: {DEFAULT_OUTPUT_DIR} "
             "under the repo root)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="overwrite existing fixtures AND allow harvesting without a "
             "generated POB_VERSION.txt (emits stale, unversioned metadata)",
    )
    parser.add_argument(
        "--stale-reason", default=None, metavar="TEXT",
        help='mark the fixture "stale": true with this reason (required '
             "honesty for XMLs not saved by the GUI at the pinned release)",
    )
    args = parser.parse_args(argv)

    root = Path(repo_root) if repo_root is not None else _REPO_ROOT_DEFAULT
    output_dir = (
        Path(args.output_dir) if args.output_dir is not None
        else root / DEFAULT_OUTPUT_DIR
    )

    try:
        try:
            version_info: tuple[str, str] | None = read_pob_version(
                root / VERSION_FILE
            )
        except HarvestError as err:
            if not args.force:
                raise
            version_info = None
            print(
                f"WARNING: {err} -- continuing under --force; fixture(s) "
                'will carry "stale": true and NO version stamp',
            )

        written = 0
        for xml_path in collect_inputs(args.inputs):
            out_path = output_dir / f"{xml_path.stem}.baseline.json"
            if out_path.exists() and not args.force:
                raise HarvestError(
                    f"{out_path} already exists -- refusing to overwrite "
                    "(pass --force to replace it)",
                    EXIT_EXISTS,
                )
            fixture = build_fixture(
                xml_path, root, args.archetype, version_info,
                args.stale_reason,
            )
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(fixture, indent=2, allow_nan=False) + "\n",
                encoding="utf-8", newline="\n",
            )
            written += 1
            print(
                f"harvested {xml_path.name} -> {out_path} "
                f"({len(fixture['stats'])} stats)"
            )
        print(f"OK: {written} fixture(s) written to {output_dir}")
        return EXIT_OK
    except HarvestError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return err.exit_code


if __name__ == "__main__":
    sys.exit(main())
