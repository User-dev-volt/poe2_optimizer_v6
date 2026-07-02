# poe2_optimizer_v6 — Timeline

> Major milestones and decisions. The story of this project.

**Project:** PoE 2 Passive Tree Optimizer
**Started:** 2025-10-06
**Current Phase:** Epic 2 - Core Optimization Engine

---

## Milestone Summary

```
Epic 1: Foundation ━━━━━━━━━━━━━━━━━━━━ COMPLETE (Oct 2025)
Epic 2: Optimizer  ━━━━━━━━━━━━━━━━━━━━ IN PROGRESS (90.9%)
Epic 3: Web UI     ━━━━━━━━━━━━━━━━━━━━ NOT STARTED
```

---

## 2025-12 (Current)

### Dec 18 - Story 2.9.2 Test Validation Complete
- **Achievement:** 90.9% success rate (10/11 eligible builds)
- **Fixed:** Debug logging cleanup, Global.lua patch documented
- **Bonus:** Totem attack support implemented (Siege Ballista: 66.52 DPS)
- **Status:** Awaiting completion decision
- **Ref:** [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-9-2-spell-dot-minimalcalc-enhancement.md|Story 2.9.2]]

### Dec 4 - Senior Dev Review
- **Reviewer:** Alec
- **Outcome:** Changes Requested (2 HIGH blockers)
- **Blockers:** Debug logging in production, Global.lua patch risk
- **Ref:** Story 2.9.2 Review section

### Dec 3 - Spell Calculation Breakthrough
- **Achievement:** Spell base damage extraction working!
- **Results:** Fireball (32.99 DPS), Essence Drain (407.94 DPS)
- **Root Cause Found:** mainSocketGroup selection was incorrect
- **Ref:** [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-9-2-STATUS-REPORT.md|Status Report]]

---

## 2025-11

### Nov 29 - Story 2.9.1 Partial Completion
- **Achievement:** Hybrid calculation infrastructure complete
- **Results:** 4/15 weapon builds working (26.7%)
- **Decision:** Split into Story 2.9.1 (infrastructure) + 2.9.2 (spell calc)
- **Ref:** [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-9-1-hybrid-calculation-approach.md|Story 2.9.1]]

### Nov 27 - Task 6 Bugs Fixed
- **Ref:** [[10_Active_Projects/poe2_optimizer_v6/docs/HANDOFF-2025-11-27-TASK-6-BUGS-FIXED.md|Handoff]]

### Nov 25 - Story 2.9 Started
- **Goal:** Integrate full PoB calculation engine
- **Ref:** [[10_Active_Projects/poe2_optimizer_v6/docs/HANDOFF-2025-11-25-STORY-2-9.md|Handoff]]

---

## 2025-10

### Oct 31 - Epic 2 Retrospective
- **Ref:** [[10_Active_Projects/poe2_optimizer_v6/docs/retrospectives/epic-002-retro-2025-10-31.md|Retro]]

### Oct 27 - Epic 1 Complete + Retrospective
- **Achievement:** Foundation complete - PoB integration working
- **Success:** 100% calculation parity with PoB GUI
- **Ref:** [[10_Active_Projects/poe2_optimizer_v6/docs/retrospectives/epic-001-retro-2025-10-27.md|Retro]]

### Oct 8 - Project Kickoff
- **Created:** PRD, Epics, Initial architecture
- **Scope:** 3 Epics, 25-31 stories, 2 month target
- **Ref:** [[10_Active_Projects/poe2_optimizer_v6/docs/PRD.md|PRD]], [[10_Active_Projects/poe2_optimizer_v6/docs/epics.md|Epics]]

### Oct 6-7 - Research Phase
- **Activities:** Brainstorming, technical research, Lupa deep dive
- **Ref:** [[10_Active_Projects/poe2_optimizer_v6/docs/research/README-Research-Summary.md|Research Summary]]

---

## Key Decisions (ADRs)

| ID | Decision | Date | Impact |
|----|----------|------|--------|
| ADR-003 | Windows LuaJIT cleanup - accept as known limitation | Oct 2025 | Use pytest-xdist for isolation |
| ADR-004 | Global.lua nil-safety patch strategy | Dec 2025 | Document + patch file for updates |

---

## Links

- **Snapshot:** [[10_Active_Projects/poe2_optimizer_v6/Snapshot]]
- **BMAD Index:** [[10_Active_Projects/poe2_optimizer_v6/BMAD_Index]]
- **Dashboard:** [[00_Meta/Dashboard]]
