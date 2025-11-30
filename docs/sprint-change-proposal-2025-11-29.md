# Sprint Change Proposal - Epic 2 Calculation Gap Analysis

**Date:** 2025-11-29
**Author:** Bob (Scrum Master)
**Workflow:** Correct Course - Sprint Change Management
**Status:** APPROVED by Alec

---

## Executive Summary

**Issue:** Epic 2 validation (Task 6) is blocked because the calculation engine only supports 20% of test builds (3 out of 15), far below the required 70% success rate needed to validate Epic 2 success criteria.

**Root Cause:** MinimalCalc.lua successfully calculates DPS for attack-based skills but returns 0 DPS for spell and DOT skills due to missing spell base damage data, spell-specific calculation logic, and DOT calculation engine components.

**Recommended Solution:** Execute comprehensive gap analysis (Story 2.9.x, 4-8 hours) to identify ALL missing calculation components, then make an informed decision about implementation approach (incremental, hybrid, or subprocess) based on total effort required.

**Timeline Impact:** 1-3 week delay to Epic 3 launch (depending on gap analysis findings and chosen implementation approach).

**Approval Status:** ✅ APPROVED by Alec on 2025-11-29

---

## 1. Issue Summary

### Discovery Context

**Date Discovered:** 2025-11-27
**Triggering Story:** Story 2.9 "Integrate Full PoB Calculation Engine" (marked complete 2025-11-26)
**Discovery Point:** Task 6 (Epic 2 Validation) execution

### Problem Statement

Story 2.9 was marked complete after implementing attack skill DPS calculation and fixing three critical bugs in items/skills loading. However, Epic 2 validation revealed that **only 20% of test builds calculate DPS successfully** (3 out of 15 builds).

**Current State vs Requirements:**
- **Target:** ≥70% success rate → **Current:** 20%
- **Target:** ≥5% median improvement → **Current:** 0% (cannot optimize builds with 0 DPS)
- **Result:** Epic 2 cannot be validated, Epic 3 cannot begin

### Root Cause Analysis

MinimalCalc.lua was scoped for Epic 1 parity testing (matching known PoB GUI outputs for specific builds). It successfully calculates DPS for **attack-based skills** (weapon attacks) but returns 0 DPS for **spell and DOT skills** due to:

1. **Missing spell base damage data:** Spell skills require base damage values not loaded in MinimalCalc
2. **Missing spell calculation logic:** Spell DPS formulas not implemented
3. **Missing DOT calculation engine:** Complex damage-over-time calculations not integrated

### Evidence

**Builds That Work (Attack Skills - 20%):**
- `deadeye_lightning_arrow_76`: **311.7 DPS** ✅
- `titan_falling_thunder_99`: **226.5 DPS** ✅
- `witch_essence_drain_86`: **204.0 DPS** ✅ (DOT skill - partial support)

**Builds That Fail (Spell/DOT Skills - 80%):**
- 12 spell/DOT builds return **0 DPS** ❌
  - Life Remnants (spell)
  - Frost spells
  - Fire spells
  - Most DOT skills
  - Minion builds (unknown)
  - Totem/Trap builds (unknown)

**Technical Evidence:**
```
[MinimalCalc]   grantedEffect name: Life Remnants
[MinimalCalc]   skillFlags.attack = false  ← Spell skill
[MinimalCalc]   mainSkill.output is NIL!   ← DPS not calculated
[MinimalCalc]   TotalDPS: 0
```

### Strategic Concern

**Pattern of Incremental Discovery:**
1. Story 2.9 marked "complete" (2025-11-26)
2. Three bugs discovered during validation (2025-11-27) → Fixed
3. Spell/DOT calculation gap discovered (2025-11-27) → Not fixed
4. **Unknown:** What else might be missing? (minion skills, complex interactions, etc.)

**Risk:** Continuing incremental approach (Story 2.9.1 → validate → discover 2.9.2 needed → validate → discover 2.9.3...) could result in 20-80+ hours of validation thrashing with unknown completion date.

