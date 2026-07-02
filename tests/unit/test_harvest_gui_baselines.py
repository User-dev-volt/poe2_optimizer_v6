"""Unit tests for scripts/harvest_gui_baselines.py (story 3.5.5).

Pure Python, no LuaJIT (Task 3.3). All outputs go to tmp_path — tests never
write into tests/fixtures/. Version-file handling is exercised through the
injectable ``repo_root`` parameter (the harvester resolves
external/POB_VERSION.txt relative to it), so no monkeypatching of module
globals is needed.

The Task 5 contract tests do NOT reimplement 3.5.4's check (d): they feed a
freshly harvested fixture to the REAL ``src.pob_env.verify()`` (via the
shared ``make_env_double`` from tests/unit/test_pob_env.py) and assert the
version-match / stale semantics end-to-end.
"""

import ast
import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# scripts/ is not a package — import via path insertion (house convention).
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import harvest_gui_baselines as harvest  # noqa: E402

from src import pob_env  # noqa: E402
from tests.unit.test_pob_env import make_env_double  # noqa: E402

DEADEYE_XML = (
    REPO_ROOT / "tests" / "fixtures" / "realistic_builds"
    / "deadeye_lightning_arrow_76.xml"
)
COMMIT = "3e1b71c92dc5f7c295031700746a418558117b06"


def make_version_root(
    tmp: Path, *, version: str = "0.15.0", commit: str = COMMIT,
    marker: bool = True, version_file: bool = True,
) -> Path:
    """Minimal repo-root double: only the external/POB_VERSION.txt the
    harvester reads (its parsing mirrors pob_env check (c) semantics)."""
    root = tmp / "repo"
    (root / "external").mkdir(parents=True)
    if version_file:
        lines = []
        if marker:
            lines.append(harvest.GENERATED_MARKER)
        lines += ["", f"Commit: {commit}", f"Version: {version}", ""]
        (root / "external" / "POB_VERSION.txt").write_text(
            "\n".join(lines), encoding="utf-8", newline="\n"
        )
    return root


def run_harvest(tmp_path, *xml_paths, root=None, force=False,
                stale_reason=None, archetype="attack"):
    """Run main() against tmp outputs; return (exit_code, output_dir)."""
    if root is None:
        root = make_version_root(tmp_path)
    out_dir = tmp_path / "out"
    argv = [*map(str, xml_paths), "--archetype", archetype,
            "--output-dir", str(out_dir)]
    if force:
        argv.append("--force")
    if stale_reason is not None:
        argv += ["--stale-reason", stale_reason]
    return harvest.main(argv, repo_root=root), out_dir


def load_fixture(out_dir: Path, stem: str = "deadeye_lightning_arrow_76"):
    path = out_dir / f"{stem}.baseline.json"
    text = path.read_text(encoding="utf-8")
    return json.loads(text), text


class TestGoldenDeadeye:
    """AC-3.5.5.2: exact value round-trip from the deadeye fixture."""

    def test_totaldps_exact_roundtrip(self, tmp_path):
        code, out_dir = run_harvest(tmp_path, DEADEYE_XML)
        assert code == harvest.EXIT_OK
        fixture, text = load_fixture(out_dir)
        assert fixture["stats"]["TotalDPS"] == 18097.067904221
        # The serialized JSON carries the raw XML digits verbatim — full
        # precision round-trip, not 2-dp agreement.
        assert "18097.067904221" in text

    def test_spot_checked_stats_match_raw_xml(self, tmp_path):
        code, out_dir = run_harvest(tmp_path, DEADEYE_XML)
        assert code == harvest.EXIT_OK
        stats = load_fixture(out_dir)[0]["stats"]
        assert stats["Life"] == 1059
        assert stats["CritChance"] == 5.5
        assert stats["AverageDamage"] == 9426.49885

    def test_stats_map_has_exactly_102_entries(self, tmp_path):
        # 102 <PlayerStat> elements in the fixture (recon-verified; story
        # AC-3.5.5.2 asserts the same count).
        code, out_dir = run_harvest(tmp_path, DEADEYE_XML)
        assert code == harvest.EXIT_OK
        stats = load_fixture(out_dir)[0]["stats"]
        assert len(stats) == 102

    def test_colon_named_stat_kept_verbatim(self, tmp_path):
        code, out_dir = run_harvest(tmp_path, DEADEYE_XML)
        assert code == harvest.EXIT_OK
        stats = load_fixture(out_dir)[0]["stats"]
        assert stats["Spec:LifeInc"] == 5  # no renaming/snake_casing

    def test_all_values_are_numbers(self, tmp_path):
        code, out_dir = run_harvest(tmp_path, DEADEYE_XML)
        assert code == harvest.EXIT_OK
        stats = load_fixture(out_dir)[0]["stats"]
        assert all(isinstance(v, float) for v in stats.values())


