# Prep Sprint Task #4: Test Corpus Status

**Task:** Pull Maxroll builds for test corpus (20-30 builds)
**Status:** 🟡 FRAMEWORK READY - Awaiting Alec's Population
**Owner:** Alec
**Critical Path:** YES - Blocks Task #5 and Epic 2 validation

---

## What's Been Done

✅ **Framework Created:**
- Test corpus directory structure
- `corpus.json` template file
- Validation script (`validate_corpus.py`)
- Comprehensive README with instructions
- Metadata schema defined

✅ **Maxroll Build List Identified:**
11 builds available on Maxroll (listed in README)

---

## What's Needed from Alec

**Estimated Time:** 2-4 hours

### Tasks:
1. **Collect 10-15 Maxroll Builds** (1-2 hours)
   - Visit https://maxroll.gg/poe2/build-guides
   - Export PoB codes from build guides
   - Record metadata (level, class, allocated points)

2. **Add 5-10 Personal Builds** (30 minutes)
   - Export from your PoB collection
   - Include "known inefficient" builds for testing
   - Document inefficiencies in notes field

3. **Create 3-5 Synthetic Builds** (30 minutes)
   - Fully optimal (convergence testing)
   - Edge cases (weird allocations)
   - Max budget (no room for improvement)

4. **Populate corpus.json** (30 minutes)
   - Fill in all metadata fields
   - Run validation script
   - Fix any errors

---

## Files Created

```
tests/fixtures/optimization_builds/
├── README.md              # Complete instructions
├── corpus.json            # Empty template (populate this!)
└── validate_corpus.py     # Validation script
```

---

## How to Complete

1. **Read:** `tests/fixtures/optimization_builds/README.md`
2. **Populate:** `tests/fixtures/optimization_builds/corpus.json`
3. **Validate:** Run `python tests/fixtures/optimization_builds/validate_corpus.py`
4. **Commit:** Once validation passes

---

## Blocking Impact

**Task #5:** Establish Epic 2 baseline stats
- Cannot run without test corpus
- Blocks "8%+ median improvement" validation

**Stories 2.1-2.8:**
- Integration tests need test corpus
- Acceptance criteria validation depends on corpus

---

## Prep Sprint Status

**Completed Tasks (3/10):**
- ✅ Task 1: Validate passive points formula
- ✅ Task 2: Profile PassiveTreeGraph
- ✅ Task 3: Create optimizer architecture

**Current Task:**
- 🟡 Task 4: Test corpus (framework ready, needs population)

**Blocked Tasks:**
- 🔴 Task 5: Baseline stats (depends on Task 4)

**Available Tasks:**
- 🟢 Task 6: Research hill climbing
- 🟢 Task 7: Define Story 2.8 scope
- 🟢 Task 8: Triage backlog
- 🟢 Task 9: Update tech spec
- 🟢 Task 10: Update README

---

**Created by:** Bob (Scrum Master)
**Date:** 2025-10-27
**Next Action:** Alec to populate corpus.json
