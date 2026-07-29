# Cowork ROI Report — v27

Adds a **Projects × Roles heatmap** to the report. No change to the methodology,
the 8 categories, the bands, or the value model — this is an added visualization.

## New: Projects × Roles heatmap (`scripts/build_report.py`, `scripts/compute.py`)
- A heatmap section renders directly **after the "Roles Cowork assembled for me"** list.
- **Projects on the Y axis (rows)** — sorted by hours, and the rows area is **scrollable**
  (`max-height`, sticky header + sticky first column) so it scales to **dozens of projects**
  over a long window without breaking the layout.
- **Roles on the X axis (columns)**, capped at **top 7 by hours**; any remaining roles fold
  into a single **Other** column. (`RP_TOP_N = 7` in `build_report.py` — change it in one place.)
- **Each cell** = that role's expert-equivalent hours in that project. A project's hours are
  split **evenly across the roles it needed** (same rule as the Roles list), so the column
  footers ("Role total") reconcile exactly with the Roles section, and the row totals ("Total")
  reconcile with each project's hours.
- Cell shade scales light→deep blue by hours; a legend and an "Other = …" note sit below.
- **`compute.py`** now emits `professional_roles` on each goal object so the renderer has the
  per-project roles it needs (previously only the rolled-up totals were in the payload).

## Housekeeping
- `import collections` added to `build_report.py` (used by the heatmap aggregation).
- SKILL.md documents the new section; kept at **17,991 chars** — a ≥2,000-char buffer under the
  20,000 limit — and `description` stays 960 chars (both plug-in-validation gates still pass).
