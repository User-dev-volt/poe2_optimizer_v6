# Product

## Register

product

## Name

**PEBO — Path of Exile Build Optimizer.** Sibling of LEBO (Last Epoch Build
Optimizer); same family, same design language, different game.

## Users

Hardcore Path of Exile 2 theorycrafters — players who already live inside Path
of Building (PoB) and optimize builds by hand. They arrive with a PoB import
code and a specific question: *"can I do better with the points and currency I
have?"* Their context is PoB open on a second monitor; they will cross-check
our output against PoB in real time. They value information density,
scan-speed, and precision, and they instantly distrust anything that looks
polished but is wrong.

## Product Purpose

A local tool that takes a PoB build and answers three questions PoB cannot:
*"is there a better tree within my budget?"*, *"what is my next-best gear
upgrade and where do I trade for it?"*, and *"why?"* It shows the answer
visually (interactive passive tree, before/after diff), computes it on PoB's
own calculation engine (PoB-accurate numbers, all archetypes), and exports a
lossless PoB code back. Deterministic engines compute every suggestion and
every number; AI narrates and explains, never invents. Roadmap and scope:
`docs/pebo-master-plan.md`.

Trust constraint: any stat is labeled by evidence tier (**reliable / approx /
estimate**), and the tiers are *generated from measured parity data* against a
pinned PoB version — never asserted. Being honest about which numbers to trust
is a core product requirement, not a disclaimer to bury.

## Brand Personality

An instrument, not an app. Three words: **precise, fast, honest.** The voice is
terse and expert — it assumes the user knows PoE2 and PoB and does not explain
the basics. It should feel like a focused desktop tool a theorycrafter keeps
open next to PoB — game-adjacent, dark, data-dense — not a consumer product and
not a marketing site. Confidence through restraint: it earns trust by being
accurate about its own limits, not by looking impressive.

## Layout (the LEBO shell)

Fixed application grid, desktop-first (min 1280×720):

```
┌───────────────────────────────────────────────────────────┐
│ AppHeader (44px): logo · nav · engine/PoB-version status  │
├──────────┬──────────────────────────────────┬─────────────┤
│ Left     │ Center workspace                 │ Right       │
│ 272px    │ tabs: Tree | Gear | Skills |     │ 340px       │
│ (48px    │       Config | Import            │ (48px       │
│ collapse)│ Tree tab = PixiJS WebGL canvas   │ collapse)   │
│          │ (pan/zoom, allocate, diff mode)  │             │
├──────────┴──────────────────────────────────┴─────────────┤
│ StatusBar (28px): engine state · parity evidence date     │
└───────────────────────────────────────────────────────────┘
```

- **Left panel — the build.** Active-build card (class/ascendancy/level/main
  skill), build-section navigator with completion counts (Tree pts, Gear n/slots,
  Skills n, Config), loadout set switcher, saved builds, import (paste PoB code).
- **Center — the workspace.** One tab visible at a time; tree canvas stays
  mounted. Tab badges carry live counts. Keyboard: `1–5` switch tabs, `[`/`]`
  collapse panels, `o` focus Optimize, Ctrl+Z/Y tree undo/redo.
- **Right panel — the verdict.** Optimization intent slider (Juggernaut ↔ Glass
  Cannon) → weight bands; Optimize button; live run progress; ranked suggestion
  cards (score delta + cost + trust chip; hover cross-highlights canvas nodes);
  stat sheet with per-stat trust chips and before/after deltas.
- **The results comparison is still the product.** The before/after — table and
  tree diff — is the hero surface; everything else is setup for it.

## Design Tokens

Adopted from LEBO's validated system (`D:\Projects\LEBOv2\lebo\src\assets\styles\global.css`),
with game colors swapped to PoE2 canon from PoB itself (`external/pob-engine/src/Data/Global.lua:7-81`).
Tailwind v4 CSS-first `@theme`; never hardcode these hex values inline — route
rarity/element colors through one utility module.

**Surfaces** — `--color-bg-base #0a0a0b`, `--color-bg-surface #141417`,
`--color-bg-elevated #1c1c21`, `--color-bg-hover #252530`, `--color-bg-sunken #060607`.

**Accent (gold)** — `--color-accent-gold #C9A84C`, `-soft #D4B96A`, `-dim #8B7030`;
tint `rgba(201,168,76,0.12)`, glow `rgba(201,168,76,0.28)`.

