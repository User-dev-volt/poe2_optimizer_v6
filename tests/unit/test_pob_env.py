"""Unit tests for src/pob_env.py and the conftest guard (story 3.5.4).

Env doubles are fabricated in tmp_path as REAL git repos: the parent repo
gets a genuine mode-160000 gitlink via ``git update-index --cacheinfo``
(no clone, no network), the submodule is a tiny local repo, and the
POB_VERSION.txt double is rendered by the REAL story 3.5.2 generator so the
format contract between generator and verifier is exercised, not mimicked.
Each broken double proves one invariant's violation; the well-formed double
proves the positive path (AC-3.5.4.4 / Task 4).

The guard-level tests run the REAL tests/conftest.py guard end-to-end: probe
test files collected under tests/ (so the actual conftest chain loads) with
POB_ENV_GUARD_ROOT pointing verify() at a double — asserting red-not-skip
for the parity-marked probe, green for the unmarked probe in the SAME run
(unmarked tests unaffected), and the violation-specific message in the
output. Probe filenames deliberately do NOT match ``test_*.py`` so a leaked
directory (Windows AV holding a handle through rmtree, hard crash skipping
finally) is invisible to normal collection.

No LuaJIT anywhere; git subprocesses only.
"""

import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from src import pob_env
from src.pob_env import verify

REPO_ROOT = Path(__file__).resolve().parents[2]

# The REAL generator renders the version-file doubles (format contract).
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import generate_pob_version  # noqa: E402

_GIT_IDENTITY = [
    "-c", "user.name=envdouble",
    "-c", "user.email=envdouble@example.invalid",
    "-c", "commit.gpgsign=false",
]

# Context-carrying patch with repo-root-relative paths, matching the
# production patch convention (diff --git header + context lines). The
# context lets a reverse-check still pass on a file with TRAILING divergence
# — exactly the blind spot the byte reconciliation exists to close.
PATCH_TEXT = (
    "diff --git a/external/pob-engine/target.txt b/external/pob-engine/target.txt\n"
    "--- a/external/pob-engine/target.txt\n"
    "+++ b/external/pob-engine/target.txt\n"
    "@@ -1,3 +1,3 @@\n"
    " ctx1\n"
    "-old\n"
    "+new\n"
    " ctx2\n"
)
TARGET_PRISTINE = "ctx1\nold\nctx2\n"
TARGET_PATCHED = "ctx1\nnew\nctx2\n"


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *_GIT_IDENTITY, *args],
        cwd=cwd, capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=True,
    )
    return result.stdout.strip()


