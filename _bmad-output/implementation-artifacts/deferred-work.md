# Deferred Work

Tracked items intentionally deferred out of a review/dev pass — real, but not actionable in the originating story.

## Deferred from: code review of 4-2-fullcalcengine-worker-pool-cooperative-cancel (2026-07-05)

- **`_select_best_neighbor` index mis-alignment** [src/optimizer/hill_climbing.py:516] — `_evaluate_neighbors` skips failed neighbors (`except: continue`), so `evaluations` can be a strict subset of `neighbors`/`mutations`, yet `_select_best_neighbor` indexes the full `mutations[]` list with `best_idx` computed over `evaluations`. If a neighbor within the evaluated prefix throws during calc, `mutations[best_idx]` can point at the wrong mutation (mis-tracked added/removed node ids). Root cause (skip-on-failure) is **pre-existing and independent of Story 4.2**; the new cooperative-cancel early-break returns a clean, aligned prefix. Flagged because AC-4.2.9 makes partial `evaluations` a routine occurrence — worth a dedicated fix (align `mutations` to `evaluations`, or carry the mutation alongside each evaluation) outside this story.
