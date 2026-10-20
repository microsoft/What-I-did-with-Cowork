# CHANGELOG — v21

## Opening questions now ask about the live cost sweep

The skill's first `AskUserQuestion` is now **three** questions instead of two:
1. **Period** — 7 / 15 / 30 days (unchanged).
2. **Live cost (Copilot Credits)** — *new* — "Include the live `/cost` credit sweep so the report shows
   your real per-session cost and ROI?" Options: **Skip it (faster)** *(default)* or **Yes — read my real
   credits live**. Only when the user picks **Yes** does the agent run the step-3b `/cost` browser sweep
   before rendering (it's opt-in because it's slower and drives the browser). When skipped, the report shows
   research-anchored Time Saved + Value and the **Credits · cost** column auto-hides.
3. **Delivery** — run once / run + automate + email (the old Q2).

Guardrail added: never run the `/cost` sweep unless Q2 = Yes; on a headless scheduled run, reuse the ledger
or skip the cost column, never block.

- `SKILL.md` — step 1 rewritten to three questions; opt-in gate documented.

## Report redesign — section order, collapsible process views, deliverables skill filter

### New section order (after *Value at a glance*)
1. **Where the time went — by task category**
2. **Roles Cowork assembled for me**
3. **Work by business process**
4. **Deliverables & the skills behind them**

(Previously *Work by business process* led the four; it now sits third, directly before *Deliverables*.)

### Work by business process — collapsible groups
- **By Job-to-be-Done:** each **Job** is now a collapsible accordion showing only the job title, project
  count, and total hours; an **expand arrow** reveals the Processes ▸ JTBDs ▸ projects beneath it (the full
  detail shown previously).
- **By Business Value Pillar:** each **Pillar** is now its own collapsible accordion (pillar name + project
  count + total hours + arrow); expanding shows the project table for that pillar.
- Added **Expand all / Collapse all** controls next to the view toggle. Groups start collapsed for a clean
  overview.

### Deliverables & the skills behind them — filter by skill
- Added a **skill-filter chip bar** above the table (rendered when ≥2 distinct skills appear). Each chip shows
  a skill and its count; clicking filters the table to deliverables that used that skill. An **All** chip
  resets. A friendly "no deliverables match" line shows when a filter empties the table.
- Each row carries a `data-skills` attribute; filtering is pure client-side JS (no rebuild needed).

- `scripts/build_report.py` — section reorder; `<details>` accordions for both process views
  (`.wbp-acc`), `wbpExpand()` expand/collapse-all, per-pillar grouping (`pillar_acc_html` replaces the flat
  `pillar_rows` table), deliverables `dl-filter` chips + `dlFilter()` JS, supporting CSS.

## Unchanged
- v18–v20 methodology: RUNS × BAND value model, Cowork-app allow-list harvest (all three `Documents/Cowork/`
  layouts, never `Apps/`), version-base dedup, the real-credit `/cost` ledger + ROI banner (now gated behind
  the Q2 opt-in), classifier and compute logic.
