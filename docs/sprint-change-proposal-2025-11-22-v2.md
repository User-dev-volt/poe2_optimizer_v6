# Sprint Change Proposal: Story 2.9 Architectural Correction

**Date:** 2025-11-22
**Author:** John (PM)
**Status:** APPROVED
**Previous Proposal:** `docs/sprint-change-proposal-2025-11-22.md` (superseded)

---

## 1. Issue Summary

### Problem Statement

The Sprint Change Proposal approved on 2025-11-22 for Story 2.9 (Full PoB Integration) contained a **critical error in risk assessment**. The proposal stated "Low technical risk - HeadlessWrapper.lua is proven, documented by PoB community" while an **existing ADR from Epic 1 (2025-10-17)** explicitly documented this approach as "architecturally impossible in a headless Python environment."

During implementation, the dev team encountered the **exact same Windows Fatal Exception (`0xe24c4a02`)** that caused the Epic 1 pivot to MinimalCalc.lua. Story 2.9 is now BLOCKED.

### Discovery Context

- **Discovered:** During Story 2.9 implementation and testing (2025-11-22)
- **Symptom:** `pytest tests/integration/test_full_pob_engine.py` crashes with Windows Fatal Exception
- **Root Cause:** HeadlessWrapper.lua requires full PoB GUI runtime with C++ native bindings, Windows windowing system, and native graphics libraries - documented in Epic 1 ADR but not referenced in Story 2.9 proposal

### Evidence

**Epic 1 ADR (2025-10-17) - `docs/Corrected Course Docs/sprint-change-proposal-epic-1-minimalcalc.md`:**
> "HeadlessWrapper.lua approach documented in the PRD and Tech Spec is **architecturally impossible** to execute in a headless Python environment. Windows Fatal Exception `0xe24c4a02` in native code - cannot be caught or worked around."

**Story 2.9 Proposal (2025-11-22) - `docs/sprint-change-proposal-2025-11-22.md`:**
> "Low technical risk - HeadlessWrapper.lua is proven, documented by PoB community"

**Story 2.9 Implementation Result:**
```
pytest tests/integration/test_full_pob_engine.py
→ Windows Fatal Exception 0xe24c4a02 at full_pob_engine.py:171
```

### Issue Type Classification

- [x] **Failed approach requiring different solution** - The HeadlessWrapper.lua approach was already proven impossible in Epic 1
- [x] **Misunderstanding of original requirements** - Prior ADR not referenced when evaluating the proposal

---

## 2. Impact Analysis

### Epic Impact

| Epic | Impact | Status |
|------|--------|--------|
| **Epic 1** | None - MinimalCalc.lua solution remains valid | Complete |
| **Epic 2** | Story 2.9 BLOCKED - Epic cannot be validated | Blocked on 2.9 |
| **Epic 3** | Waiting - Depends on Epic 2 completion | Backlog |

### Story Impact

| Story | Current Status | Impact |
|-------|---------------|--------|
| **Story 2.9** | BLOCKED | Needs architectural revision - HeadlessWrapper impossible |
| **Stories 2.1-2.8** | Done | Functionally complete but cannot validate without 2.9 |
| **Epic 2 Retrospective** | Completed | May need addendum after 2.9 resolution |

### Artifact Conflicts

| Artifact | Conflict | Resolution Needed |
|----------|----------|-------------------|
| `docs/stories/2-9-integrate-full-pob-calculation-engine.md` | Story based on impossible approach | Revise with viable approach |
| `docs/sprint-change-proposal-2025-11-22.md` | Contains incorrect risk assessment | Supersede with this document |
| `docs/epics.md` | Story 2.9 description mentions HeadlessWrapper | Update approach description |
| `docs/sprint-status.yaml` | Story 2.9 marked blocked | Update after resolution |

### Technical Impact

| Component | Impact |
|-----------|--------|
| `src/calculator/full_pob_engine.py` | Created but unusable - crashes on HeadlessWrapper load |
| `tests/integration/test_full_pob_engine.py` | Tests crash with fatal exception |
| Existing MinimalCalc.lua integration | **Unaffected** - continues to work for parity testing |

