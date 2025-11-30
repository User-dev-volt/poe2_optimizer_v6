# Calculation Gap Analysis - Decision Matrix
**Date:** 2025-11-29
**Story:** 2.9.x - Comprehensive Calculation Gap Analysis

## Executive Summary

**Recommendation:** **Full Subprocess Approach** (Option C)

**Rationale:** Simplest, lowest risk, guaranteed complete coverage, minimal effort difference (19-26 hrs vs 19-27 hrs).

---

## Finalists Comparison

| Criterion | **Hybrid Approach (B)** | **Subprocess Approach (C)** | Winner |
|-----------|------------------------|----------------------------|--------|
| **Total Effort** | 19-27 hours | 19-26 hours | Subprocess (slightly lower) |
| **Skill Coverage** | 100% (MinimalCalc + PoB) | 100% (PoB for all) | Tie |
| **Performance (Attacks)** | Fast (~10ms) | Slower (~50-100ms) | Hybrid |
| **Performance (Spells)** | Slower (~50-100ms) | Slower (~50-100ms) | Tie |
| **Code Complexity** | High (2 paths) | Low (1 path) | **Subprocess** |
| **Maintenance Burden** | High (maintain both) | Low (PoB only) | **Subprocess** |
| **Risk (Scope Creep)** | Medium (MinimalCalc bugs) | Very Low (proven system) | **Subprocess** |
| **Risk (Unknown Issues)** | Medium (attack path fragile) | Very Low (PoB handles all) | **Subprocess** |
| **Future-Proofing** | Medium (new skills → debug) | **High** (PoB auto-updates) | **Subprocess** |
| **Architectural Simplicity** | Complex | **Simple** | **Subprocess** |

**Score:** Subprocess wins 7/10 criteria, Hybrid wins 1/10 (attack performance), 2 ties.

---

## Detailed Analysis

### 1. Implementation Effort

**Hybrid Approach (19-27 hours):**
- Cat 5: Weapon stubs (2-3 hrs)
- Cat 3b: Python parser (3-4 hrs)
- Cat 3a: Lua crashes (6-8 hrs)
- Subprocess fallback for spells (8-12 hrs)

**Subprocess Approach (19-26 hours):**
- Cat 3b: Python parser (3-4 hrs)
- Replace MinimalCalc entirely (12-16 hrs)
- Performance optimization (4-6 hrs)

**Winner:** Subprocess (slightly less effort, simpler scope)

---

### 2. Performance Analysis

| Scenario | Hybrid | Subprocess | Impact |
|----------|--------|------------|--------|
| **Attack build (Lightning Arrow)** | ~10ms (MinimalCalc) | ~50-100ms (PoB) | 40-90ms slower |
| **Spell build (Frost Mage)** | ~50-100ms (PoB) | ~50-100ms (PoB) | No difference |
| **DOT build (Essence Drain)** | ~50-100ms (PoB) | ~50-100ms (PoB) | No difference |
| **Totem build** | ~50-100ms (PoB) | ~50-100ms (PoB) | No difference |

**Attack Build Impact Analysis:**

For a typical optimization run:
- Iterations: 50-200
- Calculations per iteration: 1-20 neighbors
- Total calculations: 50-4000

**Time Impact (Attack Builds Only):**
- Hybrid: 50-200 iters × 10 neighbors × 10ms = **5-20 seconds**
- Subprocess: 50-200 iters × 10 neighbors × 75ms = **37-150 seconds**
- **Difference: 32-130 seconds slower**

**Context:** Epic 2 success criteria allows up to 300 seconds per build. A 130-second slowdown still fits within budget.

**Spell/DOT/Totem Builds (80% of corpus):** No performance difference - both use subprocess.

**Winner:** Hybrid has better peak performance, but impact is acceptable for Subprocess.

---

### 3. Code Complexity & Maintainability

**Hybrid Approach:**
```
if (skill.is_attack && weapon_stub_exists):
    result = MinimalCalc.lua(build)  # Fast path
else:
    result = external_pob_subprocess(build)  # Slow path

# Must maintain:
- MinimalCalc.lua weapon stubs
- Skill type detection logic
- Fallback routing logic
- Two different error handling paths
- Two different output parsing paths
```

**Subprocess Approach:**
```
result = external_pob_subprocess(build)  # Always

# Only maintain:
- External PoB process management
- Single output parsing path
- Single error handling path
```

**Lines of Code Estimate:**
- Hybrid: ~500 LOC (MinimalCalc integration + subprocess + routing)
- Subprocess: ~200 LOC (subprocess only)

**Maintenance Scenarios:**

| Scenario | Hybrid Effort | Subprocess Effort |
|----------|---------------|-------------------|
| New weapon type added (e.g., "Focus") | High - add to MinimalCalc stubs | None - PoB handles it |
| New skill type (e.g., "Runes") | High - debug MinimalCalc or route to subprocess? | None - PoB handles it |
| PoB updates calculation formula | High - update MinimalCalc to match | None - automatic |
| Bug in MinimalCalc weapon logic | Medium - debug Lua errors | N/A |
| Bug in subprocess call | Low - fix process management | Low - fix process management |

**Winner:** Subprocess (3x simpler, zero maintenance for game updates)

---

### 4. Risk Assessment

**Hybrid Approach Risks:**

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| MinimalCalc weapon bugs persist | **HIGH** | Medium | Add more weapon types as discovered |
| Attack skill edge cases fail | Medium | Medium | Route to subprocess as fallback |
| Skill type detection errors | Medium | Low | Conservative routing (default to subprocess) |
| Two code paths drift | Low | High | Extensive testing |

