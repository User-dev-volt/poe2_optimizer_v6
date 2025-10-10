# poe2_optimizer_v6 - Epic Breakdown

**Author:** Alec
**Date:** 2025-10-08
**Project Level:** Level 3 (Full product - 12-40 stories, 2-5 epics)
**Target:** Local MVP within 2 months for personal use and validation

---

## Epic Overview

This local MVP consists of **3 major epics** delivering a complete, polished passive tree optimizer running on localhost. Total scope: **25-31 user stories**.

**Delivery Strategy:**
- Epics delivered sequentially (each depends on previous)
- Epic 3 UI design can begin during Epic 2 development
- All epics required for functional local MVP

**Epic Summary:**

1. **Foundation - PoB Integration** (8-10 stories)
   - Enable accurate PoB calculations in Python via Lupa + HeadlessWrapper.lua
   - Prerequisite for all optimization work

2. **Core Optimization Engine** (7-9 stories)
   - Implement hill climbing algorithm with dual budget constraints
   - Deliver 5-15% median improvement in passive tree efficiency

3. **UX & Local Reliability** (10-12 stories)
   - Flask web UI at localhost:5000 with complete user workflow
   - Robust error handling, progress tracking, resource cleanup

---

## Epic 1: Foundation - PoB Calculation Engine Integration

**Goal:** Enable accurate Path of Building calculations in headless Python environment.

**Business Value:** Without accurate PoB calculations, the entire product fails. Achieving 100% calculation parity with official PoB builds user trust and enables all optimization work.

**Success Criteria:**
- Calculate 100 sample builds with 100% success rate
- Calculation results match PoB GUI within 0.1% tolerance
- Performance: Single calculation completes in <100ms

---

### User Stories - Epic 1

#### Story 1.1: Parse PoB Import Code
**As a** developer
**I want** to parse Base64-encoded PoB codes into XML data structures
**So that** I can extract build information for calculations

**Acceptance Criteria:**
- System decodes Base64 PoB codes successfully
- System decompresses zlib-encoded XML
- System parses XML into Python data structure (dictionaries/objects)
- System extracts: character level, class, allocated passive nodes, items, skills
- System validates PoB code format (detect corrupted codes)
- System rejects codes >100KB (per FR-1.1)

**Technical Notes:**
- Use Python `base64`, `zlib`, `xml.etree.ElementTree` libraries
- Reference FR-1.1 (PoB Code Input Validation)
- Example PoB code structure available in PoB repository documentation

**Priority:** Must-have (MVP blocking)
**Size:** Medium (3 story points)

---

#### Story 1.2: Setup Lupa + LuaJIT Runtime
**As a** developer
**I want** to embed LuaJIT in Python using Lupa
**So that** I can execute PoB's Lua calculation engine

**Acceptance Criteria:**
- Lupa library installed and tested (`pip install lupa`)
- LuaJIT runtime initializes successfully in Python
- Can load and execute simple Lua scripts from Python
- Lua global namespace accessible from Python
- Python can call Lua functions and retrieve results

**Technical Notes:**
- Lupa requires LuaJIT (included in Lupa package on most platforms)
- Test with simple Lua script: `return 2 + 2` should return `4`
- Verify Lupa version supports table passing (dict ↔ Lua table conversion)

**Priority:** Must-have (MVP blocking)
**Size:** Small (2 story points)

---

#### Story 1.3: Implement Required Stub Functions
**As a** developer
**I want** to provide Python implementations of PoB's external dependencies
**So that** HeadlessWrapper.lua can run without PoB's GUI environment

**Acceptance Criteria:**
- Implement `Deflate(str)` and `Inflate(str)` using Python `zlib`
- Implement `ConPrintf(...)` as no-op (or print to console for debugging)
- Implement `ConPrintTable(table)` as no-op
- Implement `SpawnProcess(...)` and `OpenURL(...)` as no-ops (headless mode)
- All stubs accessible from Lua global namespace
- No errors when HeadlessWrapper.lua calls stub functions

