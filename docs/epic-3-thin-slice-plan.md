# Epic 3 Thin-Slice Implementation Plan — Localhost Flask Web UI

This plan delivers the end-to-end happy path only: paste PoB code → set budget + metric → run → watch live progress → see before/after → export optimized code. It is wired against the **verified-real** Epic 2 API (not the architecture doc's broken samples) and reuses the working `prototypes/flask_sse_demo/` plumbing.

---

## 1. Scope

**In the thin slice (Stories 3.1–3.7, the MVP happy path):**

| Story | What it delivers | Why in-slice |
|---|---|---|
| 3.1 Flask server | `python main.py` → `127.0.0.1:5000`, single page | Foundation — nothing runs without it |
| 3.2 PoB input + validation | Textarea, char count, client Base64 check, server-side parse | Entry point of the path |
| 3.3 Budget inputs | Unallocated + respec fields → `OptimizationConfiguration` | Directly feeds the optimizer config |
| 3.4 Metric dropdown | `dps`/`ehp`/`balanced` → config.metric | One required config field |
| 3.5 Live progress (SSE) | Worker thread + per-session queue + EventSource | Core UX; de-risked by the prototype |
| 3.6 Before/after results | Render `OptimizationResult.to_dict()` | The payoff of the run |
| 3.7 Export optimized code | round-trip-and-patch encoder | Closes the loop; needs new Epic 1 code |

**Deferred (pure hardening — explicitly out):**

- **3.8 Structured errors** — defer the polished 4-field error template/icon UI. *Fold in cheaply:* a minimal try/except boundary that maps `InvalidFormatError`/`UnsupportedVersionError`/`PoBParseError` → 400 and `CalculationError`/`CalculationTimeout` → 500, plus an `error` SSE event. This is ~30 min and prevents bad pastes surfacing as 500s, so it ships, but the full structured `OptimizerError` hierarchy does not.
- **3.9 5-min timeout** — *free.* `max_time_seconds=300` is already enforced by Epic 2 at `hill_climbing.py:170`. We pass it through; no Flask watchdog. Partial-result-on-timeout works because `optimize_build` returns normally with `convergence_reason='timeout'`.
- **3.10 Resource cleanup** — defer. The doc's `cleanup_lua_runtime()` targets a nonexistent `_lua_runtime` global and is a no-op against the real thread-local engines. Not needed for a single happy-path demo. *Cheap fold-in:* `del result; gc.collect()` in the worker `finally`.
- **3.11 File logging** — defer the RotatingFileHandler. *Cheap fold-in:* basic `logging.basicConfig(level=INFO)` to stderr so the dev console shows tracebacks.
- **3.12 Perf tuning** — defer entirely. NFR "1000 calc/s" conflicts with Story 2.9 subprocess routing for spell/DOT builds; not a thin-slice concern.

Also deferred from the doc but **not** a story: `POST /cancel` and the Cancel button. There is no cooperative-cancel hook in `optimize_build`, so real cancellation requires an Epic 2 change. The thin slice relies on the 5-min cap instead. (Keep the prototype's Cancel button wired to a `running` flag only if free; otherwise omit to avoid implying a guarantee we can't keep.)

---

## 2. File tree

```
poe2_optimizer_v6/
├── main.py                         # NEW: from src.web.app import create_app; app.run(...)
├── config.yaml                     # NEW: optimization.timeout_seconds=300, max_iterations=600, app.port=5000
├── requirements.txt                # +Flask==3.0.0  (+PyYAML>=6.0 if config.yaml used)
└── src/
    ├── parsers/
    │   └── pob_parser.py           # EDIT: add encode_pob_code() (round-trip-and-patch, story 3.7)
    └── web/                        # NEW package (greenfield)
        ├── __init__.py
        ├── app.py                  # create_app() app factory + register routes + globals
        ├── routes.py               # register_routes(app): /, /optimize, /progress, /result, /export
        ├── sse_manager.py          # SSEManager: {session_id -> queue.Queue(maxsize=100)}
        ├── session_manager.py      # SessionManager + OptimizationSession dataclass (in-memory dict)
        ├── optimization_runner.py  # run_optimization(session_id) worker + make_progress_callback()
        ├── templates/
        │   └── index.html          # lift prototypes/flask_sse_demo/templates/index.html
        └── static/
            ├── css/styles.css
            └── js/
                ├── main.js         # form submit, displayResults(), displayError()
                └── sse_client.js   # connectSSE() — lift from prototype
```

**requirements.txt additions:** `Flask==3.0.0`. (Skip Flask-Cors — same-origin localhost, no CORS needed. Skip psutil — that's 3.10. PyYAML only if we use `config.yaml`; for the thin slice a hardcoded `config.py` dict is simpler and one fewer dep.)

**Note the path corrections vs the architecture doc:** package is `src/parsers/` (plural), calculator is `src/calculator/build_calculator.py`. Do not copy the doc's `src/parser/` / `calculator.py` imports verbatim.

---

## 3. Backend design (wired to the REAL Epic 2 API)

Single global module-level instances in `app.py`: `session_manager = SessionManager()`, `sse_manager = SSEManager()`, and one `optimization_lock = threading.Lock()`.

### `GET /`
→ `render_template('index.html')`. No logic.

### `POST /optimize`
Request JSON:
```json
{ "pob_code": "<base64>", "metric": "dps", "unallocated_points": 15, "respec_points": null }
```
Handler (does **not** block):
```python
def optimize():
    body = request.get_json()
    code = body["pob_code"]
    if len(code) > 100_000:
        return jsonify({"error_type":"validation","reason":"Code too large"}), 400
    try:
        build = parse_pob_code(code)               # src/parsers/pob_parser.py:25
    except (InvalidFormatError, UnsupportedVersionError, PoBParseError) as e:
        return jsonify({"error_type": type(e).__name__, "reason": str(e)}), 400

    config = OptimizationConfiguration(            # src/models/optimization_config.py:9
        build=build,                               # <-- parsed BuildData goes in config.build (1st field)
        metric=body["metric"],                     # 'dps' | 'ehp' | 'balanced'
        unallocated_points=int(body["unallocated_points"]),
        respec_points=(None if body.get("respec_points") in (None,"") else int(body["respec_points"])),
        max_iterations=600,
        max_time_seconds=300,                      # Story 3.9 delegated to Epic 2
    )                                              # __post_init__ raises ValueError on bad params -> catch -> 400

    session_id = session_manager.create(config)   # stores config + status='pending'
    sse_manager.create_stream(session_id)         # CREATE QUEUE NOW, before worker starts (race fix)
    threading.Thread(target=run_optimization, args=(session_id,), daemon=True).start()
    return jsonify({"session_id": session_id, "status": "pending"}), 200
```
**Critical correction vs the doc:** the parsed `BuildData` reaches the optimizer **only** through `OptimizationConfiguration.build` (the first required field). There is no separate `build` arg to `optimize_build`, and config is a **dataclass, not a dict**. The doc's dict-config sample crashes.

**Race fix:** `create_stream` is called in the request thread *before* spawning the worker, so the queue always exists when the worker's first `send_progress` fires. (The doc/prototype create the queue lazily on SSE connect, which drops early events.)

**BuildData mutation:** `optimize_build` calls `resolve_main_socket_group(config.build)` for dps/balanced and mutates it in place. Each request re-parses a fresh `BuildData`, so this is safe — never cache/reuse a parsed build across requests.

### `GET /progress/<session_id>`
SSE `text/event-stream`. Generator drains the per-session queue (see §4). Events: `progress`, `complete`, `error`.

### `GET /result/<session_id>`
Polling fallback (also the authoritative result fetch):
```json
{ "status": "completed", "result": { ...OptimizationResult.to_dict()... }, "error": null }
```
Returns `session.result` (the dict produced by `to_dict()`), `session.status`, `session.error`.

### `GET /export/<session_id>`
```python
def export_code(session_id):
    s = session_manager.get(session_id)
    code = encode_pob_code(s.original_code, s.optimized_nodes)   # see §5
    return jsonify({"pob_code": code, "status": "ok"})
```
We stash `original_code` (the raw pasted string) and `optimized_nodes` (`sorted(result.optimized_build.passive_nodes)`) on the session at completion — **not** the serialized `to_dict()`, which drops `optimized_build`.

### Worker `run_optimization(session_id)` (in `optimization_runner.py`)
```python
def run_optimization(session_id):
    s = session_manager.get(session_id)
    config = s.config
    config.progress_callback = make_progress_callback(session_id, config.metric)
    session_manager.update(session_id, status="running")
    if not optimization_lock.acquire(timeout=1.0):
        sse_manager.send(session_id, "error", {"reason":"Optimizer busy"})
        return
    try:
        result = optimize_build(config)            # src/optimizer/hill_climbing.py:46 (BLOCKS up to 300s)
        payload = result.to_dict()                 # optimization_config.py:227 (no optimized_build inside)
        session_manager.update(
            session_id, status="completed",
            result=payload,
            optimized_nodes=sorted(result.optimized_build.passive_nodes),
        )
        sse_manager.send(session_id, "complete", payload)
    except (CalculationError, CalculationTimeout, ValueError) as e:
        session_manager.update(session_id, status="failed", error=str(e))
        sse_manager.send(session_id, "error", {"error_type": type(e).__name__, "reason": str(e)})
    finally:
        optimization_lock.release()
```
`original_code` was stored on the session at `create()` time so export can re-decode it.

---

## 4. Concurrency & SSE

**Threading model (respects LuaJIT thread-local constraint):**

- `optimize_build` internally calls `calculate_build_stats()` for baseline + every neighbor. That function lazily builds **one LuaJIT engine per thread** via `threading.local()` (`build_calculator.py:45`). Engines must never cross threads.
- Therefore each `POST /optimize` spawns **one daemon worker thread** that owns its own thread-local engine for the entire run. The HTTP request thread never touches Lua. This satisfies the "one calculator per thread, never shared" rule.
- A single global `optimization_lock` serializes runs so we never have two LuaJIT-using worker threads alive at once (single-user MVP — sequential is the design). `acquire(timeout=1.0)` rejects a second concurrent run rather than queueing.
- **Spawn-per-request trade-off:** Windows LuaJIT teardown can emit SEH `0xe24c4a02` (ADR-003). For a single-user demo with one run at a time this is acceptable noise on shutdown. We do **not** churn threads concurrently. (A long-lived dedicated worker + job queue is the more robust pattern if churn becomes a problem — noted in §7, not built in the thin slice.)
- **`debug=True` reloader hazard:** the Werkzeug reloader double-imports and can restart mid-run, orphaning the worker + held lock. **Run the thin slice with `debug=False, threaded=True`** (still need `threaded=True` so the SSE GET and the worker coexist). Lose auto-reload; gain stability.

**SSE bridge (lift from `prototypes/flask_sse_demo/app.py:106-153`, verified working):**

`SSEManager` holds `{session_id -> queue.Queue(maxsize=100)}` guarded by a lock.
- `create_stream(session_id)` → makes the queue (called in request thread before worker spawn).
- `send(session_id, event_type, data)` → `put_nowait`. **Terminal-event guarantee:** for `complete`/`error`, drain one item first if `Full` so the terminal event is never the one dropped (fixes the bounded-queue-drops-terminal risk).
- Generator:
```python
def event_stream():
    q = sse_manager.get_queue(session_id)
    try:
        while True:
            try:
                msg = q.get(timeout=1.0)
            except queue.Empty:
                yield ": keepalive\n\n"; continue
            yield f"event: {msg['event']}\n"
            yield f"data: {json.dumps(msg['data'])}\n\n"
            if msg["event"] in ("complete", "error"):
                break
    finally:
        sse_manager.close_stream(session_id)
return Response(stream_with_context(event_stream()), mimetype="text/event-stream",
                headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})
```
**Import fix:** the doc's `routes.py` forgets `import queue` and `import json` → `NameError` on first keepalive. Include both.

**Bridging the progress callback into SSE events — the key correction:**

The task brief and the dataclass type hint both say the callback is `(int, float, str)`. **That annotation is stale.** The real call site (`src/optimizer/progress.py:114-121`) invokes it with **five keyword args**. A 3-positional callback raises `TypeError`. So:

```python
def make_progress_callback(session_id, metric):
    def cb(iteration, best_metric, improvement_pct, budget_used, time_elapsed):
        sse_manager.send(session_id, "progress", {
            "iteration": iteration,
            "max_iterations": 600,
            "best_metric": best_metric,            # raw DPS/EHP score, not a percent
            "improvement_pct": improvement_pct,    # the percent
            "budget_used": {
                "unallocated": budget_used["unallocated_used"],
                "respec": budget_used["respec_used"],
            },
            "time_elapsed": time_elapsed,
        })
    return cb
```
`budget_used` is a dict with keys `unallocated_used` / `unallocated_available` / `respec_used` / `respec_available` (verified in survey). Cadence is **coarse** — only at iteration 1 and every 100th — so a short run may emit a single `progress` event then `complete`. The progress bar (`iteration/max_iterations`) is therefore an estimate; that's acceptable.

**Client (`sse_client.js`, lifted from prototype):** `new EventSource('/progress/'+id)`, `addEventListener('progress'|'complete'|'error')`, `eventSource.close()` on terminal. `GET /result/<id>` is the fallback if the SSE connection is missed.

---

## 5. Export encoder (Story 3.7)

`encode_pob_code` **does not exist** in `src/` and must be implemented in Epic 1 (`src/parsers/pob_parser.py`). The survey empirically validated the low-risk approach: **round-trip-and-patch**, *not* rebuild-from-BuildData (which is lossy — drops `<Calcs>`, `<Config>`, item `#text`, `<Sockets>`, gem data).

**Signature (changed from the doc's `encode_pob_code(build_data)`):**
```python
def encode_pob_code(original_code: str, optimized_nodes: set[int]) -> str:
    data = parse_xml(zlib.decompress(base64.b64decode(original_code)).decode("utf-8"))
    tree = data["PathOfBuilding2"]["Tree"]
    spec = tree["Spec"]
    if isinstance(spec, list):                          # multi-spec: select active (1-based)
        spec = spec[int(tree.get("@activeSpec", "1")) - 1]
    spec["@nodes"] = ",".join(str(n) for n in sorted(optimized_nodes))
    xml_str = build_xml(data)                            # REUSE src/parsers/xml_utils.py:35 (xmltodict.unparse, pretty=False)
    return base64.b64encode(zlib.compress(xml_str.encode("utf-8"), 9)).decode("ascii")
```

Why this is safe (all survey-verified):
- PoB reads allocated nodes from `Tree>Spec@nodes`; `PassiveSpec.lua:140` uses `nodes` and **ignores the `<URL>` child** when present. So patching only `@nodes` is sufficient; the stale `<URL>` is harmless for PoB import.
- **Emit STANDARD base64**, not url-safe. This project's own `parse_pob_code` (`base64.b64decode`) rejects `-`/`_` and raises; PoB desktop accepts standard. Standard round-trips through both.
- `pretty=False` is mandatory — `pretty=True` injects whitespace into significant `#text` (item blocks, Notes).
- Test asserts **semantic** equality (re-parse the exported code → node set matches), **not** byte-identical strings (deflate params differ).

**Dependency check (open):** confirm `result.optimized_build.passive_nodes` already includes the class-start + ascendancy nodes (CLAUDE.md says BFS connectivity from start is enforced, so it should). If it only contains the mutable subset, `@nodes` would render a disconnected tree.

---

## 6. Build sequence (ordered, executable story-by-story)

| # | Step | Effort |
|---|---|---|
| 0 | Create `src/web/` package skeleton + `main.py` + add `Flask==3.0.0` to requirements; `create_app()` returns a bare app serving `GET /` → "hello". Run `python main.py`, confirm `127.0.0.1:5000`. **(Story 3.1)** | 1.5h |
| 1 | `index.html` shell: textarea + char count + client-side Base64/length validation + Clear button. Lift prototype's HTML/CSS. **(3.2 client)** | 2h |
| 2 | Budget inputs (unallocated auto-filled but editable, respec blank=unlimited) + metric `<select>` (dps default). Non-negative-int validation. **(3.3 + 3.4 client)** | 1.5h |
| 3 | `SessionManager` + `OptimizationSession` dataclass (in-memory dict + lock), `SSEManager` (queue-per-session). Lift from prototype, add `create_stream`-before-worker. | 2h |
| 4 | `POST /optimize`: parse → build `OptimizationConfiguration` → spawn worker. `optimization_runner.run_optimization` + `make_progress_callback` (5-kwarg). Global `optimization_lock`. **(3.2 server + wiring)** | 3h |
| 5 | `GET /progress/<id>` SSE generator + `sse_client.js` `connectSSE`. End-to-end: paste real fixture code, watch progress bar move. **(Story 3.5)** | 2.5h |
| 6 | `GET /result/<id>` + `displayResults()` rendering before/after from `to_dict()` (baseline_stats vs optimized_stats, improvement_pct, budget_usage, node_changes; green/red indicators). **(Story 3.6)** | 3h |
| 7 | Implement `encode_pob_code(original_code, optimized_nodes)` in `pob_parser.py` + unit test round-tripping `build_01_witch_90`. **(Story 3.7 backend)** | 2.5h |
| 8 | `GET /export/<id>` + Export button + clipboard copy + success message. **(Story 3.7 client)** | 1.5h |
| 9 | Cheap hardening fold-ins: error→400/500 mapping, `error` SSE event, `del result; gc.collect()`, `logging.basicConfig`. **(slivers of 3.8/3.10/3.11)** | 1.5h |
| 10 | Manual end-to-end smoke + 1–2 Flask test-client integration tests (`POST /optimize` happy path, export round-trip). Run with `pytest -n 1`. | 2h |

**Total ≈ 23.5h** for the thin slice.

---

## 7. Risks & landmines

| Risk | Mitigation |
|---|---|
| **Stale `progress_callback` type hint** `(int,float,str)` vs real 5 kwargs → `TypeError` at runtime. | Write `cb(iteration, best_metric, improvement_pct, budget_used, time_elapsed)`. Verified against `progress.py:114`. Do not trust the dataclass annotation. |
| **Config-as-dict crash** (doc's sample). `optimize_build` needs an `OptimizationConfiguration` dataclass; `BuildData` goes in `config.build`. | Construct the real dataclass in `/optimize` (§3). Never pass a dict. |
| **LuaJIT thread-safety** — engine is thread-local; sharing across threads corrupts state. | One daemon worker per run owns its own engine; HTTP thread never calls Lua; global lock serializes runs. Never two Lua workers concurrently. |
| **Windows LuaJIT SEH `0xe24c4a02`** on thread teardown (ADR-003). | Single sequential run at a time (no thread churn). Acceptable noise for single-user demo. Run integration tests with `pytest -n 1` (process isolation). |
| **`debug=True` reloader** double-imports + can restart mid-run, orphaning lock/worker. | Run `debug=False, threaded=True` in the thin slice. Accept losing hot-reload. |
| **SSE create-before-send race** → terminal event lost if browser connects late. | `create_stream()` in the request thread before spawning the worker; `GET /result` polling as authoritative fallback. |
| **Bounded queue drops terminal `complete`/`error`** under a slow consumer. | In `SSEManager.send`, for terminal events drain-one-then-put on `Full` so the terminal event is never dropped. |
| **Export round-trip fidelity** — rebuild-from-BuildData is lossy; url-safe base64 breaks our importer. | Round-trip-and-patch only `@nodes` on the re-decoded original dict; emit STANDARD base64; assert semantic (re-parsed node set) equality, not byte equality. |
| **`encode_pob_code` is a missing hard dependency** (doesn't exist in `src/`). | Implement it as step 7 *before* wiring `/export`. It's the validated ~4-line encoder on top of existing `build_xml`. |
| **`passive_nodes` may omit start/ascendancy** → disconnected exported tree. | Verify `optimized_build.passive_nodes` is the full allocated set (BFS-connectivity claim in CLAUDE.md); add an assertion in the export test. |
| **No cancellation / hung-iteration brick** — a stuck `calculate_build_stats` holds `optimization_lock` forever. | Out of thin-slice scope. Rely on `max_time_seconds=300` per-iteration check. Document that a single hung Lua call is unrecoverable without restart; real fix (subprocess/hard-kill or cooperative cancel hook in Epic 2) is a follow-up. |
| **ADR-004 submodule patch fragility** (Global.lua nil-safety for spell/DOT subprocess path). | Don't touch `external/`. Use existing fixtures (attack builds via MinimalCalc) for the smoke test; spell/DOT builds route through the already-patched subprocess path unchanged. |

---

## 8. Open questions for Alec

1. **Cancel button:** include a best-effort `POST /cancel` (cooperative flag, only stops at the next 100-iteration boundary — not "immediate"), or omit it from the thin slice since there's no real interrupt hook in `optimize_build`? My default: **omit**, rely on the 5-min cap.
2. **Auto-detect "Detected: 15 (level 85, 98/113 allocated)" in 3.3:** the level→passive-point + quest-point derivation is unspecified. For the thin slice, prefill from `BuildData.unallocated_points` (a verified property) and skip the descriptive readout — OK?
3. **`config.yaml` + PyYAML, or a hardcoded `src/web/config.py` dict?** Thin slice leans hardcoded (one fewer dep, no story owns the config loader). Confirm.
4. **`debug=False` for stability** (loses hot-reload) acceptable for the demo, given the reloader/daemon-thread hazard?
5. **Export node-set completeness:** can you confirm the optimizer's `passive_nodes` includes class-start + ascendancy nodes? If not, the export needs to union them in before encoding.
6. **`encode_pob_code` signature change:** OK to implement it as `encode_pob_code(original_code, optimized_nodes)` (re-decode + patch) instead of the doc's lossy `encode_pob_code(build_data)`? This avoids adding a raw-XML field to `BuildData`.

**Relevant absolute paths for execution:**
- New package: `D:\Projects\poe2_optimizer_v6\src\web\`
- Encoder edit: `D:\Projects\poe2_optimizer_v6\src\parsers\pob_parser.py`
- Reuse wholesale: `D:\Projects\poe2_optimizer_v6\prototypes\flask_sse_demo\app.py` + `templates\index.html`
- Reuse serializer: `D:\Projects\poe2_optimizer_v6\src\parsers\xml_utils.py` (`build_xml`)
- Real API: `src\parsers\pob_parser.py:25`, `src\models\optimization_config.py:9`/`:227`, `src\optimizer\hill_climbing.py:46`, `src\optimizer\progress.py:114`
- Round-trip test corpus: `D:\Projects\poe2_optimizer_v6\tests\fixtures\parity_builds\build_01_witch_90.*`