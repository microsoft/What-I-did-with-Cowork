# Cowork ROI Report — v32

Category assignment now follows the **Cowork usage taxonomy table**, plus Cowork-fit
clarity and several table/heatmap cleanups.

## Category choice is table-driven (`scripts/classify.py`)
Categories are now chosen from the taxonomy's Description/Examples, not the file type:
- **Analysis & Research** is assigned only from goal text describing analytical work
  (synthesizing findings, comparing options, briefings from multiple sources) — **not
  from a spreadsheet extension**. A built **spreadsheet/tracker is now Document &
  content creation** ("creating… organizing files"), where it belongs.
- Fixed a false-positive: the bare keyword **"roi"** no longer forces Analysis (it hit
  every "ROI report / ROI member" goal). Genuine ROI *analysis* still matches.
- Net on the sample window: the two trackers move Analysis → Document, "Install ROI
  member skill" → Specialized, and **Analysis & Research is empty** (correct — none of
  these were analytical work). Totals drop accordingly — more honest, less inflated.

## Cowork-fit clarity (`scripts/compute.py`, `build_report.py`)
- **"Cowork platform op" (unclear) renamed to "Managing Cowork"** with a plain-English
  meaning: *a Cowork admin task — installing, sharing or scheduling a skill or prompt;
  only Cowork can, but it operates the tool rather than producing business work.*
- **Every H/M/L dot now has a project-specific hover reason** (e.g. "This spans Outlook
  + Excel — no single Copilot works across apps"), not a generic label.
- The summary legend spells out H/M/L in color inline.

## Table / heatmap cleanups
- **JTBD removed** from the projects table (added noise, not value).
- **H/M/L badge removed from the Roles × projects heatmap** (it belongs in the projects
  table).
- The **Roles × projects heatmap now replaces the flat role list** directly under "Roles
  Cowork assembled for me" — one place for roles.

SKILL.md stays under 20,000 chars with a ≥2,000 buffer; description 960.
