# Cowork ROI Report — v30

**Bug fix + declutter** for the single "Your projects" table introduced in v29.

## Bug fixed — empty projects table
v29 rendered the table client-side from `DATA.goals`, but the embedded payload
only carried `{rate, hours}` — so `DATA.goals` was empty and the table came up
blank. Fix:
- `compute`/`build_report` now embed a **slim `goals` array** in the client payload.
- Rows are also **rendered server-side** at build time, so the table is populated
  even before any JavaScript runs (never blank). Client JS re-renders only on
  regroup or hourly-rate change.

## Cleaner layout
- **Group-by control is now a single dropdown** (Process default / Category /
  Pillar / Cowork-fit / None) — replaces the row of five buttons.
- **Cowork-fit filter chips removed** — Cowork-fit is still a grouping option and
  every row still carries its H/M/L badge; the separate filter row is gone.
- **"Value at a glance" pillar table is hidden** behind a show/hide toggle (was
  a large always-on block above the projects).
- **Category column dropped** from the table — category is available by grouping,
  so the default list is lighter (Project · Cowork-fit · Roles · Hours · Value).

Net: fewer always-on blocks and controls; the first read is one headline area +
one clean, populated project list. Deep-dives (Value-at-a-glance, heatmap,
deliverables) are all one click away.

SKILL.md stays under the 20,000-char limit with a ≥2,000 buffer; description 960.
