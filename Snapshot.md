# poe2_optimizer_v6 — Snapshot

> Project-specific state. Updated each session. Linked from [[00_Meta/Game_Save]].

**Quick Links:** [[10_Active_Projects/poe2_optimizer_v6/Timeline|Timeline]] | [[10_Active_Projects/poe2_optimizer_v6/BMAD_Index|BMAD Index]] | [[00_Meta/Dashboard|Dashboard]]

---

## Status

**Phase:** `Testing`
**Health:** `On Track`
**Last Touched:** `2026-07-02`

---

## Current Focus

> What aspect of this project are you actively working on?

```
Story 2.9.2: Spell/DOT MinimalCalc Enhancement
- Environment restored after PC refresh (PoB 0.15.0 fresh install)
- Nil-safety patches applied to new engine
- Status: "review" - need to re-review since code review was interrupted
```

---

## Next Action
**EPIC 3.5 COMPLETE (2026-07-02).** All five stories done; 6 Tier-A GUI baselines captured at v0.15.0 and committed. Next: Epic 3.5 retrospective (optional — capture the Epic 3 thin-slice process deviation too), then **Epic 4 Truth Engine kickoff**: timeboxed driver.lua spike (go/no-go pre-committed), triage the five 0.0%-improvement M0 builds, execute the deferred v0.22.0 engine jump, retire MinimalCalc. Keep `D:\Tools\PoB2-0.15.0-official\` installed — it's the pinned capture GUI for any Tier-B re-captures (never let it auto-update). Epic 4 mass capture should deepen spell-hit/dot coverage (single-sample today).

---

## Mental RAM

> Project-specific thoughts, decisions, context to remember.

- PC refreshed - fresh PoB 0.15.0 installed to external/pob-engine/
- NEW nil-safety patches applied (in addition to Global.lua from ADR-004):
  - ModStore.lua:458 - `(value or 0)` for arithmetic on nil
  - CalcOffence.lua:5005-5010 - check for data.buildupTypes existence
- DEBUG_MODE flag added to MinimalCalc.lua (set to false for production)
- Test baseline recalibrated: Lightning Arrow DPS 311.7 → 464.04 (PoB 0.15.0 change)
- All tests passing: 4/4 weapon tests, 18/18 spell tests
- Python 3.14 venv created with all dependencies (lupa-2.6 includes bundled LuaJIT)
- Non-fatal nil errors still occur at CalcOffence.lua:1919 (handled gracefully)

---

## Open Loops

> Unresolved items, questions, blockers for this project.

- [ ] Re-review Story 2.9.2 (code review interrupted by environment setup)
- [ ] Update sprint-status.yaml to reflect current progress
- [ ] Non-fatal nil error at CalcOffence.lua:1919 - could patch but tests pass
- [ ] ADR-004 patch file may need updating to include ModStore.lua & CalcOffence.lua patches
- [ ] Task 4.5: Epic 2 validation suite not run (deferred with approval)
- [ ] Task 4.6: Performance benchmarking <500ms target not validated

---

## Decision Log

> Important decisions made and why (so you don't re-litigate them).

| Date | Decision | Reasoning |
|------|----------|-----------|
| 2025-11-29 | Hybrid calculation approach (Phase 2) | Story 2.9.1 delivered infrastructure, spell formulas needed |
| 2025-12-03 | Use skillTypes[SkillType.Spell] not skillFlags.spell | Matches PoB CalcActiveSkill.lua:522 |
| 2025-12-04 | Defer totem damage Tasks 3.1-3.2 | Separate complexity, attacks work |
| 2025-12-04 | Accept 80%+ success rate as "substantially complete" | Documented limitations acceptable |
| 2025-12-18 | Defer Epic 2 validation | With totem support, more likely to pass later |

---

## Session History

| Date | What I Did | Where I Left Off |
|------|------------|------------------|
| 2025-12-01 | Research phase - discovered spell base damage storage | Task 1 complete |
| 2025-12-03 | Breakthrough - spell base damage extraction working | Fireball & Essence Drain producing DPS |
| 2025-12-04 | Task 2.2-2.7 & 4.1-4.4 complete, 77.8% success | Senior dev review requested |
| 2025-12-04 | Senior dev review (Alec) - 2 blockers identified | Changes requested |
| 2025-12-18 | Fixed blockers, added totem support, 88.9% success | MUST FIX items complete |
| 2025-12-18 | Test validation complete, final success rate 90.9% | Ready for story completion decision |
| 2026-01-30 | PC refresh recovery: PoB 0.15.0 setup, nil patches, test baseline recalibration | Re-review 2.9.2, update sprint-status |

---

## Project Links

- **Main Files:**
  - `src/calculator/MinimalCalc.lua` - Spell base damage extraction (lines 1628-1695)
  - `src/calculator/pob_engine.py` - mainSocketGroup parameter passing
  - `tests/integration/test_story_2_9_2_spell_builds.py` - Comprehensive test suite
- **Related Notes:**
  - `docs/stories/2-9-2-spell-dot-minimalcalc-enhancement.md` - Full story doc
  - `docs/stories/2-9-2-STATUS-REPORT.md` - Session 3 status
  - `docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md` - Global.lua patch docs
- **External Resources:**
  - PoB CalcOffence.lua - Spell damage formulas reference
  - `external/patches/global-lua-nil-safety.patch` - Patch for submodule updates

---

## Completion Criteria

> How do you know this project is "done"?

**Story 2.9.2 Acceptance Criteria:**
- [x] AC-2.9.2.1: Spell base damage calculation implemented
- [x] AC-2.9.2.2: DOT calculation support
- [x] AC-2.9.2.3: Totem/minion calculation support (partial - attacks work)
- [x] AC-2.9.2.4: Spell build validation (90.9% success rate)
- [ ] AC-2.9.2.5: Epic 2 validation criteria achieved (deferred)
- [x] AC-2.9.2.6: No regressions in weapon builds

**Epic 2 Overall:**
- [ ] 100% build success rate (currently 90.9%)
- [ ] Median improvement >= 5% with unallocated points
- [ ] Zero budget violations
- [ ] Performance <500ms per calculation
