# CHANGELOG — v20

## Value model finalized: RUNS × BAND (anchored to the Cowork Time-Savings methodology deck)

The expert clock is now exactly what the methodology deck specifies and nothing else:

> **Time saved = Σ over RUNS of each run's category band** (minutes *saved per run*).

Each research-anchored band already **sums the activity-instance chain inside one run** — e.g. code 56 =
write + test + debug = 18 min × 3 steps; document 24 = 6.1 min × 4 instances (draft → rewrite → format →
polish). So the model **counts runs and multiplies by the band** — and deliberately does **not**:
- value code by lines of code (the deck: "≈ 56, *not per LOC*"), or
- add a per-artifact authoring/read anchor on top (that double-counts the chain already inside the band).

Both were interim experiments (v19 dev) and are reverted.

### Run counts come from the agentic tool-chains (telemetry-grounded)
- **code run ≈ 6 code-edit actions** (Edit / Write / MultiEdit / NotebookEdit)
- **analysis run ≈ 5 research-tool calls** (search / list / read / query / transcript)
- `mine_session.py` now emits a `runs:{category:count}` field per session from these chains;
  `classify.py` passes it through; `compute.py` applies `Σ runs × CATS[band]`.
- Sessions without telemetry use conservative estimates, labeled as such. The **run count** (and its two
  divisors) is the single transparent, auditable lever.

## Carried forward from v18–v19
- **Real per-session cost** — the `/cost` browser sweep reads Copilot Credits live and logs them; the report
  shows a **Credits · cost** column (credits × $0.01 list) and an **ROI banner** (value ÷ real cost) in both
  the JTBD and pillar views.
- **Cowork-app allow-list harvest** — all three `Documents/Cowork/` layouts, scoped by the Cowork app id,
  never `Apps/…` (Scout excluded).
- **Version-base dedup** — iterative versions of the same artifact (v6/v11/v17, report-v1/v2) collapse to one
  distinct deliverable.

## Files
- `scripts/compute.py` — `session_expert = Σ runs × band`; runs from `s["runs"]` (fallback 1 run/task).
- `scripts/mine_session.py` — emits `runs` from the write/test/debug & research tool-chains.
- `scripts/classify.py` — passes `runs` through.
- `SKILL.md` — step 4 documents runs × band + the run-counting rule.