---

## 3. Path Forward Evaluation

### Option 1: Extend MinimalCalc.lua (C-Revised)

**Description:** Extend the existing MinimalCalc.lua to calculate passive tree bonuses by manually processing passive node stats.

| Criterion | Assessment |
|-----------|------------|
| **Effort** | 8-16 hours |
| **Risk** | MEDIUM - Requires understanding PoB's passive stat aggregation |
| **Viability** | HIGH - MinimalCalc already loads Modules/Calcs.lua successfully |
| **Sustainability** | HIGH - Builds on proven Epic 1 approach |

**Approach:**
1. Load passive tree node data from `Data/3_0.lua` (PoE 2 tree)
2. For each allocated node, aggregate stat bonuses
3. Pass aggregated stats to existing calcs.perform()
4. Extract DPS/Life/EHP from calculation results

**Pros:**
- Builds on proven MinimalCalc.lua approach
- No native code dependencies
- Same process, no IPC overhead
- Already has working stub functions

**Cons:**
- May not capture complex node interactions (keystones, ascendancy)
- Accuracy may be lower than full PoB

**Status:** [x] Viable

---

### Option 2: Subprocess Isolation

**Description:** Run the FullPoBEngine in an isolated Python subprocess to avoid LuaJIT state corruption issues.

| Criterion | Assessment |
|-----------|------------|
| **Effort** | 8-12 hours |
| **Risk** | HIGH - May not fix native code crash |
| **Viability** | UNCERTAIN - Fatal exception is in native code, may crash subprocess too |
| **Sustainability** | MEDIUM - Adds IPC complexity |

**Approach:**
1. Create subprocess wrapper for FullPoBEngine
2. Communicate via JSON over stdin/stdout
3. Restart subprocess if crash detected

**Pros:**
- Isolates crash from main process
- Can recover by restarting subprocess

**Cons:**
- IPC overhead (slower calculations)
- May still crash subprocess (native exception)
- Complex error handling

