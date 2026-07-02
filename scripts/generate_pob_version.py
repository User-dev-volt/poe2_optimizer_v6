"""Generate external/POB_VERSION.txt from the pinned submodule state.

Single source of truth for engine-version metadata (story 3.5.2 AC-3.5.2.3).
Shared implementation: scripts/setup_pob.py (story 3.5.3) calls generate() on
every run; tests and release gates compare against regenerate output to detect
hand-edits (story 3.5.4 check (c)).

Output is a pure function of (parent gitlink, manifest.xml, applied-patch set)
-- deliberately NO timestamps, so back-to-back runs are byte-identical and
setup_pob.py's zero-change double-run stays provable (story 3.5.3 AC2/AC3).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SUBMODULE_PATH = "external/pob-engine"
OUTPUT_PATH = "external/POB_VERSION.txt"
PATCHES_DIR = "external/patches"

GENERATED_MARKER = "# GENERATED FILE - DO NOT EDIT BY HAND"


class PobVersionError(RuntimeError):
    """Raised when the repo state is too inconsistent to stamp a version."""


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PobVersionError(
            f"git {' '.join(args)} failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def gitlink_commit(repo_root: Path) -> str:
    """The pin: the mode-160000 gitlink recorded in the superproject index."""
    out = _git(repo_root, "ls-files", "-s", "--", SUBMODULE_PATH)
    match = re.match(r"^160000 ([0-9a-f]{40}) ", out)
    if not match:
        raise PobVersionError(
            f"no gitlink for {SUBMODULE_PATH} in the index (got: {out!r}); "
            "run the submodule repair (story 3.5.2) first"
        )
    return match.group(1)


def submodule_head(repo_root: Path) -> str:
    return _git(repo_root, "-C", SUBMODULE_PATH, "rev-parse", "HEAD")


def manifest_version(repo_root: Path) -> str:
    manifest = repo_root / SUBMODULE_PATH / "manifest.xml"
    if not manifest.is_file():
        raise PobVersionError(f"{manifest} not found")
    match = re.search(r'<Version\s+number="([^"]+)"', manifest.read_text(encoding="utf-8"))
    if not match:
        raise PobVersionError(f"no <Version number=.../> element in {manifest}")
    return match.group(1)


def submodule_url(repo_root: Path) -> str:
    """Read the URL from .gitmodules -- never a second hardcoded copy."""
    return _git(
        repo_root, "config", "-f", ".gitmodules", f"submodule.{SUBMODULE_PATH}.url"
    )


def patch_states(repo_root: Path) -> list[tuple[str, bool]]:
    """(patch filename, is_applied) for every *.patch, sorted by filename.

    Applied == reverse-apply --check passes (the story 3.5.3 skip-if-applied
    primitive). core.autocrlf is forced off: CRLF translation false-negatives
    these checks (forensics report section 4).
    """
    states: list[tuple[str, bool]] = []
    for patch in sorted((repo_root / PATCHES_DIR).glob("*.patch")):
        result = subprocess.run(
            ["git", "-c", "core.autocrlf=false", "apply", "--reverse", "--check",
             str(patch)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        states.append((patch.name, result.returncode == 0))
    return states


def render(commit: str, version: str, url: str,
           patches: list[tuple[str, bool]]) -> str:
    lines = [
        GENERATED_MARKER,
        "# Generator: scripts/generate_pob_version.py (story 3.5.2 AC-3.5.2.3)",
        "# Regenerate: python scripts/generate_pob_version.py  "
        "(setup_pob.py does this on every run -- story 3.5.3)",
        "# Hand-edits are detected by regenerate-and-compare (story 3.5.4 check (c)).",
        "",
        f"Commit: {commit}",
        f"Version: {version}",
        f"Repository: {url}",
        f"Submodule: {SUBMODULE_PATH}",
        "",
        f"## Applied patches ({PATCHES_DIR}/, filename order)",
    ]
    if patches:
        for name, applied in patches:
            lines.append(f"- {name}: {'applied' if applied else 'NOT APPLIED'}")
    else:
        lines.append("- (none)")
    lines.append("")
    return "\n".join(lines)


def generate(repo_root: Path | None = None, check_only: bool = False) -> str:
    repo_root = repo_root or Path(__file__).resolve().parents[1]

    commit = gitlink_commit(repo_root)
    head = submodule_head(repo_root)
    if head != commit:
        raise PobVersionError(
            f"submodule HEAD {head[:12]} != gitlink {commit[:12]} -- refusing to "
            "stamp a version onto a drifted checkout; align them first "
            "(git -C external/pob-engine checkout --detach <gitlink>)"
        )

    content = render(
        commit=commit,
        version=manifest_version(repo_root),
        url=submodule_url(repo_root),
        patches=patch_states(repo_root),
    )

    out = repo_root / OUTPUT_PATH
    if check_only:
        current = out.read_text(encoding="utf-8") if out.is_file() else None
        if current != content:
            raise PobVersionError(
                f"{OUTPUT_PATH} is stale or hand-edited (regenerate to fix)"
            )
    else:
        out.write_text(content, encoding="utf-8", newline="\n")
    return content


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    try:
        content = generate(check_only=check_only)
    except PobVersionError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1
    if check_only:
        print(f"{OUTPUT_PATH} is current.")
    else:
        print(f"wrote {OUTPUT_PATH}:")
        print(content, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
