# External Dependency Patches

Patches for `external/pob-engine` (Path of Building PoE2). The engine is consumed at a
pinned upstream commit; every local modification MUST exist as a patch file here — edits
made only in the working tree are silently lost on any update/re-vendor (this happened:
patches 0002/0003 below existed solely as untracked hand-edits from Story 2.9.2 until the
2026-07-02 forensics run recovered them — see
`docs/forensics/pob-engine-forensics-2026-07-02.md`).

## Patch set (applies in filename order)

**Pin target: upstream tag `v0.22.0` = `860f4268299739ce9df87c4f373abe35824101cf`**
(decided 2026-07-02 — see `docs/sprint-change-proposal-2026-07-02.md`, Decisions; story
3.5.2 executes the re-pin). The live vendored tree is still 0.15.0-era with all three
edits baked in; this set becomes operative on the fresh v0.22.0 checkout.

### `0001-global-lua-nil-safety.patch`
- **Target**: `external/pob-engine/src/Data/Global.lua` — nil guards in `OR64`/`AND64`/`XOR64`/`NOT64`
- **Why**: spell builds pass nil to the 64-bit bitwise ops during init → `attempt to perform arithmetic on a nil value`
- **Provenance**: ADR-004 / Story 2.9.2. Regenerated 2026-07-02 against v0.22.0 (upstream
  still lacks the guards; only the `#args < 2` early-return is nil-safe). v0.15.0-targeted
  draft preserved at `docs/forensics/proposed-patches/0001-global-lua-nil-safety.patch`.
- **Sentinel**: `grep -c "or 0  -- Handle nil arguments" external/pob-engine/src/Data/Global.lua` → `3`

### `0002-modstore-evalmod-nil-safety.patch`
- **Target**: `external/pob-engine/src/Classes/ModStore.lua` — `EvalMod` nil guard (value can be nil when `mod.value` is nil)
- **Provenance**: Story 2.9.2 hand-edit, never captured until the 2026-07-02 forensics run. Applies clean on both v0.15.0 and v0.22.0 (verified).
- **Sentinel**: `grep -c "Nil-safety patch (Story 2.9.2)" external/pob-engine/src/Classes/ModStore.lua` → `1`

### `0003-calcoffence-ailment-buildup-nil-safety.patch`
- **Target**: `external/pob-engine/src/Modules/CalcOffence.lua` — skip ailments missing from `data.buildupTypes` (`::continue_ailment::` goto)
- **Provenance**: Story 2.9.2 hand-edit, never captured until the 2026-07-02 forensics run. Applies clean on both v0.15.0 and v0.22.0 (verified).
- **Sentinel**: `grep -c "continue_ailment" external/pob-engine/src/Modules/CalcOffence.lua` → `2`

### Retired
- `global-lua-nil-safety.patch` (0.12.2-era; sat at a hunk offset on 0.15.0+) — superseded by `0001-global-lua-nil-safety.patch`.

## Applying

All patches are repo-root-relative (`external/pob-engine/...` paths) and LF (`.gitattributes`
here enforces `-text`). From the project root, onto an LF checkout
(`git -c core.autocrlf=false -c core.eol=lf ...`):

```bash
git -c core.autocrlf=false apply external/patches/0001-global-lua-nil-safety.patch
git -c core.autocrlf=false apply external/patches/0002-modstore-evalmod-nil-safety.patch
git -c core.autocrlf=false apply external/patches/0003-calcoffence-ailment-buildup-nil-safety.patch
```

Skip-if-applied check (per patch): forward `git apply --check` fails AND
`git apply --reverse --check` passes ⇒ already applied — skip. This logic (and the whole
sequence) is automated by `scripts/setup_pob.py` once story 3.5.3 lands; the autouse
conftest guard (story 3.5.4) verifies every patch in this directory data-driven — never
hardcode patch names anywhere.

## Regression gate

```bash
pytest -n 1 tests/integration/test_story_2_9_2_spell_builds.py -v
```

## After a version bump (patch-day workstream)

1. Check whether upstream fixed each issue (inspect the target functions at the new tag).
2. `git apply --check` each patch against the new tag's clean checkout (scratch clone).
3. Regenerate any that fail on context drift (semantic edits are documented in each header
   and in ADR-004); drop any that upstream fixed, and update this README + ADR-004.

## References

- **ADR-004**: `docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md` (incl. 2026-07-02 addendum)
- **Forensics report**: `docs/forensics/pob-engine-forensics-2026-07-02.md`
- **Change record**: `docs/sprint-change-proposal-2026-07-02.md`
- **Upstream**: https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2
