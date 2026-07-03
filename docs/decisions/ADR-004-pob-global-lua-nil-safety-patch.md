# ADR-004: PoB Global.lua Nil-Safety Patch

## Status
Accepted — under re-evaluation; supersession trigger = Epic 4 spike outcome (fixed date).

> **2026-07-03 (Story 4.1 spike outcome):** The three nil-safety patches
> (0001 Global.lua, 0002 ModStore.lua, 0003 CalcOffence.lua) were reverse-applied
> and the REAL PoB ModParser was booted (the FIRST time it runs — these nils
> originally arose only because MinimalCalc's *stubbed* ModParser fed empty mod
> lists). Result: **all 6 Tier-A GUI baselines (attack / spell-hit / DoT) compute
> at ±0.000% with ALL THREE PATCHES REVERTED** — including the ADR-004-named
> crash build `ritualist_lightning_spear_96` and a DoT build. No "arithmetic on a
> nil value" reproduced at any of the three guarded sites. **Per-patch verdict:
> all three are drop-candidates (MinimalCalc-only artifacts).** Actual removal is
> DEFERRED to Epic 4 item 8 (MinimalCalc retirement) so the guards remain while
> MinimalCalc is still the active engine; re-confirm against the full corpus +
> the Story 2.9.2 regression gate at removal. Env restored (`setup_pob.py` exit 0).
> See docs/stories/4-1-truth-engine-driver-spike.md (Task 8) + `scripts/triage_m0_builds.py`.

## Context

During Story 2.9.2 (Spell/DOT MinimalCalc Enhancement), we discovered that certain spell builds caused the PoB engine to crash with an error in `Global.lua:118`:

```
attempt to perform arithmetic on a nil value (Global.lua:118)
```

This occurred in the 64-bit bitwise operation functions (`OR64`, `AND64`, `XOR64`, `NOT64`) when nil arguments were passed during build initialization.

### Root Cause

The PoB engine's `Global.lua` bitwise functions did not handle nil arguments defensively. When spell builds with certain configurations were loaded, the functions received nil values and attempted arithmetic operations directly, causing Lua runtime errors.

### Critical Risk

The modified file `external/pob-engine/src/Data/Global.lua` is part of a Git submodule pointing to the external PathOfBuildingCommunity repository. **Any update to this submodule will overwrite our changes**, breaking spell build calculations.

## Decision

We will:

1. **Apply nil-safety patches** to `OR64`, `AND64`, `XOR64`, and `NOT64` functions in `external/pob-engine/src/Data/Global.lua`
2. **Document the patch** in this ADR with complete diff
3. **Create a reusable patch file** in `external/patches/global-lua-nil-safety.patch`
4. **Add verification instructions** for detecting when the patch needs reapplication
5. **Consider upstreaming** the fix to PathOfBuildingCommunity (PoB 2 may not exist yet upstream)

## Patch Details

### Modified Functions

**OR64** (lines 113, 117):
- Changed: `local result = args[1]` → `local result = args[1] or 0`
- Added: `local nextVal = args[i] or 0` before arithmetic operations
- Changed: Use `nextVal` instead of `args[i]` directly

**AND64** (lines 142, 146):
- Same pattern as OR64

**XOR64** (lines 171, 175):
- Same pattern as OR64

**NOT64** (lines 193-194):
- Added: `a = a or 0` to handle nil input

### Complete Patch

```diff
diff --git a/src/Data/Global.lua b/src/Data/Global.lua
index 522f0c8a1..94ccc09e6 100644
--- a/src/Data/Global.lua
+++ b/src/Data/Global.lua
@@ -108,26 +108,27 @@ function OR64(...)
     if #args < 2 then
         return args[1] or 0
     end
-
-    -- Start with first value
-    local result = args[1]
-
+
+    -- Start with first value (handle nil)
+    local result = args[1] or 0
+
     -- OR with each subsequent value
     for i = 2, #args do
+        local nextVal = args[i] or 0  -- Handle nil arguments
         -- Split into high and low 32-bit parts
         local ah = math.floor(result / 0x100000000)
         local al = result % 0x100000000
-        local bh = math.floor(args[i] / 0x100000000)
-        local bl = args[i] % 0x100000000
-
+        local bh = math.floor(nextVal / 0x100000000)
+        local bl = nextVal % 0x100000000
+
         -- Perform OR operation on both parts
         local high = bit.bor(ah, bh)
         local low = bit.bor(al, bl)
-
+
         -- Combine the results
         result = bit.band(high, HIGH_MASK_53) * 0x100000000 + low
     end
-
+
     return result
 end

@@ -136,26 +137,27 @@ function AND64(...)
     if #args < 2 then
         return args[1] or 0
     end
-
-    -- Start with first value
-    local result = args[1]
-
+
+    -- Start with first value (handle nil)
+    local result = args[1] or 0
+
     -- AND with each subsequent value
     for i = 2, #args do
+        local nextVal = args[i] or 0  -- Handle nil arguments
         -- Split into high and low 32-bit parts
         local ah = math.floor(result / 0x100000000)
         local al = result % 0x100000000
-        local bh = math.floor(args[i] / 0x100000000)
-        local bl = args[i] % 0x100000000
-
+        local bh = math.floor(nextVal / 0x100000000)
+        local bl = nextVal % 0x100000000
+
         -- Perform AND operation on both parts
         local high = bit.band(ah, bh)
         local low = bit.band(al, bl)
-
+
         -- Combine the results
         result = bit.band(high, HIGH_MASK_53) * 0x100000000 + low
     end
-
+
     return result
 end

@@ -164,30 +166,33 @@ function XOR64(...)
     if #args < 2 then
         return args[1] or 0
     end
-
-    -- Start with first value
-    local result = args[1]
-
+
+    -- Start with first value (handle nil)
+    local result = args[1] or 0
+
     -- XOR with each subsequent value
     for i = 2, #args do
+        local nextVal = args[i] or 0  -- Handle nil arguments
         -- Split into high and low 32-bit parts
         local ah = math.floor(result / 0x100000000)
         local al = result % 0x100000000
-        local bh = math.floor(args[i] / 0x100000000)
-        local bl = args[i] % 0x100000000
-
+        local bh = math.floor(nextVal / 0x100000000)
+        local bl = nextVal % 0x100000000
+
         -- Perform XOR operation on both parts
         local high = bit.bxor(ah, bh)
         local low = bit.bxor(al, bl)
-
+
         -- Combine the results
         result = bit.band(high, HIGH_MASK_53) * 0x100000000 + low
     end
-
+
     return result
 end

 function NOT64(a)
+    -- Handle nil input
+    a = a or 0
     -- Split into high and low 32-bit parts
     local ah = math.floor(a / 0x100000000)
     local al = a % 0x100000000
```

