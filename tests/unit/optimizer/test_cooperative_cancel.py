"""Fast/unmarked cooperative-cancel tests (Story 4.2 AC-4.2.9, T8).

NO LuaJIT: calculate_build_stats is monkeypatched, and the sample build carries
NO skills so resolve_main_socket_group short-circuits (n<2) and never runs the
real engine. Covers: the cancel_check config field (present, unvalidated), the
top-of-loop terminal (reason="cancelled", best-so-far), and the per-neighbor
early-break in _evaluate_neighbors.
"""

from unittest.mock import patch

import pytest

from src.models.build_data import BuildData, CharacterClass
from src.models.build_stats import BuildStats
from src.models.optimization_config import OptimizationConfiguration
from src.optimizer.hill_climbing import optimize_build, _evaluate_neighbors


def _stats(dps=1000.0):
    return BuildStats(
        total_dps=dps, effective_hp=5000.0, life=2000, energy_shield=1000, mana=800,
        resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0},
    )


@pytest.fixture
def build():
    return BuildData(character_class=CharacterClass.WITCH, level=50, passive_nodes={1, 2, 3})


def test_cancel_check_field_defaults_none_and_is_unvalidated(build):
    cfg = OptimizationConfiguration(build=build, metric="dps", unallocated_points=10)
    assert cfg.cancel_check is None
    # A bare callable is accepted without any __post_init__ validation.
    cfg2 = OptimizationConfiguration(
        build=build, metric="dps", unallocated_points=10, cancel_check=lambda: False
    )
    assert callable(cfg2.cancel_check)


@patch("src.optimizer.hill_climbing.calculate_build_stats")
def test_cancel_immediately_returns_cancelled_best_so_far(mock_calc, build):
    mock_calc.return_value = _stats()
    cfg = OptimizationConfiguration(
        build=build, metric="dps", unallocated_points=10, cancel_check=lambda: True
    )
    result = optimize_build(cfg)
    assert result.convergence_reason == "cancelled"
    assert result.iterations_run == 0
    assert result.optimized_build == build  # best-so-far is the baseline


@patch("src.optimizer.hill_climbing.calculate_build_stats")
def test_no_cancel_runs_normally(mock_calc, build):
    mock_calc.return_value = _stats()
    cfg = OptimizationConfiguration(
        build=build, metric="dps", unallocated_points=10, max_iterations=3,
        cancel_check=lambda: False,
    )
    result = optimize_build(cfg)
    assert result.convergence_reason != "cancelled"


def test_evaluate_neighbors_breaks_sweep_early_on_cancel():
    neighbors = [
        BuildData(character_class=CharacterClass.WITCH, level=50, passive_nodes={1, 2, 3, i})
        for i in range(4, 10)
    ]
    calls = {"n": 0}

    def cancel():
        return calls["n"] >= 2  # allow exactly 2 evaluations, then cancel

    def calc_side(neighbor, **kwargs):
        calls["n"] += 1
        return _stats()

    with patch("src.optimizer.hill_climbing.calculate_build_stats", side_effect=calc_side):
        evals = _evaluate_neighbors(neighbors, "dps", _stats(), cancel_check=cancel)

    assert len(evals) == 2  # broke early instead of evaluating all 6


def test_evaluate_neighbors_none_cancel_evaluates_all():
    neighbors = [
        BuildData(character_class=CharacterClass.WITCH, level=50, passive_nodes={1, 2, 3, i})
        for i in range(4, 8)
    ]
    with patch("src.optimizer.hill_climbing.calculate_build_stats", return_value=_stats()):
        evals = _evaluate_neighbors(neighbors, "dps", _stats(), cancel_check=None)
    assert len(evals) == 4  # no cancel -> full sweep
