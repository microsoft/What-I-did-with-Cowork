# CHANGELOG — v23

## Process-anchored taxonomy + durable taxonomy memory

This version makes **Business Process the aggregation anchor**, drops the standalone **Job** layer, and
adds a **durable taxonomy memory** so process/project names stay stable across runs instead of being
re-invented each time.

### Taxonomy restructure — Process is the anchor; Job layer dropped
- The "Work by business process" section now rolls up as **Business Process ▸ JTBD ▸ Project**
  (was Job ▸ Process ▸ JTBD ▸ Project). The standalone **Job** layer is gone.
- `build_report.py` — VIEW 1 rebuilt to a Process-anchored tree: **projects nest under their JTBD**, so
  a process with several JTBDs renders several indented groups. Each process shows a subtotal
  (**sessions · hours · value · % of time**). New indented hierarchy: Process (accordion header) →
  **bold JTBD** with a colored guide line → **unbolded, further-indented projects** with a dotted guide
  line. The **By process** view is the default; **By pillar** remains as a secondary toggle. The Job
  references were removed from the pillar-view rows.
- `compute.py` — the `processes[]` rollup carries a new `pct_time` field.
- The anonymized (`--anonymize`) path is unchanged for now (member / aggregated skills adopt the
  Process anchor in a later pass; they still read `process_overrides.json`).

### Durable taxonomy memory (align-first, create-if-novel)
- **New** `scripts/reconcile_taxonomy.py` — runs BEFORE `classify.py`. For each session it: (a) matches
  a known **Project** (exact slug or near-identical title) and reuses its `{process, pillar, jtbd}`;
  else (b) matches an existing **Process** by keyword similarity (reusing `classify.py`'s TF-IDF helpers)
  and reuses `{process, pillar}` + the process default JTBD, registering a new project under it; else
  (c) mints a **new Process** (flagged `"new": true`). Writes `process_overrides.json` and **persists the
  updated registry**.
- **New durable file** `~/.claude/cowork-process-registry.json` — canonical Processes (name · pillar ·
  keywords · default JTBD) + known Projects (title → process + jtbd). Read first, aligned to, and
  persisted every run. Memory-first rule: a run a week later locates the registry and aligns to it;
  only truly novel work adds a name.
- `process_overrides.json` keeps a `job` field (= process name) only for back-compat with the
  not-yet-migrated member skill — it is no longer surfaced in this report.

### What's unchanged
- The artifact-scaled two-clock methodology (v4 bands), the Cowork-app allow-list harvest across all
  three OneDrive layouts, KPIs, value-at-a-glance pillars, where-the-time-went by task category, roles,
  deliverables-and-skills, activity heatmap, glossary with clickable sources, live hourly-rate control,
  and Download-PDF — all as before. Numbers still come only from `compute.py` (no hand math).

- `SKILL.md` — step 4b rewritten to be registry-driven (align-first, create-if-novel); bundled-files and
  durable-files lists updated.
