# poe2_optimizer_v6 Product Requirements Document (PRD)

**Author:** Alec
**Date:** 2025-10-08
**Project Level:** Level 3 (Full product - 12-40 stories, 2-5 epics)
**Project Type:** Local web application (localhost)
**Target:** MVP launch within 2 months for personal use and validation before public release

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2025-10-06 | Initial draft - Product description, goals, context, initial FR outline (22 FRs) | Alec |
| 0.2 | 2025-10-07 | Added comprehensive FR details with acceptance criteria. Added NFRs 1-9. Expanded user journeys (3 complete journeys). | Alec |
| 0.3 | 2025-10-07 | Added FR-1.7 (Accessibility - WCAG 2.1 AA), FR-4.5 (Confidence Score), FR-4.6 (Cancellation). Refined dual budget constraint logic (FR-2.2, FR-4.3). | Alec |
| 0.4 | 2025-10-08 | Added Development Prerequisites section with Tier 0-4 dependency matrix. Expanded epic breakdown with story references. Added NFR-10 (Internationalization). | Alec |
| 0.5 | 2025-10-08 | Refined error handling patterns (FR-1.3 structured format). Added session isolation requirements (FR-3.5). Clarified optimization timeout strategy (FR-3.4). | Alec |
| 1.0 | 2025-10-08 | Final review and approval. Added Out of Scope section. Finalized Next Steps. Document marked COMPLETE for architecture handoff. | Alec |
| 1.1 | 2025-10-09 | Post-validation improvements: Added Document Approval section, Revision History table. NFR simplification (moved NFR-10 to Out of Scope, simplified NFR-6). | John (PM) |

**Current Version:** 1.1 (Post-Validation Edition)

---

## Description, Context and Goals

### Product Description

**The PoE 2 Passive Tree Optimizer** (internally known as "The Passive Tree Grinder") is a focused web-based optimization tool that automatically discovers mathematically superior passive skill tree configurations for Path of Exile 2 builds. By leveraging Path of Building's proven calculation engine through headless automation, the tool solves the single most tedious and complex optimization challenge players face: efficiently allocating 100+ passive points across a 1,500-node skill tree.

**Core Value Proposition:** Transform 3+ hours of manual passive tree experimentation into a 30-second automated optimization that delivers verifiable 5-15% performance improvements with mathematical proof.

**Strategic Differentiation:** Ruthless scope discipline. Unlike existing tools that attempt comprehensive build generation, this tool does ONE thing perfectly: passive tree optimization. This focused approach enables a 2-month MVP timeline versus competitors' 12+ month "complete solutions" through surgical focus, transparent mathematics, and honest limitation disclosure.

**Technical Foundation:** Python backend using Lupa library to execute Path of Building's official Lua calculation engine in headless mode via HeadlessWrapper.lua, achieving 150-500ms throughput for 1000+ calculations per optimization session with 100% accuracy guarantee.

**Target Users:** Endgame Path of Exile 2 players (level 85-100) seeking competitive advantages through min-maxed character builds, with secondary appeal to mid-game players (level 40-85) optimizing progression paths.

**User Experience Flow:**
1. Player pastes Path of Building code into text box
2. Player selects optimization goal from dropdown (Maximize DPS, Maximize EHP, or balanced approach)
3. Player optionally specifies respec point budget constraint
4. System processes optimization (30 seconds to 5 minutes depending on complexity)
5. Player receives before/after comparison with percentage improvements and new PoB code
6. Player imports optimized code into Path of Building to verify and implement changes

**Success Moment:** Player discovers an 8% DPS increase by reallocating just 6 passive points—an improvement they would never have found manually in 10 hours of experimentation. They bookmark the tool and recommend it to their guild.

### Deployment Intent

**Phase:** Local MVP for Personal Use & Validation
**Launch Target:** December 2025 (within 2 months)
**Availability:** Local-only application (runs on localhost)
**Infrastructure:** Zero-cost open-source stack
**Monetization Strategy:** None - open-source project

This is a **local development tool MVP** designed to:
- Prove technical feasibility before public deployment
- Validate optimization algorithm quality with personal builds
- Iterate on UX and feature set without deployment complexity
- Build complete, polished product before opening to public
- Eliminate hosting costs during development phase

**Deployment Model:**
```
├── Runtime: Python 3.10+ on developer machine
├── Interface: Local web UI (Flask at localhost:5000)
├── Data: PoB repository as Git submodule (external/pob-engine/)
├── Cost: $0 (open-source stack only)
└── Users: Single user (developer) running locally
```

**Success Criteria for Moving Beyond Local MVP:**
- Optimization algorithm delivers 8%+ median improvement on 20+ test builds
- 95%+ successful completion rate for valid PoB codes
- Local UX polished and intuitive (sub-5-minute learning curve)
- Feature-complete: Dual budget system, metric selection, progress tracking
- Codebase ready for open-source release or public deployment

**Future Deployment Path (Post-Validation):**
Once local MVP proves value, potential next steps:
- **Option A:** Open-source release on GitHub for community self-hosting
- **Option B:** Public web deployment with community hosting/donations
- **Option C:** Package as standalone executable (PyInstaller) for easy distribution

**Strategic Rationale:** Perfect the product locally before exposing to users. Avoid deployment complexity, hosting costs, and scaling challenges until core value is proven.

### Context

#### The Problem

Path of Exile 2 players face a mathematically intractable optimization problem: determining the optimal allocation of approximately 120 passive skill points across a tree of 1,500+ interconnected nodes, each offering different statistical bonuses with complex multiplicative interactions. This combinatorial explosion (approximately 10^250 possible configurations) makes exhaustive human evaluation impossible. Players currently spend 3-5 hours manually experimenting with passive tree configurations in Path of Building, testing combinations one-by-one, often gaining only 2-5% performance improvement despite massive time investment. Even experienced players routinely leave 8-15% performance gains undiscovered due to suboptimal pathing—wasting 5-10 passive points on weak travel nodes when better routes exist. The resource cost is significant: respec points require valuable in-game currency (15-25 respec points = 2-4 hours of farming), creating "respec anxiety" where players avoid experimentation for fear of wasting resources. This often leads to build abandonment when players can't diagnose why "damage is low" or "I keep dying" when the actual issue is passive tree inefficiency.

#### Critical Dependencies

This project's feasibility depends entirely on the Path of Building open-source ecosystem:

**Foundation Dependency: PoE 2 Path of Building (Open-Source)**
```
Repository: https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2
Status: Available, community-maintained, MIT licensed

Required Components:
├── /src/Data/            → Passive tree graph data (JSON/Lua format)
├── /src/Modules/         → Calculation engine (DPS, EHP, resistances)
├── /HeadlessWrapper.lua  → Official headless execution interface
├── /src/Classes/         → Core calculation classes (Build, Skill, Item)
└── /runtime/             → LuaJIT runtime dependencies

Integration Strategy (Recommended):
├── Method: Git submodule in /external/pob-engine/
├── Version Control: Pin to specific commit hash for stability
├── Update Cadence: Manual sync when PoE 2 game patches release
└── Folder Access: Full repo visible to AI for architecture analysis

AI Development Needs:
├── Full repository structure visible in project workspace
├── Key files to analyze: HeadlessWrapper.lua, Data/PassiveTree.lua
├── Module dependency graph documentation
└── PoB version compatibility tracking
```

**Dependency Chain:**
```
Our Tool
  ↓ depends on
Path of Building PoE2 (Open-Source)
  ↓ depends on
PoE 2 Game Data (Exported by GGG or community)
  ↓ depends on
PoE 2 Launch & Ongoing Support
```

**Risk Mitigation:** PoB has proven track record from PoE 1 (6+ years, 100K+ downloads/league). Community-maintained with active development. PoE 2 version already exists in beta state.

**Repository Setup Guide** (beginner-friendly instructions included in Architecture phase documentation)

#### Why Now

Path of Exile 2's launch represents a greenfield opportunity. The game's complexity and the community's reliance on Path of Building create sustained demand for optimization tools regardless of league timing. Recent technical research has validated the feasibility of headless Path of Building integration using Python + Lupa + HeadlessWrapper.lua, achieving 150-500ms performance for 1000+ calculations—well within the sub-1-second requirement for iterative optimization.

**Market Validation:**
- PoE 2 community consistently requests "better tree optimization tools" (500+ upvotes on Reddit)
- Path of Building receives 100K+ downloads per league launch (proven demand)
- Existing solutions are inadequate and create market gap:
  - **Path of Building (Manual):** Provides calculation accuracy but requires human decision-making—the very problem we're solving
  - **Build Guides (Static):** Show final trees without reasoning, don't account for player-specific gear, become outdated with patches
  - **"Build Creator" Tools (Vaporware):** Attempt full build generation, face exponential complexity, lack trust due to black-box recommendations, stuck in 12+ month development cycles

**Technical Validation Complete:**
- Lupa + HeadlessWrapper.lua integration proven feasible
- Performance targets exceeded (150-500ms for 1000 calculations vs. <1s requirement)
- 100% calculation accuracy achievable using official PoB engine
- All critical technical risks validated through 3-day prototype research

**Strategic Timing:**
A surgical, focused tool that does ONE thing perfectly—passive tree optimization—can capture this market with a 2-month MVP timeline while competitors remain mired in scope creep and "complete solution" vaporware. The ruthless scope discipline is the competitive advantage: ship fast, build trust, iterate based on real usage.

### Goals

#### 1. Validate Technical Feasibility and Launch MVP Within 2 Months
**Target:** MVP deployed and accepting user traffic by December 2025
**Measurement:** Deployment date and system accepting real user optimizations
**Rationale:** Prove headless PoB integration works in production before larger investment. Capture early-league demand window when players are actively optimizing builds.
**Success Criteria:**
- System processes 95%+ of valid PoB codes successfully
- Optimization completes in <5 minutes for complex builds
- Results match official Path of Building within 0.1% tolerance

#### 2. Achieve Product-Market Fit Validation Within 6 Months
**Target:** 30% of users return for second optimization session within same league
**Measurement:** Repeat usage rate tracked via analytics
**Rationale:** Distinguish genuine utility from launch novelty. If users come back, the tool solves a real problem worth their time.
**Success Criteria:**
- 30%+ repeat usage rate (users optimizing 2+ builds per league)
- 8%+ median improvement delivered (demonstrable value)
- NPS ≥40 (users would recommend to others)

#### 3. Establish Tool as Community-Recognized Standard
**Target:** Referenced in 10+ popular build guides or streamer content within first league
**Measurement:** Manual tracking of Reddit, Discord, YouTube, Twitch mentions
**Rationale:** Organic community adoption signals trust and utility. Becoming the default recommendation for passive tree optimization creates sustainable growth.
**Success Criteria:**
- Mentioned in 10+ build guides or streams
- 5+ organic community mentions per week on r/pathofexile or Discord
- Users share results without prompting

#### 4. Build Sustainable User Base for Long-Term Viability
**Target:** 5,000 unique users and 10,000 optimization sessions within first league
**Measurement:** Google Analytics 4 + backend logging
**Rationale:** Sufficient user volume to validate patterns, gather feedback, and demonstrate market demand. Establishes foundation for future growth and potential monetization.
**Success Criteria:**
- 5,000 unique users (Month 6 target)
- 10,000+ completed optimizations
- 2.5 average optimizations per user (engagement depth)
- 70%+ optimization completion rate (UI clarity and reliability)

#### 5. Maintain Lean Operations During Validation Phase
**Target:** Monthly hosting costs <$50 while supporting target user volume
**Measurement:** Monthly infrastructure billing statements
**Rationale:** Minimize financial risk during validation phase. Prove value before scaling costs. Keep breakeven achievable if future monetization is pursued.
**Success Criteria:**
- Infrastructure costs <$50/month during MVP phase
- <$200 total cash outlay for 6-month validation period
- System handles target load without performance degradation
- Clear scaling path identified if user volume exceeds projections

## Requirements

### Functional Requirements

#### FR Group 1: PoB Code Input & Validation

**FR-1.1: PoB Code Input Interface**
- System SHALL provide a large text input field for pasting Path of Building import codes
- Input field SHALL accept codes up to and including 100KB in size (100,000 bytes)
- Input field SHALL reject codes larger than 100KB and display error: "Build code too large (X KB). Maximum size: 100KB. Please verify this is a valid PoE 2 build."
- Input field SHALL provide visual feedback during paste operation (loading indicator showing "Processing...")
- **Acceptance Criteria:** User can paste any valid PoE 2 PoB code ≤100KB without truncation; codes >100KB clearly rejected with size information

**FR-1.2: PoB Code Parsing & Decoding**
- System SHALL decode Base64-encoded PoB codes to compressed format
- System SHALL decompress zlib-compressed data to XML format
- System SHALL parse XML structure to extract build data (character level, ascendancy, passive tree, items, skills, configuration)
- **Acceptance Criteria:** Successfully parse 95%+ of valid PoE 2 PoB codes; graceful error handling for corrupted codes

**FR-1.3: Input Validation & Error Handling**
- System SHALL validate PoB code format before processing
- System SHALL detect corrupted or invalid codes and display structured error messages containing:
  1. **Problem summary** (user-friendly language, no technical jargon)
  2. **Likely cause** (e.g., "Code may have been copied incorrectly")
  3. **Suggested action** (e.g., "Please re-copy the build code from Path of Building")
  4. **Optional:** Collapsible technical details for advanced users
