"""Fast/unmarked WorkerPool mechanics tests (Story 4.2 AC-4.2.3/4/5, T8).

NO LuaJIT: the pool is driven by fake in-process workers that duck-type the
DriverWorker surface the pool touches (start/restart/is_alive/ping/load_build/
get_stats/memory_mb/_stderr_tail/kill/shutdown). This carries lazy spawn, the
health-check + respawn-before-handout, one-retry-then-CalculationError, the
never-a-sentinel contract, the bounded respawn budget, ProtocolError no-retry,
cancel_inflight, and the PEBO_WORKER_POOL_SIZE override -- everything that does
NOT require the real engine to boot.

Deliberately UNMARKED so it does NOT inherit the pob_env autouse guard and never
touches a drifted engine (AC-4.2.13).
"""

import pytest

from src.calculator.driver_worker import WorkerCrash, ProtocolError
from src.calculator.exceptions import CalculationError
from src.calculator.worker_pool import WorkerPool


# --------------------------------------------------------------------------- #
# Fake workers (duck-typed DriverWorker surface the pool uses).
# --------------------------------------------------------------------------- #
class FakeWorker:
    """A healthy worker that loads + returns fixed stats."""

    STATS = {"TotalDPS": 123.0, "Life": 100}

    def __init__(self):
        self.started = 0
        self.alive = False
        self.killed = False

    def start(self):
        self.started += 1
        self.alive = True
        return {"ok": True, "ready": True}

    def restart(self):
        self.alive = False
        return self.start()

    def stop(self):
        self.alive = False

    def shutdown(self):
        self.alive = False

    def is_alive(self):
        return self.alive

    def ping(self):
        if not self.alive:
            raise WorkerCrash("dead")
        return {"ok": True, "pong": True}

    def load_build(self, xml, name="x"):
        return {"ok": True, "cmd": "LOAD_BUILD", "nodes": 1}

    def get_stats(self, stats=None):
        return dict(self.STATS)

    def memory_mb(self):
        return 200.0

    def _stderr_tail(self, n=4000):
        return "fake-stderr-tail"

    def kill(self):
        self.killed = True
        self.alive = False


class CrashOnceWorker(FakeWorker):
    """Crashes on the FIRST get_stats, succeeds after a respawn."""

    def __init__(self):
        super().__init__()
        self.calls = 0

    def get_stats(self, stats=None):
        self.calls += 1
        if self.calls == 1:
            self.alive = False
            raise WorkerCrash("first-calc crash", stderr_tail="boom")
        return {"TotalDPS": 456.0}


class AlwaysCrashWorker(FakeWorker):
    """Every calc crashes -> pool must raise CalculationError, never a sentinel."""

    def get_stats(self, stats=None):
        self.alive = False
        raise WorkerCrash("always crashes", stderr_tail="dead")


class ProtocolErrWorker(FakeWorker):
    """A LIVE worker that returns a deterministic {ok:false} (ProtocolError)."""

    def __init__(self):
        super().__init__()
        self.calls = 0

    def get_stats(self, stats=None):
        self.calls += 1
        raise ProtocolError("GET_STATS failed: mainOutput unavailable")


class BootCrashWorker(FakeWorker):
    """Never comes alive; load_build always crashes -> drives the respawn budget."""

    def start(self):
        self.started += 1
        self.alive = False
        return {"ok": False}

    def restart(self):
        return self.start()

    def is_alive(self):
        return False

    def ping(self):
        raise WorkerCrash("dead on boot")

    def load_build(self, xml, name="x"):
        raise WorkerCrash("cannot load: worker dead", stderr_tail="boot-seh")

    def _stderr_tail(self, n=4000):
        return "boot-seh-captured"


def make_factory(cls=FakeWorker):
    created = []

    def factory():
        w = cls()
        created.append(w)
        return w

    factory.created = created
    return factory


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def test_lazy_spawn_no_workers_until_acquire():
    f = make_factory()
    pool = WorkerPool(size=2, worker_factory=f)
    assert f.created == []  # nothing booted yet
    with pool.acquire() as w:
        assert w.is_alive()
    assert len(f.created) == 2  # spawned on first acquire


