# Project Workflow Analysis

**Date:** 2025-10-08
**Project:** poe2_optimizer_v6
**Analyst:** Alec

## Assessment Results

### Project Classification

- **Project Type:** Web application
- **Project Level:** Level 3 (Full product - 12-40 stories, 2-5 epics, full PRD + architect handoff)
- **Instruction Set:** instructions-lg.md (PRD workflow for Level 3 projects)

### Scope Summary

- **Brief Description:** A focused web-based tool ("The Passive Tree Grinder") that optimizes passive skill trees for Path of Exile 2 builds using headless Path of Building calculations. Delivers 5-15% performance improvements in 30 seconds by computationally exploring tree configurations that would take players 3+ hours to test manually.
- **Estimated Stories:** 20-35 stories
- **Estimated Epics:** 3-5 epics
- **Timeline:** 2 months for MVP launch (target: December 2025)

### Context

- **Greenfield/Brownfield:** Greenfield (new project, no existing codebase)
- **Existing Documentation:**
  - Product Brief (comprehensive, 28K+ tokens)
  - Technical Research Report (headless PoB integration evaluation)
  - Lupa Library Deep Research (implementation patterns)
  - Brainstorming Session Results (project scoping and ideation)
  - Research Summary (consolidated findings)
- **Team Size:** Solo developer (Alec)
- **Deployment Intent:** Public web application, free during MVP phase, future monetization potential post-PMF validation

## Recommended Workflow Path

### Primary Outputs

Based on Level 3 classification, this workflow will generate:

1. **Product Requirements Document (PRD)** - Full specification including:
   - Product vision and goals
   - User personas and use cases
   - Detailed feature specifications
   - Success metrics and KPIs
   - Technical architecture overview
   - Risk assessment and mitigation strategies

2. **Epic Breakdown Document** - High-level epic structure:
   - 3-5 major epics covering full MVP scope
   - Epic descriptions with business value
   - Epic dependencies and sequencing
   - Story count estimates per epic

3. **Architecture Handoff** - Technical foundation for development:
   - System architecture diagram
   - Technology stack decisions
   - Integration patterns (Python + Lupa + HeadlessWrapper.lua)
   - Performance requirements and targets
   - Deployment strategy

4. **Tech Specification Document** (via 3-solutioning workflow):
   - Detailed technical implementation guide
   - API specifications
   - Data models and schemas
   - Algorithm implementation details
   - Testing strategy

### Workflow Sequence

1. **Current Step:** Project Planning (plan-project workflow)
2. **Next:** PRD Generation (prd/workflow.yaml with instructions-lg.md)
3. **Then:** Epic Breakdown (epics-template.md generation)
4. **Then:** Architecture & Solutioning (invoke 3-solutioning workflow for tech specs)
5. **Final:** Validation checklist review

### Next Actions

After this analysis is complete:

1. Invoke PRD workflow for Level 3 projects (loads instructions-lg.md)
2. Generate comprehensive PRD using product brief and research as foundation
3. Break down into 3-5 epics with story estimates
4. Hand off to architecture/solutioning workflow for detailed tech specs

## Special Considerations

### Ruthless Scope Discipline (Core Philosophy)

The project explicitly follows a "do ONE thing perfectly" philosophy:
- **In scope:** Passive tree optimization only
- **Out of scope:** AI chat, item suggestions, skill gem optimization, full build generation
- This scope discipline is the competitive advantage (2-month MVP vs. 12+ month competitors)

### Technical Risk Mitigation

**Highest Risk Component:** Headless PoB integration
- **Status:** Already validated through 3-day prototype plan
- **Solution:** Lupa + HeadlessWrapper.lua (proven approach)
- **Performance:** 150-500ms for 1000 calculations (exceeds <1s requirement)

### Trust as the Product

The algorithm is not the product—trust is:
- Transparency (real-time progress messages)
- Verification (PoB codes users can inspect)
- Mathematical proof (hard numbers, not promises)
- Honest limitations (clear disclaimers about unsupported build types)

### Budget Constraints Feature

Essential for practical utility:
- User's available respec points are finite
- System must support "free optimization" (zero respec cost)
- Show cost breakdown ("requires 8 respec points")
- Prevents suggesting perfect builds that are financially impossible

### Performance Expectations

- Small builds: 1-2 minutes optimization time
- Complex builds: Up to 5 minutes (acceptable for thorough optimization)
- Real-time progress reporting throughout process
- Quality over speed (thorough > fast)

### MVP Success Criteria

Month 3 targets indicate genuine product-market fit:
- 2,000 optimizations/week
- 30% repeat usage rate
- 8%+ median improvement delivered
- Referenced in 10+ build guides or streamer content

## Technical Preferences Captured

### Technology Stack

**Backend:**
- **Language:** Python (confirmed)
- **Lua Integration:** Lupa library (LuaJIT embedded in Python)
- **PoB Integration:** HeadlessWrapper.lua (official PoB headless mode)
- **Performance:** Sub-1 second for 1000 calculations target

**Frontend:**
- **Platform:** Web-based application
- **Complexity:** Minimal (single page with text box, dropdown, button)
- **Framework:** TBD (keep simple for MVP)

**Optimization Algorithm:**
- **MVP:** Hill climbing (simple, fast, explainable)
- **V2:** Simulated annealing layer (better global optima)
- **Rejected:** Genetic algorithms, constraint solvers (over-engineering)

**Architecture:**
- **Pattern:** Backend service with headless PoB calculation engine
- **Data Flow:** PoB code input → Parse → Optimize → Generate new PoB code
- **Integration:** In-process Lupa runtime (no subprocess overhead)

### Performance Targets

- **Single calculation:** <100ms
- **Batch calculations:** 150-500ms for 1000 iterations
- **Optimization session:** <5 minutes for complex builds
- **Startup time:** <5 seconds initialization
- **Memory footprint:** <100MB recommended limit

### Data Requirements

**Must have access to:**
- PoB XML parsing (Base64 → zlib decompress → XML)
- Passive skill tree data (JSON/Lua graph structure)
- PoB calculation engine (via HeadlessWrapper.lua)
- Character/class starting data
- Node connectivity and stats

### Deployment Strategy

- **MVP Phase:** Simple VPS or serverless deployment
- **Infrastructure Budget:** <$50/month during validation
- **Scaling Strategy:** Horizontal scaling if PMF achieved
- **Monitoring:** Google Analytics 4 + backend logging

### Quality Attributes

- **Accuracy:** 100% calculation parity with official PoB (within 0.1% tolerance)
- **Reliability:** 95%+ successful completion rate
- **Determinism:** Same input → same output every time
- **Transparency:** Clear progress messages and result explanations

### Stub Functions Required

For HeadlessWrapper.lua integration:
- Compression: `Deflate`/`Inflate` using Python zlib
- Console: `ConPrintf`, `ConPrintTable` (no-ops)
- System: `SpawnProcess`, `OpenURL` (no-ops)
- Optional modules: Skip lcurl.safe for headless mode

---

_This analysis serves as the routing decision for the adaptive PRD workflow and will be referenced by future orchestration workflows._
