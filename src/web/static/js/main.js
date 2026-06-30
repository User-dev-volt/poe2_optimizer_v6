/* ============================================================
   main.js
   UI controller: gather inputs, POST /optimize, stream progress over SSE,
   render the before/after results table, and export the optimized build.

   Result field names mirror OptimizationResult.to_dict():
     { improvement_pct, baseline_stats, optimized_stats,
       budget_usage:{unallocated_used, respec_used},
       node_changes:{added[], removed[], swapped},
       convergence:{reason, iterations_run, time_elapsed_seconds} }
   ...and BuildStats.to_dict() for each *_stats object:
     { total_dps, effective_hp, life, energy_shield, mana,
       resistances:{fire,cold,lightning,chaos},
       armour, evasion, block_chance, spell_block_chance, movement_speed }
   All reads are defensive (missing keys render as a dash).
   ============================================================ */

(function () {
    "use strict";

    var MAX_CODE_LEN = 100000;

    // Em dash / middle dot / ellipsis built from char codes so the source stays ASCII.
    var EM_DASH = String.fromCharCode(0x2014);
    var DOT = String.fromCharCode(0x00b7);
    var ELLIPSIS = String.fromCharCode(0x2026);

    // Which stats to show, how to format, and how to flag accuracy.
    //   approx:   soft "(approx)" note (DPS magnitude is only roughly right)
    //   estimate: amber "estimate - not PoB-accurate" badge (calc is broken here)
    var STAT_ROWS = [
        { key: "total_dps",            label: "Total DPS",           fmt: "num", approx: true },
        { key: "life",                 label: "Life",                fmt: "int" },
        { key: "mana",                 label: "Mana",                fmt: "int" },
        { key: "energy_shield",        label: "Energy Shield",       fmt: "int", estimate: true },
        { key: "effective_hp",         label: "Effective HP",        fmt: "num", estimate: true },
        { key: "resistances.fire",     label: "Fire Resistance",     fmt: "pct", estimate: true },
        { key: "resistances.cold",     label: "Cold Resistance",     fmt: "pct", estimate: true },
        { key: "resistances.lightning",label: "Lightning Resistance",fmt: "pct", estimate: true },
        { key: "evasion",              label: "Evasion",             fmt: "int", estimate: true },
        { key: "armour",               label: "Armour",              fmt: "int", estimate: true },
        { key: "movement_speed",       label: "Movement Speed",      fmt: "pct", estimate: true }
    ];

    var els = {};
    var currentSessionId = null;
    var isRunning = false;

    // ---------------------------------------------------------------- utils

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
        var parts = dotted.split(".");
        var cur = stats;
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
            parse_error: "Could Not Read Build"
        };
        if (known[type]) return known[type];
        return String(type)
            .replace(/[_\-]+/g, " ")
            .replace(/\b\w/g, function (c) { return c.toUpperCase(); });
    }

    // ----------------------------------------------------------- log / state

    function appendLog(msg, kind) {
        var line = document.createElement("div");
        line.className = "log-line" + (kind ? " log-" + kind : "");
        var time = document.createElement("span");
        time.className = "log-time";
        time.textContent = "[" + new Date().toLocaleTimeString() + "] ";
        line.appendChild(time);
        line.appendChild(document.createTextNode(msg));
        els.eventLog.appendChild(line);
        els.eventLog.scrollTop = els.eventLog.scrollHeight;
    }

    function setRunning(running) {
        isRunning = running;
        els.optimizeBtn.disabled = running;
        els.optimizeBtn.textContent = running ? "Optimizing" + ELLIPSIS : "Optimize";
    }

    function finishRun() {
        setRunning(false);
    }

    function showProgress() {
        els.progressSection.classList.remove("hidden");
    }

    function resetProgress() {
        els.eventLog.innerHTML = "";
        els.progressBar.style.width = "0%";
        els.progressBar.textContent = "0%";
        els.statusText.textContent = "Starting" + ELLIPSIS;
    }

    function hideResults() {
        els.resultsSection.classList.add("hidden");
        els.exportBtn.classList.add("hidden");
        els.exportNote.classList.add("hidden");
    }

    function hideMessage() {
        els.messageBox.classList.add("hidden");
    }

    // -------------------------------------------------------------- progress

    function updateProgress(data) {
        var maxIter = num(data.max_iterations);
        if (!isFinite(maxIter) || maxIter <= 0) maxIter = 1;
        var iter = num(data.iteration);
        if (!isFinite(iter)) iter = 0;

        var pct = Math.max(0, Math.min(100, Math.round((iter / maxIter) * 100)));
        els.progressBar.style.width = pct + "%";
        els.progressBar.textContent = pct + "%";

        var imp = num(data.improvement_pct);
        var t = num(data.time_elapsed);
        var best = num(data.best_metric);

        els.statusText.textContent =
            "Iteration " + Math.round(iter) + " / " + Math.round(maxIter) +
            "  " + DOT + "  " + (isFinite(imp) ? fmtSigned(imp, 1) + "%" : EM_DASH) +
            "  " + DOT + "  best " + (isFinite(best) ? fmtNum(best, 0) : EM_DASH) +
            (isFinite(t) ? "  " + DOT + "  " + t.toFixed(1) + "s" : "");

        var budget = data.budget_used || {};
        appendLog(
            "iter " + Math.round(iter) + "/" + Math.round(maxIter) +
            "  best " + (isFinite(best) ? fmtNum(best, 0) : EM_DASH) +
            (isFinite(imp) ? "  " + fmtSigned(imp, 1) + "%" : "") +
            "  budget " + get(budget, "unallocated", "?") + " alloc / " +
            get(budget, "respec", "?") + " respec"
        );
    }

    // --------------------------------------------------------------- results

    function displayResults(result) {
        result = result || {};
        var before = result.baseline_stats || {};
        var after = result.optimized_stats || {};

        // Headline improvement (accurate, no badge).
        var imp = num(result.improvement_pct);
        els.improvementHeadline.textContent = isFinite(imp) ? fmtSigned(imp, 1) + "%" : EM_DASH;
        els.improvementHeadline.className =
            "headline-value " + (isFinite(imp) ? (imp > 0 ? "pos" : (imp < 0 ? "neg" : "neutral")) : "neutral");

        // Summary line (accurate facts: node counts + budget used).
        var budget = result.budget_usage || {};
        var nodes = result.node_changes || {};
        var conv = result.convergence || {};
        var added = (nodes.added || []).length;
        var removed = (nodes.removed || []).length;
        var swapped = get(nodes, "swapped", 0);
        var parts = [
            added + " nodes added",
            removed + " removed",
            swapped + " swapped",
            "budget used: " + get(budget, "unallocated_used", 0) + " allocate / " +
                get(budget, "respec_used", 0) + " respec"
        ];
        if (conv && conv.iterations_run !== undefined && conv.iterations_run !== null) {
            parts.push(conv.iterations_run + " iterations");
        }
        if (conv && conv.reason) {
            parts.push("stopped: " + conv.reason);
        }
        els.resultsSummary.textContent = parts.join("  " + DOT + "  ");

        // Before / after table.
        els.resultsTbody.innerHTML = "";
        STAT_ROWS.forEach(function (row) {
            var bVal = getStat(before, row.key);
            var aVal = getStat(after, row.key);
            var bN = num(bVal);
            var aN = num(aVal);
            var delta = (isFinite(bN) && isFinite(aN)) ? (aN - bN) : null;

            var tr = document.createElement("tr");

            // label + badges
            var tdLabel = document.createElement("td");
            tdLabel.className = "col-stat";
            var wrap = document.createElement("div");
            wrap.className = "stat-label";
            var name = document.createElement("span");
            name.className = "stat-name";
            name.textContent = row.label;
            wrap.appendChild(name);
            if (row.approx) {
                var approx = document.createElement("span");
                approx.className = "note-approx";
                approx.textContent = "(approx)";
                wrap.appendChild(approx);
            }
            if (row.estimate) {
                var badge = document.createElement("span");
                badge.className = "badge-estimate";
                badge.textContent = "estimate " + EM_DASH + " not PoB-accurate";
                wrap.appendChild(badge);
            }
            tdLabel.appendChild(wrap);

            var tdBefore = document.createElement("td");
            tdBefore.className = "col-num";
            tdBefore.textContent = formatValue(row.fmt, bVal);

            var tdAfter = document.createElement("td");
            tdAfter.className = "col-num";
            tdAfter.textContent = formatValue(row.fmt, aVal);

            var tdDelta = document.createElement("td");
            var deltaClass = (delta === null || delta === 0) ? "neutral" : (delta > 0 ? "pos" : "neg");
            tdDelta.className = "col-num delta " + deltaClass;
            tdDelta.textContent = formatDelta(row.fmt, delta);

            tr.appendChild(tdLabel);
            tr.appendChild(tdBefore);
            tr.appendChild(tdAfter);
            tr.appendChild(tdDelta);
            els.resultsTbody.appendChild(tr);
        });

        els.resultsSection.classList.remove("hidden");
        els.exportBtn.classList.remove("hidden");
    }

    // ---------------------------------------------------------------- errors

    function displayError(err) {
        err = err || {};
        var type = err.error_type || "error";
        var reason = err.reason || "Something went wrong.";

        if (type === "unsupported_build_type") {
            // Friendly info box, not a scary error (per product decision).
            els.messageBox.className = "message-box info";
            els.messageTitle.textContent = "Build Type Not Supported (Yet!)";
            els.messageBody.textContent =
                "Coming in V2: Minion builds, Totems, traps, mines, Trigger-based builds.";
        } else {
            els.messageBox.className = "message-box";
            els.messageTitle.textContent = humanizeErrorType(type);
            els.messageBody.textContent = reason;
        }
        els.messageBox.classList.remove("hidden");
        appendLog("Error: " + reason, "error");
    }

    // ------------------------------------------------------------- optimize

    function onOptimizeClick() {
        if (isRunning) return;
        hideMessage();
        hideResults();

        var code = els.pobCode.value.trim();
        if (!code) {
            displayError({ error_type: "missing_input", reason: "Please paste a Path of Building code first." });
            return;
        }
        if (code.length > MAX_CODE_LEN) {
            displayError({
                error_type: "too_long",
                reason: "Build code is " + code.length.toLocaleString() +
                    " characters, which exceeds the " + MAX_CODE_LEN.toLocaleString() + " character limit."
            });
            return;
        }

        var metric = els.metric.value;
        var unalloc = parseIntOr(els.unalloc.value, 0);
        if (unalloc < 0) unalloc = 0;
        var respecRaw = els.respec.value.trim();
        var respec = respecRaw === "" ? null : parseIntOr(respecRaw, null);
        if (respec !== null && respec < 0) respec = 0;

        setRunning(true);
        showProgress();
        resetProgress();
        appendLog("Submitting build (" + code.length.toLocaleString() + " chars, metric=" + metric + ")" + ELLIPSIS);

        fetch("/optimize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                pob_code: code,
                metric: metric,
                unallocated_points: unalloc,
                respec_points: respec
            })
        })
        .then(function (resp) {
            return resp.json().catch(function () { return {}; }).then(function (body) {
                return { ok: resp.ok, status: resp.status, body: body };
            });
        })
        .then(function (res) {
            if (!res.ok) {
                var err = (res.body && res.body.error_type)
                    ? res.body
                    : { error_type: "request_failed", reason: "Optimization request failed (HTTP " + res.status + ")." };
                displayError(err);
                finishRun();
                return;
            }
            currentSessionId = res.body && res.body.session_id;
            if (!currentSessionId) {
                displayError({ error_type: "request_failed", reason: "Server did not return a session id." });
                finishRun();
                return;
            }
            appendLog("Session " + currentSessionId + " accepted. Streaming progress" + ELLIPSIS, "success");
            connectSSE(currentSessionId);
        })
        .catch(function (e) {
            displayError({ error_type: "request_failed", reason: "Could not reach the server: " + e });
            finishRun();
        });
    }

    // --------------------------------------------------------------- export

    function legacyCopy(text) {
        try {
            var ta = document.createElement("textarea");
            ta.value = text;
            ta.setAttribute("readonly", "");
            ta.style.position = "absolute";
            ta.style.left = "-9999px";
            document.body.appendChild(ta);
            ta.select();
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
            return navigator.clipboard.writeText(text).then(
                function () { return true; },
                function () { return legacyCopy(text); }
            );
        }
        return Promise.resolve(legacyCopy(text));
    }

    function showExportNote(msg, success) {
        els.exportNote.textContent = msg;
        els.exportNote.style.color = success ? "var(--pos)" : "var(--neg)";
        els.exportNote.classList.remove("hidden");
    }

    function onExportClick() {
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
                var reason = (res.body && res.body.reason)
                    ? res.body.reason
                    : "Export failed (HTTP " + res.status + ").";
                showExportNote(reason, false);
                return;
            }
            copyToClipboard(res.body.pob_code).then(function (ok) {
                if (ok) {
                    showExportNote("Copied optimized build code to clipboard.", true);
                } else {
                    showExportNote("Could not copy automatically " + EM_DASH + " code logged to the console.", false);
                }
            });
        })
        .catch(function (e) {
            showExportNote("Export failed: " + e, false);
        });
    }

    // ------------------------------------------------------------- char count

    function updateCharCount() {
        var len = els.pobCode.value.length;
        els.charCount.textContent =
            len.toLocaleString() + " / " + MAX_CODE_LEN.toLocaleString() + " characters";
        var over = len > MAX_CODE_LEN;
        els.charCount.classList.toggle("over-limit", over);
        els.pobCode.classList.toggle("over-limit", over);
    }

    // ----------------------------------------------------------------- init

    function init() {
        els.pobCode = document.getElementById("pob-code");
        els.charCount = document.getElementById("char-count");
        els.clearBtn = document.getElementById("clear-btn");
        els.unalloc = document.getElementById("unallocated-points");
        els.respec = document.getElementById("respec-points");
        els.metric = document.getElementById("metric");
        els.optimizeBtn = document.getElementById("optimize-btn");

        els.messageBox = document.getElementById("message-box");
        els.messageTitle = document.getElementById("message-title");
        els.messageBody = document.getElementById("message-body");

        els.progressSection = document.getElementById("progress-section");
        els.progressBar = document.getElementById("progress-bar");
        els.statusText = document.getElementById("status-text");
        els.eventLog = document.getElementById("event-log");

        els.resultsSection = document.getElementById("results-section");
        els.improvementHeadline = document.getElementById("improvement-headline");
        els.resultsSummary = document.getElementById("results-summary");
        els.resultsTbody = document.getElementById("results-tbody");
        els.exportBtn = document.getElementById("export-btn");
        els.exportNote = document.getElementById("export-note");

        // Wire SSE hooks (sseClient + connectSSE provided by sse_client.js).
        sseClient.onProgress = updateProgress;
        sseClient.onComplete = function (data) {
            els.progressBar.style.width = "100%";
            els.progressBar.textContent = "100%";
            els.statusText.textContent = "Optimization complete.";
            appendLog("Optimization complete.", "success");
            displayResults(data);
            finishRun();
        };
        sseClient.onError = function (err) {
            displayError(err);
            finishRun();
        };

        // Wire DOM events.
        els.optimizeBtn.addEventListener("click", onOptimizeClick);
        els.exportBtn.addEventListener("click", onExportClick);
        els.clearBtn.addEventListener("click", function () {
            els.pobCode.value = "";
            updateCharCount();
            hideMessage();
            els.pobCode.focus();
        });
        els.pobCode.addEventListener("input", updateCharCount);

        updateCharCount();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
