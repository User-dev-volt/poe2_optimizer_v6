# poe2_optimizer_v6 — BMAD Index

> Links to all BMAD artifacts for this project.

**Project:** PoE 2 Passive Tree Optimizer
**Method:** BMAD (agents: dev, sm, pm, architect, tea)

---

## Core Documents

| Document | Description | Status |
|----------|-------------|--------|
| [[10_Active_Projects/poe2_optimizer_v6/docs/PRD.md\|PRD]] | Product Requirements Document | Complete |
| [[10_Active_Projects/poe2_optimizer_v6/docs/epics.md\|Epics]] | Epic breakdown (3 epics, 25-31 stories) | Complete |
| [[10_Active_Projects/poe2_optimizer_v6/docs/solution-architecture.md\|Architecture]] | Solution architecture | Complete |
| [[10_Active_Projects/poe2_optimizer_v6/docs/backlog.md\|Backlog]] | Full backlog | Active |

---

## Epics

### Epic 1: Foundation - PoB Integration
**Status:** COMPLETE (Oct 2025)
**Stories:** 8 stories (1.1 - 1.8)

| Story | Title | Status |
|-------|-------|--------|
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/story-1.1.md\|1.1]] | Parse PoB Import Code | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/story-1.2.md\|1.2]] | Setup Lupa + LuaJIT Runtime | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/story-1.3.md\|1.3]] | Load PoB Data Files | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/story-1.4.md\|1.4]] | Execute HeadlessWrapper.lua | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/story-1.5.md\|1.5]] | Calculate Build Stats | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/story-1.6.md\|1.6]] | Validate Calculation Accuracy | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/story-1.7.md\|1.7]] | Performance Optimization | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/story-1.8.md\|1.8]] | Error Handling | Done |

---

### Epic 2: Core Optimization Engine
**Status:** IN PROGRESS
**Stories:** 9 stories (2.1 - 2.9)

| Story | Title | Status |
|-------|-------|--------|
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-1-implement-hill-climbing-core-algorithm.md\|2.1]] | Hill Climbing Core Algorithm | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-2-generate-neighbor-configurations-1-hop-moves.md\|2.2]] | Generate Neighbor Configurations | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-3-auto-detect-unallocated-passive-points.md\|2.3]] | Auto-detect Unallocated Points | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-4-implement-dual-budget-constraint-tracking.md\|2.4]] | Dual Budget Constraint Tracking | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-5-implement-budget-prioritization-free-first-strategy.md\|2.5]] | Budget Prioritization | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-6-metric-selection-and-evaluation.md\|2.6]] | Metric Selection & Evaluation | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-7-convergence-detection.md\|2.7]] | Convergence Detection | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-8-optimization-progress-tracking.md\|2.8]] | Progress Tracking | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-9-integrate-full-pob-calculation-engine.md\|2.9]] | Full PoB Calculation Engine | Split |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-9-1-hybrid-calculation-approach.md\|2.9.1]] | Hybrid Calculation Approach | Done |
| [[10_Active_Projects/poe2_optimizer_v6/docs/stories/2-9-2-spell-dot-minimalcalc-enhancement.md\|2.9.2]] | Spell/DOT MinimalCalc Enhancement | **Review** |

---

### Epic 3: UX & Local Reliability
**Status:** NOT STARTED
**Stories:** 10-12 stories (planned)

- Flask web UI at localhost:5000
- Complete user workflow
- Error handling, progress tracking, resource cleanup

---

## Architecture & Decisions

| Document | Description |
|----------|-------------|
| [[10_Active_Projects/poe2_optimizer_v6/docs/architecture/epic-2-optimizer-design.md\|Epic 2 Design]] | Optimizer architecture |
| [[10_Active_Projects/poe2_optimizer_v6/docs/architecture/epic-3-web-architecture.md\|Epic 3 Design]] | Web UI architecture |
| [[10_Active_Projects/poe2_optimizer_v6/docs/decisions/ADR-003-windows-luajit-cleanup-mitigation.md\|ADR-003]] | Windows LuaJIT cleanup mitigation |
| [[10_Active_Projects/poe2_optimizer_v6/docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md\|ADR-004]] | Global.lua nil-safety patch |

---

## Retrospectives

| Epic | Date | Link |
|------|------|------|
| Epic 1 | 2025-10-27 | [[10_Active_Projects/poe2_optimizer_v6/docs/retrospectives/epic-001-retro-2025-10-27.md\|Retro]] |
| Epic 2 | 2025-10-31 | [[10_Active_Projects/poe2_optimizer_v6/docs/retrospectives/epic-002-retro-2025-10-31.md\|Retro]] |

---

## Research

| Document | Topic |
|----------|-------|
| [[10_Active_Projects/poe2_optimizer_v6/docs/research/README-Research-Summary.md\|Summary]] | Research overview |
| [[10_Active_Projects/poe2_optimizer_v6/docs/research/LupaLibraryDeepResearch.md\|Lupa Deep Dive]] | LuaJIT integration |
| [[10_Active_Projects/poe2_optimizer_v6/docs/research/hill-climbing-strategy.md\|Hill Climbing]] | Optimization strategy |

---

## Handoffs

| Date | Context | Link |
|------|---------|------|
| 2025-11-29 | Story 2.9.x Complete | [[10_Active_Projects/poe2_optimizer_v6/docs/HANDOFF-2025-11-29-STORY-2.9.x-COMPLETE.md\|Handoff]] |
| 2025-11-27 | Task 6 Bugs Fixed | [[10_Active_Projects/poe2_optimizer_v6/docs/HANDOFF-2025-11-27-TASK-6-BUGS-FIXED.md\|Handoff]] |
| 2025-11-25 | Story 2.9 Started | [[10_Active_Projects/poe2_optimizer_v6/docs/HANDOFF-2025-11-25-STORY-2-9.md\|Handoff]] |
| 2025-11-01 | General | [[10_Active_Projects/poe2_optimizer_v6/docs/HANDOFF-2025-11-01.md\|Handoff]] |

---

## Links

- **Snapshot:** [[10_Active_Projects/poe2_optimizer_v6/Snapshot]]
- **Timeline:** [[10_Active_Projects/poe2_optimizer_v6/Timeline]]
- **Dashboard:** [[00_Meta/Dashboard]]
