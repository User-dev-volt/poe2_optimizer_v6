# Product

## Register

product

## Users

Hardcore Path of Exile 2 theorycrafters — players who already live inside Path
of Building (PoB) and optimize builds by hand. They arrive with a PoB import
code and a specific question: *"can I do better with the points I have?"* Their
context is PoB open on a second monitor; they will cross-check our output
against PoB in real time. They value information density, scan-speed, and
precision, and they instantly distrust anything that looks polished but is
wrong.

## Product Purpose

A localhost tool that takes a PoB build, discovers a stronger passive-tree
allocation within a points/respec budget, shows a before/after comparison, and
exports an optimized PoB code. It exists to answer *"is there a better tree?"*
faster than doing it by hand. Success = a PoB power-user trusts the relative
improvement, gets the answer in seconds, and exports it back into PoB.

Critical constraint: the underlying calculator is currently a **relative**
engine — the optimizer's *improvement %* and tree changes are trustworthy, but
absolute stats (DPS magnitude, resistances, EHP, evasion, armour) are
approximate estimates. Being honest about which numbers to trust is therefore a
core product requirement, not a disclaimer to bury.

## Brand Personality

An instrument, not an app. Three words: **precise, fast, honest.** The voice is
terse and expert — it assumes the user knows PoE2 and PoB and does not explain
the basics. It should feel like a focused desktop tool a theorycrafter keeps
open, not a consumer product and not a marketing site. Confidence through
restraint: it earns trust by being accurate about its own limits, not by
looking impressive.

## Anti-references

Must NOT look AI-generated or like a generic SaaS product. Avoid every "AI
slop" tell (per Impeccable's catalog): "VibeCode" lavender/violet→blue
gradients, glassmorphism, gradient text, a centered marketing hero with a badge
above the H1, emoji nav icons, shadcn-default-everything, the same drop-shadow
on every element, colored-left-border cards, cards-nested-in-cards, and
low-contrast gray-on-dark body text. Also NOT a generic analytics dashboard
(bento grids, oversized vanity stat tiles). It is not a landing page — there is
nothing to sell; the user is already here to work.

## Design Principles

- **Trust over polish.** Being visibly honest about which stats are reliable
  beats looking impressive. The "estimate — not PoB-accurate" flags are
  first-class UI, not fine print.
- **Density is a feature.** This audience wants numbers, tightly packed and
  scannable — not whitespace and hero sections. Prefer tabular, right-aligned,
  glance-comparable data.
- **PoB-adjacent familiarity.** Borrow the mental model and rigor of Path of
  Building so users feel at home; do not reinvent conventions they already know.
- **Speed to insight.** The path from "paste code" to "see the better tree"
  should be the shortest possible. Every screen serves the current task and
  nothing else.
- **The results comparison is the product.** The before/after table is the hero
  surface; input and progress are setup for it.

## Accessibility & Inclusion

Target WCAG AA contrast — explicitly reject the low-contrast dark-mode tell
(medium-gray body text on a dark background) that fails WCAG. Never encode
meaning (improvement vs regression, estimate vs reliable) in color alone; pair
it with a sign (+/−), a label, or an icon so it survives color blindness.
Respect `prefers-reduced-motion` for any progress animation.