def make_env_double(
    root: Path,
    *,
    no_git: bool = False,
    no_gitlink: bool = False,
    gitlink_mismatch: bool = False,
    version_file: bool = True,
    version_marker: bool = True,
    version_commit_match: bool = True,
    baseline_file: bool = True,
    baseline_corrupt: bool = False,
    baseline_version: str = "0.15.0",
    baseline_stale: bool = False,
    baseline_has_version: bool = True,
    patch_applied: bool | None = None,  # None = no patch in the set
) -> Path:
    """Fabricate a repo double exhibiting exactly the requested defects."""
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main", ".")
    _git(root, "config", "core.autocrlf", "false")

    sub = root / "external" / "pob-engine"
    sub.mkdir(parents=True)
    if no_git:
        (sub / "placeholder.txt").write_text("phantom copy\n", newline="\n")
        sub_sha = "1" * 40  # gitlinks need no backing object in the parent
    else:
        _git(sub, "init", "-q", "-b", "main", ".")
        _git(sub, "config", "core.autocrlf", "false")
        (sub / "manifest.xml").write_text(
            '<Version number="0.15.0" />\n', newline="\n"
        )
        (sub / "target.txt").write_text(TARGET_PRISTINE, newline="\n")
        _git(sub, "add", "manifest.xml", "target.txt")
        _git(sub, "commit", "-q", "-m", "base")
        sub_sha = _git(sub, "rev-parse", "HEAD")
        if gitlink_mismatch:
            (sub / "drift.txt").write_text("drift\n", newline="\n")
            _git(sub, "add", "drift.txt")
            _git(sub, "commit", "-q", "-m", "drift")  # HEAD moves; pin stays
        if patch_applied is True:
            (sub / "target.txt").write_text(TARGET_PATCHED, newline="\n")

    if not no_gitlink:
        _git(
            root, "update-index", "--add",
            "--cacheinfo", f"160000,{sub_sha},external/pob-engine",
        )
    (root / ".gitmodules").write_text(
        '[submodule "external/pob-engine"]\n'
        "\tpath = external/pob-engine\n"
        "\turl = https://example.invalid/pob.git\n",
        newline="\n",
    )
    _git(root, "add", ".gitmodules")
    _git(root, "commit", "-q", "-m", "pin")

    patches = root / "external" / "patches"
    patches.mkdir()
    (patches / "README.md").write_text("not a patch\n", newline="\n")
    patch_states: list[tuple[str, bool]] = []
    if patch_applied is not None:
        (patches / "0001-test.patch").write_text(PATCH_TEXT, newline="\n")
        patch_states.append(("0001-test.patch", bool(patch_applied)))

    if version_file:
        if version_marker:
            # Rendered by the REAL generator — the exact bytes setup_pob
            # would write — so verify()'s parsing is contract-tested.
            content = generate_pob_version.render(
                commit=sub_sha if version_commit_match else "0" * 40,
                version="0.15.0",
                url="https://example.invalid/pob.git",
                patches=patch_states,
            )
        else:
            content = "\n".join(
                ["hand-written pin file", "", f"Commit: {sub_sha}",
                 "Version: 0.15.0", ""]
            )
        (root / "external" / "POB_VERSION.txt").write_text(content, newline="\n")

    fixtures = root / "tests" / "fixtures" / "parity_builds"
    fixtures.mkdir(parents=True)
    if baseline_file:
        if baseline_corrupt:
            (fixtures / "gui_baseline_stats.json").write_text(
                "{not valid json", newline="\n"
            )
        else:
            metadata: dict = {}
            if baseline_has_version:
                metadata["pob_version"] = baseline_version
            if baseline_stale:
                metadata["stale"] = True
                metadata["stale_reason"] = "test double"
            (fixtures / "gui_baseline_stats.json").write_text(
                json.dumps({"_metadata": metadata, "build_x": {"total_dps": 1.0}}),
                newline="\n",
            )

    # Story 3.5.5 extended the check-(d) allowlist. The defect flags above
    # target only the FIRST (subject) entry; every other allowlisted
    # baseline gets a stale-flagged stub, derived from the live tuple.
    # Stale-flagged is the only (d)-neutral state in EVERY double (a
    # versioned non-stale stub would trip "cannot determine pinned version"
    # in manifest-less doubles like no_git) — so a double stays red only
    # for the defect a test asked for, and future allowlist extensions
    # cannot silently break the doubles again.
    for rel in pob_env.BASELINE_METADATA_FILES[1:]:
        extra = root / rel
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_text(
            json.dumps({
                "_metadata": {
                    "pob_version": "0.15.0",
                    "stale": True,
                    "stale_reason": "env-double background stub",
                },
                "stats": {},
            }),
            newline="\n",
        )

    return root


def _invariants(result) -> list:
    return [v.invariant for v in result.violations]


class TestVerifyPositive:
    def test_wellformed_double_passes(self, tmp_path):
        root = make_env_double(tmp_path / "repo")
        result = verify(root)
        assert result.ok, result.summary()
        assert result.violations == ()

    def test_applied_patch_and_stale_flag_pass(self, tmp_path):
        # Stale-flagged old baselines are an HONEST state (story dev notes);
        # an applied patch reverse-checks clean AND byte-reconciles clean.
        root = make_env_double(
            tmp_path / "repo",
            baseline_version="0.12.2", baseline_stale=True,
            patch_applied=True,
        )
        result = verify(root)
        assert result.ok, result.summary()