---

## 2. Impact Analysis

### Epic 2: Core Optimization Engine

**Current Status:**
- ✅ **Structurally Complete:** Stories 2.1-2.8 (hill climbing algorithm, neighbor generation, budget tracking, metrics, convergence, progress tracking) all working
- ✅ **Story 2.9 Partial:** Attack skill DPS calculation working (311.7 DPS verified)
- ❌ **Validation Blocked:** Cannot validate Epic 2 success criteria with 20% build coverage

**Epic 2 Success Criteria:**
- **Epic-AC-1:** Find improvements for 80%+ of non-optimal builds → **BLOCKED** (only 20% calculate DPS)
- **Epic-AC-2:** Median improvement 8%+ for builds with budget headroom → **BLOCKED** (0% improvement when DPS = 0)
- **Epic-AC-3:** Optimization completes within 5 minutes → ✅ **WORKING** (performance validated)
- **Epic-AC-4:** Budget constraints never exceeded → ✅ **WORKING** (zero violations)

**Required Changes:**
1. Add **Story 2.9.x:** Comprehensive Calculation Gap Analysis (4-8 hours)
2. Add **Stories 2.9.1, 2.9.2+** based on gap analysis findings (scope TBD)
3. Update Epic 2 Tech Spec with calculator enhancement strategy
4. Update Epic 2 acceptance criteria to explicitly require spell/DOT skill support

### Epic 3: User Experience & Local Reliability

**Impact:**
- ⏸️ **Start Date Delayed:** By gap analysis + implementation time (estimated 1-3 weeks)
- ✅ **No Scope Changes:** Epic 3 stories remain unchanged
- ⚠️ **Minor Update:** Story 3.8 may need error messages for "unsupported skill type" if partial implementation chosen

### Project Timeline Impact

**Best Case (Simple Fixes ≤16 hours):**
- Gap analysis: 4-8 hours
- Implementation (Stories 2.9.1, 2.9.2): 8-12 hours
- Validation: 2-3 hours
- **Total Delay:** ~1 week

**Expected Case (Moderate Complexity 16-40 hours):**
- Gap analysis: 4-8 hours
- Implementation (hybrid approach): 16-24 hours
- Validation: 2-3 hours
- **Total Delay:** ~1-2 weeks

**Worst Case (Extensive Work >40 hours):**
- Gap analysis: 4-8 hours
- Implementation (subprocess approach): 20-30 hours
- Validation: 2-3 hours
- **Total Delay:** ~2-3 weeks

---

## 3. Artifact Conflicts and Updates Needed

### Documentation Updates Required

**1. PRD / Tech Spec (docs/tech-spec-epic-2.md)**
- Add explicit requirement: "Calculator must support diverse skill types (attacks, spells, DOT)"
- Update NFR-Epic2-P1 with calculation accuracy requirement for spell skills
- Clarify test corpus must include attack, spell, DOT, minion builds
- Add new section: "Calculator Enhancement Architecture"
  - Document MinimalCalc.lua extension strategy
  - Document alternative subprocess approach if gaps are extensive

**2. Story 2.9 (docs/stories/2-9-integrate-full-pob-calculation-engine.md)**
- Add section documenting 2025-11-27 gap discovery
- Add references to Stories 2.9.x, 2.9.1, 2.9.2+
- Update status to reflect partial completion (attack skills only)

**3. Sprint Status Files**
- `docs/sprint-status.yaml`:
  - Mark Story 2.9 as "done" with caveat note
  - Add Stories 2.9.x, 2.9.1+ with "pending" status
- `docs/prep-sprint-status.yaml`:
  - Change Task 6 status from "ready" to "blocked"
  - Update completion_notes to reflect gap discovery
  - Archive outdated validation_report (lines 139-247)

