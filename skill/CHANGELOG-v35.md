# Cowork ROI Report — v35

Adds a built-in **CSV export** so every report now emits a session-level data file
alongside the HTML.

## New: `scripts/to_csv.py`
- Emits `output/cowork-sessions.csv` — a tidy, **single-grain** export: **one row
  per session** (the atomic unit everything rolls up from). Because it is
  single-grain, `SUM(value_usd)` over the file is the real total with **no
  double-counting** — the category/process/role rollups stay in the report, not
  appended here.
- 28 columns: run/window identity, process, JTBD, value pillar, category (primary +
  full pipe-delimited list), conversational flag, run-task / input / output counts,
  `total_interactions`, skills, professional roles, hours, value, speed, credits,
  cost, and the full **Cowork-fit hybrid** (grade, method, rule_grade, label,
  surfaces, why).
- CSV hygiene: UTF-8 **with BOM** (Excel renders ×, — correctly), every field
  quoted, ISO dates, pipe-delimited multi-value fields, stable column order, a
  `run_id` on every row for safe appends across weekly runs.
- **Blanks are honest n/a:** `credits`/`cost_usd` without cost telemetry;
  `total_interactions` without the live-session telemetry hook.

## Supporting change: `scripts/compute.py`
- Each session (goal) in the payload now also carries `n_inputs`, `n_outputs`,
  `skills`, and `total_interactions` (from a new telemetry-turns lookup =
  user + assistant turns), so `to_csv.py` reads a **single source** (the payload)
  with no re-joining.

## Wiring
- Workflow step 5 now runs `to_csv.py` after `build_report.py`; step 6 tells the
  user both the HTML report and the CSV are saved. `to_csv.py` added to Bundled
  files.

No methodology, category, or grade-logic change. SKILL.md stays under 20,000 chars
with a 2,000 buffer; description 960.
