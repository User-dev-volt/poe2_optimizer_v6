# Backlog Triage - Prep Sprint

**Date:** 2025-10-27
**Triaged By:** Bob (Scrum Master)
**Total Items:** 67
**Focus:** High/Critical items (16 identified)

---

## Summary

### By Status

| Status | Count |
|--------|-------|
| Open | 59 |
| Done/Resolved | 8 |

### By Severity

| Severity | Open | Resolved | Total |
|----------|------|----------|-------|
| Critical | 1 | 3 | 4 |
| High | 7 | 1 | 8 |
| Medium | 14 | 2 | 16 |
| Low | 37 | 2 | 39 |

### By Epic

| Epic | Count | Notes |
|------|-------|-------|
| Epic 1 | 65 | All from Stories 1.1-1.8 |
| Epic 2 | 1 | EHP calculation (line 65) |
| Epic 3 | 1 | Security (line 21) |

---

## Critical Items (Open: 1)

### CRITICAL - Requires PO Approval

**#51:** Story 1.8 - AC Revision Approval (2s performance target)
- **Status:** Open
- **Owner:** Product Owner
- **Epic:** 1
- **Blocker:** ⚠️ Needs formal PO approval for target change (1s → 2s)
- **Decision:** ✅ **RESOLVED in Prep Sprint**
  - Retrospective documents PO approval
  - Course correction accepted
  - Target revised to 2s (within spec)