**4. New ADR Required**
- Create `docs/decisions/ADR-004-calculator-enhancement-strategy.md`
- Document gap analysis decision rationale
- Justify chosen implementation approach (will be created after gap analysis)
- Reference this sprint change proposal

### Repository Cleanup Task (NEW)

**Issue:** Root directory cluttered with debug scripts, log files, and superseded documentation making it difficult to see current project state.

**Actions Required:**
1. Create `docs/archive/` structure organized by date:
   - `2025-11-01-epic-2-initial/` (initial validation attempts)
   - `2025-11-16-validation-attempts/` (degraded corpus validation)
   - `2025-11-22-sprint-change/` (sprint change proposals)
   - `2025-11-25-story-2-9-handoff/` (Story 2.9 handoff)
   - `debug-scripts/` (all debug/test scripts from root)

2. Move superseded handoffs to archive:
   - `docs/HANDOFF-2025-11-01.md` → archive
   - `docs/HANDOFF-2025-11-25-STORY-2-9.md` → archive
   - Keep: `docs/HANDOFF-2025-11-27-TASK-6-BUGS-FIXED.md` (current)

3. Move old validation reports to archive:
   - All `docs/validation/*-2025-11-01.json/md/log` files
   - All `docs/validation/*-2025-11-16.json/md` files
   - All `docs/validation/*-2025-11-22.json` files
   - Keep: `docs/validation/realistic-validation-results.json` (current)

4. Move debug scripts from root to archive:
   - `_worker_epic2.py`, `debug_*.py`, `test_*.py`, `verify_*.py`

5. Move log files to `logs/` directory:
   - `baseline_*.log`, `*_output.log`, `epic2_validation_isolated.log`

6. Delete temporary files:
   - `docs/prep-sprint-status-temp.yaml`, `nul`, `test_raw.txt`

7. Update `.gitignore` to exclude `*.log` files in root

**Estimate:** 1-2 hours (can run parallel with gap analysis)
**Owner:** Developer (Amelia) or Scrum Master (Bob)

---

## 4. Path Forward Evaluation

### Option 1: Incremental Story Addition (NOT RECOMMENDED)

**Description:** Implement Story 2.9.1 (Spell/DOT) immediately, validate, discover what's next, repeat.

**Effort:** 20-80+ hours (HIGH UNCERTAINTY)
**Risk:** 🔴 **HIGH** - Unknown completion date, validation thrashing

**Pros:**
- ✅ Immediate implementation momentum
- ✅ Incremental progress visible

**Cons:**
- ❌ High risk of scope creep (could take 40-80+ hours)
- ❌ Multiple validation cycles waste time
- ❌ Pattern: Story 2.9 → bugs → spell gap → ??? gap
- ❌ Morale impact from repeated "done → not done" cycles

**Status:** ❌ **REJECTED** - Too uncertain, high risk

---

### Option 2: Rollback to Subprocess Approach

**Description:** Revert Story 2.9, implement external PoB subprocess for guaranteed accuracy.

**Effort:** 14-22 hours (rollback + subprocess implementation)
**Risk:** 🟡 **MEDIUM** - Architectural change, performance impact

**Pros:**
- ✅ Guaranteed complete coverage (ALL skill types)
- ✅ Known fixed scope
- ✅ No future gaps to discover

**Cons:**
- ❌ Throws away 26 hours of completed work
- ❌ Performance impact (subprocess overhead ~50-100ms)
- ❌ Morale impact from reversing "done" work
- ❌ Story 2.9's passive tree parsing is valuable

**Status:** ⚠️ **AVAILABLE** - As outcome of gap analysis if effort >40 hrs

---

### Option 3: Accept Attack Skills Only (NOT RECOMMENDED)

**Description:** Redefine Epic 2 scope to accept current limitations (attack skills only).

**Effort:** 5-8 hours (documentation updates)
**Risk:** 🟢 **LOW** (technical) / 🔴 **HIGH** (product)