class TestVerifyViolations:
    def test_missing_git_repo_is_violation_a(self, tmp_path):
        # baseline_stale=True keeps (d) quiet (no manifest in a phantom dir),
        # isolating the (a) violation.
        root = make_env_double(
            tmp_path / "repo", no_git=True, baseline_stale=True
        )
        result = verify(root)
        assert not result.ok
        assert _invariants(result) == ["(a) real-repo"]

    def test_missing_gitlink_is_violation_b(self, tmp_path):
        # The historic phantom-gitlink failure mode: no 160000 entry at all.
        root = make_env_double(tmp_path / "repo", no_gitlink=True)
        result = verify(root)
        assert not result.ok
        assert _invariants(result) == ["(b) head-matches-gitlink"]
        assert "missing" in result.violations[0].message

    def test_gitlink_mismatch_is_violation_b(self, tmp_path):
        root = make_env_double(tmp_path / "repo", gitlink_mismatch=True)
        result = verify(root)
        assert not result.ok
        assert _invariants(result) == ["(b) head-matches-gitlink"]
        assert "drifted" in result.violations[0].message

    def test_missing_version_file_is_violation_c(self, tmp_path):
        root = make_env_double(tmp_path / "repo", version_file=False)
        result = verify(root)
        assert _invariants(result) == ["(c) generated-version-file"]

    def test_markerless_version_file_is_violation_c(self, tmp_path):
        # A hand-written POB_VERSION.txt (no generation marker) must be caught.
        root = make_env_double(tmp_path / "repo", version_marker=False)
        result = verify(root)
        assert _invariants(result) == ["(c) generated-version-file"]
        assert "hand-" in result.violations[0].message

    def test_version_commit_mismatch_is_violation_c(self, tmp_path):
        root = make_env_double(tmp_path / "repo", version_commit_match=False)
        result = verify(root)
        assert _invariants(result) == ["(c) generated-version-file"]
        assert "stale or hand-edited" in result.violations[0].message

    def test_unflagged_stale_baseline_is_violation_d(self, tmp_path):
        root = make_env_double(
            tmp_path / "repo", baseline_version="0.12.2", baseline_stale=False
        )
        result = verify(root)
        assert _invariants(result) == ["(d) baseline-metadata"]
        assert "not stale-flagged" in result.violations[0].message

    def test_missing_baseline_file_is_violation_d(self, tmp_path):
        root = make_env_double(tmp_path / "repo", baseline_file=False)
        result = verify(root)
        assert _invariants(result) == ["(d) baseline-metadata"]
        assert "missing" in result.violations[0].message

    def test_corrupt_baseline_json_is_violation_d(self, tmp_path):
        root = make_env_double(tmp_path / "repo", baseline_corrupt=True)
        result = verify(root)
        assert _invariants(result) == ["(d) baseline-metadata"]
        assert "unreadable" in result.violations[0].message

    def test_missing_version_metadata_is_violation_d(self, tmp_path):
        root = make_env_double(tmp_path / "repo", baseline_has_version=False)
        result = verify(root)
        assert _invariants(result) == ["(d) baseline-metadata"]
        assert "pob_version" in result.violations[0].message

    def test_unapplied_patch_is_violation_e(self, tmp_path):
        root = make_env_double(tmp_path / "repo", patch_applied=False)
        result = verify(root)
        assert not result.ok
        # Reverse-check misses it AND the byte reconciliation flags it.
        assert set(_invariants(result)) == {"(e) patches-applied"}
        assert any(
            "not applied" in v.message for v in result.violations
        ), result.summary()

    def test_messages_carry_the_fix_command(self, tmp_path):
        root = make_env_double(tmp_path / "repo", version_file=False)
        result = verify(root)
        assert "setup_pob.py" in result.summary()


class TestRatifiedStateReconciliation:
    """The byte-exact check that closes the wrong-skip blind spot: a tree
    that still reverse-checks 'applied' but diverges from (pristine + patch
    set applied once) must be flagged — the 2026-07-02 double-apply incident
    class — as must unrecorded edits to other tracked engine files."""

    def test_divergent_patched_file_detected(self, tmp_path):
        root = make_env_double(tmp_path / "repo", patch_applied=True)
        target = root / "external" / "pob-engine" / "target.txt"
        # Still reverse-checks clean (the hunk matches at its position), but
        # the file no longer equals the ratified post-patch bytes.
        target.write_text(TARGET_PATCHED + "trailing divergence\n", newline="\n")

        problems = pob_env.patched_tree_mismatches(root)
        assert any("ratified post-patch content" in p for p in problems), problems

        result = verify(root)
        assert not result.ok
        assert "(e) patches-applied" in _invariants(result)

    def test_unrecorded_engine_edit_detected(self, tmp_path):
        # No patches at all: ANY modified tracked file in the submodule is
        # an unrecorded engine edit (plan risk #2).
        root = make_env_double(tmp_path / "repo")
        (root / "external" / "pob-engine" / "target.txt").write_text(
            "tampered\n", newline="\n"
        )

        problems = pob_env.patched_tree_mismatches(root)
        assert any("unrecorded" in p for p in problems), problems

        result = verify(root)
        assert not result.ok
        assert "(e) patches-applied" in _invariants(result)

    def test_clean_patched_tree_reconciles_empty(self, tmp_path):
        root = make_env_double(tmp_path / "repo", patch_applied=True)
        assert pob_env.patched_tree_mismatches(root) == []


