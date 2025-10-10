# Product Brief: PoE 2 Passive Tree Optimizer

**Date:** 2025-10-08
**Author:** Alec
**Status:** Draft for PM Review

---

## Executive Summary

The **PoE 2 Passive Tree Optimizer** (internally "The Passive Tree Grinder") is a focused web-based optimization tool that automatically finds mathematically superior passive skill tree configurations for Path of Exile 2 builds. By leveraging Path of Building's proven calculation engine through headless automation, the tool solves the single most tedious and complex optimization challenge players face: efficiently allocating 100+ passive points across a 1,500-node skill tree.

**Core Value Proposition:** Transform 3+ hours of manual passive tree experimentation into a 30-second automated optimization that delivers verifiable 5-15% performance improvements with mathematical proof.

**Target Market:** Endgame Path of Exile 2 players (level 85-100) seeking competitive advantages through min-maxed character builds, with secondary appeal to leveling players optimizing growth paths.

**Strategic Differentiation:** Ruthless scope discipline. Unlike existing tools that attempt comprehensive build generation, we do ONE thing perfectly: passive tree optimization. This 2-month MVP approach beats 12-month "complete solutions" through surgical focus, transparent mathematics, and honest limitation disclosure.

**Technical Foundation:** Python backend using Lupa library to execute Path of Building's official Lua calculation engine in headless mode, achieving 150-500ms throughput for 1000+ calculations per optimization session with 100% accuracy guarantee.

---

## Problem Statement

### The Core Problem: Decision Paralysis in Overwhelming Complexity

Path of Exile 2 players face a mathematically intractable optimization problem: **determining the optimal allocation of ~120 passive skill points across a tree of 1,500+ interconnected nodes**, each offering different statistical bonuses with complex multiplicative interactions.

**Quantified Pain Points:**

1. **Time Sink:** Players spend 3-5 hours manually experimenting with passive tree configurations, testing combinations one-by-one in Path of Building (PoB), often gaining only 2-5% performance improvement for massive effort investment.

2. **Suboptimal Builds:** Even experienced players miss superior configurations. The combinatorial explosion of possible allocations (1,500 choose 120 ≈ 10^250 possibilities) makes exhaustive human evaluation impossible. Players routinely leave 8-15% performance gains undiscovered.

3. **Inefficient Pathing:** Players allocate points to reach powerful keystones but use suboptimal paths, wasting 5-10 passive points on weak travel nodes when better routes exist. Identifying these inefficiencies manually requires tedious point-by-point comparison.

4. **Resource Waste:** Respec points cost in-game currency. Players who discover better trees after investing respec points have wasted valuable resources (15-25 respec points = 2-4 hours of farming).

5. **Build Abandonment:** Players give up on promising build concepts because they can't figure out "why the damage is low" or "why I keep dying" when the actual issue is passive tree inefficiency that optimization could solve.

**Why Existing Solutions Fall Short:**

- **Path of Building (Manual Tool):** Provides calculation accuracy but requires human decision-making. Players must manually test every possible configuration—the very problem we're solving.

- **Build Guides (Static Solutions):** Community build guides show final trees but not the reasoning, don't account for player's specific gear, and become outdated with balance patches.

- **"Build Creator" Tools:** Overly ambitious tools that try to generate complete builds from scratch face exponential complexity, deliver poor results, and lack trust due to black-box recommendations.

**Market Opportunity:** Path of Exile 2 players consistently request better optimization tools throughout the game's lifecycle. The evergreen nature of build optimization creates sustained demand regardless of league timing.

**Evidence:** Community discussions on r/pathofexile consistently request "better tree optimization tools" with high engagement (500+ upvotes), and Path of Building receives 100K+ downloads per league launch. Clear unmet demand exists.

---

## Proposed Solution

### "The Passive Tree Grinder" - Surgical Optimization Tool

**Core Concept:** A brutally focused web application that accepts a player's current Path of Building code and automatically discovers a mathematically superior passive tree allocation—without changing gear, skills, or any other build aspects.

**How It Works (User Experience):**

1. **Input:** Player pastes their Path of Building code into a text box
2. **Goal Selection:** Player chooses optimization objective from dropdown:
   - Maximize Total DPS
   - Maximize Effective HP (EHP)
   - Maximize DPS while maintaining current EHP
   - Advanced: Multi-objective with budget constraints
3. **Processing:** System runs headless PoB calculation engine, testing thousands of tree variations using intelligent search algorithms (hill climbing with simulated annealing for v2)
4. **Output:** Player receives:
   - **Before/After Comparison:** Clear numerical proof of improvement (e.g., "DPS: 1,250,400 → 1,410,200 (+12.8%)")
   - **New PoB Code:** Copy-paste ready code to import into Path of Building
   - **Cost Breakdown:** "Requires despeccing 8 points and reallocating 12 points (cost: 8 respec points)"
   - **Verification:** Player imports code into PoB and sees exact node changes highlighted

**Key Differentiators:**

1. **Scope Discipline = Competitive Advantage**
   - We do ONE thing (passive trees) perfectly, not ten things poorly
   - Complexity reduction: No AI chat, no item suggestions, no full build generation
   - 2-month development vs. competitors' 12+ month vaporware

2. **Trust Through Transparency**
   - Uses official Path of Building calculation engine (100% accuracy guarantee)
   - Real-time progress messages show what the algorithm is doing
   - Player can verify every recommendation in Path of Building themselves
   - Honest limitation disclosure ("minion builds not yet supported")

3. **Practical Resource Awareness**
   - Budget constraint system: "I have 15 respec points available"
   - Optimization modes: Free (zero respec cost), Limited, Full rebuild, Incremental growth
   - Prevents suggesting perfect builds that are financially impossible

4. **Mathematical Proof, Not Promises**
   - Hard numbers with percentage improvements
   - Reproducible results (same input → same output)
   - No hype, no "AI magic"—just computational exhaustiveness humans lack patience for

**Why This Succeeds Where Others Haven't:**

- **Focused Value:** Solves the hardest, most tedious optimization subtask completely
- **Verified Accuracy:** Leverages battle-tested PoB calculation code, not custom formulas
- **Speed to Market:** 2-month MVP timeline captures early-league demand window
- **Honest Positioning:** "Power tool for experts" not "build everything for everyone"

**User Success Moment:** Player discovers an 8% DPS increase by reallocating just 6 passive points—improvement they would never have found manually in 10 hours of experimentation. They bookmark the tool and recommend it to their guild.

---

## Target Users

### Primary User Segment: Endgame Min-Maxers

**Demographics:**
- **Player Level:** 85-100 (endgame content)
- **Experience:** 500-5000+ hours in PoE franchise, deep game knowledge
- **Engagement:** Active during league launches (play 20-60 hours/week first month)
- **Mindset:** Competitive, optimization-focused, value numerical precision

**Current Behavior:**
- Spend 3-5 hours manually testing passive tree variations in Path of Building
- Theory-craft builds using spreadsheets and community tools
- Watch streamers and study build guides looking for optimization strategies
- Participate in PoE subreddit, Discord channels, and build-sharing communities

**Pain Points:**
- **Time Constraints:** Want optimization results faster to spend more time playing
- **Incomplete Exploration:** Know they're leaving performance on the table but can't test everything
- **Respec Anxiety:** Fear wasting valuable respec points on suboptimal experiments
- **Build Comparison:** Struggle to determine if alternate tree configurations are better

**Goals:**
- Squeeze every possible percentage point of performance from their build
- Reach endgame boss viability (high DPS + sufficient survivability)
- Achieve leaderboard rankings or complete challenge content
- Gain competitive advantage in trade league economy through efficient farming

**Needs from Product:**
- **Verification Capability:** Must be able to import results into PoB and see they're correct
- **Transparency:** Show reasoning behind recommendations, not black-box magic
- **Performance Proof:** Hard numbers demonstrating improvement
- **Resource Awareness:** Account for their available respec point budget

**Estimated Market Size:** 50,000-100,000 players per league (based on PoB download statistics and Reddit engagement), ~10-20% of active endgame population.

**Willingness to Use Tool:** **HIGH**. This segment already uses Path of Building religiously and understands optimization value. Minimal adoption friction.

---

### Secondary User Segment: Leveling/Progression Players

**Demographics:**
- **Player Level:** 40-85 (mid-game progression)
- **Experience:** 50-500 hours, still learning game mechanics
- **Engagement:** More casual, 5-15 hours/week
- **Mindset:** Want to improve but intimidated by complexity

**Current Behavior:**
- Follow build guides but don't fully understand why certain choices were made
- Use Path of Building to import guide trees, rarely customize
- Ask for help in community channels ("my damage feels low")
- Often have messy passive trees with wasted points

**Pain Points:**
- **Confusion:** Don't know which passives are valuable for their build
- **Build Guides Diverge:** Their gear doesn't match guide assumptions
- **Feeling Stuck:** Character progression slows but don't know how to fix it
- **Resource Scarcity:** Very few respec points available, must spend wisely

**Goals:**
- Get unstuck and continue progressing through game content
- Understand what makes their build better or worse
- Learn passive tree efficiency to improve at the game
- Avoid expensive mistakes that force character rerolls

**Needs from Product:**
- **Simplicity:** Just tell them what to change, minimal jargon
- **Clear Improvement:** Show percentage gains in simple terms
- **Affordable Changes:** Respect their limited respec point budget
- **Learning Opportunity:** Help them understand tree efficiency principles

**Estimated Market Size:** 100,000-200,000 players per league (larger but less engaged than primary segment).

**Willingness to Use Tool:** **MODERATE**. Need more hand-holding and simpler UX, but will use if it helps them feel less stuck.

**MVP Prioritization:** Secondary segment can use MVP with minimal accommodation (simple dropdown is already accessible). Don't over-optimize for them yet—focus on primary segment first. V2 can add "explain changes" tooltips and simplified result presentation.

---

## Goals and Success Metrics

### Business Objectives

1. **Launch MVP within 2 months** (by December 2025)
   - Proves technical feasibility before larger investment
   - Captures early-league demand window
   - **Success Metric:** MVP deployed and accepting user traffic by target date

2. **Achieve product-market fit validation within 6 months**
   - Demonstrate users find genuine value, not just novelty
   - **Success Metric:** 30% of users return for second optimization session within same league

3. **Establish tool as community-recognized standard**
   - Become the default recommendation for tree optimization
   - **Success Metric:** Referenced in 10+ popular build guides or streamer content

4. **Build sustainable user base for future monetization/growth**
   - Prove concept has legs beyond initial curiosity
   - **Success Metric:** 5,000 unique users and 10,000 optimization sessions within first league

5. **Minimize operational costs during validation phase**
   - Keep infrastructure lean while proving value
   - **Success Metric:** Monthly hosting costs <$50 during MVP phase

### User Success Metrics

**Primary Success Indicators (Behavior-Based):**

1. **Optimization Completion Rate:** 70%+ of users who start an optimization complete it
   - *Measures:* UI clarity, process reliability, acceptable wait times
   - *Target:* ≥70% completion rate

2. **Result Verification Rate:** 50%+ of users import the optimized code into PoB
   - *Measures:* Trust in results, actionable output format
   - *Target:* ≥50% of completions result in PoB import

3. **Repeat Usage Rate:** 30%+ of users optimize multiple builds in same league
   - *Measures:* Genuine utility, not just curiosity
   - *Target:* ≥30% return for second+ optimization

4. **Average Improvement Delivered:** 5-15% DPS/EHP gain vs. user's starting tree
   - *Measures:* Algorithm effectiveness, real value delivered
   - *Target:* Median improvement ≥8%

5. **User Satisfaction (Post-Optimization Survey):** "Would you recommend this tool?"
   - *Measures:* Net Promoter Score
   - *Target:* NPS ≥40 (good for B2C tools)

**Secondary Success Indicators:**

6. **Time to Result:** 90%+ optimizations complete within 5 minutes
   - *Target:* <2 minutes for simple builds, <5 minutes for complex

7. **Error Rate:** <5% of optimization attempts fail due to technical issues
   - *Target:* ≥95% success rate

8. **Social Sharing:** Users share results in Discord/Reddit without prompting
   - *Target:* Organic mentions in 5+ community channels per week

### Key Performance Indicators (KPIs)

**North Star Metric:** **Completed Optimizations per Week**
- Combines user acquisition, engagement, and product reliability
- Target progression:
  - **Month 1 (MVP launch):** 500 optimizations/week
  - **Month 3:** 2,000 optimizations/week
  - **Month 6:** 5,000 optimizations/week

**Supporting KPIs:**

| Category | KPI | Target (Month 1) | Target (Month 6) |
|----------|-----|------------------|------------------|
| **Acquisition** | Unique Users | 1,000 | 10,000 |
| **Engagement** | Avg Optimizations per User | 1.5 | 2.5 |
| **Retention** | 7-Day Return Rate | 20% | 35% |
| **Quality** | Median Improvement Delivered | 7% | 10% |
| **Reliability** | Successful Completion Rate | 90% | 95% |
| **Performance** | Median Time to Result | 3 min | 2 min |
| **Trust** | PoB Code Import Rate | 40% | 60% |
| **Growth** | Community Mentions/Week | 5 | 25 |