**Technical Notes:**
- Reference `LupaLibraryDeepResearch.md` Section 6 for stub implementation patterns
- Compression functions critical (PoB codes are compressed)
- Console functions can be no-ops (or log to file for debugging)
- Process/URL functions not needed for calculations

**Priority:** Must-have (MVP blocking)
**Size:** Medium (3 story points)

---

#### Story 1.4: Load HeadlessWrapper.lua and PoB Modules
**As a** developer
**I want** to load HeadlessWrapper.lua and required PoB data modules
**So that** the PoB calculation engine is ready to process builds

**Acceptance Criteria:**
- System locates HeadlessWrapper.lua in `external/pob-engine/`
- System loads HeadlessWrapper.lua via Lupa
- System loads required PoB modules: Data/PassiveTree.lua, Data/Classes.lua
- System initializes PoB calculation context
- No Lua errors during module loading
- PoB passive tree data accessible (nodes, connections, stats)

**Technical Notes:**
- Requires PoB repository as Git submodule (external/pob-engine/)
- May need to set Lua package path to find PoB modules
- Reference REPOSITORY-SETUP-GUIDE.md for submodule setup
- Test with: Load passive tree data, verify node count matches PoB

**Priority:** Must-have (MVP blocking)
**Size:** Large (5 story points)

---

#### Story 1.5: Execute Single Build Calculation
**As a** developer
**I want** to calculate stats for a single PoB build
**So that** I can verify calculation accuracy

**Acceptance Criteria:**
- System accepts PoB XML data as input
- System calls PoB calculation engine via HeadlessWrapper
- System extracts calculated stats: DPS, Life, EHP, resistances
- Calculation completes in <100ms
- No Lua errors during calculation
- Results are numeric (not nil/undefined)

**Technical Notes:**
- Reference HeadlessWrapper.lua API documentation
- May need to create Build object in Lua, set passive nodes, call CalcBuild()
- Extract stats from Build.calcs table (DPS, Life, etc.)
- Profile performance (target: <100ms per calculation)

**Priority:** Must-have (MVP blocking)
**Size:** Large (5 story points)

---

#### Story 1.6: Validate Calculation Accuracy (Parity Testing)
**As a** developer
**I want** to verify calculations match PoB GUI results
**So that** I can trust optimization recommendations

**Acceptance Criteria:**
- Create 10 test builds with known PoB GUI results
- Calculate each build using headless engine
- Compare results to PoB GUI: DPS, Life, EHP, resistances
- All results within 0.1% tolerance (per NFR-1)
- Document any discrepancies and root cause
- Create automated parity test suite

**Technical Notes:**
- Export test builds from PoB GUI, save as fixture files
- Manually record PoB GUI stats for comparison
- Use pytest for automated testing
- Reference FR-5.5 (Round-Trip Validation)

**Priority:** Must-have (MVP blocking)
**Size:** Medium (3 story points)

---

#### Story 1.7: Handle PoE 2-Specific Passive Tree Data
**As a** developer
**I want** to load PoE 2 passive tree structure
**So that** optimization can navigate the tree correctly

**Acceptance Criteria:**
- System loads PoE 2 passive tree JSON/Lua data
- System understands node IDs, connections (edges), and node stats
- System identifies character class starting positions
- System validates allocated nodes are connected (no orphan nodes)
- System handles Notable/Keystone/Small passive types

