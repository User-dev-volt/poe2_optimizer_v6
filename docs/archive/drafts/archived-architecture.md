# Solution Architecture: PoE 2 Passive Tree Optimizer

**Project:** poe2_optimizer_v6
**Author:** Winston (System Architect)
**Date:** 2025-10-09
**Version:** 1.0 - Draft in Progress

---

## Prerequisites and Scale Assessment

### Project Classification
- **Project Level:** Level 3 (Full product - 12-40 stories, 2-5 epics)
- **Project Type:** Web application (local development, Flask at localhost:5000)
- **Field Type:** Greenfield (new project, no existing codebase)
- **UI Complexity:** Minimal (single-page interface)

### Prerequisites Validation

✅ **PRD Complete**
- Version: 1.1 (Post-Validation Edition)
- Status: COMPLETE for architecture handoff
- Content: Comprehensive FRs, NFRs, epics, and user stories

⚠️ **UX Spec Skipped**
- Rationale: UI is extremely minimal (text box, dropdown, button, results display)
- PRD contains sufficient UI detail for implementation
- Separate UX spec would add ceremony without value

✅ **Prerequisites Met - Proceeding with Solution Architecture Workflow**

---

## PRD and Requirements Analysis

### Document Overview
- **PRD Version:** 1.1 (Post-Validation Edition)
- **Total Requirements:** 22 Functional Requirements (FRs) + 9 Non-Functional Requirements (NFRs)
- **Epic Structure:** 3 major epics, 25-31 user stories, ~80 story points

### Product Summary

**"The PoE 2 Passive Tree Optimizer"** is a focused local web application that automatically discovers mathematically superior passive skill tree configurations for Path of Exile 2 builds. The tool transforms 3+ hours of manual passive tree experimentation into a 30-second to 5-minute automated optimization delivering verifiable 5-15% performance improvements.

**Core Differentiator:** Ruthless scope discipline - does ONE thing perfectly (passive tree optimization only) enabling a 2-month MVP vs. competitors' 12+ month "complete solutions".

**Deployment Model:** Local-only Flask application running at localhost:5000 for personal use and validation before any public release.

### Functional Requirements Summary

**FR Group 1: PoB Code Input & Validation (7 requirements)**
- FR-1.1: Large text input field accepting PoB codes up to 100KB
- FR-1.2: Base64 decode → zlib decompress → XML parsing
- FR-1.3: Structured error handling with user-friendly messages
- FR-1.4: Build summary display (class, level, ascendancy, DPS, EHP, passive point allocation)
- FR-1.5: Version compatibility detection (reject PoE 1 codes)
- FR-1.6: Unsupported build type detection (minions, totems, traps, mines, triggers)
- FR-1.7: WCAG 2.1 AA accessibility compliance

**FR Group 2: Optimization Goal Selection (2 requirements)**
- FR-2.1: Dropdown menu with 3 goals (Maximize DPS, Maximize EHP, Balanced)
- FR-2.2: Dual budget constraint system:
  - **Unallocated points** (free allocations, character level - allocated points)
  - **Respec points** (costly deallocations, requires in-game currency)

**FR Group 3: PoB Calculation Engine Integration (5 requirements)**
- FR-3.1: Lupa + HeadlessWrapper.lua integration with Python stub functions
- FR-3.2: Single build state calculation (DPS, EHP, resistances, life, ES, mana)
- FR-3.3: Batch calculation performance (1000 calculations in <1s, target 150-500ms)
- FR-3.4: Calculation timeout (5s per calculation) and error recovery
- FR-3.5: Multi-user session isolation (10 concurrent sessions, unique LuaRuntime per user)

**FR Group 4: Passive Tree Optimization Algorithm (6 requirements)**
- FR-4.1: Hill climbing algorithm (MVP)
- FR-4.2: Tree connectivity validation (all nodes connected to class starting position)
- FR-4.3: Dual budget enforcement (never exceed unallocated or respec point limits)
- FR-4.4: Real-time progress reporting (every 2s or 100 iterations)
- FR-4.5: Optimization quality confidence score (verification calculation)
- FR-4.6: Optimization cancellation with 2-second resource cleanup

**FR Group 5: Results Display & Export (5 requirements)**
- FR-5.1: Before/after comparison display (stats, improvements)
- FR-5.2: Optimized PoB code generation (Python → XML → zlib → Base64)
- FR-5.3: Change visualization (nodes added, removed, replaced with names)
- FR-5.4: Verification instructions for PoB GUI
- FR-5.5: Round-trip validation (parse generated code → recalculate → verify)

**FR Group 6: Analytics & Tracking (2 requirements)**
- FR-6.1: Usage analytics (optimization attempts, completion rate, average improvement)
- FR-6.2: Optional user feedback surveys

### Non-Functional Requirements Summary

**NFR-1: Performance**
- Page load: <2s, PoB parsing: <500ms, Optimization: <2-10 min depending on complexity
- Batch calculations: 1000 calcs in 150-500ms under normal load (1-5 concurrent users)
- Concurrent capacity: 10 simultaneous optimizations on 2-core, 4GB RAM VPS

