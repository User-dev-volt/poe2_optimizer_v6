"""PoB engine environment verifier (story 3.5.4).

``verify()`` checks the five environment invariants that make parity/corpus
evidence trustworthy:

  (a) external/pob-engine is a real git repo (resolvable .git — gitfile or dir)
  (b) submodule HEAD == the parent gitlink (the pin, read from the index —
      the same source setup_pob.py and generate_pob_version.py use, so all
      three tools agree on what "the pin" is)
  (c) external/POB_VERSION.txt carries the story 3.5.2 generation marker,
      its recorded commit matches the gitlink, and its recorded version
      matches the pinned manifest (hand-edits detectable)
  (d) baseline metadata versions match the pinned engine version OR are
      explicitly stale-flagged (``"stale": true``); a mismatch without the
      flag — or missing version metadata — is a violation
  (e) the submodule working tree matches the RATIFIED post-patch state:
      every patch in external/patches/*.patch reverse-checks as applied,
      every patched file is byte-identical to (pristine pinned blob + the
      full patch set applied once, in order), and no OTHER tracked submodule
      file is modified. Byte-exactness closes the wrong-skip blind spot
      where a double-applied patch (repeating context, e.g. 0002's EvalMod
      block) still passes a bare reverse-check — the 2026-07-02 incident
      class — and catches unrecorded submodule edits (plan risk #2).
      Data-driven throughout: the patch set is discovered by glob; no patch
      name, count, or content marker is hardcoded.

Consumers (AC-3.5.4.3/5): the autouse guard in tests/conftest.py (FAILS
parity/gui_parity tests on violation — never skips), the corpus entry point
scripts/run_epic2_validation_isolated.py (exits 2 before spending corpus
time), scripts/setup_pob.py (shares the reconciliation helpers), and Epic 4's
future release_gate.py.

Deliberately dependency-free: stdlib + git subprocess only, no pytest import,
and an explicit ``repo_root`` parameter so tests can point it at fabricated
environment doubles (AC-3.5.4.5). ``verify()`` NEVER raises for a bad
environment — every problem becomes a Violation; a verifier-internal crash
is itself reported as a violation rather than propagated.

The standard fix for any violation: ``python scripts/setup_pob.py``.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

SUBMODULE_PATH = "external/pob-engine"
PATCHES_DIR = "external/patches"
VERSION_FILE = "external/POB_VERSION.txt"

# Baseline files whose _metadata.pob_version is checked by invariant (d).
# Story 3.5.5's harvested fixtures adopt the same metadata contract and
# extend this tuple. A unit test (test_every_committed_baseline_fixture_is_
# guarded) goes red if a committed *.baseline.json is missing from it.
BASELINE_METADATA_FILES = (
    "tests/fixtures/parity_builds/gui_baseline_stats.json",
    # Story 3.5.5 Tier-A captures — PoB PoE2 GUI v0.15.0 (3e1b71c9), 2026-07-02
    "tests/fixtures/gui_baselines/bloodmage_remnants_95.baseline.json",
    "tests/fixtures/gui_baselines/deadeye_lightning_arrow_76.baseline.json",
    "tests/fixtures/gui_baselines/ritualist_lightning_spear_96.baseline.json",
    "tests/fixtures/gui_baselines/titan_falling_thunder_99.baseline.json",
    "tests/fixtures/gui_baselines/warrior_earthquake_89.baseline.json",
    "tests/fixtures/gui_baselines/witch_essence_drain_86.baseline.json",
)

# Must equal scripts/generate_pob_version.py GENERATED_MARKER — pinned by a
# unit test (src must not import from scripts/, hence the mirrored literal).
GENERATED_MARKER = "# GENERATED FILE - DO NOT EDIT BY HAND"

FIX_HINT = "fix: python scripts/setup_pob.py"


@dataclass(frozen=True)
class Violation:
    invariant: str  # "(a) real-repo" ... "(e) patches-applied"
    message: str    # observed vs expected, plus the fix command


@dataclass(frozen=True)
class PobEnvResult:
    ok: bool
    violations: tuple[Violation, ...]

    def summary(self) -> str:
        if self.ok:
            return "PoB environment OK (all five invariants hold)"
        lines = [f"PoB environment: {len(self.violations)} violation(s)"]
        for v in self.violations:
            lines.append(f"  [{v.invariant}] {v.message}")
        return "\n".join(lines)


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    # utf-8 + replace: git-for-windows emits UTF-8; the locale default
    # (cp1252, strict) would raise on non-ASCII paths in output.
    return subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=False,
    )


def _git_bytes(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, check=False
    )


def gitlink_from_index(repo_root: Path) -> tuple[str | None, str | None]:
    """(gitlink sha, error). The pin = the mode-160000 entry in the index —
    the same definition setup_pob.py and generate_pob_version.py use.

    An unresolved merge conflict on the gitlink (multiple index stages) is
    reported as an error rather than silently picking a stage.
    """
    out = _git(repo_root, "ls-files", "-s", "--", SUBMODULE_PATH)
    if out.returncode != 0:
        return None, f"git ls-files failed: {out.stderr.strip()}"
    entries = re.findall(r"^160000 ([0-9a-f]{40}) (\d)\t", out.stdout, re.M)
    if not entries:
        return None, (
            f"no gitlink for {SUBMODULE_PATH} in the index — the pin itself "
            "is missing; restore it from git history (story 3.5.2 "
            "established it)"
        )
    if len(entries) > 1 or entries[0][1] != "0":
        return None, (
            f"the {SUBMODULE_PATH} gitlink has {len(entries)} unmerged index "
            "stage(s) — resolve the merge conflict on the pin first"
        )
    return entries[0][0], None


def _pinned_version(repo_root: Path) -> str | None:
    """Engine version string of the pinned checkout, from the submodule's
    manifest.xml (the same source generate_pob_version.py stamps)."""
    manifest = repo_root / SUBMODULE_PATH / "manifest.xml"
    if not manifest.is_file():
        return None
    try:
        text = manifest.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = re.search(r'<Version\s+number="([^"]+)"', text)
    return match.group(1) if match else None


def patch_target_files(patch_path: Path) -> list[str]:
    """Repo-relative target paths from a patch's headers.

    Prefers ``diff --git`` lines; falls back to ``+++ b/`` lines so plain
    unified diffs (legal input to git apply) are parsed too.
    """
    targets: list[str] = []
    try:
        text = patch_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return targets
    for line in text.splitlines():
        match = re.match(r"^diff --git a/(\S+) b/(\S+)$", line) or re.match(
            r"^\+\+\+ b/(\S+)", line
        )
        target = match.group(match.lastindex) if match else None
        if target and target not in targets:
            targets.append(target)
    return targets


def discover_patches(repo_root: Path) -> list[Path]:
    """Every *.patch under external/patches/, sorted by filename (data-driven
    — never hardcode patch names)."""
    patches_dir = repo_root / PATCHES_DIR
    if not patches_dir.is_dir():
        return []
    return sorted(patches_dir.glob("*.patch"), key=lambda p: p.name)


def patched_tree_mismatches(repo_root: Path) -> list[str]:
    """Byte-exact reconciliation of the submodule tree vs the ratified state.

    Reconstructs, in a scratch git repo, what every patch target file MUST
    contain: the pristine pinned blob (submodule HEAD) with the full patch
    set applied once in sorted order. Then reports, as human-readable
    strings:
      - patches that do not apply to the pristine tree (the set no longer
        fits the pin),
      - target files whose working bytes differ from the reconstruction
        (double-apply, hand-edit inside a patched file, wrong variant), and
      - any OTHER tracked submodule file with local modifications
        (unrecorded engine edits — plan risk #2).

    A bare ``--reverse --check`` cannot distinguish applied-once from
    applied-twice when a patch's context repeats (0002's EvalMod block —
    observed live 2026-07-02); byte equality can. Shared by setup_pob.py
    (exit 6 on mismatch) and verify() invariant (e).
    """
    problems: list[str] = []
    patches = discover_patches(repo_root)
    sub_prefix = SUBMODULE_PATH + "/"

    targets: list[str] = []
    for patch in patches:
        for target in patch_target_files(patch):
            if target not in targets:
                targets.append(target)

    expected: dict[str, bytes] = {}
    if targets:
        with tempfile.TemporaryDirectory(prefix="pob_env_reconcile_") as tmp:
            scratch = Path(tmp)
            init = _git(scratch, "init", "-q", ".")
            if init.returncode != 0:
                return [f"reconciliation scratch repo failed: {init.stderr.strip()}"]
            for target in targets:
                if target.startswith(sub_prefix):
                    show = _git_bytes(
                        repo_root, "-C", SUBMODULE_PATH,
                        "show", f"HEAD:{target[len(sub_prefix):]}",
                    )
                else:
                    show = _git_bytes(repo_root, "show", f"HEAD:{target}")
                dest = scratch / target
                dest.parent.mkdir(parents=True, exist_ok=True)
                if show.returncode == 0:
                    dest.write_bytes(show.stdout)
                # else: file is created by a patch — leave absent
            for patch in patches:
                applied = _git(
                    scratch, "-c", "core.autocrlf=false",
                    "apply", str(patch.resolve()),
                )
                if applied.returncode != 0:
                    problems.append(
                        f"{PATCHES_DIR}/{patch.name} does not apply to the "
                        f"pristine pinned tree "
                        f"({applied.stderr.strip() or 'git apply failed'}) — "
                        "the patch set no longer fits the pin"
                    )
            if problems:
                return problems
            for target in targets:
                path = scratch / target
                expected[target] = path.read_bytes() if path.is_file() else b""

    for target, want in expected.items():
        actual_path = repo_root / target
        actual = actual_path.read_bytes() if actual_path.is_file() else b""
        # EOL-normalized comparison: the live v0.15.0 checkout renders CRLF
        # on disk while the blobs are LF; git's attribute-aware matching
        # treats them identical, and the 3.5.2 validation was likewise an
        # EOL-controlled diff (forensics section 4 discipline). Content
        # divergence is what matters; pure EOL flavor is not drift.
        if actual.replace(b"\r\n", b"\n") != want.replace(b"\r\n", b"\n"):
            problems.append(
                f"{target} does not match the ratified post-patch content "
                "(double-applied patch, hand-edit inside a patched file, or "
                "wrong patch variant)"
            )

    # Unrecorded edits: tracked submodule files modified beyond the patch set.
    status = _git(
        repo_root, "-C", SUBMODULE_PATH,
        "status", "--porcelain", "--untracked-files=no",
    )
    if status.returncode == 0:
        allowed = {
            t[len(sub_prefix):] for t in targets if t.startswith(sub_prefix)
        }
        for line in status.stdout.splitlines():
            if len(line) < 4:
                continue
            path = line[3:].strip().strip('"')
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            if path not in allowed:
                problems.append(
                    f"{SUBMODULE_PATH}/{path} has local modifications that "
                    "are NOT part of the ratified patch set — an unrecorded "
                    "engine edit (plan risk #2); disposition it (commit it "
                    "as a patch, or restore the file)"
                )

    return problems


def _verify_inner(repo_root: Path) -> PobEnvResult:
    violations: list[Violation] = []
    submodule_dir = repo_root / SUBMODULE_PATH

    # --- (a) real git repo ------------------------------------------------
    git_marker = submodule_dir / ".git"
    repo_probe = _git(repo_root, "-C", SUBMODULE_PATH, "rev-parse", "--git-dir")
    real_repo = git_marker.exists() and repo_probe.returncode == 0
    if not real_repo:
        violations.append(Violation(
            "(a) real-repo",
            f"{SUBMODULE_PATH} is not a real git repo (no resolvable .git); "
            f"observed: {'missing directory' if not submodule_dir.is_dir() else 'directory without a working .git'}; "
            f"{FIX_HINT}",
        ))

    # --- (b) submodule HEAD == parent gitlink (the pin, from the index) ---
    gitlink, gitlink_error = gitlink_from_index(repo_root)
    if gitlink is None:
        violations.append(Violation("(b) head-matches-gitlink", gitlink_error))
    elif real_repo:
        head_probe = _git(repo_root, "-C", SUBMODULE_PATH, "rev-parse", "HEAD")
        head = head_probe.stdout.strip()
        if head_probe.returncode != 0:
            violations.append(Violation(
                "(b) head-matches-gitlink",
                f"cannot resolve {SUBMODULE_PATH} HEAD: "
                f"{head_probe.stderr.strip()}; {FIX_HINT}",
            ))
        elif head != gitlink:
            violations.append(Violation(
                "(b) head-matches-gitlink",
                f"submodule HEAD {head[:12]} != pinned gitlink {gitlink[:12]} "
                f"— the checkout has drifted from the pin; {FIX_HINT} "
                f"(setup refuses to auto-reset; disposition local state first)",
            ))

    # --- (c) generated POB_VERSION.txt matches the pin --------------------
    pinned_version = _pinned_version(repo_root)
    version_file = repo_root / VERSION_FILE
    if not version_file.is_file():
        violations.append(Violation(
            "(c) generated-version-file",
            f"{VERSION_FILE} is missing; {FIX_HINT}",
        ))
    else:
        try:
            content = version_file.read_text(encoding="utf-8", errors="replace")
        except OSError as err:
            content = None
            violations.append(Violation(
                "(c) generated-version-file",
                f"{VERSION_FILE} is unreadable: {err}; {FIX_HINT}",
            ))
        if content is not None:
            if GENERATED_MARKER not in content:
                violations.append(Violation(
                    "(c) generated-version-file",
                    f"{VERSION_FILE} lacks the generation marker "
                    f"({GENERATED_MARKER!r}) — it was hand-written or "
                    f"hand-edited; {FIX_HINT}",
                ))
            else:
                commit_match = re.search(r"^Commit: ([0-9a-f]{40})$", content, re.M)
                recorded = commit_match.group(1) if commit_match else None
                if recorded is None:
                    violations.append(Violation(
                        "(c) generated-version-file",
                        f"{VERSION_FILE} has no 'Commit: <sha>' line; {FIX_HINT}",
                    ))
                elif gitlink is not None and recorded != gitlink:
                    violations.append(Violation(
                        "(c) generated-version-file",
                        f"{VERSION_FILE} records commit {recorded[:12]} but "
                        f"the gitlink is {gitlink[:12]} — stale or "
                        f"hand-edited; {FIX_HINT}",
                    ))
                version_match = re.search(r"^Version: (.+)$", content, re.M)
                recorded_version = (
                    version_match.group(1).strip() if version_match else None
                )
                if (
                    recorded_version is not None
                    and pinned_version is not None
                    and recorded_version != pinned_version
                ):
                    violations.append(Violation(
                        "(c) generated-version-file",
                        f"{VERSION_FILE} records Version: {recorded_version} "
                        f"but the pinned manifest says {pinned_version} — "
                        f"stale or hand-edited; {FIX_HINT}",
                    ))
                for patch in discover_patches(repo_root):
                    if f"- {patch.name}:" not in content:
                        violations.append(Violation(
                            "(c) generated-version-file",
                            f"{VERSION_FILE} has no entry for "
                            f"{patch.name} — stale or hand-edited; {FIX_HINT}",
                        ))

    # --- (d) baseline metadata version match-or-stale-flag ----------------
    for rel in BASELINE_METADATA_FILES:
        baseline = repo_root / rel
        if not baseline.is_file():
            violations.append(Violation(
                "(d) baseline-metadata",
                f"{rel} is missing — parity baselines without version "
                f"metadata cannot be trusted; restore it from git history "
                f"or re-harvest (story 3.5.5 metadata contract)",
            ))
            continue
        try:
            metadata = json.loads(
                baseline.read_text(encoding="utf-8-sig", errors="replace")
            ).get("_metadata", {})
            if not isinstance(metadata, dict):
                raise ValueError("_metadata is not an object")
        except (json.JSONDecodeError, ValueError, OSError) as err:
            violations.append(Violation(
                "(d) baseline-metadata",
                f"{rel} is unreadable: {err}; restore it from git history",
            ))
            continue
        baseline_version = metadata.get("pob_version")
        if not baseline_version:
            violations.append(Violation(
                "(d) baseline-metadata",
                f"{rel} has no _metadata.pob_version — missing version "
                f"metadata is a violation (add it, or re-harvest per story "
                f"3.5.5's metadata contract)",
            ))
        elif metadata.get("stale") is True:
            pass  # explicitly stale-flagged: an honest state, verify passes
        elif pinned_version is None:
            violations.append(Violation(
                "(d) baseline-metadata",
                f"cannot determine the pinned engine version (no readable "
                f"{SUBMODULE_PATH}/manifest.xml) to compare against {rel} "
                f"_metadata.pob_version={baseline_version!r}; {FIX_HINT}",
            ))
        elif baseline_version != pinned_version:
            violations.append(Violation(
                "(d) baseline-metadata",
                f"{rel} _metadata.pob_version={baseline_version!r} != pinned "
                f"engine version {pinned_version!r} and is not stale-flagged "
                f'— add "stale": true with a stale_reason, or re-harvest',
            ))

    # --- (e) ratified patch state, byte-exact ------------------------------
    patches_dir = repo_root / PATCHES_DIR
    if not patches_dir.is_dir():
        violations.append(Violation(
            "(e) patches-applied",
            f"{PATCHES_DIR}/ directory is missing — incomplete checkout "
            f"(an EMPTY patch directory is a valid state; a missing one is "
            f"not); restore it from git history",
        ))
    else:
        for patch in discover_patches(repo_root):
            probe = _git(
                repo_root,
                "-c", "core.autocrlf=false",
                "apply", "--reverse", "--check", str(patch),
            )
            if probe.returncode != 0:
                violations.append(Violation(
                    "(e) patches-applied",
                    f"{PATCHES_DIR}/{patch.name} is not applied to the "
                    f"submodule working tree; {FIX_HINT}",
                ))
        if real_repo:
            for problem in patched_tree_mismatches(repo_root):
                violations.append(Violation("(e) patches-applied", problem))

    return PobEnvResult(ok=not violations, violations=tuple(violations))


def verify(repo_root: Path | str | None = None) -> PobEnvResult:
    """Check the five invariants; return ok + an ordered violation list.

    NEVER raises for a bad environment — every problem becomes a Violation
    with an actionable message, so callers choose fail/report behavior.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]
    repo_root = Path(repo_root)
    try:
        return _verify_inner(repo_root)
    except Exception as err:  # never-raises contract (AC-3.5.4.1)
        return PobEnvResult(
            ok=False,
            violations=(Violation(
                "(internal) verifier-error",
                f"verifier crashed while inspecting {repo_root}: {err!r} — "
                f"treat the environment as unverified; {FIX_HINT}",
            ),),
        )


if __name__ == "__main__":
    result = verify()
    print(result.summary())
    sys.exit(0 if result.ok else 1)