class TestMetadata:
    """AC-3.5.5.1: embedded metadata block, field names per 3.5.4."""

    def test_metadata_fields(self, tmp_path):
        root = make_version_root(tmp_path)
        xml_dir = root / "tests" / "fixtures" / "gui_baselines" / "xml"
        xml_dir.mkdir(parents=True)
        xml_copy = xml_dir / DEADEYE_XML.name
        shutil.copyfile(DEADEYE_XML, xml_copy)

        code, out_dir = run_harvest(tmp_path, xml_copy, root=root)
        assert code == harvest.EXIT_OK
        fixture = load_fixture(out_dir)[0]

        assert fixture["schema_version"] == 1
        meta = fixture["_metadata"]
        assert meta["pob_version"] == "0.15.0"  # string, exact form
        assert meta["pob_commit"] == COMMIT
        assert meta["captured"] == date.today().isoformat()
        # Repo-relative posix path when the XML lives under repo_root.
        assert meta["source_xml"] == (
            "tests/fixtures/gui_baselines/xml/deadeye_lightning_arrow_76.xml"
        )
        assert meta["source_sha256"] == hashlib.sha256(
            DEADEYE_XML.read_bytes()
        ).hexdigest()
        assert meta["archetype"] == "attack"
        assert meta["stale"] is False
        assert "stale_reason" not in meta

    def test_stale_reason_flag_marks_fixture_stale(self, tmp_path):
        # Corpus XMLs (unknown uploader GUI version) must be committable
        # only as honestly stale fixtures (story dev notes).
        code, out_dir = run_harvest(
            tmp_path, DEADEYE_XML, stale_reason="pobb.in provenance"
        )
        assert code == harvest.EXIT_OK
        meta = load_fixture(out_dir)[0]["_metadata"]
        assert meta["stale"] is True
        assert meta["stale_reason"] == "pobb.in provenance"
        assert meta["pob_version"] == "0.15.0"  # attested version still stamped


class TestInputHandling:
    def test_directory_input_harvests_each_xml(self, tmp_path):
        src_dir = tmp_path / "builds"
        src_dir.mkdir()
        shutil.copyfile(DEADEYE_XML, src_dir / "a.xml")
        shutil.copyfile(DEADEYE_XML, src_dir / "b.xml")
        code, out_dir = run_harvest(tmp_path, src_dir)
        assert code == harvest.EXIT_OK
        assert (out_dir / "a.baseline.json").is_file()
        assert (out_dir / "b.baseline.json").is_file()

    def test_missing_input_path_is_input_error(self, tmp_path, capsys):
        code, _ = run_harvest(tmp_path, tmp_path / "nope.xml")
        assert code == harvest.EXIT_INPUT
        assert "ERROR" in capsys.readouterr().err

    def test_directory_without_xml_is_input_error(self, tmp_path, capsys):
        empty = tmp_path / "empty"
        empty.mkdir()
        code, _ = run_harvest(tmp_path, empty)
        assert code == harvest.EXIT_INPUT
        assert "no *.xml" in capsys.readouterr().err

    def test_subdirectory_named_xml_is_skipped(self, tmp_path):
        # A DIRECTORY named *.xml must not reach read_bytes() (raw
        # PermissionError on Windows); it is silently skipped by the
        # is_file() filter.
        src_dir = tmp_path / "builds"
        src_dir.mkdir()
        (src_dir / "decoy.xml").mkdir()
        shutil.copyfile(DEADEYE_XML, src_dir / "real.xml")
        code, out_dir = run_harvest(tmp_path, src_dir)
        assert code == harvest.EXIT_OK
        assert (out_dir / "real.baseline.json").is_file()
        assert not (out_dir / "decoy.baseline.json").exists()

    def test_equal_stem_inputs_are_refused_up_front(self, tmp_path, capsys):
        # dirA/build.xml + dirB/build.xml both map to build.baseline.json;
        # under --force the second would silently clobber the first, so the
        # collision is an input error before anything is written.
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()
        shutil.copyfile(DEADEYE_XML, dir_a / "build.xml")
        shutil.copyfile(DEADEYE_XML, dir_b / "build.xml")
        code, out_dir = run_harvest(tmp_path, dir_a, dir_b, force=True)
        assert code == harvest.EXIT_INPUT
        assert "collision" in capsys.readouterr().err
        assert not out_dir.exists()  # refused before any write