**Pros:**
- ✅ Lowest technical effort
- ✅ Epic 2 can be marked complete quickly

**Cons:**
- ❌ **CRITICAL:** Optimizer only works for 20% of builds
- ❌ Product value severely diminished
- ❌ Epic 3 UI ships with "attack builds only" limitation
- ❌ Defeats MVP purpose (validate optimizer effectiveness)
- ❌ Delays problem - spell/DOT still needed eventually

**Status:** ❌ **REJECTED** - Unacceptable product quality

---

### Option 4: Comprehensive Gap Analysis First (RECOMMENDED)

**Description:** Execute systematic gap analysis (4-8 hours) to identify ALL missing components, then make informed decision about implementation approach.

**Effort:** 4-8 hours (analysis) + 12-40 hours (implementation based on findings)
**Risk:** 🟡 **MEDIUM** - Upfront analysis time, but eliminates uncertainty

**Why This Approach:**
1. **Eliminates Uncertainty:** 4-8 hour investment reveals TRUE scope
2. **Prevents Validation Thrashing:** Single informed decision vs repeated discovery cycles
3. **Preserves Flexibility:** Can choose incremental, hybrid, or subprocess based on facts
4. **Addresses Pattern Risk:** Reveals ALL gaps at once vs incremental discovery
5. **Aligns with Product Value:** Must support 70%+ of builds for Epic 2 validation

**Implementation Plan:**

**Phase 1: Gap Analysis (Story 2.9.x - 4-8 hours)**
1. Test all 15 realistic builds with detailed logging
2. Categorize failures by skill type (spell, DOT, minion, totem, etc.)
3. Identify root causes in MinimalCalc.lua for each failure category
4. Estimate effort for each fix category:
   - Low (<4 hrs): Simple data loading
   - Medium (4-8 hrs): Calculation logic implementation
   - High (8-16 hrs): Complex engine integration
   - Very High (16+ hrs): Architectural overhaul

**Phase 2: Decision Point (based on total effort)**
- **If ≤16 hours:** Implement Stories 2.9.1, 2.9.2 (incremental approach)
- **If 16-40 hours:** Implement hybrid (MinimalCalc for attacks, subprocess for spells)
- **If >40 hours:** Implement full subprocess (guaranteed coverage)

**Phase 3: Implementation (12-40 hours based on decision)**
- Execute selected approach
- Single validation cycle after all implementation complete
- Update documentation and create ADR-004

**Status:** ✅ **RECOMMENDED** - Approved by Alec

---

## 5. Recommended Approach

### Selected Path Forward

**Approach:** Comprehensive Gap Analysis → Informed Decision (Option 4)

**Justification:**

**Trade-offs Considered:**

| Factor | Incremental (No Analysis) | Gap Analysis First |
|--------|---------------------------|-------------------|
| **Time to Start Coding** | Immediate | 4-8 hrs delay |
| **Total Time to Complete** | 20-80+ hrs (uncertain) | 12-40 hrs (known) |
| **Risk of Rework** | 🔴 HIGH | 🟢 LOW |
| **Morale Impact** | 🔴 Repeated failures | 🟢 Clear path |
| **Product Quality** | ⚠️ Unknown | ✅ Guaranteed |

**Why Comprehensive Gap Analysis First:**

1. **Eliminates Uncertainty:** Upfront 4-8 hour investment reveals TRUE scope, prevents 20-80+ hours of incremental validation thrashing

2. **Preserves Flexibility:** Can choose incremental, hybrid, or subprocess based on FACTS, not committed to expensive approach if simple fix exists

3. **Addresses Pattern Risk:** Story 2.9 → bugs found → spell gap found → ??? (unknown). Gap analysis reveals ALL missing components at once

4. **Aligns with Product Value:** Must support 70%+ of builds for Epic 2 validation. Spell/DOT builds represent 80% of PoE 2

5. **Long-Term Sustainability:** Proper fix now vs band-aid approach. Avoids shipping technical debt. Enables confident Epic 3 launch

