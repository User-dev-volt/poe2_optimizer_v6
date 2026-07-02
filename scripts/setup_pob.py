"""The ONE setup command for the PoB engine environment (story 3.5.3).

Idempotent: safe to run on a fresh clone or an already-configured checkout.

    python scripts/setup_pob.py

What it does, in order:
  1. Preflight: git on PATH, a real git checkout (not a zip download),
     .gitmodules with the pob-engine entry, external/patches/ present.
  2. Submodule init/update to the pinned gitlink (never ``--remote``).
     Non-destructive: if the submodule HEAD has drifted from the gitlink,
     the script FAILS with remediation instead of resetting your state.
  3. Applies every patch in external/patches/*.patch in sorted-filename
     order, from the repo root (the promoted patches carry
     ``external/pob-engine/...`` paths — see each patch's header).
     Skip-if-applied, reverse-check FIRST: ``git apply --reverse --check``
     -> already applied, skip; else ``git apply --check`` -> apply it;
     else conflict. Reverse-check priority is load-bearing: patch 0002's
     context block repeats inside EvalMod, so a forward-check can succeed
     on an ALREADY-PATCHED tree (matching the second occurrence) — a
     forward-first rule double-applies it (observed 2026-07-02). This
     matches external/patches/README.md and generate_pob_version.py.
  4. Reconciles the submodule tree byte-exactly against the ratified
     post-patch state (pristine pinned blobs + the patch set applied once,
     via src/pob_env.patched_tree_mismatches). A bare reverse-check cannot
     distinguish applied-once from applied-twice when patch context
     repeats; byte equality can. Unrecorded edits to other tracked engine
     files are flagged too (plan risk #2).
  5. Regenerates external/POB_VERSION.txt via scripts/generate_pob_version.py
     (the story 3.5.2 generator — the single implementation). Unconditional:
     hand-edits never survive a run.

Exit codes (stable — consumed by story 3.5.4's verify and future CI):
  0  success (including the all-patches-skipped second run)
  1  unexpected internal error (including generator failures after all
     environment checks passed)
  2  command-line usage error (argparse)
  3  preflight failure: git not on PATH, not a git checkout (zip/tarball
     download), .gitmodules missing/without the external/pob-engine entry,
     no (or an unmerged) gitlink in the index, or external/patches/ missing
  4  submodule missing/uninitialized: no real git repo at external/pob-engine
     after the init/update attempt
  5  gitlink/working-tree mismatch: submodule HEAD != parent gitlink; the
     script never destructively resets the submodule (plan risk #2)
  6  patch conflict or ratified-state mismatch: a patch matches neither the
     pre- nor post-patch state, a patched file diverges from the ratified
     bytes (e.g. double-applied), or an unrecorded engine edit exists
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT_DEFAULT = Path(__file__).resolve().parents[1]

# Shared generator (story 3.5.2) lives beside this script; scripts/ is not a
# package, so import it via the directory path. The reconciliation helpers
# are shared with the story 3.5.4 verifier (single implementation).
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(_REPO_ROOT_DEFAULT))
import generate_pob_version  # noqa: E402
from src.pob_env import (  # noqa: E402
    discover_patches,
    patch_target_files,
    patched_tree_mismatches,
)

SUBMODULE_PATH = "external/pob-engine"
PATCHES_DIR = "external/patches"

EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_USAGE = 2
EXIT_PREFLIGHT = 3
EXIT_SUBMODULE_MISSING = 4
EXIT_GITLINK_MISMATCH = 5
EXIT_PATCH_CONFLICT = 6

# Patch decision outcomes (pure function below — unit-tested in
# tests/unit/test_setup_pob.py).
APPLY = "apply"
SKIP = "skip"
CONFLICT = "conflict"


class SetupError(RuntimeError):
    """Fatal setup failure carrying its exit code."""

    def __init__(self, exit_code: int, message: str):
        super().__init__(message)
        self.exit_code = exit_code


def decide_patch_action(check_ok: bool, reverse_check_ok: bool) -> str:
    """The skip-if-applied primitive (story 3.5.3 AC2), reverse-check first.

    ``git apply --reverse --check`` passes -> SKIP (already applied); else
    ``git apply --check`` passes -> APPLY; else CONFLICT.

    "Already applied" MUST outrank "could apply": when a patch's context
    appears more than once in the target file (0002's EvalMod block does),
    the forward check still succeeds on a patched tree by matching the
    other occurrence, and a forward-first rule re-applies the patch there
    on every run. The story text's forward-first wording predates this
    discovery; README/generate_pob_version.py always specified reverse-first.
    Note SKIP is provisional: the byte-exact reconciliation step still
    validates that "applied" means applied-exactly-once (see module docs).
    """
    if reverse_check_ok:
        return SKIP
    if check_ok:
        return APPLY
    return CONFLICT


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    # utf-8 + replace: git-for-windows emits UTF-8; the locale default
    # (cp1252, strict) would raise on non-ASCII paths in output.
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=False,
    )


def _git_apply(repo_root: Path, patch_path: Path, *extra: str) -> subprocess.CompletedProcess:
    # core.autocrlf is forced off: CRLF translation false-negatives the
    # --check probes (forensics report section 4). Applied from the repo
    # root — the promoted patches carry external/pob-engine/... paths.
    return _run_git(
        ["-c", "core.autocrlf=false", "apply", *extra, str(patch_path)],
        cwd=repo_root,
    )


def preflight(repo_root: Path) -> None:
    if shutil.which("git") is None:
        raise SetupError(
            EXIT_PREFLIGHT,
            "git is not on PATH. Install git and re-run: python scripts/setup_pob.py",
        )
    in_repo = _run_git(["rev-parse", "--git-dir"], cwd=repo_root)
    if in_repo.returncode != 0:
        raise SetupError(
            EXIT_PREFLIGHT,
            f"{repo_root} is not a git checkout "
            f"({in_repo.stderr.strip() or 'git rev-parse failed'}). A zip/"
            "tarball download cannot pin the engine — clone the repository "
            "with git and re-run: python scripts/setup_pob.py",
        )
    gitmodules = repo_root / ".gitmodules"
    if not gitmodules.is_file():
        raise SetupError(
            EXIT_PREFLIGHT,
            f".gitmodules not found at {gitmodules} — are you running from a "
            "clone of poe2_optimizer_v6? (repo root inferred: "
            f"{repo_root})",
        )
    entry = _run_git(
        ["config", "-f", ".gitmodules", f"submodule.{SUBMODULE_PATH}.path"],
        cwd=repo_root,
    )
    if entry.returncode != 0:
        raise SetupError(
            EXIT_PREFLIGHT,
            f".gitmodules has no submodule.{SUBMODULE_PATH} entry: "
            f"{entry.stderr.strip() or 'missing section'}",
        )
    if not (repo_root / PATCHES_DIR).is_dir():
        raise SetupError(
            EXIT_PREFLIGHT,
            f"{PATCHES_DIR}/ is missing — incomplete checkout (sparse "
            "checkout excluding it, or accidental deletion). An engine "
            "without its ratified patches must not be certified; restore "
            f"{PATCHES_DIR}/ from git history and re-run.",
        )


def gitlink_commit(repo_root: Path) -> str:
    """The pinned commit: the mode-160000 gitlink in the superproject index.

    Refuses to guess during an unresolved merge conflict on the gitlink
    (multiple index stages) instead of silently picking a stage.
    """
    out = _run_git(["ls-files", "-s", "--", SUBMODULE_PATH], cwd=repo_root)
    if out.returncode != 0:
        raise SetupError(
            EXIT_PREFLIGHT, f"git ls-files failed: {out.stderr.strip()}"
        )
    entries = re.findall(r"^160000 ([0-9a-f]{40}) (\d)\t", out.stdout, re.M)
    if not entries:
        raise SetupError(
            EXIT_PREFLIGHT,
            f"no gitlink for {SUBMODULE_PATH} in the git index "
            f"(got: {out.stdout.strip()!r}). The pin itself is missing — "
            "this is not something setup can invent; restore it from git "
            "history (story 3.5.2 established it).",
        )
    if len(entries) > 1 or entries[0][1] != "0":
        raise SetupError(
            EXIT_PREFLIGHT,
            f"the {SUBMODULE_PATH} gitlink has {len(entries)} unmerged index "
            "stage(s) — resolve the merge conflict on the pin first, then "
            "re-run: python scripts/setup_pob.py",
        )
    return entries[0][0]


def is_real_submodule_repo(repo_root: Path) -> bool:
    """True when external/pob-engine is a real git repo (gitfile or dir)."""
    probe = _run_git(
        ["-C", SUBMODULE_PATH, "rev-parse", "--git-dir"], cwd=repo_root
    )
    return probe.returncode == 0 and (repo_root / SUBMODULE_PATH / ".git").exists()


def submodule_head(repo_root: Path) -> str:
    out = _run_git(["-C", SUBMODULE_PATH, "rev-parse", "HEAD"], cwd=repo_root)
    if out.returncode != 0:
        raise SetupError(
            EXIT_SUBMODULE_MISSING,
            f"{SUBMODULE_PATH} has no resolvable HEAD: {out.stderr.strip()}",
        )
    return out.stdout.strip()


def ensure_submodule(repo_root: Path) -> None:
    """Initialize/update the submodule to the pinned gitlink — non-destructively.

    Fresh clone (no repo at the path): ``git submodule update --init`` checks
    out the gitlink commit. Existing real repo: verify HEAD == gitlink FIRST
    and fail with remediation on drift — never silently reset user state
    (story AC-3.5.3.5 / plan risk #2).
    """
    gitlink = gitlink_commit(repo_root)

    if is_real_submodule_repo(repo_root):
        head = submodule_head(repo_root)
        if head != gitlink:
            raise SetupError(
                EXIT_GITLINK_MISMATCH,
                f"submodule HEAD {head[:12]} != pinned gitlink {gitlink[:12]}.\n"
                "  Refusing to reset the submodule for you — your checkout may "
                "hold state that is not dispositioned.\n"
                "  If the drift is intentional debris, align it with:\n"
                f"    git -C {SUBMODULE_PATH} checkout --detach {gitlink}\n"
                "  then re-run: python scripts/setup_pob.py",
            )
        # Aligned real repo: a plain update is a no-op; --init also repairs a
        # missing .git/config registration. Uncommitted patch modifications
        # survive (checkout to the same commit does not touch the worktree).
        result = _run_git(
            ["submodule", "update", "--init", "--", SUBMODULE_PATH], cwd=repo_root
        )
        if result.returncode != 0:
            raise SetupError(
                EXIT_SUBMODULE_MISSING,
                f"git submodule update --init failed:\n{result.stderr.strip()}",
            )
        return

    # No real repo at the path yet (fresh clone: empty dir; or the historic
    # phantom state: files on disk without .git — update will refuse, which
    # is the correct non-destructive outcome).
    result = _run_git(
        ["submodule", "update", "--init", "--", SUBMODULE_PATH], cwd=repo_root
    )
    if result.returncode != 0 or not is_real_submodule_repo(repo_root):
        detail = result.stderr.strip() or "no .git at the submodule path"
        raise SetupError(
            EXIT_SUBMODULE_MISSING,
            f"{SUBMODULE_PATH} is not a real git repo after init/update: "
            f"{detail}\n"
            "  If the directory holds a non-repo copy of the engine, move it "
            "aside (do NOT delete it until you have dispositioned any local "
            "edits) and re-run: python scripts/setup_pob.py",
        )

    head = submodule_head(repo_root)
    if head != gitlink:
        raise SetupError(
            EXIT_GITLINK_MISMATCH,
            f"after init/update, submodule HEAD {head[:12]} != gitlink "
            f"{gitlink[:12]} — align it with:\n"
            f"    git -C {SUBMODULE_PATH} checkout --detach {gitlink}\n"
            "  then re-run: python scripts/setup_pob.py",
        )


def apply_patches(repo_root: Path) -> tuple[list[tuple[str, str]], list[str]]:
    """Apply the patch set with skip-if-applied. Returns (report, conflicts).

    report: (patch name, outcome line) per patch, in order.
    conflicts: patch names that conflicted. Non-conflicting patches are still
    applied so a re-run after fixing one bad patch converges.
    """
    report: list[tuple[str, str]] = []
    conflicts: list[str] = []
    for patch in discover_patches(repo_root):
        # Reverse-check first; the forward probe only runs when the patch is
        # not already applied (see decide_patch_action for why order matters).
        reverse_ok = _git_apply(repo_root, patch, "--reverse", "--check").returncode == 0
        check_ok = (
            False if reverse_ok
            else _git_apply(repo_root, patch, "--check").returncode == 0
        )
        action = decide_patch_action(check_ok, reverse_ok)
        if action == APPLY:
            applied = _git_apply(repo_root, patch)
            if applied.returncode != 0:
                # --check passed but apply failed: treat as conflict.
                action = CONFLICT
            else:
                report.append((patch.name, "applied"))
                continue
        if action == SKIP:
            report.append((patch.name, "skipped (already applied)"))
            continue
        # CONFLICT
        targets = ", ".join(patch_target_files(patch)) or "(no diff headers found)"
        report.append((patch.name, f"FAILED: {patch.name} -> {targets}"))
        conflicts.append(patch.name)
    return report, conflicts


def regenerate_version_file(repo_root: Path) -> None:
    """Unconditional regeneration — the anti-drift mechanism (AC-3.5.3.3)."""
    try:
        generate_pob_version.generate(repo_root)
    except generate_pob_version.PobVersionError as err:
        # Every environment condition the generator re-checks (gitlink, HEAD
        # alignment, manifest readability) was already validated above, so a
        # failure here is unexpected — internal, not a documented env class.
        raise SetupError(EXIT_INTERNAL, f"version stamp failed unexpectedly: {err}")


def main(argv: list[str] | None = None, repo_root: Path | str | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Idempotent PoB engine setup: submodule init/update to the pinned "
            "gitlink, patch auto-apply (skip-if-applied), byte-exact ratified-"
            "state reconciliation, POB_VERSION.txt regeneration. Exit codes: "
            "0 ok, 3 preflight, 4 submodule missing, 5 gitlink mismatch "
            "(never auto-reset), 6 patch conflict/ratified-state mismatch."
        )
    )
    parser.parse_args(argv)

    repo_root = Path(repo_root) if repo_root is not None else _REPO_ROOT_DEFAULT

    try:
        preflight(repo_root)
        ensure_submodule(repo_root)
        report, conflicts = apply_patches(repo_root)
        for name, outcome in report:
            print(f"  {name}: {outcome}")
        if conflicts:
            print(
                f"ERROR: {len(conflicts)} patch(es) conflict "
                f"({', '.join(conflicts)}). The submodule tree matches neither "
                "the pre- nor post-patch state. Inspect with:\n"
                f"  git -c core.autocrlf=false apply --check {PATCHES_DIR}/<patch>\n"
                "and disposition local edits before re-running.",
                file=sys.stderr,
            )
            return EXIT_PATCH_CONFLICT
        # Byte-exact reconciliation: "skipped (already applied)" above is
        # provisional — a double-applied patch (repeating context) also
        # reverse-checks clean. Only byte equality with the ratified
        # post-patch reconstruction certifies the tree (2026-07-02 incident).
        mismatches = patched_tree_mismatches(repo_root)
        if mismatches:
            print(
                "ERROR: the submodule tree diverges from the ratified "
                "post-patch state:",
                file=sys.stderr,
            )
            for problem in mismatches:
                print(f"  - {problem}", file=sys.stderr)
            print(
                "  Disposition local edits first; to restore a diverged "
                "patched file:\n"
                f"    git -C {SUBMODULE_PATH} checkout -- <file>\n"
                "  then re-run: python scripts/setup_pob.py",
                file=sys.stderr,
            )
            return EXIT_PATCH_CONFLICT
        regenerate_version_file(repo_root)
        applied = sum(1 for _, o in report if o == "applied")
        skipped = len(report) - applied
        print(
            f"OK: submodule at pinned gitlink; patches: {applied} applied, "
            f"{skipped} skipped; ratified-state reconciliation clean; "
            "external/POB_VERSION.txt regenerated."
        )
        return EXIT_OK
    except SetupError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return err.exit_code


if __name__ == "__main__":
    sys.exit(main())
