"""Unit tests for scripts/setup_pob.py (story 3.5.3).

Fast and hermetic: the skip-if-applied decision function is pure, patch
discovery runs against tmp_path, and the apply loop is exercised with
monkeypatched git probes. No LuaJIT, no real git repo needed.
"""

import sys
from pathlib import Path

import pytest

# scripts/ is not a package — import via path insertion (story 3.5.3 dev notes).
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import setup_pob  # noqa: E402


class TestDecidePatchAction:
    """The skip-if-applied primitive (AC-3.5.3.2): full truth table.

    Reverse-check FIRST: "already applied" outranks "could apply". Patch
    0002's context block repeats inside EvalMod, so on an already-patched
    tree the forward check still passes (matching the second occurrence);
    a forward-first rule double-applies the patch (observed 2026-07-02).
    """

    def test_check_passes_means_apply(self):
        assert setup_pob.decide_patch_action(True, False) == setup_pob.APPLY

    def test_reverse_wins_even_if_forward_also_passes(self):
        # The double-apply hazard: forward-check can succeed on a patched
        # tree when the patch context repeats. Reverse-check has priority.
        assert setup_pob.decide_patch_action(True, True) == setup_pob.SKIP

    def test_reverse_check_passes_means_skip(self):
        assert setup_pob.decide_patch_action(False, True) == setup_pob.SKIP

    def test_neither_passes_means_conflict(self):
        assert setup_pob.decide_patch_action(False, False) == setup_pob.CONFLICT


class TestDiscoverPatches:
    """Patch set is data (AC-3.5.3.1): glob *.patch, sorted, nothing hardcoded."""

    def test_sorted_patch_files_only(self, tmp_path):
        patches = tmp_path / "external" / "patches"
        patches.mkdir(parents=True)
        (patches / "0002-second.patch").write_text("b")
        (patches / "0001-first.patch").write_text("a")
        (patches / "README.md").write_text("not a patch")
        (patches / ".gitattributes").write_text("*.patch -text")

        found = setup_pob.discover_patches(tmp_path)

        assert [p.name for p in found] == ["0001-first.patch", "0002-second.patch"]

    def test_missing_directory_is_empty_set(self, tmp_path):
        assert setup_pob.discover_patches(tmp_path) == []


class TestPatchTargetFiles:
    """Conflict messages must name the target file(s) (AC-3.5.3.5)."""

    def test_extracts_and_dedupes_diff_headers(self, tmp_path):
        patch = tmp_path / "x.patch"
        patch.write_text(
            "prologue line\n"
            "diff --git a/external/pob-engine/src/Data/Global.lua "
            "b/external/pob-engine/src/Data/Global.lua\n"
            "--- a/external/pob-engine/src/Data/Global.lua\n"
            "+++ b/external/pob-engine/src/Data/Global.lua\n"
            "@@ -1 +1 @@\n-a\n+b\n"
            "diff --git a/external/pob-engine/src/Modules/CalcOffence.lua "
            "b/external/pob-engine/src/Modules/CalcOffence.lua\n"
        )
        assert setup_pob.patch_target_files(patch) == [
            "external/pob-engine/src/Data/Global.lua",
            "external/pob-engine/src/Modules/CalcOffence.lua",
        ]


class TestExitCodes:
    """Exit codes are distinct and stable (AC-3.5.3.5) — 3.5.4/CI branch on them."""

    def test_all_distinct(self):
        codes = [
            setup_pob.EXIT_OK,
            setup_pob.EXIT_INTERNAL,
            setup_pob.EXIT_USAGE,
            setup_pob.EXIT_PREFLIGHT,
            setup_pob.EXIT_SUBMODULE_MISSING,
            setup_pob.EXIT_GITLINK_MISMATCH,
            setup_pob.EXIT_PATCH_CONFLICT,
        ]
        assert len(set(codes)) == len(codes)
        assert setup_pob.EXIT_OK == 0
        assert all(c != 0 for c in codes[1:])

    def test_documented_in_module_docstring(self):
        assert "Exit codes" in setup_pob.__doc__


class TestApplyPatchesLoop:
    """Loop semantics (AC-3.5.3.1/2/5): per-patch outcome, deterministic order,
    conflicts reported with targets while non-conflicting patches still apply."""

    @pytest.fixture
    def three_patches(self, tmp_path, monkeypatch):
        patches = tmp_path / "external" / "patches"
        patches.mkdir(parents=True)
        for name in ("0001-fresh.patch", "0002-applied.patch", "0003-broken.patch"):
            (patches / name).write_text(
                f"diff --git a/target/{name}.lua b/target/{name}.lua\n"
            )

        # Simulated git-probe outcomes per (patch, mode). Reverse-check runs
        # first; the forward check is only probed when reverse fails:
        #   0001: reverse fails, --check passes -> apply (real apply succeeds)
        #   0002: reverse passes -> skip (forward probe must NOT run)
        #   0003: both checks fail -> conflict
        class FakeResult:
            def __init__(self, rc):
                self.returncode = rc
                self.stderr = "simulated"

        calls = []

        def fake_git_apply(repo_root, patch_path, *extra):
            calls.append((patch_path.name, extra))
            outcomes = {
                ("0001-fresh.patch", ("--reverse", "--check")): 1,
                ("0001-fresh.patch", ("--check",)): 0,
                ("0001-fresh.patch", ()): 0,
                ("0002-applied.patch", ("--reverse", "--check")): 0,
                ("0003-broken.patch", ("--reverse", "--check")): 1,
                ("0003-broken.patch", ("--check",)): 1,
            }
            # A probe missing from the table (e.g. a forward check on an
            # already-applied patch) is a test failure by KeyError.
            return FakeResult(outcomes[(patch_path.name, extra)])

        monkeypatch.setattr(setup_pob, "_git_apply", fake_git_apply)
        return tmp_path, calls

    def test_report_and_conflicts(self, three_patches):
        repo_root, calls = three_patches
        report, conflicts = setup_pob.apply_patches(repo_root)

        assert report[0] == ("0001-fresh.patch", "applied")
        assert report[1] == ("0002-applied.patch", "skipped (already applied)")
        assert report[2][0] == "0003-broken.patch"
        assert report[2][1].startswith("FAILED: 0003-broken.patch -> ")
        assert "target/0003-broken.patch.lua" in report[2][1]
        assert conflicts == ["0003-broken.patch"]
        # "applied" must mean the real (non-check) git apply actually ran —
        # a report-only regression must not stay green.
        assert ("0001-fresh.patch", ()) in calls

    def test_processing_order_is_sorted(self, three_patches):
        repo_root, calls = three_patches
        setup_pob.apply_patches(repo_root)
        seen_order = [name for name, extra in calls if extra == ("--reverse", "--check")]
        assert seen_order == sorted(seen_order)

    def test_no_forward_probe_on_applied_patch(self, three_patches):
        # Guards the double-apply fix: once reverse-check passes, the
        # forward check must not even be consulted.
        repo_root, calls = three_patches
        setup_pob.apply_patches(repo_root)
        assert ("0002-applied.patch", ("--check",)) not in calls