**Measurement Infrastructure:**

- **Analytics:** Google Analytics 4 for user flows, Plausible for privacy-friendly basics
- **Backend Logging:** Track optimization parameters, results, completion times
- **User Feedback:** Optional post-optimization survey (1 question: NPS scale)
- **Community Monitoring:** Manual tracking of Reddit/Discord mentions initially

**Review Cadence:**
- **Weekly:** Completion rate, error rate, time to result (operational health)
- **Bi-weekly:** User acquisition, engagement trends, repeat usage
- **Monthly:** Full KPI dashboard review, strategic adjustments

**Success Definition:** MVP is successful if Month 3 targets are achieved, indicating genuine product-market fit rather than launch novelty.

---

## Strategic Alignment and Financial Impact

### Financial Impact

**Development Investment (MVP Phase - 2 Months):**

- **Labor:** Solo developer, opportunity cost basis
  - Time investment: 200-300 hours (full-time equivalent for 2 months)
  - Opportunity cost: $20,000-30,000 (based on contractor rates)
  - **Actual cash outlay:** $0 (sweat equity)

- **Infrastructure:**
  - Domain + SSL: $15/year
  - Hosting (VPS or serverless): $10-50/month during MVP
  - **Total cash required:** <$200 for 6-month validation period

**Post-MVP Investment (Months 3-6):**
- Scaling infrastructure: $50-200/month depending on traffic
- Potential part-time assistance for support/marketing: $0-2,000 (optional)
- **Total additional investment:** $300-1,200

**Revenue Potential (Speculative - Not Required for MVP):**

*Note: MVP is intentionally monetization-free to maximize adoption and validation. Revenue models are future considerations contingent on PMF.*

Potential future models (NOT for MVP):
- **Freemium:** Basic optimization free, premium features (multi-objective, historical tracking, priority queue) $5-10/month → potential $5,000-15,000/month at 1,000-1,500 paying users (conservative 10% conversion)
- **One-time purchases:** Pay-per-optimization credits → potential $0.50-1.00 per optimization
- **Sponsorship/Donations:** Patreon/Ko-fi support from community → potential $500-2,000/month

**Conservative ROI Projection:**
- **Break-even timeline:** Month 12-18 if monetization implemented after PMF validation
- **MVP phase ROI:** Not applicable—this is validation investment, not revenue-generating phase

**Strategic Value Beyond Direct Revenue:**
- **Portfolio/Resume Asset:** Demonstrates full-stack capability, algorithm implementation, product thinking
- **Community Contribution:** Goodwill and reputation in PoE community
- **Learning Investment:** Mastery of Python-Lua integration, optimization algorithms, production deployment
- **Future Product Platform:** If successful, foundation for additional PoE 2 tools/services

**Risk-Adjusted Value:**
- **Downside:** $200 cash + 300 hours opportunity cost if project fails validation
- **Upside:** $10,000+ annual revenue potential + portfolio value + learning outcomes if successful
- **Expected Value:** Positive given low cash risk and multiple value dimensions beyond revenue

### Company Objectives Alignment

*Note: This is a solo developer project, not corporate initiative. "Company" refers to personal development objectives.*

**Alignment with Personal/Professional Goals:**

1. **Skill Development Objective:** "Build production-grade full-stack applications"
   - **Alignment:** ✅ HIGH - Requires backend (Python/Lupa), frontend (web UI), DevOps (deployment), algorithm design (optimization), and integration engineering (PoB headless mode)

2. **Portfolio Objective:** "Create portfolio pieces demonstrating real-world problem-solving"
   - **Alignment:** ✅ HIGH - Addresses genuine user pain with measurable value delivery, not tutorial project

3. **Community Contribution Objective:** "Give back to gaming communities that provided value"
   - **Alignment:** ✅ HIGH - Free tool for PoE community, solves real player frustration

4. **Entrepreneurial Learning Objective:** "Experience full product lifecycle from idea to users"
   - **Alignment:** ✅ HIGH - Includes research, scoping, technical validation, MVP development, launch, user feedback, iteration

5. **Technical Challenge Objective:** "Tackle novel integration problems requiring creative solutions"
   - **Alignment:** ✅ HIGH - Headless PoB integration, optimization algorithm design, performance tuning for 1000+ calculation throughput

**Opportunity Cost Analysis:**

**Alternative Uses of 300 Hours:**
- Learning new framework/language (React, Go, Rust): Educational but less tangible outcome
- Contract work at $50-100/hour: $15,000-30,000 revenue but pure labor exchange
- Job search activities: Potentially higher long-term compensation but less skill demonstration
- Tutorial/course projects: Learning but no real users or validation

**Why This Project Wins:**
- **Portfolio Differentiation:** Real users + measurable impact > tutorial projects
- **Skill Breadth:** Touches more technology areas than typical web CRUD app
- **Validation Proof:** If successful, proves ability to identify needs and ship solutions
- **Risk Mitigation:** 2-month timeline limits downside if approach fails

### Strategic Initiatives

**Short-Term Initiatives (Months 1-6):**

1. **Technical Foundation Excellence**
   - Validate Lupa + HeadlessWrapper.lua integration (Days 1-3 prototype)
   - Achieve <1 second performance target for 1000 calculations
   - Build robust error handling and logging infrastructure
   - **Why:** Technical reliability = trust = repeat usage

2. **Transparent Communication**
   - Clear progress messages during optimization
   - Honest limitation disclosure (unsupported build types)
   - Detailed "what changed" explanations in results
   - **Why:** Trust is the product, not the algorithm

3. **Community Seeding**
   - Soft launch in r/pathofexile with "I built a tool" post
   - Respond to feedback and iterate quickly based on early user pain points
   - Share interesting optimization case studies (with user permission)
   - **Why:** Organic growth through community validation > paid marketing

4. **Data-Driven Iteration**
   - Instrument everything (completion rates, improvement distributions, common failure modes)
   - Weekly metrics review and adjustment
   - A/B test messaging, UI flow, default settings
   - **Why:** Let user behavior guide V2 priorities, not assumptions

**Medium-Term Initiatives (Months 6-12 - Post-PMF):**

5. **Advanced Feature Rollout** (Only if MVP succeeds)
   - Multi-objective optimization ("The Build Equalizer")
   - Historical tracking (see build evolution over time)
   - Reference build integration (optimize toward meta builds)
   - **Why:** Deepen value for power users who validated the concept

6. **Expansion to Adjacent Problems**
   - Skill gem optimization
   - Item upgrade recommendations
   - Ascendancy comparison
   - **Why:** If passive tree works, adjacent optimizations follow same trust pattern

7. **Monetization Exploration** (Only if PMF + strong retention)
   - Premium features for power users (priority queue, advanced constraints)
   - Donation/support model with transparency about costs
   - **Why:** Sustainability enables long-term maintenance and feature development

**Long-Term Vision (12+ Months):**

8. **Platform Evolution**
   - Comprehensive PoE 2 build optimization suite
   - API for third-party integrations (streamers, guide creators)
   - Mobile companion app for on-the-go optimization
   - **Why:** If trust and utility are established, expand surface area

**Strategic Non-Goals (Explicit Scope Boundaries):**

- ❌ **AI Chat Interface:** Complexity creep, minimal value over simple dropdown
- ❌ **Full Build Generation:** Exponentially harder, dilutes focus
- ❌ **Account Integration via API:** External dependency risk, authentication complexity
- ❌ **Support for ALL Build Types:** 80/20 rule—focus on common builds, defer minions/triggers
- ❌ **Real-Time Racing/PvP Features:** Niche use case, premature optimization

**Decision Framework:** Only add features that reinforce core value proposition (mathematical passive tree optimization) without compromising simplicity or trust.

---

## MVP Scope

### Core Features (Must Have)

**1. PoB Code Input & Parsing** ✅ CRITICAL
- **Functionality:**
  - Large text area for pasting Path of Building code
  - Base64 decoding → zlib decompression → XML parsing
  - Extract character level, ascendancy, current passive tree allocation, items, skills, configuration
  - Input validation with helpful error messages
- **Why Critical:** This is the entry point—if input fails, nothing else matters
- **Acceptance Criteria:**
  - Successfully parse 95%+ of valid PoE 2 PoB codes
  - Clear error message for invalid/corrupted codes
  - Display parsed character summary (class, level, ascendancy) for user confirmation

**2. Optimization Goal Selection** ✅ CRITICAL
- **Functionality:**
  - Dropdown menu with clear options:
    - "Maximize Total DPS" (default)
    - "Maximize Effective HP (EHP)"
    - "Maximize DPS while maintaining current EHP"
  - Optional: "Available respec points" input field (default: unlimited)
- **Why Critical:** Algorithm needs clear objective function—users must specify intent
- **Acceptance Criteria:**
  - All goal options produce different tree recommendations
  - Budget constraint (if specified) is respected in results
  - Default selection works without user needing to understand options deeply

**3. Headless PoB Calculation Engine Integration** ✅ CRITICAL - HIGHEST RISK
- **Functionality:**
  - Lupa library embedded in Python backend
  - HeadlessWrapper.lua loaded with required stub functions (Deflate/Inflate, ConPrintf, etc.)
  - Accept build state as input, return calculated stats (DPS, EHP, resistances) as output
  - Deterministic results (same input → same output every time)
- **Why Critical:** This is the oracle—wrong calculations = broken product
- **Acceptance Criteria:**
  - Calculation results match official Path of Building within 0.1% tolerance
  - Single calculation completes in <100ms
  - 1000 batch calculations complete in <1 second
  - Graceful handling of calculation errors with stack traces

**4. Passive Tree Optimization Algorithm** ✅ CRITICAL
- **Functionality:**
  - Hill climbing algorithm (MVP): Iteratively test node allocation changes, keep improvements
  - Respects tree pathing rules (must maintain connectivity to starting point)
  - Respects respec budget if specified
  - Convergence detection (stop when no further improvements found)
  - Real-time progress updates ("Evaluating damage increase...", "Checking alternate paths...")
- **Why Critical:** This is the core value—delivering superior trees users wouldn't find manually
- **Acceptance Criteria:**
  - Produces trees with 5-15% improvement over baseline for 80%+ of inputs
  - Completes optimization in <5 minutes for complex builds (120 points allocated)
  - Never violates tree connectivity rules (all nodes pathable from start)
  - Respects budget constraints when specified

**5. Results Presentation & PoB Code Generation** ✅ CRITICAL
- **Functionality:**
  - Before/After comparison showing:
    - Key stats (DPS, EHP, resistances)
    - Percentage improvements clearly highlighted
    - Cost breakdown ("Deallocate X points, reallocate Y points, cost: Z respec points")
  - Generate new PoB code (XML → zlib compression → Base64 encoding)
  - Copy button for easy PoB import
  - Display time taken ("Optimization completed in 3m 24s")
- **Why Critical:** Output must be actionable and verifiable—users need proof
- **Acceptance Criteria:**
  - Generated PoB code imports successfully into Path of Building
  - PoB highlights exact node changes (visual diff)
  - Percentage improvements displayed match PoB recalculation
  - Cost breakdown is accurate

**6. Budget Constraint System** ✅ ESSENTIAL (Promoted from V2)
- **Functionality:**
  - Input field: "How many respec points can you spend?"
  - Four optimization modes:
    - Free optimization (0 respec cost—only reallocate existing points)
    - Limited respec (user-specified budget)
    - Full rebuild (unlimited budget for theory-crafting)
    - Incremental growth (just leveled up, 1 new point to spend)
  - Algorithm rejects tree changes exceeding budget
  - Display respec cost in results
- **Why Essential:** Without this, tool suggests impossible builds—ruins trust
- **Acceptance Criteria:**
  - Optimizations never exceed specified respec budget
  - "Free optimization" mode produces zero-cost improvements when possible
  - Clear warning if no improvements possible within budget

**7. Real-Time Progress Transparency** ✅ ESSENTIAL
- **Functionality:**
  - Status message display during processing:
    - "Parsing your build..."
    - "Baseline DPS: 847,300"
    - "Evaluating node allocations... (34% complete)"
    - "Found improvement: +4.2% DPS..."
    - "Testing alternate paths..."
    - "Optimization complete!"
  - Progress bar or spinner indicating work is happening
- **Why Essential:** Keeps users engaged during 1-5 minute wait, builds trust by showing work
- **Acceptance Criteria:**
  - Status updates at least every 15 seconds during optimization
  - Progress messages accurately reflect algorithm state
  - User never sees "frozen" UI during processing

**8. Basic Error Handling & Reliability** ✅ CRITICAL
- **Functionality:**
  - Graceful handling of invalid inputs
  - Timeout protection (optimization stops after 10 minutes with best result so far)
  - Error logging for debugging failures
  - User-friendly error messages (not raw stack traces)