class TestNeverRaises:
    def test_nonexistent_root_returns_violations_not_exception(self, tmp_path):
        result = verify(tmp_path / "does-not-exist")
        assert not result.ok
        assert result.violations  # every problem is a Violation, no raise


class TestSharedContracts:
    def test_generated_marker_matches_generator(self):
        # src/ must not import from scripts/, so the marker literal is
        # mirrored — this test pins the two constants together.
        assert pob_env.GENERATED_MARKER == generate_pob_version.GENERATED_MARKER


class TestCorpusEntryGuard:
    """AC-3.5.4.3: the corpus entry point refuses to run (exit 2) on a bad
    environment — exercised against the real script module."""

    def _load_script_module(self):
        import importlib.util

        script = REPO_ROOT / "scripts" / "run_epic2_validation_isolated.py"
        spec = importlib.util.spec_from_file_location(
            "run_epic2_validation_under_test", script
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_corpus_main_exits_2_on_env_violation(self, monkeypatch, capsys):
        mod = self._load_script_module()
        bad = pob_env.PobEnvResult(
            ok=False,
            violations=(pob_env.Violation("(a) real-repo", "fabricated"),),
        )
        monkeypatch.setattr(mod, "verify", lambda root: bad)

        assert mod.main() == 2
        out = capsys.readouterr().out
        assert "PoB environment verification failed" in out
        assert "setup_pob.py" in out


class TestConftestGuard:
    """AC-3.5.4.4: the REAL autouse guard goes red-not-skip on a broken env,
    while an unmarked test in the SAME run stays green (AC-3.5.4.3: unmarked
    tests unaffected).

    Probe files are placed under tests/ (so the actual tests/conftest.py is
    in their conftest chain) and passed to a subprocess pytest as explicit
    file args with POB_ENV_GUARD_ROOT pointing at an env double. Filenames
    do not match test_*.py, so a leaked probe dir is inert for discovery.
    """

    def _run_guarded_probes(self, guard_root: Path) -> subprocess.CompletedProcess:
        probe_dir = REPO_ROOT / "tests" / f"_tmp_guard_{uuid.uuid4().hex[:8]}"
        probe_dir.mkdir()
        try:
            marked = probe_dir / "guard_probe_marked.py"
            unmarked = probe_dir / "guard_probe_unmarked.py"
            marked.write_text(
                "import pytest\n"
                "\n"
                "@pytest.mark.parity\n"
                "def test_parity_marked_probe():\n"
                "    assert True\n",
                newline="\n",
            )
            unmarked.write_text(
                "def test_unmarked_probe():\n"
                "    assert True\n",
                newline="\n",
            )
            env = dict(os.environ, POB_ENV_GUARD_ROOT=str(guard_root))
            return subprocess.run(
                [sys.executable, "-m", "pytest", str(marked), str(unmarked),
                 "-q", "-p", "no:cacheprovider"],
                cwd=REPO_ROOT, env=env,
                capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=180,
            )
        finally:
            shutil.rmtree(probe_dir, ignore_errors=True)

    @pytest.mark.slow
    def test_broken_env_fails_never_skips_and_spares_unmarked(self, tmp_path):
        broken = make_env_double(tmp_path / "broken", version_marker=False)
        proc = self._run_guarded_probes(broken)
        out = proc.stdout + proc.stderr

        assert proc.returncode != 0, out
        # The guard's banner AND the violation-specific message reach output.
        assert "PoB environment verification FAILED" in out
        assert "generation marker" in out, out
        # Marked probe: red as failure or setup error — NOT skipped.
        assert ("1 error" in out) or ("1 failed" in out), out
        assert "skipped" not in out, out
        # Unmarked probe in the SAME run is untouched by the broken env.
        assert "1 passed" in out, out

    @pytest.mark.slow
    def test_wellformed_env_lets_both_probes_pass(self, tmp_path):
        good = make_env_double(tmp_path / "good")
        proc = self._run_guarded_probes(good)
        out = proc.stdout + proc.stderr

        assert proc.returncode == 0, out
        assert "2 passed" in out, out