6. **Stakeholder Alignment:**
   - **Alec (Product Owner):** Needs working optimizer for all build types before Epic 3
   - **Developer:** Needs clear scope to avoid rework
   - **Business Value:** Epic 2 must validate optimizer effectiveness (blocked if limited to 20% of builds)

---

## 6. Implementation Plan

### Immediate Actions (Week 1)

**Story 2.9.x: Comprehensive Calculation Gap Analysis**
- **Owner:** Developer (Amelia)
- **Agent Command:** `/bmad:bmm:agents:dev`
- **Estimate:** 4-8 hours
- **Priority:** CRITICAL (blocks Epic 2 completion)

**Deliverable:** Gap analysis report documenting:
- All 15 builds tested with detailed failure categorization
- Root causes identified for each failure category
- Effort estimates for each fix category
- Decision matrix for selecting implementation approach

**Activities:**
1. Test all 15 realistic builds with MinimalCalc.lua
2. Log detailed output for each calculation
3. Categorize failures:
   - Spell skills (missing base damage, calculation logic)
   - DOT skills (missing DOT engine, tick rate calculations)
   - Minion builds (if any in corpus)
   - Totem/Trap/Mine (if any in corpus)
   - Complex interactions (conversions, penetration, etc.)
4. Identify root causes in MinimalCalc.lua:
   - Missing data files (spell gems, base damage tables)
   - Missing calculation functions (spell DPS formulas)
   - Missing engine components (DOT tick engine)
   - Architectural limitations (complex interactions)
5. Estimate effort for each category:
   - Low (<4 hrs): Data loading only
   - Medium (4-8 hrs): Calculation logic implementation
   - High (8-16 hrs): Engine integration
   - Very High (16+ hrs): Architectural overhaul
6. Create decision matrix and recommend approach

**Parallel Task: Repository Cleanup**
- **Owner:** Developer (Amelia) or Scrum Master (Bob)
- **Estimate:** 1-2 hours
- **Can run parallel** with gap analysis

**Deliverable:** Organized archive structure, clean root directory

---

### Decision Point (End of Week 1)

**Review Gap Analysis with Alec:**
- Present findings and categorized failures
- Present effort estimates for each approach
- Recommend implementation path based on decision matrix

**Select Implementation Approach:**

**Scenario A: Simple Fixes (Total Effort ≤16 hours)**
- **Stories:** 2.9.1 (Spell Base Damage), 2.9.2 (DOT Calculations)
- **Approach:** Extend MinimalCalc.lua incrementally
- **Timeline:** 1-2 weeks implementation

**Scenario B: Moderate Complexity (Total Effort 16-40 hours)**
- **Stories:** 2.9.1 (Hybrid Approach - Subprocess for Spells)
- **Approach:** Keep MinimalCalc for attacks, add subprocess wrapper for spells/DOT only
- **Timeline:** 2 weeks implementation

**Scenario C: Extensive Work (Total Effort >40 hours)**
- **Stories:** 2.9.1 (Full Subprocess Integration)
- **Approach:** Keep passive tree parsing, replace skill DPS calculation with external PoB subprocess
- **Timeline:** 2 weeks implementation

**Scrum Master Actions:**
- Create story files (2.9.1, 2.9.2+) based on selected approach
- Update sprint status files
- Mark stories ready for development

---

### Implementation Phase (Week 2-3)

**Execute Selected Approach:**
- Developer implements stories based on gap analysis decision
- Estimated time: 12-40 hours depending on scenario
- Daily progress updates to sprint status

**Success Criteria:**
- Implementation passes all integration tests
- Backward compatibility maintained (Epic 1 tests still pass)
- No performance regressions

---

### Validation Phase (End of Week 2-3)

**Task 6: Epic 2 Validation (Re-run)**
- **Owner:** TEA (Murat) + Developer (Amelia)
- **Agent Command:** `/bmad:bmm:agents:tea`
- **Estimate:** 2-3 hours