class TestNegativeCases:
    """AC-3.5.5.2 / Task 3.2: zero PlayerStat, duplicates, overwrite."""

    def test_xml_without_playerstat_is_clear_error(self, tmp_path, capsys):
        bad = tmp_path / "empty_build.xml"
        bad.write_text(
            "<PathOfBuilding2><Build level=\"1\"/></PathOfBuilding2>",
            encoding="utf-8", newline="\n",
        )
        code, out_dir = run_harvest(tmp_path, bad)
        assert code == harvest.EXIT_INPUT
        err = capsys.readouterr().err
        assert "no <PlayerStat> elements" in err
        assert not (out_dir / "empty_build.baseline.json").exists()

    def test_duplicate_stat_name_rejected_and_named(self, tmp_path, capsys):
        bad = tmp_path / "dup.xml"
        bad.write_text(
            "<PathOfBuilding2><Build>"
            "<PlayerStat stat=\"Life\" value=\"100\"/>"
            "<PlayerStat stat=\"Life\" value=\"200\"/>"
            "<PlayerStat stat=\"Mana\" value=\"50\"/>"
            "</Build></PathOfBuilding2>",
            encoding="utf-8", newline="\n",
        )
        code, _ = run_harvest(tmp_path, bad)
        assert code == harvest.EXIT_INPUT
        err = capsys.readouterr().err
        assert "duplicate" in err
        assert "Life" in err  # names the offending stat

    def test_non_numeric_value_is_input_error(self, tmp_path, capsys):
        bad = tmp_path / "nan.xml"
        bad.write_text(
            "<PathOfBuilding2><Build>"
            "<PlayerStat stat=\"Life\" value=\"not-a-number\"/>"
            "</Build></PathOfBuilding2>",
            encoding="utf-8", newline="\n",
        )
        code, _ = run_harvest(tmp_path, bad)
        assert code == harvest.EXIT_INPUT
        assert "non-numeric" in capsys.readouterr().err

    def test_non_finite_value_is_input_error(self, tmp_path, capsys):
        # float() accepts "nan"/"inf", but json must stay strict RFC 8259:
        # non-finite stats are refused instead of emitting NaN tokens.
        bad = tmp_path / "nonfinite.xml"
        bad.write_text(
            "<PathOfBuilding2><Build>"
            "<PlayerStat stat=\"Life\" value=\"100\"/>"
            "<PlayerStat stat=\"TotalDPS\" value=\"nan\"/>"
            "</Build></PathOfBuilding2>",
            encoding="utf-8", newline="\n",
        )
        code, out_dir = run_harvest(tmp_path, bad)
        assert code == harvest.EXIT_INPUT
        assert "non-finite" in capsys.readouterr().err
        assert not (out_dir / "nonfinite.baseline.json").exists()

    def test_malformed_xml_is_input_error(self, tmp_path, capsys):
        bad = tmp_path / "broken.xml"
        bad.write_text("<PathOfBuilding2>", encoding="utf-8", newline="\n")
        code, _ = run_harvest(tmp_path, bad)
        assert code == harvest.EXIT_INPUT
        assert "malformed XML" in capsys.readouterr().err

    def test_minionstat_is_ignored(self, tmp_path):
        # <MinionStat> exists in the corpus but is out of scope (Epic 4).
        mixed = tmp_path / "mixed.xml"
        mixed.write_text(
            "<PathOfBuilding2><Build>"
            "<PlayerStat stat=\"Life\" value=\"100\"/>"
            "<MinionStat stat=\"TotalDPS\" value=\"999\"/>"
            "</Build></PathOfBuilding2>",
            encoding="utf-8", newline="\n",
        )
        code, out_dir = run_harvest(tmp_path, mixed)
        assert code == harvest.EXIT_OK
        stats = load_fixture(out_dir, "mixed")[0]["stats"]
        assert stats == {"Life": 100.0}

    def test_existing_output_refused_without_force(self, tmp_path, capsys):
        root = make_version_root(tmp_path)
        code, out_dir = run_harvest(tmp_path, DEADEYE_XML, root=root)
        assert code == harvest.EXIT_OK
        before = load_fixture(out_dir)[1]

        code, _ = run_harvest(tmp_path, DEADEYE_XML, root=root)
        assert code == harvest.EXIT_EXISTS
        err = capsys.readouterr().err
        assert "already exists" in err
        assert "--force" in err
        assert load_fixture(out_dir)[1] == before  # untouched

    def test_force_allows_overwrite(self, tmp_path):
        root = make_version_root(tmp_path)
        code, out_dir = run_harvest(tmp_path, DEADEYE_XML, root=root)
        assert code == harvest.EXIT_OK
        code, _ = run_harvest(tmp_path, DEADEYE_XML, root=root, force=True)
        assert code == harvest.EXIT_OK


