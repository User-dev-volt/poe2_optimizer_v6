/* ============================================================
   sse_client.js
   Thin wrapper around EventSource for the optimizer progress stream.

   The main script sets the hooks:
       sseClient.onProgress = fn(data)
       sseClient.onComplete = fn(data)   // data = OptimizationResult.to_dict()
       sseClient.onError    = fn({error_type, reason})

   then calls connectSSE(sessionId).

   Server emits named events 'progress' | 'complete' | 'error', each carrying a
   JSON `data` line. The stream is closed locally on 'complete' / 'error' so the
   browser does not auto-reconnect after the server-side generator ends.
   ============================================================ */

(function (global) {
    "use strict";

    var sseClient = {
        source: null,
        onProgress: null,
        onComplete: null,
        onError: null,

        close: function () {
            if (this.source) {
                this.source.close();
                this.source = null;
            }
        }
    };

    function safeParse(raw) {
        if (raw === undefined || raw === null || raw === "") {
            return null;
        }
        try {
            return JSON.parse(raw);
        } catch (e) {
            return null;
        }
    }

    function fire(cb, payload) {
        if (typeof cb === "function") {
            try {
                cb(payload);
            } catch (e) {
                // Never let a callback error tear down the stream silently.
                if (global.console) {
                    console.error("sse callback error", e);
                }
            }
        }
    }

    /**
     * Open an EventSource against /progress/<sessionId> and wire the handlers.
     * Returns the underlying EventSource.
     */
    function connectSSE(sessionId) {
        // Drop any prior stream before opening a new one.
        sseClient.close();

        var source = new EventSource("/progress/" + encodeURIComponent(sessionId));
        sseClient.source = source;

        source.addEventListener("progress", function (event) {
            var data = safeParse(event.data);
            if (data) {
                fire(sseClient.onProgress, data);
            }
        });

        source.addEventListener("complete", function (event) {
            var data = safeParse(event.data);
            sseClient.close();
            fire(sseClient.onComplete, data || {});
        });

        // NOTE: 'error' fires for BOTH server-sent application errors (which
        // carry a JSON `data` line) AND native transport errors (no data, and
        // the browser may be mid-reconnect). Distinguish by presence of data.
        source.addEventListener("error", function (event) {
            var data = safeParse(event && event.data);

            if (data) {
                // Application-level error from the server.
                sseClient.close();
                fire(sseClient.onError, data);
                return;
            }

            // Transport-level error. readyState CONNECTING (0) => the browser is
            // auto-retrying; let it. CLOSED (2) => terminal, surface and stop.
            if (source.readyState === EventSource.CLOSED) {
                sseClient.close();
                fire(sseClient.onError, {
                    error_type: "connection_error",
                    reason: "Lost connection to the optimization stream."
                });
            }
        });

        return source;
    }

    // Expose on the global scope for main.js.
    global.sseClient = sseClient;
    global.connectSSE = connectSSE;
})(window);
