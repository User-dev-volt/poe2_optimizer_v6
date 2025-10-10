# Brainstorming Session Results

**Session Date:** 2025-10-06
**Facilitator:** Business Analyst Mary
**Participant:** Alec

## Executive Summary

**Topic:** AI-Powered Path of Building Optimization System for Path of Exile 2

**Session Goals:** Create a system that uses Path of Building (PoB) to create and optimize builds based on user input. The AI will interact with the actual PoB application to generate new builds or optimize existing ones using items, skill tree adjustments, and all build components. The system takes user questions/requirements and translates them into optimized builds within PoB for Path of Exile 2.

**Techniques Used:** First Principles Thinking, SCAMPER Method, What If Scenarios

**Total Ideas Generated:** 50+ ideas explored across technical architecture, features, algorithms, and implementation strategies

### Key Themes Identified:

**1. Ruthless Scope Discipline is the Competitive Advantage**
The MVP is "The Passive Tree Grinder" - a brutally focused tool that does ONE thing perfectly: optimizes passive skill trees. All complexity (AI chat, item suggestions, skill gems, full build generation) was eliminated. This reduces a 12-month project to 2 months and creates a simpler, more trustworthy product.

**2. Trust is the Actual Product, Not the Algorithm**
Mathematical correctness is necessary but insufficient. Users need transparency (real-time progress messages), verification (PoB codes they can inspect), and honest limitations (clear disclaimers about unsupported build types). The algorithm is just the mechanism - trust is what's being sold.

**3. Validate the Hardest Risk First**
Headless PoB integration is the highest technical risk that blocks all downstream development. Build a throwaway prototype in 2-3 days to validate feasibility before investing weeks in UI, parsers, and algorithms. This is pure risk mitigation.

**4. Budget Constraints are Essential, Not Optional**
Without respec point budgets, the optimizer suggests perfect builds that are financially impossible. Budget constraints transform "here's optimal" into "here's what you can actually afford" - making the tool practical vs. theoretical.

**5. All Stakeholders Want the Same Thing**
Analysis of diverse personas (hardcore min-maxers, skeptical veterans, casual players, PoB developers, solo developer) revealed alignment: everyone wants a focused, honest tool that does one job well. The conflicts are imaginary.

**6. Start Simple, Evolve Intelligently**
MVP uses hill climbing algorithm (simple, fast, explainable). V2 adds simulated annealing layer for better results. Genetic algorithms and constraint solvers are rejected as over-engineering. Each evolution is incremental, not a rewrite.

## Technique Sessions

### Session 1: First Principles Thinking (Creative)

**Duration:** 20 minutes

**Fundamental Truths Identified:**

1. **PoB is a Deterministic Calculator**
   - For given inputs (tree, items, skills, config), outputs (DPS, EHP) are always identical
   - No randomness - pure mathematical equation, not game simulation
   - Makes it perfect for computational optimization

2. **Entirely Data-Reliant**
   - Useless without game's data files
   - Must be perfect digital mirror of game mechanics and numbers
   - Requires accurate, machine-readable database of passive tree, skills, items, monster stats for PoE 2

3. **Standardized Import/Export Format**
   - Sharable PoB code (compressed encoded build representation) is the universal API
   - System must parse this format to read builds and generate it to share builds
   - Community lifeblood for build sharing

4. **Open-Source Logic Engine**
   - Community fork calculation logic publicly available (Lua)
   - Can see exactly how damage, defenses calculated
   - **Critical assumption:** PoE 2 PoB will also be open-source, allowing direct use of calculation engine

5. **Simulation vs Reality Gap**
   - Calculates theoretical maximums under specific conditions
   - Does NOT account for: player skill, boss mechanics preventing attacks, build "feel"
   - High PoB numbers ≠ enjoyable gameplay experience
   - **Critical limitation** system and users must acknowledge

**Five Irreducible Components for Build Optimization (Closed-Loop System):**

1. **Definable State:** Starting point - user's build as parsed PoB code (complete snapshot of tree, gear, skills)

2. **Quantifiable Goal (Objective Function):** "Better" must be a number
   - Examples: Maximize Total DPS, Maximize Effective HP, Reach 75% Fire Resistance
   - Multi-objective: "Maximize Total DPS while keeping Effective HP above 40,000"

3. **Modifiable Variables (The Levers):**
   - Basic: Passive skill tree nodes (allocate/deallocate)
   - Complex: Rare gear stats ("how much life on this helmet?")
   - Advanced: Item swapping, skill gem substitution

4. **Calculation Engine (The Judge):** Headless PoB core
   - After changing variables, sends new state to get updated objective function numbers

5. **Optimization Algorithm (The Strategist):** Intelligent search algorithm
   - Decides which lever to pull next (not random)
   - Explores space of possible changes to improve objective function
   - Range: Simple (Hill Climbing) to Complex (Genetic Algorithms)
   - **Process:** Measure State → Change Variable (strategic) → Re-measure → Compare to Goal → Repeat

**Irreducible User Needs - Converting Vague Goals into Optimal, Actionable Plans:**

1. **Navigating Overwhelming Complexity**
   - Problem: "1,500 passive nodes - which 120 are best for my Frost Axe Berserker?"
   - Need: Navigator through astronomical combination space

2. **Quantifying "Better"**
   - Problem: "New axe has higher phys damage but lower attack speed - is it an upgrade?"
   - Need: Definitive numerical answer to avoid costly mistakes

3. **Saving Time and Effort**
   - Problem: "Spent 3 hours moving tree points, gained only 2% damage"
   - Need: Results of optimization without manual tedium

4. **Clear Path Forward**
   - Problem: "Character dying, damage low - what's the single most effective next step?"
   - Need: Prioritized action list, not just unattainable perfect build

**Core Essence:** Decision support system that converts user intent ("I want more damage") into concrete, trustworthy instructions ("Change these 5 passive points and buy helmet with X stat. Here's the PoB proof.")

**MVP Definition: "The Passive Tree Grinder"**

Philosophy: An MVP that doesn't solve a real problem is useless. The key is violent scope reduction until one thing is done perfectly - solving the single most tedious, mathematically complex, and common optimization task.

**What the MVP Does:**
Given user's existing build, finds mathematically superior passive skill tree allocation without changing anything else.

**What's Excluded from MVP:**
- Natural language processing
- Item suggestions
- Skill gem swaps
- Creating builds from scratch
- Gear, skills treated as fixed constants

**User Experience (Single Webpage, 3 Elements):**

1. **Text Box:** "Paste your Path of Building Code here"
2. **Dropdown Menu:** "What is your primary goal?"
   - Maximize Total DPS
   - Maximize Effective HP (EHP)
   - Maximize Total DPS while maintaining current EHP
3. **Button:** "Optimize My Tree"

**Processing Flow:**

1. **Input:** User's PoB code
2. **Parse:** Decode XML, identify character level, ascendancy, currently allocated passive nodes
3. **Calculate Baseline:** Run current tree through headless PoB calculation engine for starting numbers
4. **Optimize (The Magic):** Core algorithm - "grinding" the tree
   - Has N passive points to spend (e.g., 113)
   - Makes small changes: un-allocate one point, allocate different nearby one
   - Re-runs PoB calculation after each change
   - Keeps changes that improve target metric, discards if not
   - Repeats hundreds/thousands of times, exploring possibilities humans lack patience for
   - Literally grinding optimal pathing one point at a time
5. **Output:** Clear results display
   ```
   Your Original Build:
   Total DPS: 1,250,400
   Effective HP: 35,600

   Optimized Tree Results:
   Total DPS: 1,410,200 (+12.8%)
   Effective HP: 36,100 (+1.4%)

   New Path of Building Code: [generated code]
   ```

**Why This MVP Provides Genuine Value:**

1. **Navigates Overwhelming Complexity:** Computationally searches vast passive tree combinations - finds inefficient paths to notables, identifies better 4-point reallocations
2. **Quantifies "Better":** Hard numerical answer with percentage increase as proof of value
3. **Saves Time and Effort:** KILLER FEATURE - accomplishes in 30 seconds what takes humans hours of tedious manual point-shuffling
4. **Clear Path Forward:** Actionable output - copy new code, paste into PoB, see visual diff of nodes to regret/allocate

**MVP Positioning:** Not a build creator or chatbot - it's a **power tool**. Like an impact wrench: doesn't teach you to build an engine, but does one specific laborious job 100x faster and more efficiently.