**Technical Notes:**
- PoE 2 tree structure in Data/PassiveTree.lua
- Tree is a graph: nodes have IDs, edges connect neighbors
- Class starting positions define valid entry points
- Must handle pathing (can't allocate disconnected nodes)

**Priority:** Must-have (MVP blocking)
**Size:** Medium (3 story points)

---

#### Story 1.8: Batch Calculation Optimization
**As a** developer
**I want** to calculate 1000+ builds efficiently
**So that** optimization completes in reasonable time

**Acceptance Criteria:**
- Batch calculate 1000 builds in <1 second (per performance requirement)
- Pre-compile Lua functions (compile once, call 1000x)
- Reuse Build objects where possible (avoid recreation overhead)
- Memory usage <100MB during batch processing
- No memory leaks (verify with repeated runs)

**Technical Notes:**
- Reference `LupaLibraryDeepResearch.md` Section 2 (Performance)
- Key optimization: Pre-compile Lua functions
- Avoid creating new Lua tables on each iteration
- Profile with Python `cProfile` or `line_profiler`

**Priority:** Must-have (MVP blocking)
**Size:** Medium (3 story points)

---

**Epic 1 Total:** 8 stories (26 story points estimated)

---

## Epic 2: Core Optimization Engine

**Goal:** Implement hill climbing algorithm that discovers mathematically superior passive tree configurations within budget constraints.

**Business Value:** This is the "magic" users pay for—automatic discovery of better trees. Delivering 5-15% median improvement transforms 3+ hours of manual work into 30 seconds of computation.

**Success Criteria:**
- Find improvements for 80%+ of non-optimal builds
- Median improvement: 8%+ for builds with budget headroom
- Optimization completes within 5 minutes for complex builds
- Budget constraints never exceeded (hard stop enforcement)

---

### User Stories - Epic 2

#### Story 2.1: Implement Hill Climbing Core Algorithm
**As a** developer
**I want** to implement a hill climbing algorithm
**So that** the system can iteratively improve passive tree configurations

**Acceptance Criteria:**
- Algorithm starts with current passive tree (baseline)
- Algorithm generates neighbor configurations (add/swap 1 node)
- Algorithm evaluates each neighbor using PoB calculations
- Algorithm selects best neighbor if improvement found
- Algorithm repeats until convergence (no improvement)
- Algorithm returns best configuration found

**Technical Notes:**
- Classic hill climbing: current → neighbors → evaluate → best
- Convergence: Stop when no neighbor improves metric
- Track iteration count, best found, improvement history
- Reference FR-4.1 (Hill Climbing Optimization)

**Priority:** Must-have (MVP blocking)
**Size:** Large (5 story points)

---

#### Story 2.2: Generate Neighbor Configurations (1-Hop Moves)
**As a** developer
**I want** to generate valid neighbor passive tree configurations
**So that** hill climbing can explore the optimization space

**Acceptance Criteria:**
- Generate "add node" neighbors: add any unallocated connected node
- Generate "swap node" neighbors: remove 1 node, add 1 connected node
- Validate all neighbors are valid (connected tree, within budget)
- Limit neighbor count to reasonable size (e.g., 50-200 per iteration)
- Prioritize high-value nodes (Notable/Keystone over travel nodes)

**Technical Notes:**
- Must check node connectivity (can't allocate disconnected nodes)
- Connected = path exists from class starting position
- Use passive tree graph structure from Epic 1
- May implement smart neighbor selection (prune low-value moves)

**Priority:** Must-have (MVP blocking)
**Size:** Large (5 story points)

---

#### Story 2.3: Auto-Detect Unallocated Passive Points
**As a** developer
**I want** to automatically calculate unallocated passive points from PoB build
**So that** users don't have to manually enter this value

**Acceptance Criteria:**
- Calculate: `max_points = get_max_passive_points(character_level)`
- Calculate: `allocated_points = count_allocated_nodes(passive_tree)`
- Calculate: `unallocated_points = max(0, max_points - allocated_points)`
- Display auto-detected value in UI (user can override if wrong)
- Handle edge cases: quest rewards, special nodes, ascendancy points

**Technical Notes:**
- PoE 2 formula: Level 1 starts with N points, +1 per level, +quests
- Verify formula matches PoE 2 (may differ from PoE 1)
- Reference FR-2.2 (Budget Constraint - Unallocated Points)
- User override important (auto-detection ~90% accurate)

**Priority:** Must-have (MVP blocking)
**Size:** Small (2 story points)

---

#### Story 2.4: Implement Dual Budget Constraint Tracking
**As a** developer
**I want** to track unallocated points (U) and respec points (R) separately
**So that** optimization prioritizes free allocations over costly respecs

**Acceptance Criteria:**
- Track `unallocated_available` and `unallocated_used` (free allocations)
- Track `respec_available` and `respec_used` (costly deallocations)
- Enforce: `unallocated_used <= unallocated_available`
- Enforce: `respec_used <= respec_available` (or unlimited if None)
- Prevent moves that exceed either budget
- Log budget usage in optimization progress

**Technical Notes:**
- Reference FR-4.3 (Budget Enforcement - Dual Constraint)
- Reference DUAL-BUDGET-FEATURE-SUMMARY.md for implementation details
- Two separate counters, two separate limits
- Algorithm should prefer using U before R (prioritization)

**Priority:** Must-have (MVP blocking)
**Size:** Medium (3 story points)

---

#### Story 2.5: Implement Budget Prioritization (Free-First Strategy)
**As a** developer
**I want** optimization to use unallocated points before respec points
**So that** users maximize free value before spending currency

**Acceptance Criteria:**
- When generating neighbors, prioritize "add node" moves (use unallocated)
- Only generate "swap node" moves if unallocated exhausted
- Result breakdown shows: "Used X of Y unallocated (FREE), Z of W respec"
- Users see immediate value from free allocations

**Technical Notes:**
- Neighbor generation order matters: add-only first, then swaps
- May implement two-phase optimization:
  - Phase 1: Add nodes only (use unallocated points)
  - Phase 2: Swap nodes (use respec points)
- Reference DUAL-BUDGET-FEATURE-SUMMARY.md optimization strategy

**Priority:** Should-have (important for UX)
**Size:** Small (2 story points)

---

#### Story 2.6: Metric Selection and Evaluation
**As a** developer
**I want** to support multiple optimization goals (DPS, EHP, weighted)
**So that** users can optimize for their playstyle

**Acceptance Criteria:**
- Support metric: "Maximize DPS" (total DPS output)
- Support metric: "Maximize EHP" (effective hit points)
- Support metric: "Balanced" (weighted: 60% DPS, 40% EHP)
- Extract correct stats from PoB calculation results
- Normalize metrics for comparison (DPS and EHP different scales)

**Technical Notes:**
- DPS: Extract from Build.calcs.TotalDPS or similar
- EHP: Calculate from Life, ES, resistances, armor
- Weighted: Normalize both to 0-100 scale, apply weights
- Reference FR-2.1 (Metric Selection)

**Priority:** Must-have (MVP blocking)
**Size:** Medium (3 story points)

---

#### Story 2.7: Convergence Detection
**As a** developer
**I want** to detect when optimization has converged
**So that** the algorithm stops when no further improvement is possible

**Acceptance Criteria:**
- Stop when no neighbor improves metric for N consecutive iterations (e.g., N=3)
- Stop when improvement delta <0.1% (diminishing returns)
- Stop when maximum iteration limit reached (e.g., 1000 iterations)
- Log convergence reason: "Converged: no improvement for 3 iterations"

**Technical Notes:**
- Track: iterations_without_improvement counter
- Reset counter when improvement found
- May implement adaptive convergence (longer patience for large improvements)
- Reference FR-4.2 (Convergence Detection)

**Priority:** Must-have (MVP blocking)
**Size:** Small (2 story points)

---

#### Story 2.8: Optimization Progress Tracking
**As a** developer
**I want** to track and report optimization progress
**So that** users see real-time updates (implemented in Epic 3 UI)

**Acceptance Criteria:**
- Track: current iteration number
- Track: best metric value found so far
- Track: current improvement percentage vs baseline
- Track: budget usage (unallocated used, respec used)
- Provide progress callback for UI updates
- Update every 100 iterations (per FR-5.2 consistency fix)

**Technical Notes:**
- Progress callback: `on_progress(iteration, best_metric, improvement_pct, budget_used)`
- Epic 3 UI will consume these progress updates
- Reference FR-5.2 (Real-Time Progress Messages)

**Priority:** Must-have (MVP blocking)
**Size:** Small (2 story points)

---

**Epic 2 Total:** 8 stories (24 story points estimated)

---

## Epic 3: User Experience & Local Reliability

**Goal:** Deliver a complete local web UI for build optimization with robust error handling, progress tracking, and reliable resource management for repeated local use.

**Business Value:** This epic transforms the working algorithm into a polished, usable tool. Combining UX with local reliability ensures the developer can run optimizations repeatedly without crashes, memory leaks, or confusing errors—building confidence before any public release.

**Success Criteria:**
- 95%+ of valid PoB codes parse successfully
- Clear error messages for 100% of unsupported cases
- Users can verify results in PoB GUI (round-trip validation)
- Budget breakdown shows free vs costly changes
- Can run 50+ consecutive optimizations without memory leaks
- All optimizations complete or timeout within 5 minutes

---

### User Stories - Epic 3

#### Story 3.1: Flask Web Server Setup
**As a** user
**I want** to access the optimizer via web browser
**So that** I have a familiar, easy-to-use interface

**Acceptance Criteria:**
- Flask server runs on `localhost:5000`
- Server starts with `python main.py` command
- Server displays: "Optimizer running at http://localhost:5000"
- Opening browser to localhost:5000 shows main page
- Server handles concurrent requests (single user, sequential processing)
- Server shuts down cleanly with Ctrl+C

**Technical Notes:**
- Use Flask framework (lightweight, easy to setup)
- Single HTML page for MVP (no complex routing)
- Static assets served from `/static/` directory
- Reference NFR-9 (Local Startup)

**Priority:** Must-have (MVP blocking)
**Size:** Small (2 story points)

---

#### Story 3.2: PoB Code Input and Validation UI
**As a** user
**I want** to paste my PoB code into a text box
**So that** I can submit my build for optimization

**Acceptance Criteria:**
- Large textarea for PoB code input (supports 50KB+ codes)
- Placeholder text: "Paste your Path of Building code here..."
- Real-time validation: Detect invalid format, show error before submit
- Character count display (e.g., "12,345 characters")
- Reject codes >100KB (per FR-1.1)
- Clear button to reset input

**Technical Notes:**
- Use HTML `<textarea>` with monospace font
- Client-side validation: Check Base64 format, size limit
- Server-side validation: Full parsing and PoE 2 compatibility check
- Reference FR-1.1, FR-1.2 (PoB Code Input)

**Priority:** Must-have (MVP blocking)
**Size:** Small (2 story points)

---

#### Story 3.3: Budget Input UI (Dual Fields)
**As a** user
**I want** to specify my unallocated and respec points
**So that** optimization respects my budget constraints

**Acceptance Criteria:**
- Number input: "Unallocated points" (auto-detected, editable)
- Number input: "Respec points" (user entered, blank = unlimited)
- Helper text explaining each field
- Auto-detection displays: "Detected: 15 (level 85, 98/113 allocated)"
- Quick select buttons: [Free (0 respec)], [Budget (15)], [Unlimited]
- Both fields validate: non-negative integers only

**Technical Notes:**
- Reference FR-2.2 (Budget Constraint - Dual Input)
- Reference DUAL-BUDGET-FEATURE-SUMMARY.md for UI mockup
- Auto-detection: Calculate from parsed PoB build
- User can override auto-detected unallocated if wrong

**Priority:** Must-have (MVP blocking)
**Size:** Medium (3 story points)

---

#### Story 3.4: Metric Selection Dropdown
**As a** user
**I want** to choose my optimization goal
**So that** the tool optimizes for what I care about

**Acceptance Criteria:**
- Dropdown menu with options:
  - "Maximize DPS" (default)
  - "Maximize EHP (survivability)"
  - "Balanced (60% DPS, 40% EHP)"
- Helper text explains each option
- Selection persists if user reruns optimization
- Selected metric passed to optimization algorithm

**Technical Notes:**
- HTML `<select>` element
- Default: "Maximize DPS" (most common use case)
- Reference FR-2.1 (Metric Selection)

**Priority:** Must-have (MVP blocking)
**Size:** Small (1 story point)

---

#### Story 3.5: Optimization Progress Display (Real-Time)
**As a** user
**I want** to see real-time progress during optimization
**So that** I know the system is working and not frozen

**Acceptance Criteria:**
- Progress bar showing percentage complete (estimate)
- Live updates every 100 iterations (per FR-5.2):
  - "Iteration 300/1000"
  - "Best found: +12.3% DPS"
  - "Budget used: 8/15 unallocated, 2/12 respec"
- Time elapsed counter: "Running for 1m 23s"
- Cancel button to stop optimization early
- Progress updates without page refresh (AJAX or Server-Sent Events)

**Technical Notes:**
- Use SSE (Server-Sent Events) for live updates from Flask
- Alternative: AJAX polling every 500ms
- Progress callback from Epic 2 Story 2.8 feeds this display
- Reference FR-5.2 (Real-Time Progress Messages)

**Priority:** Must-have (MVP blocking)
**Size:** Medium (3 story points)

---

#### Story 3.6: Results Display (Before/After Comparison)
**As a** user
**I want** to see clear before/after comparison
**So that** I understand the improvement

**Acceptance Criteria:**
- Side-by-side comparison: "Before" vs "After"
- Key stats displayed: DPS, Life, EHP, resistances
- Percentage improvement highlighted: "+12.3% DPS"
- Budget breakdown:
  - "Unallocated points: Used 15 of 15 (all used)"
  - "Respec points: Used 4 of 12 (8 remaining)"
- Node changes summary: "15 nodes added, 4 nodes removed"
- Visual indicators: Green for improvements, red for regressions

**Technical Notes:**
- Reference FR-5.1, FR-5.3 (Results Display)
- Reference DUAL-BUDGET-FEATURE-SUMMARY.md for budget display format
- Calculate improvement: `(after - before) / before * 100`

**Priority:** Must-have (MVP blocking)
**Size:** Medium (3 story points)

---

#### Story 3.7: Export Optimized PoB Code
**As a** user
**I want** to export the optimized build as a PoB code
**So that** I can import it into Path of Building to verify and implement

**Acceptance Criteria:**
- "Export Optimized Build" button visible after optimization
- Clicking button generates new PoB code with optimized passive tree
- Code copied to clipboard automatically
- Success message: "PoB code copied! Import into Path of Building to verify."
- Original build data preserved (items, skills, config unchanged)
- Only passive tree modified

**Technical Notes:**
- Modify passive node allocations in XML
- Re-encode: XML → zlib compress → Base64
- Reference FR-5.4, FR-5.5 (PoB Code Export & Validation)
- Critical: Round-trip validation (exported code must import successfully)

**Priority:** Must-have (MVP blocking)
**Size:** Medium (3 story points)

---

#### Story 3.8: Error Messages (Structured, Actionable)
**As a** user
**I want** clear error messages when something goes wrong
**So that** I know how to fix the issue

**Acceptance Criteria:**
- Error messages follow structured format (per FR-1.4):
  - **Error Type:** "Unsupported Build"
  - **Reason:** "This build uses unsupported features"
  - **Details:** "Unique jewel: Timeless Jewel detected"
  - **Action:** "Remove unique jewels and try again"
- Errors displayed in red box with icon
- Multiple error types supported:
  - Invalid PoB code format
  - PoE 1 code (not PoE 2)
  - Unsupported build features
  - Calculation timeout
  - Out of budget (shouldn't happen, but defensive)

**Technical Notes:**
- Reference FR-1.3, FR-1.4, FR-1.5 (Error Handling)
- Use consistent error message template across all failures
- Log errors to logs/optimizer.log for debugging

**Priority:** Must-have (MVP blocking)
**Size:** Small (2 story points)

---

#### Story 3.9: Optimization Timeout (5-Minute Hard Stop)
**As a** user
**I want** optimizations to timeout if taking too long
**So that** I'm not stuck waiting indefinitely

**Acceptance Criteria:**
- Hard timeout: 5 minutes (300 seconds) per FR-3.4
- Timeout check every 100 iterations
- If timeout reached:
  - Stop optimization immediately
  - Display best result found so far
  - Show message: "Optimization timed out after 5 minutes. Showing best result found."
  - Partial results still useful (e.g., found +10% improvement in 3 minutes)
- Timeout duration configurable in config file

**Technical Notes:**
- Use Python `time.time()` to track elapsed time
- Check: `if time.time() - start_time > timeout: break`
- Reference FR-3.4 (Calculation Timeout & Error Recovery)
- Graceful degradation: Return partial results, not error

**Priority:** Must-have (reliability requirement)
**Size:** Small (2 story points)

---

#### Story 3.10: Resource Cleanup (Prevent Memory Leaks)
**As a** user
**I want** the server to remain stable after repeated optimizations
**So that** I can use it multiple times without restarting

**Acceptance Criteria:**
- Cleanup after each optimization:
  - Clear Lua state (release memory)
  - Delete temporary variables
  - Reset optimization context
- Memory usage returns to baseline after cleanup
- Can run 50+ consecutive optimizations without memory growth
- Server remains responsive after hours of use

**Technical Notes:**
- Lupa: Explicitly delete Lua runtime or create new one per session
- Python: Use `del` to remove large objects, trigger GC if needed
- Monitor memory with `psutil` or manual testing
- Reference FR-3.3 (Resource Cleanup)

**Priority:** Must-have (reliability requirement)
**Size:** Small (2 story points)

---

#### Story 3.11: File-Based Error Logging
**As a** developer
**I want** detailed error logs saved to disk
**So that** I can debug issues when they occur

**Acceptance Criteria:**
- Logs written to `logs/optimizer.log`
- Log format: `[2025-10-08 14:32:15] ERROR: <message>`
- Log levels: DEBUG, INFO, WARN, ERROR
- Logs include: timestamps, severity, stack traces (for errors)
- Log rotation: New file when >10MB, keep last 5 files
- Sensitive data NOT logged (no full PoB codes)

**Technical Notes:**
- Use Python `logging` module
- Reference FR-6.1 (File-Based Error Logging)
- Configure log level in config file (default: INFO for MVP)
- Rotate with `logging.handlers.RotatingFileHandler`

**Priority:** Should-have (debugging aid)
**Size:** Small (2 story points)

---

#### Story 3.12: Performance Optimization (Final Polish)
**As a** user
**I want** optimizations to complete as fast as possible
**So that** I get results quickly

**Acceptance Criteria:**
- 1000 calculations complete in <1 second (per NFR-1)
- Optimization completes in <2 minutes for typical builds
- Memory usage <100MB during optimization
- Profile bottlenecks and optimize hot paths
- Implement batch calculation optimizations from Epic 1 Story 1.8

**Technical Notes:**
- Profile with Python `cProfile`: `python -m cProfile main.py`
- Optimize: Pre-compile Lua, reuse objects, avoid unnecessary copies
- Reference NFR-1 (Performance), Epic 1 Story 1.8
- Final performance tuning before declaring MVP complete

**Priority:** Should-have (quality improvement)
**Size:** Medium (3 story points)

---

**Epic 3 Total:** 12 stories (30 story points estimated)

---

## Summary

**Total Story Count:** 28 stories (80 story points estimated)

**Epic Breakdown:**
- Epic 1: 8 stories (26 points) - Foundation
- Epic 2: 8 stories (24 points) - Optimization Engine
- Epic 3: 12 stories (30 points) - UX & Reliability

**Delivery Timeline Estimate (2 months):**
- **Weeks 1-3:** Epic 1 (PoB Integration) - Highest risk, foundation work
- **Weeks 4-6:** Epic 2 (Optimization) - Core algorithm implementation
- **Weeks 7-8:** Epic 3 (UX & Reliability) - Polish and local deployment

**Risk Mitigation:**
- Epic 1 addresses highest technical risk (PoB integration)
- Epic 1 Story 1.6 (parity testing) validates core assumption
- Epic 3 includes robust error handling and reliability

**Dependencies:**
- Epic 2 blocked until Epic 1 complete (need working calculations)
- Epic 3 blocked until Epic 2 complete (need working optimization)
- Epic 3 UI design can start during Epic 2 (parallel work opportunity)

---

**Next Steps:**
1. Review epic breakdown for completeness
2. Validate story acceptance criteria are testable
3. Confirm story priorities align with MVP goals
4. Proceed to architecture phase for technical design