def test_acquire_returns_healthy_and_releases():
    f = make_factory()
    pool = WorkerPool(size=2, worker_factory=f)
    with pool.acquire() as w1:
        assert w1.is_alive()
    # released -> reusable
    with pool.acquire() as w2:
        assert w2.is_alive()


def test_health_check_respawns_dead_worker_before_handout():
    f = make_factory()
    pool = WorkerPool(size=1, worker_factory=f)
    with pool.acquire() as w:
        pass
    # Simulate the worker dying while idle.
    w.alive = False
    with pool.acquire() as w2:
        assert w2 is w
        assert w2.is_alive()          # respawned before handout
        assert w2.started == 2        # initial start + one restart


def test_calculate_happy_path_returns_stats_dict():
    pool = WorkerPool(size=1, worker_factory=make_factory())
    stats = pool.calculate("<xml/>", name="t")
    assert stats == FakeWorker.STATS


def test_calculate_one_retry_then_success_on_mid_calc_crash():
    inst = CrashOnceWorker()
    pool = WorkerPool(size=1, worker_factory=lambda: inst)
    stats = pool.calculate("<xml/>")
    assert stats == {"TotalDPS": 456.0}   # succeeded on the retry
    assert inst.calls == 2                 # crashed once, retried once
    assert inst.started == 2               # respawned between attempts


def test_calculate_persistent_crash_raises_calc_error_never_sentinel():
    pool = WorkerPool(size=1, worker_factory=make_factory(AlwaysCrashWorker))
    with pytest.raises(CalculationError) as ei:
        pool.calculate("<xml/>")
    # never a zero/sentinel BuildStats -- an exception, carrying the stderr tail.
    assert "crashed on both attempts" in str(ei.value)
    assert "dead" in str(ei.value)  # stderr_tail surfaced


def test_calculate_protocol_error_is_not_retried():
    inst = ProtocolErrWorker()
    pool = WorkerPool(size=1, worker_factory=lambda: inst)
    with pytest.raises(CalculationError) as ei:
        pool.calculate("<xml/>")
    assert "protocol error" in str(ei.value).lower()
    assert inst.calls == 1  # a live worker's {ok:false} is deterministic -> no retry


def test_respawn_budget_bounded_fails_with_stderr_tail():
    pool = WorkerPool(size=1, worker_factory=make_factory(BootCrashWorker))
    budget_err = None
    for _ in range(6):  # each calculate burns ~2 respawns; budget is 5/60s
        with pytest.raises(CalculationError) as ei:
            pool.calculate("<xml/>")
        if "respawn budget exceeded" in str(ei.value):
            budget_err = str(ei.value)
            break
    assert budget_err is not None, "respawn budget should eventually trip"
    assert "boot-seh-captured" in budget_err  # the dead worker's captured stderr tail


def test_cancel_inflight_kills_checked_out_worker():
    pool = WorkerPool(size=2, worker_factory=make_factory())
    with pool.acquire() as w:
        killed = pool.cancel_inflight()
        assert killed == 1
        assert w.killed is True
    # nothing in flight after release -> no-op
    assert pool.cancel_inflight() == 0


def test_pool_size_env_override(monkeypatch):
    monkeypatch.setenv("PEBO_WORKER_POOL_SIZE", "4")
    pool = WorkerPool(worker_factory=make_factory())  # size=None -> read env
    assert pool.size == 4


def test_shutdown_stops_all_and_excludes_teardown_from_budget():
    f = make_factory()
    pool = WorkerPool(size=2, worker_factory=f)
    with pool.acquire():
        pass
    pool.shutdown()
    assert all(not w.is_alive() for w in f.created)
    # _shutting_down is reset so the pool can lazily re-spawn afterwards
    assert pool._shutting_down is False


def test_memory_mb_sums_workers():
    pool = WorkerPool(size=2, worker_factory=make_factory())
    with pool.acquire():
        pass
    assert pool.memory_mb() == pytest.approx(400.0)  # 2 x 200MB
