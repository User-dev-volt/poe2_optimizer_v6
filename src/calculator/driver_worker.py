"""PEBO Truth Engine -- respawnable worker-process host for driver.lua (Story 4.1 spike).

This is the Task-4 deliverable: a Python parent <-> Lua child host that boots the
REAL PoB engine (via src/calculator/driver.lua) inside a SEPARATE OS PROCESS so a
native SEH fault (0xe24c4a02) is contained -- the parent survives and reports the
crash instead of dying with the child (AC-4.1.1). It is respawnable (restart()),
speaks a line-delimited JSON protocol (LOAD_BUILD / GET_STATS / PING / GC /
EVAL_NEIGHBORS-stub / APPLY_MOVE-stub / SHUTDOWN), and measures per-process memory
(risk #9, 200-400MB per full-Data.lua worker) and latency (Task 7).

TWO LANES, ONE driver.lua (AC-4.1.4 / AC-4.1.5):
  * lane="embedded"  -> child = `python -m src.calculator.driver_worker --serve`,
                        which embeds lupa.luajit21 and dofiles driver.lua with
                        HEADLESS_EMBED=true; this Python child runs the stdin/stdout
                        JSON loop, calling Driver.handle_command via Lupa.
  * lane="luajit"    -> child = `<luajit.exe> driver.lua`; driver.lua's own
                        Driver.serve() Lua loop speaks the identical protocol.

The parent (DriverWorker) is lane-agnostic once started. NOTHING here is wired
behind build_calculator.py -- driver.lua stays standalone (AC-4.1.10).

House-script convention: stdlib + psutil only; list-args subprocess with explicit
cwd; never shell=True. Exit codes on the --serve child: 0 ok / 3 boot input error /
4 boot attestation (LuaError) -- mirrors scripts/setup_pob.py.
[Source: src/calculator/full_pob_engine.py:41-49,92-133; src/calculator/pob_engine.py:564-579;
         external/pob-engine/src/Launch.lua:45-46; CLAUDE.md thread-safety/-n1 constraints]
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import threading
import time
from typing import Any, Optional

# --------------------------------------------------------------------------- #
# Paths (repo-relative, resolved from this file's location).
# --------------------------------------------------------------------------- #
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
POB_SRC_DIR = os.path.join(_PROJECT_ROOT, "external", "pob-engine", "src")
DRIVER_LUA = os.path.join(_THIS_DIR, "driver.lua")


class WorkerCrash(RuntimeError):
    """Raised when the worker process dies (EOF/exit) -- e.g. a boot-time SEH."""

    def __init__(self, message: str, returncode: Optional[int] = None, stderr_tail: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stderr_tail = stderr_tail


# =========================================================================== #
# CHILD (--serve): embed Lupa, boot driver.lua, run the JSON stdin/stdout loop.
# =========================================================================== #
def _serve() -> int:
    """Embedded-lane worker entry point. Boots driver.lua and serves commands.

    stdout carries ONLY JSON protocol lines (one per command, plus a READY line
    after boot). All Lua boot noise is routed to stderr by driver.lua itself.
    """
    # Force UTF-8 on the protocol streams; XML payloads are UTF-8.
    sys.stdin.reconfigure(encoding="utf-8", newline="\n")
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")

    def emit(obj: dict) -> None:
        sys.stdout.write(json.dumps(obj) + "\n")
        sys.stdout.flush()

    # driver.lua reads POB_SRC_DIR from the env and requires cwd == POB_SRC_DIR.
    pob_src = os.environ.get("POB_SRC_DIR", POB_SRC_DIR)
    if not os.path.isdir(pob_src):
        emit({"ok": False, "error": f"POB_SRC_DIR not a directory: {pob_src}", "phase": "boot"})
        return 3
    os.chdir(pob_src)

    try:
        from lupa.luajit21 import LuaRuntime
        import lupa
    except Exception as e:  # pragma: no cover - env guarantees lupa
        emit({"ok": False, "error": f"cannot import lupa.luajit21: {e}", "phase": "boot"})
        return 3

    lua = LuaRuntime()
    g = lua.globals()
    g.HEADLESS_EMBED = True  # driver.lua: do NOT auto-run the serve loop

    driver_path = DRIVER_LUA.replace("\\", "/")
    boot_t0 = time.perf_counter()
    try:
        lua.execute(f'dofile("{driver_path}")')
    except lupa.LuaError as e:
        emit({"ok": False, "error": f"driver.lua boot LuaError: {e}", "phase": "boot"})
        return 4
    boot_ms = (time.perf_counter() - boot_t0) * 1000.0

    handle = g.Driver.handle_command
    emit({"ok": True, "ready": True, "lane": "embedded", "boot_ms": round(boot_ms, 1),
          "pid": os.getpid()})

    # Command loop: one JSON line in -> one JSON line out.
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line:
            continue
        try:
            resp = handle(line)  # driver.lua pcalls internally; returns a JSON string
        except lupa.LuaError as e:
            resp = json.dumps({"ok": False, "error": f"handle_command LuaError: {e}"})
        sys.stdout.write(resp + "\n")
        sys.stdout.flush()
        try:
            if json.loads(line).get("cmd") == "SHUTDOWN":
                break
        except Exception:
            pass
    return 0


# =========================================================================== #
# PARENT: DriverWorker -- spawn, drive, measure, respawn.
# =========================================================================== #
class DriverWorker:
    """Parent-side handle to a respawnable driver.lua worker process."""

    def __init__(
        self,
        lane: str = "embedded",
        luajit_exe: Optional[str] = None,
        pob_src: str = POB_SRC_DIR,
        stderr_path: Optional[str] = None,
        boot_timeout: float = 60.0,
        cmd_timeout: float = 60.0,
    ):
        if lane not in ("embedded", "luajit"):
            raise ValueError(f"lane must be 'embedded' or 'luajit', got {lane!r}")
        if lane == "luajit" and not luajit_exe:
            raise ValueError("lane='luajit' requires luajit_exe=<path to luajit.exe>")
        self.lane = lane
        self.luajit_exe = luajit_exe
        self.pob_src = pob_src
        self.stderr_path = stderr_path
        self.boot_timeout = boot_timeout
        self.cmd_timeout = cmd_timeout
        self.proc: Optional[subprocess.Popen] = None
        self._stderr_fh: Optional[io.TextIOBase] = None
        self.boot_info: dict = {}
        self.boot_wall_ms: float = 0.0

    # ----- lifecycle ----------------------------------------------------- #
    def _argv(self) -> list[str]:
        if self.lane == "embedded":
            # -u = unbuffered; run this module as the --serve child.
            return [sys.executable, "-u", os.path.abspath(__file__), "--serve"]
        return [self.luajit_exe, DRIVER_LUA.replace("\\", "/")]

    def start(self) -> dict:
        """Spawn the worker and block until it emits READY (or crashes)."""
        env = dict(os.environ)
        env["POB_SRC_DIR"] = self.pob_src
        env.pop("CI", None)  # ensure ModCache path matches the GUI-baseline capture

        if self.stderr_path:
            self._stderr_fh = open(self.stderr_path, "w", encoding="utf-8")
            stderr_dest = self._stderr_fh
        else:
            stderr_dest = subprocess.DEVNULL  # avoid pipe-fill deadlock on boot noise

        t0 = time.perf_counter()
        self.proc = subprocess.Popen(
            self._argv(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr_dest,
            cwd=self.pob_src,
            env=env,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        # Read stdout until READY. Boot noise is on stderr, so the first stdout
        # line should be the READY JSON. A dead child -> EOF -> WorkerCrash.
        ready = self._read_until_ready()
        self.boot_wall_ms = (time.perf_counter() - t0) * 1000.0
        self.boot_info = ready
        return ready

    def _readline_with_timeout(self, timeout: float, phase: str = "read") -> str:
        """Blocking stdout.readline() bounded by `timeout` seconds.

        Windows pipes support neither select() nor non-blocking reads, so the
        read runs on a throwaway daemon thread and we bound it with Thread.join.
        On timeout the wedged child is KILLED (so the reader unblocks on EOF) and
        a WorkerCrash is raised -- turning an unbounded hang (a silent boot stall,
        or a non-terminating PoB calc reached via LOAD_BUILD/GET_STATS) into a
        bounded, catchable failure. full_pob_engine's `timeout_seconds` only
        measured elapsed time AFTER the calc returned; it never interrupted one.
        Returns the line ("" on EOF).
        """
        assert self.proc and self.proc.stdout
        stdout = self.proc.stdout
        box: dict = {}

        def _reader() -> None:
            try:
                box["line"] = stdout.readline()
            except Exception as e:  # pipe torn down under us, etc.
                box["exc"] = e

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        t.join(timeout)
        if t.is_alive():
            try:
                self.proc.kill()  # unblock the reader (EOF) and bound the hang
            except Exception:
                pass
            t.join(5)
            raise WorkerCrash(
                f"worker unresponsive during {phase}: no line within "
                f"{timeout:.0f}s (killed)",
                returncode=self._returncode(),
                stderr_tail=self._stderr_tail(),
            )
        if "exc" in box:
            raise WorkerCrash(
                f"worker read failed during {phase}: {box['exc']}",
                returncode=self._returncode(),
                stderr_tail=self._stderr_tail(),
            )
        return box.get("line", "")

    def _read_until_ready(self) -> dict:
        assert self.proc and self.proc.stdout
        deadline = time.perf_counter() + self.boot_timeout
        while True:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                self.stop()
                raise WorkerCrash(f"worker boot timed out after {self.boot_timeout:.0f}s")
            # Bounded read: a child that hangs during boot without printing a line
            # or exiting no longer blocks here forever -- the original untimed
            # readline() made boot_timeout unreachable on a silent stall.
            line = self._readline_with_timeout(remaining, phase="boot")
            if line == "":  # EOF -> process exited during boot (e.g. SEH)
                rc = self.proc.wait()
                raise WorkerCrash(
                    f"worker exited during boot (rc={rc}) -- possible boot-time SEH",
                    returncode=rc,
                    stderr_tail=self._stderr_tail(),
                )
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue  # stray stdout line; ignore (shouldn't happen)
            if obj.get("ready"):
                return obj
            if obj.get("ok") is False:
                raise WorkerCrash(f"worker boot error: {obj.get('error')}",
                                  stderr_tail=self._stderr_tail())

    # ----- protocol ------------------------------------------------------ #
    def _send(self, obj: dict) -> dict:
        if not self.is_alive():
            raise WorkerCrash("worker is not alive", returncode=self._returncode())
        assert self.proc and self.proc.stdin and self.proc.stdout
        try:
            self.proc.stdin.write(json.dumps(obj) + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise WorkerCrash(f"write failed: {e}", returncode=self._returncode(),
                              stderr_tail=self._stderr_tail())
        line = self._readline_with_timeout(self.cmd_timeout, phase="command")
        if line == "":
            rc = self.proc.wait()
            raise WorkerCrash(f"worker died mid-command (rc={rc}) -- possible SEH",
                              returncode=rc, stderr_tail=self._stderr_tail())
        return json.loads(line.strip())

    def ping(self) -> dict:
        return self._send({"cmd": "PING"})

    def load_build(self, xml: str, name: str = "spike") -> dict:
        return self._send({"cmd": "LOAD_BUILD", "xml": xml, "name": name})

    def get_stats(self, stats: Optional[list[str]] = None) -> dict:
        resp = self._send({"cmd": "GET_STATS", "stats": stats})
        return resp.get("stats", {}) if resp.get("ok") else resp

    def eval_neighbors(self, payload: Optional[dict] = None) -> dict:
        return self._send({"cmd": "EVAL_NEIGHBORS", **(payload or {})})

    def apply_move(self, payload: Optional[dict] = None) -> dict:
        return self._send({"cmd": "APPLY_MOVE", **(payload or {})})

    def gc(self) -> dict:
        return self._send({"cmd": "GC"})

    def shutdown(self) -> None:
        if self.is_alive():
            try:
                self._send({"cmd": "SHUTDOWN"})
            except WorkerCrash:
                pass
        self.stop()

    # ----- health / measurement ----------------------------------------- #
    def is_alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def _returncode(self) -> Optional[int]:
        return self.proc.poll() if self.proc else None

    def memory_mb(self) -> Optional[float]:
        """Resident set size of the worker process TREE in MB (risk #9).

        Sums the spawned process and any children: a venv whose python.exe is a
        redirector stub (e.g. when the venv lives on another drive) re-execs the
        real interpreter as a grandchild, so the stub's own RSS is ~4MB while the
        actual ~200-400MB footprint is in the child. Summing the tree is correct
        for either layout.
        """
        if not self.is_alive():
            return None
        try:
            import psutil
            proc = psutil.Process(self.proc.pid)
            rss = proc.memory_info().rss
            for child in proc.children(recursive=True):
                try:
                    rss += child.memory_info().rss
                except psutil.Error:
                    pass
            return rss / (1024 * 1024)
        except Exception:
            return None

    def _stderr_tail(self, n: int = 4000) -> str:
        if not self.stderr_path or not os.path.exists(self.stderr_path):
            return ""
        try:
            with open(self.stderr_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()[-n:]
        except Exception:
            return ""

    def restart(self) -> dict:
        """Kill (if needed) and respawn the worker (AC-4.1.1 respawnable)."""
        self.stop()
        return self.start()

    def stop(self) -> None:
        if self.proc is not None:
            try:
                if self.proc.poll() is None:
                    self.proc.terminate()
                    try:
                        self.proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.proc.kill()
                        self.proc.wait(timeout=5)
            except Exception:
                pass
            for stream in (self.proc.stdin, self.proc.stdout):
                try:
                    if stream:
                        stream.close()
                except Exception:
                    pass
            self.proc = None
        if self._stderr_fh is not None:
            try:
                self._stderr_fh.close()
            except Exception:
                pass
            self._stderr_fh = None

    # ----- context manager ------------------------------------------------ #
    def __enter__(self) -> "DriverWorker":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.shutdown()


if __name__ == "__main__":
    if "--serve" in sys.argv:
        raise SystemExit(_serve())
    # Tiny smoke CLI: boot the embedded worker, ping, report boot time + memory.
    w = DriverWorker(lane="embedded")
    info = w.start()
    print(f"READY: {info}")
    print(f"PING:  {w.ping()}")
    print(f"boot_wall_ms={w.boot_wall_ms:.0f}  memory_mb={w.memory_mb()}")
    w.shutdown()
