# Cowork ROI Report — v28

Adds a **Cowork-fit H/M/L grade** to every project, answering: *did this project
need Cowork, or could a single surface-specific Copilot have done it?*

## New: the "single-surface test" (`scripts/compute.py`)
Deterministic scorer (`cowork_fit()`) — no LLM. Guiding question: **could one
in-app / surface-specific Copilot have done this end-to-end?**
- **H — Cowork-worthy**: it builds/packages a skill or app, runs a cross-system
  automation/connector/browser task, synthesizes >5 sources, **or spans ≥2
  Copilot surfaces** (e.g. Outlook + Excel) — none of which a single Copilot does.
- **M — Cowork-platform op**: install / share / schedule a skill or prompt.
- **L — Copilot-sufficient**: one surface-specific Copilot (Excel, Word,
  PowerPoint, Outlook, Teams, or chat) could have done it — the surface is named.
- "Produced an artifact" is deliberately **weak** (Copilot agent mode saves files);
  the methodology time-band is **not** used. Out-of-domain specialized roles
  (DevOps, SWE, Frontend, Architect vs a BVA/analytics job) are a supporting signal.
- Emits `cowork_fit` per goal and a `cowork_fit_summary` (H/M/L counts).

## New: badges + portfolio view (`scripts/build_report.py`)
- Every project row in **Projects by category** and the **Projects × Roles heatmap**
  carries an H/M/L badge with a "Could run in … Copilot" / "Cowork-only" /
  "Needs A + B Copilot" tooltip.
- A **portfolio summary** heads the section (e.g. *3 needed Cowork · 3 platform ops
  · 2 single-Copilot*). New glossary entry documents the test and its limits.

## Honest limitation
Grades are **heuristic and directional** — inferred from harvested artifacts,
systems and roles, not from measured tool telemetry (present for only some
sessions). Labeled as such in the report.

## Housekeeping
- SKILL.md documents the feature; kept at 18,000 chars (2,000-char buffer under the
  20,000 plug-in-validation limit); `description` unchanged at 960 (both gates pass).
