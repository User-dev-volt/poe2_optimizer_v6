# Epic Alignment Matrix

**Project:** poe2_optimizer_v6
**Date:** 2025-10-10
**Purpose:** Map epics to architectural components, FRs, and stories for implementation planning

---

## Matrix Overview

This document provides a comprehensive mapping between:
- **3 Epics** (from PRD.md)
- **Architectural Components** (from solution-architecture-complete.md)
- **22 Functional Requirements** (from PRD.md)
- **31 User Stories** (estimated from epic breakdown)

**Use this matrix to:**
1. Understand which components implement which epics
2. Track epic-level progress during implementation
3. Identify component dependencies
4. Plan parallel development workstreams

---

## Epic 1: Foundation - PoB Calculation Engine Integration

### Epic Overview

**Goal:** Enable accurate PoB calculations in headless Python environment

**Success Criteria:**
- 100 sample builds calculated with 100% success rate
- <100ms per calculation (single)
- 150-500ms for 1000 calculations (batch)
- ±0.1% accuracy vs PoB GUI

**Story Count:** 8-10 stories
**Estimated Story Points:** ~25-30 points
**Duration:** Weeks 1-2

---

### Component Mapping

| Component | Responsibility | Files | Lines Est. |
|-----------|---------------|-------|------------|
| **parsers/** | PoB code encoding/decoding | `pob_parser.py`, `pob_generator.py`, `xml_utils.py`, `exceptions.py` | ~500 lines |
| **calculator/** | Python-Lua bridge for PoB calculations | `pob_engine.py`, `stub_functions.py`, `passive_tree.py`, `build_calculator.py` | ~800 lines |
| **models/** | Data structures for builds and stats | `build_data.py`, `build_stats.py` | ~200 lines |
| **utils/** | Shared utilities | `logging_config.py`, `performance.py` | ~150 lines |
| **external/pob-engine/** | Path of Building (Git submodule) | HeadlessWrapper.lua, PassiveTree.lua, CalcPerform.lua, etc. | Read-only |
| **tests/unit/** | Unit tests for parsers | `test_pob_parser.py`, `test_pob_generator.py` | ~400 lines |
| **tests/integration/** | Integration tests for calculator | `test_pob_engine_integration.py` | ~300 lines |

**Total Implementation:** ~2,350 lines (excluding tests)

---

### FR Mapping

| FR | Description | Component | Priority |
|----|-------------|-----------|----------|
| FR-1.2 | PoB Code Parsing & Decoding | `parsers/pob_parser.py` | P0 - Critical |
| FR-3.1 | Lupa + HeadlessWrapper Integration | `calculator/pob_engine.py`, `calculator/stub_functions.py` | P0 - Critical |
| FR-3.2 | Build State Calculation | `calculator/build_calculator.py`, `calculator/pob_engine.py` | P0 - Critical |
| FR-3.3 | Batch Calculation Performance | `calculator/pob_engine.py` (thread-local engines, lazy init) | P1 - High |
| FR-3.4 | Calculation Timeout & Error Recovery | `calculator/pob_engine.py` (error handling wrappers) | P1 - High |
| FR-3.5 | Multi-User Session Isolation | Thread-local engine pattern in `calculator/pob_engine.py` | P1 - High |
| FR-5.2 | Optimized PoB Code Generation | `parsers/pob_generator.py` | P1 - High |
| FR-5.5 | Round-Trip Validation | `parsers/pob_generator.py` (generate → parse → validate) | P2 - Medium |

---

### Story Breakdown

| Story | Description | Component | Est. Points | Dependencies |
|-------|-------------|-----------|-------------|--------------|
| **E1-S1** | Parse PoB code from Base64 to BuildData | `parsers/pob_parser.py` | 3 | None |
| **E1-S2** | Generate PoB code from BuildData to Base64 | `parsers/pob_generator.py` | 3 | E1-S1 |
| **E1-S3** | Implement Python stub functions (Deflate, Inflate, ConPrintf) | `calculator/stub_functions.py` | 2 | None |
| **E1-S4** | Load HeadlessWrapper.lua via Lupa | `calculator/pob_engine.py` | 5 | E1-S3 |
| **E1-S5** | Calculate build stats (DPS, EHP) for single build | `calculator/build_calculator.py` | 5 | E1-S4 |
| **E1-S6** | Validate calculation accuracy (±0.1% vs PoB GUI) | Integration tests | 3 | E1-S5 |
| **E1-S7** | Optimize batch performance (<1s/1000 calculations) | `calculator/pob_engine.py` optimizations | 3 | E1-S6 |
| **E1-S8** | Handle calculation errors gracefully | `calculator/pob_engine.py` error handling | 2 | E1-S5 |
| **E1-S9** | Support concurrent sessions (10 users) | Thread-local engine pattern | 3 | E1-S7 |
| **E1-S10** | Round-trip validation (parse → generate → parse) | `parsers/pob_generator.py` tests | 2 | E1-S2 |

**Total Story Points:** 31 points

---

### Implementation Sequence

**Week 1: Parsing and Basic Integration**
```
Day 1-2: E1-S1 (Parse PoB codes)
Day 2-3: E1-S3 (Python stubs) + E1-S4 (Load HeadlessWrapper)
Day 4-5: E1-S5 (Single build calculation)
```

**Week 2: Performance and Reliability**
```
Day 1-2: E1-S6 (Accuracy validation) + E1-S7 (Batch performance)
Day 3: E1-S8 (Error handling)
Day 4: E1-S9 (Concurrent sessions)
Day 5: E1-S2 + E1-S10 (PoB code generation + round-trip validation)
```

---

## Epic 2: Core Optimization Engine

### Epic Overview

**Goal:** Implement hill climbing algorithm discovering superior passive tree configurations

**Success Criteria:**
- 8%+ median improvement on test builds
- 80%+ of non-optimal builds improved
- <5 minute completion time
- All trees remain valid (connected, within budget)

**Story Count:** 7-9 stories
**Estimated Story Points:** ~28-35 points
**Duration:** Weeks 3-4

---

### Component Mapping

| Component | Responsibility | Files | Lines Est. |
|-----------|---------------|-------|------------|
| **optimizer/** | Hill climbing algorithm | `hill_climbing.py`, `tree_validator.py`, `neighbor_generator.py`, `budget_tracker.py`, `convergence.py` | ~1,000 lines |
| **calculator/** | Passive tree graph loading | `passive_tree.py` (load PassiveTree.lua, build adjacency list) | ~300 lines |
| **models/** | Optimization configuration | `optimization_config.py` (OptimizationGoal enum, config dataclass) | ~100 lines |
| **tests/unit/** | Unit tests for optimizer | `test_hill_climbing.py`, `test_tree_validator.py`, `test_budget_tracker.py` | ~600 lines |
| **tests/integration/** | Integration tests | `test_optimization_pipeline.py` | ~400 lines |

**Total Implementation:** ~1,400 lines (excluding tests)

---

### FR Mapping

| FR | Description | Component | Priority |
|----|-------------|-----------|----------|
| FR-2.1 | Optimization Goal Dropdown | `models/optimization_config.py` (OptimizationGoal enum) | P0 - Critical |
| FR-2.2 | Budget Constraint (Dual Budget) | `optimizer/budget_tracker.py` | P0 - Critical |
| FR-4.1 | Hill Climbing Algorithm (MVP) | `optimizer/hill_climbing.py` | P0 - Critical |
| FR-4.2 | Tree Connectivity Validation | `optimizer/tree_validator.py` (BFS implementation) | P0 - Critical |
| FR-4.3 | Budget Enforcement (Dual Constraint) | `optimizer/budget_tracker.py` | P0 - Critical |
| FR-4.5 | Optimization Quality Confidence Score | `optimizer/hill_climbing.py` (verification calculation) | P1 - High |

---

### Story Breakdown

| Story | Description | Component | Est. Points | Dependencies |
|-------|-------------|-----------|-------------|--------------|
| **E2-S1** | Load passive tree graph from PoB (PassiveTree.lua) | `calculator/passive_tree.py` | 5 | Epic 1 complete |
| **E2-S2** | Build adjacency list for tree graph | `calculator/passive_tree.py` | 3 | E2-S1 |
| **E2-S3** | Validate tree connectivity using BFS | `optimizer/tree_validator.py` | 5 | E2-S2 |
| **E2-S4** | Generate neighbor trees (±1 node changes) | `optimizer/neighbor_generator.py` | 4 | E2-S3 |
| **E2-S5** | Implement hill climbing main loop | `optimizer/hill_climbing.py` | 5 | E2-S4 |
| **E2-S6** | Track and enforce dual budget constraints | `optimizer/budget_tracker.py` | 4 | E2-S5 |
| **E2-S7** | Detect convergence (no improvement for 50 iterations) | `optimizer/convergence.py` | 3 | E2-S5 |
| **E2-S8** | Implement objective functions (DPS/EHP/Balanced) | `optimizer/hill_climbing.py` | 3 | E2-S5 |
| **E2-S9** | Verify optimization quality (round-trip calculation) | `optimizer/hill_climbing.py` | 3 | E2-S5 |

**Total Story Points:** 35 points

---

### Implementation Sequence

**Week 3: Tree Validation and Neighbor Generation**
```
Day 1-2: E2-S1 + E2-S2 (Load passive tree, build graph)
Day 3-4: E2-S3 (BFS connectivity validation)
Day 5: E2-S4 (Neighbor generation)
```

**Week 4: Optimization Algorithm**
```
Day 1-2: E2-S5 (Hill climbing main loop)
Day 3: E2-S6 (Budget tracking) + E2-S8 (Objective functions)
Day 4: E2-S7 (Convergence detection) + E2-S9 (Quality verification)
Day 5: Integration testing and optimization tuning
```

---

## Epic 3: User Experience & Local Reliability

### Epic Overview

**Goal:** Deliver complete local web UI with robust error handling and resource management

**Success Criteria:**
- 95%+ parse success rate
- Clear error messages for all failure modes
- 50+ consecutive optimizations without memory leaks
- Real-time progress updates (every 2s)

**Story Count:** 10-12 stories
**Estimated Story Points:** ~35-40 points
**Duration:** Weeks 5-6

---

### Component Mapping

| Component | Responsibility | Files | Lines Est. |
|-----------|---------------|-------|------------|
| **web/** | Flask application layer | `app.py`, `routes.py`, `sse.py`, `session_manager.py`, `forms.py` | ~800 lines |
| **frontend/templates/** | HTML templates (Bootstrap 5) | `base.html`, `index.html`, `progress.html`, `results.html`, `error.html` | ~600 lines |
| **frontend/static/css/** | Custom styles | `custom.css` | ~150 lines |
| **frontend/static/js/** | JavaScript for interactivity | `progress.js`, `copy-code.js` | ~300 lines |
| **tests/e2e/** | End-to-end tests | `test_optimization_workflow.py` | ~400 lines |

**Total Implementation:** ~1,850 lines (excluding tests)

---

### FR Mapping

| FR | Description | Component | Priority |
|----|-------------|-----------|----------|
| FR-1.1 | PoB Code Input Interface | `frontend/templates/index.html` (Form UI) | P0 - Critical |
| FR-1.3 | Input Validation & Error Handling | `parsers/exceptions.py` + `frontend/templates/error.html` | P0 - Critical |
| FR-1.4 | Build Summary Display | `web/routes.py` (POST /optimize handler) | P1 - High |
| FR-1.5 | Version Compatibility Detection | `parsers/pob_parser.py` (integrated in Epic 1) | P1 - High |
| FR-1.6 | Unsupported Build Type Detection | `parsers/pob_parser.py` (integrated in Epic 1) | P2 - Medium |
| FR-1.7 | Accessibility (WCAG 2.1 AA) | `frontend/templates/` (Bootstrap 5, semantic HTML) | P1 - High |
| FR-2.1 | Optimization Goal Dropdown | `frontend/templates/index.html` (Form UI) | P0 - Critical |
| FR-2.2 | Budget Constraint Input | `frontend/templates/index.html` (Dual budget inputs) | P0 - Critical |
| FR-4.4 | Real-Time Progress Reporting | `web/sse.py` + `frontend/static/js/progress.js` (SSE streaming) | P0 - Critical |
| FR-4.6 | Optimization Cancellation | `web/session_manager.py` + `frontend/templates/progress.html` | P1 - High |
| FR-5.1 | Before/After Comparison | `frontend/templates/results.html` | P0 - Critical |
| FR-5.3 | Change Visualization | `frontend/templates/results.html` (Node lists) | P1 - High |
| FR-5.4 | Verification Instructions | `frontend/templates/results.html` (Step-by-step guide) | P2 - Medium |
| FR-6.1 | File-Based Error Logging | `utils/logging_config.py` (integrated in Epic 1) | P1 - High |

---

### Story Breakdown

| Story | Description | Component | Est. Points | Dependencies |
|-------|-------------|-----------|-------------|--------------|
| **E3-S1** | Create Flask application structure | `web/app.py` (Flask app factory) | 2 | None |
| **E3-S2** | Implement home page with form | `frontend/templates/index.html` + `web/routes.py` | 3 | E3-S1 |
| **E3-S3** | Add goal selection dropdown | `frontend/templates/index.html` (FR-2.1) | 2 | E3-S2 |
| **E3-S4** | Add budget input (dual budget: unallocated + respec) | `frontend/templates/index.html` (FR-2.2) | 3 | E3-S2 |
| **E3-S5** | Handle PoB code submission (create session, start thread) | `web/routes.py` POST /optimize | 4 | E3-S2, Epic 1, Epic 2 |
| **E3-S6** | Display build summary after parsing | `web/routes.py` + build validation (FR-1.4) | 3 | E3-S5 |
| **E3-S7** | Implement SSE progress streaming | `web/sse.py` (FR-4.4) | 5 | E3-S5 |
| **E3-S8** | Create progress page with real-time updates | `frontend/templates/progress.html` + `frontend/static/js/progress.js` | 4 | E3-S7 |
| **E3-S9** | Display optimization results (before/after comparison) | `frontend/templates/results.html` (FR-5.1, FR-5.3) | 4 | E3-S5, Epic 2 |
| **E3-S10** | Add copy PoB code button | `frontend/static/js/copy-code.js` | 2 | E3-S9 |
| **E3-S11** | Implement optimization cancellation | `web/session_manager.py` cleanup (FR-4.6) | 3 | E3-S7 |
| **E3-S12** | Add structured error pages | `frontend/templates/error.html` (FR-1.3) | 2 | E3-S2 |

**Total Story Points:** 37 points

---

### Implementation Sequence

**Week 5: Flask Application and Basic UI**
```
Day 1: E3-S1 + E3-S2 (Flask app + home page)
Day 2: E3-S3 + E3-S4 (Goal dropdown + budget inputs)
Day 3: E3-S5 (PoB code submission, session creation)
Day 4: E3-S6 + E3-S12 (Build summary + error pages)
Day 5: E3-S7 start (SSE progress streaming)
```

**Week 6: Progress Reporting and Results Display**
```
Day 1: E3-S7 complete + E3-S8 (SSE progress + progress page)
Day 2: E3-S9 (Results display)
Day 3: E3-S10 + E3-S11 (Copy button + cancellation)
Day 4-5: E2E testing, bug fixes, polish
```

---

## Cross-Epic Dependencies

### Epic 1 → Epic 2 Dependencies

| Epic 1 Deliverable | Epic 2 Requirement |
|--------------------|---------------------|
| `parsers/pob_parser.py` (parse PoB codes) | `optimizer/hill_climbing.py` needs BuildData input |
| `calculator/build_calculator.py` (calculate stats) | `optimizer/hill_climbing.py` calls for each candidate tree |
| `calculator/passive_tree.py` (passive tree graph) | `optimizer/tree_validator.py` needs adjacency list for BFS |
| `models/build_data.py` (BuildData dataclass) | `optimizer/` uses BuildData throughout |

**Blocker:** Epic 2 **CANNOT START** until Epic 1 delivers:
- Working PoB parser (E1-S1)
- Working stat calculator (E1-S5)
- Passive tree graph loader (E1-S1, extracted as separate story in E2-S1)

---

### Epic 2 → Epic 3 Dependencies

| Epic 2 Deliverable | Epic 3 Requirement |
|--------------------|---------------------|
| `optimizer/hill_climbing.py` (optimization algorithm) | `web/routes.py` POST /optimize calls optimization in background thread |
| `optimizer/hill_climbing.py` progress updates | `web/sse.py` streams progress to browser |
| Optimized BuildData result | `parsers/pob_generator.py` generates new PoB code for display |
| `models/optimization_config.py` | `web/routes.py` validates form inputs against this model |

**Blocker:** Epic 3 **CANNOT START** until Epic 2 delivers:
- Working optimization algorithm (E2-S5)
- Progress update mechanism (part of E2-S5)

---

### Epic 1 → Epic 3 Dependencies

| Epic 1 Deliverable | Epic 3 Requirement |
|--------------------|---------------------|
| `parsers/pob_parser.py` | `web/routes.py` POST /optimize parses user input |
| `parsers/pob_generator.py` | `web/routes.py` GET /results generates optimized PoB code |
| `parsers/exceptions.py` | `web/routes.py` catches parse errors, renders structured error pages |
| `models/build_data.py` | `web/routes.py` passes BuildData between components |

**Blocker:** Epic 3 web routes **DEPEND ON** Epic 1 parsers for input/output.

---

## Parallel Development Opportunities

### Week 1-2 (Epic 1 Development)

**Parallel Workstreams:**

**Team A: Parsers (E1-S1, E1-S2, E1-S10)**
- Can work independently on PoB code parsing/generation
- No PoB engine dependency yet
- Testable with sample PoB codes

**Team B: Lupa Integration (E1-S3, E1-S4, E1-S5)**
- Requires PoB engine (Git submodule initialized first)
- Can work in parallel with Team A
- Integration happens at end of Week 2

**Team C: Frontend Prototype (Epic 3 early start)**
- Can start E3-S1, E3-S2 (Flask app skeleton, home page)
- Mock data for testing
- Does NOT depend on Epic 1 completion

---

### Week 3-4 (Epic 2 Development)

**Parallel Workstreams:**

**Team A: Tree Validation (E2-S1, E2-S2, E2-S3)**
- Depends on Epic 1 `calculator/passive_tree.py`
- Can work independently once tree loading complete

**Team B: Optimization Algorithm (E2-S4, E2-S5, E2-S6)**
- Depends on E2-S3 (tree validator)
- Can mock calculator for early testing
- Integration testing at end

**Team C: Frontend Continuation (E3-S3, E3-S4, E3-S5 start)**
- Can continue Epic 3 work in parallel
- Mock optimization for testing
- Integration happens Week 5

---

### Week 5-6 (Epic 3 Completion)

**Serial Work:** Epic 3 requires both Epic 1 and Epic 2 complete for full integration.

**Parallel Workstreams:**

**Team A: SSE Progress (E3-S7, E3-S8)**
- Can work independently on SSE mechanism
- Mock progress updates for testing

**Team B: Results Display (E3-S9, E3-S10)**
- Depends on Epic 2 results
- Can mock result data for UI development

**Team C: Polish (E3-S11, E3-S12 + E2E tests)**
- Error handling, cancellation, testing
- Can work in parallel with A and B

---

## Testing Strategy by Epic

### Epic 1 Testing

**Unit Tests:**
- `tests/unit/test_pob_parser.py` - Valid codes, invalid codes, edge cases
- `tests/unit/test_pob_generator.py` - Round-trip validation

**Integration Tests:**
- `tests/integration/test_pob_engine_integration.py` - Real PoB engine, accuracy validation
- `tests/integration/test_batch_performance.py` - Performance testing (1000 calcs <1s)

**Test Coverage Target:** >90% (critical path)

---

### Epic 2 Testing

**Unit Tests:**
- `tests/unit/test_tree_validator.py` - Connected trees, disconnected trees
- `tests/unit/test_hill_climbing.py` - Mock calculator, algorithm logic
- `tests/unit/test_budget_tracker.py` - Budget enforcement edge cases

**Integration Tests:**
- `tests/integration/test_optimization_pipeline.py` - Full optimization with real calculator

**Test Coverage Target:** >85%

---

### Epic 3 Testing

**Unit Tests:**
- Minimal (mostly UI, not heavily unit-tested)

**Integration Tests:**
- `tests/integration/test_session_management.py` - Concurrent sessions, cleanup

**E2E Tests:**
- `tests/e2e/test_optimization_workflow.py` - Full workflow: submit → progress → results

**Test Coverage Target:** >70% (UI less critical than business logic)

---

## Success Metrics by Epic

### Epic 1 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Parse Success Rate | 95%+ | Test with 100 sample PoB codes |
| Calculation Accuracy | ±0.1% vs PoB GUI | Compare with known builds |
| Single Calc Performance | <100ms | Performance benchmarks |
| Batch Calc Performance | <1s for 1000 | Performance benchmarks |
| Round-Trip Success Rate | 100% | Generate → parse → compare |

---

### Epic 2 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Median Improvement | 8%+ | Test with 20+ sample builds |
| Improvement Rate | 80%+ of non-optimal builds | Test with varied builds |
| Tree Validity Rate | 100% | All outputs importable to PoB |
| Optimization Completion Time | <5 minutes | Measure on complex builds |
| Budget Enforcement | 100% | Never exceed constraints |

---

### Epic 3 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| First-Time Success Rate | 80%+ | User testing (submit code → see results) |
| Error Message Clarity | 90%+ users understand | User testing feedback |
| Progress Update Latency | <10s lag max | SSE testing |
| Memory Leak Rate | 0 | 50+ consecutive optimizations |
| Cancellation Success Rate | 100% | Cancel at various stages |

---

## Conclusion

**Total Epic Alignment:**
- **Epic 1:** 4 components, 8 FRs, 10 stories → ~2,350 lines
- **Epic 2:** 3 components, 6 FRs, 9 stories → ~1,400 lines
- **Epic 3:** 3 components, 14 FRs, 12 stories → ~1,850 lines

**Total Implementation:** ~5,600 lines of production code (excluding tests)

**Critical Path:**
```
Epic 1 (Weeks 1-2) → Epic 2 (Weeks 3-4) → Epic 3 (Weeks 5-6)
```

**Parallel Development:**
- Week 1-2: Parsers (Team A) + Lupa Integration (Team B) + Frontend skeleton (Team C)
- Week 3-4: Tree validation (Team A) + Optimization algorithm (Team B) + Frontend forms (Team C)
- Week 5-6: Full integration and E2E testing

**Overall Readiness:** ✅ **100% - ALL EPICS READY FOR IMPLEMENTATION**

---

**Document Generated:** 2025-10-10
**Author:** Winston (System Architect)

---

_End of Epic Alignment Matrix_