**Text** — primary `#F0EAE0`, secondary `#9E9494`, muted `#5A5050` (muted is for
disabled/decoration only — body text must hold WCAG AA on its surface).

**Tree node states** — allocated `#C9A84C` (gold), available `#4A7A9E` (blue ring),
locked `#2A2A35`, suggested-gold `#7B68EE`→ replace with gold pulse + purple only
for AI-suggested tier if both appear together; suggested-silver `#C0C6D2`.
Diff mode: added `#5EBD78` ring, removed `#E85E5E` ring (always paired with +/− glyphs).

**PoE2 rarity (from PoB canon)** — normal `#C8C8C8`, magic `#8888FF`, rare
`#FFFF77`, unique `#AF6025`, gem `#1AA29B`, currency `#AA9E82`, enchant `#B8DAF1`,
crafted `#5CF0BB`, fractured `#A29160`.

**PoE2 elements/pools (from PoB canon)** — fire `#B97123`, cold `#3F6DB3`,
lightning `#ADAA47`, chaos `#D02090`; life `#E05030`, mana `#7070FF`,
energy shield `#88FFFF`; positive `#33FF77`, negative `#DD0022`.

**Trust chips** — reliable: quiet outline chip; approx: subdued; estimate: amber —
each chip's tooltip cites its evidence ("22/22 builds within 0.1% vs PoB 0.15.0,
2026-07-xx"). Trust is never encoded in color alone.

**Type** — UI: `Inter Variable, system-ui, sans-serif`; numbers/code:
`JetBrains Mono Variable, monospace` (self-hosted woff2, no CDN). Base size
13px, line-height 1.45. All stat columns right-aligned, tabular-nums, mono.

**Shape & density** — radii 3/5/8/12px (`--r-sm..--r-xl`); padding 12px default,
8px tight, 16px loose; hairline borders `rgba(255,255,255,0.06)` (strong: 0.1).
Dense by default: this audience wants numbers tightly packed and scannable.

**Motion** — gold pulse on Optimize (~1.8s period), suggestion-hover node pulse
(1.2s), 150ms panel transitions. Everything honors `prefers-reduced-motion`.
Focus: 2px gold `:focus-visible` outline everywhere.

**Intent slider** — track gradient Juggernaut `#2A4D7A` → Glass Cannon `#C73232`,
16px gold thumb, zone label + weight readout below ("65% Damage / 35% Survival").

## Anti-references

Must NOT look AI-generated or like a generic SaaS product. Avoid every "AI
slop" tell: lavender/violet→blue gradients, glassmorphism, gradient text,
centered marketing hero with a badge above the H1, emoji nav icons,
shadcn-default-everything, the same drop-shadow on every element,
colored-left-border cards, cards-nested-in-cards, and low-contrast gray-on-dark
body text. Not a generic analytics dashboard (bento grids, vanity stat tiles).
Not a landing page — the user is already here to work. Also not a pixel-clone
of PoB's 2013-era chrome: PEBO borrows PoB's *mental model* (tabs, sidebar
stats, comparison tooltips) with LEBO's modern instrument styling.

## Design Principles

- **Trust over polish.** Evidence-backed trust tiers are first-class UI. A
  number without a tier is a bug.
- **Density is a feature.** Tabular, right-aligned, glance-comparable data;
  no whitespace theater.
- **PoB-adjacent familiarity.** Tabs, sidebar stats, hover comparison deltas —
  conventions this audience already knows. Lossless round-trip with PoB is
  sacred; a single corrupted export permanently kills trust.
- **The engine decides, the AI explains.** Every suggestion renders fully from
  deterministic engine data; narration is additive, grounded, and optional
  (fully functional offline).
- **Speed to insight.** Paste → verdict in seconds; long scans stream
  incrementally (first slot in seconds, never a blank spinner).
- **Strictly better at every milestone.** Each release must beat the previous
  state even if work stops there (see master plan cut-lines).

## Accessibility & Inclusion

Target WCAG AA contrast on all body text and stat values — explicitly reject
the low-contrast dark-mode tell. Never encode meaning (improvement vs
regression, estimate vs reliable, allocated vs suggested) in color alone; pair
it with a sign (+/−), a label, or an icon so it survives color blindness — the
PoE2 rarity/element palette is decorative reinforcement, not the sole channel.
Respect `prefers-reduced-motion` for all pulses/progress animation. The PixiJS
canvas is invisible to screen readers: mirror allocation state and suggestion
focus into an aria-live region, and keep every canvas action reachable via
keyboard (search → focus node → allocate).