- **Why Critical:** Users will submit broken builds, edge cases—must handle gracefully
- **Acceptance Criteria:**
  - 95%+ successful completion rate for valid inputs
  - Clear error messages for unsupported build types ("Minion builds not yet supported")
  - No crashes or infinite loops
  - Failed optimizations don't block other users (isolated sessions)

### Out of Scope for MVP

**Explicitly Deferred Features (V2 Candidates):**

1. ❌ **AI Chat Interface for Goal Definition**
   - **Why excluded:** NLP complexity, months of development, marginal value over dropdown
   - **When to add:** V2 if user feedback shows dropdown too limiting

2. ❌ **User Accounts & Authentication**
   - **Why excluded:** Database, auth infrastructure, GDPR compliance—massive complexity
   - **When to add:** V2 when historical tracking or paid features require accounts

3. ❌ **Historical Tracking (Build Evolution Over Time)**
   - **Why excluded:** Requires user accounts, database, more complex UI
   - **When to add:** V2 after PMF validation

4. ❌ **Auto-Import from PoE Account API**
   - **Why excluded:** External dependency, OAuth complexity, API rate limits
   - **When to add:** V2 as convenience feature if users request

5. ❌ **Multi-Objective Optimization "Build Equalizer"**
   - **Why excluded:** 10+ weighted stat sliders = analysis paralysis for most users
   - **When to add:** V2 as "Advanced" tab for power users

6. ❌ **Reference Build Integration (Import from Maxroll, etc.)**
   - **Why excluded:** External dependencies, scraping complexity, maintenance burden
   - **When to add:** V2 if users request "optimize toward meta build" feature

7. ❌ **Skill Gem or Item Optimization**
   - **Why excluded:** Exponentially more complex than passive tree, dilutes focus
   - **When to add:** Separate future product after passive tree succeeds

8. ❌ **Support for Minion/Trigger/Complex Build Types**
   - **Why excluded:** 80/20 rule—focus on 80% of builds (self-cast/attack)
   - **When to add:** V2 after MVP proves core algorithm works

9. ❌ **Live Game Balance Integration (Patch Note Parsing)**
   - **Why excluded:** Complex ongoing maintenance, premature optimization
   - **When to add:** V3 if tool becomes community standard

10. ❌ **Mobile App or Advanced Visualizations**
    - **Why excluded:** Scope creep, minimal value for optimization use case
    - **When to add:** Only if web version reaches 50K+ users and mobile requested

**Scope Enforcement:** Any feature request not on "Core Features" list requires written justification of why it's essential for MVP hypothesis validation before consideration.

### MVP Success Criteria

**Technical Success (Gates V2 Investment):**

✅ **Criterion 1: Prototype Validation (Days 1-3)**
- Headless PoB integration working
- Single build calculation accuracy matches PoB GUI within 0.1%
- Performance: 1000 calculations in <1 second
- **If FAIL:** Project pivots or stops

✅ **Criterion 2: MVP Deployment (Week 8)**
- Web application accessible at public URL
- End-to-end optimization flow functional
- 95%+ successful completion rate for test builds
- **If FAIL:** Extend development timeline or simplify scope

✅ **Criterion 3: Algorithm Effectiveness (Week 8)**
- Median improvement delivered: ≥8% for optimization_target metric
- 80%+ of optimizations produce ≥5% improvement
- Generated PoB codes import successfully into PoB
- **If FAIL:** Improve algorithm or adjust optimization strategy

**User Success (Gates V2 Investment):**

✅ **Criterion 4: Initial Traction (Month 1)**
- 1,000 unique users attempt optimization
- 70%+ completion rate (users finish optimization)
- 40%+ import rate (users copy PoB code)
- **If FAIL:** Improve UX, reduce friction, or improve messaging

✅ **Criterion 5: Product-Market Fit Signal (Month 3)**
- 30%+ repeat usage rate (users optimize 2+ builds)
- NPS ≥40 from post-optimization survey
- Organic community mentions (5+ per week in Reddit/Discord)
- **If FAIL:** Pivot positioning, improve value delivery, or reassess market

✅ **Criterion 6: Value Delivery (Month 3)**
- Median optimization time: <3 minutes
- User reports: "Saved time vs. manual optimization"
- Community feedback: "Actually useful, not just a novelty"
- **If FAIL:** Improve performance or reconsider value proposition

**GO/NO-GO Decision Points:**

- **After Prototype (Day 3):** GO if headless PoB works → proceed to MVP
- **After MVP Launch (Month 1):** GO if completion rate ≥70% → continue to Month 3
- **After 3 Months:** GO if repeat usage ≥30% and NPS ≥40 → invest in V2
- **NO-GO Triggers:** Completion rate <50%, repeat usage <15%, negative community sentiment

**Definition of MVP Success:** MVP is successful if Month 3 criteria achieved, proving genuine utility and product-market fit rather than launch curiosity.

---

## Post-MVP Vision

### Phase 2 Features (Months 6-12 - If MVP Succeeds)

**Priority 1: Advanced Optimization Capabilities** (Deepen value for power users)

1. **Multi-Objective Optimization "Build Equalizer"**
   - Advanced tab with 5-10 weighted stat sliders
   - Examples: DPS (100%), EHP (80%), Chaos Resist (target: 52%), Movement Speed (40%)
   - Solves complex constraint problems: "Max damage while hitting resist caps"
   - Target audience: Expert theory-crafters (10-20% of users)

2. **Simulated Annealing Layer for Better Results**
   - Hybrid algorithm: Hill climbing → simulated annealing → final refinement
   - Escapes local optima that pure hill climbing misses
   - Expected improvement: 2-5% better results for same optimization time
   - Technical upgrade, transparent to users

3. **Budget Optimization Modes Expansion**
   - "Optimize for next 5 levels" (incremental growth path planning)
   - "Best bang for buck" (prioritize high-impact low-cost changes)
   - "Respec minimization" (achieve X goal with fewest respec points)

**Priority 2: User Experience Enhancements** (Increase retention)

4. **Historical Tracking & Build Evolution**
   - User accounts (optional, not required)
   - See progression: Build v1 → v2 → v3 over league
   - Compare: "My DPS last week vs. now"
   - Rollback: "Show me my previous tree"
   - Value: Users understand impact of changes over time

5. **Explanation & Learning Features**
   - "Explain changes" button: Why did algorithm choose these nodes?
   - Node value heatmap: Show which nodes most impact your goal
   - Comparison mode: "What if I picked X keystone instead of Y?"
   - Value: Helps players learn passive tree efficiency principles

6. **Reference Build Integration**
   - Import builds from Maxroll, poe.ninja, or URLs
   - "Optimize this meta build for my preferences"
   - "Make my build more like this reference"
   - Value: Leverage community expertise, provide proven baselines

**Priority 3: Expanded Build Type Support** (Address remaining 20%)

7. **Minion Build Support**
   - Handle minion scaling calculations (separate damage instance)
   - Animate Guardian gear modeling
   - Minion AI and uptime assumptions
   - Technical complexity: HIGH, but expands addressable market

8. **Trigger Build Support**
   - Cast on Crit, Cast when Damage Taken, etc.
   - Model proc rates and trigger loops
   - Cooldown and resource management calculations

9. **Attribute Stacking & Aura Build Support**
   - Handle complex multiplicative scaling (e.g., INT scaling spell damage)
   - Aura effect calculations with reserved mana modeling

**Priority 4: Community & Collaboration Features**

10. **Crowd-Sourced Optimization Intelligence**
    - Aggregate anonymized optimization data across users
    - Generate insights: "87% of optimized Frost Berserkers allocate these nodes"
    - Heat maps: Most valuable tree regions by build archetype
    - Value: Community consensus validation, not just algorithm opinion

11. **Social Sharing & Build Comparison**
    - Share optimization results with unique URL
    - Compare your build with friend's or streamer's
    - "Challenge" mode: "Can the optimizer beat this build?"

### Long-term Vision (12-24 Months)

**Vision Statement:** Evolve from single-purpose tree optimizer to **comprehensive PoE 2 build optimization suite**, becoming the de facto standard for competitive build creation and refinement.

**Expansion Pillars:**

**Pillar 1: Full Build Optimization (Not Just Tree)**
- **Skill Gem Optimizer:** Best gem links for DPS/utility
- **Item Upgrade Advisor:** "Which gear slot to upgrade for biggest impact?"
- **Ascendancy Comparison:** "Which ascendancy is optimal for this playstyle?"
- **Complete Build Generator:** "I want Frost Berserker" → system outputs full build
- **Rationale:** If passive tree works and users trust the tool, adjacent optimizations follow same pattern

**Pillar 2: Platform & Ecosystem**
- **Public API:** Third-party integrations (streamers, guide creators, build planners)
- **Mobile Companion App:** On-the-go optimization, build comparison
- **Discord/Twitch Bots:** "!optimize <PoB code>" in chat
- **Rationale:** Maximize surface area for user acquisition, reduce friction

**Pillar 3: Data-Driven Intelligence**
- **Live Game Balance Tracker:** Parse patch notes, trigger re-optimization notifications
- **Meta Analysis Dashboard:** What's strong this patch based on optimization data
- **Predictive Build Scoring:** "This build will be nerfed next patch" warnings
- **Rationale:** Transform tool from utility to strategic intelligence platform

**Pillar 4: Monetization & Sustainability**
- **Freemium Model:** Basic free, premium features $5-10/month (priority queue, advanced constraints, historical tracking, API access)
- **Sponsorship Model:** Patreon/Ko-fi for community supporters
- **Enterprise/Creator Licensing:** Streamers/guide sites pay for API access or white-label
- **Rationale:** Ensure long-term maintenance and feature development sustainability

**Success Metrics (24 Months):**
- 50,000+ monthly active users
- 10-15% premium conversion rate (5,000-7,500 paying users)
- $25,000-75,000 annual revenue (sustainable solo developer income)
- Mentioned in 50+ build guides, 10+ streamer endorsements
- Recognized as community standard for build optimization

**Moonshot Vision (5+ Years):**
- Expand to other complex optimization games (Last Epoch, Grim Dawn, D4)
- ML-based build suggestion ("Recommend me a build based on my playstyle")
- Real-time in-game overlay integration (if game permits)
- Become "optimization as a service" platform for theorycrafters across games

### Expansion Opportunities

**Adjacent Market Opportunities:**

1. **PoE 1 Passive Tree Optimizer (Backward Compatibility)**
   - Port algorithm to PoE 1 PoB
   - Tap into larger existing user base (millions vs. hundreds of thousands)
   - Lower development cost (same architecture, different data files)
   - Rationale: Validate business model in larger market

2. **League Starter Build Generator**
   - "Suggest league starter builds for X playstyle"
   - Optimize for low gear requirements, smooth leveling curve
   - Rationale: Solves different but related problem for same audience

3. **Racing & Speedrun Optimization**
   - Optimize for leveling speed, not endgame power
   - Target: Speedrunners, racers, HC league players
   - Rationale: Niche but highly engaged audience

4. **Educational Content & Courses**
   - "Learn Passive Tree Efficiency" course using tool as teaching aid
   - YouTube/Twitch content demonstrating optimization principles
   - Rationale: Monetization path + marketing channel

5. **B2B Services for Content Creators**
   - White-label optimization for build guide sites
   - API access for streamers/YouTubers to offer "optimized viewer builds"
   - Rationale: Leverage their audiences, recurring revenue potential

**Geographic/Platform Expansion:**

6. **Localization for Non-English Markets**
   - Chinese, Russian, Spanish, Portuguese translations
   - Rationale: PoE is global, huge markets in CN/RU

7. **Console Player Support (If PoE 2 on Consoles)**
   - Simplified UI for controller navigation
   - Rationale: Expand addressable market beyond PC

**Technology Platform Opportunities:**

8. **"Optimization Engine" as White-Label SaaS**
   - Sell optimization algorithm infrastructure to other game tool developers
   - Rationale: Technology has broader applications beyond PoE

9. **Patreon-Funded Development Model**
   - Community-driven feature prioritization
   - Transparent development process
   - Rationale: Align incentives with users, not ad revenue

**Constraints on Expansion:**
- **Don't expand until MVP proves PMF** - Premature optimization kills projects
- **Maintain focus** - Say no to opportunities that dilute core value proposition
- **Sustainability first** - Only expand if current product can self-sustain

**Decision Framework for Expansion:**
1. Does it serve existing users better? (Deepen before broadening)
2. Does it leverage existing technical infrastructure? (Low marginal cost)
3. Does it align with core mission (mathematical optimization + trust)?
4. Can it be done without compromising MVP/V2 quality?

If NO to 2+ questions → defer or decline.

---

## Technical Considerations

### Platform Requirements

**Primary Platform: Web Application (Browser-Based)**

