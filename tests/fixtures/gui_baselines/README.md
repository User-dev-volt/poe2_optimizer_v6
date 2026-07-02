# GUI Baseline Fixtures (story 3.5.5)

Tier-A parity baselines: `<PlayerStat>` values computed by the **official
Path of Building (PoE 2) GUI** and harvested verbatim by
`scripts/harvest_gui_baselines.py`. These are external ground truth for the
Epic 4 parity harness — never numbers computed by this project's own engine
(the `scripts/generate_baseline_stats.py` circular-validation anti-pattern).

## Committed layout

```
tests/fixtures/gui_baselines/
  README.md                     <- this file
  xml/                          <- GUI-saved source build XMLs
    <name>.xml
  <name>.baseline.json          <- harvested fixture, one JSON per build,
                                   paired 1:1 with xml/<name>.xml
```

## Fixture schema (`schema_version` 1)

```json
{
  "schema_version": 1,
  "_metadata": {
    "pob_version": "0.15.0",
    "pob_commit": "3e1b71c92dc5f7c295031700746a418558117b06",
    "captured": "YYYY-MM-DD",
    "source_xml": "tests/fixtures/gui_baselines/xml/<name>.xml",
    "source_sha256": "<hex sha-256 of the exact source XML bytes>",
    "archetype": "attack | spell-hit | dot",
    "stale": false,
    "stale_reason": "(present only when stale is true)"
  },
  "stats": {
    "TotalDPS": 18097.067904221,
    "Spec:LifeInc": 5.0,
    "...": 0.0
  }
}
```

- `stats` contains **every** `<PlayerStat>` from the source XML, stat names
  verbatim (including colon-named stats such as `Spec:LifeInc`), values as
  full-precision floats, in XML document order. No renaming, no curated
  subset, no hand-copied numbers (AC-3.5.5.1).
- `<MinionStat>` elements are ignored by design (see the deferral note
  below).
- Duplicate stat names in one build are a harvester hard error.

### Field-name contract with story 3.5.4 (AC-3.5.5.5)

`src/pob_env.py` `verify()` invariant (d) machine-reads exactly these
fields — do not rename them:

- top-level `_metadata` (must be a JSON object),
- `_metadata.pob_version` — a **string** compared by exact equality against
  the pinned submodule `manifest.xml` version (`"0.15.0"`, never `0.15`,
  never `"v0.15.0"`),
- `_metadata.stale` — must be the JSON **boolean** `true` to exempt a
  version-mismatched fixture (the string `"true"` or `1` does not count).

`stale_reason` is a human-honesty convention shared with the 3.5.2 AC4
precedent (`tests/fixtures/parity_builds/gui_baseline_stats.json`); the
verifier does not parse it but the convention is: no `stale: true` without
a `stale_reason`. Note: the story's draft schema sketch used a `metadata`
key with a nested `pob_version` object; it was flattened to `_metadata` +
string `pob_version` because 3.5.4's verifier shipped first and reads these
exact names.

When new fixtures are **committed** here, add their repo-relative paths to
`BASELINE_METADATA_FILES` in `src/pob_env.py` so invariant (d) guards them
(that tuple is the allowlist — files not listed are not checked).

## Capture protocol (Tier-A — the only accepted source)

1. Read the **generated** `external/POB_VERSION.txt` (never assume): it
   names the pinned engine release. Today: **v0.15.0**, commit
   `3e1b71c9...` If the file is missing or hand-written, run
   `python scripts/setup_pob.py` first.
2. Open the official Path of Building PoE2 GUI **at exactly that release**.
3. Import or open the build there, let the GUI recalculate, and **SAVE the
   build XML from that GUI**. The save is what stamps the `<PlayerStat>`
   values at the pinned version — GUI XML does not embed the app version,
   so the protocol is what makes the harvester's version stamp true.
4. Place the saved XML in `xml/` and run:

   ```
   python scripts/harvest_gui_baselines.py tests/fixtures/gui_baselines/xml/<name>.xml --archetype <attack|spell-hit|dot>
   ```

5. Commit the XML + `.baseline.json` pair together.

**Fresh GUI saves at the pinned release are the ONLY Tier-A source.** The
XMLs under `tests/fixtures/realistic_builds/` are harvester food (pobb.in
provenance — computed by whatever PoB version the uploader ran): any
fixture harvested from them must be marked stale
(`--stale-reason "pobb.in provenance, pre-pin GUI version unknown"`) or
must stay uncommitted. Mixing capture and pin versions recreates the
four-way drift Epic 3.5 exists to kill.

## Deferral note (AC-3.5.5.3)

**Minion, totem, and trap build capture is explicitly deferred to Epic 4
item 6 mass capture** (20-24 builds, after the headless-driver spike
verdict). This directory holds only the first 6-8 geared Tier-A builds
covering the v1-gated archetypes: **attack, spell-hit, DoT first**. Do not
capture minion/totem/trap baselines here; the harvester emits `<PlayerStat>`
only and ignores `<MinionStat>` until that Epic 4 story lands.
