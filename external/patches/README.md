# External Dependency Patches

This directory contains patches for external dependencies (Git submodules) that require modifications for our project.

## Why Patches?

External dependencies are managed as Git submodules, which point to upstream repositories. When we need to modify files in these submodules:
- Changes are **lost** when the submodule is updated to a new commit
- We cannot commit changes directly to the submodule (it's a read-only reference)

Patches provide a **reusable, documented way** to reapply necessary modifications after submodule updates.

## Available Patches

### `global-lua-nil-safety.patch`

**Purpose**: Adds nil-safety to 64-bit bitwise operations in PoB engine

**Target file**: `external/pob-engine/src/Data/Global.lua`

**Functions patched**:
- `OR64` - Handles nil arguments in OR operations
- `AND64` - Handles nil arguments in AND operations
- `XOR64` - Handles nil arguments in XOR operations
- `NOT64` - Handles nil input

**Why needed**: Spell builds pass nil values to bitwise functions during initialization, causing `Global.lua:118` errors

**Documentation**: See [ADR-004](../../docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md)

## Usage

### Verify Patch Status

Check if patch is applied:

```bash
# From project root
grep -n "or 0  -- Handle nil arguments" external/pob-engine/src/Data/Global.lua
```

**Expected output (patch applied)**:
```
117:        local nextVal = args[i] or 0  -- Handle nil arguments
146:        local nextVal = args[i] or 0  -- Handle nil arguments
175:        local nextVal = args[i] or 0  -- Handle nil arguments
```

**No output = patch NOT applied** (needs reapplication)

### Apply Patch

```bash
# From project root
cd external/pob-engine
git apply ../../external/patches/global-lua-nil-safety.patch
cd ../..
```

### Verify Application

```bash
# Run regression tests
pytest tests/integration/test_story_2_9_2_spell_builds.py -v
```

All spell build tests should pass.

### Reapply After Submodule Update

When you update the `external/pob-engine` submodule:

1. Update submodule to new commit:
   ```bash
   cd external/pob-engine
   git pull origin main  # or specific branch/tag
   cd ../..
   git add external/pob-engine
   ```

2. Reapply patches:
   ```bash
   cd external/pob-engine
   git apply ../../external/patches/global-lua-nil-safety.patch
   cd ../..
   ```

3. Verify tests still pass:
   ```bash
   pytest tests/integration/test_story_2_9_2_spell_builds.py -v
   ```

4. If patch fails to apply (upstream changed Global.lua):
   - Review upstream changes in `src/Data/Global.lua`
   - Manually merge our nil-safety fixes
   - Regenerate patch file:
     ```bash
     cd external/pob-engine
     git diff src/Data/Global.lua > ../../external/patches/global-lua-nil-safety.patch
     cd ../..
     ```
   - Update ADR-004 with new patch details

## Automated Verification (CI)

Add to your CI pipeline (`.github/workflows/test.yml` or similar):

```yaml
- name: Verify PoB patches applied
  run: |
    if ! grep -q "or 0  -- Handle nil arguments" external/pob-engine/src/Data/Global.lua; then
      echo "ERROR: Global.lua nil-safety patch not applied!"
      echo "Run: cd external/pob-engine && git apply ../../external/patches/global-lua-nil-safety.patch"
      exit 1
    fi
```

## Future Improvements

### Option 1: Upstream Contribution
If PoB 2 appears in PathOfBuildingCommunity repository, propose these fixes upstream.

### Option 2: Fork Submodule
Create our own fork of `pob-engine` with patches permanently applied:
- Simpler maintenance (no reapplication needed)
- More work to keep fork synced with upstream

### Option 3: Automated Patch Application
Add Git hooks or build scripts to automatically apply patches on submodule checkout.

## References

- **ADR-004**: [PoB Global.lua Nil-Safety Patch](../../docs/decisions/ADR-004-pob-global-lua-nil-safety-patch.md)
- **Story 2.9.2**: [Spell/DOT MinimalCalc Enhancement](../../docs/stories/2-9-2-spell-dot-minimalcalc-enhancement.md)
- **Upstream**: [PathOfBuildingCommunity/PathOfBuilding](https://github.com/PathOfBuildingCommunity/PathOfBuilding)