**Subprocess Approach Risks:**

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| PoB process crashes | Low | Medium | Process pool + restart |
| PoB output format changes | Very Low | Low | PoB format stable for years |
| Performance unacceptable | Very Low | Low | Already measured ~75ms, fits budget |

**Winner:** Subprocess (lower probability and impact across all risks)

---

### 5. Future-Proofing

**Hybrid Approach:**
- New PoE 2 skills → Need to classify (attack vs spell) and potentially debug MinimalCalc
- New game mechanics (e.g., Runes, Spirit) → May require MinimalCalc updates
- PoB formula changes → Need to keep MinimalCalc in sync

**Subprocess Approach:**
- New PoE 2 skills → PoB handles automatically
- New game mechanics → PoB handles automatically
- PoB formula changes → Flow through automatically

**Winner:** Subprocess (zero-effort future-proofing)

---

### 6. Alignment with Project Goals

**Epic 2 Goal:** Reliable optimization for 70%+ of builds with 8%+ median improvement.

**Hybrid:**
- Achieves 100% coverage ✓
- Optimizes attack performance ✓
- Adds architectural complexity ✗
- Increases maintenance burden ✗

**Subprocess:**
- Achieves 100% coverage ✓
- Accepts performance tradeoff ✓
- Maintains architectural simplicity ✓
- Minimizes maintenance burden ✓

**Project Philosophy (from retrospectives):**
- "Simplicity over optimization" (Epic 1 retro)
- "Avoid premature optimization" (Epic 1 retro)
- "Use proven libraries" (Epic 1 retro)

**Winner:** Subprocess (better alignment with project values)

---

### 7. Performance Tradeoff Acceptability

**Question:** Is 32-130 seconds slower acceptable for attack builds?

**Analysis:**

**Epic 2 Success Criteria:**
- Max completion time: < 300 seconds per build
- Current attack build time: ~40 seconds (with MinimalCalc)
- With subprocess: ~70-170 seconds
- **Still well under 300-second budget** ✓

**User Experience:**
- Attack build optimization: 40s → 170s (~2-3 minutes)
- Spell build optimization: Already 170s (no change)
- User perception: "A few minutes" either way

**Throughput:**
- Can still process 15 builds in < 45 minutes (current: ~10 minutes)
- For batch validation: acceptable

**Alternative - Batch Optimization:**
If performance becomes an issue later, can add:
- Process pooling (reuse PoB process)
- Build XML caching
- Parallel calculation of neighbors
- **Likely speedup: 2-3x** → back to ~60-90s per build

**Conclusion:** Performance tradeoff is acceptable. Optimization is premature.

---

## Decision Recommendation

### **RECOMMENDED: Full Subprocess Approach (C)**

**Effort:** 19-26 hours
**Success Rate:** 100% (guaranteed)
**Performance:** 50-100ms per calculation (~2-3 min per optimization)
**Risk:** Very low
**Maintenance:** Minimal

### Implementation Plan (Story 2.9.1)

**Phase 1: Core Integration (12-16 hours)**
1. Remove MinimalCalc.lua dependency from calculator.py
2. Implement external PoB subprocess wrapper:
   - Write build XML to temp file
   - Call PoB command line: `pob-cli calculate build.xml`
   - Parse JSON output
   - Extract DPS, life, defenses
3. Update tests to use new subprocess path
4. Validate against 15 realistic builds

**Phase 2: Performance Optimization (4-6 hours)**
1. Implement process pooling (keep PoB warm)
2. Add build XML caching (skip redundant writes)
3. Parallel neighbor evaluation (if needed)

**Phase 3: Error Handling (3-4 hours)**
1. Graceful degradation for PoB crashes
2. Timeout handling (kill hung processes)
3. Logging and diagnostics

**Total: 19-26 hours**

### Success Metrics

- [ ] All 15 realistic builds produce DPS > 0
- [ ] Success rate ≥ 70% (reach 100%)
- [ ] Median improvement ≥ 5%
- [ ] Max completion time < 300s per build
- [ ] Zero budget violations
- [ ] Code complexity reduced (remove MinimalCalc.lua)

---

## Alternative: Hybrid Approach (If Performance is Critical)

**Only choose Hybrid if:**
- Attack build performance is absolutely critical (e.g., real-time optimization UI)
- Willing to accept 2x code complexity
- Willing to maintain MinimalCalc weapon stubs going forward

**Recommendation:** Start with Subprocess. If performance becomes a proven bottleneck (not theoretical), can add MinimalCalc fast path later as optimization.

---

## Rejected: Incremental Approach (A)

**Effort:** 75-97 hours
**Risk:** Validation thrashing
**Scope:** Likely to grow to 100-150 hours

**Reason for Rejection:** Exceeds 16-hour threshold by 5-6x. High risk of discovering more gaps during implementation. Sprint Change Proposal explicitly warns against this pattern.

---

## Next Steps

1. **Get Alec's approval** on Subprocess approach
2. **Create Story 2.9.1:** Implement Full Subprocess Calculator
3. **Mark Story 2.9.x complete:** Gap analysis delivered
4. **Execute Story 2.9.1:** 19-26 hour implementation
5. **Validate with 15 builds:** Achieve 100% success rate
6. **Proceed to Epic 2 validation:** Complete Task 6