class TestVersionAttestation:
    """Subtask 1.3: refuse to stamp a version the generated
    POB_VERSION.txt cannot attest; --force degrades to stale+unversioned."""

    def test_missing_version_file_refused_without_force(self, tmp_path, capsys):
        root = make_version_root(tmp_path, version_file=False)
        code, out_dir = run_harvest(tmp_path, DEADEYE_XML, root=root)
        assert code == harvest.EXIT_VERSION
        assert "ERROR" in capsys.readouterr().err
        assert not out_dir.exists()  # nothing written

    def test_markerless_version_file_refused_without_force(
        self, tmp_path, capsys
    ):
        root = make_version_root(tmp_path, marker=False)
        code, _ = run_harvest(tmp_path, DEADEYE_XML, root=root)
        assert code == harvest.EXIT_VERSION
        assert "generation marker" in capsys.readouterr().err

    def test_force_yields_stale_unversioned_fixture_with_warning(
        self, tmp_path, capsys
    ):
        root = make_version_root(tmp_path, version_file=False)
        code, out_dir = run_harvest(
            tmp_path, DEADEYE_XML, root=root, force=True
        )
        assert code == harvest.EXIT_OK
        assert "WARNING" in capsys.readouterr().out
        meta = load_fixture(out_dir)[0]["_metadata"]
        assert meta["stale"] is True
        assert meta["pob_version"] is None  # never fabricated
        assert meta["pob_commit"] is None
        assert "stale_reason" in meta

    def test_markerless_with_force_is_stale(self, tmp_path):
        root = make_version_root(tmp_path, marker=False)
        code, out_dir = run_harvest(
            tmp_path, DEADEYE_XML, root=root, force=True
        )
        assert code == harvest.EXIT_OK
        meta = load_fixture(out_dir)[0]["_metadata"]
        assert meta["stale"] is True
        assert meta["pob_version"] is None


class TestSourceGuard:
    """Subtask 1.5 / AC-3.5.5.4: engine-agnostic by construction."""

    def test_no_forbidden_imports_in_script_source(self):
        source = (REPO_ROOT / "scripts" / "harvest_gui_baselines.py").read_text(
            encoding="utf-8"
        )
        modules: set[str] = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
        forbidden = sorted(
            m for m in modules
            if m == "lupa" or m.startswith("lupa.")
            or m == "src.calculator" or m.startswith("src.calculator.")
        )
        assert forbidden == [], f"engine imports leaked in: {forbidden}"

    def test_generation_marker_shared_with_pob_env(self):
        # The harvester consumes pob_env's constant (import, not a mirror)
        # so the 3.5.2/3.5.4 marker contract cannot drift.
        assert harvest.GENERATED_MARKER == pob_env.GENERATED_MARKER


