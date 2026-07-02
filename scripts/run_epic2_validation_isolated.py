"""Epic 2 Validation with Full Subprocess Isolation

Runs optimizer on each build in a completely separate Python process
to avoid Windows Fatal Exception 0xe24c4a02.

Each build gets its own fresh Python interpreter with no LuaJIT state carryover.

Usage:
    python scripts/run_epic2_validation_isolated.py

Exit codes:
    0  validation ran and passed
    1  validation ran and failed (missing corpus, errors, or gate miss)
    2  PoB environment verification failed (story 3.5.4): the engine is
       drifted/unverifiable, so no corpus time is spent — run
       `python scripts/setup_pob.py` and retry

Author: Amelia (Dev Agent)
Date: 2025-11-26
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
from statistics import median, mean

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pob_env import verify  # noqa: E402  (needs the path insert above)

# Windows: when stdout is redirected to a file, Python defaults to cp1252 and
# printing '→'/'✅' raises UnicodeEncodeError — which the per-build except block
# would swallow, silently converting SUCCESSFUL results into errors.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


CORPUS_DIR = Path("tests/fixtures/realistic_builds")
RESULTS_DIR = Path("docs/validation")
OPTIMIZATION_BUDGET = 20
MAX_TIME_SECONDS = 300


# Worker script content (will be written to temp file)
WORKER_SCRIPT = '''
import sys
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.build_data import BuildData, CharacterClass
from src.models.optimization_config import OptimizationConfiguration
from src.optimizer.hill_climbing import optimize_build
from src.parsers.xml_utils import parse_xml
import src.parsers.pob_parser as pob_parser


def load_build_from_xml(xml_path: Path) -> BuildData:
    """Load BuildData from XML file."""
    xml_str = xml_path.read_text(encoding='utf-8')
    data = parse_xml(xml_str)

    pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
    build_section = pob_root["Build"]

    character_class = CharacterClass(build_section.get("@className", "Witch"))
    level = int(build_section.get("@level", "90"))
    ascendancy = build_section.get("@ascendClassName")
    if ascendancy == "None":
        ascendancy = None

    tree_section = pob_root.get("Tree", {})
    spec = tree_section.get("Spec", {}) if isinstance(tree_section, dict) else {}
    nodes_str = spec.get("@nodes", "") if isinstance(spec, dict) else ""

    passive_nodes = set()
    if nodes_str:
        try:
            passive_nodes = set(int(n.strip()) for n in nodes_str.split(",") if n.strip())
        except ValueError:
            pass

    # Use the production config parser (handles multi-<ConfigSet> XML + @boolean inputs).
    config = pob_parser._extract_config(pob_root)

    # Load items AND skills so the calc is meaningful. Without them the build has no
    # weapon/skill and DPS collapses to a degenerate ~1.5 baseline, making any
    # optimization result meaningless (this was the original harness bug).
    items = pob_parser._extract_items(pob_root)
    skills = pob_parser._extract_skills(pob_root)

    return BuildData(
        character_class=character_class,
        level=level,
        ascendancy=ascendancy,
        passive_nodes=passive_nodes,
        tree_version=build_section.get("@targetVersion", "0_1"),
        build_name=xml_path.stem,
        items=items,
        skills=skills,
        config=config
    )


if __name__ == "__main__":
    xml_path = Path(sys.argv[1])
    budget = int(sys.argv[2])
    max_time = int(sys.argv[3])
    result_path = Path(sys.argv[4])

    result = {
        "build_name": xml_path.stem,
        "status": "pending",
        "error": None
    }

    try:
        build = load_build_from_xml(xml_path)

        config = OptimizationConfiguration(
            build=build,
            metric="dps",
            unallocated_points=budget,
            respec_points=None,
            max_iterations=200,
            max_time_seconds=max_time,
            convergence_patience=5
        )

        start_time = time.time()
        opt_result = optimize_build(config)
        elapsed = time.time() - start_time

        result["status"] = "success"
        result["baseline_dps"] = opt_result.baseline_stats.total_dps
        result["optimized_dps"] = opt_result.optimized_stats.total_dps
        result["baseline_life"] = opt_result.baseline_stats.life
        result["optimized_life"] = opt_result.optimized_stats.life
        result["baseline_mana"] = opt_result.baseline_stats.mana
        result["optimized_mana"] = opt_result.optimized_stats.mana
        result["improvement_pct"] = opt_result.improvement_pct
        result["life_change"] = opt_result.optimized_stats.life - opt_result.baseline_stats.life
        result["mana_change"] = opt_result.optimized_stats.mana - opt_result.baseline_stats.mana
        result["time_seconds"] = elapsed
        result["iterations"] = opt_result.iterations_run
        result["nodes_added"] = len(opt_result.nodes_added)
        result["unallocated_used"] = opt_result.unallocated_used
        result["respec_used"] = opt_result.respec_used
        result["convergence_reason"] = opt_result.convergence_reason

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    # Write to a file, NOT stdout: the embedded Lua engine prints to C-level
    # stdout, which interleaves unpredictably with Python's buffered stream and
    # corrupts any JSON printed here (observed: JSON spliced mid-line into a
    # [MinimalCalc] DEBUG print).
    result_path.write_text(json.dumps(result), encoding="utf-8")
'''


def run_build_isolated(xml_path: Path) -> dict:
    """Run optimization on a single build in isolated subprocess."""
    print(f"\n{'='*60}")
    print(f"Build: {xml_path.stem}")

    # Write worker script to temp file
    worker_file = Path("_worker_epic2.py")
    worker_file.write_text(WORKER_SCRIPT)
    result_file = Path(f"_worker_epic2_result_{xml_path.stem}.json")

    try:
        # Run in subprocess with timeout
        proc = subprocess.run(
            [sys.executable, str(worker_file), str(xml_path), str(OPTIMIZATION_BUDGET), str(MAX_TIME_SECONDS), str(result_file)],
            capture_output=True,
            text=True,
            timeout=MAX_TIME_SECONDS + 60  # Add buffer for overhead
        )

        if proc.returncode != 0:
            print(f"  ERROR: Process exited with code {proc.returncode}")
            print(f"  stderr: {proc.stderr[:500]}")
            return {
                "build_name": xml_path.stem,
                "status": "error",
                "error": f"Process exit code {proc.returncode}: {proc.stderr[:200]}"
            }

        # Read JSON result from the handoff file (stdout is contaminated by
        # interleaved Lua engine prints and must not be parsed).
        if not result_file.exists():
            print("  ERROR: Worker exited 0 but wrote no result file")
            print(f"  stdout tail: {proc.stdout[-300:]}")
            return {
                "build_name": xml_path.stem,
                "status": "error",
                "error": "Worker exited 0 but wrote no result file"
            }
        result = json.loads(result_file.read_text(encoding="utf-8"))

        # Reporting must never be able to discard a loaded result.
        try:
            if result["status"] == "success":
                print(f"  DPS: {result['baseline_dps']:.1f} -> {result['optimized_dps']:.1f} ({result['improvement_pct']:+.1f}%)")
                print(f"  Life: {result['baseline_life']} -> {result['optimized_life']} ({result['life_change']:+d})")
                print(f"  Time: {result['time_seconds']:.1f}s, Iterations: {result['iterations']}")
            else:
                print(f"  ERROR: {result.get('error', 'Unknown error')}")
        except Exception as print_err:
            print(f"  (report formatting error: {print_err!r})")

        return result

    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: Exceeded {MAX_TIME_SECONDS}s limit")
        return {
            "build_name": xml_path.stem,
            "status": "error",
            "error": f"Timeout after {MAX_TIME_SECONDS}s"
        }
    except Exception as e:
        print(f"  ERROR: {e}")
        return {
            "build_name": xml_path.stem,
            "status": "error",
            "error": str(e)
        }
    finally:
        # Cleanup worker script + result handoff file
        if worker_file.exists():
            worker_file.unlink()
        if result_file.exists():
            result_file.unlink()


def main():
    """Run validation on all builds."""
    # Environment guard (story 3.5.4 AC-3.5.4.3): corpus evidence produced
    # against a drifted engine is worthless — fail fast, before any corpus
    # machine time, with the same verifier the parity test guard uses.
    env = verify(PROJECT_ROOT)
    if not env.ok:
        print("ERROR: PoB environment verification failed:")
        print(env.summary())
        print("Fix: python scripts/setup_pob.py")
        return 2

    if not CORPUS_DIR.exists():
        print(f"ERROR: Corpus directory not found: {CORPUS_DIR}")
        return 1

    xml_files = sorted(CORPUS_DIR.glob("*.xml"))

    if not xml_files:
        print(f"ERROR: No XML files found in {CORPUS_DIR}")
        return 1

    print("="*60)
    print("EPIC 2 VALIDATION - Full Subprocess Isolation")
    print("="*60)
    print(f"Corpus: {CORPUS_DIR}")
    print(f"Builds: {len(xml_files)}")
    print(f"Budget: {OPTIMIZATION_BUDGET} points per build")
    print(f"Max time: {MAX_TIME_SECONDS}s per build")

    # Run each build in isolated subprocess
    results = []
    for i, xml_path in enumerate(xml_files, 1):
        print(f"\n[{i}/{len(xml_files)}]", end=" ")
        result = run_build_isolated(xml_path)
        results.append(result)

    # Analyze results
    successful = [r for r in results if r["status"] == "success"]
    errors = [r for r in results if r["status"] == "error"]

    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Total: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Errors: {len(errors)}")

    if successful:
        improvements = [r["improvement_pct"] for r in successful]
        times = [r["time_seconds"] for r in successful]
        nodes_added = [r["nodes_added"] for r in successful]
        dps_improvements = [r for r in successful if r["improvement_pct"] > 0]
        life_improvements = [r for r in successful if r["life_change"] > 0]

        success_rate = len(dps_improvements) / len(successful) * 100
        median_improvement = median(improvements)
        max_time = max(times)
        budget_violations = len([r for r in successful if r["unallocated_used"] > OPTIMIZATION_BUDGET])

        print(f"\nSuccess Rate: {success_rate:.1f}% ({len(dps_improvements)}/{len(successful)})")
        print(f"Median Improvement: {median_improvement:.2f}%")
        print(f"Max Time: {max_time:.1f}s")
        print(f"Budget Violations: {budget_violations}")
        print(f"Life Improvements: {len(life_improvements)} builds")
        print(f"Total Nodes Allocated: {sum(nodes_added)}")

        print("\n" + "="*60)
        print("TASK 6 ACCEPTANCE CRITERIA")
        print("="*60)

        ac1 = success_rate >= 70
        ac2 = median_improvement >= 5
        ac3 = max_time < 300
        ac4 = budget_violations == 0

        print(f"{'✅' if ac1 else '❌'} Success rate >= 70%: {success_rate:.1f}%")
        print(f"{'✅' if ac2 else '❌'} Median improvement >= 5%: {median_improvement:.2f}%")
        print(f"{'✅' if ac3 else '❌'} All completions < 5 minutes: {max_time:.1f}s")
        print(f"{'✅' if ac4 else '❌'} Zero budget violations: {budget_violations}")

        overall_pass = all([ac1, ac2, ac3, ac4])
        print("\n" + "="*60)
        if overall_pass:
            print("✅ EPIC 2 VALIDATION: PASSED")
        else:
            print("❌ EPIC 2 VALIDATION: FAILED")
        print("="*60)

    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = RESULTS_DIR / "realistic-validation-results.json"

    output_data = {
        "timestamp": datetime.now().isoformat(),
        "corpus": str(CORPUS_DIR),
        "optimization_budget": OPTIMIZATION_BUDGET,
        "max_time_seconds": MAX_TIME_SECONDS,
        "summary": {
            "total_builds": len(results),
            "successful": len(successful),
            "errors": len(errors),
            "success_rate_pct": success_rate if successful else 0,
            "median_improvement_pct": median_improvement if successful else 0,
            "max_time_seconds": max_time if successful else 0,
            "budget_violations": budget_violations if successful else 0,
        },
        "results": results
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return 0 if (successful and overall_pass) else 1


if __name__ == "__main__":
    sys.exit(main())