**Rationale:**
- **Accessibility:** No installation friction—users paste code and go
- **Cross-Platform:** Works on Windows, Mac, Linux without separate builds
- **Update Velocity:** Deploy fixes and features instantly, no user update required
- **Cost Efficiency:** Single codebase for all platforms

**Browser Support:**
- **Target Browsers:**
  - Chrome/Edge (Chromium): 90%+ of PoE players
  - Firefox: 5-8% of users
  - Safari: <5% (Mac users)
- **Minimum Browser Versions:** Last 2 major versions (auto-update era)
- **Compatibility Strategy:** Progressive enhancement, graceful degradation for old browsers

**Performance Requirements:**

**Backend (Optimization Engine):**
- **Response Time:**
  - Parse PoB code: <500ms
  - Single tree calculation: <100ms
  - Full optimization (1000+ calculations): <5 minutes (target: 2-3 minutes)
- **Throughput:**
  - 10-50 concurrent optimizations (MVP scale)
  - Scale to 100+ concurrent (V2, vertical scaling or queue system)
- **Reliability:**
  - 99%+ uptime during league launch windows (first 2 weeks of league)
  - Graceful degradation under load (queue system vs. crashes)

**Frontend (User Interface):**
- **Load Time:** Initial page load <2 seconds on 10Mbps connection
- **Responsiveness:** UI interactions <100ms response time
- **Real-time Updates:** Progress messages update every 10-15 seconds during optimization

**Accessibility Standards:**

**MVP Targets:**
- **Keyboard Navigation:** All interactions accessible via keyboard (tab, enter, arrow keys)
- **Screen Reader Compatibility:** Semantic HTML, ARIA labels for critical elements
- **Color Contrast:** WCAG AA compliance for text readability
- **Responsive Design:** Works on desktop (1920x1080 down to 1366x768)

**Post-MVP Accessibility:**
- Mobile responsive design (tablet/phone support)
- WCAG AAA compliance
- Multiple language support

**Data Requirements:**
- **Latency Tolerance:** Users will tolerate 2-5 minute optimization times if progress is shown
- **Data Privacy:** No user accounts initially = no PII storage, GDPR-compliant by default
- **Offline Support:** Not required for MVP (web-only, requires backend processing)

**Infrastructure Requirements (MVP Scale):**
- **Hosting:** Single VPS or serverless functions (AWS Lambda, Vercel, Railway)
- **Database:** Not required for MVP (stateless optimizations)
- **CDN:** Optional for MVP, useful for V2 (static asset delivery)
- **Monitoring:** Error tracking (Sentry) + basic analytics (Google Analytics or Plausible)

### Technology Preferences

**Backend Stack:**

**Language: Python 3.11+** ✅ DECIDED
- **Rationale:**
  - Required for Lupa library (Python-LuaJIT integration)
  - Excellent ecosystem for web frameworks, scientific computing, data processing
  - Fast development velocity, readable code
- **Alternatives Considered:**
  - Node.js + Fengari: Rejected (Fengari appears abandoned, poor performance)
  - Go + Lua FFI: Rejected (higher complexity, smaller ecosystem)

**Web Framework: FastAPI** ✅ RECOMMENDED
- **Rationale:**
  - Modern async Python framework (handles concurrent optimizations well)
  - Automatic OpenAPI documentation (useful for future API)
  - Type hints + Pydantic validation (reduces bugs)
  - Fast development, excellent performance
- **Alternative:** Flask (simpler but less modern, harder to scale)

**Lua Integration: Lupa 2.5+** ✅ DECIDED (based on research)
- **Rationale:**
  - Embeds LuaJIT 2.1 directly in Python process
  - Excellent performance (0.15-0.5ms per calculation)
  - Active maintenance, binary wheels for all platforms
  - Proven production usage
- **Critical Dependency:** PoB HeadlessWrapper.lua + stub functions

**Frontend Stack:**

**HTML/CSS/JavaScript: Vanilla or Minimal Framework** ✅ RECOMMENDED
- **Rationale:**
  - MVP UI is simple (text box, dropdown, button, results display)
  - No need for React/Vue complexity
  - Faster load times, smaller bundle size
- **Technology Choices:**
  - **HTML5:** Semantic markup for accessibility
  - **CSS:** Tailwind CSS or simple custom styles
  - **JavaScript:** Vanilla JS or Alpine.js (lightweight reactivity)
- **When to Upgrade:** V2 if UI becomes complex (multi-step flows, interactive visualizations)

**Infrastructure & DevOps:**

**Hosting: VPS (Hetzner, DigitalOcean) or Serverless (Railway, Render)** ⚠️ TBD
- **VPS Pros:** Full control, predictable costs, persistent runtime
- **VPS Cons:** Manual server management, must handle scaling
- **Serverless Pros:** Zero-ops, auto-scaling, pay-per-use
- **Serverless Cons:** Cold starts (bad for optimization), cost unpredictable at scale
- **Decision:** Start with VPS (predictable, Lupa runtime persistent), consider serverless for frontend/API layer only

**Database: None for MVP** ✅ DECIDED
- **Rationale:** Stateless optimizations, no user accounts, no data persistence needed
- **When to Add:** V2 if adding historical tracking or user accounts (likely PostgreSQL or SQLite)

**Analytics: Plausible or Google Analytics 4** ⚠️ TBD
- **Plausible Pros:** Privacy-friendly, GDPR compliant, no cookie consent needed
- **Plausible Cons:** Paid service ($9/month)
- **GA4 Pros:** Free, comprehensive tracking, familiar ecosystem
- **GA4 Cons:** Privacy concerns, requires cookie consent, complex setup
- **Decision:** Plausible for MVP (aligns with trust/transparency values)

**Error Tracking: Sentry (Free Tier)** ✅ RECOMMENDED
- **Rationale:** Catch backend errors, track optimization failures, debug issues
- **Cost:** Free for <5K errors/month (sufficient for MVP)

**Version Control & CI/CD:**
- **Git + GitHub:** Source control, issue tracking, project management
- **CI/CD:** GitHub Actions for automated testing and deployment
- **Deployment:** Git push → automated deploy to VPS or serverless

### Architecture Considerations

**High-Level Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                     USER BROWSER                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Frontend (HTML/CSS/JS)                            │ │
│  │  - Input form (PoB code, goal, budget)            │ │
│  │  - Progress display (real-time updates)           │ │
│  │  - Results presentation (before/after, new code)  │ │
│  └────────────────────────────────────────────────────┘ │
└────────────────┬────────────────────────────────────────┘
                 │ HTTPS (REST API)
                 ▼
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (Python/FastAPI)                │
│  ┌────────────────────────────────────────────────────┐ │
│  │  API Layer                                         │ │
│  │  - POST /optimize (accept PoB code + params)      │ │
│  │  - GET /status/:job_id (progress polling)         │ │
│  │  - GET /result/:job_id (fetch completed result)   │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Optimization Engine                               │ │
│  │  - PoB Code Parser (Base64 → XML)                 │ │
│  │  - Passive Tree Graph Builder                     │ │
│  │  - Optimization Algorithm (Hill Climbing)         │ │
│  │  - PoB Code Generator (XML → Base64)              │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Headless PoB Integration (Lupa + LuaJIT)         │ │
│  │  - LuaRuntime initialization                      │ │
│  │  - HeadlessWrapper.lua loader                     │ │
│  │  - Stub functions (Deflate/Inflate, Console)      │ │
│  │  - Calculation interface (input → stats)          │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Key Architectural Decisions:**

**1. Stateless Request Model (MVP)**
- **Decision:** Each optimization is independent, no server-side session state
- **Rationale:** Simplifies infrastructure, avoids database requirement
- **Trade-off:** No ability to resume interrupted optimizations
- **V2 Evolution:** Add job queue + persistent storage for long-running optimizations

**2. Synchronous Optimization (MVP)**
- **Decision:** API request blocks until optimization completes (with timeout)
- **Rationale:** Simpler implementation, fewer moving parts
- **Trade-off:** Single request can take 2-5 minutes (acceptable with progress updates)
- **V2 Evolution:** Async job queue (Celery + Redis) for scalability

**3. In-Process Lupa Integration**
- **Decision:** Lua runtime embedded in Python process (not separate service)
- **Rationale:** Eliminates IPC overhead, simplifies deployment, achieves best performance
- **Trade-off:** Lua crashes could affect Python process (mitigated by error handling)
- **Alternative Rejected:** Separate Lua process + IPC (too complex for MVP)

**4. Single-Server Deployment (MVP)**
- **Decision:** One VPS instance handles all traffic initially
- **Rationale:** Sufficient for 10-50 concurrent users, minimizes cost and complexity
- **Scaling Path:** Vertical scaling (bigger VPS) → Horizontal scaling (load balancer + multiple instances) → Async job queue
- **When to Scale:** When single server CPU >80% sustained or response times degrade

**5. No Database (MVP)**
- **Decision:** Store nothing persistently, pure compute service
- **Rationale:** Eliminates entire class of complexity (backups, migrations, schema design)
- **Trade-off:** No historical tracking, no user preferences
- **When to Add:** V2 when adding user accounts or result history

**Scalability Considerations:**

**Expected Load (MVP Launch):**
- **Week 1:** 500-1,000 users, 1,000-2,000 optimizations
- **Concurrent Load:** 5-10 simultaneous optimizations
- **CPU Usage:** Optimization is CPU-bound (LuaJIT calculations)
- **Memory Usage:** 1-10MB per optimization session
- **Single Server Capacity:** 4-core VPS can handle 10-20 concurrent optimizations

**Bottlenecks & Mitigation:**

1. **CPU Saturation (Most Likely)**
   - **Symptom:** Optimization times increase under load
   - **Mitigation:** Vertical scaling (8-core VPS) or request queue with "position in line" feedback

2. **Memory Exhaustion (Unlikely but Possible)**
   - **Symptom:** Server OOM errors when too many large builds optimized simultaneously
   - **Mitigation:** Memory limits per request, graceful rejection with "try again later"

3. **Cold Start Delays (If Using Serverless)**
   - **Symptom:** First request after idle period takes 10+ seconds (Lua runtime initialization)
   - **Mitigation:** Use VPS with persistent runtime, or serverless keep-warm strategies

**Security Considerations:**

**MVP Security Requirements:**

1. **Input Validation:**
   - Sanitize PoB code input (prevent XML injection, billion laughs attack)
   - Limit input size (max 5MB PoB code to prevent DoS)
   - Rate limiting (10 requests per IP per hour initially)

2. **Lua Sandboxing:**
   - Memory limits on LuaRuntime (100MB max per session)
   - Timeout protection (kill optimization after 10 minutes)
   - Disable dangerous Lua functions (file I/O, network access) via stubs