**Status:** [ ] Viable - **NOT RECOMMENDED** (doesn't address root cause)

---

### Option 3: External PoB CLI/GUI

**Description:** Use PoB's existing CLI or GUI externally via subprocess for full calculations.

| Criterion | Assessment |
|-----------|------------|
| **Effort** | 4-8 hours |
| **Risk** | LOW - Uses PoB as designed |
| **Viability** | HIGH - Guaranteed to work (PoB GUI works) |
| **Sustainability** | LOW - Requires PoB installation, slow |

**Approach:**
1. Save build XML to temp file
2. Call PoB CLI/GUI with build file
3. Parse output for stats
4. Use for validation/spot-checking only

**Pros:**
- Guaranteed accuracy (uses actual PoB)
- No Lua integration issues

**Cons:**
- Very slow (process spawn overhead)
- Requires PoB installation
- Not suitable for batch optimization (1000+ calcs)

**Status:** [x] Viable for validation, [ ] Not viable for optimization

---

### Option 4: Hybrid Approach (Recommended)

**Description:** Use MinimalCalc.lua (extended) for fast optimization calculations, use External PoB for final validation.

| Criterion | Assessment |
|-----------|------------|
| **Effort** | 12-20 hours |
| **Risk** | LOW - Combines proven approaches |
| **Viability** | HIGH - Best of both worlds |
| **Sustainability** | HIGH - Matches Epic 1 ADR approach |

**Approach:**
1. **Phase 1 (8-12 hrs):** Extend MinimalCalc.lua to calculate passive tree bonuses
2. **Phase 2 (4-8 hrs):** Implement External PoB validation for final results
3. Optimization uses MinimalCalc (fast, ~100ms/calc)
4. Final result validated against External PoB (slow, ~2s, but only once)

**Pros:**
- Fast optimization (MinimalCalc)
- Accurate validation (External PoB)
- Builds on proven approaches
- Clear separation of concerns

**Cons:**
- More implementation effort
- Two calculation paths to maintain

**Status:** [x] **RECOMMENDED**

---

### Selected Approach: Option 4 - Hybrid

**Rationale:**
1. **Proven foundations** - Builds on Epic 1's MinimalCalc.lua success
2. **Accuracy guaranteed** - External PoB validates final results
3. **Performance maintained** - MinimalCalc handles optimization loop
4. **Risk mitigation** - No native code dependencies in critical path
5. **Aligns with Epic 1 ADR** - Respects documented architectural constraints

---

## 4. Detailed Change Proposals

### Change 1: Revise Story 2.9 Approach

**File:** `docs/stories/2-9-integrate-full-pob-calculation-engine.md`
**Section:** Technical Notes / Implementation Approach

**OLD:**
```markdown
### Implementation Approach
1. [x] Replace MinimalCalc.lua loader with HeadlessWrapper.lua loader
2. [x] Implement full Build object creation from PoB XML
3. [x] Configure PoB to load items, skills, and passive tree
4. [x] Extract comprehensive stats from calcs table
5. [x] Handle edge cases (missing items, unsupported skills)
```

**NEW:**
```markdown
### Implementation Approach (Revised - Hybrid)

**Phase 1: Extend MinimalCalc.lua (8-12 hours)**
1. [ ] Load passive tree node data from Data/3_0.lua
2. [ ] Implement passive node stat aggregation
3. [ ] Pass aggregated stats to calcs.perform()
4. [ ] Extract DPS/Life/EHP from calculation results
5. [ ] Validate against known builds

**Phase 2: External PoB Validation (4-8 hours)**
1. [ ] Implement ExternalPoBValidator class
2. [ ] Save build to temp XML file
3. [ ] Call PoB CLI/GUI subprocess
4. [ ] Parse output stats
5. [ ] Compare with MinimalCalc results

**Note:** HeadlessWrapper.lua approach abandoned per Epic 1 ADR.
See: `docs/Corrected Course Docs/sprint-change-proposal-epic-1-minimalcalc.md`
```

**Rationale:** Replace impossible HeadlessWrapper approach with proven hybrid strategy.

---

### Change 2: Update Story 2.9 Acceptance Criteria

**File:** `docs/stories/2-9-integrate-full-pob-calculation-engine.md`
**Section:** Acceptance Criteria

**OLD:**
```markdown
### AC-2.9.1: Full HeadlessWrapper.lua Integration
- [ ] Calculator loads and executes HeadlessWrapper.lua (not MinimalCalc.lua)
```

**NEW:**
```markdown
### AC-2.9.1: Extended MinimalCalc.lua Integration
- [ ] Calculator extends MinimalCalc.lua with passive tree stat aggregation
- [ ] Passive tree node bonuses reflected in calculations
- [ ] No HeadlessWrapper.lua dependencies (per Epic 1 ADR)
```

**Rationale:** Align ACs with viable implementation approach.

---

### Change 3: Update Story 2.9 Status

**File:** `docs/stories/2-9-integrate-full-pob-calculation-engine.md`
**Section:** Header

**OLD:**
```markdown
**Status:** blocked
```

**NEW:**
```markdown
**Status:** in_progress
```

**Rationale:** Unblock story with revised approach.

---

### Change 4: Update Sprint Status

**File:** `docs/sprint-status.yaml`
**Section:** Epic 2

**OLD:**
```yaml
2-9-integrate-full-pob-calculation-engine: blocked  # BLOCKED: Architectural conflict
```

**NEW:**
```yaml
2-9-integrate-full-pob-calculation-engine: in_progress  # Revised: Hybrid approach per v2 proposal
```

**Rationale:** Reflect unblocked status.

---

### Change 5: Update Epic 2 Story Description

**File:** `docs/epics.md`
**Section:** Story 2.9

**OLD:**
```markdown
**Acceptance Criteria:**
- Full HeadlessWrapper.lua integration (replaces MinimalCalc.lua)
```

**NEW:**
```markdown
**Acceptance Criteria:**
- Extended MinimalCalc.lua with passive tree stat aggregation
- External PoB validation for final results
- No HeadlessWrapper.lua dependencies (per Epic 1 ADR)
```

**Rationale:** Align epic description with revised approach.

---

### Change 6: Add Process Improvement Note

**File:** `docs/stories/2-9-integrate-full-pob-calculation-engine.md`
**Section:** References (new section)

**ADD:**
```markdown
## Process Improvement Note

**Issue:** Story 2.9's original proposal (2025-11-22) did not reference Epic 1's ADR documenting HeadlessWrapper.lua as architecturally impossible.

**Root Cause:** No formal ADR lookup step in sprint change workflow.

**Recommendation:** Add mandatory ADR review step to correct-course and sprint-change workflows before approving technical approaches.

**Related ADR:** `docs/Corrected Course Docs/sprint-change-proposal-epic-1-minimalcalc.md`
```

**Rationale:** Document process gap to prevent recurrence.

---

## 5. Implementation Handoff

### Change Scope: MODERATE

Story 2.9 approach revision with new implementation strategy. No fundamental project replan required.

### Execution Sequence

| Step | Action | Owner | Estimate |
|------|--------|-------|----------|
| 1 | Apply story changes (this proposal) | PM (John) | 1 hr |
| 2 | Implement Phase 1: Extend MinimalCalc.lua | Dev (Amelia) | 8-12 hrs |
| 3 | Implement Phase 2: External PoB Validation | Dev (Amelia) | 4-8 hrs |
| 4 | Re-run Epic 2 validation | TEA (Murat) | 2-3 hrs |
| 5 | Update Epic 2 retrospective if needed | PM (John) | 1 hr |
| 6 | Complete Epic 3 prep tasks | Various | 6-8 hrs |
| 7 | Start Epic 3 | - | - |

**Total Estimated Effort:** 22-33 hours (vs. original 16-24 hrs)

### Handoff Recipients

| Role | Agent | Responsibility |
|------|-------|----------------|
| **Scrum Master** | Sarah | Update sprint status, track Story 2.9 v2 |
| **Developer** | Amelia | Implement hybrid approach (Phase 1 + 2) |
| **TEA** | Murat | Validation testing after implementation |
| **PM** | John | Update retrospective, monitor process improvement |

### Success Criteria

Story 2.9 v2 is successful when:

- [ ] Extended MinimalCalc.lua calculates passive tree bonuses
- [ ] Adding/removing nodes changes DPS/Life/EHP proportionally
- [ ] External PoB validation confirms accuracy (within 5% tolerance)
- [ ] Epic 2 validation passes:
  - [ ] Success rate ≥70%
  - [ ] Median improvement ≥5%
  - [ ] All completions <5 minutes
  - [ ] Zero budget violations
- [ ] Process improvement documented for future sprint changes

---

## 6. Checklist Completion Summary

| Section | Status | Notes |
|---------|--------|-------|
| 1. Trigger and Context | [x] Done | HeadlessWrapper ADR not referenced in original proposal |
| 2. Epic Impact Assessment | [x] Done | Epic 2 blocked, Epic 3 waiting |
| 3. Artifact Conflict Analysis | [x] Done | Story 2.9, epics.md, sprint-status.yaml need updates |
| 4. Path Forward Evaluation | [x] Done | Hybrid approach selected (Option 4) |
| 5. Sprint Change Proposal | [x] Done | This document |
| 6. Final Review and Handoff | [ ] Pending | Awaiting user approval |

---

## 7. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | Alec | 2025-11-22 | APPROVED |
| PM | John | 2025-11-22 | APPROVED |

---

## References

- **Epic 1 ADR:** `docs/Corrected Course Docs/sprint-change-proposal-epic-1-minimalcalc.md`
- **Original Story 2.9 Proposal:** `docs/sprint-change-proposal-2025-11-22.md` (superseded)
- **Story 2.9:** `docs/stories/2-9-integrate-full-pob-calculation-engine.md`
- **Sprint Status:** `docs/sprint-status.yaml`

---

*Generated by John (PM) using BMAD-CORE Correct-Course Workflow*
*Configuration: D:\poe2_optimizer_v6\bmad\bmm\config.yaml*
