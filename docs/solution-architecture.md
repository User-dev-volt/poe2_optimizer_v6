# Solution Architecture: PoE 2 Passive Tree Optimizer

**Project:** poe2_optimizer_v6
**Author:** Winston (System Architect)
**Date:** 2025-10-10
**Version:** 1.0 - Complete Architecture
**Status:** ✅ Ready for Implementation

---

## Document Overview

This comprehensive solution architecture document provides complete design specifications for the PoE 2 Passive Tree Optimizer. It merges requirements analysis, architectural decisions, technology selections, and implementation guidance into a single authoritative reference.

**Document Purpose:**
- Define system architecture and component boundaries
- Specify technology stack with exact versions
- Document architectural decisions and rationale
- Provide implementation readiness guidance

**Audience:**
- Development team (implementation reference)
- Stakeholders (understanding system design)
- Future maintainers (architectural context)

**Related Documents:**
- `PRD.md` - Product Requirements (22 FRs, 9 NFRs, 3 epics)
- `project-workflow-analysis.md` - Project classification and workflow
- `implementation-guide.md` - Beginner-friendly walkthrough (companion to this doc)
- `tech-spec-epic-*.md` - Epic-level technical specifications

---

## Table of Contents

1. [Prerequisites and Scale Assessment](#1-prerequisites-and-scale-assessment)
2. [PRD and Requirements Analysis](#2-prd-and-requirements-analysis)
3. [Architecture Pattern and Decisions](#3-architecture-pattern-and-decisions)
4. [Technology Stack and Library Decisions](#4-technology-stack-and-library-decisions)
5. [Proposed Source Tree](#5-proposed-source-tree)
6. [System Architecture](#6-system-architecture)
7. [Component Architecture](#7-component-architecture)
8. [Data Architecture](#8-data-architecture)
9. [DevOps and Development](#9-devops-and-development)
10. [Security Architecture](#10-security-architecture)
11. [Testing Strategy](#11-testing-strategy)
12. [Architecture Decision Records](#12-architecture-decision-records)
13. [Implementation Roadmap](#13-implementation-roadmap)
14. [Appendices](#14-appendices)

---

## 1. Prerequisites and Scale Assessment

### 1.1 Project Classification

- **Project Level:** Level 3 (Full product - 12-40 stories, 2-5 epics)
- **Project Type:** Web application (local development, Flask at localhost:5000)
- **Field Type:** Greenfield (new project, no existing codebase)
- **UI Complexity:** Minimal (single-page interface)

### 1.2 Prerequisites Validation

✅ **PRD Complete**
- Version: 1.1 (Post-Validation Edition)
- Status: COMPLETE for architecture handoff
- Content: Comprehensive FRs, NFRs, epics, and user stories
- Location: `docs/PRD.md`

⚠️ **UX Spec Skipped**
- Rationale: UI is extremely minimal (text box, dropdown, button, results display)
- PRD contains sufficient UI detail for implementation
- Separate UX spec would add ceremony without value
- Decision: Proceed without dedicated UX specification

✅ **Project Analysis Complete**
- Document: `project-workflow-analysis.md`
- Project level determined: Level 3
- Workflow path: Full solution architecture required

✅ **Prerequisites Met - Proceeding with Solution Architecture**

---

## 2. PRD and Requirements Analysis

### 2.1 Document Overview

- **PRD Version:** 1.1 (Post-Validation Edition)
- **Total Requirements:** 22 Functional Requirements (FRs) + 9 Non-Functional Requirements (NFRs)
- **Epic Structure:** 3 major epics, 25-31 user stories, ~80 story points
- **Validation Status:** PRD validated 2025-10-09, all critical issues resolved

### 2.2 Product Summary

**"The PoE 2 Passive Tree Optimizer"** is a focused local web application that automatically discovers mathematically superior passive skill tree configurations for Path of Exile 2 builds. The tool transforms 3+ hours of manual passive tree experimentation into a 30-second to 5-minute automated optimization delivering verifiable 5-15% performance improvements.

**Core Differentiator:** Ruthless scope discipline - does ONE thing perfectly (passive tree optimization only) enabling a 2-month MVP vs. competitors' 12+ month "complete solutions".

**Deployment Model:** Local-only Flask application running at localhost:5000 for personal use and validation before any public release.

### 2.3 Functional Requirements Summary

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

### 2.4 Non-Functional Requirements Summary

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

### 2.5 Epic Breakdown

**Epic 1: Foundation - PoB Calculation Engine Integration**
- **Goal:** Enable accurate PoB calculations in headless Python environment
- **Story Count:** 8-10 stories
- **Key Deliverables:** Parse PoB codes, load HeadlessWrapper.lua via Lupa, implement Python stubs, execute calculations, validate accuracy (±0.1% tolerance)
- **Success Criteria:** 100 sample builds calculated with 100% success rate, <100ms per calculation
- **Tech Spec:** `tech-spec-epic-1.md`

**Epic 2: Core Optimization Engine**
- **Goal:** Implement hill climbing algorithm discovering superior passive tree configurations
- **Story Count:** 7-9 stories
- **Key Deliverables:** Hill climbing with neighbor generation, dual budget constraint enforcement, metric selection, convergence detection
- **Success Criteria:** 8%+ median improvement, 80%+ of non-optimal builds improved, <5 min completion
- **Tech Spec:** `tech-spec-epic-2.md`

**Epic 3: User Experience & Local Reliability**
- **Goal:** Deliver complete local web UI with robust error handling and resource management
- **Story Count:** 10-12 stories
- **Key Deliverables:** Flask UI, budget input with auto-detection, real-time progress, results display, error handling, timeout, resource cleanup
- **Success Criteria:** 95%+ parse success, clear error messages, 50+ consecutive optimizations without leaks
- **Tech Spec:** `tech-spec-epic-3.md`

**Epic Dependencies:** Sequential (Epic 1 → Epic 2 → Epic 3)

### 2.6 Key Technical Characteristics

**Project Type:** Web application (local Flask at localhost:5000)

**Architecture Style Implications:**
- Monolithic Python backend with simple frontend
- In-process Lua integration (no subprocess overhead)
- Stateless where possible, session data with expiration

**Technology Stack (Explicitly Specified in PRD):**
- **Backend:** Python 3.10+ with Lupa library (LuaJIT embedded)
- **PoB Integration:** HeadlessWrapper.lua (official PoB headless mode)
- **Frontend:** Web-based, Flask web framework (minimal complexity)
- **Algorithm:** Hill climbing (MVP), simulated annealing (V2)
- **Data:** Git submodule (external/pob-engine/)

**Performance Targets:**
- Single calculation: <100ms
- Batch: 150-500ms for 1000 iterations
- Optimization session: <5 minutes for complex builds
- Startup time: <5 seconds
- Memory: <100MB per session

---

## 3. Architecture Pattern and Decisions

### 3.1 Confirmed Architecture

- **Architecture Style:** Modular Monolith (single Python application with clear module boundaries)
- **Repository Strategy:** Monorepo with PoB engine as Git submodule
- **Frontend:** Server-Side Rendering (Flask + Jinja2 templates + Bootstrap 5 CDN)
- **Backend:** Synchronous Flask with thread-based background processing
- **Progress Reporting:** Server-Sent Events (SSE) with polling fallback
- **Session Storage:** In-memory (Python dict with threading.Lock)
- **Styling:** Bootstrap 5 via CDN (professional UI, accessibility support, progress visualization)

### 3.2 Architecture Pattern Rationale

**Modular Monolith Choice:**
- **Reason:** Local MVP scope (single user, localhost deployment)
- **Benefits:**
  - Simple deployment (single process)
  - No network overhead between components
  - Easy debugging (single codebase)
  - Lower complexity for beginner developers
- **Module Boundaries:**
  - `parsers/` - PoB code encoding/decoding
  - `calculator/` - Lua integration and PoB calculations
  - `optimizer/` - Hill climbing algorithm
  - `web/` - Flask routes and session management
  - `frontend/` - Templates and static assets

**When to Split:** If scaling to hundreds of concurrent users or distributed deployment, consider:
- Extracting optimizer to separate service (CPU-intensive)
- Redis for session state (multi-server deployment)
- Load balancer for horizontal scaling

### 3.3 User Skill Level Adaptation

**Target Skill Level:** Beginner
**Adaptation Strategy:**
- Detailed code comments and docstrings
- Type hints throughout codebase (mypy validation)
- Comprehensive test examples
- Step-by-step implementation guide (separate document)
- Clear module boundaries (easy to understand responsibilities)

---

## 4. Technology Stack and Library Decisions

### 4.1 Complete Technology Table

| Category | Technology | Version | Justification |
|----------|------------|---------|-----------|
| **Backend Framework** | Flask | 3.0.0 | Lightweight Python web framework perfect for local MVP. Simple request/response model, easy to understand for beginners. Supports background threading and Server-Sent Events without async complexity. Widely documented, mature ecosystem. |
| **Programming Language** | Python | 3.10+ | Required for Lupa library compatibility (LuaJIT bindings). Strong standard library (threading, zlib, base64). Type hints support for maintainability. Excellent for algorithm development and data processing. |
| **Lua Integration** | Lupa | 2.0 | Provides LuaJIT bindings for Python, enabling in-process execution of PoB's Lua calculation engine. Critical for performance (<100ms per calculation). No subprocess overhead, shared memory space. |
| **Template Engine** | Jinja2 | 3.1.2 | Built into Flask. Server-side HTML rendering with template inheritance, filters, and control structures. Familiar Django-like syntax. Enables reusable components (base.html, macros). |
| **Frontend Styling** | Bootstrap | 5.3.2 (CDN) | Professional UI components out of the box. Built-in progress bars, spinners, alerts perfect for optimization progress display. WCAG 2.1 AA accessible by default. No build step (CDN), no npm complexity. Grid system for responsive layouts. |
| **Frontend JavaScript** | Vanilla JavaScript | ES2020+ | Minimal JavaScript needs: SSE connection for progress updates, form validation, loading states. No framework overhead. Modern browser features (EventSource API, fetch, async/await) sufficient. |
| **XML Parsing** | xmltodict | 0.13.0 | Converts PoB's XML format to Python dicts for easy manipulation. Simple API: `xmltodict.parse(xml_string)`. Handles Base64 → zlib → XML pipeline. |
| **HTTP Server** | Werkzeug | 3.0.1 | Flask's underlying WSGI server. Built-in development server perfect for local MVP. Supports threading for concurrent requests. Automatic reloader for development. |
| **Testing Framework** | pytest | 7.4.3 | De facto Python testing standard. Fixtures for test setup, parametrize for multiple test cases, coverage reporting. Simple assert syntax. Plugins for Flask testing (pytest-flask). |
| **Type Checking** | mypy | 1.7.1 | Static type analysis for Python. Catches bugs before runtime. Enforces type hints across codebase. Configured in strict mode for maximum safety. |
| **Code Formatting** | black | 23.11.0 | Opinionated code formatter. Zero configuration, deterministic output. Enforces PEP 8 automatically. Consistent style across codebase. |
| **Linting** | ruff | 0.1.6 | Fast Python linter (Rust-based). Replaces flake8, isort, pylint. Catches unused imports, undefined variables, style issues. 10-100x faster than traditional linters. |

### 4.2 Technology Decision Criteria

All technology selections based on:
1. **Local MVP requirements** - No cloud dependencies, simple setup
2. **Beginner-friendly** - Well-documented, large community, clear examples
3. **Performance targets** - Meet NFR-1 requirements (<100ms calculations)
4. **Maintainability** - Type hints, testing, linting support
5. **Accessibility** - WCAG 2.1 AA compliance (Bootstrap default)

### 4.3 Explicitly Rejected Alternatives

| Technology | Rejected Alternative | Reason for Rejection |
|------------|---------------------|---------------------|
| Flask | FastAPI | Requires async/await (complicates Lupa integration), over-engineering for local MVP |
| Flask | Django | Too heavyweight, includes unused features (ORM, admin, auth) |
| Bootstrap | Tailwind CSS | Requires build step (npm, PostCSS), more complex setup |
| Bootstrap | Plain CSS | Weeks of development time for progress bars, responsive grid |
| SSE | WebSockets | Bidirectional communication not needed, more complex setup |
| SSE | Polling only | Higher overhead, used as fallback only |
| In-memory session | Redis | Over-engineering for single-user local deployment |

---

## 5. Proposed Source Tree

### 5.1 Complete Directory Structure

```
poe2_optimizer_v6/
├── src/                                  # Application source code
│   ├── __init__.py
│   ├── main.py                          # Flask app entry point
│   │
│   ├── parsers/                         # FR-1.x: PoB Code Parsing
│   │   ├── __init__.py
│   │   ├── pob_parser.py                # Base64 → zlib → XML → BuildData
│   │   ├── pob_generator.py             # BuildData → XML → zlib → Base64
│   │   ├── xml_utils.py                 # XML parsing helpers
│   │   └── exceptions.py                # PoBParseError, InvalidFormatError
│   │
│   ├── calculator/                      # FR-3.x: PoB Calculation Engine
│   │   ├── __init__.py
│   │   ├── pob_engine.py                # Lupa integration, HeadlessWrapper
│   │   ├── stub_functions.py            # Python stubs (Deflate, Inflate, ConPrintf)
│   │   ├── passive_tree.py              # PassiveTree.lua loader, graph structure
│   │   └── build_calculator.py          # BuildData → BuildStats via PoB
│   │
│   ├── optimizer/                       # FR-4.x: Optimization Algorithm
│   │   ├── __init__.py
│   │   ├── hill_climbing.py             # Hill climbing implementation
│   │   ├── tree_validator.py            # Connectivity validation (BFS)
│   │   ├── neighbor_generator.py        # Generate 1-hop neighbors
│   │   ├── budget_tracker.py            # Dual budget constraint enforcement
│   │   └── convergence.py               # Detect optimization completion
│   │
│   ├── web/                             # Flask web application
│   │   ├── __init__.py
│   │   ├── app.py                       # Flask app factory
│   │   ├── routes.py                    # HTTP routes (/, /optimize, /progress, /results)
│   │   ├── sse.py                       # Server-Sent Events implementation
│   │   ├── session_manager.py           # Session dict, threading.Lock, cleanup
│   │   └── forms.py                     # Flask-WTF forms (optional, for CSRF)
│   │
│   ├── frontend/                        # Static assets and templates
│   │   ├── templates/
│   │   │   ├── base.html                # Base template (Bootstrap CDN, navbar)
│   │   │   ├── index.html               # Home page (form)
│   │   │   ├── progress.html            # Progress page (SSE connection)
│   │   │   ├── results.html             # Results page (before/after comparison)
│   │   │   └── error.html               # Error page (FR-1.3 structured errors)
│   │   │
│   │   └── static/
│   │       ├── css/
│   │       │   └── custom.css           # Custom styles on top of Bootstrap
│   │       ├── js/
│   │       │   ├── progress.js          # SSE connection, progress bar updates
│   │       │   └── copy-code.js         # Copy PoB code to clipboard
│   │       └── img/
│   │           └── favicon.ico
│   │
│   ├── models/                          # Data models (dataclasses)
│   │   ├── __init__.py
│   │   ├── build_data.py                # BuildData, CharacterClass enum
│   │   ├── build_stats.py               # BuildStats (DPS, EHP, resistances)
│   │   └── optimization_config.py       # OptimizationConfig (goal, budgets)
│   │
│   └── utils/                           # Shared utilities
│       ├── __init__.py
│       ├── logging_config.py            # Structured logging setup
│       └── performance.py               # Performance monitoring, timeouts
│
├── external/                            # External dependencies
│   └── pob-engine/                      # Git submodule (Path of Building)
│       ├── HeadlessWrapper.lua
│       ├── src/
│       │   ├── Data/
│       │   │   ├── PassiveTree.lua
│       │   │   └── Classes.lua
│       │   └── Modules/
│       │       └── CalcPerform.lua
│       └── ... (full PoB codebase)
│
├── tests/                               # Test suite (pytest)
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures
│   │
│   ├── unit/                            # Unit tests (isolated modules)
│   │   ├── test_pob_parser.py
│   │   ├── test_pob_generator.py
│   │   ├── test_tree_validator.py
│   │   ├── test_hill_climbing.py
│   │   └── test_budget_tracker.py
│   │
│   ├── integration/                     # Integration tests (module interaction)
│   │   ├── test_pob_engine_integration.py
│   │   ├── test_optimization_pipeline.py
│   │   └── test_session_management.py
│   │
│   └── e2e/                             # End-to-end tests (full workflow)
│       └── test_optimization_workflow.py
│
├── logs/                                # Application logs
│   └── optimizer.log                    # Rotating log file
│
├── docs/                                # Documentation
│   ├── PRD.md                           # Product Requirements Document
│   ├── solution-architecture-complete.md # This document
│   ├── implementation-guide.md          # Beginner-friendly walkthrough
│   ├── cohesion-check-report.md         # Requirements coverage validation
│   ├── epic-alignment-matrix.md         # Epic-to-component mapping
│   ├── tech-spec-epic-1.md              # Epic 1 technical specification
│   ├── tech-spec-epic-2.md              # Epic 2 technical specification
│   ├── tech-spec-epic-3.md              # Epic 3 technical specification
│   ├── ADRs/                            # Architecture Decision Records
│   │   ├── ADR-001-flask-over-fastapi.md
│   │   ├── ADR-002-threading-over-asyncio.md
│   │   └── ADR-003-bootstrap-styling.md
│   └── project-workflow-analysis.md
│
├── scripts/                             # Utility scripts
│   ├── setup_pob_submodule.sh           # Initialize Git submodule
│   └── run_tests.sh                     # Test execution script
│
├── .gitignore                           # Git ignore patterns
├── .gitmodules                          # Git submodule config
├── requirements.txt                     # Production dependencies
├── requirements-dev.txt                 # Development dependencies (pytest, mypy, black)
├── pyproject.toml                       # Python project config (black, mypy, ruff)
├── README.md                            # Project overview, setup instructions
├── LICENSE                              # MIT License
└── POB_VERSION.txt                      # Pinned PoB commit hash
```

### 5.2 Module Responsibilities

**parsers/ (FR-1.x)**
- **Responsibility:** PoB code encoding/decoding
- **Dependencies:** None (isolated module)
- **Key Files:**
  - `pob_parser.py` - Parse PoB codes into BuildData objects
  - `pob_generator.py` - Generate PoB codes from BuildData objects
- **Testing:** Unit tests with sample PoB codes

**calculator/ (FR-3.x)**
- **Responsibility:** Python-Lua bridge for PoB calculations
- **Dependencies:** Lupa, external/pob-engine/
- **Key Files:**
  - `pob_engine.py` - Lupa integration, HeadlessWrapper loading
  - `stub_functions.py` - Python implementations for Lua dependencies
  - `passive_tree.py` - Load and cache PassiveTree.lua graph
- **Testing:** Integration tests with real PoB engine

**optimizer/ (FR-4.x)**
- **Responsibility:** Hill climbing algorithm
- **Dependencies:** calculator/ (for stat calculations)
- **Key Files:**
  - `hill_climbing.py` - Main optimization loop
  - `tree_validator.py` - BFS connectivity validation
  - `neighbor_generator.py` - Generate candidate trees
- **Testing:** Unit tests with mock calculator

**web/ (FR-5.x, Epic 3)**
- **Responsibility:** Flask application layer
- **Dependencies:** parsers/, calculator/, optimizer/
- **Key Files:**
  - `app.py` - Flask app factory
  - `routes.py` - HTTP endpoints
  - `sse.py` - Server-Sent Events for progress
  - `session_manager.py` - Thread-safe session storage
- **Testing:** Flask test client, E2E tests

**frontend/ (FR-1.7, FR-5.x)**
- **Responsibility:** User interface (templates + static assets)
- **Dependencies:** Bootstrap 5 CDN
- **Key Files:**
  - `templates/base.html` - Base template with navbar
  - `templates/index.html` - Main form
  - `static/js/progress.js` - SSE client
- **Testing:** Manual testing, E2E tests

### 5.3 External Dependencies

**external/pob-engine/ (Git Submodule)**
- **Repository:** Path of Building official repository
- **Pinned Commit:** Documented in POB_VERSION.txt
- **Key Files Used:**
  - `HeadlessWrapper.lua` - Main calculation entry point
  - `src/Data/PassiveTree.lua` - Passive tree node graph
  - `src/Data/Classes.lua` - Character starting nodes
- **Update Strategy:** Monthly testing, manual commit hash updates

---

## 6. System Architecture

### 6.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (User)                           │
│  ┌────────────┐  ┌───────────────┐  ┌───────────────────────┐  │
│  │  Form UI   │  │ Progress Page │  │  Results Display      │  │
│  │ (index.html)│  │  (SSE stream) │  │ (before/after compare)│  │
│  └────────────┘  └───────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                     │                      │
         │ HTTP POST           │ HTTP GET (SSE)       │ HTTP GET
         │ /optimize           │ /sse/<session_id>    │ /results/<session_id>
         ↓                     ↓                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Flask Web Server (src/web/)                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Routes (routes.py)                                      │   │
│  │  - POST /optimize → parse, create session, start thread │   │
│  │  - GET /sse/<id> → stream progress updates              │   │
│  │  - GET /results/<id> → render results page              │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Session Manager (session_manager.py)                   │   │
│  │  - sessions: Dict[str, SessionData]                     │   │
│  │  - session_lock: threading.Lock                         │   │
│  │  - Background thread pool (max 10 concurrent)           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │                          │
         │ Parse PoB code           │ Optimize tree (background thread)
         ↓                          ↓
┌──────────────────────┐   ┌────────────────────────────────────┐
│  Parsers Module      │   │  Optimizer Module                  │
│  (src/parsers/)      │   │  (src/optimizer/)                  │
│                      │   │                                    │
│  Base64 → zlib →    │   │  Hill Climbing Algorithm:          │
│  XML → BuildData     │   │  1. Load passive tree graph        │
│                      │   │  2. Calculate baseline stats       │
│                      │   │  3. Loop:                          │
│                      │   │     - Generate neighbor            │
│                      │   │     - Validate connectivity        │
│                      │   │     - Calculate stats              │
│                      │   │     - Keep if improved             │
│                      │   │  4. Convergence check              │
└──────────────────────┘   └────────────────────────────────────┘
                                       │
                                       │ Calculate stats
                                       ↓
                           ┌──────────────────────────────────┐
                           │  Calculator Module               │
                           │  (src/calculator/)               │
                           │                                  │
                           │  PoB Engine (Lupa/LuaJIT):      │
                           │  - Load HeadlessWrapper.lua      │
                           │  - Execute PoB calculations      │
                           │  - Return DPS, EHP, resistances  │
                           │                                  │
                           │  Python Stubs:                   │
                           │  - Deflate/Inflate (zlib)        │
                           │  - ConPrintf (no-op logging)     │
                           └──────────────────────────────────┘
                                       │
                                       │ Read Lua files
                                       ↓
                           ┌──────────────────────────────────┐
                           │  Path of Building Engine         │
                           │  (external/pob-engine/)          │
                           │                                  │
                           │  - HeadlessWrapper.lua           │
                           │  - PassiveTree.lua (tree graph)  │
                           │  - CalcPerform.lua (DPS formulas)│
                           │  - Classes.lua (starting nodes)  │
                           └──────────────────────────────────┘
```

### 6.2 Data Flow: User Request to Response

```
[User Action] Paste PoB code, select goal, click "Optimize"
    ↓
[1] Browser sends POST /optimize with form data
    ↓
[2] Flask routes.py receives request
    ↓
[3] Validate input (size <100KB, format)
    │
    ├─ Error → Render error page with structured message
    │
    └─ Valid ↓
    ↓
[4] parsers/pob_parser.py: Base64 → zlib → XML → BuildData
    │
    ├─ Parse error → Structured error page
    │
    └─ Success ↓
    ↓
[5] session_manager.create_session(session_id, BuildData, goal, budgets)
    ↓
[6] Start background optimization thread
    ↓
[7] Return 202 Accepted + redirect to /progress/<session_id>
    ↓
[8] Browser renders progress.html with SSE connection
    ↓
[9] JavaScript: EventSource connects to GET /sse/<session_id>
    ↓
    ┌─────────────────────────────────────────────────────┐
    │  Background Thread (Optimization Worker)            │
    │                                                      │
    │  [10] Load passive tree graph (cached)              │
    │  [11] Calculate baseline stats (PoB engine)         │
    │  [12] Hill climbing loop:                           │
    │       - Generate neighbors                          │
    │       - Validate connectivity                       │
    │       - Calculate stats for each                    │
    │       - Keep best improvement                       │
    │       - Update session progress every 2s            │
    │  [13] Convergence → Set status="complete"           │
    │                                                      │
    └─────────────────────────────────────────────────────┘
    ↓ (SSE streams updates to browser in parallel)
    ↓
[14] SSE endpoint streams: {"status": "running", "progress": 0.5, "message": "..."}
    ↓
[15] JavaScript updates progress bar, status text
    ↓
[16] Status "complete" → Redirect to /results/<session_id>
    ↓
[17] routes.py /results handler:
     - Fetch optimized BuildData
     - parsers/pob_generator.py: BuildData → XML → zlib → Base64
     - Render results.html with before/after comparison
    ↓
[18] User copies new PoB code, pastes into Path of Building
```

### 6.3 Component Interaction Patterns

**Parser → Calculator → Optimizer → Web (Layered Architecture)**

```
┌─────────────────────────────────────────────────────────┐
│  Presentation Layer (web/, frontend/)                   │
│  - HTTP routes, templates, SSE streaming                │
└─────────────────────────────────────────────────────────┘
                      ↓ uses
┌─────────────────────────────────────────────────────────┐
│  Business Logic Layer (optimizer/)                      │
│  - Hill climbing algorithm, tree validation             │
└─────────────────────────────────────────────────────────┘
                      ↓ uses
┌─────────────────────────────────────────────────────────┐
│  Integration Layer (calculator/)                        │
│  - Lupa/PoB bridge, stat calculations                   │
└─────────────────────────────────────────────────────────┘
                      ↓ uses
┌─────────────────────────────────────────────────────────┐
│  Data Layer (parsers/, models/)                         │
│  - PoB code encoding/decoding, data models              │
└─────────────────────────────────────────────────────────┘
```

**Dependency Rules:**
- **Upper layers depend on lower layers** (standard layered architecture)
- **Lower layers NEVER depend on upper layers** (no circular dependencies)
- **Each layer has single clear responsibility**
- **Models/ is shared across all layers** (data transfer objects)

---

## 7. Component Architecture

### 7.1 Parsers Component (src/parsers/)

**Responsibility:** Transform PoB codes between encoded format and structured data

**Key Classes/Functions:**
- `parse_pob_code(code: str) -> BuildData` - Main parsing entry point
- `generate_pob_code(build: BuildData) -> str` - Main generation entry point
- `PoBParseError` - Custom exception for parse failures

**Input/Output Contracts:**

```python
# Input: PoB code (Base64 string)
pob_code: str = "eNqVVktv..."

# Output: Structured BuildData
class BuildData:
    character_class: CharacterClass  # enum: Witch, Warrior, etc.
    level: int                       # 1-100
    ascendancy: Optional[str]        # e.g., "Elementalist"
    passive_nodes: Set[int]          # Set of allocated passive node IDs
    items: List[Item]                # Equipment
    skills: List[Skill]              # Active skill gems
    # ... additional fields
```

**Error Handling:**
- Invalid Base64 → `PoBParseError("Invalid Base64 encoding")`
- Corrupt zlib data → `PoBParseError("Failed to decompress")`
- Invalid XML → `PoBParseError("Unable to parse XML structure")`
- PoE 1 code detected → `PoBParseError("PoE 1 codes not supported")`

**Testing Strategy:**
- Unit tests with sample PoB codes (valid, invalid, edge cases)
- Round-trip tests: parse → generate → parse (should equal original)

### 7.2 Calculator Component (src/calculator/)

**Responsibility:** Bridge Python and Lua (PoB calculation engine)

**Key Classes/Functions:**
- `PoBCalculationEngine` - Lupa integration class
- `get_pob_engine() -> PoBCalculationEngine` - Thread-local engine retrieval
- `calculate_build_stats(build: BuildData) -> BuildStats` - Main calculation

**Architecture Pattern:** Thread-local singleton (one engine per thread)

**Rationale:** Lua state is not thread-safe, so each optimization thread needs its own engine instance

**Integration Points:**
- Python → Lua: Call `loadBuildFromXML(xml_string)` via Lupa
- Lua → Python: PoB code calls Python stubs (Deflate, Inflate, ConPrintf)
- Passive tree loading: Load PassiveTree.lua once, cache in memory

**Performance Optimizations:**
- Lazy initialization (load on first use)
- Passive tree graph caching (avoid repeated file reads)
- LuaJIT compilation (first call slower, subsequent calls fast)

**Testing Strategy:**
- Integration tests with real PoB engine
- Performance tests (1000 calculations <1s)
- Accuracy tests (compare with PoB GUI, ±0.1% tolerance)

### 7.3 Optimizer Component (src/optimizer/)

**Responsibility:** Hill climbing algorithm for passive tree optimization

**Key Classes/Functions:**
- `HillClimbingOptimizer` - Main optimization class
- `optimize(initial_build, goal, budgets) -> OptimizedBuild`
- `TreeValidator` - BFS connectivity validation
- `NeighborGenerator` - Generate candidate trees
- `BudgetTracker` - Enforce dual budget constraints

**Algorithm Pattern:** Local search with convergence detection

**Optimization Loop:**
```
1. Calculate baseline stats (initial build)
2. Loop (max 1000 iterations or convergence):
   a. Generate all valid neighbors (±1 node)
   b. Validate tree connectivity (BFS)
   c. Calculate stats for each neighbor
   d. Select best improvement
   e. If no improvement for 50 iterations → converge
   f. Update progress every 100 iterations
3. Return best build found
```

**Objective Functions:**
- Maximize DPS: `score = total_dps`
- Maximize EHP: `score = effective_hp`
- Balanced: `score = 0.7 * (dps/100k) + 0.3 * (ehp/50k)`

**Constraints:**
- Tree connectivity (all nodes reachable from starting node)
- Unallocated points budget (never exceed available points)
- Respec points budget (limit costly deallocations)

**Testing Strategy:**
- Unit tests with mock calculator (fast)
- Integration tests with real calculator (slower)
- Property-based tests (all outputs are valid trees)

### 7.4 Web Component (src/web/)

**Responsibility:** Flask application layer (HTTP, sessions, SSE)

**Key Classes/Functions:**
- `create_app() -> Flask` - Flask app factory
- `routes.py` - HTTP endpoint handlers
- `SessionManager` - Thread-safe session storage
- `stream_progress(session_id) -> Response` - SSE endpoint

**Session Management Pattern:**

```python
# In-memory session storage
sessions: Dict[str, SessionData] = {}
session_lock = threading.Lock()

class SessionData:
    status: str  # "pending", "running", "complete", "error"
    progress: float  # 0.0-1.0
    message: str
    result: Optional[BuildData]
```

**HTTP Endpoints:**
- `GET /` - Home page (form)
- `POST /optimize` - Submit optimization (create session, start thread)
- `GET /progress/<id>` - Progress page (SSE connection)
- `GET /sse/<id>` - SSE stream (real-time updates)
- `GET /results/<id>` - Results page (before/after comparison)
- `GET /api/progress/<id>` - JSON progress (polling fallback)

**Concurrency Model:**
- Flask main thread handles HTTP requests
- Background threads run optimizations (one per session)
- threading.Lock protects shared session dictionary
- Max 10 concurrent optimization threads

**Testing Strategy:**
- Flask test client for route testing
- Mock optimization for fast tests
- E2E tests for full workflow

### 7.5 Frontend Component (src/frontend/)

**Responsibility:** User interface (HTML templates, CSS, JavaScript)

**Template Structure:**
- `base.html` - Base template (Bootstrap CDN, navbar, footer)
- `index.html` - Extends base, form for PoB code input
- `progress.html` - Extends base, progress bar + SSE client
- `results.html` - Extends base, before/after comparison table
- `error.html` - Extends base, structured error messages

**JavaScript Responsibilities:**
- SSE connection (`EventSource` API)
- Progress bar updates (Bootstrap progress component)
- Copy to clipboard (Clipboard API)
- Form validation (HTML5 + custom)

**Accessibility (WCAG 2.1 AA):**
- Semantic HTML (proper heading hierarchy)
- ARIA labels for progress indicators
- Keyboard navigation (all interactive elements)
- Color contrast (Bootstrap defaults compliant)
- Screen reader support (status announcements)

**Testing Strategy:**
- Manual testing for UI/UX
- E2E tests for workflows
- Accessibility testing (axe DevTools)

---

## 8. Data Architecture

### 8.1 Core Data Models

**BuildData (src/models/build_data.py)**
```python
@dataclass
class BuildData:
    """
    Represents a Path of Exile 2 build configuration.

    This is the central data model passed between components.
    """
    character_class: CharacterClass  # enum
    level: int  # 1-100
    ascendancy: Optional[str]
    passive_nodes: Set[int]  # Set of allocated node IDs
    items: List[Item]
    skills: List[Skill]
    tree_version: str  # PoB tree version

    # Metadata
    build_name: Optional[str] = None
    notes: Optional[str] = None
```

**BuildStats (src/models/build_stats.py)**
```python
@dataclass
class BuildStats:
    """
    Calculated statistics for a build.

    Returned by calculator component after PoB calculation.
    """
    total_dps: float
    effective_hp: float
    life: int
    energy_shield: int
    mana: int
    resistances: Dict[str, int]  # fire, cold, lightning, chaos

    # Additional stats
    armour: int = 0
    evasion: int = 0
    block_chance: float = 0.0
```

**OptimizationConfig (src/models/optimization_config.py)**
```python
@dataclass
class OptimizationConfig:
    """
    Configuration for optimization algorithm.
    """
    goal: OptimizationGoal  # enum: MAXIMIZE_DPS, MAXIMIZE_EHP, BALANCED
    unallocated_points: int  # Free allocations
    respec_points: int  # Costly deallocations

    # Algorithm parameters
    max_iterations: int = 1000
    convergence_threshold: int = 50  # No improvement iterations
    timeout_seconds: int = 300  # 5 minutes
```

### 8.2 Data Flow Between Components

```
[User Input] PoB code (Base64 string)
    ↓ parsers/pob_parser.py
[BuildData] Structured build object
    ↓ calculator/build_calculator.py
[BuildStats] Calculated DPS, EHP, etc.
    ↓ optimizer/hill_climbing.py
[BuildData] Optimized build (modified passive_nodes)
    ↓ parsers/pob_generator.py
[PoB Code] New Base64 string
    ↓
[User Output] Paste into Path of Building
```

### 8.3 Session Data Storage

**Session Storage Pattern:** In-memory dictionary with threading.Lock

**Rationale:**
- Local MVP (single user, localhost)
- Simple implementation (no Redis dependency)
- Fast access (no network overhead)
- Automatic cleanup (15-minute expiration)

**When to Migrate:** If scaling to multi-user or distributed deployment:
- Use Redis for session state
- Implement session serialization
- Add session persistence (survive restarts)

### 8.4 External Data Sources

**Path of Building Engine (external/pob-engine/)**
- **Data Files:**
  - `PassiveTree.lua` - Node graph structure (adjacency list)
  - `Classes.lua` - Character starting nodes
  - `CalcPerform.lua` - DPS calculation formulas
- **Access Pattern:** Read-only, loaded at startup, cached in memory
- **Update Strategy:** Git submodule, manual updates, test before merging

**No Database Required:**
- No persistent data storage
- No user accounts
- No history tracking (V2 feature)
- Session data expires after 15 minutes

---

## 9. DevOps and Development

### 9.1 Local Development Setup

**Prerequisites:**
- Python 3.10 or higher
- Git 2.40+
- Modern browser (Chrome 90+, Firefox 88+)

**Setup Steps:**
```bash
# 1. Clone repository
git clone <repository-url>
cd poe2_optimizer_v6

# 2. Initialize Git submodule (Path of Building engine)
git submodule init
git submodule update

# 3. Verify PoB submodule
ls external/pob-engine/HeadlessWrapper.lua  # Should exist

# 4. Create Python virtual environment
python3.10 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 5. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 6. Verify installation
python -c "import lupa; print('Lupa OK')"
python -c "import flask; print('Flask OK')"

# 7. Run tests
pytest tests/unit/  # Fast unit tests

# 8. Start application
python src/main.py

# Should see:
#  * Running on http://127.0.0.1:5000
#  * Press CTRL+C to quit
```

### 9.2 Development Workflow

**Terminal Setup (3 terminals recommended):**

```bash
# Terminal 1: Run application with auto-reload
python src/main.py

# Terminal 2: Run tests in watch mode
pytest-watch tests/

# Terminal 3: Code quality checks
black src/ tests/        # Format code
ruff check src/ --fix    # Lint and auto-fix
mypy src/                # Type check
```

**Git Workflow:**
```bash
# Feature branch workflow
git checkout -b feature/epic-1-pob-parser
# ... make changes ...
black src/
ruff check src/ --fix
mypy src/
pytest
git add .
git commit -m "feat: implement PoB parser (FR-1.2)"
git push origin feature/epic-1-pob-parser
```

### 9.3 Logging Configuration

**Log Levels:**
- **DEBUG:** Detailed PoB engine calls, algorithm iterations
- **INFO:** Optimization started/completed, session created
- **WARNING:** Parse errors, calculation timeouts
- **ERROR:** Unexpected failures, Lua errors

**Log Location:** `logs/optimizer.log` (rotating, 10MB max, 3 backups)

**Log Format:**
```
2025-10-10 14:32:15,123 [INFO] session_manager.py:45 - Created optimization session: abc-123
2025-10-10 14:32:15,456 [DEBUG] pob_engine.py:78 - Calculating stats for build (level 90, Witch)
2025-10-10 14:32:15,567 [DEBUG] pob_engine.py:92 - Calculation result: DPS=125430, EHP=42150
2025-10-10 14:32:15,789 [INFO] hill_climbing.py:123 - Iteration 100: +8.2% DPS improvement found
2025-10-10 14:33:42,012 [INFO] hill_climbing.py:234 - Optimization complete: final improvement +12.5% DPS
```

### 9.4 Dependency Management

**Production Dependencies (requirements.txt):**
```
Flask==3.0.0
Lupa==2.0
xmltodict==0.13.0
Jinja2==3.1.2
Werkzeug==3.0.1
```

**Development Dependencies (requirements-dev.txt):**
```
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
mypy==1.7.1
black==23.11.0
ruff==0.1.6
```

**Version Pinning Strategy:**
- Exact versions (`==`) for stability
- Monthly security updates (pip-audit)
- Test before updating versions

### 9.5 Performance Monitoring

**Key Metrics:**
- Parse time (target: <500ms)
- Single calculation time (target: <100ms)
- Batch calculation time (target: <1s for 1000)
- Optimization completion time (target: <5 min)
- Memory usage per session (target: <100MB)

**Monitoring Approach:**
- Timing decorators on key functions
- Log performance warnings if targets exceeded
- Manual profiling during development (cProfile)

---

## 10. Security Architecture

### 10.1 Threat Model (Local Deployment)

**Attack Surface:** Minimal (localhost-only, single user)

**Threat Vectors:**
- Malicious PoB codes (oversized, crafted XML)
- Lua code injection (prevented by read-only PoB engine)
- Denial of service (resource exhaustion)
- Dependency vulnerabilities

**Out of Scope (Local MVP):**
- Network attacks (not exposed to network)
- Multi-user attacks (single user)
- Data breaches (no persistent data)
- Authentication/authorization (not needed)

### 10.2 Input Validation

**PoB Code Validation:**
- **Size limit:** 100KB maximum (FR-1.1)
- **Format validation:** Valid Base64 → valid zlib → valid XML
- **Content validation:** Required fields present (class, level, tree)
- **Sanitization:** Escape HTML in error messages (prevent XSS)

**Form Input Validation:**
- **Goal:** Must be one of ["maximize_dps", "maximize_ehp", "balanced"]
- **Unallocated points:** Integer, 0-120 range
- **Respec points:** Integer, 0-1000 range

**Implementation:**
```python
def validate_pob_code(code: str) -> None:
    if len(code) > 100 * 1024:
        raise PoBParseError("PoB code too large (max 100KB)")

    # Base64 validation
    try:
        decoded = base64.b64decode(code)
    except Exception:
        raise PoBParseError("Invalid Base64 encoding")

    # zlib validation
    try:
        decompressed = zlib.decompress(decoded)
    except Exception:
        raise PoBParseError("Failed to decompress (corrupted data)")

    # XML validation
    try:
        tree = xmltodict.parse(decompressed)
    except Exception:
        raise PoBParseError("Unable to parse XML structure")
```

### 10.3 Dependency Security

**Automated Scanning:**
```bash
# Check for known vulnerabilities
pip-audit

# Update vulnerable dependencies
pip install --upgrade <package-name>
```

**Pinned Versions:**
- All dependencies use exact versions (`==`)
- Prevents unexpected updates with vulnerabilities
- Manually review and test updates

**Supply Chain Security:**
- Verify package integrity (pip checksums)
- Use official PyPI packages only
- Review dependency tree (pipdeptree)

### 10.4 Runtime Security

**Network Binding:**
```python
# src/main.py
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",  # Localhost only, NOT 0.0.0.0
        port=5000,
        debug=False,  # Disable debug mode (prevents code execution)
        threaded=True
    )
```

**Lua Sandbox:**
- Lupa provides basic sandboxing
- PoB engine is read-only (no file writes)
- Timeouts prevent infinite loops (5s per calculation)

**Resource Limits:**
- Max 10 concurrent optimizations
- 5-minute timeout per optimization
- Session cleanup after 15 minutes
- No persistent file storage

**Data Privacy:**
- No logging of PoB codes
- No analytics sent to external services
- No persistent storage (all in-memory)
- Session data cleared on completion

---

## 11. Testing Strategy

### 11.1 Testing Pyramid

```
                  /\
                 /  \
                /E2E \       10% - Full workflow (slow, brittle)
               /______\
              /        \
             /Integration\   30% - Module interaction
            /____________\
           /              \
          /  Unit Tests    \  60% - Fast, isolated, mocked
         /__________________\
```

**Coverage Targets:**
- Overall: >80%
- Critical paths (calculator, optimizer, parsers): >90%
- UI/frontend: Manual testing (not counted in coverage)

### 11.2 Unit Testing (60% of tests)

**Characteristics:**
- Fast (<1s for full suite)
- Isolated (no external dependencies)
- Mocked dependencies (mock PoB engine, mock HTTP)

**Testing Approach:**
```python
# tests/unit/test_pob_parser.py
def test_parse_valid_pob_code():
    code = "eNqVVktv...valid..."
    build = parse_pob_code(code)
    assert build.level == 90
    assert build.character_class == CharacterClass.WITCH

def test_parse_invalid_base64():
    with pytest.raises(PoBParseError, match="Invalid Base64"):
        parse_pob_code("invalid!!!")

def test_parse_oversized_code():
    code = "A" * (101 * 1024)  # 101KB
    with pytest.raises(PoBParseError, match="too large"):
        parse_pob_code(code)
```

**Mock Strategy:**
```python
# tests/unit/test_hill_climbing.py
@pytest.fixture
def mock_calculator():
    calculator = Mock()
    calculator.calculate_stats.return_value = BuildStats(
        total_dps=100000,
        effective_hp=50000,
        # ...
    )
    return calculator

def test_hill_climbing_finds_improvement(mock_calculator):
    optimizer = HillClimbingOptimizer(calculator=mock_calculator)
    result = optimizer.optimize(initial_build, goal="maximize_dps")
    assert result.improvement > 0
```

### 11.3 Integration Testing (30% of tests)

**Characteristics:**
- Moderate speed (10-30s for suite)
- Real dependencies (actual PoB engine, real Flask app)
- Module interaction testing

**Testing Approach:**
```python
# tests/integration/test_pob_engine_integration.py
@pytest.mark.slow
def test_pob_calculation_accuracy():
    """
    Test PoB engine calculates stats matching official PoB GUI.
    Requires: external/pob-engine/ initialized
    """
    with open("tests/fixtures/sample_warrior_build.txt") as f:
        pob_code = f.read()

    build = parse_pob_code(pob_code)
    engine = get_pob_engine()
    stats = engine.calculate_stats(build)

    # Expected values verified in PoB GUI
    assert abs(stats.total_dps - 125430) < 100  # ±0.1%
    assert abs(stats.effective_hp - 42150) < 100

@pytest.mark.slow
def test_batch_calculation_performance():
    """Test batch calculation meets performance target (FR-3.3)."""
    build = load_sample_build()
    engine = get_pob_engine()

    # Time 1000 calculations
    start = time.time()
    for _ in range(1000):
        engine.calculate_stats(build)
    elapsed_ms = (time.time() - start) * 1000

    assert elapsed_ms < 1000, f"Too slow: {elapsed_ms:.0f}ms"
```

### 11.4 End-to-End Testing (10% of tests)

**Characteristics:**
- Slow (1-5 minutes per test)
- Full system testing (browser → server → optimization)
- Real user workflows

**Testing Approach:**
```python
# tests/e2e/test_optimization_workflow.py
def test_full_optimization_workflow(client):
    """
    Test complete workflow: submit → progress → results.
    This is the primary E2E test.
    """
    # Load sample PoB code
    pob_code = load_sample_build_code()

    # [1] Submit optimization
    response = client.post('/optimize', data={
        'pob_code': pob_code,
        'goal': 'maximize_dps',
        'unallocated_points': 10,
        'respec_points': 5
    }, follow_redirects=False)

    assert response.status_code == 302
    session_id = response.location.split('/')[-1]

    # [2] Poll progress until complete
    max_wait = 60  # 1 minute timeout
    start = time.time()

    while time.time() - start < max_wait:
        response = client.get(f'/api/progress/{session_id}')
        data = response.get_json()

        if data['status'] == 'complete':
            break
        time.sleep(2)
    else:
        pytest.fail("Optimization timed out")

    # [3] Fetch results
    response = client.get(f'/results/{session_id}')
    assert response.status_code == 200
    assert b"Optimization Complete" in response.data
```

### 11.5 Test Execution

**Running Tests:**
```bash
# Run all tests
pytest

# Run only unit tests (fast)
pytest tests/unit/

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_pob_parser.py

# Run tests matching pattern
pytest -k "test_parse"

# Skip slow tests (integration/E2E)
pytest -m "not slow"

# Verbose output
pytest -v
```

**Continuous Testing:**
```bash
# Watch mode (re-run on file changes)
pytest-watch tests/
```

**Coverage Report:**
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 12. Architecture Decision Records

### ADR-001: Flask over FastAPI

**Date:** 2025-10-09
**Status:** Accepted

**Context:**
Need web framework for local MVP. Options: Flask, FastAPI, Django.

**Decision:** Use Flask 3.0.

**Rationale:**
- **Simplicity:** Minimal boilerplate, easy for beginners
- **Synchronous model:** Matches Lupa's blocking Lua calls (no async complexity)
- **Mature ecosystem:** Extensive documentation, large community
- **Threading support:** Built-in for concurrent requests
- **SSE support:** Possible with generators

**Alternatives Considered:**
- **FastAPI:** Requires async/await (complicates Lupa integration), over-engineering for local MVP
- **Django:** Too heavyweight, includes unused features (ORM, admin, auth)

**Consequences:**
- Simpler codebase, faster development
- Limited async capabilities (acceptable for local use)
- May need migration if scaling to thousands of concurrent users (V2 concern)

**Related Requirements:** NFR-5 (Maintainability), NFR-6 (Portability)

---

### ADR-002: Bootstrap 5 for Styling

**Date:** 2025-10-09
**Status:** Accepted

**Context:**
Need clean, professional UI with progress visualization and accessibility.

**Decision:** Use Bootstrap 5 via CDN.

**Rationale:**
- **Time savings:** Professional components out-of-the-box
- **Accessibility:** WCAG 2.1 AA compliance by default (FR-1.7 requirement)
- **Progress UI:** Built-in progress bars, spinners, alerts
- **No build step:** Include via CDN (simpler than npm + webpack)
- **Responsive:** Grid system handles different screen sizes

**Alternatives Considered:**
- **Tailwind CSS:** Utility-first, but requires build step (npm, PostCSS)
- **Plain CSS:** Maximum control, but weeks of development time
- **Material-UI:** React-based, requires SPA (over-engineering)

**Consequences:**
- Larger initial page load (~200KB CSS from CDN), acceptable for local
- Less customization flexibility (Bootstrap look-and-feel)
- Easy for beginners to understand and modify

**Related Requirements:** FR-1.7 (Accessibility), NFR-4 (Usability)

---

### ADR-003: Server-Sent Events for Progress

**Date:** 2025-10-09
**Status:** Accepted

**Context:**
Need real-time progress updates during optimization (FR-4.4). Options: SSE, WebSockets, polling.

**Decision:** Use SSE with polling fallback.

**Rationale:**
- **SSE perfect for one-way server→client streaming**
- **Built into browsers** (EventSource API)
- **Simpler than WebSockets** (no bidirectional communication needed)
- **Automatic reconnection** on disconnect
- **HTTP/1.1 compatible** (no HTTP/2 requirement)

**Alternatives Considered:**
- **WebSockets:** Bidirectional, but we only need server→client. More complex setup.
- **Polling only:** Simpler, but higher overhead (client requests every 2s). Used as fallback.

**Consequences:**
- Efficient real-time updates
- One persistent connection per optimization (acceptable for 10 concurrent users)
- Fallback ensures compatibility with all browsers

**Related Requirements:** FR-4.4 (Real-time progress), NFR-1 (Performance)

---

### ADR-004: In-Memory Session Storage

**Date:** 2025-10-10
**Status:** Accepted

**Context:**
Need session storage for optimization state. Options: In-memory, Redis, database.

**Decision:** Use in-memory Python dict with threading.Lock.

**Rationale:**
- **Local MVP scope** (single user, localhost deployment)
- **Simple implementation** (no external dependencies)
- **Fast access** (no network overhead)
- **Automatic cleanup** (15-minute expiration)

**Alternatives Considered:**
- **Redis:** Over-engineering for single-user local deployment
- **Database:** Persistent storage not needed (no history tracking in MVP)

**Consequences:**
- State lost on server restart (acceptable for local use)
- Limited to single-server deployment
- Will need Redis if scaling to multi-user/distributed deployment

**Migration Path:** If scaling to production:
1. Replace dict with Redis client
2. Implement session serialization (pickle or JSON)
3. Add session persistence

**Related Requirements:** NFR-6 (Portability), NFR-9 (Operational)

---

## 13. Implementation Roadmap

### 13.1 Epic 1: PoB Calculation Engine Integration (Weeks 1-2)

**Week 1:**
- Set up repository structure (source tree as specified)
- Initialize PoB submodule (`external/pob-engine/`)
- Implement Base64 → zlib → XML parsing (`parsers/pob_parser.py`)
- Implement XML → zlib → Base64 generation (`parsers/pob_generator.py`)
- Write unit tests for parser (valid codes, invalid codes, edge cases)
- **Deliverable:** Can parse and generate PoB codes with 100% accuracy

**Week 2:**
- Lupa integration: Load HeadlessWrapper.lua (`calculator/pob_engine.py`)
- Implement Python stub functions (`calculator/stub_functions.py`)
- Load passive tree graph (`calculator/passive_tree.py`)
- Test single build calculation (compare with PoB GUI, ±0.1% tolerance)
- Batch performance optimization (target: 1000 calculations <1s)
- **Deliverable:** PoB calculations working with required accuracy and performance

**Acceptance Criteria:**
- 100 sample builds calculated with 100% success rate
- <100ms per calculation (single)
- 150-500ms for 1000 calculations (batch)
- ±0.1% accuracy vs PoB GUI

---

### 13.2 Epic 2: Core Optimization Engine (Weeks 3-4)

**Week 3:**
- Load passive tree graph (PassiveTree.lua → adjacency list)
- Implement tree connectivity validation (BFS algorithm, `optimizer/tree_validator.py`)
- Implement neighbor generation (`optimizer/neighbor_generator.py`)
- Write unit tests for tree validator (connected trees, disconnected trees)
- **Deliverable:** Tree validation working correctly

**Week 4:**
- Implement hill climbing algorithm (`optimizer/hill_climbing.py`)
- Dual budget constraint tracking (`optimizer/budget_tracker.py`)
- Convergence detection (no improvement for 50 iterations)
- Integration tests: Full optimization pipeline (parser → calculator → optimizer)
- **Deliverable:** Optimization algorithm producing improved builds within budget

**Acceptance Criteria:**
- 8%+ median improvement on test builds
- 80%+ of non-optimal builds improved
- <5 minute completion time
- All trees remain valid (connected, within budget)

---

### 13.3 Epic 3: User Experience & Reliability (Weeks 5-6)

**Week 5:**
- Flask application structure (`web/app.py`, `web/routes.py`)
- HTML templates with Bootstrap 5 (`frontend/templates/`)
- Form submission → session creation → background thread
- SSE progress streaming (`web/sse.py`)
- Results page with before/after comparison
- **Deliverable:** Basic UI working end-to-end

**Week 6:**
- Error handling (FR-1.3 structured errors, `frontend/templates/error.html`)
- Session timeout and cleanup (15-minute expiration)
- Optimization cancellation
- File-based logging (`logs/optimizer.log`)
- E2E testing (full workflow validation)
- **Deliverable:** Complete local web application, production-ready

**Acceptance Criteria:**
- 95%+ parse success rate
- Clear error messages for all failure modes
- 50+ consecutive optimizations without memory leaks
- Real-time progress updates (every 2s)

---

### 13.4 Weeks 7-8: Polish and Validation

**Testing Phase:**
- Run 50+ test optimizations with personal builds
- Fix bugs discovered during testing
- Performance tuning if needed (profile, optimize)
- Documentation updates (README, setup instructions)
- Optional: Package as executable (PyInstaller for non-technical users)

**Validation:**
- Verify all FRs satisfied (checklist review)
- Verify all NFRs met (performance testing, coverage report)
- Generate cohesion check report (final validation)
- Update project-workflow-analysis.md (mark complete)

**Deliverable:** MVP ready for personal use

---

## 14. Appendices

### 14.1 Glossary

**Terms for Beginners:**

- **Base64:** Encoding scheme converting binary data to text (ASCII). PoB codes use this.
- **zlib:** Compression library. Makes PoB codes smaller (reduces file size).
- **XML:** eXtensible Markup Language. PoB stores build data in XML format.
- **Flask:** Python web framework. Handles HTTP requests, renders HTML.
- **Jinja2:** Template engine for Flask. Lets you embed Python logic in HTML.
- **SSE (Server-Sent Events):** Protocol for server→client streaming over HTTP.
- **Threading:** Running multiple tasks concurrently in same process.
- **LuaJIT:** Just-In-Time compiler for Lua. Makes Lua code run fast.
- **Lupa:** Python library providing LuaJIT bindings (lets Python call Lua).
- **Hill Climbing:** Optimization algorithm that incrementally improves solutions.
- **Monolith:** Single application (opposite of microservices).
- **Modular:** Code organized into separate modules with clear responsibilities.
- **Git Submodule:** Way to include one Git repository inside another.
- **BFS (Breadth-First Search):** Graph traversal algorithm for connectivity checking.
- **Dataclass:** Python class for storing data (auto-generates __init__, __repr__, etc.).
- **Type Hints:** Python annotations specifying expected types (e.g., `def foo(x: int) -> str:`).

### 14.2 Reference Documents

**Primary Documents:**
- `PRD.md` - Product Requirements (22 FRs, 9 NFRs, 3 epics, 25-31 stories)
- `project-workflow-analysis.md` - Project classification (Level 3)
- `cohesion-check-report.md` - Requirements coverage validation
- `epic-alignment-matrix.md` - Epic-to-component mapping

**Tech Specs (Epic-Level):**
- `tech-spec-epic-1.md` - Epic 1: PoB Calculation Engine Integration
- `tech-spec-epic-2.md` - Epic 2: Core Optimization Engine
- `tech-spec-epic-3.md` - Epic 3: User Experience & Local Reliability

**Supporting Documents:**
- `implementation-guide.md` - Beginner-friendly walkthrough of this architecture
- `validation-report-*.md` - Architecture validation reports

**Architecture Decision Records:**
- `ADRs/ADR-001-flask-over-fastapi.md`
- `ADRs/ADR-002-threading-over-asyncio.md`
- `ADRs/ADR-003-bootstrap-styling.md`
- `ADRs/ADR-004-sse-progress-reporting.md`
- `ADRs/ADR-005-in-memory-sessions.md`

### 14.3 Requirements Traceability

**Epic → FR Mapping:**
- Epic 1 → FR-1.x (PoB parsing), FR-3.x (PoB calculation engine)
- Epic 2 → FR-4.x (Optimization algorithm), FR-2.x (Goal selection)
- Epic 3 → FR-5.x (Results display), FR-6.x (Analytics), FR-1.7 (Accessibility)

**Epic → NFR Mapping:**
- Epic 1 → NFR-1 (Performance: <100ms calculations), NFR-7 (Compatibility: PoB XML)
- Epic 2 → NFR-1 (Performance: <5 min optimization), NFR-2 (Reliability: circuit breaker)
- Epic 3 → NFR-3 (Security), NFR-4 (Usability), NFR-5 (Maintainability), NFR-9 (Operational)

**Full traceability matrix available in:** `cohesion-check-report.md`

### 14.4 Contact and Support

**For Implementation Questions:**
- Refer to `implementation-guide.md` (beginner-friendly walkthrough)
- Review relevant tech spec (`tech-spec-epic-*.md`)
- Check ADRs for decision rationale

**For Architecture Questions:**
- This document is authoritative reference
- Validation reports explain checklist compliance
- Cohesion check report shows requirements coverage

---

**Document Status:** ✅ Complete and Ready for Implementation
**Last Updated:** 2025-10-10
**Next Steps:** Review with stakeholders → Begin Epic 1 implementation → Follow tech specs

---

_End of Solution Architecture Document_