3. **Web Security Basics:**
   - HTTPS only (Let's Encrypt SSL certificate)
   - CORS headers (restrict API access to frontend domain)
   - No user authentication = no password security concerns

**V2 Security Additions:**
- User authentication (OAuth or email/password with bcrypt)
- CSRF protection for state-changing operations
- API rate limiting per user account

**Data Flow Example (Typical Optimization):**

1. User pastes PoB code in browser, selects "Maximize DPS", enters "15 respec points available", clicks "Optimize"
2. Frontend sends POST /optimize with payload: `{pob_code, goal: "dps", budget: 15}`
3. Backend parses PoB code → extracts current tree, level, items, skills
4. Backend initializes Lua runtime, loads HeadlessWrapper.lua, calculates baseline stats (DPS: 847,300)
5. Backend runs hill climbing algorithm:
   - Iteration 1: Try deallocating node X, allocating node Y → recalculate → DPS: 852,100 (+0.6%) → KEEP
   - Iteration 2: Try deallocating node Z, allocating node W → recalculate → DPS: 851,900 (-0.02%) → REJECT
   - ... (repeat 100-500 iterations)
   - Send progress updates to frontend every 15 seconds via Server-Sent Events or polling
6. Algorithm converges: Best tree found with DPS: 931,450 (+9.9%), cost: 8 respec points (within 15 budget)
7. Backend generates new PoB code (XML → zlib compress → Base64 encode)
8. Backend returns result: `{baseline: {...}, optimized: {...}, improvement: 9.9%, new_code: "...", cost: 8}`
9. Frontend displays before/after comparison, user clicks "Copy PoB Code" and imports into Path of Building

**Architecture Evolution Path:**

- **MVP (Months 1-3):** Synchronous, stateless, single server
- **V2 (Months 6-12):** Async job queue, database for user accounts, horizontal scaling
- **V3 (12+ months):** Microservices (API gateway + optimization workers), caching layer, CDN

**Technology Risks & Mitigation:**

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Lupa performance worse than expected | High (violates perf target) | Low (proven in research) | Already validated in prototype |
| PoB HeadlessWrapper breaking changes | Medium (requires rework) | Medium (PoB updates frequently) | Pin PoB version, monitor releases, parity tests |
| Lua calculation errors/crashes | High (wrong results = broken trust) | Medium (complex edge cases) | Comprehensive error handling, test suite, parity validation |
| Server overwhelmed by traffic | Medium (slow/unavailable) | Medium (if goes viral) | Queue system, "try again later" messages, vertical scaling ready |
| Dependency supply chain issues | Low (annoying but recoverable) | Low | Pin all dependency versions, vendor critical libs |

**Decision Record:** Architecture optimized for MVP speed and simplicity with clear evolution path. Avoid premature optimization—solve scaling when it becomes a problem, not before.

---

## Constraints and Assumptions

### Constraints

**Resource Constraints:**

1. **Solo Developer / Limited Bandwidth** ✅ CRITICAL
   - **Impact:** All design, development, testing, deployment, marketing done by one person
   - **Implications:**
     - MVP scope must be ruthlessly minimal to hit 2-month timeline
     - No specialized expertise (UX designer, DevOps engineer, marketer) available
     - Technical decisions favor simplicity over perfection
     - Support burden must stay manageable (self-service documentation, minimal manual intervention)
   - **Mitigation:** Extreme focus on one problem, reuse proven libraries/frameworks, community self-help

2. **Budget: $0-200 Cash Outlay for MVP** ✅ CRITICAL
   - **Impact:** Infrastructure and tooling must be free or near-free initially
   - **Implications:**
     - Use free tiers (Vercel, Railway, Hetzner cheapest VPS)
     - No paid marketing, advertising, or customer acquisition costs
     - Leverage free open-source tools (Lupa, Path of Building, FastAPI)
   - **Mitigation:** Organic community marketing (Reddit, Discord), free hosting options, freemium model only after PMF validation

3. **Timeline: 2 Months to MVP Launch** ✅ CRITICAL
   - **Impact:** Aggressive timeline forces hard scope choices
   - **Implications:**
     - Days 1-3: Prototype validation (GO/NO-GO gate)
     - Weeks 1-2: Backend core (PoB integration, parser, algorithm)
     - Weeks 3-5: Optimization algorithm refinement and testing
     - Week 6: Frontend UI and integration
     - Week 7: End-to-end testing, bug fixes
     - Week 8: Deployment, soft launch
   - **Mitigation:** Dual-track prototype strategy, cut features aggressively, accept technical debt for MVP

**Technical Constraints:**

4. **Must Use Official Path of Building Calculation Engine** ✅ CRITICAL
   - **Impact:** 100% calculation accuracy non-negotiable, defines architecture
   - **Implications:**
     - Lua integration via Lupa required (not optional)
     - PoB HeadlessWrapper.lua must work with PoE 2 version
     - Dependency on PoB community maintaining open-source project
     - Calculation logic changes with PoB updates (requires maintenance)
   - **Mitigation:** Pin PoB version for MVP, monitor PoB GitHub for breaking changes, comprehensive parity test suite

5. **Performance Target: <1 Second for 1000 Calculations** ✅ CRITICAL
   - **Impact:** Enables iterative optimization algorithms (hill climbing, simulated annealing)
   - **Implications:**
     - Lupa + LuaJIT required (subprocess approaches too slow)
     - Algorithm design constrained by calculation throughput
     - Must batch calculations efficiently (pre-compile functions, minimize boundary crossings)
   - **Mitigation:** Already validated in Lupa deep research (150-500ms achievable), optimization patterns documented

6. **PoE 2 Data Availability** ⚠️ MEDIUM RISK
   - **Impact:** Passive tree data, item/skill data must be machine-readable
   - **Assumptions:** PoE 2 PoB will include JSON/Lua data files like PoE 1
   - **Risk:** If data formats differ significantly, requires additional parsing work
   - **Mitigation:** PathOfBuildingAPI library may help with parsing, PoB community will solve this

**Market/User Constraints:**

7. **Target Audience: PC Players Only (Initially)** ✅ DECIDED
   - **Impact:** Web UI optimized for desktop browsers, not mobile
   - **Rationale:** PoE 2 is PC-first, players optimize builds on desktop with Path of Building open
   - **Implication:** Mobile optimization deferred to V2 (if requested)

8. **English Language Only (MVP)** ✅ DECIDED
   - **Impact:** Limits addressable market (excludes CN, RU, etc.)
   - **Rationale:** Solo dev can't translate/localize in 2 months
   - **Implication:** Significant markets left untapped (CN is huge PoE market)
   - **V2 Expansion:** Add localization if MVP succeeds

**Operational Constraints:**

9. **No 24/7 Support Availability** ✅ CRITICAL
    - **Impact:** Solo developer cannot provide round-the-clock issue resolution
    - **Implications:**
      - Tool must be highly reliable (minimal manual intervention needed)
      - Self-service documentation critical
      - Reasonable downtime acceptable for maintenance during off-peak hours
    - **Mitigation:** Comprehensive error messages, FAQ documentation, community support channels (Discord)

10. **Regulatory/Legal: GDPR, Data Privacy** ✅ LOW IMPACT (MVP)
    - **Impact:** If storing user data, must comply with privacy regulations
    - **MVP Mitigation:** No user accounts, no data persistence = minimal GDPR surface area
    - **V2 Consideration:** If adding accounts, must implement GDPR compliance (data export, deletion, consent)

### Key Assumptions

**Technical Assumptions:**

1. **PoE 2 Path of Building Will Remain Open-Source** ✅ HIGH CONFIDENCE
   - **Assumption:** Community fork of Path of Building will be available for PoE 2 with calculation engine accessible
   - **Rationale:** PoE 1 PoB has been open-source for years, strong community precedent
   - **Risk if Wrong:** Entire project infeasible without calculation engine access
   - **Validation:** Already confirmed via GitHub (PathOfBuildingCommunity/PathOfBuilding-PoE2 exists)

2. **Lupa + HeadlessWrapper.lua Integration Will Work for PoE 2 PoB** ✅ MEDIUM CONFIDENCE
   - **Assumption:** Research-validated Lupa patterns will work with PoE 2 PoB's HeadlessWrapper.lua
   - **Rationale:** Deep research shows pattern proven for PoE 1, architecture unlikely to change drastically
   - **Risk if Wrong:** Fallback to pob_wrapper (slower) or manual module extraction (complex)
   - **Validation:** Days 1-3 prototype explicitly validates this assumption (GO/NO-GO gate)

3. **Performance Target Achievable (150-500ms for 1000 Calculations)** ✅ HIGH CONFIDENCE
   - **Assumption:** Lupa deep research benchmarks apply to PoB calculations
   - **Rationale:** PoB calculations are pure Lua mathematical operations (ideal for LuaJIT)
   - **Risk if Wrong:** Optimization algorithms slower, user experience degraded
   - **Validation:** Prototype Day 2 measures real-world performance with PoB calculations

4. **Hill Climbing Algorithm Will Produce 5-15% Improvements** ⚠️ MEDIUM CONFIDENCE
   - **Assumption:** Simple hill climbing (without simulated annealing) sufficient for MVP
   - **Rationale:** Most players have suboptimal trees with low-hanging fruit (inefficient pathing)
   - **Risk if Wrong:** Tool delivers marginal value (<5% improvements), users unimpressed
   - **Validation:** Week 7 MVP testing with diverse real builds measures actual improvement distribution

**User/Market Assumptions:**

5. **Target Users Know What Path of Building Is** ✅ HIGH CONFIDENCE
   - **Assumption:** Primary audience (endgame min-maxers) already uses Path of Building regularly
   - **Rationale:** PoB is de facto standard for build planning in PoE community
   - **Risk if Wrong:** Onboarding friction higher, users don't understand PoB code input
   - **Validation:** User testing during soft launch reveals onboarding issues

6. **Users Trust Mathematical Optimization Over Manual Intuition** ⚠️ MEDIUM CONFIDENCE
   - **Assumption:** Players will accept algorithm recommendations even when counter-intuitive
   - **Rationale:** Gamers respect "math" and verifiable improvements (DPS numbers)
   - **Risk if Wrong:** Users reject recommendations, don't import optimized codes
   - **Mitigation:** Transparency (real-time progress), verification (import to PoB), honest limitations

7. **5-10% Performance Improvement Is Worth 2-5 Minutes of User Time** ✅ HIGH CONFIDENCE
   - **Assumption:** Players value efficiency gains, willing to wait briefly for optimization
   - **Rationale:** Players already spend hours manually optimizing, tool is 50-100x time saver
   - **Risk if Wrong:** Users abandon during optimization, completion rate <70%
   - **Validation:** Month 1 completion rate KPI measures actual tolerance

8. **Community Will Share Tool Organically If Valuable** ⚠️ MEDIUM CONFIDENCE
   - **Assumption:** No paid marketing budget, rely on word-of-mouth and Reddit/Discord mentions
   - **Rationale:** PoE community actively shares useful tools (PoB itself spread organically)
   - **Risk if Wrong:** Low user acquisition, tool remains niche
   - **Mitigation:** Soft launch post on r/pathofexile, engage with community, request feedback

**Business Assumptions:**

9. **MVP Success Doesn't Require Monetization** ✅ HIGH CONFIDENCE
   - **Assumption:** Free tool sufficient to validate product-market fit, monetization deferred to V2
   - **Rationale:** Focus is proving value and retention, not generating revenue in first 6 months
   - **Risk if Wrong:** None—no revenue target for MVP
   - **V2 Decision:** Only monetize if retention + engagement demonstrate strong PMF

10. **Solo Developer Can Execute Full Product Lifecycle** ✅ MEDIUM CONFIDENCE
    - **Assumption:** One person can research, design, build, launch, support, and iterate on MVP
    - **Rationale:** Ruthless scope discipline + leveraging existing tools (PoB, Lupa, FastAPI)
    - **Risk if Wrong:** Burnout, missed deadlines, quality compromises
    - **Mitigation:** 2-month hard deadline forces scope cuts, prototype validates highest risk first

**External Dependency Assumptions:**

11. **Path of Building Community Will Maintain PoE 2 Fork** ✅ HIGH CONFIDENCE
    - **Assumption:** PathOfBuildingCommunity GitHub org will continue maintaining PoE 2 PoB
    - **Rationale:** PoE 1 PoB has been maintained for years, PoE 2 is bigger opportunity
    - **Risk if Wrong:** Calculation engine becomes outdated or unavailable
    - **Mitigation:** Pin specific PoB version for MVP, monitor community health

12. **PoE 2 Balance Patches Won't Break HeadlessWrapper.lua** ⚠️ LOW CONFIDENCE
    - **Assumption:** Game balance changes affect calculations but not HeadlessWrapper API
    - **Rationale:** HeadlessWrapper is stable interface, calculation logic updates are internal
    - **Risk if Wrong:** MVP breaks after PoE 2 patch, requires urgent fixes
    - **Mitigation:** Comprehensive parity test suite detects breaking changes quickly, flexible deployment for hotfixes

**Assumption Validation Plan:**

- **Prototype (Days 1-3):** Validates assumptions #1, #2, #3 (technical feasibility)
- **MVP Testing (Week 7):** Validates assumptions #4, #5, #7 (algorithm effectiveness, user behavior)
- **Month 1 KPIs:** Validates assumptions #6, #8, #9 (trust, sharing, monetization-free viability)
- **Month 3 Review:** Validates assumption #10 (solo developer sustainability)

**Contingency Planning:**

- **If Assumption #2 Fails (Lupa integration):** Fallback to pob_wrapper (slower but functional)
- **If Assumption #4 Fails (algorithm effectiveness):** Upgrade to simulated annealing mid-MVP
- **If Assumption #6 Fails (user trust):** Increase transparency messaging, add verification features
- **If Assumption #8 Fails (organic sharing):** Small paid marketing test ($50-100 Reddit ads)

---

## Risks and Open Questions

### Key Risks

**Technical Risks:**

1. **HIGHEST RISK: Headless PoB Integration Fails** ⚠️ CRITICAL - PROJECT BLOCKER
   - **Description:** Lupa + HeadlessWrapper.lua integration doesn't work as expected for PoE 2 PoB
   - **Impact:** Entire project infeasible without calculation engine
   - **Likelihood:** MEDIUM (validated in PoE 1 research, but PoE 2 untested)
   - **Mitigation Strategy:**
     - **Days 1-3 Prototype:** Explicit validation before full MVP investment
     - **Fallback Option 1:** Use pob_wrapper (slower but proven for PoE 1)
     - **Fallback Option 2:** Manual PoB module extraction (more complex, higher maintenance)
     - **Nuclear Option:** Project pivot if all approaches fail
   - **Contingency Budget:** 3 days allocated to validate, 1 day buffer if prototype needs troubleshooting

2. **HIGH RISK: Algorithm Delivers Weak Improvements (<5%)** ⚠️ VALUE PROPOSITION FAILURE
   - **Description:** Hill climbing produces marginal gains users don't care about
   - **Impact:** Users try once, never return—PMF failure
   - **Likelihood:** LOW-MEDIUM (most builds have inefficient pathing, but depends on input quality)
   - **Mitigation Strategy:**
     - **Week 7 Testing:** Test with 20-30 diverse real builds, measure improvement distribution
     - **If median <5%:** Upgrade to simulated annealing before launch
     - **User Expectation Management:** Honest messaging—"5-15% typical, depends on starting tree"
   - **Indicators:** Median improvement in test builds, user feedback during soft launch

3. **MEDIUM RISK: Performance Worse Than Expected** ⚠️ UX DEGRADATION
   - **Description:** Optimizations take >5 minutes, users abandon before completion
   - **Impact:** Low completion rate (<70%), poor user experience
   - **Likelihood:** LOW (research shows 150-500ms for 1000 calcs achievable, ample headroom)
   - **Mitigation Strategy:**
     - **Prototype Day 2:** Measure real-world performance with complex builds
     - **If slow:** Optimize hot paths (localize functions, pre-allocate tables, reduce boundary crossings)
     - **UX Mitigation:** Clear time estimates ("Optimizing complex build: ~4 minutes"), progress bar
   - **Acceptable Range:** 1-2 minutes for simple builds, 3-5 minutes for complex builds

4. **MEDIUM RISK: PoB Update Breaks Compatibility** ⚠️ MAINTENANCE BURDEN
   - **Description:** Path of Building releases breaking change to HeadlessWrapper or calculation logic
   - **Impact:** Optimizer produces wrong results or crashes, trust destroyed
   - **Likelihood:** MEDIUM (PoB updates frequently with game patches)
   - **Mitigation Strategy:**
     - **Pin PoB Version:** MVP uses specific tested PoB commit, controlled updates
     - **Parity Test Suite:** Automated tests compare optimizer results vs. PoB GUI
     - **Monitoring:** Subscribe to PoB GitHub releases, test new versions before upgrading
     - **Rollback Plan:** Keep previous PoB version available if update causes issues
   - **Response Time:** Critical fixes within 24-48 hours for breaking changes

5. **LOW RISK: Lua Memory Leaks or Crashes** ⚠️ RELIABILITY ISSUE
   - **Description:** Long-running optimizations cause memory exhaustion or Lua runtime crashes
   - **Impact:** Failed optimizations, server instability
   - **Likelihood:** LOW (Lupa mature, error handling patterns documented)
   - **Mitigation Strategy:**
     - **Memory Limits:** LuaRuntime max_memory=100MB per session
     - **Timeout Protection:** Kill optimization after 10 minutes
     - **Graceful Degradation:** Catch exceptions, return partial results if possible
     - **Process Isolation:** Each optimization in separate thread/process (V2)

**Product/Market Risks:**

6. **HIGH RISK: Users Don't Trust Black-Box Recommendations** ⚠️ ADOPTION BARRIER
   - **Description:** Users reject algorithm suggestions because they don't understand reasoning
   - **Impact:** Low PoB code import rate (<40%), users view tool as novelty not utility
   - **Likelihood:** MEDIUM (trust is hard-earned in gaming communities)
   - **Mitigation Strategy:**
     - **Transparency:** Real-time progress messages show algorithm thinking
     - **Verification:** Users import to PoB and see exact node changes
     - **Honest Limitations:** "Minion builds not yet supported" builds credibility
     - **Community Validation:** Respected players/streamers endorse tool
   - **Early Warning Signs:** Month 1 import rate <40%, negative Reddit sentiment

7. **MEDIUM RISK: Competition Launches First** ⚠️ MARKET TIMING
   - **Description:** Another developer releases similar tool 2-4 weeks before MVP launch
   - **Impact:** Reduced first-mover advantage, harder user acquisition
   - **Likelihood:** LOW-MEDIUM (no known competitors building tree optimizer)
   - **Mitigation Strategy:**
     - **Speed:** Aggressive 2-month timeline captures early-league window
     - **Differentiation:** Focus + transparency + trust = competitive moat even if second
     - **Collaboration:** Reach out to competitor for potential collaboration vs. competition
   - **Response:** If competitor emerges, analyze their approach, differentiate on trust/quality

8. **MEDIUM RISK: Low User Acquisition (Organic Growth Fails)** ⚠️ DISCOVERY PROBLEM
   - **Description:** Reddit post gets buried, community doesn't share tool organically
   - **Impact:** <1,000 users Month 1, insufficient data to validate PMF
   - **Likelihood:** MEDIUM (depends on messaging quality, community reception)
   - **Mitigation Strategy:**
     - **Compelling Messaging:** "I saved 3 hours of tree optimization—here's proof" vs. "I built a tool"
     - **Multiple Channels:** Reddit, Discord, official forums, build guide sites
     - **Community Engagement:** Respond to feedback, iterate quickly, build relationships
     - **Paid Boost:** Small Reddit ad spend ($50-100) if organic fails
   - **Early Warning Signs:** <500 users Week 1, <5 community mentions

9. **LOW RISK: League Mechanics Change Optimization Priorities** ⚠️ META SHIFT
   - **Description:** PoE 2 patch changes meta (e.g., defense becomes more important than DPS)
   - **Impact:** "Maximize DPS" goal less relevant, user needs shift
   - **Likelihood:** LOW-MEDIUM (meta shifts happen but tree optimization remains valuable)
   - **Mitigation Strategy:**
     - **Flexible Goals:** Support multiple optimization objectives (DPS, EHP, hybrid)
     - **Community Feedback:** Monitor what goals users request, add popular ones quickly
     - **V2 Feature:** Multi-objective optimization addresses all meta shifts

**Operational Risks:**

10. **MEDIUM RISK: Solo Developer Burnout** ⚠️ SUSTAINABILITY THREAT
    - **Description:** 300-hour MVP sprint + ongoing support causes exhaustion, quality degrades
    - **Impact:** Missed deadlines, bugs, poor user support, project abandonment
    - **Likelihood:** MEDIUM (common for solo projects)
    - **Mitigation Strategy:**
      - **Scope Discipline:** Ruthlessly cut features to protect timeline
      - **Time Boundaries:** Max 40-50 hours/week, avoid crunch mode
      - **Breaks:** Take 2-3 days off after MVP launch before V2 planning
      - **Community Help:** Leverage Discord for peer support, potential contributors
    - **Early Warning Signs:** Missing weekly milestones, declining code quality, frustration

11. **LOW RISK: Server Costs Spiral Out of Control** ⚠️ FINANCIAL CONSTRAINT
    - **Description:** Viral growth causes hosting bills to exceed $200 budget
    - **Impact:** Need to shut down service or introduce monetization prematurely
    - **Likelihood:** LOW (good problem to have—means tool is successful)
    - **Mitigation Strategy:**
      - **Usage Limits:** Rate limiting (10 optimizations per IP per hour)
      - **Graceful Degradation:** Queue system if server overwhelmed
      - **Vertical Scaling First:** Bigger VPS ($20-50/month) before complex infrastructure
      - **Monetization:** If sustained high usage, introduce donations or premium tier

### Open Questions

**Technical Questions:**

1. **What's the actual improvement distribution for real builds?**
   - **Why Unknown:** Haven't tested algorithm with diverse PoE 2 builds yet
   - **Impact:** Determines if MVP delivers promised value
   - **When Answered:** Week 7 testing with 20-30 real builds
   - **Research Needed:** Collect sample builds from community, run optimizations, analyze improvement percentiles

2. **How many concurrent optimizations can a single VPS handle?**
   - **Why Unknown:** Haven't load-tested under realistic conditions
   - **Impact:** Determines when to scale infrastructure
   - **When Answered:** Week 8 load testing before launch
   - **Research Needed:** Simulate 10, 20, 50 concurrent optimization requests, measure CPU/memory/response times

3. **What percentage of PoE 2 builds are compatible with MVP algorithm?**
   - **Why Unknown:** Don't know distribution of build types (self-cast vs. minion vs. trigger)
   - **Impact:** Determines addressable market size
   - **When Answered:** Month 1 based on user submissions (track rejection reasons)
   - **Research Needed:** Instrument backend to log build characteristics, categorize compatibility

4. **Should optimization be synchronous or async for MVP?**
   - **Why Unknown:** Trade-off between implementation complexity and scalability
   - **Current Plan:** Synchronous (simpler MVP)
   - **Decision Point:** Week 5—if optimization times >5 minutes, consider async
   - **Research Needed:** Prototype both approaches, measure development overhead vs. UX benefit

**Product/UX Questions:**

5. **What level of transparency do users actually want?**
   - **Why Unknown:** Research suggests "trust through transparency" but unclear how much detail is optimal
   - **Options:**
     - Minimal: Just show progress bar
     - Moderate: High-level messages ("Evaluating nodes...")
     - Detailed: Specific nodes being tested, intermediate DPS values
   - **When Answered:** Month 1 user feedback and A/B testing
   - **Research Needed:** Test 2-3 messaging levels, measure completion rate + user satisfaction

6. **Do users want "explain changes" feature in MVP or V2?**
   - **Why Unknown:** Nice-to-have but adds complexity
   - **Current Plan:** Defer to V2
   - **Decision Point:** Soft launch feedback—if users frequently ask "why did it change this?", prioritize
   - **Trade-off:** MVP simplicity vs. user understanding

7. **Should MVP support mobile/tablet or desktop-only?**
   - **Why Unknown:** Don't know if users would optimize on mobile
   - **Current Plan:** Desktop-only (responsive but not optimized for mobile)
   - **Decision Point:** Month 1 analytics—if >20% mobile traffic, invest in mobile UX
   - **Research Needed:** Check analytics for device breakdown

8. **What error messages are most helpful when optimization fails?**
   - **Why Unknown:** Don't know common failure modes yet
   - **Current Plan:** Generic messages initially, refine based on real errors
   - **When Answered:** Month 1 error logs + user feedback
   - **Research Needed:** Categorize failure modes, craft specific helpful messages

**Business/Strategy Questions:**

9. **What monetization model (if any) makes sense post-MVP?**
   - **Options:**
     - Freemium (basic free, premium features $5-10/month)
     - Pay-per-use (credits for optimizations)
     - Donations (Patreon/Ko-fi)
     - Free forever (community contribution)
   - **Current Plan:** Free for MVP, decide after PMF validation
   - **Decision Point:** Month 6—if retention strong (30%+ repeat usage), explore monetization
   - **Research Needed:** Survey users about willingness to pay, test pricing sensitivity

10. **Is there appetite for enterprise/creator licensing (streamers, guide sites)?**
    - **Why Unknown:** Don't know if content creators would pay for API access or white-label
    - **Current Plan:** Defer until V2
    - **Decision Point:** If 3+ streamers/creators request integration, explore B2B model
    - **Potential Value:** Recurring revenue, broad audience reach through partnerships

11. **Should we prioritize PoE 1 backward compatibility or PoE 2 exclusive?**
    - **Why Unknown:** PoE 1 has larger user base but PoE 2 is the future
    - **Current Plan:** PoE 2 exclusive (smaller market but less competition)
    - **Decision Point:** Month 6—if PoE 2 user base too small, consider PoE 1 port
    - **Trade-off:** Focus vs. market size

12. **What's the long-term vision—single tool or platform?**
    - **Options:**
      - Stay focused: Best-in-class passive tree optimizer forever
      - Expand: Comprehensive PoE 2 build optimization suite
      - Platform: API/infrastructure for third-party tools
    - **Current Plan:** Focus for MVP, reassess after PMF
    - **Decision Point:** Month 12—if MVP successful, explore adjacent problems

### Areas Needing Further Research

**Before MVP Launch:**

1. **Community Sentiment on Tree Optimization Tools** 📊 MEDIUM PRIORITY
   - **Research Question:** Do players want this? What have they tried? What frustrated them?
   - **Action:** Search Reddit/Discord for "tree optimization" discussions, analyze feedback
   - **Value:** Informs messaging, feature priorities, differentiation strategy
   - **Deadline:** Week 1 (guides brainstorming session validation)

3. **Competitive Landscape** 🔍 LOW PRIORITY
   - **Research Question:** Are others building similar tools? What's their approach?
   - **Action:** Monitor PoE 2 tool ecosystem, GitHub searches, community announcements
   - **Value:** Identifies collaboration opportunities, differentiation needs
   - **Ongoing:** Passive monitoring throughout MVP development

**Post-Launch Research (Month 1-3):**

4. **User Behavior Analysis** 📈 HIGH PRIORITY
   - **Research Question:** How do users actually use the tool? Where do they drop off?
   - **Action:** Analyze analytics (funnel conversion, time to complete, repeat usage patterns)
   - **Value:** Identifies UX friction points, guides V2 priorities
   - **Timeline:** Weekly review during Month 1

5. **Improvement Distribution Study** 📊 HIGH PRIORITY
   - **Research Question:** What's the actual distribution of improvements delivered? (5th, 50th, 95th percentile)
   - **Action:** Log optimization results (anonymized), analyze improvement statistics
   - **Value:** Validates value proposition, informs marketing messaging
   - **Timeline:** Continuous collection, analyze at Month 1

6. **Feature Request Prioritization** 💡 MEDIUM PRIORITY
   - **Research Question:** What features do users request most? Which have highest impact?
   - **Action:** Collect feedback (Discord, Reddit, post-optimization survey), categorize requests
   - **Value:** Guides V2 roadmap, ensures building what users actually want
   - **Timeline:** Ongoing collection, prioritization at Month 3

7. **Monetization Willingness Study** 💰 LOW PRIORITY (Month 6+)
   - **Research Question:** Would users pay? How much? For what features?
   - **Action:** Survey retained users, test pricing hypotheses
   - **Value:** Informs V2 monetization strategy (or confirms free-forever model)
   - **Timeline:** Month 6 (only if PMF validated)

**Technical Deep Dives (As Needed):**

8. **Simulated Annealing Performance Testing** ⚙️ CONDITIONAL
   - **Research Question:** How much better are results with SA vs. hill climbing? Is speed trade-off worth it?
   - **Trigger:** If MVP hill climbing delivers <8% median improvement
   - **Action:** Implement SA, run comparison study with same test builds
   - **Timeline:** Week 5-6 if needed

9. **Horizontal Scaling Architecture** 🏗️ CONDITIONAL
   - **Research Question:** What's the optimal architecture for 100+ concurrent users?
   - **Trigger:** Single server CPU >80% sustained or response times degrade
   - **Action:** Research async job queues (Celery, RQ), load balancing, caching strategies
   - **Timeline:** Month 3-6 if traffic warrants

**Community Research (Ongoing):**

10. **Build Archetype Distribution Study** 🎮 MEDIUM PRIORITY
    - **Research Question:** What % of builds are self-cast/attack vs. minion vs. trigger?
    - **Action:** Analyze PoB code submissions (anonymized), categorize build types
    - **Value:** Determines priority for expanding build type support in V2
    - **Timeline:** Month 1-3 data collection, analyze at Month 3

11. **Trust Signal Effectiveness Study** 🤝 MEDIUM PRIORITY
    - **Research Question:** Which trust signals matter most? (Progress messages, PoB verification, limitation disclaimers)
    - **Action:** A/B test messaging variations, measure import rate + NPS
    - **Value:** Optimizes UX for trust-building
    - **Timeline:** Month 2-3 experiments

**Research Prioritization Framework:**

- **URGENT (Before Launch):** Competitive landscape scan, community sentiment
- **HIGH (Month 1):** User behavior, improvement distribution
- **MEDIUM (Month 2-3):** Feature requests, build archetype distribution
- **LOW (Month 6+):** Monetization willingness, horizontal scaling deep dive

**Research Budget:**
- **Time Investment:** 5-10 hours/week for analytics review, feedback analysis, documentation
- **Tools:** Google Analytics/Plausible (free/cheap), Discord (free), Reddit monitoring (free)
- **Cost:** $0-20/month (analytics tool subscription)

---

## Appendices

### A. Research Summary

This Product Brief synthesizes insights from comprehensive research conducted October 6-8, 2025, comprising four major research documents:

#### 1. Brainstorming Session Results (2025-10-06)

**Methodologies Applied:**
- First Principles Thinking (creative exploration)
- SCAMPER Method (structured ideation)
- What If Scenarios (risk analysis)
- Stakeholder Round Table (multi-perspective validation)
- Tree of Thoughts (algorithm exploration)
- Reverse Engineering (implementation path mapping)

**Key Outputs:**
- **MVP Definition:** "The Passive Tree Grinder"—ruthlessly focused tool optimizing only passive trees, not full builds
- **Scope Discipline:** Eliminated AI chat, user accounts, API imports, complex build types → reduced 12-month project to 2 months
- **Trust Framework:** "Trust is the actual product, not the algorithm"—transparency, verification, honest limitations
- **Budget Constraint System:** Essential feature to prevent suggesting financially impossible builds
- **Stakeholder Alignment:** All personas (min-maxers, skeptics, casuals, PoB developers, solo dev) want same thing: focused, honest tool

**Critical Insights:**
- **80/20 Rule is 95/5 in PoE:** Supporting simple builds (self-cast/attack) = 80%+ users, minion/trigger adds 300% complexity for 15%
- **External Dependencies = Existential Risks:** PoB open-source status manageable, GGG account API unmanageable
- **The 2-Month MVP Philosophy:** An MVP isn't "final product with fewer features"—it's "smallest thing solving real problem completely"

**Strategic Priorities Identified:**
1. **Priority #1:** Prototype Headless PoB Integration (highest risk, blocks all downstream work)
2. **Priority #2:** Build MVP "Passive Tree Grinder" (Steps 0-7 reverse-engineered path)
3. **Priority #3:** Implement Budget Constraint System (essential for real-world usability)

#### 2. Technical/Architecture Research (2025-10-07, Updated 2025-10-08)

**Research Scope:** Evaluated 5 approaches for headless Path of Building integration

**Options Evaluated:**
1. **Python + Lupa (Embedded LuaJIT)** → RECOMMENDED
2. **Python + pob_wrapper (Headless PoB Process)** → Fallback
3. **Python + PathOfBuildingAPI** → ELIMINATED (parse-only, no calculations)
4. **Node.js + Fengari** → ELIMINATED (abandoned, poor performance)
5. **Standalone Lua + IPC** → ELIMINATED (too complex for MVP)

**Decision Framework:**
- **Priority Weighting:** Risk Mitigation > Reliability & Accuracy > Implementation Feasibility
- **Winner (Risk Mitigation):** Initially pob_wrapper (lowest risk, uses official PoB)
- **Revised Recommendation (2025-10-08):** Lupa + HeadlessWrapper.lua (after deep research discovery)

**Architecture Decision Record (ADR-001):**
- **Dual-Track Prototype Strategy:**
  - Day 1: Test pob_wrapper with PoE 2 PoB (quick validation)
  - Day 2-3: If pob_wrapper fails, implement Lupa + PoB module extraction
- **Updated Strategy (2025-10-08):** HeadlessWrapper.lua discovery changed recommendation to Lupa-first approach

**Key Findings:**
- **pob_wrapper Issues:** Version compatibility problems, fragile headless mode, unknown PoE 2 support
- **Lupa Strengths:** Excellent performance, stable library, production-ready
- **Performance Validation:** <1ms calculations possible, sufficient for iterative optimization algorithms
- **Critical Bottleneck:** Headless PoB integration is highest technical risk—must prototype first

#### 3. Lupa Library Deep Research (2025-10-08) **CRITICAL DISCOVERY**

**Research Focus:** Production implementation patterns for Python-LuaJIT integration with Path of Building

**CRITICAL DISCOVERY: HeadlessWrapper.lua**
- Path of Building **already includes** `HeadlessWrapper.lua` specifically designed for headless execution
- PoB developers anticipated this use case—infrastructure already exists
- **Impact:** Changes recommendation from "extract modules manually" to "use HeadlessWrapper.lua + stubs"

**Performance Benchmarks (Validated):**
- **Single Calculation:** 1-10ms for complex builds with all mechanics
- **1000 Calculations (Batch):** 150-500ms (0.15-0.5ms average)
- **Memory Usage:** 1-10 MB depending on build complexity
- **Verdict:** ✅ Performance target (<1 second) EASILY ACHIEVABLE

**Implementation Patterns Documented:**
1. **Multi-Stage Initialization:** Version selection (LuaJIT fallback chain), package path configuration, pre-load core modules
2. **Data Transfer:** Use `table_from()` with recursive conversion for nested structures (single boundary crossing)
3. **HeadlessWrapper Pattern:** Load wrapper + implement required stub functions (Deflate/Inflate, ConPrintf, system stubs)
4. **Batch Processing:** Pre-compile functions once, reuse for 1000+ calls
5. **Error Handling:** Multi-layer strategy (Lua xpcall + Python try-catch)
6. **Memory Management:** Set limits (100MB), periodic GC, monitor usage

**Production Deployment Patterns:**
- **Platform Strategy:** Use Debian-based Docker images (binary wheels work out-of-box), avoid Alpine
- **Linux Symbol Visibility:** Set dlopen flags before importing Lupa (fixes "undefined symbol" errors)
- **Monitoring:** Track Lua memory usage, calculation latency, error rate by type

**Production Readiness Assessment:**
- **Lupa Library:** ✅ Production-ready (13 years, active maintenance, Python 3.8-3.13, binary wheels)
- **PoB Integration:** ✅ Feasible with HeadlessWrapper (proven approach, minimal stubs)
- **Timeline:** 1 week to POC, 5-8 weeks to production

**Code Examples Provided:**
- Complete HeadlessWrapper integration (lines 1128-1283)
- Batch calculation optimizer (lines 249-305)
- Error handling patterns (lines 396-458)
- Memory management (lines 742-786)

#### 4. Research Summary Document (2025-10-08)

**Purpose:** Consolidate findings and provide 3-day prototype execution plan

**Final Recommendation:** ✅ **PRIMARY APPROACH: Lupa + HeadlessWrapper.lua**

**Rationale:**
1. HeadlessWrapper.lua exists—designed for this exact use case
2. 100% calculation accuracy—uses official PoB code directly
3. Performance target met—150-500ms for 1000 calculations
4. Low maintenance—PoB updates work automatically
5. Production ready—Lupa mature, binary wheels available

**3-Day Prototype Plan (UPDATED):**

**Day 1: HeadlessWrapper.lua Approach (PRIMARY)**
- Clone PoE 2 PoB repository
- Install Lupa: `pip install lupa`
- Implement stub functions (Deflate/Inflate, Console, System)
- Load HeadlessWrapper.lua
- Test single build calculation
- Extract stats (Life, DPS, EHP, resistances)
- **Success Criteria:** Load build, execute calculation, extract stats matching PoB GUI

**Day 2: Batch Optimization (If Day 1 Succeeds)**
- Implement batch calculation mode
- Pre-compile Lua functions
- Test 100-1000 build variations
- Profile performance (confirm <1s target)
- Verify accuracy vs. PoB GUI (0.1% tolerance)
- **Success Criteria:** 1000 calculations in <1 second, 100% accuracy

**Day 3: Fallback to pob_wrapper (If Days 1-2 Fail)**
- Install pob_wrapper: `pip install pob_wrapper`
- Test with PoE 2 PoB (validate compatibility)
- Measure performance overhead
- Document findings
- **Outcome:** Use pob_wrapper (slower but works) OR PROJECT NOT FEASIBLE

**Performance Expectations Table:**

| Metric | Target | Expected (Lupa) | Expected (pob_wrapper) |
|--------|--------|-----------------|------------------------|
| Single calculation | < 1s | 5-20ms | 100-500ms |
| 1000 calculations | < 1s | 150-500ms | 100-500s (too slow) |
| Memory usage | Reasonable | 1-10 MB | Unknown |
| Accuracy | 100% | 100% | 100% |

**Critical Success Factors:**
1. ✅ Use HeadlessWrapper.lua (not manual module extraction)
2. ✅ Implement compression functions (Deflate/Inflate with Python zlib)
3. ✅ Pre-compile Lua functions for batch processing
4. ✅ Validate accuracy against PoB GUI (parity testing)
5. ✅ Set memory limits (100MB recommended)

**Lessons Learned:**
1. Research pays off—initial research suggested manual extraction, deep research revealed HeadlessWrapper.lua (game changer)
2. PoB has infrastructure—leverage their work, don't reinvent
3. Performance is achievable—1000 calculations in 150-500ms far exceeds requirement
4. Risk mitigation works—dual-track approach ensures fallback options
5. Deep research >> quick research—implementation-ready patterns vs. conceptual understanding

#### Research Synthesis

**Convergent Themes Across All Research:**

1. **Scope Discipline = Success**
   - Brainstorming: "Ruthless scope discipline is the competitive advantage"
   - Technical Research: "Eliminate features aggressively to hit 2-month timeline"
   - Deep Research: "HeadlessWrapper exists—leverage it, don't extract modules"

2. **Trust Through Transparency**
   - Brainstorming: "Trust is the actual product, not the algorithm"
   - Stakeholder Analysis: All users want "honest tool that does one job well"
   - Implementation: Real-time progress messages, PoB verification, limitation disclaimers

3. **Validate Highest Risk First**
   - Brainstorming: "Headless PoB integration is highest technical risk"
   - Technical Research: "Prototype bottleneck before building around it"
   - Deep Research: "Days 1-3 prototype explicitly validates assumption (GO/NO-GO gate)"

4. **Performance Target is Achievable**
   - Brainstorming: "<1 second per calculation for 1000+ calculations"
   - Technical Research: "Lupa provides 15-100x speedup vs. pure Python"
   - Deep Research: "150-500ms for 1000 calculations validated in benchmarks"

5. **External Dependencies Managed**
   - Brainstorming: "PoB open-source status is reliable, API integration is risky"
   - Technical Research: "Use pob_wrapper (battle-tested) or Lupa (full control)"
   - Deep Research: "HeadlessWrapper.lua + Lupa = no external dependencies beyond PoB"

**Research Quality Assessment:**
- **Comprehensiveness:** 4 documents, 3 days of research, 300+ pages of analysis
- **Depth:** Deep-dive on Lupa produced implementation-ready code patterns
- **Validation:** Benchmarks cited, production patterns documented, risks identified
- **Decision-Readiness:** Clear recommendation with prototype plan and success criteria

**Outstanding Validation Needed:**
- PoE 2 PoB HeadlessWrapper.lua compatibility (validates Days 1-3)
- Actual improvement distribution with real builds (validates algorithm effectiveness)
- User behavior and trust signals (validates product-market fit assumptions)

**Next Research Milestones:**
- **Day 3 (Post-Prototype):** Update ADR-001 with GO/NO-GO decision and findings
- **Week 7 (Pre-Launch):** Algorithm effectiveness study with 20-30 diverse builds
- **Month 1 (Post-Launch):** User behavior analysis, completion rate, improvement distribution
- **Month 3 (PMF Validation):** Repeat usage, NPS, community sentiment analysis

### B. Stakeholder Input

**Stakeholder Round Table Analysis** (from Brainstorming Session - 2025-10-06)

Five distinct stakeholder personas were analyzed to ensure MVP addresses diverse needs and concerns:

---

#### Persona 1: The Hardcore Min-Maxer (Primary Target User)

**Quote:** *"I've spent 2000 hours in PoE. I know my build is good, but I need PROOF it's optimal."*

**What They Value:**
- Mathematical rigor and transparency—show me the numbers
- Verification capability—I must be able to import result into PoB and see it's correct
- Marginal gains—even 3% improvement is worth it at endgame
- Time savings—I'd rather spend time playing than moving tree points for hours

**What They Fear:**
- Black box optimization—don't just give answer, show me WHY
- Breaking my build—if you reduce my EHP below safe thresholds, I can't trust you
- Wasting respec points—I have limited currency, don't make me regret using your tool

**Their Success Criteria:**
- "This tool found 8% more DPS I would never have discovered manually"
- "The before/after comparison is crystal clear and verifiable"
- "I can afford the suggested changes with my available respec points"

**How MVP Addresses Their Needs:**
- ✅ Uses official PoB calculation engine (mathematical rigor)
- ✅ Generated PoB code imports to PoB for verification (transparency)
- ✅ Budget constraint system respects available respec points
- ✅ Before/after comparison with percentage improvements
- ✅ Real-time progress messages show algorithm thinking

---

#### Persona 2: The Solo Developer (You—Product Creator)

**Quote:** *"I want to build something valuable without getting crushed by scope creep."*

**What You Value:**
- Shipping something real vs. talking about perfect systems forever
- Learning by doing—tackling hard technical challenges (Lua integration, optimization algorithms)
- Community contribution—giving back to PoE community
- Sustainable scope—2 months to MVP, not 2 years to "complete"

**What You Fear:**
- Analysis paralysis—spending months planning instead of building
- Feature request death spiral—users wanting items, gems, full build generation
- Building on shaky foundations—if headless PoB integration impossible, everything collapses
- Burning out on overscoped project that never launches

**Your Success Criteria:**
- "I launched working MVP in 2 months"
- "Users are actually getting value from it"
- "The technical challenges taught me valuable skills"
- "I can add features incrementally without rewriting everything"

**How MVP Addresses Your Needs:**
- ✅ 2-month timeline with ruthless scope discipline
- ✅ Days 1-3 prototype validates technical foundation before full investment
- ✅ Clear feature boundaries (passive trees only, defer everything else)
- ✅ Extensible architecture (can add multi-objective, historical tracking in V2)

---

#### Persona 3: The Skeptical Veteran Player

**Quote:** *"I've seen a dozen 'revolutionary PoE tools' that died in beta. Why should I trust this?"*

**What They Value:**
- Proven track record—show me it works, don't promise vaporware
- Respecting game complexity—PoE is deep, don't oversimplify
- Honest limitations—tell me what you DON'T support upfront
- No bloat—I don't need 50 features, I need ONE thing that works perfectly

**What They Fear:**
- Another dead project—investing time learning tool that gets abandoned
- Bad recommendations—optimizer that doesn't understand build synergies gives garbage advice
- Hype without substance—"AI-powered" means nothing if results are wrong
- Privacy/security issues—I'm not giving you my account credentials

**Their Success Criteria:**
- "This tool has been working reliably for 3+ months"
- "Other experienced players vouch for it"
- "It admits when it can't help (e.g., 'minion builds not yet supported')"
- "It's brutally simple—paste code, get result, done"

**How MVP Addresses Their Needs:**
- ✅ Uses official PoB calculations (not custom formulas that could be wrong)
- ✅ Honest limitation disclaimers ("minion builds not yet supported")
- ✅ Simple UX—text box, dropdown, button, results (no feature bloat)
- ✅ No account required, no API integration (respects privacy)
- ✅ 2-month timeline reduces vaporware risk (ship fast or fail fast)

---

#### Persona 4: The Casual Leveling Player (Secondary User)

**Quote:** *"I'm level 40 and my tree already feels messy. Can this help me?"*

**What They Value:**
- Simplicity—I don't understand all the terminology yet
- Clear improvement—just tell me if this makes my character better
- Low commitment—I don't want to spend an hour figuring out your tool
- Safety—I'm scared of breaking my build

**What They Fear:**
- Overwhelming complexity—too many options, too much jargon
- Making things worse—what if "optimized" tree ruins my character?
- Wasting resources—respec points are precious and I don't have many
- Not understanding why—if I don't learn from this, I'm just cargo-culting

**Their Success Criteria:**
- "I pasted my code, clicked optimize, and got +15% damage—easy!"
- "The tool explained the changes in simple terms"
- "It only asked me to respec 5 points, which I can afford"
- "I feel smarter about tree building after using it"

**How MVP Addresses Their Needs:**
- ✅ Simple dropdown (no jargon—"Maximize DPS" vs. technical terms)
- ✅ Clear before/after with percentage improvements (easy to understand)
- ✅ Budget constraint system respects limited respec points
- ⚠️ Deferred to V2: "Explain changes" feature (nice-to-have but adds complexity)

---

#### Persona 5: The Path of Building Community Developer

**Quote:** *"Your tool sits on top of our work. We're allies, not competitors."*

**What They Value:**
- Attribution and respect—acknowledge that PoB makes this possible
- Bug reports upstream—if you find issues in our calculations, tell us
- Open collaboration—maybe we can integrate your optimizer into PoB someday
- Not fragmenting ecosystem—don't create competing standards

**What They Fear:**
- Misrepresentation—users thinking your tool IS Path of Building
- Blame for your bugs—"the optimizer gave wrong numbers" when it's your parsing error
- Ecosystem fragmentation—multiple incompatible build formats
- Lack of understanding—using PoB code without understanding mechanics

**Their Success Criteria:**
- "This tool drives more users to understand and use PoB properly"
- "They're citing PoB as calculation source and contributing back"
- "They're not breaking or misusing the PoB format"
- "We're collaborating on improving both tools"

**How MVP Addresses Their Needs:**
- ✅ Uses official PoB HeadlessWrapper.lua (respects their architecture)
- ✅ Clear attribution: "Powered by Path of Building calculation engine"
- ✅ Parity testing ensures calculations match PoB (catches bugs)
- ✅ Encourages PoB usage (users verify results by importing to PoB)
- ✅ Open to collaboration (GitHub repository, community engagement)

---

#### Stakeholder Alignment Analysis

**Key Finding:** All stakeholders want the SAME thing—**a tool that does one thing correctly and honestly communicates its limitations.**

**Convergent Needs:**
- **Min-Maxers:** Transparency, verification, budget constraints, mathematical proof
- **Solo Developer:** Ruthless scope discipline, 2-month MVP, extensible architecture
- **Skeptics:** Honest limitations, brutally simple UX, no hype, proven reliability
- **Casuals:** Clear explanations, safe defaults, "it just works" experience
- **PoB Developers:** Attribution, bug reporting upstream, format compatibility, collaboration

**The conflicts are imaginary.** Shipping a focused, transparent, well-scoped MVP satisfies everyone.

**Validation Strategy:**
- **Min-Maxers:** Measure completion rate, PoB import rate, repeat usage
- **Solo Developer:** Hit 2-month timeline, sustainable workload, learn Lupa/algorithms
- **Skeptics:** Track community sentiment (Reddit/Discord mentions), reliability metrics
- **Casuals:** Month 1 completion rate for lower-level characters (<85), user feedback
- **PoB Developers:** Reach out post-launch for feedback, report any calculation discrepancies

**Stakeholder Communication Plan:**
- **Min-Maxers:** Reddit post with proof (screenshot showing improvement), respond to technical questions
- **Skeptics:** Honest launch post ("here's what it does, here's what it doesn't, here's the proof")
- **Casuals:** Clear onboarding, simple messaging, minimal jargon
- **PoB Developers:** GitHub issue or Discord message: "Built optimizer using HeadlessWrapper.lua, here's our approach, happy to collaborate"

### C. References

**Primary Research Documents:**
1. Brainstorming Session Results (2025-10-06): `D:\poe2_optimizer_v6\docs\brainstorming-session-results-2025-10-06.md`
2. Technical Research Report (2025-10-07): `D:\poe2_optimizer_v6\docs\technical-research-2025-10-07.md`
3. Lupa Library Deep Research (2025-10-08): `D:\poe2_optimizer_v6\docs\LupaLibraryDeepResearch.md`
4. Research Summary (2025-10-08): `D:\poe2_optimizer_v6\docs\README-Research-Summary.md`

**Technical Documentation:**
- Lupa GitHub Repository: https://github.com/scoder/lupa
- Lupa PyPI Package: https://pypi.org/project/lupa/
- LuaJIT Documentation: https://luajit.org/
- LuaJIT FFI Library: https://luajit.org/ext_ffi.html

**Path of Building Resources:**
- PoE 2 PoB Repository: https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2
- PoE 1 PoB Repository: https://github.com/PathOfBuildingCommunity/PathOfBuilding
- PoB Community Website: https://pathofbuilding.community/
- PoB Documentation: https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/blob/dev/docs/rundown.md

**Alternative Integration Approaches:**
- pob_wrapper GitHub: https://github.com/coldino/pob_wrapper
- PathOfBuildingAPI GitHub: https://github.com/ppoelzl/PathOfBuildingAPI
- Fengari (Lua in JS): https://fengari.io/

**Performance Benchmarks:**
- LuaJIT Benchmarks: https://gitspartv.github.io/LuaJIT-Benchmarks/
- Programming Language Benchmarks (Lua): https://programming-language-benchmarks.vercel.app/lua
- Lupa Performance Blog Post: https://brmmm3.github.io/posts/2019/07/28/python_and_lua/

**Community Resources:**
- r/pathofexile Subreddit: https://reddit.com/r/pathofexile
- Path of Exile Official Website: https://pathofexile.com
- Path of Exile 2 Early Access Info: https://pathofexile.com/poe2

**Software Engineering References:**
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Python 3.11+ Documentation: https://docs.python.org/3/
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/

**Product Management Frameworks:**
- Lean Startup Methodology (MVP, Build-Measure-Learn)
- Jobs to Be Done Framework (user needs analysis)
- First Principles Thinking (problem decomposition)
- SCAMPER Ideation Technique (feature exploration)

**Research Methodologies:**
- BMad Research Workflow - Technical Research v2.0
- BMad Brainstorming Framework (CIS)
- Architecture Decision Records (ADR) format

**Tools and Libraries:**
- Lupa 2.5+ (Python-LuaJIT integration)
- FastAPI (Python web framework)
- Plausible or Google Analytics 4 (analytics)
- Sentry (error tracking)
- GitHub Actions (CI/CD)

**Deployment Platforms:**
- Hetzner Cloud (VPS hosting)
- DigitalOcean (VPS hosting)
- Railway (serverless deployment)
- Render (serverless deployment)
- Vercel (frontend hosting)

**Related Projects:**
- pob_wrapper: Python subprocess wrapper for headless PoB (PoE 1)
- PathOfBuildingAPI: Python parser for PoB codes (parse-only, no calculations)
- PoBExporter: Python library for PoB exports from PoE API

**Monitoring and Observability:**
- Sentry (error tracking): https://sentry.io/
- Plausible Analytics (privacy-friendly): https://plausible.io/
- Google Analytics 4 (comprehensive tracking): https://analytics.google.com/

**Open Questions Requiring External Research:**
- PoE 2 league launch schedule (monitor official announcements)
- Community sentiment on tree optimization tools (Reddit/Discord search)
- Competitive landscape (monitor PoE 2 tool ecosystem)

---

_This Product Brief serves as the foundational input for Product Requirements Document (PRD) creation._

_Next Steps: Handoff to Product Manager for PRD development using the `workflow prd` command._