**NFR-2: Reliability**
- 95% uptime, graceful failure handling, session isolation, round-trip validation, circuit breaker

**NFR-3: Security (Local Deployment)**
- Input sanitization, dependency scanning, no permanent storage, localhost binding, Lua timeouts

**NFR-4: Usability**
- First-time users complete workflow without docs, <30s submission time, NPS ≥40, WCAG 2.1 AA

**NFR-5: Maintainability**
- >80% test coverage, type hints (mypy), PEP 8 (black), modular architecture, ADRs

**NFR-6: Portability (Local MVP)**
- Python 3.10+ on developer's machine, modern browsers, cross-platform libraries preferred

**NFR-7: Compatibility**
- Pinned PoB commit hash, monthly PoB testing, PoB XML format support (Dec 2025)

**NFR-8: Compliance & Legal**
- MIT License, data minimization, no permanent storage, clear disclaimers

**NFR-9: Operational Requirements (Local)**
- Single-command startup, <5s initialization, file-based logging, health check endpoint

### Epic Breakdown

**Epic 1: Foundation - PoB Calculation Engine Integration**
- Goal: Enable accurate PoB calculations in headless Python environment
- Story Count: 8-10 stories
- Key Deliverables: Parse PoB codes, load HeadlessWrapper.lua via Lupa, implement Python stubs, execute calculations, validate accuracy (±0.1% tolerance)
- Success: 100 sample builds calculated with 100% success rate, <100ms per calculation

**Epic 2: Core Optimization Engine**
- Goal: Implement hill climbing algorithm discovering superior passive tree configurations
- Story Count: 7-9 stories
- Key Deliverables: Hill climbing with neighbor generation, dual budget constraint enforcement, metric selection, convergence detection
- Success: 8%+ median improvement, 80%+ of non-optimal builds improved, <5 min completion

**Epic 3: User Experience & Local Reliability**
- Goal: Deliver complete local web UI with robust error handling and resource management
- Story Count: 10-12 stories
- Key Deliverables: Flask UI, budget input with auto-detection, real-time progress, results display, error handling, timeout, resource cleanup
- Success: 95%+ parse success, clear error messages, 50+ consecutive optimizations without leaks

**Epic Dependencies:** Sequential (Epic 1 → Epic 2 → Epic 3)

### Key Technical Characteristics Identified

**Project Type:** Web application (local Flask at localhost:5000)

**Architecture Style Hints:**
- Monolithic Python backend with simple frontend
- In-process Lua integration (no subprocess overhead)
- Stateless where possible, session data with expiration

**Technology Stack (Explicitly Specified):**
- **Backend:** Python 3.10+ with Lupa library (LuaJIT embedded)
- **PoB Integration:** HeadlessWrapper.lua (official PoB headless mode)
- **Frontend:** Web-based, Flask web framework (minimal complexity)
- **Algorithm:** Hill climbing (MVP), simulated annealing (V2)
- **Data:** Git submodule (external/pob-engine/)

**Special Integration Requirements:**
- Python stub functions: Deflate/Inflate (zlib), ConPrintf (no-ops), SpawnProcess/OpenURL (no-ops)
- PoB data files: PassiveTree.lua (node graph), Classes.lua (starting positions), HeadlessWrapper.lua

**Performance Targets:**
- Single calculation: <100ms
- Batch: 150-500ms for 1000 iterations
- Optimization session: <5 minutes for complex builds
- Startup time: <5 seconds
- Memory: <100MB per session

**Data Flow:**
1. User pastes PoB code (Base64)
2. Decode → Decompress → Parse XML
3. Load into HeadlessWrapper.lua via Lupa
4. Run hill climbing (1000+ calculations per iteration)
5. Generate optimized tree
6. Export as PoB code (XML → Compress → Base64)

### Architecture Decisions Needed

**Already Specified (No Gaps):**
- Primary technology stack (Python + Lupa + Flask)
- Algorithm approach (hill climbing)
- Performance targets clearly defined
- Deployment model (local-only)

**Decisions Required:**
1. **Frontend Framework:** Minimal UI specified - which approach?
2. **Repository Strategy:** Monorepo vs polyrepo (likely monorepo for local project)
3. **State Management:** Session storage mechanism (in-memory, Redis, file-based)
4. **Progress Reporting:** SSE vs polling implementation
5. **Testing Strategy:** Framework selection and coverage approach

---

## Architecture Pattern and Decisions

### Confirmed Architecture
- **Architecture Style:** Modular Monolith (single Python application with clear module boundaries)
- **Repository Strategy:** Monorepo with PoB engine as Git submodule
- **Frontend:** Server-Side Rendering (Flask + Jinja2 templates + Bootstrap 5 CDN)
- **Backend:** Synchronous Flask with thread-based background processing
- **Progress Reporting:** Server-Sent Events (SSE) with polling fallback
- **Session Storage:** In-memory (Python dict with threading.Lock)
- **Styling:** Bootstrap 5 via CDN (professional UI, accessibility support, progress visualization)

### User Skill Level
**Level:** Beginner (detailed explanations with rationale for all decisions)

---

