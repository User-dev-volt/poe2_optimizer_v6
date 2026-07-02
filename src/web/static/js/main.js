/* ============================================================================
   main.js — UI controller for the two-panel optimizer workspace.

   Gathers input, POSTs /optimize, streams progress over SSE (sse_client.js),
   renders the before/after readout, and exports the optimized build. Backend
   contract is unchanged:
     POST /optimize -> { session_id, status, build:{class,level,ascendancy,main_skill} }
     SSE  /progress/<id> -> progress | complete(OptimizationResult) | error
     GET  /export/<id> -> { pob_code }
   Result fields mirror OptimizationResult.to_dict():
     { improvement_pct, baseline_stats, optimized_stats,
       budget_usage:{unallocated_used, respec_used},
       node_changes:{added[], removed[], swapped}, convergence:{...} }
   All reads are defensive (missing keys render as a dash).
   ============================================================================ */
(function () {
    "use strict";

    var MAX_CODE_LEN = 100000;
    var ACCENT_KEY = "poe2opt.accent";
    var EM_DASH = String.fromCharCode(0x2014);
    var DOT = String.fromCharCode(0x00b7);
    var ELLIPSIS = String.fromCharCode(0x2026);

    // Trust tier per stat: (none) = reliable, approx = rough magnitude,
    // estimate = the calc is only a directional approximation here.
    var STAT_ROWS = [
        { key: "total_dps",             label: "Total DPS",            fmt: "num", approx: true },
        { key: "life",                  label: "Life",                 fmt: "int" },
        { key: "mana",                  label: "Mana",                 fmt: "int" },
        { key: "energy_shield",         label: "Energy Shield",        fmt: "int", estimate: true },
        { key: "effective_hp",          label: "Effective HP",         fmt: "num", estimate: true },
        { key: "resistances.fire",      label: "Fire Resistance",      fmt: "pct", estimate: true },
        { key: "resistances.cold",      label: "Cold Resistance",      fmt: "pct", estimate: true },
        { key: "resistances.lightning", label: "Lightning Resistance", fmt: "pct", estimate: true },
        { key: "evasion",               label: "Evasion",              fmt: "int", estimate: true },
        { key: "armour",                label: "Armour",               fmt: "int", estimate: true },
        { key: "movement_speed",        label: "Movement Speed",       fmt: "pct", estimate: true }
    ];

    var els = {};
    var currentSessionId = null;
    var isRunning = false;
    var selectedGoal = "dps";

    // ------------------------------------------------------------ formatting
    function num(v) {
        if (typeof v === "number") return v;
        if (v === null || v === undefined || v === "") return NaN;
        return Number(v);
    }
    function get(obj, key, fallback) {
        if (obj && obj[key] !== undefined && obj[key] !== null) return obj[key];
        return fallback;
    }
    function getStat(stats, dotted) {
        if (!stats) return undefined;
        var parts = dotted.split("."), cur = stats;
        for (var i = 0; i < parts.length; i++) {
            if (cur === null || cur === undefined) return undefined;
            cur = cur[parts[i]];
        }
        return cur;
    }
    function fmtNum(v, digits) {
        var n = num(v);
        if (!isFinite(n)) return EM_DASH;
        return n.toLocaleString(undefined, { maximumFractionDigits: digits || 0 });
    }
    function fmtSigned(v, digits) {
        var n = num(v);
        if (!isFinite(n)) return EM_DASH;
        var sign = n > 0 ? "+" : (n < 0 ? "-" : "");
        return sign + Math.abs(n).toLocaleString(undefined, { maximumFractionDigits: digits || 0 });
    }
    function formatValue(kind, v) {
        var n = num(v);
        if (!isFinite(n)) return EM_DASH;
        if (kind === "pct") return fmtNum(n, 1) + "%";
        return fmtNum(n, 0);
    }
    function formatDelta(kind, d) {
        if (d === null || !isFinite(d)) return EM_DASH;
        if (kind === "pct") return fmtSigned(d, 1) + "%";
        return fmtSigned(d, 0);
    }
    function parseIntOr(raw, fallback) {
        if (raw === null || raw === undefined) return fallback;
        var s = String(raw).trim();
        if (s === "") return fallback;
        var n = parseInt(s, 10);
        return isNaN(n) ? fallback : n;
    }
    function prettyClass(s) {
        if (!s) return null;
        return String(s).split(/[_\s]+/).map(function (w) {
            return w ? w.charAt(0).toUpperCase() + w.slice(1).toLowerCase() : w;
        }).join(" ");
    }
    function humanizeErrorType(type) {
        var known = {
            unsupported_build_type: "Build Type Not Supported (Yet!)",
            optimizer_busy: "Optimizer Busy",
            connection_error: "Connection Lost",
            request_failed: "Request Failed",
            missing_input: "Nothing to Optimize",
            too_long: "Build Code Too Long",
            invalid_format: "Invalid Build Code",
            unsupported_version: "Unsupported PoB Version",
            parse_error: "Could Not Read Build",
            calculation_error: "Calculation Failed"
        };
        if (known[type]) return known[type];
        return String(type).replace(/[_\-]+/g, " ").replace(/\b\w/g, function (c) { return c.toUpperCase(); });
    }

    // --------------------------------------------------------------- states
    function showState(name) {
        els.stateEmpty.classList.toggle("hidden", name !== "empty");
        els.stateMsg.classList.toggle("hidden", name !== "msg");
        els.stateRunning.classList.toggle("hidden", name !== "running");
        els.stateResults.classList.toggle("hidden", name !== "results");
    }
    function setEngine(state, text) {
        els.engineStatus.setAttribute("data-state", state);
        els.engineText.textContent = text;
    }
    function setRunning(running) {
        isRunning = running;
        els.optimizeBtn.disabled = running;
        els.optimizeBtn.textContent = running ? "Optimizing" + ELLIPSIS : "Optimize";
        setEngine(running ? "busy" : "idle", running ? "optimizing" + ELLIPSIS : "engine ready");
    }

    function appendLog(msg, kind) {
        var line = document.createElement("div");
        line.className = "log-line" + (kind ? " log-" + kind : "");
        var t = document.createElement("span");
        t.className = "log-time";
        t.textContent = "[" + new Date().toLocaleTimeString() + "] ";
        line.appendChild(t);
        line.appendChild(document.createTextNode(msg));
        els.eventLog.appendChild(line);
        els.eventLog.scrollTop = els.eventLog.scrollHeight;
    }

    function resetRunning() {
        els.eventLog.innerHTML = "";
        els.progressBar.style.width = "0%";
        els.meter.setAttribute("aria-valuenow", "0");
        els.runImp.textContent = EM_DASH;
        els.runIter.textContent = "0 / 0";
        els.runBest.textContent = EM_DASH;
        els.runElapsed.textContent = "0.0s";
    }

    function setBuildIdentity(build) {
        if (!build) { els.buildId.classList.add("hidden"); return; }
        var cls = prettyClass(build["class"]);
        els.biClass.textContent = cls || EM_DASH;
        els.biAsc.textContent = build.ascendancy || EM_DASH;
        els.biLevel.textContent = (build.level !== null && build.level !== undefined) ? String(build.level) : EM_DASH;
        els.biSkill.textContent = build.main_skill || EM_DASH;
        els.buildId.classList.remove("hidden");
    }

    // -------------------------------------------------------------- progress
    function updateProgress(data) {
        var maxIter = num(data.max_iterations);
        if (!isFinite(maxIter) || maxIter <= 0) maxIter = 1;
        var iter = num(data.iteration);
        if (!isFinite(iter)) iter = 0;

        var pct = Math.max(0, Math.min(100, Math.round((iter / maxIter) * 100)));
        els.progressBar.style.width = pct + "%";
        els.meter.setAttribute("aria-valuenow", String(pct));

        var imp = num(data.improvement_pct);
        var best = num(data.best_metric);
        var t = num(data.time_elapsed);

        els.runImp.textContent = isFinite(imp) ? fmtSigned(imp, 1) + "%" : EM_DASH;
        els.runIter.textContent = Math.round(iter) + " / " + Math.round(maxIter);
        els.runBest.textContent = isFinite(best) ? fmtNum(best, 0) : EM_DASH;
        els.runElapsed.textContent = isFinite(t) ? t.toFixed(1) + "s" : EM_DASH;

        var budget = data.budget_used || {};
        appendLog(
            "iter " + Math.round(iter) + "/" + Math.round(maxIter) +
            "  best " + (isFinite(best) ? fmtNum(best, 0) : EM_DASH) +
            (isFinite(imp) ? "  " + fmtSigned(imp, 1) + "%" : "") +
            "  budget " + get(budget, "unallocated", "?") + " alloc / " + get(budget, "respec", "?") + " respec"
        );
    }

    // --------------------------------------------------------------- results
    function renderNodeDiff(nodes) {
        var added = (nodes.added || []).length;
        var removed = (nodes.removed || []).length;
        var swapped = get(nodes, "swapped", 0);
        els.ndAdded.textContent = String(added);
        els.ndRemoved.textContent = String(removed);
        els.ndSwapped.textContent = String(swapped);
        var total = added + removed;
        els.ndSegAdd.style.width = total > 0 ? (added / total * 100) + "%" : "0%";
        els.ndSegRem.style.width = total > 0 ? (removed / total * 100) + "%" : "0%";
    }

    function renderTable(before, after) {
        els.resultsTbody.innerHTML = "";
        STAT_ROWS.forEach(function (row) {
            var bVal = getStat(before, row.key), aVal = getStat(after, row.key);
            var bN = num(bVal), aN = num(aVal);
            var delta = (isFinite(bN) && isFinite(aN)) ? (aN - bN) : null;

            var tr = document.createElement("tr");

            var tdLabel = document.createElement("td");
            tdLabel.className = "col-stat";
            var wrap = document.createElement("div");
            wrap.className = "stat-label";
            var name = document.createElement("span");
            name.className = "stat-name";
            name.textContent = row.label;
            wrap.appendChild(name);
            if (row.approx) {
                var ap = document.createElement("span");
                ap.className = "note-approx";
                ap.textContent = "approx";
                wrap.appendChild(ap);
            }
            if (row.estimate) {
                var chip = document.createElement("span");
                chip.className = "chip chip-estimate";
                chip.textContent = "estimate";
                chip.title = "Fast in-process estimate — not PoB-accurate";
                wrap.appendChild(chip);
            }
            tdLabel.appendChild(wrap);

            var tdB = document.createElement("td");
            tdB.className = "num";
            tdB.textContent = formatValue(row.fmt, bVal);

            var tdA = document.createElement("td");
            tdA.className = "num";
            tdA.textContent = formatValue(row.fmt, aVal);

            var tdD = document.createElement("td");
            var dClass = (delta === null || delta === 0) ? "neutral" : (delta > 0 ? "pos" : "neg");
            tdD.className = "num delta " + dClass;
            tdD.textContent = formatDelta(row.fmt, delta);

            tr.appendChild(tdLabel);
            tr.appendChild(tdB);
            tr.appendChild(tdA);
            tr.appendChild(tdD);
            els.resultsTbody.appendChild(tr);
        });
    }

    function displayResults(result) {
        result = result || {};
        var before = result.baseline_stats || {};
        var after = result.optimized_stats || {};

        var imp = num(result.improvement_pct);
        els.headline.textContent = isFinite(imp) ? fmtSigned(imp, 1) + "%" : EM_DASH;
        els.headline.className = "headline-value " + (isFinite(imp) ? (imp > 0 ? "pos" : (imp < 0 ? "neg" : "")) : "");

        var budget = result.budget_usage || {};
        var nodes = result.node_changes || {};
        var conv = result.convergence || {};
        var parts = [
            "budget used: " + get(budget, "unallocated_used", 0) + " allocate / " + get(budget, "respec_used", 0) + " respec"
        ];
        if (conv && conv.iterations_run !== undefined && conv.iterations_run !== null) parts.push(conv.iterations_run + " iterations");
        if (conv && conv.reason) parts.push("stopped: " + conv.reason);
        els.resultsSummary.textContent = parts.join("  " + DOT + "  ");

        renderNodeDiff(nodes);
        renderTable(before, after);

        showState("results");
        els.exportNote.classList.add("hidden");
        els.exportBtn.disabled = false;
    }

    // ---------------------------------------------------------------- errors
    function displayError(err) {
        err = err || {};
        var type = err.error_type || "error";
        var reason = err.reason || "Something went wrong.";
        if (type === "unsupported_build_type") {
            els.stateMsg.className = "pane state-msg info";
            els.msgKind.textContent = "Not yet supported";
            els.msgTitle.textContent = "Build Type Not Supported (Yet!)";
            els.msgBody.textContent = "Coming in V2: Minion builds, Totems, traps, mines, and Trigger-based builds.";
        } else {
            els.stateMsg.className = "pane state-msg";
            els.msgKind.textContent = "Error";
            els.msgTitle.textContent = humanizeErrorType(type);
            els.msgBody.textContent = reason;
        }
        showState("msg");
        appendLog("Error: " + reason, "error");
    }

    // ------------------------------------------------------------- optimize
    function onOptimize(e) {
        if (e) e.preventDefault();
        if (isRunning) return;

        var code = els.pobCode.value.trim();
        if (!code) {
            displayError({ error_type: "missing_input", reason: "Please paste a Path of Building code first." });
            return;
        }
        if (code.length > MAX_CODE_LEN) {
            displayError({
                error_type: "too_long",
                reason: "Build code is " + code.length.toLocaleString() + " characters, exceeding the " +
                    MAX_CODE_LEN.toLocaleString() + " character limit."
            });
            return;
        }

        var unalloc = parseIntOr(els.unalloc.value, 0);
        if (unalloc < 0) unalloc = 0;
        var respecRaw = els.respec.value.trim();
        var respec = respecRaw === "" ? null : parseIntOr(respecRaw, null);
        if (respec !== null && respec < 0) respec = 0;

        setRunning(true);
        resetRunning();
        showState("running");
        appendLog("Submitting build (" + code.length.toLocaleString() + " chars, goal=" + selectedGoal + ")" + ELLIPSIS);

        fetch("/optimize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                pob_code: code, metric: selectedGoal,
                unallocated_points: unalloc, respec_points: respec
            })
        })
        .then(function (resp) {
            return resp.json().catch(function () { return {}; }).then(function (body) {
                return { ok: resp.ok, status: resp.status, body: body };
            });
        })
        .then(function (res) {
            if (!res.ok) {
                var err = (res.body && res.body.error_type) ? res.body
                    : { error_type: "request_failed", reason: "Optimization request failed (HTTP " + res.status + ")." };
                displayError(err);
                setRunning(false);
                return;
            }
            currentSessionId = res.body && res.body.session_id;
            if (!currentSessionId) {
                displayError({ error_type: "request_failed", reason: "Server did not return a session id." });
                setRunning(false);
                return;
            }
            setBuildIdentity(res.body.build);
            appendLog("Session " + currentSessionId + " accepted. Streaming progress" + ELLIPSIS, "success");
            connectSSE(currentSessionId);
        })
        .catch(function (e2) {
            displayError({ error_type: "request_failed", reason: "Could not reach the server: " + e2 });
            setRunning(false);
        });
    }

    // --------------------------------------------------------------- export
    function legacyCopy(text) {
        try {
            var ta = document.createElement("textarea");
            ta.value = text; ta.setAttribute("readonly", "");
            ta.style.position = "absolute"; ta.style.left = "-9999px";
            document.body.appendChild(ta); ta.select();
            var ok = document.execCommand("copy");
            document.body.removeChild(ta);
            if (!ok && window.console) console.log("Optimized PoB code:", text);
            return ok;
        } catch (e) {
            if (window.console) console.log("Optimized PoB code:", text);
            return false;
        }
    }
    function copyToClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text).then(function () { return true; }, function () { return legacyCopy(text); });
        }
        return Promise.resolve(legacyCopy(text));
    }
    function showExportNote(msg, ok) {
        els.exportNote.textContent = msg;
        els.exportNote.className = "export-note " + (ok ? "ok" : "err");
        els.exportNote.classList.remove("hidden");
    }
    function onExport() {
        if (!currentSessionId) return;
        els.exportNote.classList.add("hidden");
        fetch("/export/" + encodeURIComponent(currentSessionId))
        .then(function (resp) {
            return resp.json().catch(function () { return {}; }).then(function (body) {
                return { ok: resp.ok, status: resp.status, body: body };
            });
        })
        .then(function (res) {
            if (!res.ok || !res.body || !res.body.pob_code) {
                showExportNote((res.body && res.body.reason) ? res.body.reason : "Export failed (HTTP " + res.status + ").", false);
                return;
            }
            copyToClipboard(res.body.pob_code).then(function (ok) {
                showExportNote(ok ? "Copied optimized build code to clipboard." :
                    "Could not copy automatically " + EM_DASH + " code logged to the console.", ok);
            });
        })
        .catch(function (e) { showExportNote("Export failed: " + e, false); });
    }

    // ------------------------------------------------------------- controls
    function updateCharCount() {
        var len = els.pobCode.value.length;
        els.charCount.textContent = len.toLocaleString() + " / " + MAX_CODE_LEN.toLocaleString();
        var over = len > MAX_CODE_LEN;
        els.charCount.classList.toggle("over-limit", over);
        els.pobCode.classList.toggle("over-limit", over);
    }

    function applyAccent(accent) {
        var val = (accent === "gold") ? "gold" : "teal";
        document.documentElement.setAttribute("data-accent", val);
        var opts = document.querySelectorAll(".accent-opt");
        for (var i = 0; i < opts.length; i++) {
            opts[i].setAttribute("aria-pressed", String(opts[i].getAttribute("data-accent-val") === val));
        }
        try { localStorage.setItem(ACCENT_KEY, val); } catch (e) { /* ignore */ }
    }

    function wireGoal() {
        var segs = els.goalSeg.querySelectorAll(".seg");
        function select(seg) {
            selectedGoal = seg.getAttribute("data-goal");
            for (var i = 0; i < segs.length; i++) {
                var on = segs[i] === seg;
                segs[i].setAttribute("aria-checked", String(on));
                segs[i].tabIndex = on ? 0 : -1;
            }
        }
        for (var i = 0; i < segs.length; i++) {
            (function (seg) {
                seg.addEventListener("click", function () { select(seg); });
            })(segs[i]);
        }
        els.goalSeg.addEventListener("keydown", function (ev) {
            var idx = -1, list = els.goalSeg.querySelectorAll(".seg");
            for (var i = 0; i < list.length; i++) { if (list[i].getAttribute("aria-checked") === "true") { idx = i; break; } }
            if (idx < 0) return;
            var next = idx;
            if (ev.key === "ArrowRight" || ev.key === "ArrowDown") next = (idx + 1) % list.length;
            else if (ev.key === "ArrowLeft" || ev.key === "ArrowUp") next = (idx - 1 + list.length) % list.length;
            else return;
            ev.preventDefault();
            select(list[next]); list[next].focus();
        });
    }

    // ----------------------------------------------------------------- init
    function init() {
        els.pobCode = document.getElementById("pob-code");
        els.charCount = document.getElementById("char-count");
        els.clearBtn = document.getElementById("clear-btn");
        els.unalloc = document.getElementById("unallocated-points");
        els.respec = document.getElementById("respec-points");
        els.goalSeg = document.getElementById("goal-seg");
        els.optimizeForm = document.getElementById("optimize-form");
        els.optimizeBtn = document.getElementById("optimize-btn");

        els.engineStatus = document.getElementById("engine-status");
        els.engineText = document.getElementById("engine-text");

        els.buildId = document.getElementById("build-id");
        els.biClass = document.getElementById("bi-class");
        els.biAsc = document.getElementById("bi-asc");
        els.biLevel = document.getElementById("bi-level");
        els.biSkill = document.getElementById("bi-skill");

        els.stateEmpty = document.getElementById("state-empty");
        els.stateMsg = document.getElementById("state-msg");
        els.stateRunning = document.getElementById("state-running");
        els.stateResults = document.getElementById("state-results");
        els.msgKind = document.getElementById("msg-kind");
        els.msgTitle = document.getElementById("msg-title");
        els.msgBody = document.getElementById("msg-body");

        els.runImp = document.getElementById("run-imp");
        els.runIter = document.getElementById("run-iter");
        els.runBest = document.getElementById("run-best");
        els.runElapsed = document.getElementById("run-elapsed");
        els.meter = document.getElementById("meter");
        els.progressBar = document.getElementById("progress-bar");
        els.eventLog = document.getElementById("event-log");

        els.headline = document.getElementById("improvement-headline");
        els.resultsSummary = document.getElementById("results-summary");
        els.ndAdded = document.getElementById("nd-added");
        els.ndRemoved = document.getElementById("nd-removed");
        els.ndSwapped = document.getElementById("nd-swapped");
        els.ndSegAdd = document.getElementById("nd-seg-add");
        els.ndSegRem = document.getElementById("nd-seg-rem");
        els.resultsTbody = document.getElementById("results-tbody");
        els.exportBtn = document.getElementById("export-btn");
        els.exportNote = document.getElementById("export-note");

        // Accent: restore persisted choice.
        var saved = "teal";
        try { saved = localStorage.getItem(ACCENT_KEY) || "teal"; } catch (e) { /* ignore */ }
        applyAccent(saved);
        var accentOpts = document.querySelectorAll(".accent-opt");
        for (var i = 0; i < accentOpts.length; i++) {
            (function (opt) {
                opt.addEventListener("click", function () { applyAccent(opt.getAttribute("data-accent-val")); });
            })(accentOpts[i]);
        }

        wireGoal();

        // SSE hooks.
        sseClient.onProgress = updateProgress;
        sseClient.onComplete = function (data) {
            els.progressBar.style.width = "100%";
            els.meter.setAttribute("aria-valuenow", "100");
            appendLog("Optimization complete.", "success");
            displayResults(data);
            setRunning(false);
        };
        sseClient.onError = function (err) { displayError(err); setRunning(false); };

        // Events.
        els.optimizeForm.addEventListener("submit", onOptimize);
        els.exportBtn.addEventListener("click", onExport);
        els.clearBtn.addEventListener("click", function () {
            els.pobCode.value = "";
            updateCharCount();
            els.buildId.classList.add("hidden");
            showState("empty");
            els.pobCode.focus();
        });
        els.pobCode.addEventListener("input", updateCharCount);

        updateCharCount();
    }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
})();