**Value Proposition:** For serious min-maxers, squeezing extra 5-10% damage for free by making passive tree more efficient is a game-changer.

**Performance Expectations:**
- Speed is secondary to quality - prefer thorough optimization over fast completion
- Small build optimization: ~1-2 minutes
- Large/complex build optimization: ~1 hour
- Real-time progress reporting: System tells user what it's doing throughout process to maintain engagement

**The Four Foundational Pillars (Absolute Technical Prerequisites):**

These are non-negotiable dependencies that must exist in the PoE 2 ecosystem before development can begin. All are created by GGG or community - not buildable by this project.

**1. The PoE 2 "Path of Building" Application (The Oracle)**

Must have two critical properties:
- **A. Open-Source:** Access to source code (likely GitHub) to extract core logic. Closed-source .exe is a useless black box.
- **B. Isolatable Calculation Logic:** Code calculating DPS, EHP must be separable from GUI. Current PoB uses Lua scripts - expecting similar architecture for PoE 2. If calculation code is tangled with visual elements, project becomes exponentially harder or impossible.

*If doesn't exist:* Project is a non-starter. No verified formulas, no calculation engine.

**2. Standardized Build Data Format (The API)**

PoB's import/export text string is the universal API:
- **A. Defined, Stable Schema:** Structure (likely XML like current PoB) must be known and consistent. Need to know `<Tree>` contains passive nodes, `<Items>` contains gear, etc.
- **B. Reversible Encoding/Compression Method:** Text string is compressed (e.g., zlib) and encoded (e.g., Base64) XML. Must know exact steps to:
  - Decode string into readable data
  - Encode modified data back into valid string that official PoB can import

*If doesn't exist:* No way for users to provide builds or receive optimized results. Closed loop with no entry/exit point.

**3. Machine-Readable Game Data Exports (The Map)**

PoB is built on data extracted from game files. Optimization algorithm needs same raw data:

**A. Complete Passive Skill Tree Graph (MOST CRITICAL for MVP):** File (JSON or Lua table) representing entire passive tree as data structure. For every node:
- Unique ID
- Stats (e.g., +10 Strength, +5% increased Physical Damage)
- Connections to adjacent nodes (graph edges)
- Type (Notable, Keystone, travel node)

**B. Character Starting Data:** Starting passive tree locations for each class, base stats, Ascendancy trees

*If doesn't exist:* Optimization algorithm is blind. Cannot intelligently navigate tree, doesn't know which nodes are valuable or how to path between points.

**4. Headless Execution Environment (The Engine Block)**

Must be able to run isolated PoB calculation logic from own server/application:

**A. Compatible Runtime:** If PoB logic is in Lua (likely), backend must execute Lua code via:
- Direct Lua interpreter on server
- Library like lunatic-python for Python
- Wrapping Lua code in CLI callable as separate process

**B. Interface for Input/Output:** Clear, programmatic way to:
- Feed "build object" (e.g., JSON format) into headless engine
- Receive "results object" back
- Bridge that lets optimization code "ask" PoB engine: "What's the DPS for this tree configuration?"

*If doesn't exist:* Have the logic but no way to "press the button" to run it. Can't automate calculation process, which is the entire point of the grinder.

**Prerequisites Summary Table:**

| What Must Exist | Why It's Absolute Prerequisite for MVP |
|-----------------|----------------------------------------|
| 1. Open-Source PoB for PoE 2 | Trusted, community-verified calculation engine. Without it, numbers are meaningless guesswork. |
| 2. Standardized Import/Export Format | Only way for users to provide input (their build) and receive output (optimized build). |
| 3. Machine-Readable Passive Tree Data | Map/graph for optimization algorithm to make intelligent decisions. Without it, algorithm is blind. |
| 4. Headless PoB Logic Execution | Mechanism allowing programmatic execution of thousands of calculations per second. |

**Strategic Positioning:** Project feasibility is 100% dependent on future work of PoB community developers. Role is NOT to recreate their work, but to be **first and best at building powerful automation layer on top of it** once it becomes available.

### Session 2: SCAMPER Method (Structured)

**Duration:** 25 minutes

#### **S - Substitute: What could you substitute or swap?**

**Substitution 1: Goal Definition Interface**
- **Original:** Simple dropdown menu (Maximize DPS, Maximize EHP, Maximize DPS while maintaining EHP)
- **Substituted with:** AI chat interface where user interacts with AI to articulate what they want
- **Benefit:** Natural language understanding of nuanced goals, more flexible than rigid dropdown options

**Substitution 2: Reference Build Integration**
- **Original:** User only provides their own build
- **Substituted with:** Option to select pre-vetted builds from specialized PoE 2 sites (e.g., Maxroll)
- **How it works:** System pulls 4+ example builds from external sources
- **User can:** Select reference builds as templates or optimization targets
- **Use cases:**
  - "Make my build more like this meta build"
  - "Use this build's tree as starting point"
  - "Show me how far my build is from this reference"
- **Benefit:** Leverages community expertise, gives users proven baselines

**Expanded Goal Options via AI Chat:**
- Maximize DPS
- Maximize HP (Health Pool)
- Maximize MP (Mana Pool)
- Maximize ES (Energy Shield)
- Multi-objective combinations (e.g., "High DPS but tanky enough for endgame")
- Resistance capping priorities
- Attribute thresholds (meeting STR/DEX/INT requirements)
- Quality-of-life stats (movement speed, cast speed)

#### **C - Combine: What could you combine or merge?**

**Combination 1: Budget Constraint System (ESSENTIAL)**
- **What it combines:** Optimization algorithm + Resource limitation awareness
- **Critical for real-world use:** Player's available respec points are finite and valuable
- **System must know:**
  - Total passive skill points available (based on character level)
  - How many points currently allocated
  - How many respec points player has available
  - Cost of each proposed change (number of points to respec)
- **Optimization modes based on budget:**
  - **"Free" optimization:** Only reallocate existing points (no new points needed, just better pathing)
  - **"Limited respec" mode:** "I have 15 respec points - what's the best improvement I can make?"
  - **"Full rebuild" mode:** Unlimited respec assumed (for planning/theorycrafting)
  - **"Incremental growth" mode:** "I just leveled up and got 1 new point - where should it go?"
- **UI enhancement:** Show cost breakdown of recommendations
  - Example: "This optimization requires despeccing 8 points and reallocating 12 points (total cost: 8 respec points)"
- **Value proposition:** Prevents suggesting perfect builds that are financially impossible for player to achieve

**Combination 2: Historical Evolution Tracking**
- **What it combines:** Optimization results + Session history + Progress visualization
- **Feature:** Track how build evolved over multiple optimization sessions
- **Benefits:**
  - See progression: "Build v1 → Build v2 → Build v3"
  - Compare: "How did my DPS change from last week?"
  - Rollback: "I don't like the new tree, show me the previous version"
  - Learning: Users understand which changes had biggest impact

**Combination 3: Crowd-Sourced Optimization Intelligence**
- **What it combines:** Multiple users' optimization results + Pattern recognition + Community consensus
- **Feature:** Aggregate anonymized optimization data across users
- **Insights generated:**
  - "87% of optimized Frost Berserker builds allocate these 5 keystone nodes"
  - "Consensus optimal path from Marauder start to Resolute Technique"
  - Heat maps showing most valuable tree regions for specific build archetypes
- **Trust factor:** Not just one algorithm's opinion - it's what actually works for thousands of real players

**Combination 4: Live Game Balance Integration**
- **What it combines:** Patch note parsing + Automated re-optimization triggers + Change impact analysis
- **Feature:** When PoE 2 releases balance patches, automatically detect affected mechanics
- **Workflow:**
  1. New patch drops (e.g., "Fire damage reduced by 15%")
  2. System parses patch notes, identifies affected stats
  3. Notifies users: "Your build may be affected by the latest patch"
  4. Offers one-click re-optimization: "Would you like to re-optimization based on new balance?"
- **Value:** Keeps builds current without manual monitoring of patch notes

#### **A - Adapt: How could you adapt this for different contexts or users?**

**Primary Target Audience: Endgame Min-Maxers**
- High-level characters (typically level 85-100)
- Deep game knowledge
- Seeking marginal gains (squeezing out that extra 3-5%)
- Willing to invest time in optimization process
- Value numerical precision and proof

