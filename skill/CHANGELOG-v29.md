# Cowork ROI Report — v29

Report-layout overhaul to **stop repeating the project list**. Same data,
methodology and grades as v28 — this is presentation only.

## Problem
The same ~8 projects were enumerated in four places (Work by business process,
Projects by category, the Roles × projects heatmap, and Deliverables & skills),
forcing a lot of scrolling and re-reading of the same list.

## Fix — one canonical "Your projects" table (`scripts/build_report.py`)
- A single **"Your projects" table** is now the only place projects are listed,
  positioned prominently under the KPI cards.
- **Group by** switch — **Process** (default), **Category**, **Pillar**,
  **Cowork-fit**, or **None** — regroups the rows **in place** (group header rows
  show sessions · hours · % of total). No more separate per-dimension sections.
- **Cowork-fit filter chips** (All / H / M / L) filter the same table.
- Columns: Project (+ process sub-line) · Cowork-fit badge · Category tags ·
  Roles · Hours · Value. Value recomputes live from the hourly-rate control.
- Rendered client-side from `DATA.goals` (already embedded); regroup/filter/rate
  changes re-render without adding anything to the page.

## Collapsed deep-dives
- The **Roles × projects heatmap** and **Deliverables & skills** table are now
  behind **show/hide toggles** (`<details>`), collapsed by default — the first
  read is short; the detail is one click away.

## Removed from the default view
- The Process ▸ JTBD ▸ Project accordion and the Projects-by-category fold
  (their content is fully covered by grouping the one table).

Net: ~6 project-listing blocks → **1 table + 2 collapsed panels**.
SKILL.md stays under the 20,000-char limit with a ≥2,000 buffer; description 960.