- Error message format example:
  ```
  ❌ Unable to Load Build

  The build code appears to be corrupted or incomplete.

  This usually happens when:
  • Code was only partially copied from Path of Building
  • Code contains invalid characters

  Please try:
  1. Open Path of Building
  2. Click "Import/Export Build"
  3. Ensure entire code is selected and copied
  4. Paste here and try again

  [Show Technical Details ▼]
  ```
- **Acceptance Criteria:** All error messages follow structured format; users understand both problem and solution; 90%+ of users can self-recover from errors

**FR-1.4: Build Summary Display**
- System SHALL display parsed character summary for user confirmation (class, level, ascendancy, current DPS, current EHP)
- System SHALL show current passive point allocation count (e.g., "87/120 points allocated")
- System SHALL detect and display invalid stats (DPS=0, NaN values) with warning: "Unable to calculate DPS—verify build in PoB"
- System SHALL cross-validate passive point count against character level limits and flag discrepancies
- **Acceptance Criteria:** User can verify correct build was loaded before optimization; invalid data clearly flagged

**FR-1.5: Version Compatibility Detection** ⭐ NEW
- System SHALL detect PoE 1 vs PoE 2 build codes by analyzing XML structure and version markers
- System SHALL reject PoE 1 codes with clear message: "This appears to be a PoE 1 build. Please use a PoE 2 Path of Building code."
- System SHALL display detected PoB version and expected version for user awareness
- **Acceptance Criteria:** 0% false positives (valid PoE 2 codes never rejected); 95%+ PoE 1 code detection rate

**FR-1.6: Unsupported Build Type Detection** ⭐ NEW
- System SHALL detect and reject unsupported build types for MVP:
  - **Minion builds:** Detected if build has active minion skills OR allocates minion-specific passive nodes
  - **Totem builds:** Detected if build uses Totem support gems
  - **Trap/Mine builds:** Detected if build uses Trap or Mine support gems
  - **Complex trigger builds:** Detected if build uses Cast on Crit (CoC), Cast while Channelling (CwC), or similar triggers
- System SHALL display structured error message (consistent with FR-1.3 format):
  ```
  ❌ Build Type Not Supported (Yet!)

  Your build uses MINIONS which isn't supported in the MVP.

  ✅ What IS supported:
  • Direct damage builds (attacks, spells, DoT)
  • Self-cast and melee builds
  • Most defensive builds

  ⏳ Coming in V2:
  • Minion builds
  • Totems, traps, mines
  • Trigger-based builds

  Why the limitation?
  These build types require specialized calculation logic.
  We're focusing on getting core optimization perfect first.

  [Learn more about our roadmap]
  ```
