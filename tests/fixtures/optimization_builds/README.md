# Optimization Test Corpus

**Purpose:** Collection of diverse PoE 2 builds for Epic 2 validation and testing.

**Owner:** Alec (to populate with actual PoB codes)
**Created:** 2025-10-27 (Prep Sprint Task #4)
**Status:** 🔴 INCOMPLETE - Requires Alec's input

---

## Target: 20-30 Builds

### Source Distribution

1. **Maxroll Builds (10-15 builds)** - High-quality, diverse archetypes
2. **Personal Builds (5-10 builds)** - Include "known inefficient" for optimization testing
3. **Synthetic Builds (3-5 builds)** - Already optimal or edge cases

---

## Required Metadata Per Build

Each build needs:

```json
{
  "build_id": "unique-identifier",
  "source": "maxroll" | "personal" | "synthetic",
  "name": "Storm Mage Lich",
  "url": "https://maxroll.gg/poe2/build-guides/storm-mage-lich-build-guide",
  "pob_code": "eNp...",  // Full Base64 PoB code
  "character_class": "Witch",
  "ascendancy": "Lich",
  "level": 85,
  "allocated_points": 98,
  "unallocated_points": 10,
  "archetype": "minion" | "spell" | "attack" | "hybrid",
  "notes": "Known inefficient - has 5 unoptimized travel nodes",
  "expected_improvement": "high" | "medium" | "low" | "none"
}
```

---

## Build Selection Criteria

### Diversity Requirements

✅ **Class Variety** (aim for 2-3 builds per class):
- [ ] Witch (at least 2)
- [ ] Sorceress (at least 2)
- [ ] Ranger (at least 2)
- [ ] Warrior (at least 2)
- [ ] Monk (at least 2)
- [ ] Mercenary (at least 2)
- [ ] Huntress (at least 2)

✅ **Level Variety**:
- [ ] Low (40-60): 3-5 builds
- [ ] Mid (61-80): 5-8 builds
- [ ] High (81-95): 8-12 builds
- [ ] Max (96-100): 2-5 builds

✅ **Passive Points Allocated**:
- [ ] Small (50-80 points): 3-5 builds
- [ ] Medium (81-110 points): 10-15 builds
- [ ] Large (111-123 points): 5-10 builds

✅ **Optimization Potential**:
- [ ] High potential (inefficient, budget headroom): 10-15 builds
- [ ] Medium potential (decent but improvable): 5-8 builds
- [ ] Low potential (already well-optimized): 3-5 builds
- [ ] No potential (fully optimal, convergence tests): 2-3 builds

✅ **Archetype Variety**:
- [ ] Minion builds: 3-5
- [ ] Spell caster builds: 5-7
- [ ] Attack builds: 5-7
- [ ] Hybrid builds: 3-5

---

## How to Populate

### Step 1: Export from Maxroll Builds

1. Go to https://maxroll.gg/poe2/build-guides
2. Choose a build guide
3. Look for "Import to PoB" button or embedded planner
4. Copy the PoB code (Base64 string starting with "eN...")
5. Add to `corpus.json` (see template below)

### Step 2: Add Personal Builds

1. Open your PoB builds
2. Click "Import/Export Build" → "Generate"
3. Copy the code
4. Add to `corpus.json` with notes about known inefficiencies

### Step 3: Create Synthetic Builds

1. Use PoB to create edge case builds:
   - Fully optimal (all points spent efficiently)
   - Already at max budget (no room for improvement)
   - Weird edge cases (disconnected sections, keystone-heavy)
2. Export and add to `corpus.json`

---

## File Format: corpus.json

```json
{
  "version": "1.0",
  "created": "2025-10-27",
  "total_builds": 23,
  "builds": [
    {
      "build_id": "maxroll-storm-mage-lich-001",
      "source": "maxroll",
      "name": "Storm Mage Lich",
      "url": "https://maxroll.gg/poe2/build-guides/storm-mage-lich-build-guide",
      "pob_code": "eNp...",
      "character_class": "Witch",
      "ascendancy": "Lich",
      "level": 85,
      "allocated_points": 98,
      "unallocated_points": 10,
      "archetype": "minion",
      "notes": "Maxroll endgame build - likely well-optimized",
      "expected_improvement": "low"
    },
    {
      "build_id": "personal-inefficient-ranger-001",
      "source": "personal",
      "name": "Alec's Lightning Arrow Test",
      "url": null,
      "pob_code": "eNp...",
      "character_class": "Ranger",
      "ascendancy": "Deadeye",
      "level": 75,
      "allocated_points": 85,
      "unallocated_points": 13,
      "archetype": "attack",
      "notes": "Intentionally inefficient - took scenic route to Keystone, 7 wasted travel nodes",
      "expected_improvement": "high"
    }
  ]
}
```

---

## Example PoB Codes (Samples)

**Note:** These are placeholder examples. Replace with real PoB codes!

```
eNp1VU1vHDcQ... (Storm Mage Lich - Witch)
eNq9Vk1v3DYU... (Lightning Arrow - Ranger)
eNp9VktP4zoU... (Boneshatter - Warrior)
```

---

## Validation Script

Once `corpus.json` is populated, run:

```bash
python tests/fixtures/optimization_builds/validate_corpus.py
```

This will:
- Parse all PoB codes
- Verify metadata accuracy (level, allocated points, etc.)
- Check diversity criteria (class, level, archetype distribution)
- Report any issues

---

## Prep Sprint Blockers

**Task #4 Status:** 🔴 INCOMPLETE
**Blocker:** Requires Alec to populate corpus.json with 20-30 real PoB codes
**Impact:** Blocks Task #5 (Establish baseline stats)

**Estimated Time:** 2-4 hours (Alec)
- 1-2 hours: Collect 10-15 Maxroll builds
- 30 min: Export 5-10 personal builds
- 30 min: Create 3-5 synthetic builds
- 30 min: Fill corpus.json metadata

**Priority:** ⚠️ CRITICAL PATH - Epic 2 Stories 2.1-2.8 depend on this corpus for testing

---

## Available Maxroll Builds (Reference)

Based on web search, these builds are available on Maxroll:

1. Storm Mage Lich (Witch)
2. Grenade Mercenary (Mercenary - Witchhunter)
3. Falling Thunder Invoker (Monk)
4. Boneshatter Warbringer (Warrior)
5. Ice Nova Snap Stormweaver (Sorceress)
6. Minion Army Infernalist (Witch)
7. Ice Strike Invoker (Monk)
8. Fireball Blood Mage (Witch)
9. Lightning Arrow Deadeye (Ranger)
10. Frost Mage Infernalist (Witch)

**Action:** Visit https://maxroll.gg/poe2/build-guides and export PoB codes from these guides.

---

## Next Steps

**For Alec:**
1. [ ] Populate `corpus.json` with 20-30 builds
2. [ ] Run validation script to check completeness
3. [ ] Commit to repository
4. [ ] Notify Bob (SM) that Task #4 is complete

**For Epic 2:**
- Task #5 (baseline stats) can proceed once corpus is ready
- Story 2.1-2.8 tests will use this corpus
- "8%+ median improvement" success criteria measured against this corpus

---

**Created by:** Bob (Scrum Master) - Prep Sprint
**Date:** 2025-10-27
**Status:** Framework ready, awaiting Alec's population