**Secondary Use Case: Leveling Players**
- Can still benefit from tree optimization while leveling
- Different constraints: fewer skill points, different gear availability
- May need different optimization priorities (e.g., prioritize survivability until reaching endgame)
- Feature consideration: "Leveling path preview" showing efficient progression route to endgame tree

**Adaptation 1: Difficulty/League Mode Context**
- **Hardcore Mode Adaptation:**
  - System automatically weighs survivability metrics (EHP, max resistances, block/dodge) more heavily
  - Warning system: "This optimization increases DPS by 8% but reduces EHP by 12% - risky for Hardcore"
  - Conservative vs. Aggressive optimization profiles
  - Death = permanent character loss, so builds must be tankier

- **Softcore Mode Adaptation:**
  - More tolerance for glass cannon builds
  - Can push DPS optimization further at expense of defenses
  - Death penalty is experience loss, not character loss

**Adaptation 2: Economy/Wealth Context**
- **League Starter Mode:**
  - Assumes minimal currency/gear
  - Optimizes with "realistic gear" constraints
  - Prioritizes cheap, accessible nodes over those requiring expensive gear synergies
  - "Budget build" optimization

- **Late League/High Currency Mode:**
  - Assumes access to high-tier gear
  - Can recommend nodes that synergize with mirror-tier items
  - Unlocks optimization options requiring specific rare items or uniques

**Adaptation 3: Platform Considerations**
- Primary focus: PC players
- Future consideration: Console UI would need simplified interface (controller-friendly)
- Web-based tool works across platforms

**Adaptation 4: Player Experience Level**
- **For Min-Maxers (Primary):**
  - Show detailed metrics, breakpoints, calculation transparency
  - Advanced options exposed
  - Technical terminology expected

- **For Leveling/Casual Players (Secondary):**
  - Simplified result presentation
  - Focus on "% improvement" rather than raw numbers
  - Optional "explain why" tooltips for recommendations
  - Can still use tool effectively without deep game knowledge

#### **M - Modify: What could you magnify, minify, or otherwise modify?**

**Magnification 1: Optimization Process Transparency**
- **What to magnify:** Visibility into what the algorithm is doing in real-time
- **Implementation:** Simple status messages during processing
- **Example progress statements:**
  - "Allocating points..."
  - "Evaluating damage increase..."
  - "Reallocating down new path..."
  - "Evaluating damage..."
  - "Checking other paths..."
  - "Evaluating damage..."
  - "Increase found..."
  - "Preparing final optimization results..."
- **Value:** Keeps user engaged during 1-60 minute optimization, builds trust by showing work being done
- **Psychology:** Transforms wait time from frustrating to fascinating - user sees the "thinking" process

**Magnification 2: Multi-Objective Optimization - "The Build Equalizer" (ADVANCED/FUTURE FEATURE)**
- **Concept:** Complex dashboard allowing 10+ simultaneous weighted objectives
- **Implementation:** Advanced tab with sliders/input boxes for comprehensive stat weighting
- **Example objectives with weights:**
  - Total DPS: [slider at 100%]
  - Effective HP: [slider at 80%]
  - Spell Suppression Chance: [slider at 60%, target: 100%]
  - Movement Speed: [slider at 40%]
  - Mana Sustain: [slider at 25%]
  - Chaos Resistance: [slider + threshold: "at least 52%"]
  - Cast Speed: [slider at 35%]
  - Life Regeneration: [slider at 20%]
  - Stun Threshold: [slider at 15%]
  - Block Chance: [slider at 50%, target: 75%]

**Pros:**
- **Ultimate Power & Control:** Holy grail for expert theory-crafters
- **Precision Build Definition:** Define build's "feel" with incredible specificity
- **Solves Niche Problems:** "I need exactly 52% chaos resistance and maximum damage after that" - system can solve this
- **Situational Optimization:** Different weights for mapping vs. boss killing