**Activities:**
1. Run validation script on full 15-build corpus
2. Verify success criteria:
   - ✅ Success rate ≥70% (builds calculate DPS)
   - ✅ Median improvement ≥5%
   - ✅ All completions <5 minutes
   - ✅ Zero budget constraint violations
3. Document results in `docs/validation/realistic-validation-results.json`
4. Generate validation report

**Pass Criteria:**
- All Epic 2 acceptance criteria validated
- Alec reviews and approves results

---

### Epic 2 Completion (Week 3-4)

**Epic 2 Retrospective**
- **Owner:** Scrum Master (Bob)
- **Agent Command:** `/bmad:bmm:agents:sm`
- **Estimate:** 1-2 hours

**Activities:**
1. Facilitate retrospective with all agents
2. Capture lessons learned:
   - Why did the calculator gap occur?
   - How can we prevent similar gaps in future epics?
   - What worked well in the correction process?
3. Document findings in `docs/retrospectives/epic-002-retro-2025-11-29.md`

**Epic 2 Closeout:**
- Update sprint status: Epic 2 → "done"
- Create final Epic 2 completion report
- Obtain Alec approval for Epic 3 launch

---

### Epic 3 Launch Preparation (Week 3-4)

**Tasks 7-10: Epic 3 Prep**
- Owner: Various agents
- Estimate: 6-8 hours
- Reference: `docs/prep-sprint-status.yaml`

**Activities:**
- Task 7: Requirements clarification
- Task 8: Risk mitigation planning
- Task 9: Test strategy
- Task 10: Update project documentation

**Epic 3 Launch:**
- Begin Story 3.1: Flask Web Server Setup
- Target: 2-4 weeks from today (2025-12-13 to 2025-12-27)

---

## 7. Agent Handoff and Responsibilities

### Change Scope Classification

**Scope:** 🟡 **MODERATE**
- Requires backlog reorganization and story creation
- Impacts Epic 2 completion timeline
- Does not require fundamental architecture replan

### Primary Handoff Recipients

**1. Developer Agent (Amelia) - PRIMARY OWNER**

**Agent Command:** `/bmad:bmm:agents:dev`

**Responsibilities:**
- Execute Story 2.9.x (Comprehensive Gap Analysis) - 4-8 hours
- Execute Stories 2.9.1, 2.9.2+ based on gap analysis findings - 12-40 hours
- Execute repository cleanup task - 1-2 hours (parallel)
- Update technical documentation (Story 2.9, tech spec)
- Create ADR-004 documenting enhancement strategy

**Deliverables:**
- `docs/validation/calculation-gap-analysis-2025-11-29.md` (gap analysis report)
- Implemented stories with code + tests
- Updated story files
- `docs/decisions/ADR-004-calculator-enhancement-strategy.md`
- Clean repository structure (`docs/archive/` organized)

---

**2. Scrum Master (Bob) - COORDINATION OWNER**

**Agent Command:** `/bmad:bmm:agents:sm`

**Responsibilities:**
- Update sprint status files (`docs/sprint-status.yaml`, `docs/prep-sprint-status.yaml`)
- Create Stories 2.9.1, 2.9.2+ based on gap analysis findings
- Mark Story 2.9.x ready for development after gap analysis plan approved
- Coordinate Epic 2 validation (Task 6) re-run
- Facilitate Epic 2 retrospective after validation

**Deliverables:**
- Updated sprint status files
- New story markdown files (2.9.1, 2.9.2+)
- `docs/retrospectives/epic-002-retro-2025-11-29.md`

---

**3. Test Engineer Architect (Murat) - VALIDATION OWNER**

**Agent Command:** `/bmad:bmm:agents:tea`

**Responsibilities:**
- Support gap analysis with testing guidance
- Execute Task 6 (Epic 2 Validation) re-run after implementation
- Verify ≥70% success rate, ≥5% median improvement
- Document validation results