class TestPobEnvContract:
    """Task 5 / AC-3.5.5.5: a freshly harvested fixture satisfies the REAL
    3.5.4 verify() check (d) — same fields, same stale semantics. Uses the
    shared env double and places the fixture at the exact path
    BASELINE_METADATA_FILES lists (coordinate, don't duplicate)."""

    def _harvest_into_double(self, tmp_path):
        double = make_env_double(tmp_path / "double")  # green env, 0.15.0
        out_dir = tmp_path / "out"
        code = harvest.main(
            [str(DEADEYE_XML), "--archetype", "attack",
             "--output-dir", str(out_dir)],
            repo_root=double,
        )
        assert code == harvest.EXIT_OK
        target = double / pob_env.BASELINE_METADATA_FILES[0]
        shutil.copyfile(
            out_dir / "deadeye_lightning_arrow_76.baseline.json", target
        )
        return double, target

    def test_fresh_fixture_passes_check_d(self, tmp_path):
        double, _ = self._harvest_into_double(tmp_path)
        result = pob_env.verify(double)
        assert result.ok, result.summary()

    def test_version_mismatch_without_stale_flag_is_violation_d(
        self, tmp_path
    ):
        double, target = self._harvest_into_double(tmp_path)
        doc = json.loads(target.read_text(encoding="utf-8"))
        doc["_metadata"]["pob_version"] = "0.14.0"  # simulate a pin bump
        target.write_text(json.dumps(doc), encoding="utf-8", newline="\n")

        result = pob_env.verify(double)
        assert not result.ok
        assert [v.invariant for v in result.violations] == [
            "(d) baseline-metadata"
        ]
        assert "not stale-flagged" in result.summary()

    def test_stale_flag_keeps_mismatched_fixture_green(self, tmp_path):
        double, target = self._harvest_into_double(tmp_path)
        doc = json.loads(target.read_text(encoding="utf-8"))
        doc["_metadata"]["pob_version"] = "0.14.0"
        doc["_metadata"]["stale"] = True
        doc["_metadata"]["stale_reason"] = "pin bumped; awaiting re-capture"
        target.write_text(json.dumps(doc), encoding="utf-8", newline="\n")

        result = pob_env.verify(double)
        assert result.ok, result.summary()

    def test_forced_unversioned_fixture_would_fail_check_d(self, tmp_path):
        # A --force fixture (pob_version null) is NOT committable as a
        # guarded baseline: check (d) flags missing version metadata even
        # when stale is true — documented in the README protocol.
        double = make_env_double(tmp_path / "double")
        (double / "external" / "POB_VERSION.txt").unlink()
        out_dir = tmp_path / "out"
        code = harvest.main(
            [str(DEADEYE_XML), "--archetype", "attack",
             "--output-dir", str(out_dir), "--force"],
            repo_root=double,
        )
        assert code == harvest.EXIT_OK
        target = double / pob_env.BASELINE_METADATA_FILES[0]
        shutil.copyfile(
            out_dir / "deadeye_lightning_arrow_76.baseline.json", target
        )

        result = pob_env.verify(double)
        assert not result.ok
        assert any(
            v.invariant == "(d) baseline-metadata" and "pob_version" in v.message
            for v in result.violations
        ), result.summary()

    def test_every_committed_baseline_fixture_is_guarded(self):
        # Ratchet for Task 4: pob_env check (d) reads ONLY the allowlist
        # tuple BASELINE_METADATA_FILES — a committed *.baseline.json that
        # is not listed there is invisible to verify(). Vacuously green
        # today (no fixtures captured yet); the moment a capture lands
        # without extending the tuple, this test goes red.
        fixture_dir = REPO_ROOT / "tests" / "fixtures" / "gui_baselines"
        committed = sorted(fixture_dir.glob("*.baseline.json"))
        guarded = set(pob_env.BASELINE_METADATA_FILES)
        unguarded = [
            p.relative_to(REPO_ROOT).as_posix()
            for p in committed
            if p.relative_to(REPO_ROOT).as_posix() not in guarded
        ]
        assert unguarded == [], (
            "committed baseline fixtures missing from "
            f"pob_env.BASELINE_METADATA_FILES: {unguarded} -- extend the "
            "tuple so verify() check (d) covers them (see "
            "tests/fixtures/gui_baselines/README.md)"
        )