**Cons (Why it's Advanced/Future):**
- **Analysis Paralysis:** Vast majority of players don't know how to weight values against each other
- **Intimidation Factor:** UI unusable for non-experts - "Is 1% more DPS better than 2% more Movement Speed?"
- **Conflicting Goals:** System struggles with contradictory objectives (max damage + max block + max EHP all at 100%)
- **"It Depends" Problem:** Ideal weighting is situational - mapping vs. Uber bosses require different profiles
- **Complexity Creep:** Adds another layer of decision-making

**Implementation Strategy:**
- **MVP:** Simple dropdown (3-5 basic goals)
- **Future "Advanced" Tab:** The Build Equalizer for power users
- **Progressive Disclosure:** Don't overwhelm new users, but give experts the tools they crave

**Do NOT Minify:**
- **Input Requirements:** Keep PoB code + AI chat for goal articulation - context matters
- **Output Detail:** Full metrics, explanations, PoB code - users need comprehensive results for trust and verification

#### **P - Put to Other Uses: What else could this system do?**

**Decision:** Keep focused on core mission - passive tree optimization
- No additional use cases for MVP or near-term roadmap
- Feature creep is a real risk - stay laser-focused on doing one thing perfectly
- Other potential uses (meta analysis, educational tools, challenge builds, APIs) are distractions from primary value proposition

#### **E - Eliminate: What could you remove or simplify?**

**The Leanest Possible MVP - Aggressive Elimination Strategy**

**Elimination 1: AI Chat Interface**
- **VERDICT: ELIMINATE**
- **Rationale:**
  - Natural language interface = massive undertaking (intent parsing, entity recognition, ambiguity handling)
  - High-effort feature solving a problem users don't have
  - Users with PoB codes already understand "DPS" and "EHP"
  - Simple dropdown is faster for user interaction and infinitely simpler to implement
- **Replacement:** Simple HTML form with text box + dropdown
- **Impact:** Cuts months of NLP development work

**Elimination 2: User Accounts & Login**
- **VERDICT: ELIMINATE AGGRESSIVELY**
- **Rationale:** User accounts introduce monumental complexity for zero MVP value:
  - Database management
  - Authentication (sign up, login, logout, password security, resets)
  - Data privacy compliance (GDPR, etc.)
  - Session management
  - Core user need is "optimize this build NOW" - not "save my history"
- **Replacement:** Stateless, anonymous utility - paste code, get result, session forgotten on tab close
- **Impact:** Single-use transactional system removes all user friction and infrastructure complexity

**Elimination 3: Auto-Import from Account API**
- **VERDICT: ELIMINATE API IMPORT for MVP - stick with PoB code**
- **Rationale:** Auto-import is fantastic V2 feature but terrible MVP feature:
  - **External Dependency Risk:** Entire system depends on GGG's API being available, stable, and public for PoE 2
  - **Authentication Hell:** Need to implement OAuth for users to grant secure account access - complex and sensitive
  - **PoB code is the universal standard:** Every target user already knows what it is and how to get it
  - Copy-paste friction is tiny compared to engineering/security overhead of API integration
- **Replacement:** Keep text box: "Paste your Path of Building Code here" - reliable, universal, zero external dependencies
- **Impact:** Removes massive external dependency and auth complexity

**Elimination 4: Support for All Build Types**
- **VERDICT: ELIMINATE - be explicit about what you DON'T support**
- **Rationale:** 80/20 rule applies viciously to PoE builds
  - Simple hit-based attack/spell builds are 1 order of magnitude easier than:
    - Minion builds (Animate Guardian gear, snapshotting, minion scaling tags)
    - Complex aura-stacking or attribute-stacking builds
    - Trigger-based builds with intricate proc loops (e.g., Wardloop)
    - Builds relying on very specific, weird mechanics
  - Supporting everything delays launch by months and results in buggy, unreliable product
  - Reputation damage from giving minion player "terrible" optimization > telling them build isn't supported yet
- **Replacement:** Launch with "boring" majority support:
  - **MVP Supported:** Self-cast, self-attack, simple damage-over-time builds
  - **Clear Disclaimer:** "Optimization is currently most accurate for non-minion, non-trigger builds"
- **Impact:** Focuses on 80% of builds that generate 80% of value, allows faster launch

**The Result: Brutally Focused, Achievable MVP**

**Single Web Page:**
- No other pages, no navigation, no blog
- No login/accounts - open to everyone instantly

**The UI:**
- Title: "PoE 2 Passive Tree Optimizer"
- Large text area: "Paste your PoB Code"
- Simple dropdown: "Optimize For: [Maximize Total DPS] | [Maximize Effective HP]"
- Button: "Optimize"

**The Backend:**
- Accepts only PoB codes for limited set of common build archetypes
- Runs headless PoB engine to perform tree grinding optimization
- No database, stores nothing

**The Output:**
- Clear "Before vs. After" comparison of target stat
- Newly generated, optimized PoB code for user to copy
- Small disclaimer about which build types are best supported

**Project Timeline Impact:**
- **Without eliminations:** Potential 12-month project
- **With aggressive eliminations:** 2-month project
- **Focus proves:** "Can we programmatically generate a mathematically superior passive tree for a user's build?"
- **If YES and users find value:** Solid foundation to build all "nice-to-have" features

#### **R - Reverse/Rearrange: What if you flipped the process or changed the order?**

**Decision:** Keep the standard workflow
- User provides build → System optimizes → User gets result
- This is the most intuitive and direct approach
- No value in reversing or rearranging the core process for MVP
- Standard workflow matches user mental model and expectations

### Session 3: What If Scenarios (Creative)

**Duration:** 15 minutes

#### **Scenario 1: What if PoE 2's Path of Building is NOT open-source?**

**Assessment:** NON-ISSUE - PoE 2's PoB IS open-source
- Community PoB for PoE 2 will be open-source (confirmed expectation based on PoE 1 precedent)
- This prerequisite is reliable and not a project risk
- No Plan B needed - foundation is solid

#### **Scenario 2: What if the optimizer becomes wildly popular (100,000+ concurrent users)?**

**Assessment:** Defer to future planning session
- Scaling challenges (server infrastructure, calculation engine bottlenecks) are real but premature for MVP
- First priority: Prove the concept works and provides value
- Growth problems are good problems to have
- Will address scaling architecture when/if demand materializes

#### **Scenario 3: What if a competitor launches a similar optimizer 2 weeks before you?**

**Assessment:** Not a concern - focus is on building, not competing
- Goal is to create a valuable tool, not to dominate a market
- Multiple optimizers can coexist - different approaches, different strengths
- Being "first" is less important than being good and solving the problem well
- Motivation is intrinsic (building something useful) not extrinsic (beating competitors)

#### **Scenario 4: What if the algorithm finds unintuitive pathing that "feels wrong" to experienced players?**

**Assessment:** Trust the math - if stats are improved, it's valid
- As long as passive tree pathing rules are followed correctly and target stats objectively increase, the optimization is successful
- "Feels wrong" is subjective - numbers don't lie
- Part of the tool's value is discovering non-obvious optimizations that human intuition would miss
- Veteran players may be surprised, but the PoB proof is irrefutable
- Counter-intuitive solutions are often the most valuable discoveries
- System's job is mathematical optimization, not conforming to conventional wisdom

{{technique_sessions}}

## Idea Categorization

### Immediate Opportunities

_Ideas ready to implement now_

**1. Budget Constraint System (ESSENTIAL)**
- Four optimization modes: Free optimization, Limited respec, Full rebuild, Incremental growth
- Shows cost breakdown of recommendations
- Prevents suggesting financially impossible builds
- Critical for real-world usability

**2. Real-Time Progress Transparency**
- Simple status messages during optimization process
- Keeps users engaged during 1-60 minute wait times
- Builds trust by showing the "thinking" process
- Low implementation complexity, high user satisfaction

**3. Hardcore/Softcore Mode Toggle**
- Simple UI element to adjust optimization priorities
- Automatically weighs survivability vs. DPS appropriately
- Addresses fundamentally different risk profiles
- Small code change, significant value

**4. Reference Build Integration (MVP FEATURE - MOVED FROM FUTURE)**
- System maintains curated collection of 4+ reference builds
- Builds sourced from specialized PoE 2 sites (e.g., Maxroll)
- **MVP UI includes:**
  - Dropdown to select from reference builds OR
  - Text box to paste PoB code OR
  - URL input field to import build from external source
- Use cases:
  - "Optimize this reference build for my preferences"
  - "Use reference build as starting template"
  - "Make my build more like this meta build"
- Leverages community expertise, provides proven baselines

{{immediate_opportunities}}

### Future Innovations

_Ideas requiring development/research_

**1. Historical Evolution Tracking**
- Track build progression over multiple optimization sessions
- Compare results across time, rollback capability
- Requires user accounts/database (post-MVP feature)
- Value: Users understand which changes had biggest impact

**2. "Build Equalizer" - Multi-Objective Optimization**
- Advanced tab with 10+ weighted stat sliders for expert theory-crafters
- Complex multi-objective optimization problem solving
- High complexity, serves power-user niche
- Implement after MVP proves core value

**3. Crowd-Sourced Optimization Intelligence**
- Aggregate anonymized optimization data across user base
- Generate consensus insights: "87% of optimized Frost Berserkers allocate these nodes"
- Heat maps showing valuable tree regions by archetype
- Requires significant user base first

**4. Live Game Balance Integration**
- Parse patch notes, auto-detect affected mechanics
- Trigger re-optimization notifications when builds affected by balance changes
- One-click re-optimization based on new game balance
- Complex ongoing maintenance requirement

{{future_innovations}}

### Moonshots

_Ambitious, transformative concepts_

**1. AI Chat Interface for Goal Definition (Eliminated from MVP, possible premium feature)**
- Natural language understanding of nuanced build goals
- Replaces simple dropdown with conversational interface
- Requires NLP expertise, significant development effort
- High wow-factor but questionable ROI vs. simple UI
- Eliminated for MVP to maintain focus and speed

**2. Account API Auto-Import**
- Direct import from player's PoE account (no PoB code needed)
- Eliminates copy-paste friction entirely
- Massive external dependencies: GGG API availability, OAuth implementation
- Great UX but risky foundation with external dependencies
- Better as future enhancement after core value proven

**3. Full Build Generation from Scratch**
- Complete build creation, not just optimization
- User input: "I want to play Frost Berserker" → System outputs complete build
- Exponentially more complex than passive tree grinding
- Fundamentally different product scope
- Long-term vision, not near-term roadmap

{{moonshots}}

### Insights and Learnings

_Key realizations from the session_

**Applied Method: First Principles Analysis**

**Fundamental Truths Discovered:**

1. **The Real Product is Certainty, Not Code**
   - Users don't want software - they want confidence in their decisions
   - The value proposition isn't "we optimize trees" - it's "we eliminate doubt"
   - Every feature must answer: "Does this make the user more certain they're doing the right thing?"

2. **Simplicity is a Competitive Moat**
   - In a complex game like PoE, the tool that's easiest to use wins
   - Every eliminated feature is a victory, not a compromise
   - Complexity is a liability that competitors will inherit if they copy you
   - The 2-month MVP beats the 12-month "feature-complete" product every time

3. **The Algorithm is Worthless Without Trust**
   - Mathematical correctness is necessary but insufficient
   - Users must see the work being done (transparency)
   - Users must verify the results (PoB code they can inspect)
   - Users must understand the limitations (build type disclaimers)
   - Trust is the actual product - the algorithm is just the mechanism

4. **MVP Philosophy Misunderstood = Project Failure**
   - An MVP isn't "the final product with fewer features"
   - An MVP is "the smallest thing that solves a real problem completely"
   - Your MVP doesn't create builds, suggest items, or parse natural language
   - Your MVP does ONE thing: makes passive trees mathematically superior
   - That one thing is actually enough - it solves the "tedious optimization" problem entirely

5. **External Dependencies are Existential Risks**
   - Every external API is a single point of failure
   - PoB open-source status: manageable risk (historically stable)
   - GGG account API: unmanageable risk (outside your control, OAuth complexity)
   - Third-party build sites: moderate risk (can be worked around)
   - Design principle: Core functionality must work with zero external calls

6. **The User's Context is the Constraint**
   - Respec points aren't infinite - budget constraints are mandatory
   - Hardcore vs Softcore isn't preference - it's existential risk profile
   - Level 50 vs Level 95 isn't detail - it's completely different optimization spaces
   - "Make it better" is meaningless - "better" requires resource context

7. **Speed is Strategy, Not Feature**
   - Being first to market isn't about revenue - it's about setting the standard
   - Your data format becomes the standard, your terminology becomes canonical
   - Later entrants must either copy you (validation) or differentiate (fragmentation)
   - But: Being first with broken product is worse than being second with working product

8. **The 80/20 Rule is Actually 95/5 in PoE**
   - Supporting simple builds (self-cast, self-attack) covers 80%+ of users
   - Supporting minions, triggers, snapshotting adds 300% complexity for 15% users
   - Launch for the 80%, iterate to the 95%, maybe never hit 100%
   - Explicitly stating "not supported yet" is better than silently giving wrong answers

**Rebuilt Architecture from First Principles:**

**The Absolute Minimum System:**
1. Input mechanism (PoB code parser)
2. Constraint definition (what are we optimizing FOR, what RESOURCES do we have)
3. Calculation oracle (headless PoB engine)
4. Search algorithm (tree grinding optimizer)
5. Output mechanism (before/after comparison + new PoB code)

**Everything Else is Enhancement, Not Foundation**

---

**Applied Method: Dependency Mapping**

**System Component Dependencies & Critical Paths:**

```
EXTERNAL DEPENDENCIES (Available - Open Source):
│
├─ [AVAILABLE] PoE 2 Path of Building (Open-Source - Confirmed)
│  ├─→ Calculation Engine (Lua scripts) ✓ Available
│  ├─→ Data Files (Passive Tree JSON/Lua) ✓ Available
│  └─→ Build Format Specification (XML schema) ✓ Available
│     │
│     └─→ STATUS: Ready for integration
│        RISK: Low (open-source, community-maintained)
│        ACTION: Begin development immediately
│
└─ [OPTIONAL] Third-Party Build Sites (Maxroll, etc.)
   └─→ Reference Build URLs/Codes
      │
      └─→ BLOCKS: Reference build feature only
         RISK: Low (can manually curate if APIs unavailable)
         MITIGATION: Fallback to manual curation

INTERNAL DEPENDENCIES (Your Control):

MVP CORE (Sequential - Must Complete in Order):
│
├─ 1. PoB Code Parser
│  ├─→ Decode: Base64 → zlib decompress → XML
│  ├─→ Extract: Character level, ascendancy, allocated nodes
│  └─→ BLOCKS: Everything - no input = no system
│     DEPENDENCY: PoB format specification
│     COMPLEXITY: Medium
│
├─ 2. Headless PoB Integration
│  ├─→ Lua runtime environment setup
│  ├─→ Calculation engine wrapper/interface
│  ├─→ Input: Build state object
│  └─→ Output: Stats object (DPS, EHP, etc.)
│     │
│     └─→ BLOCKS: Optimization algorithm, all output
│        DEPENDENCY: PoB calculation engine (Lua)
│        COMPLEXITY: High (most technically challenging)
│
├─ 3. Passive Tree Graph Data Structure
│  ├─→ Parse: Node IDs, stats, connections, types
│  ├─→ Build: Graph representation for pathfinding
│  └─→ BLOCKS: Optimization algorithm navigation
│     DEPENDENCY: PoB data files
│     COMPLEXITY: Medium
│
├─ 4. Optimization Algorithm
│  ├─→ Input: Current tree state, optimization goal, constraints
│  ├─→ Process: Search algorithm (hill climbing/genetic)
│  ├─→ Loop: Modify tree → Calculate via headless PoB → Evaluate
│  └─→ Output: Optimized tree configuration
│     │
│     └─→ BLOCKS: Final output generation
│        DEPENDENCY: Components 1, 2, 3
│        COMPLEXITY: Very High (core intelligence)
│
└─ 5. Output Generator
   ├─→ Format: Before/after comparison
   ├─→ Encode: XML → zlib compress → Base64 (PoB code)
   └─→ BLOCKS: Nothing (final step)
      DEPENDENCY: Components 1-4
      COMPLEXITY: Low

MVP FEATURES (Parallel - Can Develop Alongside Core):
│
├─ Budget Constraint System
│  ├─→ Input: Available respec points
│  ├─→ Logic: Cost calculation per tree change
│  └─→ INTEGRATES WITH: Optimization algorithm (constraint)
│     DEPENDENCY: Optimization algorithm
│     COMPLEXITY: Medium
│     WHEN: After algorithm MVP working
│
├─ Real-Time Progress Messages
│  ├─→ Logging: Optimization algorithm state
│  ├─→ Display: Status updates to UI
│  └─→ INTEGRATES WITH: Optimization algorithm (instrumentation)
│     DEPENDENCY: Optimization algorithm
│     COMPLEXITY: Low
│     WHEN: Can add during algorithm development
│
├─ Reference Build Integration
│  ├─→ Storage: Curated build collection
│  ├─→ UI: Dropdown selector
│  └─→ INTEGRATES WITH: Input mechanism (alternative source)
│     DEPENDENCY: PoB code parser
│     COMPLEXITY: Low
│     WHEN: After parser working
│
└─ Hardcore/Softcore Mode Toggle
   ├─→ UI: Simple checkbox/dropdown
   ├─→ Logic: Adjust optimization weights
   └─→ INTEGRATES WITH: Optimization algorithm (parameter)
      DEPENDENCY: Optimization algorithm
      COMPLEXITY: Low
      WHEN: After algorithm supports multi-objective

CRITICAL PATH (What MUST happen sequentially):
1. Build PoB Code Parser (internal)
2. Integrate Headless PoB Engine (internal - hardest)
3. Load Passive Tree Graph Data (internal)
4. Implement Optimization Algorithm (internal - core value)
5. Build Output Generator (internal)
6. → MVP COMPLETE ←

PARALLEL PATH (What CAN happen simultaneously with step 5-6):
- UI/UX design
- Reference build curation
- Progress messaging system
- Budget constraint logic
- Mode toggle implementation

RISK ANALYSIS BY DEPENDENCY:
│
├─ HIGHEST RISK: Headless PoB Integration
│  └─→ Why: Complex, undocumented, Lua runtime challenges
│     MITIGATION: Prototype early, budget extra time
│
├─ MEDIUM RISK: Optimization Algorithm
│  └─→ Why: Novel implementation, performance unknowns
│     MITIGATION: Start with simple hill climbing, iterate
│
└─ LOW RISK: Everything else
   └─→ Why: Standard web dev, data parsing, UI work
      MITIGATION: Use proven libraries/frameworks
```

**Key Insights from Dependency Analysis:**

1. **Ready to Build:** PoE 2 PoB is open-source and available - development can start immediately
2. **Bottleneck Identified:** Headless PoB integration is the hardest technical challenge
3. **Parallelization Opportunity:** Features can be built while algorithm develops
4. **Risk Concentration:** 80% of technical risk in components 2 & 4 (headless integration + optimization algorithm)
5. **Prototype Priority:** Test headless PoB integration FIRST before building around it
6. **Critical Path is 6 Steps:** No external waiting - pure development execution

---

**Applied Method: Stakeholder Round Table**

**Diverse Perspectives on the PoE 2 Passive Tree Optimizer:**

**Persona 1: The Hardcore Min-Maxer (Target User)**
*"I've spent 2000 hours in PoE. I know my build is good, but I need PROOF it's optimal."*

**What they value:**
- Mathematical rigor and transparency - show me the numbers
- Verification capability - I must be able to import the result into PoB and see it's correct
- Marginal gains - even 3% improvement is worth it at endgame
- Time savings - I'd rather spend time playing than moving tree points around for hours

**What they fear:**
- Black box optimization - don't just give me an answer, show me WHY
- Breaking my build - if you suggest changes that reduce my EHP below safe thresholds, I can't trust you
- Wasting respec points - I have limited currency, don't make me regret using your tool

**Their success criteria:**
- "This tool found 8% more DPS I would never have discovered manually"
- "The before/after comparison is crystal clear and verifiable"
- "I can afford the suggested changes with my available respec points"

---

**Persona 2: The Solo Developer (You)**
*"I want to build something valuable without getting crushed by scope creep."*

**What you value:**
- Shipping something real vs. talking about perfect systems forever
- Learning by doing - tackling the hard technical challenges (Lua integration, optimization algorithms)
- Community contribution - giving back to the PoE community you're part of
- Sustainable scope - 2 months to MVP, not 2 years to "complete"

**What you fear:**
- Analysis paralysis - spending months planning instead of building
- The "feature request death spiral" - users wanting items, gems, full build generation
- Building on shaky foundations - if headless PoB integration is impossible, everything collapses
- Burning out on an overscoped project that never launches

**Your success criteria:**
- "I launched a working MVP in 2 months"
- "Users are actually getting value from it"
- "The technical challenges taught me valuable skills"
- "I can add features incrementally without rewriting everything"

---

**Persona 3: The Skeptical Veteran Player**
*"I've seen a dozen 'revolutionary PoE tools' that died in beta. Why should I trust this?"*

**What they value:**
- Proven track record - show me it works, don't promise vaporware
- Respecting game complexity - PoE is deep, don't oversimplify
- Honest limitations - tell me what you DON'T support upfront
- No bloat - I don't need 50 features, I need ONE thing that works perfectly

**What they fear:**
- Another dead project - investing time learning a tool that gets abandoned
- Bad recommendations - an optimizer that doesn't understand build synergies will give garbage advice
- Hype without substance - "AI-powered" means nothing if the results are wrong
- Privacy/security issues - I'm not giving you my account credentials

**Their success criteria:**
- "This tool has been working reliably for 3+ months"
- "Other experienced players vouch for it"
- "It admits when it can't help (e.g., 'minion builds not yet supported')"
- "It's brutally simple - paste code, get result, done"

---

**Persona 4: The Casual Leveling Player**
*"I'm level 40 and my tree already feels messy. Can this help me?"*

**What they value:**
- Simplicity - I don't understand all the terminology yet
- Clear improvement - just tell me if this makes my character better
- Low commitment - I don't want to spend an hour figuring out your tool
- Safety - I'm scared of breaking my build

**What they fear:**
- Overwhelming complexity - too many options, too much jargon
- Making things worse - what if the "optimized" tree ruins my character?
- Wasting resources - respec points are precious and I don't have many
- Not understanding why - if I don't learn from this, I'm just cargo-culting

**Their success criteria:**
- "I pasted my code, clicked optimize, and got +15% damage - easy!"
- "The tool explained the changes in simple terms"
- "It only asked me to respec 5 points, which I can afford"
- "I feel smarter about tree building after using it"

---

**Persona 5: The Path of Building Community Developer**
*"Your tool sits on top of our work. We're allies, not competitors."*

**What they value:**
- Attribution and respect - acknowledge that PoB makes this possible
- Bug reports upstream - if you find issues in our calculations, tell us
- Open collaboration - maybe we can integrate your optimizer into PoB someday
- Not fragmenting the ecosystem - don't create competing standards

**What they fear:**
- Misrepresentation - users thinking your tool IS Path of Building
- Blame for your bugs - "the optimizer gave wrong numbers" when it's your parsing error
- Ecosystem fragmentation - multiple incompatible build formats
- Lack of understanding - using PoB code without understanding the mechanics

**Their success criteria:**
- "This tool drives more users to understand and use PoB properly"
- "They're citing PoB as the calculation source and contributing back"
- "They're not breaking or misusing the PoB format"
- "We're collaborating on improving both tools"

---

**Synthesis: Balanced Solution Addressing All Stakeholders**

**For Min-Maxers:** Transparency, verification, budget constraints, mathematical proof
**For You (Developer):** Ruthless scope discipline, 2-month MVP, extensible architecture
**For Skeptics:** Honest limitations, brutally simple UX, no hype, proven reliability
**For Casuals:** Clear explanations, safe defaults, "it just works" experience
**For PoB Developers:** Attribution, bug reporting upstream, format compatibility, collaboration

**The Alignment:**
All stakeholders actually want the SAME thing: **A tool that does one thing correctly and honestly communicates its limitations.** The conflicts are imaginary - shipping a focused, transparent, well-scoped MVP satisfies everyone.

---

**Applied Method: Tree of Thoughts**

**Exploring Multiple Reasoning Paths for the Optimization Algorithm**

**Path 1: Hill Climbing (Greedy Local Search)**

**Approach:**
- Start with user's current tree
- For each iteration:
  - Try all possible single-node changes (allocate/deallocate)
  - Calculate impact via headless PoB for each
  - Keep the change that produces best improvement
  - Repeat until no single change improves the objective

**Strengths:**
- Simple to implement and debug
- Fast per-iteration (only evaluates neighbors)
- Guaranteed to find a local optimum
- Predictable behavior - easy to explain to users

**Weaknesses:**
- Gets stuck in local optima (can't escape "good enough" solutions)
- May miss the global optimum if it requires temporary regression
- No exploration of distant tree regions
- Path-dependent - result depends on starting point

**Best for:** MVP launch - proves concept works, gets results quickly

---

**Path 2: Simulated Annealing (Probabilistic Search)**

**Approach:**
- Start with user's current tree
- At each step:
  - Randomly select a tree modification
  - Calculate new objective value
  - Always accept improvements
  - Sometimes accept worse solutions (probability decreases over time)
- "Temperature" parameter controls exploration vs. exploitation

**Strengths:**
- Can escape local optima via probabilistic jumps
- Better chance of finding global optimum
- Still relatively simple to implement
- Well-studied algorithm with proven convergence properties

**Weaknesses:**
- Requires careful tuning of temperature schedule
- Slower than hill climbing (more wasted evaluations)
- Stochastic - different runs produce different results
- Harder to explain to users ("why did it accept worse solutions?")

**Best for:** V2 improvement - better results for users willing to wait longer

---

**Path 3: Genetic Algorithm (Population-Based Search)**

**Approach:**
- Maintain population of candidate trees
- Each generation:
  - Evaluate fitness (objective value) for all candidates
  - Select best performers as parents
  - Create offspring via crossover (combine portions of parent trees)
  - Apply random mutations
  - Repeat for N generations

**Strengths:**
- Explores solution space broadly (multiple candidates in parallel)
- Can discover non-obvious combinations
- Naturally handles multi-objective optimization
- Impressive to users ("AI evolving your build")

**Weaknesses:**
- Much more complex to implement correctly
- Requires many more PoB evaluations (population × generations)
- Challenging tree crossover - how do you "merge" two passive trees meaningfully?
- Can be slower than other methods
- Risk of premature convergence if diversity isn't maintained

**Best for:** Advanced feature - when simple algorithms plateau and users demand better

---

**Path 4: Constraint-Based Branch and Bound**

**Approach:**
- Model tree optimization as constraint satisfaction problem
- Use formal constraints:
  - Must stay connected to starting point
  - Budget constraint on respec points
  - Minimum/maximum values for stats
- Systematically explore search space, pruning branches that can't improve

**Strengths:**
- Guaranteed optimal solution within constraints
- Elegant handling of budget constraints
- Can prove no better solution exists
- Mathematical rigor appeals to theory-crafters

**Weaknesses:**
- Exponential worst-case complexity
- Requires sophisticated constraint solver
- May be too slow for large trees with many points
- Implementation complexity is high

**Best for:** Niche use case - "provably optimal" mode for hardcore users

---

**Path 5: Hybrid Approach (Multi-Stage Pipeline)**

**Approach:**
- Stage 1: Quick hill climbing to find local optimum (30 seconds)
- Stage 2: Simulated annealing from that base to explore nearby (2 minutes)
- Stage 3: Final hill climbing refinement (30 seconds)
- Total: 3-minute optimization delivering best of both worlds

**Strengths:**
- Balances speed and quality
- Hill climbing gives fast baseline, annealing improves it
- Predictable time budget
- Can show incremental progress to user ("Found 5% improvement, searching for more...")

**Weaknesses:**
- More complex implementation (three algorithms)
- Requires coordination between stages
- Parameter tuning for each stage
- Risk of over-engineering

**Best for:** Post-MVP refinement - once core is proven, optimize the optimizer

---

**Evaluation: Which Path to Take?**

**For MVP (Priority 1):**
**Winner: Path 1 - Hill Climbing**
- Simplest implementation
- Fast enough for user tolerance (1-2 minutes)
- Predictable, explainable behavior
- Gets 80% of the value with 20% of the complexity
- Easy to test and debug
- Proves core concept: "Can we programmatically improve a tree?"

**For V2 (Future Enhancement):**
**Winner: Path 5 - Hybrid Approach**
- Once hill climbing MVP is stable, add simulated annealing layer
- Incremental improvement doesn't require rewrite
- Gives better results without sacrificing simplicity narrative

**Not Recommended:**
- Path 3 (Genetic Algorithm): Complexity doesn't justify improvement for this problem
- Path 4 (Branch and Bound): Too slow for real-time use with large trees

**Selected Path: Start with Hill Climbing, evolve to Hybrid**

---

**Applied Method: Reverse Engineering**

**Working Backwards from Desired Outcome to Implementation Path**

**The Desired End State (User Success Moment):**

A hardcore PoE 2 player opens your website at 2 AM during league launch. They paste their level 87 Frost Monk build code, select "Maximize DPS," click "Optimize," wait 90 seconds while watching progress messages, and receive:

```
OPTIMIZATION COMPLETE

Your Original Build:
- Total DPS: 847,300
- Effective HP: 42,100

Optimized Tree:
- Total DPS: 931,450 (+9.9%)
- Effective HP: 42,850 (+1.8%)

Changes Required:
- Deallocate 6 nodes
- Reallocate 8 nodes
- Respec Cost: 6 points

[New PoB Code - Ready to Copy]
```

They copy the code, paste into PoB, see the visual diff showing exactly which nodes changed, verify the math checks out, spend their 6 respec points in-game, and their build is measurably stronger. They bookmark your site and tell their guild.

**That's success. Now let's reverse engineer how to get there.**

---

**Step 7 (Final): User Receives Verified, Actionable Result**

**What must be true:**
- PoB code is validly formatted (can be imported)
- Stats are accurate (match what PoB calculates)
- Changes are affordable (within respec budget)
- User trusts the result (transparency throughout)

**Prerequisites:**
- Output generator correctly encodes XML → zlib → Base64
- Before/after comparison is clear and honest
- Respec cost calculation is accurate

**To get here, we need Step 6...**

---

**Step 6: System Generates Optimized Build Output**

**What must be true:**
- Optimization algorithm has completed and found improvements
- Final tree state is known and valid
- All stats have been calculated via PoB engine
- Tree maintains required connectivity

**Prerequisites:**
- Output generator can format results
- Can encode tree back into PoB format
- Can calculate respec costs

**To get here, we need Step 5...**

---

**Step 5: Optimization Algorithm Runs Successfully**

**What must be true:**
- Algorithm can iterate through tree modifications
- Each modification triggers PoB recalculation
- Algorithm evaluates which changes improve objective
- Process continues until convergence (no more improvements)
- Real-time progress is communicated to user

**Prerequisites:**
- Hill climbing algorithm implemented
- Can modify tree state (allocate/deallocate nodes)
- Can call headless PoB engine for each state
- Can compare results to find improvements
- Has stopping criteria

**To get here, we need Step 4...**

---

**Step 4: Headless PoB Engine Responds to Queries**

**What must be true:**
- PoB calculation engine is isolated and callable
- Can accept build state as input
- Returns stats (DPS, EHP, etc.) as output
- Executes fast enough for iteration (< 1 second per call)
- Lua runtime is stable

**Prerequisites:**
- Lua interpreter running on server
- PoB Lua scripts loaded and functional
- Interface layer translates between your code and Lua
- Build state can be serialized for input
- Results can be deserialized from output

**To get here, we need Step 3...**

---

**Step 3: Passive Tree Graph is Loaded and Navigable**

**What must be true:**
- Tree data parsed from PoB files
- Graph structure built (nodes + connections)
- Can query: "What nodes are adjacent to X?"
- Can validate: "Is this allocation valid?"
- Knows stats for each node

**Prerequisites:**
- PoB data files accessible
- Parser extracts node IDs, stats, connections
- Graph data structure implemented
- Pathfinding/adjacency logic works

**To get here, we need Step 2...**

---

**Step 2: User's Build is Parsed and Understood**

**What must be true:**
- PoB code successfully decoded
- XML parsed and validated
- Character data extracted (level, class, ascendancy)
- Current passive tree allocation extracted
- Build is compatible (not unsupported type like minions)

**Prerequisites:**
- Base64 decoder
- Zlib decompressor
- XML parser
- Validation logic for supported build types
- Error handling for invalid/unsupported builds

**To get here, we need Step 1...**

---

**Step 1: User Submits Build via Web Interface**

**What must be true:**
- Website is live and accessible
- UI is simple and clear
- User can paste PoB code OR select reference build OR paste URL
- Optimization goal dropdown works
- Submit button triggers backend process
- User receives immediate feedback ("Processing...")

**Prerequisites:**
- Web server running
- Frontend UI built (HTML/CSS/JS)
- Form validation works
- Backend API endpoint ready to receive requests
- Reference builds curated and stored

**To get here, we need Step 0...**

---

**Step 0: Development Environment and Foundation Ready**

**What must be true:**
- PoE 2 PoB is available (✓ Already true)
- Development environment set up
- Programming language selected (likely Python or Node.js)
- Version control initialized (Git)
- Basic project structure created
- Dependencies identified

**This is where we start.**

---

**The Complete Reverse-Engineered Path (Start → Finish):**

```
TODAY → Step 0: Set up dev environment
     ↓
     → Step 1: Build simple web UI (form + button)
     ↓
     → Step 2: Implement PoB code parser (decode → XML → extract)
     ↓
     → Step 3: Parse passive tree data into graph structure
     ↓
     → Step 4: Integrate headless PoB engine (HARDEST STEP)
     ↓
     → Step 5: Implement hill climbing optimization algorithm
     ↓
     → Step 6: Build output generator (stats + new PoB code)
     ↓
     → Step 7: User tests, verifies, shares with guild
     ↓
LAUNCH → User success moment achieved
```

**Critical Insight from Reverse Engineering:**

The path is LINEAR and SEQUENTIAL. You cannot skip steps. Step 4 (headless PoB) blocks everything downstream. That's your critical path bottleneck - **prototype it first to validate feasibility before building Steps 1-3.**

**Recommended Approach:**
1. Build a **throwaway prototype** of Step 4 (headless PoB integration) FIRST
2. If it works → proceed with confidence through Steps 0-3
3. If it's impossible → pivot entire project concept before investing time
4. Once Step 4 is proven possible, build Steps 1-7 in order

**Risk Mitigation:**
Don't build the house before confirming the foundation can support it. Validate the hardest technical challenge (Lua integration) before investing in everything else.

{{insights_learnings}}

## Action Planning

### Top 3 Priority Ideas

#### #1 Priority: Prototype Headless PoB Integration (Risk Validation)

**Rationale:**
This is the highest-risk technical component that blocks all downstream development. If headless PoB integration is impossible or too slow, the entire project concept fails. Building a throwaway prototype first validates feasibility before investing weeks in UI, parsers, and algorithms that sit on a broken foundation. This is pure risk mitigation - spend 2-3 days to potentially save 2 months of wasted effort.

**Next steps:**
1. Clone PoE 2 PoB repository from GitHub
2. Study the Lua calculation engine structure and identify entry points
3. Set up local Lua runtime environment (install Lua interpreter)
4. Create minimal test harness: hardcode a simple build state
5. Attempt to call PoB calculation engine with test data
6. Measure: Does it return correct DPS/EHP? How fast (<1 second = success)?
7. Document findings: What works, what doesn't, what's needed for production
8. Make GO/NO-GO decision on project viability

**Resources needed:**
- PoE 2 PoB source code (available on GitHub)
- Lua interpreter (free, open-source)
- Time: 2-3 days of focused experimentation
- Documentation: PoB community wiki, Lua docs
- Fallback: If stuck, reach out to PoB community for guidance

**Timeline:**
- **Days 1-2:** Environment setup, code exploration, first integration attempt
- **Day 3:** Testing, performance measurement, documentation
- **Decision Point:** GO = proceed to Step 0-7, NO-GO = pivot project concept

---

#### #2 Priority: Build MVP "Passive Tree Grinder" (Steps 0-7 in Order)

**Rationale:**
Once headless PoB integration is validated (Priority #1), execute the complete reverse-engineered implementation path. This is the 2-month sprint to a working, valuable product. Each step builds on the previous, so they must be done sequentially. The MVP proves the core concept: "Can we programmatically generate a mathematically superior passive tree?" Everything else is enhancement.

**Next steps:**
- **Step 0:** Set up development environment, select tech stack (Python/Node.js), initialize Git repo
- **Step 1:** Build simple web UI (single page: text box, dropdown, button)
- **Step 2:** Implement PoB code parser (Base64 → zlib → XML → extract data)
- **Step 3:** Parse passive tree data into graph structure (nodes, connections, stats)
- **Step 4:** Integrate headless PoB engine (production-ready version of prototype from Priority #1)
- **Step 5:** Implement hill climbing optimization algorithm
- **Step 6:** Build output generator (format results, encode new PoB code)
- **Step 7:** Deploy, test with real users, gather feedback

**Resources needed:**
- Development environment (IDE, Git, web server)
- Tech stack libraries (web framework, XML parser, compression libs)
- PoE 2 PoB data files and calculation engine
- Hosting/deployment platform (consider free tier: Vercel, Railway, Render)
- Time: 2 months focused development
- Testing: PoE 2 builds from friends/community for validation

**Timeline:**
- **Week 1:** Steps 0-1 (environment + basic UI)
- **Week 2-3:** Step 2-3 (parsing PoB codes + tree data)
- **Week 4-5:** Step 4 (headless PoB integration - hardest)
- **Week 6-7:** Step 5 (optimization algorithm implementation)
- **Week 8:** Step 6-7 (output generation, deployment, testing)
- **Target Launch:** 2 months from start

---

#### #3 Priority: Implement Budget Constraint System (Essential MVP Feature)

**Rationale:**
Without budget constraints, the optimizer can suggest perfect builds that cost 50+ respec points - financially impossible for most players. This feature is what makes the tool practical vs. theoretical. It transforms "here's the mathematically optimal tree" into "here's the best improvement you can actually afford." This is essential for real-world usability and user trust. Must be included in MVP, not deferred to V2.

**Next steps:**
1. Add UI input field: "How many respec points do you have available?" (default: unlimited)
2. Implement respec cost calculator:
   - Count nodes being deallocated = respec cost
   - Compare to user's budget
3. Modify optimization algorithm to respect constraint:
   - Track cumulative respec cost during tree modifications
   - Reject changes that exceed budget
   - Prioritize high-impact, low-cost changes first
4. Implement four optimization modes:
   - **Free optimization:** Only reallocate existing points (0 respec cost)
   - **Limited respec:** User specifies available respec points
   - **Full rebuild:** Unlimited budget (theorycrafting mode)
   - **Incremental growth:** Player just leveled up, has 1 new point to spend
5. Display cost breakdown in results: "Deallocate 6 nodes, reallocate 8 nodes = 6 respec points required"
6. Add warning if optimizations aren't possible within budget: "No improvements found within your 3 respec point budget. Try increasing budget or use 'Free optimization' mode."

**Resources needed:**
- Integration with Step 5 (optimization algorithm) - must be built alongside
- Simple cost calculation logic
- UI updates for budget input and cost display
- Testing with various budget constraints to ensure algorithm respects limits

**Timeline:**
- **During Week 6-7:** Build alongside optimization algorithm (Priority #2, Step 5)
- **Cannot be added later:** Core algorithm must know about constraints from the start
- **Testing:** Week 8 during overall system testing

---

**Execution Order:**
1. **First (Days 1-3):** Priority #1 - Validate technical feasibility
2. **Then (Months 1-2):** Priority #2 - Build complete MVP (Steps 0-7)
3. **Integrated (Week 6-7):** Priority #3 - Add budget constraints during algorithm development

## Reflection and Follow-up

### What Worked Well

**Reverse Engineering Technique:**
The reverse engineering approach was highly productive - working backwards from the desired end state (user success moment) to implementation steps provided exceptional clarity. It revealed the complete linear path from today to launch and identified the critical bottleneck (headless PoB integration) that must be prototyped first. This technique transformed abstract ideas into a concrete, actionable roadmap with clear decision points.

**Multiple Perspectives (Stakeholder Round Table):**
Examining the project through diverse stakeholder lenses was fruitful. Analyzing needs and fears of different personas (hardcore min-maxers, skeptical veterans, casual players, PoB developers, and you as developer) revealed that all stakeholders actually want the same thing: a focused, honest tool that does one job well. This validation confirmed the MVP approach and eliminated imagined conflicts.

**First Principles Thinking:**
Stripping away assumptions to fundamental truths early in the session established a solid foundation. Identifying the five irreducible components (definable state, quantifiable goal, modifiable variables, calculation engine, optimization algorithm) and the core user need (decision support) kept the entire session grounded in reality rather than speculation.

**SCAMPER Method for Systematic Exploration:**
The structured SCAMPER lens (Substitute, Combine, Adapt, Modify, Put to other uses, Eliminate, Reverse) systematically explored possibilities while maintaining ruthless focus. The "Eliminate" section was particularly valuable - cutting AI chat, user accounts, API imports, and complex build support reduced a 12-month project to 2 months.

### Areas for Further Exploration

**Technical Deep Dives:**
- Lua runtime integration patterns and best practices
- Specific optimization algorithm implementations (hill climbing variants, convergence criteria)
- PoB data file formats and parsing strategies
- Performance benchmarking: how many tree evaluations per second are achievable?

**User Experience Refinement:**
- Optimal progress messaging cadence and content during optimization
- How to explain "counter-intuitive" optimizations that algorithms discover
- Error handling and user feedback for unsupported build types
- Visual design for trust and credibility

**Post-MVP Feature Prioritization:**
- Which V2 features provide the most value: reference builds, hardcore/softcore modes, historical tracking, or multi-objective optimization?
- How to gather and incorporate user feedback after launch
- Monetization strategy (if any): donations, premium features, or keep it free?

**Community Collaboration:**
- How to engage with PoB community developers productively
- Contributing improvements/bug fixes back to PoB project
- Building trust with skeptical PoE veteran community

### Recommended Follow-up Techniques

**For Technical Implementation Planning:**
- **Failure Mode Analysis** - Systematically explore how each component could fail to build robust error handling
- **Pre-mortem Analysis** - Imagine project failure scenarios to identify risks before they materialize

**For Algorithm Development:**
- **Tree of Thoughts** (already used effectively) - Continue exploring optimization algorithm variations
- **Scientific Method/Reproducibility Check** - Ensure optimization results are consistent and verifiable

**For Launch Planning:**
- **Challenge from Critical Perspective** - Stress-test the MVP before launch by playing devil's advocate
- **Hindsight Reflection** - After MVP launches, conduct retrospective to extract lessons learned

### Questions That Emerged

**Technical Questions:**
1. What's the actual performance of the PoB calculation engine when called headlessly? (Prototype will answer this)
2. How large is the passive tree search space? How many node combinations exist?
3. Can hill climbing converge in reasonable time (<2 minutes) for level 90+ characters?
4. What's the optimal balance between speed and quality in the optimization algorithm?

**Product Questions:**
1. Should the MVP support all PoE 2 classes/ascendancies from day 1, or launch with subset?
2. How do you communicate "this build type isn't supported yet" without frustrating users?
3. What disclaimer/attribution is needed for PoB community developers?
4. Is there demand for this tool, or are you building in a vacuum? (Validate with community polls/feedback)

**Strategic Questions:**
1. Open-source the optimizer itself, or keep it proprietary while using open-source PoB?
2. How to prevent the tool from being misused or causing harm to the PoE economy?
3. Should you build a community around the tool (Discord, Reddit) or keep it simple?

### Next Session Planning

**Suggested Topics:**

1. **Technical Architecture Deep Dive** (After Priority #1 prototype succeeds)
   - Review prototype findings
   - Design production architecture for headless PoB integration
   - Select specific tech stack and libraries
   - Plan testing and validation strategy

2. **Algorithm Implementation Strategy** (Before Priority #2, Step 5)
   - Deep dive into hill climbing implementation details
   - Define convergence criteria and stopping conditions
   - Design test cases for algorithm validation
   - Plan performance benchmarking approach

3. **Launch and Marketing Strategy** (After MVP built, before deployment)
   - Where to announce the tool (PoE subreddit, forums, Discord)
   - How to gather initial user feedback
   - Iteration plan based on real user data
   - V2 feature prioritization based on requests

**Recommended Timeframe:**
- **Session 2:** 1 week after Priority #1 prototype complete (assuming GO decision)
- **Session 3:** End of Week 5 (after headless integration done, before algorithm work)
- **Session 4:** End of Week 8 (MVP built, planning launch)

**Preparation Needed:**
- **For Session 2:** Prototype findings documented, technical questions answered, architecture options researched
- **For Session 3:** Headless PoB integration complete and tested, algorithm research completed
- **For Session 4:** MVP fully functional, initial test users recruited, feedback collected

---

_Session facilitated using the BMAD CIS brainstorming framework_