**Deliverables:**
- Updated `docs/validation/realistic-validation-results.json`
- Validation report documenting Epic 2 success

---

**4. Product Owner (Alec) - APPROVAL AUTHORITY**

**Decision Points:**
- Gap analysis findings review (end of Week 1)
- Implementation approach selection (incremental/hybrid/subprocess)
- Epic 2 validation results approval
- Epic 3 launch approval

---

### Handoff Sequence

```
1. Scrum Master (Bob) - NOW
   ↓ Creates Story 2.9.x, updates sprint status

2. Developer (Amelia) - Week 1
   ↓ Executes gap analysis (4-8 hrs)
   ↓ Executes repository cleanup (1-2 hrs, parallel)

3. Product Owner (Alec) - End of Week 1
   ↓ Reviews findings, approves approach

4. Scrum Master (Bob) - End of Week 1
   ↓ Creates Stories 2.9.1, 2.9.2+ based on decision

5. Developer (Amelia) - Week 2-3
   ↓ Implements stories (12-40 hrs)

6. TEA (Murat) + Developer (Amelia) - End of Week 2-3
   ↓ Re-run Task 6 validation (2-3 hrs)

7. Scrum Master (Bob) - Week 3
   ↓ Facilitates Epic 2 retrospective

8. Product Owner (Alec) - Week 3-4
   ↓ Approves Epic 3 launch

9. Epic 3 Launch - Week 4+
```

---

### Success Criteria

**Story 2.9.x Complete When:**
- [ ] All 15 builds tested with detailed failure categorization
- [ ] Root causes identified for each failure category
- [ ] Effort estimates documented for each fix
- [ ] Decision matrix created (incremental/hybrid/subprocess)
- [ ] Gap analysis report reviewed and approved by Alec

**Stories 2.9.1+ Complete When:**
- [ ] Implementation passes all integration tests
- [ ] Task 6 validation achieves ≥70% success rate
- [ ] Task 6 validation achieves ≥5% median improvement
- [ ] All budget constraints validated (zero violations)
- [ ] Documentation updated (story files, tech spec, ADR-004)
- [ ] Repository cleaned and organized

**Epic 2 Complete When:**
- [ ] All Epic 2 acceptance criteria validated
- [ ] Epic 2 retrospective completed
- [ ] Epic 3 launch approved by Alec

---

## 8. Risk Assessment

### Identified Risks

**Risk 1: Gap Analysis Reveals >40 Hours of Work**
- **Probability:** Medium
- **Impact:** High (2-3 week delay)
- **Mitigation:** Subprocess approach available as alternative, guaranteed coverage
- **Contingency:** Hybrid approach (subprocess for spells only) balances effort and performance

**Risk 2: Unknown Skill Types in Test Corpus**
- **Probability:** Medium
- **Impact:** Medium (additional effort if minion/totem builds present)
- **Mitigation:** Gap analysis will reveal all skill types in corpus
- **Contingency:** Can adjust decision based on skill type distribution

**Risk 3: Performance Impact from Subprocess Approach**
- **Probability:** Low (only if >40 hrs effort triggers this path)
- **Impact:** Medium (50-100ms overhead per calculation)
- **Mitigation:** Hybrid approach keeps fast path for attacks
- **Contingency:** Acceptable trade-off for guaranteed accuracy

**Risk 4: Morale Impact from Extended Timeline**
- **Probability:** Low (Alec approved "quality over speed")
- **Impact:** Low
- **Mitigation:** Clear communication, single informed decision prevents thrashing
- **Contingency:** Visible progress with gap analysis report and implementation milestones

### Risk Acceptance

**Alec has approved the following:**
- ✅ 1-3 week timeline delay for quality
- ✅ Comprehensive gap analysis approach
- ✅ Decision framework for implementation selection
- ✅ No concerns about proposed plan

---

## 9. Timeline and Milestones

