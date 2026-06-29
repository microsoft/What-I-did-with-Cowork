# CHANGELOG — v19

## Real per-session cost: the `/cost` browser sweep + Credits·cost column

**The problem.** Cowork's true cost unit is **Copilot Credits** (`/cost` → "N credits used for this task so
far"), priced at **1¢/credit** (PAYG list). That number is **rendered client-side and never persisted** —
not in the OneDrive session records, not in any hook payload, not in the agent transcript, and `/cost`
output never reaches the agent. It also **can't be recomputed** without Microsoft's exact 4-component rate
card (model use · context retrieval · tool calls · runtime); any token×rate estimate fails to reconcile to
`/cost`. So earlier versions could only show a research-anchored *value*, never the real *cost*.

**The fix — read the live `/cost` with the browser, hands-free (new step 3b).** The agent itself drives the
browser to the web Cowork app, opens each in-window session, types `/cost`, screenshots the result, and
reads the credits off the image — no copy-paste, no typing from the user. Captured values land in a durable
ledger (`cowork-session-credits.json`); `compute.py` reads it and attaches `credits` + `cost_usd`
(= credits × $0.01) per session; `build_report.py` renders a **"Credits · cost"** column.

Key facts established and encoded:
- **Reopening a prior session shows its real running total** (verified live) — so past sessions are
  capturable, not just the active one.
- **Surface-independent:** the sweep drives *web* Cowork (`m365.cloud.microsoft/agents/cowork`), which
  exposes the same sessions and the same `/cost` whether the user normally uses the browser or the native
  Copilot app. Requirements: browser-automation available + local browser signed into M365 Copilot.
- **1 credit = 1¢** (Microsoft GA pricing, pay-as-you-go list; P3 commitment pays less) — the only math
  applied; credits → dollars is exact, not estimated.

**Guardrails.** Never estimate or fabricate a credit number. If the browser isn't available (e.g. a headless
scheduled run), reuse the ledger's last values or ask the user to paste/screenshot `/cost`.

## Files touched
- `SKILL.md` — new **step 3b** (the `/cost` browser sweep + ledger + fallbacks).
- `scripts/compute.py` — `load_credits_lookup()`; attaches `credits` and `cost_usd` (credits × $0.01) per session.
- `scripts/build_report.py` — **"Credits · cost"** column (credits with the dollar equivalent beneath).

## Unchanged
- v18 harvest (Cowork-app allow-list, all three `Documents/Cowork/` layouts, never `Apps/`).
- Methodology bands, classifier, value model.

## Display additions (cost surfaced everywhere)
- **Per-project cost in the Job-to-be-Done view** — each project in the Job ▸ Process ▸ JTBD tree now shows its real `credits · $cost` next to hours/value/speed (the Pillar view already had the column).
- **ROI banner** — real Copilot-credit cost vs research-anchored value, with the return multiple (value ÷ cost) and net %.

## Value model corrected to RUNS × BAND (methodology-deck-anchored)
- Per the Cowork Time-Savings methodology deck, every category band is **minutes saved per RUN**, with the
  activity-instance chain already summed inside it (code 56 = write+test+debug = 18min×3; doc 24 = 6.1×4).
  So the expert clock = **Σ runs × band** — no per-LOC valuation, no per-artifact authoring add-on (both
  double-count the chain). Reverted the interim LOC/authoring experiments.
- **Run counts come from the agentic tool-chains** (telemetry-grounded): code run ≈ 6 code-edits,
  analysis run ≈ 5 research-tool calls. `mine_session.py` now emits a `runs:{category:count}` field;
  `classify.py` passes it through; `compute.py` applies `Σ runs × CATS[band]`. Sessions without telemetry
  use conservative estimates, labeled as such.
- Iterative versions of the same artifact still collapse to one distinct deliverable (version-base dedup).