## Reapplication Instructions

### Detecting Patch Loss

Run the verification script:

```bash
grep -n "or 0  -- Handle nil arguments" external/pob-engine/src/Data/Global.lua
```

**Expected output** (patch applied):
```
117:        local nextVal = args[i] or 0  -- Handle nil arguments
146:        local nextVal = args[i] or 0  -- Handle nil arguments
175:        local nextVal = args[i] or 0  -- Handle nil arguments
```

**If no output** → Patch needs reapplication

### Manual Reapplication

1. Navigate to external PoB engine:
   ```bash
   cd external/pob-engine
   ```

2. Apply the patch:
   ```bash
   git apply ../../external/patches/global-lua-nil-safety.patch
   ```

3. Verify patch applied:
   ```bash
   grep -n "or 0  -- Handle nil arguments" src/Data/Global.lua
   ```

4. Run regression tests:
   ```bash
   cd ../..
   pytest tests/integration/test_story_2_9_2_spell_builds.py -v
   ```

### Automatic Verification (CI)

Add to CI pipeline (`.github/workflows/test.yml` or similar):

```yaml
- name: Verify PoB Global.lua patch applied
  run: |
    if ! grep -q "or 0  -- Handle nil arguments" external/pob-engine/src/Data/Global.lua; then
      echo "ERROR: Global.lua nil-safety patch not applied!"
      echo "Run: cd external/pob-engine && git apply ../../external/patches/global-lua-nil-safety.patch"
      exit 1
    fi
```

## Consequences

### Positive
- **Spell builds work**: ritualist_lightning_spear_96 and other spell builds no longer crash
- **Defensive programming**: Nil arguments handled gracefully
- **Documented**: Clear process for reapplication
- **Verifiable**: Automated checks can detect patch loss

### Negative
- **Manual maintenance**: Requires reapplication after PoB engine updates
- **Submodule friction**: Adds complexity to submodule updates
- **No upstream fix**: PoB 2 may not exist in upstream repository yet

### Future Options

1. **Upstream contribution**: If PoB 2 appears in PathOfBuildingCommunity, propose this fix
2. **Fork PoB engine**: Create our own fork with patches permanently applied
3. **Lua preprocessing**: Apply patches during build/test setup automatically
4. **Wait for PoB 2 release**: Official PoB 2 may include these fixes natively

## References

- **Story 2.9.2**: Spell/DOT MinimalCalc Enhancement (`docs/stories/2-9-2-spell-dot-minimalcalc-enhancement.md`)
- **Error location**: `external/pob-engine/src/Data/Global.lua:118`
- **Test coverage**: `tests/integration/test_story_2_9_2_spell_builds.py`
- **Senior Developer Review**: Action item [AI-Review][HIGH] (lines 717-743 in story file)

## Date
2025-12-04

## Authors
- Amelia (Dev Agent) - Implementation
- Alec - Review and approval

---

## Addendum — 2026-07-02 (correct-course / forensics)

The 2026-07-02 pob-engine forensics run (`docs/forensics/pob-engine-forensics-2026-07-02.md`)
and the sprint change proposal Decisions section supersede parts of this ADR:

1. **Patch file renamed/regenerated.** `external/patches/global-lua-nil-safety.patch`
   (cut against 0.12.2) is retired. The nil-safety fix now lives at
   `external/patches/0001-global-lua-nil-safety.patch`, regenerated against upstream
   **v0.22.0** (`860f4268` — the pin target decided 2026-07-02; v0.22.0 was verified to
   still lack these guards). Paths inside the patch are now repo-root-relative
   (`git apply` from project root, no `cd` into the submodule).
2. **Two sibling patches discovered and captured.** Story 2.9.2 also hand-edited
   `src/Classes/ModStore.lua` (EvalMod nil guard) and `src/Modules/CalcOffence.lua`
   (ailment buildupTypes guard) directly in the vendored tree with **no patch file
   anywhere** — exactly the failure mode this ADR warned about. Now captured as
   `0002-modstore-evalmod-nil-safety.patch` / `0003-calcoffence-ailment-buildup-nil-safety.patch`.
3. **Reapplication is being automated.** Stories 3.5.3 (`scripts/setup_pob.py`,
   idempotent apply of every patch in `external/patches/`) and 3.5.4 (autouse conftest
   `pob_env.verify()`, data-driven per-patch check) replace this ADR's manual
   apply/verify instructions and its hardcoded-marker CI snippet.
4. **Open question for the Epic 4 spike** (pebo-master-plan §6 E4 item 1): whether the
   real ModParser pipeline still needs these guards at all — if not, the patches are
   dropped (one-file change each, by design).