- **Acceptance Criteria:** 95%+ detection rate for unsupported types; 0% false positives (supported builds never rejected); users understand what IS supported (not just what isn't); error format consistent with FR-1.3 structure

**FR-1.7: Accessibility (Basic WCAG 2.1 AA Compliance)** ⭐ NEW
- System SHALL implement basic accessibility features:
  - **Keyboard navigation:** Full workflow completable without mouse
    * Tab order logical: Input field → Goal dropdown → Budget input → Optimize button
    * Enter key submits form from any input field
    * Escape key closes modals/dialogs
  - **Screen reader support:**
    * Form labels properly associated with inputs (for/id attributes)
    * Progress updates announced to screen readers (aria-live="polite" regions)
    * Error messages announced immediately (aria-live="assertive")
  - **Visual accessibility:**
    * Color contrast ratios ≥4.5:1 for normal text (WCAG AA standard)
    * Focus indicators visible on all interactive elements (2px outline minimum)
    * No information conveyed by color alone (use icons + text for success/error states)
  - **Text scalability:**
    * Layout doesn't break when text scaled to 200% via browser zoom
    * Minimum font size: 14px for body text, 16px for input fields
- **Acceptance Criteria:** Automated WCAG scan passes at AA level (using axe or WAVE tools); manual keyboard-only navigation test successful; screen reader test (NVDA or JAWS) confirms all content accessible; high-contrast OS mode doesn't break layout

#### FR Group 2: Optimization Goal Selection

**FR-2.1: Optimization Goal Dropdown**
- System SHALL provide dropdown menu with predefined optimization goals:
  - "Maximize Total DPS" (default)
  - "Maximize Effective HP (EHP)"
  - "Maximize DPS while maintaining current EHP" (balanced)
- System SHALL allow only one goal selection per optimization session
- **Acceptance Criteria:** Clear goal descriptions; user understands what each option optimizes for

**FR-2.2: Budget Constraint (Unallocated Points + Respec Points)**
- System SHALL provide budget input with clear UI for TWO types of points:

  **Primary Input - Unallocated Passive Points:**
  - **Number input field:** "Unallocated points available"
  - **Placeholder:** "0" (default assumes all points already allocated)
  - **Helper text:** "Points you've earned but haven't spent yet (check character level vs allocated points)"
  - **Auto-detection:** System SHALL attempt to calculate from PoB code (character level - currently allocated points)
  - **Editable:** User can override if auto-detection wrong

  **Secondary Input - Respec Points:**
  - **Number input field:** "Respec points available"
  - **Placeholder:** "Leave blank for unlimited"
  - **Helper text:** "Currency to deallocate already-spent points (check PoB: Character Stats → Respec Points)"
  - **Quick select buttons:**
    * [Free (0)] - Sets respec to 0 (no deallocations allowed)
    * [Budget (15)] - Sets respec to 15 (common amount, user can modify)
    * [Unlimited] - Clears field (blank = no respec limit)

- System SHALL interpret combined budget as follows:
  - **Unallocated points (U):** Can allocate up to U new nodes at ZERO cost
  - **Respec points (R):** Can deallocate up to R nodes and reallocate them
  - **Total potential changes:** U free allocations + R deallocations + R reallocations

  **Example scenarios:**
  ```
  Scenario 1: U=15, R=0 (Free mode)
  → Can add 15 new nodes, cannot remove any existing nodes
  → Best for leveling up, adding new points efficiently

  Scenario 2: U=0, R=12 (Respec-only mode)
  → Cannot add new nodes, can swap 12 existing nodes for better ones
  → Best for level 100 characters wanting to optimize existing allocation

  Scenario 3: U=8, R=12 (Combined mode)
  → Can add 8 new nodes freely + swap 12 existing nodes
  → Most common scenario for leveling characters

  Scenario 4: U=0, R=blank (Theoretical respec)
  → All points already allocated, unlimited respec budget
  → Find absolute best tree ignoring respec cost
  ```

- System SHALL display budget mode to user during optimization:
  - "Optimizing with 15 unallocated + 12 respec points available"
  - "Optimizing with 8 unallocated points (no respec budget)"
  - "Optimizing with unlimited budget (theoretical best)"

- System SHALL respect both constraints during optimization:
  - Never allocate more than U new nodes
  - Never deallocate more than R nodes
  - Prioritize using unallocated points first (free) before suggesting respecs (costly)

- **Acceptance Criteria:**
  - System correctly distinguishes unallocated vs respec points
  - Auto-detection of unallocated points works 90%+ of time from PoB code
  - Users understand the difference between the two types
  - Optimization prioritizes free allocations over costly respecs
  - Results clearly show: "Used X of Y unallocated points, Z of W respec points"

**FR-2.3: Advanced Goal Options (Post-MVP)**
- System MAY support multi-objective optimization with sliders (e.g., "70% DPS focus, 30% EHP focus")
- System MAY support threshold constraints (e.g., "Maximize DPS while maintaining at least 75% all resistances")
- **Note:** Deferred to V2 based on user feedback

#### FR Group 3: Headless PoB Calculation Engine

**FR-3.1: Lupa + HeadlessWrapper Integration**
- System SHALL embed LuaJIT runtime via Lupa library in Python backend
- System SHALL load Path of Building's HeadlessWrapper.lua for headless execution
- System SHALL implement required stub functions (Deflate/Inflate using Python zlib, ConPrintf, ConPrintTable, SpawnProcess, OpenURL)
- **Acceptance Criteria:** PoB calculation engine loads without errors; stub functions prevent GUI dependencies

**FR-3.2: Build State Calculation**
- System SHALL accept build state as input (passive tree configuration, items, skills, configuration flags)
- System SHALL execute PoB calculation engine to compute stats (Total DPS, Effective HP, resistances, life, energy shield, mana)
- System SHALL return calculated stats to optimization algorithm
- **Acceptance Criteria:** Calculation results match official PoB GUI within 0.1% tolerance; deterministic results (same input → same output)

**FR-3.3: Batch Calculation Performance**
- System SHALL achieve batch calculation performance targets:
  - **Per optimization session (single user):** 1000 calculations in <1 second (target: 150-500ms)
  - **Hardware baseline:** Standard VPS (2 CPU cores, 4GB RAM) or equivalent serverless function
  - **Load condition (normal):** Server handling 1-5 concurrent optimizations
    * Performance: 150-500ms per 1000 calculations
    * CPU utilization: 40-60%
    * Memory usage: 500MB-600MB
  - **Load condition (heavy):** Server handling 6-10 concurrent optimizations
    * Performance may degrade to 500ms-1s per 1000 calculations (graceful degradation)
    * CPU utilization: 80-95%
    * Memory usage: 1-1.5GB
    * System SHALL prioritize fair scheduling (no session starved of resources)
    * System SHALL display to user: "Server busy—optimization may take longer than usual"
  - **At capacity (10 concurrent):** System considered at heavy load (acceptable for MVP)
    * 11th user receives 'Server at Capacity' message per FR-3.5 (no queuing in MVP)
- System SHALL reuse compiled Lua functions for batch operations (compile once, call 1000x)
- System SHALL limit memory footprint to <100MB per optimization session
- System SHALL monitor memory usage per batch and trigger garbage collection if needed
- System SHALL isolate each optimization session with separate LuaRuntime instance to prevent state interference
- **Acceptance Criteria:** Performance targets met on specified hardware under normal load (1-5 users); graceful degradation under heavy load (6-10 users, no crashes); fair resource sharing confirmed; users informed when performance will be slower; load testing validates 10 concurrent users complete optimizations without errors

**FR-3.4: Calculation Timeout & Error Recovery** ⭐ NEW
- System SHALL implement 5-second timeout per individual calculation to prevent infinite loops
- System SHALL catch and log Lua runtime errors without crashing the optimization session
- System SHALL provide graceful degradation: "Unable to calculate stats for this configuration—skipping variant"
- System SHALL log all unexpected Lua→Python function calls for debugging and stub coverage improvement
- **Acceptance Criteria:** 0% optimization session crashes due to edge case builds; <1% calculation timeout rate; all errors logged for analysis

**FR-3.5: Multi-User Session Isolation** ⭐ NEW
- System SHALL support concurrent optimization sessions from multiple users:
  - Each session SHALL have isolated LuaRuntime instance (no state sharing between users)
  - Each session SHALL have unique session ID for tracking and debugging
  - Sessions SHALL be stateless where possible (HTTP request contains context) OR session data stored server-side with expiration
  - System SHALL limit concurrent sessions per server instance: **10 simultaneous optimizations** (MVP target based on 2-core VPS)
- Session lifecycle management:
  1. User submits PoB code → Server creates unique session ID
  2. Optimization runs with isolated resources (dedicated LuaRuntime, memory allocation)
  3. Results returned to user → Session marked for cleanup
  4. **Timeout:** Sessions idle >15 minutes automatically terminated and resources freed
  5. **Cleanup timing (two-phase approach):**
     - **Cancelled sessions:** Immediate primary cleanup (2 seconds per FR-4.6) + background secondary cleanup
     - **Completed sessions:** Lazy cleanup within 5 minutes (resources freed but not urgent)
     - **Timed-out sessions:** Immediate primary cleanup (same as cancelled)
- Capacity management:
  - If server at capacity (10 active sessions), new requests receive HTTP 503 with message:
    ```
    Server at Capacity

    All optimization slots currently in use.

    Please wait 30-60 seconds and try again.

    Current queue: ~2 minutes average wait
    ```
- **Acceptance Criteria:** 10 concurrent users can optimize simultaneously without interference; session isolation verified (User A's optimization doesn't affect User B's results or performance); memory cleanup confirmed (completed sessions don't leak memory); capacity limits enforced (11th user gets clear "busy" message, not crash); load testing validates isolation and resource cleanup

#### FR Group 4: Passive Tree Optimization Algorithm

**FR-4.1: Hill Climbing Algorithm (MVP)**
- System SHALL implement hill climbing algorithm for passive tree optimization:
  - Start with user's current tree configuration
  - Iteratively test small changes (deallocate 1 point, allocate different nearby point)
  - Keep changes that improve objective function, discard changes that don't
  - Continue until no further improvements found (convergence)
- **Acceptance Criteria:** Algorithm produces measurable improvements (5-15% median gain); completes within 5 minutes for complex builds

**FR-4.2: Tree Connectivity Validation**
- System SHALL enforce passive tree pathing rules (all allocated nodes must be connected to character starting position)
- System SHALL never suggest trees that violate connectivity requirements
- System SHALL validate tree legality before returning results to user
- **Acceptance Criteria:** 100% of optimized trees are importable into official PoB without errors

**FR-4.3: Budget Enforcement (Dual Constraint)**
- System SHALL track and enforce TWO separate budget constraints:

  **Unallocated Points Constraint:**
  - Count new node allocations (nodes not in original tree)
  - Never exceed unallocated points budget (U)
  - Cost: FREE (no in-game currency required)

  **Respec Points Constraint:**
  - Count node deallocations (nodes removed from original tree)
  - Never exceed respec points budget (R)
  - Cost: EXPENSIVE (requires valuable in-game currency)

- System SHALL prioritize optimization strategy based on available budgets:
  1. **First priority:** Use unallocated points (U) - maximize value from free allocations
  2. **Second priority:** Use respec points (R) only if additional improvement possible
  3. **Optimization goal:** Maximize performance improvement while minimizing respec cost

- System SHALL calculate and display cost breakdown in results:
  ```
  Budget Usage:
  • Unallocated points: Used 12 of 15 available (3 remaining)
  • Respec points: Used 4 of 12 available (8 remaining)

  Changes:
  • 12 new nodes allocated (FREE)
  • 4 nodes deallocated and replaced (costs 4 respec points)
  • Total nodes changed: 16
  ```

- System SHALL handle edge cases:
  - If U=0 and R=0: Display "No budget available - cannot optimize. Gain levels or earn respec points first."
  - If optimization finds no improvements within budget: Display "No improvements found within budget. Consider increasing respec point budget."
  - If user has unallocated points but suboptimal existing allocation: Suggest "You have 15 free points to allocate. Consider using some respec points to improve your existing tree too."

- **Acceptance Criteria:**
  - Optimization never exceeds unallocated points budget (U)
  - Optimization never exceeds respec points budget (R)
  - Free allocations always used before costly respecs
  - Results clearly distinguish free vs costly changes
  - Cost breakdown matches actual node changes (verified via testing)

**FR-4.4: Real-Time Progress Reporting**
- System SHALL display progress updates during optimization:
  - **Update frequency:** Every 2 seconds OR every 100 iterations of the optimization loop (whichever comes first)
  - **Note:** Loop iteration includes calculation + tree manipulation + comparison logic (not raw PoB calculation speed)
  - **Technical mechanism:** Server-Sent Events (SSE) for streaming updates OR polling every 2 seconds as fallback
  - **Progress information includes:**
    * Percentage complete (0-100%, monotonically increasing only)
    * Current best improvement found (e.g., "+8.2% DPS so far")
    * Iterations evaluated (e.g., "247 configurations tested")
    * Status message (e.g., "Exploring damage improvements...")
- Sample progress messages:
  - "Analyzing current tree... (DPS: 1,250,400)"
  - "Testing damage improvements... (42 configurations evaluated)"
  - "Optimizing pathing efficiency... (found 8% improvement)"
  - "Finalizing results..."
- System SHALL show estimated time remaining only after 30% completion (prevent wildly inaccurate early estimates)
- System SHALL use rolling average of last 100 iterations for time estimation accuracy
- System SHALL ensure progress percentage is monotonically increasing (never decreases, causes user anxiety)
- System SHALL implement hard timeout: 5 minutes for simple builds, 10 minutes maximum for complex builds
- If updates lag >10 seconds:
  - Display: "Still optimizing... (server processing intensive section)"
  - Keep spinner/animation active to prevent "frozen" perception
- **Acceptance Criteria:** User never waits >10 seconds without visual feedback; progress percentage never decreases; users can identify if system is stuck vs. working; time estimates within 2x actual completion time (not 10x off); SSE or polling mechanism works across all modern browsers

**FR-4.5: Optimization Quality Confidence Score** ⭐ NEW
- System SHALL recalculate final optimized tree independently (fresh calculation) to verify claimed improvement
- System SHALL compare verification result to optimization result with tiered confidence levels:
  - **High confidence (verified):** Verification matches within 0.1% (same tolerance as FR-3.2 PoB GUI parity)
  - **Medium confidence:** Verification differs by 0.1% < diff < 0.5% (display "Medium confidence—small variance detected")
  - **Low confidence:** Verification differs by diff ≥ 0.5% (display "Low confidence—verify in PoB" + log error for investigation)
- System SHALL flag suspicious results: improvements >50% trigger warning "Unusually large improvement—please verify in PoB before investing respec points"
- System SHALL document known limitations: "Result is local optimum—global optimum may exist but wasn't found"
- **Acceptance Criteria:** 99%+ accuracy in claimed improvements; users trust results; suspicious cases clearly flagged; confidence levels consistent with FR-3.2 tolerance standards

**FR-4.6: Optimization Cancellation** ⭐ NEW
- System SHALL allow users to cancel in-progress optimization:
  - UI SHALL display prominent "Cancel Optimization" button during entire optimization process
  - Button SHALL remain clickable and responsive throughout optimization (not disabled or grayed out)
  - Clicking "Cancel" SHALL terminate optimization immediately (within 2 seconds maximum)
  - System SHALL clean up resources with two-phase approach:
    * **Primary cleanup (immediate, within 2 seconds):** Free LuaRuntime, deallocate session memory, terminate calculation threads
    * **Secondary cleanup (background, within 5 minutes):** Python garbage collection, log file closure, temp file cleanup (per FR-3.5)
    * **User impact:** None—user can immediately start new optimization after 2-second primary cleanup completes
  - System SHALL display confirmation message: "Optimization cancelled. You can start a new one anytime."
- Cancellation behavior and UX:
  - **Partial results:** NOT saved or shown to user (clean slate, prevents confusion)
  - **Session cleanup:** Resources fully released (no memory leaks from cancelled sessions)
  - **User state preservation:** Original PoB code remains in input field (user doesn't lose their work)
  - **Immediate retry:** User can immediately start new optimization after cancelling (no cooldown period)
  - **Analytics:** Cancellations tracked to identify UX issues (e.g., if 50% of users cancel, optimization too slow)
- **Acceptance Criteria:** Cancel button visible and functional during entire optimization; cancellation completes within 2 seconds; no memory leaks from cancelled sessions (verified via load testing 100 cancel operations); user can immediately start new optimization after cancelling; original input preserved after cancel

#### FR Group 5: Results Presentation & Export

**FR-5.1: Before/After Comparison**
- System SHALL display side-by-side comparison showing:
  - Original build stats (DPS, EHP, resistances, life, ES, mana)
  - Optimized build stats (same metrics)
  - Percentage improvements clearly highlighted (e.g., "DPS: +12.8%")
  - Cost breakdown ("Requires despeccing 8 points, reallocating 12 points, cost: 8 respec points")
- **Acceptance Criteria:** Results are immediately understandable; improvements are obvious at a glance

**FR-5.2: Optimized PoB Code Generation**
- System SHALL generate new PoB code with optimized passive tree (modify XML, compress with zlib level 9, encode to Base64)
- System SHALL deep copy original XML and modify ONLY the <Tree> section to prevent data corruption
- System SHALL preserve all non-tree build aspects unchanged (items, skills, configuration remain identical)
- System SHALL use exact same compression settings as official PoB for compatibility
- System SHALL provide "Copy to Clipboard" button for one-click PoB code copy
- **Acceptance Criteria:** Generated code imports successfully into official PoB; only passive tree changes visible; 0% data corruption in items/skills/config

**FR-5.3: Change Visualization**
- System SHALL list specific node changes:
  - "Nodes to deallocate: [Node A, Node B, Node C]"
  - "Nodes to allocate: [Node X, Node Y, Node Z]"
- System SHALL load human-readable node names from PoB data files (not internal IDs)
- System SHALL calculate net stat changes by comparing before/after PoB calculations (not node-by-node math)
- System SHALL highlight net changes (e.g., "+15% increased Physical Damage, +120 Life, -5% increased Attack Speed")
- **Acceptance Criteria:** User understands exactly what changed and why stats improved; node names match PoB display

**FR-5.4: Verification Instructions**
- System SHALL provide clear next-step instructions:
  1. "Copy the optimized PoB code above"
  2. "Open Path of Building"
  3. "Click Import/Export Build"
  4. "Paste the code and click Import"
  5. "Review highlighted node changes in the passive tree"
- **Acceptance Criteria:** First-time users can successfully import and verify results

**FR-5.5: Round-Trip Validation** ⭐ NEW
- System SHALL parse generated PoB code back internally before showing to user (round-trip test)
- System SHALL compare generated code stats to expected optimized stats (difference must be <0.1%)
- System SHALL diff original XML vs modified XML to verify ONLY <Tree> section changed
- System SHALL abort code generation if validation fails and display: "Code generation error—please report this bug [details]"
- System SHALL run automated round-trip tests with known-good builds during development
- **Acceptance Criteria:** 0% corrupted codes delivered to users; all exports are importable into PoB; non-tree data never modified

#### FR Group 6: Local Debugging & Logging

**FR-6.1: File-Based Error Logging (Local Only)**
- System SHALL log errors and warnings to local file: `logs/optimizer.log`
- System SHALL log with timestamps, severity levels (ERROR, WARN, INFO), and stack traces
- System SHALL rotate log files when exceeding 10MB (keep last 5 files)
- System SHALL log key events:
  - Optimization start (timestamp, metric selected, budget constraints)
  - Optimization completion (timestamp, result summary, improvement %)
  - Errors and exceptions (full stack traces for debugging)
  - Performance metrics (calculation time, iterations completed)
- System SHALL NOT log sensitive data: full PoB codes, character names
- System SHALL provide log level configuration in config file (DEBUG, INFO, WARN, ERROR)
- **Acceptance Criteria:** Logs written to file successfully; log rotation works; developer can debug issues from logs; no sensitive data leaked

---

## Development Prerequisites & Implementation Sequencing

### Critical Dependency: Path of Building Repository Integration

⚠️ **BLOCKER WARNING:** This project has an absolute dependency on the Path of Building PoE2 open-source repository. **No development of FR-3.x (calculation engine) or FR-4.x (optimization algorithm) can begin until the PoB repository is properly integrated into the project.**

#### Repository Setup Requirements (MUST BE COMPLETE BEFORE DEVELOPMENT)

**PoB Repository Location:**
```
Project Root: poe2_optimizer_v6/
└── external/
    └── pob-engine/          ← Git submodule pointing to PoB PoE2 repository
        ├── HeadlessWrapper.lua              [CRITICAL - Entry point for headless mode]
        ├── src/
        │   ├── Data/
        │   │   ├── PassiveTree.lua          [CRITICAL - Node graph, connections, stats]
        │   │   ├── Classes.lua              [CRITICAL - Character starting positions]
        │   │   ├── Skills.lua               [Required for calculation accuracy]
        │   │   └── Items.lua                [Required for calculation accuracy]
        │   ├── Modules/
        │   │   ├── CalcPerform.lua          [CRITICAL - Main calculation orchestrator]
        │   │   ├── CalcOffence.lua          [Required - DPS calculations]
        │   │   ├── CalcDefence.lua          [Required - EHP calculations]
        │   │   └── [30+ other modules]      [Required - Complete calculation engine]
        │   └── Classes/
        │       ├── Build.lua                [CRITICAL - Build state management]
        │       ├── Skill.lua                [Required - Skill calculations]
        │       └── Item.lua                 [Required - Item stat parsing]
        └── runtime/                         [LuaJIT dependencies]
```

**Setup Commands:**
```bash
# Step 1: Clone main repository (if not already done)
git clone https://github.com/YOUR_USERNAME/poe2-passive-tree-optimizer.git
cd poe2-passive-tree-optimizer

# Step 2: Add PoB as git submodule
git submodule add https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2 external/pob-engine

# Step 3: Initialize and update submodule
git submodule update --init --recursive

# Step 4: Pin to stable commit (CRITICAL for reproducibility)
cd external/pob-engine
git checkout <STABLE_COMMIT_HASH>  # Document this hash in POB_VERSION.txt
cd ../..

# Step 5: Verify critical files exist
ls external/pob-engine/HeadlessWrapper.lua  # Must exist
ls external/pob-engine/src/Data/PassiveTree.lua  # Must exist
ls external/pob-engine/src/Modules/CalcPerform.lua  # Must exist

# Step 6: Document PoB version
echo "PoB Version: <COMMIT_HASH>" > POB_VERSION.txt
echo "Date: $(date)" >> POB_VERSION.txt
```

**Validation Checklist:**
- [ ] external/pob-engine/ directory exists
- [ ] HeadlessWrapper.lua file exists and is readable
- [ ] src/Data/PassiveTree.lua exists (required for FR-4.2)
- [ ] src/Modules/ folder contains 30+ Lua files
- [ ] src/Classes/ folder exists with Build.lua, Skill.lua, Item.lua
- [ ] PoB repository is visible in AI/IDE workspace for code analysis
- [ ] POB_VERSION.txt documents pinned commit hash
- [ ] Git submodule status shows no errors: `git submodule status`

**AI Development Requirements:**
- AI MUST have read access to external/pob-engine/ directory during architecture and development phases
- AI will need to analyze HeadlessWrapper.lua to identify required stub functions (FR-3.1)
- AI will need to read PassiveTree.lua structure to implement tree validation (FR-4.2)
- AI will need to understand PoB module loading order for proper Lupa integration

---

### Functional Requirement Dependency Matrix

#### Tier 0: Prerequisites (No Code Dependencies)

**External Dependencies (MUST EXIST FIRST):**
- ✅ Path of Building PoE2 repository cloned to `external/pob-engine/`
- ✅ Python 3.10+ installed
- ✅ Git configured with submodule support

**Development Environment:**
- ✅ PoB repository visible to AI workspace
- ✅ Python dependencies installable: `pip install lupa xmltodict flask python-dotenv`

---

#### Tier 1: Foundation Layer (Week 1 - Can Develop in Parallel)

**NO PoB ENGINE REQUIRED - Just UI and Data Parsing**

```
FR-1.1 [PoB Code Input Interface]
  Dependencies: None (just HTML textarea)
  Can start: Immediately

FR-1.2 [PoB Code Parsing]
  Dependencies: xmltodict library
  Blocks: FR-1.3, FR-1.4, FR-1.5, FR-5.2, FR-5.5
  Can start: Immediately (doesn't need PoB calculation engine)

FR-1.3 [Input Validation]
  Dependencies: FR-1.2 (needs parsing to validate)
  Can start: After FR-1.2 complete

FR-1.5 [Version Detection]
  Dependencies: FR-1.2 (needs parsed XML to detect version)
  Requires: Sample PoE1 and PoE2 codes for testing
  Can start: After FR-1.2 complete

FR-2.1 [Goal Selection Dropdown]
  Dependencies: None (just UI)
  Can start: Immediately

FR-2.2 [Respec Budget Input]
  Dependencies: None (just UI)
  Can start: Immediately
```

**Tier 1 Deliverables:**
- User can paste PoB code
- System can parse XML structure
- User can select optimization goal
- User can specify budget constraint
- **NO calculation or optimization yet**

---

#### Tier 2: PoB Integration Layer (Week 2 - REQUIRES external/pob-engine/)

⚠️ **CRITICAL BLOCKER:** Cannot start Tier 2 without PoB repository fully integrated

**AI MUST READ BEFORE DEVELOPMENT:**
- `external/pob-engine/HeadlessWrapper.lua` - Identify required stubs
- `external/pob-engine/src/Modules/CalcPerform.lua` - Understand calculation flow

```
FR-3.1 [Lupa + HeadlessWrapper Integration] ⭐ FOUNDATION
  Dependencies: external/pob-engine/HeadlessWrapper.lua EXISTS
  Dependencies: Lupa library installed
  Blocks: FR-3.2, FR-3.3, FR-3.4, ALL FR-4.x, ALL FR-5.x
  Development Steps:
    1. AI reads HeadlessWrapper.lua source
    2. Identify required stub functions (Deflate, Inflate, ConPrintf, etc.)
    3. Implement stub_functions.py with Python equivalents
    4. Load HeadlessWrapper via Lupa LuaRuntime
    5. Validate initialization (no errors)
  Outputs: PoBCalculationEngine class
  Can start: After Tier 1 OR in parallel (independent)

FR-3.2 [Build State Calculation]
  Dependencies: FR-3.1 (needs calculation engine), FR-1.2 (needs parsed build)
  Dependencies: external/pob-engine/src/Classes/*.lua
  Blocks: FR-1.4, FR-3.3, FR-4.1
  Outputs: calculate_stats(build) → {dps, ehp, resistances, life, es, mana}
  Can start: After FR-3.1 complete

FR-3.3 [Batch Calculation Performance]
  Dependencies: FR-3.2 (needs single calculation working first)
  Optimization: Pre-compile Lua functions, reuse LuaRuntime
  Can start: After FR-3.2 complete

FR-3.4 [Calculation Timeout & Error Recovery]
  Dependencies: FR-3.2 (wraps calculation with timeout)
  Can start: After FR-3.2 complete (can develop in parallel with FR-3.3)

FR-1.4 [Build Summary Display]
  Dependencies: FR-3.2 (needs calculated stats to display)
  Can start: After FR-3.2 complete
```

**Tier 2 Deliverables:**
- PoB calculation engine integrated via Lupa
- Can calculate DPS, EHP for any build
- Batch processing optimized (<1s for 1000 calcs)
- **Ready for optimization algorithm**

**Tier 2 Gate:**
✋ **DO NOT PROCEED to Tier 3 until:**
- Single build calculation works (FR-3.2 complete)
- Results match official PoB GUI within 0.1% (accuracy validated)
- Batch performance target met (FR-3.3 complete)

---

#### Tier 3: Optimization Algorithm Layer (Week 3-4 - REQUIRES PoB Data Files)

⚠️ **CRITICAL BLOCKER:** Cannot start Tier 3 without `external/pob-engine/src/Data/PassiveTree.lua`

**AI MUST READ BEFORE DEVELOPMENT:**
- `external/pob-engine/src/Data/PassiveTree.lua` - Node graph structure
- `external/pob-engine/src/Data/Classes.lua` - Character starting positions

```
FR-4.2 [Tree Connectivity Validation] ⭐ MUST DEVELOP FIRST
  Dependencies: external/pob-engine/src/Data/PassiveTree.lua EXISTS
  Blocks: FR-4.1, FR-4.3 (cannot optimize without valid trees)
  Development Steps:
    1. AI reads PassiveTree.lua to understand structure
    2. Parse node graph (IDs, connections/edges, positions)
    3. Load character class starting node IDs from Classes.lua
    4. Build adjacency list/graph representation in Python
    5. Implement pathfinding: isConnected(startNode, allocatedNodes)
    6. Validate: all allocated nodes form connected path to start
  Outputs: TreeValidator class with isValidTree() method
  Can start: After Tier 2 complete + Data files available

FR-4.1 [Hill Climbing Algorithm] ⭐ CORE OPTIMIZATION
  Dependencies: FR-4.2 (tree validator), FR-3.2 (calculator), FR-2.1 (goal), FR-2.2 (budget)
  Blocks: FR-4.3, FR-4.4, FR-4.5, ALL FR-5.x
  Algorithm Flow:
    1. Load current tree from parsed build
    2. Calculate baseline stats (FR-3.2)
    3. Loop:
       a. Generate neighbor (deallocate 1 node, try allocating nearby node)
       b. Validate connectivity (FR-4.2)
       c. Calculate new stats (FR-3.2)
       d. If improvement AND within budget (FR-2.2): keep change
       e. Else: revert
    4. Converge when no improvements found
  Can start: After FR-4.2 complete

FR-4.3 [Respec Budget Enforcement]
  Dependencies: FR-4.1 (integrated into optimization loop), FR-2.2 (budget input)
  Can start: During FR-4.1 development (part of loop logic)

FR-4.4 [Real-Time Progress Reporting]
  Dependencies: FR-4.1 (reports on optimization progress)
  Can start: After FR-4.1 basic loop working (polish feature)

FR-4.5 [Optimization Quality Confidence Score]
  Dependencies: FR-4.1 (verify optimization results), FR-3.2 (recalculate)
  Can start: After FR-4.1 complete (validation layer)
```

**Tier 3 Deliverables:**
- Optimization algorithm produces improved trees
- Trees respect connectivity rules (always valid)
- Budget constraints enforced
- Real-time progress updates
- Confidence scoring for trust

**Tier 3 Gate:**
✋ **DO NOT PROCEED to Tier 4 until:**
- Optimization produces 5-15% median improvement (validated with test builds)
- All optimized trees import successfully into official PoB (0% invalid trees)
- Budget constraints never violated (test with various budgets)

---

#### Tier 4: Results & Export Layer (Week 5 - Uses PoB Data for Display)

**Uses PoB Data Files for Human-Readable Output**

```
FR-5.1 [Before/After Comparison Display]
  Dependencies: FR-4.1 (optimization results)
  Can start: After FR-4.1 produces results

FR-5.3 [Change Visualization]
  Dependencies: FR-4.1 (node changes), external/pob-engine/src/Data/PassiveTree.lua (node names)
  Data needed: Load node display names (not just IDs) from PassiveTree.lua
  Can start: After FR-4.1 complete

FR-5.2 [Optimized PoB Code Generation]
  Dependencies: FR-4.1 (optimized tree), FR-1.2 (knows XML structure)
  Reverse process: Python build → XML → zlib compress → Base64 encode
  Can start: After FR-4.1 complete

FR-5.5 [Round-Trip Validation]
  Dependencies: FR-5.2 (generated code), FR-1.2 (parser), FR-3.2 (recalculate)
  Validation: Parse generated code → calculate stats → compare to expected
  Can start: After FR-5.2 complete

FR-5.4 [Verification Instructions]
  Dependencies: FR-5.2 (have code to verify)
  Can start: After FR-5.2 complete (documentation/UI)
```

**Tier 4 Deliverables:**
- User sees clear before/after comparison
- Optimized PoB code generated and validated
- Human-readable change descriptions
- Verification instructions provided
- **MVP functionality complete**

---

#### Tier 5: Analytics & Polish (Week 6 - Optional/Parallel)

```
FR-6.1 [Usage Analytics Tracking]
  Dependencies: All prior tiers (tracks entire user flow)
  Can start: In parallel throughout development (add tracking incrementally)

FR-6.2 [Optional User Feedback]
  Dependencies: FR-5.x (post-results survey)
  Can start: After results display working
```

---

### Development Phase Gates & Blockers

```
WEEK 0: Repository Setup
┌─────────────────────────────────────────────────────┐
│ ✅ Clone PoB repository to external/pob-engine/    │
│ ✅ Verify HeadlessWrapper.lua exists               │
│ ✅ Verify src/Data/PassiveTree.lua exists          │
│ ✅ Pin to stable commit, document version          │
│ ✅ Make visible to AI workspace                    │
└─────────────────────────────────────────────────────┘
         │
         ▼
    🚪 GATE 0: PoB Repository Available
         │
         ├─────────────────┬──────────────────┐
         ▼                 ▼                  ▼
    WEEK 1           WEEK 1 (parallel)   WEEK 2 (BLOCKED until Gate 0)
    Tier 1           Tier 1              Tier 2
    FR-1.1,1.2,1.3   FR-2.1,2.2          ⏸️ WAITING
    FR-1.5
         │                 │                  │
         └────────┬────────┘                  │
                  ▼                           ▼
             🚪 GATE 1: Input Layer Complete + PoB Available
                                              │
                                         WEEK 2: Tier 2
                                         FR-3.1 → FR-3.2 → FR-3.3
                                              │
                                              ▼
                                    🚪 GATE 2: Calculation Engine Working
                                    (Results match PoB GUI ±0.1%)
                                              │
                                         WEEK 3-4: Tier 3
                                         FR-4.2 → FR-4.1 → FR-4.3,4.4,4.5
                                              │
                                              ▼
                                    🚪 GATE 3: Optimization Produces Valid Results
                                    (5-15% improvement, 0% invalid trees)
                                              │
                                         WEEK 5: Tier 4
                                         FR-5.1,5.2,5.3,5.4,5.5
                                              │
                                              ▼
                                    🚪 GATE 4: MVP Complete
                                    (End-to-end workflow functional)
```

**Critical Blockers:**
1. **Gate 0 Blocker:** No PoB repository = Cannot start Tier 2, 3, 4
2. **Gate 2 Blocker:** Calculation engine inaccurate = Optimization produces garbage results
3. **Gate 3 Blocker:** Invalid trees generated = Users get corrupted builds

---

### AI Development Notes: PoB File Reading Requirements

**When AI Begins Architecture Phase:**
- [ ] Read `external/pob-engine/HeadlessWrapper.lua` in full
- [ ] Identify all function calls made by HeadlessWrapper (these need stubs)
- [ ] Document module loading order (dependencies between Lua files)

**When AI Begins FR-3.1 (PoB Integration):**
- [ ] Read `external/pob-engine/src/Modules/CalcPerform.lua` to understand calculation orchestration
- [ ] Read examples in `external/pob-engine/` folder (if examples exist)
- [ ] Verify LuaJIT compatibility of PoB code

**When AI Begins FR-4.2 (Tree Validation):**
- [ ] Read `external/pob-engine/src/Data/PassiveTree.lua` structure
- [ ] Parse node graph: IDs, connections (out/in edges), stats, positions
- [ ] Read `external/pob-engine/src/Data/Classes.lua` for starting node IDs per class
- [ ] Build Python representation of tree graph for pathfinding

**When AI Begins FR-5.3 (Node Display Names):**
- [ ] Re-read `external/pob-engine/src/Data/PassiveTree.lua`
- [ ] Extract node display names (human-readable) vs node IDs (internal)
- [ ] Build ID→Name mapping dictionary

---

### Non-Functional Requirements

#### NFR-1: Performance

**Response Time:**
- **Page Load:** Initial page load SHALL complete in <2 seconds on standard broadband (10 Mbps download)
- **PoB Code Parsing:** SHALL complete in <500ms for codes up to 100KB
- **Optimization Duration:**
  - Simple builds (level 40-60, <80 passive points): Target <2 minutes
  - Standard builds (level 70-85, 80-110 passive points): Target <5 minutes
  - Complex builds (level 90-100, 110-120 passive points): Maximum 10 minutes
- **Results Display:** SHALL render results page in <1 second after optimization completes
- **Interactive Elements:** All UI interactions (button clicks, dropdowns) SHALL respond in <100ms

**Throughput:**
- System SHALL handle 10 concurrent optimizations on 2-core, 4GB RAM VPS (per FR-3.3)
- System SHALL maintain <1s calculation performance (1000 calcs) under normal load (1-5 concurrent users)

**Scalability:**
- Architecture SHALL support horizontal scaling (add more server instances to handle 100+ concurrent users)
- Session state SHALL be portable (can move sessions between server instances for load balancing in future)

**Acceptance Criteria:**
- 95th percentile optimization completes within target times
- Page load times measured via WebPageTest <2s on Cable connection
- Load testing validates 10 concurrent users achieve target performance

---

#### NFR-2: Reliability

**Availability:**
- System SHALL target 95% uptime during MVP validation phase (acceptable for free tool)
- Planned maintenance SHALL be announced 24 hours in advance via status page

**Fault Tolerance:**
- System SHALL gracefully handle PoB calculation engine failures (display error, log for debugging, don't crash)
- System SHALL recover from individual session crashes without affecting other concurrent users (per FR-3.5 isolation)
- System SHALL implement circuit breaker pattern: if PoB integration fails 5 times in 1 minute, pause new optimizations for 5 minutes and display "System maintenance" message

**Data Integrity:**
- System SHALL never modify user's original PoB code (read-only input)
- System SHALL validate all generated PoB codes via round-trip testing before delivery (per FR-5.5)
- System SHALL never corrupt non-tree build data (items, skills, configuration) (per FR-5.2)

**Error Recovery:**
- System SHALL log all errors with sufficient context for debugging (session ID, PoB code length, character class, error stack trace)
- System SHALL provide "Report Bug" link on error pages with pre-filled error details

**Acceptance Criteria:**
- Uptime measured via UptimeRobot or similar monitoring (95%+ over 30-day period)
- Load testing: 100 concurrent session crashes don't affect 101st user
- Round-trip validation catches 100% of corrupted codes before delivery

---

#### NFR-3: Security (Local Deployment)

**Input Validation:**
- System SHALL sanitize all user inputs to prevent code injection (escape HTML in error messages, results display)
- System SHALL validate PoB code size limits before processing (reject >100KB per FR-1.1)
- System SHALL validate PoB code format before passing to Lua engine (prevent malicious Lua injection)

**Dependency Security:**
- System SHALL use dependency scanning (pip-audit, safety) to identify vulnerable Python packages
- System SHALL update dependencies monthly or immediately if critical CVE discovered
- System SHALL pin dependency versions in requirements.txt for reproducibility

**Data Privacy (Local-Only):**
- System SHALL NOT store user PoB codes permanently (process in memory, discard after session ends)
- System SHALL NOT log sensitive data in logs/optimizer.log: no full PoB codes, no character names (per FR-6.1)
- System SHALL store nothing on disk except temporary session data (cleared on server restart)

**Local Execution Safety:**
- System SHALL run Flask in development mode with debug=False (prevent arbitrary code execution)
- System SHALL bind to localhost only (127.0.0.1:5000) - no external network access
- System SHALL set Lua execution timeout to prevent infinite loops in PoB calculations

**Acceptance Criteria:**
- pip-audit passes with 0 high-severity vulnerabilities
- Flask bound to localhost only (verify with netstat)
- Log files contain no full PoB codes or sensitive data
- Lua execution timeout prevents infinite loops

---

#### NFR-4: Usability

**Learnability:**
- First-time users SHALL be able to complete full workflow (paste code → optimize → get results) without documentation
- System SHALL provide inline help text for all inputs (placeholders, helper text, tooltips)
- Error messages SHALL include actionable recovery steps (per FR-1.3 structured format)

**Efficiency:**
- Experienced users SHALL complete optimization workflow in <30 seconds of active time (excluding optimization processing)
- System SHALL remember last used optimization goal (stored in browser localStorage)
- System SHALL provide keyboard shortcuts for common actions (Enter to submit, Escape to cancel)

**User Satisfaction:**
- System SHALL target Net Promoter Score (NPS) ≥40 within first 3 months (per Goal 2)
- System SHALL minimize user frustration: clear progress indicators (per FR-4.4), cancellation option (per FR-4.6), honest error messages

**Accessibility:**
- System SHALL meet WCAG 2.1 AA compliance (per FR-1.7)
- System SHALL support keyboard-only navigation
- System SHALL work with screen readers (NVDA, JAWS)

**Acceptance Criteria:**
- User testing: 8/10 first-time users complete workflow without assistance
- NPS survey results: ≥40 score within 3 months
- WCAG automated scan (axe, WAVE) passes AA level
- Task completion time measured: 95% of users submit optimization in <30s

---

#### NFR-5: Maintainability

**Code Quality:**
- System SHALL maintain >80% test coverage for critical paths (PoB integration, optimization algorithm, code generation)
- System SHALL use type hints in Python (mypy static type checking)
- System SHALL follow PEP 8 style guidelines (enforced via black formatter)
- System SHALL document all public functions with docstrings

**Modularity:**
- System SHALL separate concerns: PoB integration module, optimization algorithm module, web API module, frontend (loosely coupled)
- System SHALL use dependency injection for testability (mock PoB engine during tests)

**Documentation:**
- System SHALL maintain README with setup instructions (per REPOSITORY-SETUP-GUIDE.md)
- System SHALL document API endpoints (if exposing programmatic access)
- System SHALL maintain ADRs (Architecture Decision Records) for major technical decisions

**Monitoring & Observability:**
- System SHALL log key metrics: optimization completion rate, average improvement, processing time (per FR-6.1)
- System SHALL implement structured logging (JSON format) for easy parsing
- System SHALL expose health check endpoint: /health returns 200 if system operational

**Acceptance Criteria:**
- pytest coverage report shows ≥80% for src/calculator/ and src/parsers/
- mypy static type checking passes with 0 errors
- All modules have clear single responsibility (SRP compliance)
- Health endpoint monitored via UptimeRobot (downtime alerts)

---

#### NFR-6: Portability (Local MVP - Single Platform Focus)

**Platform Requirements (MVP):**
- System SHALL run on developer's local machine (Python 3.10+ environment)
- System SHALL use cross-platform Python libraries where possible (prefer portability without requiring it)
- System SHALL document any platform-specific setup requirements in README.md

**Browser Compatibility:**
- Frontend SHALL support modern browsers: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- Primary testing on developer's default browser (sufficient for local MVP)

**Future Portability (Post-MVP):**
- Cross-platform testing deferred to V2 (when preparing for public release)
- Multi-platform CI/CD deferred to V2 (GitHub Actions testing on Linux/macOS/Windows)
- Cloud deployment portability deferred to V2 (VPS, serverless platforms)

**Acceptance Criteria (MVP):**
- System runs successfully on developer's local machine
- Setup documented in README.md with any OS-specific notes
- Browser compatibility verified in at least one modern browser (Chrome or Firefox)

---

#### NFR-7: Compatibility

**PoB Version Compatibility:**
- System SHALL pin to specific PoB PoE2 commit hash (documented in POB_VERSION.txt)
- System SHALL test against PoB updates monthly
- System SHALL provide migration path if PoB API changes (communicate deprecation 2 weeks before breaking change)

**Data Format Compatibility:**
- System SHALL support PoB XML format as of December 2025 (current standard)
- System SHALL handle minor XML schema variations gracefully (missing optional fields don't break parsing)

**API Stability (if exposed):**
- System SHALL version API endpoints (/v1/optimize) if programmatic access added in future
- System SHALL maintain backwards compatibility for at least 6 months when deprecating API versions

**Acceptance Criteria:**
- System works with PoB repository commit hash ABC123 (documented)
- Parsing handles builds from PoE 2 Early Access through League 1
- API versioning strategy documented (even if not implemented in MVP)

---

#### NFR-8: Compliance & Legal

**Open Source Licensing:**
- System SHALL use MIT License (permissive, community-friendly)
- System SHALL respect PoB's MIT License (attribute properly, include license text)
- System SHALL audit all dependencies for license compatibility (no GPL violations)

**Privacy Principles (Local-Only):**
- System SHALL practice data minimization: only process data needed for optimization
- System SHALL NOT store user PoB codes permanently (local session only)
- System SHALL NOT share data with third parties (no analytics, no cloud services)

**Disclaimers:**
- README SHALL include disclaimer:
  - Tool is provided "as-is" with no warranties
  - Not affiliated with Grinding Gear Games (PoE developer)
  - User responsible for in-game consequences of using optimized builds
  - No guarantee of optimization quality (disclaimer on "local optimum" limitation)

**Content Ownership:**
- README SHALL clarify: User retains ownership of their build codes
- System SHALL NOT use build codes for purposes beyond optimization (local processing only)

**Acceptance Criteria:**
- LICENSE file included in repository (MIT)
- README.md includes clear disclaimers
- No user data leaves local machine (verified by network monitoring)
- Legal review confirms compliance with open-source licensing (automated tools: licensee, FOSSA)

---

#### NFR-9: Operational Requirements (Local Deployment)

**Local Startup:**
- System SHALL support single-command startup: `python main.py` or `flask run`
- System SHALL initialize in <5 seconds (load PoB modules, start Flask server)
- System SHALL display clear startup message: "Optimizer running at http://localhost:5000"
- System SHALL document setup steps in README.md (install dependencies, run server)

**Error Logging & Debugging:**
- System SHALL log errors to local file system: `logs/optimizer.log` (per FR-6.1)
- System SHALL log key metrics: optimization completion rate, average improvement, processing time
- System SHALL provide detailed error messages in logs (stack traces for debugging)
- System SHALL rotate log files automatically (prevent disk space issues)

**Development Workflow:**
- System SHALL use Git for version control (all code committed to repository)
- System SHALL pin dependency versions in requirements.txt (reproducible environment)
- System SHALL document environment setup in README.md (Python version, required packages)

**Cost Management:**
- System SHALL operate with $0 hosting costs (local-only, no cloud infrastructure)
- System SHALL use only open-source dependencies (no paid services required)

**Acceptance Criteria:**
- Fresh clone + setup completes in <10 minutes following README
- Server starts successfully on localhost:5000
- Logs written to logs/optimizer.log successfully
- All dependencies documented in requirements.txt
- Zero runtime costs verified

---

## User Journeys

### Journey 1: Experienced Min-Maxer Optimizing Endgame Build

**Persona:** Marcus, Level 92 Mercenary, 200+ hours in PoE 2, understands build mechanics
**Goal:** Squeeze out 8-10% more DPS from passive tree to tackle Tier 16+ content
**Context:** Has 12 respec points available, wants cost-effective improvements

**Journey Flow:**

1. **Discovery** (External to Tool)
   - Marcus reads build guide on Reddit mentioning "passive tree optimizer"
   - Clicks link from comment, arrives at landing page
   - **Decision Point:** Does the tool look trustworthy? → Sees simple UI, open-source link, clear value prop → Continues

2. **Preparation** (Path of Building)
   - Opens Path of Building with current level 92 build
   - Reviews current stats: 1,450,000 DPS, 42,000 EHP
   - Clicks "Import/Export Build" → "Generate" → Copies PoB code to clipboard
   - **Pain Point Avoided:** No account creation, no file upload, just paste code

3. **Input & Configuration** (Our Tool)
   - Pastes PoB code into large text area (build is ~85KB, loads instantly)
   - **Validation Feedback:** Green checkmark + "Build loaded: Level 92 Mercenary, 1.45M DPS"
   - **Auto-detection:** System shows "Detected: 0 unallocated points (level 92, 115/115 allocated)"
   - Reviews optimization goal dropdown: "Maximize Total DPS" (default) ✓
   - **Decision Point:** Should I set budget? → Sees two fields: "Unallocated points" and "Respec points"
   - Unallocated field shows "0" (auto-detected correctly - he's maxed out at level 92)
   - Respec field blank → Has 12 respec points, doesn't want to waste them
   - Clicks [Budget (15)] quick-select button → changes to 12 manually
   - **Helper Text:** "Currency to deallocate already-spent points"
   - Clicks "Optimize My Tree" button

4. **Processing & Waiting** (Optimization in Progress)
   - Progress bar appears: "Analyzing current tree... (DPS: 1,450,000)"
   - After 15 seconds: "Testing damage improvements... (127 configurations evaluated)"
   - After 45 seconds: "Optimizing pathing efficiency... (found +6.8% improvement)"
   - **Emotional State:** Confident system is working, sees incremental progress
   - **Decision Point:** Is this taking too long? → Sees progress increasing, estimate shows "~1 minute remaining" → Waits
   - After 1 minute 23 seconds: "Finalizing results..."

5. **Results Review** (Success)
   - Results page displays side-by-side comparison:
     ```
     Your Original Build:           Optimized Tree Results:
     Total DPS: 1,450,000           Total DPS: 1,569,400 (+8.2%) ✓
     Effective HP: 42,000           Effective HP: 42,300 (+0.7%)

     Budget Usage:
     • Unallocated points: Used 0 of 0 available (none to use)
     • Respec points: Used 6 of 12 available (6 remaining) ✓

     Changes:
     • 0 new nodes allocated (no free points available)
     • 6 nodes deallocated and replaced (costs 6 respec points)
     • Total nodes changed: 6

     Confidence: High (verified) ✓
     ```
   - **Emotional Response:** Excited! 8.2% DPS gain for only 6 respec points
   - Scrolls down to see specific changes:
     - "Nodes to deallocate: Berserking, Bloodletting, Quick Recovery, ..."
     - "Nodes to allocate: Overwhelming Force, Weapon Mastery, Titanic Impacts, ..."
   - **Decision Point:** Should I trust this? → Sees "High confidence (verified)" + specific node changes → Trusts

6. **Export & Verification** (Path of Building)
   - Clicks "Copy to Clipboard" button for optimized PoB code
   - Opens Path of Building → "Import/Export Build" → "Import from Clipboard"
   - **Critical Moment:** PoB loads successfully, shows 1.57M DPS (matches tool's claim)
   - Sees highlighted passive tree changes (red = removed, green = added)
   - Manually verifies a few nodes match the tool's list → Correct!

7. **Implementation** (In-Game)
   - Logs into PoE 2, goes to passive tree
   - Uses 6 respec points to deallocate old nodes
   - Allocates new nodes as shown in PoB
   - Checks character sheet: DPS increased from 1.45M → 1.57M ✓

8. **Advocacy** (Post-Use)
   - Returns to Reddit thread, comments: "Just used this, gained 8% DPS for 6 respec points. Legit."
   - Bookmarks tool for future league starts
   - **NPS:** Would recommend = 9/10 (Promoter)

**Success Metrics:**
- ✅ Optimization completed in <2 minutes
- ✅ Delivered 8.2% improvement (within 5-15% target)
- ✅ Budget constraint honored (6 ≤ 12 respec points)
- ✅ User verified results and implemented successfully
- ✅ Became advocate (NPS promoter)

---

### Journey 2: Casual Player's First-Time Experience (With Error Recovery)

**Persona:** Sarah, Level 58 Sorceress, 30 hours in PoE 2, heard about "build optimization"
**Goal:** "My damage feels low, maybe my tree is bad?"
**Context:** First time using any build tool besides PoB, not sure what to expect

**Journey Flow:**

1. **Discovery** (YouTube)
   - Watches PoE 2 build guide video, creator mentions "passive tree optimizer"
   - Clicks description link → Arrives at tool landing page
   - **Decision Point:** Is this safe? Will it steal my account? → Sees "No login required, paste your PoB code" → Relieved

2. **Learning Path of Building** (First-Time Setup)
   - Downloads Path of Building (tool link provides PoB download)
   - Opens PoB, confused by interface
   - **Decision Point:** How do I import my character? → Googles "Path of Building import character" → Finds guide
   - Imports character from PoE 2 account → Build loads
   - Clicks "Import/Export Build" → "Generate" → Copies code (partial copy due to mouse slip)

3. **First Attempt - Error** (Validation Failure)
   - Pastes truncated PoB code (only copied 60% of it)
   - Clicks "Optimize My Tree"
   - **Error Message Appears:**
     ```
     ❌ Unable to Load Build

     The build code appears to be corrupted or incomplete.

     This usually happens when:
     • Code was only partially copied from Path of Building
     • Code contains invalid characters

     Please try:
     1. Open Path of Building
     2. Click "Import/Export Build"
     3. Ensure entire code is selected and copied
     4. Paste here and try again

     [Show Technical Details ▼]
     ```
   - **Emotional State:** Frustrated, but error message is helpful
   - **Decision Point:** Give up or try again? → Error message was clear about what to do → Tries again

4. **Second Attempt - Success** (Corrected Input)
   - Returns to PoB, carefully selects ALL of code, copies
   - Pastes full code (95KB) into tool
   - **Validation Feedback:** "Build loaded: Level 58 Sorceress, 385,000 DPS" ✓
   - **Auto-detection:** System shows "Detected: 11 unallocated points (level 58, 69/80 allocated)"
   - **Surprise:** "Oh! I have 11 points I haven't spent yet"
   - Selects "Maximize Total DPS" (doesn't understand the other options)
   - **Decision Point:** Should I set respec budget? → Sees two fields:
     * "Unallocated points: 11" (already filled in - looks right!)
     * "Respec points: [blank]" → Doesn't know how many she has → Leaves blank
   - Clicks "Optimize My Tree"

5. **Processing** (Shorter Duration for Lower-Level Build)
   - Progress shows: "Analyzing current tree... (DPS: 385,000)"
   - After 35 seconds: "Optimizing pathing efficiency... (found +11.2% improvement)"
   - Completes in 58 seconds
   - **Emotional State:** Hopeful but uncertain what results mean

6. **Results Understanding** (Learning Moment)
   - Sees comparison:
     ```
     Your Original Build:           Optimized Tree Results:
     Total DPS: 385,000             Total DPS: 459,200 (+19.3%) ✓
     Effective HP: 18,200           Effective HP: 19,100 (+4.9%)

     Budget Usage:
     • Unallocated points: Used 11 of 11 available (all used) ✓
     • Respec points: Used 8 of unlimited available

     Changes:
     • 11 new nodes allocated (FREE - used your unspent points!)
     • 8 nodes deallocated and replaced (costs 8 respec points)
     • Total nodes changed: 19
     ```
   - **Understanding:** "Oh! It used my 11 free points PLUS suggested 8 respecs"
   - **Concern:** "Wait, I only have 3 respec points, not 8..."
   - **Decision Point:** Is this still useful? → Realizes she can:
     * Implement the 11 FREE allocations now (no cost!)
     * Save the respec suggestions for later when she earns 5 more respec points
   - **Learning:** "Next time I'll enter my actual respec budget so it doesn't suggest changes I can't afford right now."

7. **Partial Implementation** (Immediate + Deferred)
   - Copies optimized PoB code
   - Opens PoB → Imports → Verifies it loads correctly
   - Saves optimized build as "OPTIMIZED - Full version for later"
   - **Immediate action:** Goes in-game and allocates the 11 FREE nodes (no cost!)
   - Checks character sheet: DPS went from 385K → 428K (+11%) just from free allocations!
   - **Deferred action:** Saves the 8 respec suggestions for when she earns 5 more respec points
   - **Emotional state:** Happy she got immediate value (11% boost) without spending currency

8. **Return Visit** (2 Weeks Later)
   - Reaches level 68, earned 9 more respec points (total: 12)
   - Returns to tool, pastes updated build (now has all 11 free allocations from last time)
   - **This Time:** Sets respec budget correctly:
     * Unallocated points: Shows "10" (auto-detected from leveling 58→68)
     * Respec points: Sets to 12 (clicks [Budget (15)] → changes to 12)
   - Optimization completes showing:
     ```
     Budget Usage:
     • Unallocated points: Used 10 of 10 available
     • Respec points: Used 5 of 12 available

     Changes:
     • 10 new nodes allocated (FREE)
     • 5 nodes deallocated and replaced (costs 5 respec points)
     ```
   - Implements full optimization in-game
   - **Outcome:** DPS goes from 510K → 597K (+17%) using 10 free + 5 respec
   - **NPS:** Would recommend = 8/10 (Promoter) - "Now I understand how to use it!"

**Success Metrics:**
- ✅ Error recovery successful (clear guidance)
- ✅ Auto-detection of unallocated points worked perfectly
- ✅ Immediate value from FREE allocations (11% boost without spending currency!)
- ✅ Deferred implementation still valuable (saved full optimization for later)
- ✅ Return visit with proper budget usage → became Promoter
- ✅ Dual-budget system provides tiered implementation path

**UX Improvements Identified:**
- ✅ Auto-detection of unallocated points eliminates user confusion
- ✅ Clear distinction between FREE (unallocated) vs COSTLY (respec) points
- Future: Add in-game currency cost calculator ("8 respec points ≈ 45 minutes farming")

---

### Journey 3: Edge Case - Unsupported Build Type Detection

**Persona:** David, Level 75 Necromancer with minion build
**Goal:** Optimize minion damage passive tree
**Context:** Knows tool exists, not aware of MVP limitations

**Journey Flow:**

1. **Confident Entry** (Direct Navigation)
   - Bookmarked tool from friend's recommendation
   - Opens PoB, copies minion Necromancer build code
   - Pastes into tool (no hesitation, expects it to work)

2. **Unsupported Build Detection** (Immediate Feedback)
   - System detects: Build has active Zombie skill + Minion Damage passive nodes
   - **Error Message Appears** (before optimization starts):
     ```
     ❌ Build Type Not Supported (Yet!)

     Your build uses MINIONS which isn't supported in the MVP.

     ✅ What IS supported:
     • Direct damage builds (attacks, spells, DoT)
     • Self-cast and melee builds
     • Most defensive builds

     ⏳ Coming in V2:
     • Minion builds
     • Totems, traps, mines
     • Trigger-based builds

     Why the limitation?
     These build types require specialized calculation logic.
     We're focusing on getting core optimization perfect first.

     [Learn more about our roadmap]
     ```
   - **Emotional Response:** Disappointed but appreciates honesty

3. **Decision Points**
   - **Option A:** Click "Learn more" → Sees roadmap showing minions targeted for V2 in 3 months
   - **Option B:** Leave feedback → Optional survey: "What build type would you like us to support next?"
   - **Option C:** Bookmark for later → "Remind me when minion builds supported"

4. **Outcome** (Positive Despite Limitation)
   - David selects "Notify me when minion support added" (email signup)
   - Shares tool with guild: "Works for attack/spell builds, they're adding minions soon"
   - **NPS:** Would recommend = 6/10 (Passive, but would be Promoter if minions supported)

**Success Metrics:**
- ✅ Clear limitation communication (95%+ detection rate)
- ✅ No false expectation (user knows why it doesn't work)
- ✅ Future engagement captured (email notification signup)
- ✅ Positive framing ("Coming in V2" not "Not supported")

---

## Journey Decision Points Summary

**Common Decision Points Across Journeys:**
1. **Trust Assessment:** "Is this safe/legitimate?" → Addressed via simple UI, no login, open-source transparency
2. **Budget Setting:** "Should I enter respec points?" → Mixed clarity (quick-select helps, but tooltip needed)
3. **Error Recovery:** "What do I do when it fails?" → Structured error messages enable self-recovery
4. **Result Trust:** "Can I trust these numbers?" → Confidence scoring + verification in PoB builds trust
5. **Limitation Acceptance:** "Will this work for my build?" → Honest upfront communication about MVP scope

**Key Success Factors:**
- **Immediate feedback** at each step (validation, progress, errors)
- **Clear next actions** (never leave user wondering "what now?")
- **Trust building** through verification and transparency
- **Honest limitations** prevent disappointment and build credibility

## UX Design Principles

### Principle 1: Trust Through Transparency

**Philosophy:** The algorithm is not the product—trust is. Every decision, limitation, and calculation must be visible and verifiable.

**Implementation:**
- Display real-time progress messages showing what system is doing ("Testing damage improvements... 247 configurations evaluated")
- Show confidence scores on results ("High confidence - verified" vs "Low confidence - verify in PoB")
- Provide exportable PoB codes users can inspect themselves
- Never hide errors—show structured error messages with technical details available
- Document known limitations upfront (local optimum disclaimer, unsupported build types)

**Example:**
> Bad: "Optimization complete. +12% DPS" (black box, no proof)
> Good: "Optimization complete. +12% DPS. Confidence: High (verified). [See 6 node changes] [Copy PoB code to verify yourself]"

**Success Metric:** 90%+ of users verify results in PoB before implementing (indicates trust)

---

### Principle 2: Immediate Feedback at Every Step

**Philosophy:** Users should never wonder "is this working?" or "what do I do next?" The system continuously communicates state and next actions.

**Implementation:**
- Paste PoB code → Instant validation with green checkmark or error message
- Click Optimize → Progress bar appears within 500ms
- Optimization running → Updates every 2 seconds with status messages
- Results ready → Clear before/after comparison with action buttons
- Error occurs → Structured message with recovery steps

**Example:**
> Bad: User pastes code → 5 second silence → suddenly shows results (anxiety!)
> Good: User pastes code → "Processing..." (200ms) → "Build loaded: Level 92 Mercenary, 1.45M DPS" → Green checkmark

**Success Metric:** <1% of users report "system froze" or "not sure if it's working"

---

### Principle 3: Ruthless Simplicity (One Job Perfectly)

**Philosophy:** This tool optimizes passive trees. Nothing more. Every feature that doesn't directly serve that goal is clutter.

**Implementation:**
- Single-page workflow: Input → Optimize → Results (no navigation complexity)
- Three inputs total: PoB code, goal dropdown, budget fields
- No account creation, no file uploads, no settings menus
- No feature creep: Item suggestions, skill optimization, full build generation = OUT OF SCOPE
- Clear rejection of unsupported features with honest explanation

**Example:**
> Bad: Dashboard with "My Builds," "Settings," "Community Builds," "Pro Features" tabs
> Good: One page with text box, dropdown, two number inputs, one button

**Success Metric:** 95%+ of first-time users complete workflow without documentation

---

### Principle 4: Honest Limitations Over False Promises

**Philosophy:** Admitting what the tool CAN'T do builds more trust than overpromising capabilities.

**Implementation:**
- Detect unsupported builds (minions, totems) BEFORE optimization starts
- Display clear "Not Supported (Yet!)" messages with positive framing ("Coming in V2")
- Document local optimum limitation: "Result may not be global best - this is inherent to algorithm"
- Show confidence levels: High/Medium/Low instead of claiming 100% accuracy
- Provide "Learn more about limitations" links for curious users

**Example:**
> Bad: Accept minion build → fail 3 minutes later → "Error: Cannot optimize"
> Good: Detect minion build → immediate message → "Not supported yet. Coming in V2. Here's what IS supported..."

**Success Metric:** 0% angry users feeling "misled" or "wasted time"

---

### Principle 5: Prioritize Free Value Over Costly Changes

**Philosophy:** Players care about in-game currency cost. Always show them what they can get for FREE before suggesting expensive changes.

**Implementation:**
- Auto-detect unallocated passive points (free to allocate)
- Prioritize free allocations in optimization algorithm (use unallocated points first)
- Clearly distinguish FREE changes from COSTLY respecs in results:
  - "11 new nodes allocated (FREE)"
  - "4 nodes deallocated and replaced (costs 4 respec points)"
- Show tiered implementation plan: "Implement free changes now, respec changes when you earn points"
- Display cost-benefit analysis: "4 respec points for +5% DPS = 30min farming for permanent boost"

**Example:**
> Bad: "Change 15 nodes for +12% DPS" (user doesn't know 11 are free, 4 cost currency)
> Good: "Use your 11 FREE points + swap 4 nodes (4 respec) for +12% DPS. Implement free changes now!"

**Success Metric:** 80%+ of users with unallocated points implement free allocations immediately

---

### Principle 6: Progressive Disclosure (Show Complexity Only When Needed)

**Philosophy:** Simple by default, detailed when requested. Don't overwhelm casual users; don't hide depth from power users.

**Implementation:**
- Default view: Simple results (DPS before/after, improvement %)
- Expandable sections:
  - "Show node changes" → Lists specific nodes to allocate/deallocate
  - "Show technical details" → Displays error stack traces, calculation details
  - "Show advanced options" → Multi-objective optimization, constraint tuning (V2)
- Helper text: Subtle, non-intrusive (small gray text below inputs)
- Tooltips: Available on hover/focus but not required for basic workflow

**Example:**
> Bad: Results page shows 50 lines of technical data upfront (overwhelming)
> Good: "DPS: +12% (1.45M → 1.62M)" with [Show 6 node changes ▼] and [Show calculation details ▼]

**Success Metric:** Advanced users find all details they want; casual users never see unnecessary complexity

---

### Principle 7: Zero Friction for Core Workflow

**Philosophy:** Every click, field, or step that doesn't add value is friction that reduces completion rate.

**Implementation:**
- No account creation required (stateless)
- No file upload (just paste text)
- Auto-detect unallocated points (one less field to fill)
- Auto-select "Maximize DPS" as default goal (most common use case)
- Quick-select buttons for budget ([Free (0)], [Budget (15)], [Unlimited])
- One-click "Copy to Clipboard" for PoB code export
- Keyboard shortcuts: Enter submits form, Escape cancels

**Example:**
> Bad: 8-step workflow with account creation, email verification, file upload, settings configuration
> Good: 3 steps: Paste code → Click Optimize → Copy result

**Success Metric:** 95th percentile task completion time <30 seconds (excluding optimization processing)

---

### Principle 8: Accessible by Default (Not an Afterthought)

**Philosophy:** Accessibility features benefit everyone, not just users with disabilities. They're table stakes, not nice-to-haves.

**Implementation:**
- Keyboard-only navigation works perfectly (Tab, Enter, Escape)
- Screen reader support via semantic HTML and ARIA labels
- High contrast ratios (4.5:1 minimum for WCAG AA)
- Focus indicators visible on all interactive elements
- No information conveyed by color alone (use icons + text)
- Text scales to 200% without breaking layout
- Minimum font size: 14px body, 16px inputs

**Example:**
> Bad: Custom styled dropdowns that break with keyboard navigation
> Good: Native HTML elements enhanced with ARIA, fully keyboard accessible

**Success Metric:** WCAG 2.1 AA automated scan passes with 0 errors

---

### Principle 9: Error Recovery Over Error Prevention

**Philosophy:** Users will make mistakes. The system should help them recover gracefully, not blame them.

**Implementation:**
- Structured error messages: Problem + Cause + Solution + Technical details (collapsible)
- Never say "Invalid input"—say "Build code appears incomplete. Try re-copying from PoB."
- Preserve user input after errors (PoB code stays in text field, don't make them re-paste)
- Suggest fixes: "Not sure how many respec points you have? Check PoB: Character Stats → Respec Points"
- Cancel button always available (let users abort and retry)

**Example:**
> Bad: "Error 402: Invalid XML schema" (user has no idea what to do)
> Good: "Build code corrupted. Usually happens when partially copied. Please re-copy entire code from PoB. [Show technical details ▼]"

**Success Metric:** 90%+ of users recover from first error and successfully complete workflow

---

### Principle 10: Performance IS User Experience

**Philosophy:** Speed isn't a technical metric—it's a trust signal. Fast responses communicate "this tool respects your time."

**Implementation:**
- Page loads <2 seconds (lightweight, no heavy frameworks)
- Input validation <100ms (instant feedback feels responsive)
- Parsing PoB code <500ms (green checkmark appears quickly)
- Progress updates every 2 seconds (never >10s without feedback)
- Results render <1 second after optimization completes
- UI interactions <100ms (button clicks feel instant)

**Performance Budget:**
- Initial page load: <2s on 10 Mbps connection
- JavaScript bundle: <100KB gzipped
- No render-blocking resources
- Optimize images: WebP format, lazy loading

**Example:**
> Bad: 8-second page load → 3-second parse delay → 15-second silence during optimization
> Good: <2s page load → <500ms parse with instant green checkmark → 2s update intervals during optimization

**Success Metric:** 95th percentile page load <2s; all interactions feel instant (<100ms)

---

## UX Principles Applied to Key Features

### Budget Input (Dual Budget System)

**Principles Applied:**
- **#5 (Free Value Priority):** Separate unallocated (FREE) from respec (COSTLY)
- **#2 (Immediate Feedback):** Auto-detect unallocated points, show calculation
- **#6 (Progressive Disclosure):** Simple by default (two number inputs), helper text subtle
- **#7 (Zero Friction):** Quick-select buttons reduce typing

**Result:** Users understand budget options without reading documentation

### Error Messages

**Principles Applied:**
- **#1 (Transparency):** Show technical details (collapsible)
- **#9 (Error Recovery):** Structured format with solution steps
- **#4 (Honest Limitations):** "Not supported yet" instead of vague errors

**Result:** 90%+ error recovery rate without support tickets

### Results Display

**Principles Applied:**
- **#1 (Transparency):** Confidence score, node changes visible, PoB code exportable
- **#5 (Free Value Priority):** FREE allocations highlighted separately from costly respecs
- **#6 (Progressive Disclosure):** Summary view with expandable details
- **#2 (Immediate Feedback):** Clear before/after comparison

**Result:** Users trust results enough to implement immediately

---

## Principles Priority Ranking (When in Conflict)

1. **Trust Through Transparency** - Non-negotiable. If we lose trust, tool is worthless.
2. **Honest Limitations** - Critical for long-term credibility
3. **Immediate Feedback** - Prevents user abandonment during processing
4. **Ruthless Simplicity** - Prevents feature creep that dilutes value
5. **Free Value Priority** - Differentiator that builds user loyalty
6. **Performance IS UX** - Speed builds trust and respect
7. **Zero Friction** - Maximizes completion rate
8. **Error Recovery** - Reduces support burden, improves satisfaction
9. **Accessible by Default** - Expands addressable market
10. **Progressive Disclosure** - Balances simplicity vs depth

**Example Conflict:**
> Adding "Save build history" feature would add value BUT violates Ruthless Simplicity (#3).
> Decision: Reject feature for MVP. Complexity cost > marginal value.

---

## Anti-Patterns to Avoid

**❌ Dark Patterns:**
- No manipulative design (no hidden fees, no misleading buttons, no forced sharing)
- No "Sign up for Pro to see full results" bait-and-switch
- No artificial delays to make free tier feel slow

**❌ Over-Engineering:**
- No accounts/auth for MVP (stateless is simpler)
- No custom UI framework (use semantic HTML + light CSS)
- No complex state management (React overkill for single-page tool)

**❌ False Precision:**
- Don't claim "12.7482% improvement" (implies false precision)
- Round to 1 decimal place: "12.7% improvement"
- Show confidence levels instead of pretending 100% accuracy

**❌ Jargon & Gatekeeping:**
- Don't assume users know optimization algorithms
- Don't require understanding of "hill climbing" or "local optima"
- Explain in plain language: "Result may not be absolute best, but it's a solid improvement"



## Epics

### Epic Structure Overview

This local MVP is organized into **3 major epics** delivering incremental value toward a complete, polished local tool. Total estimated scope: **25-31 user stories**.

**Delivery Strategy:** Sequential with limited parallel work. Epics 1-2 are foundation (must complete first), Epic 3 delivers complete user-facing local application with reliability built in.

---

### Epic 1: Foundation - PoB Calculation Engine Integration

**Goal:** Enable accurate Path of Building calculations in headless Python environment.

**Business Value:** This is the technical foundation—without accurate PoB calculations, the entire product fails. Achieving 100% calculation parity with official PoB builds user trust and enables all optimization work.

**Key Capabilities Delivered:**
- Parse PoB import codes (Base64 → XML → build data structure)
- Load HeadlessWrapper.lua via Lupa in Python runtime
- Implement required stub functions (Deflate/Inflate, ConPrintf, etc.)
- Execute single-build calculations and extract stats (DPS, EHP, resistances)
- Validate calculation accuracy against PoB GUI (within 0.1% tolerance)
- Handle PoE 2-specific passive tree data and character classes

**Story Count Estimate:** 8-10 stories

**Critical Dependencies:**
- PoB PoE2 repository cloned to `external/pob-engine/` (Git submodule)
- Lupa library installed and tested
- Access to HeadlessWrapper.lua and Data/ modules

**Success Criteria:**
- Calculate 100 sample builds with 100% success rate
- Calculation results match PoB GUI within 0.1% tolerance
- Performance: Single calculation completes in <100ms

**References:** FR-1.1, FR-1.3, FR-3.1, FR-3.2, FR-5.5, NFR-1, NFR-7

---

### Epic 2: Core Optimization Engine

**Goal:** Implement hill climbing algorithm that discovers mathematically superior passive tree configurations within budget constraints.

**Business Value:** This is the "magic" users pay for—automatic discovery of better trees. Delivering 5-15% median improvement transforms 3+ hours of manual work into 30 seconds of computation.

**Key Capabilities Delivered:**
- Hill climbing algorithm with neighbor generation (1-hop node additions/swaps)
- Dual budget constraint enforcement (unallocated points + respec points)
- Auto-detection of unallocated passive points from character level
- Metric selection and optimization target (DPS, EHP, or custom weight)
- Convergence detection (stop when no improvement found)
- Budget prioritization (use free allocations before costly respecs)

**Story Count Estimate:** 7-9 stories

**Critical Dependencies:**
- Epic 1 complete (calculation engine working)
- Passive tree graph structure loaded (node connections, pathing)
- Understanding of allocated nodes, class starting positions

**Success Criteria:**
- Find improvements for 80%+ of non-optimal builds
- Median improvement: 8%+ for builds with budget headroom
- Optimization completes within 5 minutes for complex builds
- Budget constraints never exceeded (hard stop enforcement)

**References:** FR-2.1, FR-2.2, FR-2.3, FR-4.1, FR-4.2, FR-4.3, FR-4.4, FR-4.6, NFR-2

---

### Epic 3: User Experience & Local Reliability

**Goal:** Deliver a complete local web UI for build optimization with robust error handling, progress tracking, and reliable resource management for repeated local use.

**Business Value:** This epic transforms the working algorithm into a polished, usable tool. Combining UX with local reliability ensures the developer can run optimizations repeatedly without crashes, memory leaks, or confusing errors—building confidence before any public release.

**Key Capabilities Delivered:**

**User Interface (Flask localhost:5000):**
- Local web UI with PoB code input textarea and validation
- Budget input UI with dual fields (unallocated + respec) and auto-detection
- Metric selection dropdown (DPS, EHP, weighted blend)
- Real-time optimization progress messages (current iteration, best found, etc.)
- Results display with before/after comparison and budget breakdown
- Export optimized PoB code for round-trip verification
- Error messages for unsupported builds with clear explanations

**Local Reliability:**
- Optimization timeout (5-minute hard stop prevents infinite loops)
- Resource cleanup after each optimization (prevent memory leaks on repeated runs)
- File-based error logging (logs/optimizer.log for debugging)
- Performance optimization (batch calculation efficiency, memory limits)

**Story Count Estimate:** 10-12 stories

**Critical Dependencies:**
- Epic 2 complete (optimization engine functional)
- Flask installed (lightweight web framework)
- Simple HTML/CSS UI (no complex frontend framework needed)

**Success Criteria:**
- 95%+ of valid PoB codes parse successfully
- Clear error messages for 100% of unsupported cases
- Users can verify results in PoB GUI (round-trip validation)
- Budget breakdown shows free vs costly changes
- Can run 50+ consecutive optimizations without memory leaks
- All optimizations complete or timeout within 5 minutes
- Errors logged to file for debugging

**References:** FR-1.2, FR-1.4, FR-1.5, FR-1.6, FR-1.7, FR-2.2, FR-3.3, FR-3.4, FR-5.1, FR-5.2, FR-5.3, FR-5.4, NFR-2, NFR-4, NFR-5

---

### Epic Dependency Map

```
Epic 1 (Foundation - PoB Integration)
    ↓
Epic 2 (Core Optimization Engine)
    ↓
Epic 3 (UX & Local Reliability) ← Complete local MVP
```

**Delivery Strategy:**
- Epics must be completed sequentially (each depends on previous)
- Epic 3 UI design can begin during Epic 2 development
- Total estimated scope: **25-31 stories** across 3 epics

---

### Detailed Story Breakdown

See **[epics.md](epics.md)** for complete user story hierarchy with acceptance criteria, technical notes, and story point estimates.

**Summary:** 28 user stories across 3 epics (80 story points estimated)

## Out of Scope

The following features are **intentionally excluded** from the local MVP to maintain ruthless scope discipline and 2-month timeline. These may be considered for post-MVP phases after validation.

### Deferred to V2 (Post-MVP Validation)

**Advanced Optimization Algorithms:**
- Simulated annealing layer on top of hill climbing
- Genetic algorithms or constraint solvers
- Multi-objective optimization (Pareto frontiers)
- Global optimum guarantees

**Public Deployment Features:**
- Cloud hosting (VPS, serverless, container orchestration)
- User accounts and authentication
- Multi-user session management
- Rate limiting and abuse prevention
- Uptime monitoring and alerting
- Analytics tracking (GA4, Plausible)
- Privacy policy and Terms of Service pages

**UI Enhancements:**
- Visual passive tree display (node highlighting, pathing animation)
- Drag-and-drop PoB code import
- Save/load optimization history
- Compare multiple optimization results side-by-side
- Mobile-responsive design
- Dark mode
- Internationalization and localization:
  * Community translations for major PoE markets (Korean, Chinese, Russian, Portuguese)
  * Multi-language UI support with i18n framework
  * Regional date/time formatting
  * Note: Initial launch English-only, but UI text should be externalized to constants/config for future translation

**Advanced Features:**
- Cluster jewel optimization (extremely complex, high risk)
- Ascendancy class optimization (respec class choice)
- Skill gem link optimization
- Item recommendation (stat requirements, synergies)
- Budget optimizer (gold cost per improvement)

### Explicitly NOT Building (Ever)

**Out of Scope - Philosophy Violation:**
- AI chatbot for build advice (scope creep, over-engineering)
- Full build generation from scratch (competitive disadvantage—too complex)
- Build sharing and community features (social network complexity)
- Monetization infrastructure (paywall, subscriptions, ads)

**Out of Scope - Technical Infeasibility:**
- Real-time PoB API integration (PoB has no official API)
- Automatic PoB installation or updates (distribution complexity)
- In-game overlay or integration (ToS violation risk)

### Unsupported Build Features (Technical Limitations)

**MVP Will NOT Support:**
- Timeless Jewels (passive tree modifications unpredictable)
- Thread of Hope (range calculations complex)
- Forbidden Flesh/Flame jewels (ascendancy node allocation)
- Corrupted passive trees (non-standard modifications)
- Private League modifiers (custom tree modifications)

**Rationale:** These features add 10x complexity for <5% of users. Better to serve 95% of users well than 100% of users poorly.

---

**Scope Validation:** Every feature request during MVP development should be evaluated against this list. If not on the "must-have" list, defer to V2 or reject entirely.

---

## Assumptions and Dependencies

### Critical Assumptions

**Technical Assumptions:**
1. **PoB PoE 2 Repository Stability:** PathOfBuildingCommunity/PathOfBuilding-PoE2 repository will remain available and maintained
2. **Lupa Performance:** Lupa + LuaJIT can achieve 150-500ms for 1000 calculations (validated in research, needs confirmation in practice)
3. **HeadlessWrapper.lua Compatibility:** HeadlessWrapper.lua works with PoE 2 passive tree data (not just PoE 1)
4. **Calculation Accuracy:** Headless PoB calculations will match GUI results within 0.1% tolerance
5. **Python Environment:** Python 3.10+ available on developer machine

**Algorithm Assumptions:**
1. **Hill Climbing Sufficient:** Hill climbing will find 5-15% improvements for 80%+ of non-optimal builds (no need for advanced algorithms in MVP)
2. **Local Optima Acceptable:** Users will accept "good improvement" vs "guaranteed global optimum"
3. **Neighbor Space Manageable:** 1-hop neighbor generation produces reasonable search space (50-200 neighbors per iteration)
4. **Convergence Time:** Most optimizations will converge within 5 minutes

**User Assumptions:**
1. **PoB Familiarity:** Users already use Path of Building and understand PoB codes
2. **Technical Comfort:** Developer user (you) can run Python scripts and use localhost web UI
3. **Build Quality:** Test builds are non-trivial (not already perfectly optimized)

### External Dependencies

**Required Third-Party Software:**
- **PoB PoE 2 Repository:** GitHub.com/PathOfBuildingCommunity/PathOfBuilding-PoE2 (MIT License, active maintenance)
- **Python 3.10+:** Available from python.org or system package manager
- **Lupa Library:** PyPI package `lupa>=2.0` (LuaJIT included)
- **Flask Framework:** PyPI package `flask>=3.0` (web server)

**Data Dependencies:**
- **PoE 2 Passive Tree Data:** Included in PoB repository (Data/PassiveTree.lua)
- **Character Class Data:** Included in PoB repository (Data/Classes.lua)
- **PoB Calculation Modules:** Included in PoB repository (src/Modules/)

**Development Tools (Optional):**
- **Git:** For version control and submodule management
- **pytest:** For automated testing
- **pip-audit:** For dependency security scanning

**Dependency Risks:**
- **PoB Repository Changes:** PoB updates may break integration (mitigation: pin to specific commit, manual sync)
- **PoE 2 Game Patches:** Game balance changes may require PoB updates (mitigation: wait for PoB community updates)
- **Lupa Compatibility:** New Python versions may break Lupa (mitigation: pin Python version in requirements.txt)

---

## Next Steps

### Immediate Next Steps (Before Development)

**Phase 1: Repository Setup (1 day)**
- [ ] Create GitHub repository: `poe2-passive-tree-optimizer`
- [ ] Initialize with README, .gitignore (Python), LICENSE (MIT)
- [ ] Follow REPOSITORY-SETUP-GUIDE.md to create folder structure
- [ ] Add PoB PoE 2 repository as Git submodule: `external/pob-engine/`
- [ ] Verify PoB files accessible: `external/pob-engine/HeadlessWrapper.lua` exists
- [ ] Create `requirements.txt` and `requirements-dev.txt`
- [ ] Install dependencies: `pip install -r requirements-dev.txt`

**Phase 2: Architecture & Technical Design (3-5 days)**
- [ ] Create `docs/architecture.md` with system component diagram
- [ ] Design data flow: PoB code → Parser → Optimizer → Results → Export
- [ ] Design Python module structure: `src/api/`, `src/calculator/`, `src/parsers/`
- [ ] Document Lupa integration pattern (stub functions, module loading)
- [ ] Design optimization algorithm classes (HillClimber, BudgetTracker, NeighborGenerator)
- [ ] Create API contracts for internal functions
- [ ] Identify technical spikes needed (e.g., HeadlessWrapper.lua POC)

**Phase 3: Development Sprint Planning (1 day)**
- [ ] Break down Epic 1 stories into tasks
- [ ] Prioritize Epic 1 Story 1.5 (Execute Single Build) as first integration test
- [ ] Plan 2-week sprints: Sprint 1 = Epic 1, Sprint 2-3 = Epic 2, Sprint 4 = Epic 3
- [ ] Set up development environment checklist
- [ ] Create initial test fixtures (10 sample PoB codes)

### Handoff to Architecture Phase

**Documents Required:**
- ✅ PRD (this document) - **COMPLETE**
- ✅ Epic Breakdown (epics.md) - **COMPLETE**
- ✅ Product Brief - **EXISTS** (product-brief-poe2-passive-tree-optimizer-2025-10-08.md)
- ✅ Technical Research - **EXISTS** (technical-research-2025-10-07.md, LupaLibraryDeepResearch.md)
- ✅ Repository Setup Guide - **COMPLETE** (REPOSITORY-SETUP-GUIDE.md)
- ⏭️ **Architecture Document** - **TODO** (create docs/architecture.md)

**Key Questions for Architecture Phase:**
1. How should Python modules be organized? (Monolithic vs. modular)
2. What's the exact Lupa integration pattern? (Class-based wrapper vs. functional)
3. How to handle Lua state management? (Singleton vs. per-session instances)
4. What's the data model for passive trees? (Graph library vs. custom adjacency list)
5. How to structure Flask routes? (Single endpoint vs. RESTful API)
6. What testing strategy? (Unit tests, integration tests, E2E tests)

**Success Criteria for Architecture Phase:**
- System architecture diagram created
- All major components defined with responsibilities
- Internal APIs documented (function signatures, data structures)
- Technical risks identified with mitigation strategies
- Development environment setup validated (can load PoB, run Flask)

### Development Workflow Recommendations

**Week-by-Week Plan (8 weeks to MVP):**

**Weeks 1-3: Epic 1 (Foundation)**
- Week 1: Stories 1.1-1.4 (Parse PoB, Setup Lupa, Stubs, Load HeadlessWrapper)
- Week 2: Stories 1.5-1.6 (Execute Calculation, Parity Testing)
- Week 3: Stories 1.7-1.8 (PoE 2 Tree, Batch Optimization)

**Weeks 4-6: Epic 2 (Optimization)**
- Week 4: Stories 2.1-2.3 (Hill Climbing, Neighbors, Auto-Detect)
- Week 5: Stories 2.4-2.6 (Dual Budget, Prioritization, Metrics)
- Week 6: Stories 2.7-2.8 (Convergence, Progress Tracking)

**Weeks 7-8: Epic 3 (UX & Reliability)**
- Week 7: Stories 3.1-3.7 (Flask UI, Input, Results, Export)
- Week 8: Stories 3.8-3.12 (Errors, Timeout, Cleanup, Logging, Performance)

**Buffer:** 2-3 days for unexpected issues, polish, documentation

### Validation Checklist (MVP Complete)

**Functional Validation:**
- [ ] Can parse 20+ different PoB codes successfully
- [ ] Calculations match PoB GUI within 0.1% tolerance (10 test builds)
- [ ] Optimization finds 8%+ improvement on 15+ non-optimal builds
- [ ] Dual budget system works correctly (free allocations prioritized)
- [ ] All 3 metrics work: DPS, EHP, Balanced
- [ ] Exported PoB codes import successfully into PoB GUI
- [ ] Clear error messages for 5+ unsupported build types

**Non-Functional Validation:**
- [ ] 1000 calculations complete in <1 second
- [ ] Optimizations complete within 5 minutes (or timeout gracefully)
- [ ] 50+ consecutive optimizations without memory leaks
- [ ] Server starts in <5 seconds
- [ ] Zero runtime costs (no paid services used)

**User Experience Validation:**
- [ ] First-time use completes without documentation
- [ ] Progress messages update in real-time
- [ ] Budget breakdown shows free vs. costly changes clearly
- [ ] Error messages are actionable (not cryptic)

**Code Quality:**
- [ ] All code committed to Git
- [ ] README.md documents setup in <10 steps
- [ ] requirements.txt includes all dependencies with versions
- [ ] No sensitive data in logs
- [ ] MIT License file included

---

**Next Document to Create:** `docs/architecture.md`
**Workflow Transition:** PRD Phase → Architecture & Design Phase

## Document Approval

**Author:** John (Product Manager)
**Reviewed By:** Alec (Product Owner)
**Review Date:** 2025-10-08
**Approval Date:** 2025-10-09
**Approval Status:** ✅ **APPROVED** - Ready for Architecture Phase

**Review Notes:**
- PRD validated against planning workflow checklist (68/72 items passed - 94.4%)
- All critical requirements documented and testable
- Scope appropriately constrained for 2-month local MVP
- Zero blocking issues identified
- Minor documentation gaps addressed (approval section, revision history)

**Sign-off Authority:** Product Owner approved for technical architecture and development phases.

---

## Document Status

- [x] Goals and context validated (local MVP scope confirmed)
- [x] All functional requirements reviewed (26 FRs across 6 groups)
- [x] User journeys cover all major personas (3 journeys documented)
- [x] Epic structure approved for phased delivery (3 epics, 28 stories)
- [x] Ready for architecture phase

**PRD Status:** ✅ **COMPLETE** - Ready for handoff to architecture & design phase

**Documents Generated:**
- `docs/PRD.md` (this document) - 2,200+ lines
- `docs/epics.md` - 28 user stories with acceptance criteria
- `docs/REPOSITORY-SETUP-GUIDE.md` - Beginner-friendly Git/GitHub setup
- `docs/DUAL-BUDGET-FEATURE-SUMMARY.md` - Dual budget feature deep-dive

**Key Decisions:**
- ✅ Local-only MVP (zero hosting costs)
- ✅ Dual budget system (unallocated + respec points)
- ✅ 3 epics, 8-week timeline
- ✅ Flask localhost:5000 interface
- ✅ Hill climbing algorithm (no advanced optimization needed)

---

_This PRD was generated for Level 3 project scope with local deployment constraints applied._