### Critical Path

| Milestone | Owner | Duration | Target Date |
|-----------|-------|----------|-------------|
| Sprint Change Proposal Approved | Bob (SM) | - | 2025-11-29 ✅ |
| Story 2.9.x Created | Bob (SM) | 1 hour | 2025-11-29 |
| Gap Analysis Complete | Amelia (Dev) | 4-8 hours | 2025-12-02 |
| Repository Cleanup Complete | Amelia/Bob | 1-2 hours | 2025-12-02 |
| Implementation Approach Decided | Alec (PO) | - | 2025-12-02 |
| Stories 2.9.1+ Created | Bob (SM) | 2 hours | 2025-12-03 |
| Implementation Complete | Amelia (Dev) | 12-40 hours | 2025-12-06 to 2025-12-13 |
| Task 6 Validation Complete | Murat/Amelia | 2-3 hours | 2025-12-13 |
| Epic 2 Retrospective | Bob (SM) | 1-2 hours | 2025-12-13 |
| Epic 2 Complete | Team | - | 2025-12-13 |
| Epic 3 Launch | Team | - | 2025-12-13 to 2025-12-20 |

### Best/Expected/Worst Case Timelines

**Best Case (≤16 hours effort):**
- Epic 2 complete: 2025-12-06
- Epic 3 launch: 2025-12-06
- **Total delay: ~1 week**

**Expected Case (16-40 hours effort):**
- Epic 2 complete: 2025-12-13
- Epic 3 launch: 2025-12-13
- **Total delay: ~2 weeks**

**Worst Case (>40 hours effort):**
- Epic 2 complete: 2025-12-20
- Epic 3 launch: 2025-12-20
- **Total delay: ~3 weeks**

---

## 10. Approval and Sign-Off

**Product Owner Approval:** ✅ **APPROVED by Alec on 2025-11-29**

**Approved Items:**
1. ✅ Story 2.9.x (Comprehensive Gap Analysis) as immediate next action
2. ✅ Decision framework for implementation approach selection
3. ✅ Timeline impact (1-3 weeks, quality over speed)
4. ✅ Repository cleanup task
5. ✅ Complete implementation plan and handoff strategy

**Approval Statement:**
> "1: Yes, 2: Yes, 3: Yes - QUALITY over speed, 4: No concerns. Approved"
> — Alec, 2025-11-29

**Next Steps:**
1. Scrum Master creates Story 2.9.x and updates sprint status
2. Developer begins gap analysis (Week 1)
3. Decision point at end of Week 1 to select implementation approach
4. Implementation and validation (Weeks 2-3)
5. Epic 2 retrospective and Epic 3 launch (Week 3-4)

---

## 11. References

**Related Documents:**
- Story 2.9: `docs/stories/2-9-integrate-full-pob-calculation-engine.md`
- Task 6 Bug Fix Handoff: `docs/HANDOFF-2025-11-27-TASK-6-BUGS-FIXED.md`
- Epic 2 Tech Spec: `docs/tech-spec-epic-2.md`
- Sprint Status: `docs/sprint-status.yaml`
- Prep Sprint Status: `docs/prep-sprint-status.yaml`
- Epic 2 Retrospective (previous): `docs/retrospectives/epic-002-retro-2025-10-31.md`

**Sprint Change Proposals (Previous):**
- `docs/sprint-change-proposal-2025-11-22.md` (Story 2.9 creation decision)
- `docs/sprint-change-proposal-2025-11-22-v2.md` (revision)

**ADRs Referenced:**
- ADR-003: Windows LuaJIT Fatal Exception Mitigation (process isolation via pytest-xdist)

**ADRs To Be Created:**
- ADR-004: Calculator Enhancement Strategy (after gap analysis)

---

**End of Sprint Change Proposal**

**Generated by:** Bob (Scrum Master) via Correct Course Workflow
**Date:** 2025-11-29
**Status:** APPROVED and ready for implementation
