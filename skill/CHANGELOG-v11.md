# Cowork ROI Report — v11 changelog

Cumulative changes since v6, consolidated into the v11 package.

## Classification & business value
- **TF-IDF APQC classifier** (`classify.py` + `apqc_taxonomy.json`) replaces the hand-tuned
  keyword lexicon. Business processes are matched by cosine similarity against the APQC Process
  Classification Framework (13 categories) — handles plurals, synonyms, abbreviations.
- **Value pillar is data-driven**: each APQC category carries a `value_pillar` + `pillar_css`
  field in the taxonomy (Improved Performance / Cost Savings / Innovation / Risk Mitigation).
  No hardcoded pillar map in the renderer.

## Methodology
- Bands aligned to **Cowork_Methodology_Walkthrough 0605**: Analysis Typical 71→**67**
  (Stanford-WB basket mean), Meeting High 45→**43**, Communication High 6→**11**.

## Skills augmented (method borrowed from microsoft/What-I-Did-Copilot)
- `skills_vocabulary.json` — controlled DOMAIN_SKILLS + TECH_SKILLS vocabulary.
- Skills are tagged **per deliverable** by the in-loop agent (mirrors their gpt-4o-mini step;
  no external API). Aggregate skill-hours roll up from the per-deliverable tags.

## Report sections
- **Value-at-a-glance summary table** (Improved Performance / Cost Savings / Innovation) modeled
  on the BVM Value Ladder (lagging KPI / leading KPI / your result).
- **Work by business process** grouped by value pillar with colored section headers; neutral-gray
  process pills, teal Improved-Performance accent (no color collisions).
- **Session cost column** — shows the real `/usage` figure captured by the statusLine hook, or
  "data not available" for sessions predating cost logging.
- **Skills augmented** moved up (after "Where the time went").
- **Deliverables & the skills behind them** — per-artifact table: deliverable → skills → expert
  hours (hours sum back to session totals; chat-only sessions appear only in the skill bars).
- **Activity heatmap removed**; circular phase-breakdown removed.
- 0-task categories relabeled honestly ("authoring time · N deliverables").

## Cost capture (statusLine)
- `statusline_cost.py` taps the harness-provided `cost.total_cost_usd` on every render and writes
  a de-duplicated per-session log (`/mnt/user-config/.claude/cowork-session-costs.json`). No
  calculation; latest cumulative wins on session re-entry. Wired via `settings.json` statusLine.

## Robustness fixes
- **Cowork folder discovery**: locate `/Documents/Cowork*` dynamically (handles `Cowork 1`,
  localized names) instead of assuming a fixed path; glossary text no longer hardcodes a folder.
- SKILL.md guardrail: run each pipeline script as its own command (avoids false "Failed" markers
  from bundled schema-guessing snippets).