class TestMainExitPaths:
    """Real failure paths return their documented exit codes (AC-3.5.3.5) —
    driven end-to-end against fabricated env doubles, not mocked dispatch."""

    def test_not_a_git_checkout_exits_preflight(self, tmp_path, capsys):
        # The zip/tarball-download case: files on disk, no git repo.
        (tmp_path / ".gitmodules").write_text("stub", newline="\n")
        assert setup_pob.main([], repo_root=tmp_path) == setup_pob.EXIT_PREFLIGHT
        assert "not a git checkout" in capsys.readouterr().err

    def test_missing_gitmodules_exits_preflight(self, tmp_path, capsys):
        from tests.unit.test_pob_env import _git
        _git(tmp_path, "init", "-q", "-b", "main", ".")
        assert setup_pob.main([], repo_root=tmp_path) == setup_pob.EXIT_PREFLIGHT
        assert ".gitmodules" in capsys.readouterr().err

    def test_missing_patches_dir_exits_preflight(self, tmp_path, capsys):
        from tests.unit.test_pob_env import make_env_double
        root = make_env_double(tmp_path / "repo")
        import shutil as _shutil
        _shutil.rmtree(root / "external" / "patches")
        assert setup_pob.main([], repo_root=root) == setup_pob.EXIT_PREFLIGHT
        assert "external/patches" in capsys.readouterr().err

    def test_gitlink_mismatch_exits_5_and_never_resets(self, tmp_path, capsys):
        from tests.unit.test_pob_env import make_env_double, _git
        root = make_env_double(tmp_path / "repo", gitlink_mismatch=True)
        sub = root / "external" / "pob-engine"
        drifted_head = _git(sub, "rev-parse", "HEAD")

        assert setup_pob.main([], repo_root=root) == setup_pob.EXIT_GITLINK_MISMATCH
        err = capsys.readouterr().err
        assert "Refusing to reset" in err
        assert "checkout --detach" in err  # remediation names the command
        # Non-destructive: the drifted checkout is untouched (plan risk #2).
        assert _git(sub, "rev-parse", "HEAD") == drifted_head

    def test_patch_conflict_exits_6_naming_patch_and_target(self, tmp_path, capsys):
        from tests.unit.test_pob_env import make_env_double
        root = make_env_double(tmp_path / "repo", patch_applied=False)
        # Neither pre- nor post-patch state: both probes fail -> conflict.
        (root / "external" / "pob-engine" / "target.txt").write_text(
            "weird\n", newline="\n"
        )
        assert setup_pob.main([], repo_root=root) == setup_pob.EXIT_PATCH_CONFLICT
        err = capsys.readouterr().err
        assert "0001-test.patch" in err

    def test_fresh_apply_happy_path_exits_0(self, tmp_path, capsys):
        from tests.unit.test_pob_env import make_env_double, TARGET_PATCHED
        root = make_env_double(tmp_path / "repo", patch_applied=False)

        assert setup_pob.main([], repo_root=root) == setup_pob.EXIT_OK
        # The patch was REALLY applied (not just reported).
        target = root / "external" / "pob-engine" / "target.txt"
        assert target.read_text(encoding="utf-8") == TARGET_PATCHED
        # And the version file was regenerated from the double's own state.
        version = (root / "external" / "POB_VERSION.txt").read_text(encoding="utf-8")
        assert "0001-test.patch: applied" in version
        out = capsys.readouterr().out
        assert "0001-test.patch: applied" in out
        assert "reconciliation clean" in out

    def test_divergent_patched_file_exits_6(self, tmp_path, capsys):
        # Reverse-check still passes (the hunk matches at its position) but
        # the byte reconciliation catches trailing divergence — the
        # double-apply incident class.
        from tests.unit.test_pob_env import make_env_double, TARGET_PATCHED
        root = make_env_double(tmp_path / "repo", patch_applied=True)
        (root / "external" / "pob-engine" / "target.txt").write_text(
            TARGET_PATCHED + "trailing divergence\n", newline="\n"
        )
        assert setup_pob.main([], repo_root=root) == setup_pob.EXIT_PATCH_CONFLICT
        assert "ratified post-patch state" in capsys.readouterr().err
