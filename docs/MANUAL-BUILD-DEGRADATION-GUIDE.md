# Manual Build Degradation Guide for Epic 2 Validation

**Goal:** Create 13-15 degraded builds to test the optimizer
**Time estimate:** 30-60 minutes total (~3 minutes per build)
**Why:** I successfully auto-generated 7 builds, but need 13-15 more for statistical significance

---

## What You'll Do (Simple Version)

1. Open a build in Path of Building
2. Remove some passive nodes randomly
3. Export the degraded build to a specific location
4. Repeat 13-15 times

---

## Detailed Instructions

### Setup (One Time)

1. **Create output folder** (if not exists):
   ```
   D:\poe2_optimizer_v6\tests\fixtures\optimization_corpus\degraded\manual\
   ```

2. **Open Path of Building** (PoE 2 version)

---

### For Each Build (Repeat 13-15 times)

#### Step 1: Load a Source Build

Pick one of these builds from `D:\poe2_optimizer_v6\tests\fixtures\parity_builds\`:

**Recommended builds to degrade** (these have items/skills so optimizer has real DPS to optimize):

1. `huntress_68_poeninja.xml`
2. `huntress_71_poeninja.xml`
3. `invoker_100_poeninja.xml`
4. `litch_100_poeninja.xml`
5. `monk_72_poeninja.xml`
6. `pathfinder_100_poeninja.xml`
7. `ranger_68_poeninja.xml`
8. `ritualist_68_poeninja.xml`
9. `smithofkitava_80_poeninja.xml`
10. `sorceress_69_poeninja.xml`
11. `titan_100_poeninja.xml`
12. `warrior_79_poeninja.xml`
13. `witch_67_poeninja.xml`
14. `witch_76_poeninja.xml`
15. `witchhunter_100_poeninja.xml`

**In PoB:**
- Click "Import/Export Build"
- Click "Import from..."
- Navigate to the build file and import it

#### Step 2: Note Original Node Count

Look at the passive tree. You should see something like "92 points allocated" or similar.

#### Step 3: Remove Nodes Based on Difficulty

**Cycle through these difficulties** as you go through the list:

| Build # | Difficulty | How Many Nodes to Remove | Expected Result |
|---------|------------|-------------------------|-----------------|
| 1, 4, 7, 10, 13 | **HIP** (High) | Remove **40-50%** of nodes | Optimizer should find BIG improvements (10-25%) |
| 2, 5, 8, 11, 14 | **MIP** (Medium) | Remove **20-30%** of nodes | Optimizer should find moderate improvements (5-15%) |
| 3, 6, 9, 12, 15 | **LIP** (Low) | Remove **5-15%** of nodes | Optimizer should find small improvements (2-8%) |

**Example:**
- Build has 90 nodes allocated
- You're doing HIP (High) → Remove 40-50% → Remove **36-45 nodes**
- You're doing MIP (Medium) → Remove 20-30% → Remove **18-27 nodes**
- You're doing LIP (Low) → Remove 5-15% → Remove **5-14 nodes**

**How to remove nodes in PoB:**
1. Click the "Tree" tab
2. Click on allocated passive nodes to deselect them
3. **IMPORTANT:** Don't remove nodes that would disconnect the tree! Try to remove:
   - Nodes on the outer edges/tips
   - Entire branches you pathed to
   - Clusters of small nodes
4. Keep removing until you hit the target count
5. **It's OK to be approximate** - if target is 40 nodes and you remove 38, that's fine!

#### Step 4: Export the Degraded Build

1. Click "Import/Export Build"
2. Click "Generate"
3. Copy the build code (it's in your clipboard)
4. Open Notepad or any text editor
5. Paste the code
6. Save as XML file with this naming pattern:
   ```
   D:\poe2_optimizer_v6\tests\fixtures\optimization_corpus\degraded\manual\{original_name}_manual_{difficulty}.xml
   ```

**Example filenames:**
- `huntress_68_poeninja_manual_hip.xml` (High difficulty)
- `monk_72_poeninja_manual_mip.xml` (Medium difficulty)
- `ranger_68_poeninja_manual_lip.xml` (Low difficulty)

**Wait, that's the PoB code, not XML!**

Let me correct that:

1. Instead of generating build code, use **File → Save**
2. Save to: `D:\poe2_optimizer_v6\tests\fixtures\optimization_corpus\degraded\manual\`
3. Name it: `{original_name}_manual_{difficulty}.xml`

**OR Easier Method - Import then Export:**
1. After removing nodes, click "Import/Export Build"
2. Click "Save" (saves to PoB's builds folder)
3. Name it descriptively
4. Then find it in PoB's save folder and copy it to our manual folder

Actually, **EASIEST METHOD:**
1. After removing nodes, just click **File → Save As**
2. Navigate to: `D:\poe2_optimizer_v6\tests\fixtures\optimization_corpus\degraded\manual\`
3. Save with name: `{original_name}_manual_{difficulty}.xml`

#### Step 5: Track Your Progress

Keep a simple list as you go (text file or paper):

```
✓ 1. huntress_68 - HIP - removed 50 nodes
✓ 2. huntress_71 - MIP - removed 25 nodes
✓ 3. invoker_100 - LIP - removed 10 nodes
... (continue)
```

---

## Quick Reference Table

Here's exactly what to do for each of the 15 builds:

| # | Source Build | Difficulty | Target Removal | Save As |
|---|--------------|------------|---------------|---------|
| 1 | huntress_68_poeninja.xml | HIP | ~45-50 nodes | huntress_68_poeninja_manual_hip.xml |
| 2 | huntress_71_poeninja.xml | MIP | ~20-25 nodes | huntress_71_poeninja_manual_mip.xml |
| 3 | invoker_100_poeninja.xml | LIP | ~10-15 nodes | invoker_100_poeninja_manual_lip.xml |
| 4 | litch_100_poeninja.xml | HIP | ~60-70 nodes | litch_100_poeninja_manual_hip.xml |
| 5 | monk_72_poeninja.xml | MIP | ~20-25 nodes | monk_72_poeninja_manual_mip.xml |
| 6 | pathfinder_100_poeninja.xml | LIP | ~10-15 nodes | pathfinder_100_poeninja_manual_lip.xml |
| 7 | ranger_68_poeninja.xml | HIP | ~40-45 nodes | ranger_68_poeninja_manual_hip.xml |
| 8 | ritualist_68_poeninja.xml | MIP | ~20-25 nodes | ritualist_68_poeninja_manual_mip.xml |
| 9 | smithofkitava_80_poeninja.xml | LIP | ~10-15 nodes | smithofkitava_80_poeninja_manual_lip.xml |
| 10 | sorceress_69_poeninja.xml | HIP | ~40-45 nodes | sorceress_69_poeninja_manual_hip.xml |
| 11 | titan_100_poeninja.xml | MIP | ~35-45 nodes | titan_100_poeninja_manual_mip.xml |
| 12 | warrior_79_poeninja.xml | LIP | ~10-15 nodes | warrior_79_poeninja_manual_lip.xml |
| 13 | witch_67_poeninja.xml | HIP | ~40-45 nodes | witch_67_poeninja_manual_hip.xml |
| 14 | witch_76_poeninja.xml | MIP | ~20-30 nodes | witch_76_poeninja_manual_mip.xml |
| 15 | witchhunter_100_poeninja.xml | LIP | ~10-15 nodes | witchhunter_100_poeninja_manual_lip.xml |

---

## Tips

1. **Don't overthink it** - Just remove nodes semi-randomly. The goal is to make the build worse so optimizer can improve it.

2. **Don't worry about "optimal" removal** - Any degraded build helps us test.

3. **If you disconnect the tree** - PoB should warn you. Just add back a connecting node and remove a different one.

4. **Take breaks** - Do 5 builds, take a break, do another 5, etc.

5. **If you get stuck** - Skip that build and move to the next one. We need ~13-15 total, doesn't matter which ones.

---

## When You're Done

1. Let me know how many builds you created
2. I'll run the validation script on all builds (auto + manual)
3. We'll see if the optimizer works!

---

## Expected Results

After I run validation on your degraded builds:

- **HIP builds**: Optimizer should restore 60-90% of removed nodes, showing 10-25% improvement
- **MIP builds**: Optimizer should restore 40-70% of removed nodes, showing 5-15% improvement
- **LIP builds**: Optimizer should restore 20-50% of removed nodes, showing 2-8% improvement

If we hit **≥70% success rate** and **≥5% median improvement**, Epic 2 validation is complete! ✅

---

**Questions?** Just start with the first 3 builds and let me know if you hit any issues.