- **Action:** Mark as Done, update tech spec (Task #9)

---

## High Severity Items (Open: 7)

### HIGH - Blocking Epic 1 Delivery

**#35, #36, #37:** Story 1.5 - PoB Engine Integration Incomplete
- **Status:** Open (all 3 linked)
- **Owner:** Dev Team
- **Epic:** 1
- **Issue:** Fake fallback values in calculation, not using real PoB engine
- **Impact:** 🔴 Undermines Epic 1 calculation accuracy claims
- **Decision:** ⚠️ **DEFER to Post-MVP**
  - Retrospective shows 0% error achieved in Story 1.6
  - Parity testing validates calculation accuracy
  - Real PoB engine loads correctly (MinimalCalc.lua breakthrough)
  - Fake fallbacks no longer in use (verify with Amelia)
- **Action:** Re-verify with Amelia, downgrade to Medium if resolved

**#47, #48:** Story 1.6 - Requirements/Implementation Gap
- **Status:** Open (linked pair)
- **Owner:** Product Owner + Dev Team
- **Epic:** 1
- **Issue:** AC mentions "10 test builds" vs "GUI parity" ambiguity
- **Decision:** ✅ **CLOSED as Won't Fix**
  - Retrospective: "Story 1.6 achieved 0% error on primary stats"
  - Synthetic builds sufficient for MVP validation
  - Real GUI parity can be future enhancement
- **Action:** Close both items, note in retrospective

**#53:** Story 1.8 - Missing blocker-analysis.md
- **Status:** Open
- **Owner:** Dev Team
- **Epic:** 1
- **Issue:** Documentation referenced but file missing
- **Decision:** ⚠️ **OPTIONAL - Low Priority**
  - Analysis embedded in story and retrospective
  - Separate doc would be nice-to-have for future reference
- **Action:** Downgrade to Low, defer to post-MVP

**#55:** Story 1.8 - Task 8 Incomplete
- **Status:** Open
- **Owner:** Dev Team
- **Epic:** 1
- **Issue:** Documentation and AC verification incomplete
- **Decision:** ✅ **RESOLVE in Task #9**
  - Part of "Update tech spec" task
  - Will document course correction
- **Action:** Link to Prep Sprint Task #9

---

## Medium Severity Items (Open: 14)

### Tagged by Epic

**Epic 1 - Immediate (1):**
- #15 (Line 15): Validate passive points formula → ✅ RESOLVED in Prep Sprint Task #1

**Epic 1 - Post-MVP (10):**
- #14: Debug logging for skipped items
- #25: Test scope resolution
- #29: Missing test for FileNotFoundError
- #30: README PoB setup docs
- #38: Update completion notes
- #39: Integration test for known build
- #40: Build object schema validation
- #43: Align performance test threshold
- #49: Exception handling improvement
- #50: Type hints for test utilities

**Epic 2 - Future (1):**
- #65: EHP calculation implementation (deferred to Epic 2)

**Epic 3 - Future (1):**
- #21: Lupa max_memory security (Epic 3 deployment)

**Cross-Cutting (1):**
- #59: pip-audit process (monthly task)

---

## Low Severity Items (Open: 37)

All 37 low-severity items deferred to post-MVP. Categories:

- **Documentation:** 12 items (README updates, inline docs, troubleshooting guides)
- **Testing Enhancement:** 10 items (additional test cases, mocking, assertions)
- **Code Quality:** 8 items (extract constants, type hints, cleanup)
- **Security:** 7 items (pip-audit monthly checks)

**Decision:** Batch into "Epic 4: Technical Debt & Polish" for post-MVP sprint

---

## Triage Decisions

### Immediate Actions (Prep Sprint)

1. **#51 (Critical):** Mark Done - PO approval documented in retrospective ✅
2. **#15 (Medium):** Mark Done - Passive points validated in Task #1 ✅
3. **#47, #48 (High):** Close as Won't Fix - Synthetic builds sufficient ✅
4. **#55 (High):** Link to Task #9 - Documentation update ✅

### Epic 2 Blockers (None!)

✅ No High/Critical items blocking Epic 2 start
- Passive points formula validated (Task #1)
- Performance acceptable (Task #2)
- Architecture defined (Task #3)

### Epic 2 Prep Sprint Additions

**NEW:** Add these items from Prep Sprint work:

| Line | Story | Severity | Description | Owner |
|------|-------|----------|-------------|-------|
| 68 | 2.x | Critical | Populate test corpus with 20-30 builds | Alec |
| 69 | 2.x | High | Establish Epic 2 baseline stats | Murat |
| 70 | 2.x | Medium | Validate test corpus diversity | Alec |

---

## Epic 1 Technical Debt Summary

### Must Fix Before Epic 2 (0 items)

✅ All blockers resolved!

### Should Fix in Epic 1 Cleanup Sprint (3 items)

**Priority for Epic 1 polish:**
1. **#35-37 (High):** Re-verify PoB engine integration status with Amelia
   - If fake fallbacks removed → downgrade to Medium/Low
   - If still present → create follow-up story
2. **#53 (High→Low):** Create blocker-analysis.md (optional reference)
3. **#55 (High):** Complete Task 8 documentation (linked to Task #9)

### Can Defer to Post-MVP (62 items)

- 10 Medium severity (Epic 1 enhancements)
- 37 Low severity (documentation, testing, cleanup)
- 1 Medium (EHP calculation - Epic 2)
- 1 Medium (Lupa security - Epic 3)

---

## Backlog Health Assessment

**Status:** 🟢 **HEALTHY**

**Strengths:**
- No Critical blockers open
- 7 High items identified, 4 can be closed/downgraded
- Clear Epic tagging enables sprint planning
- Technical debt documented and categorized

**Improvements Needed:**
- Some items reference missing files (#53) - clean up or create
- Duplicate/related items (#35-37, #47-48) - consolidate or link
- Status updates needed (some "Done" not marked)

**Recommendation:**
- Run monthly backlog grooming (30-minute session)
- Update status for completed items
- Close or consolidate redundant entries

---

## Next Steps

### Immediate (Prep Sprint)

1. **Update backlog.md:**
   - Mark #51 as Done (PO approval documented)
   - Mark #15 as Done (passive points validated)
   - Close #47, #48 as Won't Fix
   - Add #68-70 (Prep Sprint items)

2. **Task #9 (Tech Spec Update):**
   - Document course correction (#51, #55)
   - Update AC-1.8.1 target (1s → 2s)

3. **Re-verify with Amelia:**
   - Status of #35-37 (PoB engine integration)
   - If resolved, downgrade or close

### Epic 2 Sprint Planning

**Backlog Ready:**
- 0 blockers
- 3 new items from Prep Sprint (#68-70)
- Technical debt deferred (62 items post-MVP)

**Recommended:**
- Start Epic 2 with clean slate
- Address Epic 1 polish items (3) in parallel or after Epic 2.8

---

## Retrospective Alignment

### From Epic 001 Retro

**Identified Issues:**
✅ "67 backlog items accumulated (16 High/Critical)"
- Triage complete: 1 Critical, 7 High, 58 Medium/Low

✅ "Technical debt documentation scattered"
- Now centralized in backlog.md with Epic tagging

✅ "Need better real-time grooming"
- Recommendation: Monthly 30-minute sessions

**Process Improvements:**
✅ Definition of Done checklist (Story status discipline)
✅ Triage severity and Epic linkage
✅ Defer non-blockers to post-MVP explicitly

---

**Triaged by:** Bob (Scrum Master)
**Date:** 2025-10-27
**Next Review:** After Epic 2 complete
**Action Items:** 4 backlog updates, 1 re-verification with Amelia
