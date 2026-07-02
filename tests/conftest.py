"""Root test conftest: the PoB environment guard (story 3.5.4).

Parity evidence must never again be produced against a drifted engine.
An autouse fixture verifies the five environment invariants
(src/pob_env.verify: real submodule, HEAD == gitlink, generated
POB_VERSION.txt matching the pin, baseline metadata match-or-stale-flag,
every patch applied) before any test marked ``parity`` or ``gui_parity``
runs, and FAILS them on violation — errored-at-setup, never skipped, never
silently green. Fix: ``python scripts/setup_pob.py``.

Unmarked tests are unaffected: the guard is a cheap no-op for them (no
subprocess is ever spawned), so plain ``pytest tests/unit/`` gains no new
failure mode. Verification runs at most once per session (per xdist
worker), lazily, triggered by the first marked test; the cached result is
reused by every other marked test.

``POB_ENV_GUARD_ROOT`` (env var) overrides the repo root that verify()
inspects. It exists solely so the guard's own tests can point the REAL
guard at fabricated environment doubles (tests/unit/test_pob_env.py) —
never set it otherwise.
"""

import os
from pathlib import Path

import pytest

from src.pob_env import verify

_GUARDED_MARKERS = ("parity", "gui_parity")
_REPO_ROOT = Path(__file__).resolve().parents[1]
_cached_results: dict[str, object] = {}  # keyed by verified root


def _guard_root() -> Path:
    override = os.environ.get("POB_ENV_GUARD_ROOT")
    return Path(override) if override else _REPO_ROOT


@pytest.fixture(autouse=True)
def pob_env_guard(request):
    """FAIL (never skip) parity/gui_parity tests on a bad PoB environment."""
    if not any(
        request.node.get_closest_marker(m) is not None for m in _GUARDED_MARKERS
    ):
        return  # strict no-op for unmarked tests: no subprocess cost

    root = _guard_root()
    key = str(root)
    if key not in _cached_results:
        _cached_results[key] = verify(root)
    result = _cached_results[key]

    if not result.ok:
        overridden = (
            f"\n(POB_ENV_GUARD_ROOT override active — verified root: {root})"
            if os.environ.get("POB_ENV_GUARD_ROOT")
            else ""
        )
        pytest.fail(
            "PoB environment verification FAILED — refusing to run "
            "parity/corpus tests against a drifted engine.\n"
            + result.summary()
            + "\nFix: python scripts/setup_pob.py"
            + overridden,
            pytrace=False,
        )
