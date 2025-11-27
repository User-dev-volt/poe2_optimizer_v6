# Sprint Change Proposal: Full PoB Integration

**Date:** 2025-11-22
**Author:** John (PM)
**Status:** APPROVED
**Approved By:** Alec

---

## 1. Issue Summary

### Problem Statement

The Epic 2 optimizer is structurally complete but functionally unvalidated. MinimalCalc.lua (Epic 1 scope) was designed for parity testing—verifying calculation engine outputs match PoB GUI. It does NOT calculate stats from passive tree node bonuses, returning ~1.2 DPS for all builds regardless of allocation. The optimizer has no signal to optimize toward, and we cannot prove the core value proposition: "optimizer makes builds better."

### Discovery Context

- **Discovered:** During Epic 2 validation testing (Task 6)
- **Symptom:** 0% improvement on all test builds
- **Root Cause:** Calculator returns identical stats regardless of passive tree changes

### Evidence

```
amazon_80: 61 nodes → DPS=1.18, 65 nodes → DPS=1.18 (0% change)
deadeye_100: 69 nodes → DPS=1.27, 73 nodes → DPS=1.27 (0% change)
```

---

## 2. Impact Analysis

### Epic Impact

| Epic | Impact | Status |
|------|--------|--------|
| Epic 1 | Calculator module enhanced (code location) | Code modified |
| Epic 2 | Story 2.9 added, success criteria can be validated | Story added |
| Epic 3 | Unblocked, builds on validated foundation | No changes |

### Artifact Impact

| Artifact | Change |
|----------|--------|
| `docs/epics.md` | Story 2.9 added to Epic 2 |
| `docs/stories/2-9-integrate-full-pob-calculation-engine.md` | New file created |
| `docs/prep-sprint-status.yaml` | Option D decision recorded, sequencing updated |
| `src/calculator/` | Full PoB integration replaces MinimalCalc.lua |
| `tests/fixtures/realistic_builds/` | New test corpus with items/skills |

---

## 3. Recommended Approach

### Selected Option: D - Full PoB Integration

**Implementation:** Story 2.9 added to Epic 2

### Rationale

1. **Fulfills PRD requirements** - "verifiable 5-15% improvements with mathematical proof"
2. **Required for Epic 3 anyway** - Web UI needs real calculations to display
3. **No throwaway work** - Unlike Options B/C, this is the permanent solution
4. **Low technical risk** - HeadlessWrapper.lua is proven, documented by PoB community
5. **Bounded effort** - 16-24 hours is predictable and manageable

### Options Considered

| Option | Description | Effort | Risk | Decision |
|--------|-------------|--------|------|----------|
| A | Accept and proceed (defer validation) | 0 hrs | HIGH | Rejected - ships broken product |
| B | Add node quality heuristics | 4-6 hrs | MEDIUM | Rejected - partial, throwaway |
| C | Fix calculator (Life/Mana only) | 8-12 hrs | LOW | Rejected - incomplete solution |
| **D** | **Full PoB integration** | **16-24 hrs** | **LOW** | **SELECTED** |

---

## 4. Detailed Change Proposals

### Change 1: Add Story 2.9 to Epic 2

**File:** `docs/stories/2-9-integrate-full-pob-calculation-engine.md`

**Summary:** New story implementing full HeadlessWrapper.lua integration to enable accurate DPS/Life/EHP calculations that reflect passive tree allocations.

**Key Acceptance Criteria:**
- Full HeadlessWrapper.lua integration
- Passive tree stats reflected in calculations
- Items and skills loaded from build
- Performance: <500ms single, <60s batch 100
- Epic 2 validation passes (≥70% success, ≥5% improvement)

### Change 2: Update Epic 2 Story Count

**File:** `docs/epics.md`

**Change:** Epic 2 total updated from 8 stories (24 points) to 9 stories (40-48 points)

### Change 3: Update Sprint Status

**File:** `docs/prep-sprint-status.yaml`

**Changes:**
- Task 6 status: blocked → in_progress (depends on Story 2.9)
- Decision recorded: Option D selected
- Workflow sequence defined: Story 2.9 → Task 6 → Retro → Tasks 7-10 → Epic 3

### Change 4: Test Corpus Creation (Collaborative)

**Location:** `D:\poe2_optimizer_v6\tests\fixtures\realistic_builds\`

**Process:**
1. AI agent provides links to 10-15 suitable builds
2. AI specifies degradation level for each (points to remove)
3. Alec retrieves builds, removes points in PoB, exports as XML
4. Files saved to realistic_builds directory

---

## 5. Implementation Handoff

### Change Scope: MODERATE

Requires story creation and implementation, but no fundamental replan.

### Execution Sequence

| Step | Action | Owner | Estimate |
|------|--------|-------|----------|
| 1 | Create Story 2.9 file | PM (John) | Done |
| 2 | Implement full PoB integration | Dev (Amelia) | 16-24 hrs |
| 3 | Create realistic test corpus | Dev + Alec | 2-4 hrs |
| 4 | Re-run Epic 2 validation | TEA (Murat) | 2-3 hrs |
| 5 | Epic 2 Retrospective | All | 1-2 hrs |
| 6 | Complete Tasks 7-10 (Epic 3 prep) | Various | 6-8 hrs |
| 7 | Start Epic 3 | - | - |

### Handoff Recipients

| Role | Agent | Responsibility |
|------|-------|----------------|
| Scrum Master | Sarah | Track Story 2.9, update backlog |
| Developer | Amelia | Implement Story 2.9 |
| TEA | Murat | Validation testing |
| PM | John | Retrospective facilitation |

---

## 6. Success Criteria

Story 2.9 and this change proposal are successful when:

- [ ] Full PoB integration implemented and tested
- [ ] Realistic test corpus created (10-15 builds with items/skills)
- [ ] Epic 2 validation passes:
  - [ ] Success rate ≥70%
  - [ ] Median improvement ≥5%
  - [ ] All completions <5 minutes
  - [ ] Zero budget violations
- [ ] Epic 2 retrospective completed
- [ ] Epic 3 unblocked

---

## 7. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | Alec | 2025-11-22 | APPROVED |
| PM | John | 2025-11-22 | APPROVED |

---

## References

- Epic 2 Validation Report: `docs/validation/epic-2-validation-report-2025-11-16.md`
- Story 2.9: `docs/stories/2-9-integrate-full-pob-calculation-engine.md`
- Sprint Status: `docs/prep-sprint-status.yaml`
- Realistic Builds: `tests/fixtures/realistic_builds/`
