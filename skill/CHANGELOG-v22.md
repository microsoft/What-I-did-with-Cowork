# CHANGELOG — v22

## Removed Copilot-credits (no credits question, no `/cost` sweep)

This version drops the live Copilot-credits feature that v21 added. The report stays the **full, detailed
personal impact report** — project names, deliverables, the Job ▸ Process ▸ JTBD work-by-process view, roles,
and skills are all shown, exactly as before. The only change is that credits are gone.

### What's removed
- **The credits question.** The opening `AskUserQuestion` is back to **two** questions — **Period**
  (7 / 15 / 30 days) and **Delivery** (run once / run + automate + email). The v21 "Live cost (Copilot
  Credits)" question is gone.
- **The `/cost` browser sweep (old step 3b).** The skill no longer drives the browser to read
  "N credits used for this task so far", no longer writes the credits ledger, and never prompts you to
  paste/screenshot `/cost`.
- **No credits / cost line in the report.** With no live reading, the **Credits · cost** column and the
  ROI banner stay hidden (the renderer already auto-hides them when there's no cost data). Nothing is
  fabricated.

### What's unchanged (still the full detailed report)
- Speed multiplier + professional-services value, KPIs, Value-at-a-glance pillar table.
- Where-the-time-went by task category, Roles Cowork assembled, Work by business process
  (Job ▸ Process ▸ JTBD ▸ projects, and the By-Pillar view), Deliverables & the skills behind them,
  activity heatmap, methodology glossary with clickable sources.
- The artifact-scaled two-clock methodology (v4 bands), the Cowork-app allow-list harvest across all three
  `Documents/Cowork/` layouts, version-base dedup, and the classifier/compute logic.

- `SKILL.md` — step 1 back to two questions; the step-3b `/cost` sweep section removed; no credits/cost
  references in the workflow, scheduling, or email steps.
- `scripts/build_report.py` — unchanged renderer (the dormant `--anonymize` team-safe mode remains available
  but is **not** used by this personal skill).
