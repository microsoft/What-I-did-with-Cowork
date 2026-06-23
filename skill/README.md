# Cowork ROI — Personal Impact Report (skill)

Generates a **"What Cowork Did for Me"** single-file HTML report from a user's own
Copilot Cowork session history in OneDrive. It quantifies the leverage Cowork provided
as a **speed multiplier** and a **professional-services-equivalent value**, using an
artifact-scaled time model anchored in published research.

> **v14 (single self-contained skill).** The package is one self-contained skill — the
> standard *attach-zip → "Add this skill"* flow installs it cleanly. The `map-my-work`
> workflow-mapping logic is **folded in as bundled references** (`references/`) and runs
> **inline** to derive each user's own Jobs ▸ Business Processes ▸ Value Pillars ▸ JTBD —
> no separate skill install, still fully personalized per user. See
> [`CHANGELOG-v14.md`](CHANGELOG-v14.md) (and v13 / v11 / v6 / v5) for the history.

---

## Contents

```
cowork-roi-report/
├── SKILL.md                     # skill definition + workflow (loaded by Cowork)
├── README.md                    # this file
├── CHANGELOG-v14.md             # latest — single self-contained skill, four value pillars
├── CHANGELOG-v13.md             # bundle + rich {process, pillar, job, jtbd} override
├── CHANGELOG-v11.md             # TF-IDF APQC classifier, skills-augmented, cost capture
├── CHANGELOG-v6.md / -v5.md     # earlier history
├── references/
│   ├── map-my-work-playbook.md  # derives the user's own taxonomy (runs inline at step 4b)
│   └── value-pillars.md         # four-pillar crosswalk — single source of truth
├── scripts/
│   ├── mine_session.py          # live-session telemetry (Stop hook): exec_min, tool intensity, artifacts
│   ├── statusline_cost.py       # per-session cost capture (statusLine hook)
│   ├── classify.py              # category + business-process classifier; preserves skills tags
│   ├── compute.py               # applies the methodology -> payload JSON
│   ├── build_report.py          # renders the self-contained HTML report
│   ├── apqc_taxonomy.json       # generic APQC 13 fallback (used when map-my-work isn't run)
│   └── skills_vocabulary.json   # controlled DOMAIN_SKILLS + TECH_SKILLS vocabulary
└── examples/
    └── sample_sessions.json     # synthetic input (safe to share)
```

## Install

1. **Download** `cowork-roi-report-skill-v14.zip` from the latest release. *(No need to unzip — attach it as-is.)*
2. **Open** a new [Copilot Cowork](https://copilot.cloud.microsoft/cowork) session.
3. **Click the ➕ (plus) symbol** to attach the zip, then send: **"Add this skill."**
4. Once it's added, ask: **"Generate my impact summary report."** It'll ask one quick question — which period to measure (**7, 15, or 30 days**) — then build your report.

## Run the scripts directly

```bash
python scripts/compute.py     --in working/cowork_sessions.json --out working/cowork_roi_data.json
python scripts/build_report.py --data working/cowork_roi_data.json --out output/cowork-roi-report.html
```

No third-party dependencies — standard-library Python 3 only.

---

## Input schema (`cowork_sessions.json`)

The skill harvests Cowork session workspaces from OneDrive
(`Documents/Cowork/sessions/<uuid>/input` and `/output`) and writes this:

```jsonc
{
  "meta": {
    "user": "Jane Doe",
    "email": "jane@contoso.com",
    "generated": "2026-06-08",
    "window": { "from": "2026-04-09", "to": "2026-06-08", "label": "Last 60 days", "months": 2 },
    "hourly_rate": 72
  },
  "sessions": [
    {
      "id": "8836abd1",
      "date": "2026-04-27",
      "hour": 12,                       // 0–23, user's local time
      "goal": "Synthesize team deck from 8 reports",
      "inputs":  [ {"name": "report-1.pdf", "ext": "pdf"} ],          // analyzed
      "outputs": [ {"name": "deck.pptx", "ext": "pptx",
                    "skills": ["Presentation Design", "Data Analysis"] } ], // produced + skills tags
      "skills":  ["Stakeholder Communication"],                       // session-level (chat-only) skills
      "tasks":   ["analysis", "document"],                            // category keys
      "has_folder": true,
      "exec_min": 22                                                  // measured run time (telemetry), or null
    }
  ]
}
```

- **Skills tags (required for the skill tables).** Each `outputs[]` item carries a `skills:[...]`
  array drawn **only** from the controlled vocabulary in `scripts/skills_vocabulary.json`
  (`DOMAIN_SKILLS` + `TECH_SKILLS`); output-less / chat-only sessions carry a session-level
  `skills:[...]`. `compute.py` rolls these into the *Skills augmented* bars and the per-deliverable
  table. Without tags those tables render empty. Tag conservatively, evidence-based — never invent
  a skill outside the vocabulary.
- **Business process / pillar overrides (`scripts/process_overrides.json`).** Written *before*
  `classify.py` runs, this maps each session id to a **rich tuple** derived live by the map-my-work
  playbook (back-compat: a plain `"<id>": "Process"` string is still accepted):

  ```json
  { "<session_id>": { "process": "…",
                      "pillar":  "Revenue Growth|Cost Reduction|Risk Mitigation|Transformation",
                      "job":     "…",
                      "jtbd":    "…" } }
  ```
  `classify.py` consumes these directly; `pillar_css` is derived from the pillar name. If the
  playbook isn't run, `classify.py` falls back to the generic APQC framework in
  `scripts/apqc_taxonomy.json` (Job = "Other", default pillar).

### Task category keys
`analysis · document · email · meeting · comms · special · code · general`

---

## Methodology — the two-clock model

Each session is scored on two clocks; the ratio is the speed multiplier.

**Expert clock (unassisted)** — what a professional would take with no AI:

```
expert_min =  Σ analysis-band per analysis task        (research-anchored, v4)
            + Σ general-band per general task
            + Σ read_time(input)     ( 12 min / document,  5 min / image )
            + Σ author_time(output)  ( deck 45 · doc 40 · sheet|page|code 35 · other 30 )
```

`document` tasks contribute **only** through their output authoring time (so authoring is
never double-counted with the analysis band).

**Assisted clock (your time)** — a modeled estimate of hands-on effort:

```
assisted_min = 8  (fixed prompt/setup)  +  2 × (num inputs + num outputs)     (floor 4)
```

**Headline metrics:**

```
speed_multiplier            = Σ expert_min / Σ assisted_min          (rate-independent)
professional_services_value = (Σ expert_min / 60) × hourly_rate
```

**Conservative / Optimistic range** re-runs the expert clock with the published floor/ceiling
analysis bands and lighter/heavier read & authoring weights.

### Research-anchored category bands (min saved / task)

| Category | Low | **Typical** | High |
|---|---:|---:|---:|
| Analysis & Research | 30 | **67** | 92 |
| Document & content creation | 12 | **24** | 42 |
| Email workflows | 3 | **7** | 12 |
| Meeting workflows | 12 | **31** | 43 |
| Communication workflows | 2 | **4** | 11 |
| Specialized workflows | 10 | **25** | 40 |
| Write or debug code | 30 | **56** | 96 |
| General assistance / Other | 2 | **5** | 8 |

Full source citations (Stanford-WB, Microsoft Research, NBER, Forrester, etc.) are embedded
in the report's Glossary and in `build_report.py`.

---

## Output (HTML report sections)

- **Hero** — speed multiplier (conservative/typical/optimistic) + professional-services value, with a live hourly-rate control and a Download-PDF button
- **Value at a glance** — business-value table mapping impact to the **four value pillars** (Revenue Growth · Cost Reduction · Risk Mitigation · Transformation), each pairing a business outcome (lagging KPI) with a Cowork indicator (leading KPI) and your result
- **KPIs** — Cowork sessions, tasks completed, active days, expert-equivalent hours, hands-on hours
- **Work by business process** — one row per session, **banded by Job × Value Pillar** with a *job-to-be-done (JTBD)* sub-line. The process taxonomy is **derived live per user** by the bundled map-my-work playbook (from their own M365 footprint) — nothing hard-coded; falls back to the generic APQC framework if the playbook isn't run. A **session-cost column** shows actual Cowork spend where captured, and **auto-hides** when no session has cost data. **Chat-only sessions** (no saved file) are counted via telemetry.
- **By category** — where the expert-equivalent time went (research-anchored bars)
- **Skills augmented** — the professional skills Cowork put to work (Presentation Design, Technical Writing, Data Analysis, Financial Modelling, Frontend Development, …), each with the expert-equivalent hours covered — turning time saved into *capability* without added headcount
- **Deliverables & the skills behind them** — every artifact produced, the skills that went into it, and the expert effort attributed to each
- **Analyzed → Produced** — sources you fed in (by type) vs. deliverables produced (by type), with sources-distilled-per-deliverable
- **Methodology & glossary** — every band traceable, with clickable research sources

---

## Business value — the four value pillars

Every session's impact is expressed in one shared vocabulary, defined once in
[`references/value-pillars.md`](references/value-pillars.md) (the single source of truth, shared
with the map-my-work playbook):

| Pillar | Type | What it captures |
|---|---|---|
| **Revenue Growth** | Tangible · money coming in | Demand created, converted, monetised — opportunities, win rates, pricing, faster deal cycles |
| **Cost Reduction** | Tangible · money going out | Inefficiencies eliminated, manual work automated, spend optimised |
| **Risk Mitigation** | Intangible · losses avoided | Issues detected earlier, controls improved, faster correction |
| **Transformation** | Intangible · new ways of working | Better/faster decisions, responsive operations, stronger collaboration, AI-workflow adoption |

The pillar per session is chosen by an **intent-verb rule** (the work's JTBD); when no intent signal
fires, the **process default** applies. Never force-fit a tangible pillar onto work with no money
signal; pillars with no qualifying work render as zero, not hidden.

## Skills augmented & the required tagging step

The *Skills augmented* and *Deliverables* tables are populated from explicit **skills tags** on the
harvested sessions. Tagging is a **required harvest step** (without it those tables render empty):

- Draw skills **only** from the controlled vocabulary in
  [`scripts/skills_vocabulary.json`](scripts/skills_vocabulary.json)
  (`DOMAIN_SKILLS` + `TECH_SKILLS`, borrowed from `microsoft/What-I-Did-Copilot`).
- Tag each `outputs[]` item with a `skills:[...]` array; tag chat-only sessions at session level.
- The in-loop agent supplies the judgment (semantic tagging from the deliverable); the vocabulary
  constrains the output. Tag conservatively and evidence-based — never invent a skill not in the list.
- `classify.py`'s `norm()` preserves these tags; `compute.py` rolls per-deliverable skill-hours up
  into the aggregate bars (hours follow the artifact each skill is tagged on).

## Optional hooks — cost & telemetry (additive)

Two optional hooks enrich the report. Both are **additive** — the report renders fine without them;
they just add signal. Wire them in `settings.json` and activate with **`/hooks`** (or restart the
session) so the harness picks them up.

| Hook | Script | What it does |
|---|---|---|
| **statusLine** (cost) | `scripts/statusline_cost.py` | The harness pipes the live session cost to the statusLine command on every render. The script persists the authoritative `total_cost_usd` (verbatim — no calculation) to a de-duplicated per-session log (`/mnt/user-config/.claude/cowork-session-costs.json`). No `/usage` needed; the latest cumulative total wins per session. Surfaces as the **session-cost column** (which **auto-hides** when no data exists). |
| **Stop** (telemetry) | `scripts/mine_session.py --log …cowork-session-telemetry.json` | Runs on **every** session stop, upserting measured `exec_min`, tool intensity, artifacts, and a `produced_artifact` flag into a durable log — so **chat-only / folder-less sessions self-record** and are counted going forward. The harvest merges in any session not already covered by a OneDrive folder. Only the *live* session is minable at run time, so the log builds history forward (it can't backfill sessions predating the hook). |

---

## Caveats (state these in any readout)

- **Personalized at run time; nothing individual-specific in the skill.** The process / pillar / job /
  JTBD taxonomy is derived live from whoever runs the report (their own M365 footprint) — nothing in
  this skill is hard-coded or borrowed from another person. Calendar items marked private surface only
  as a time block; the skill maps work, it never scores or ranks people.
- The **assisted clock is modeled**, not measured — OneDrive records artifacts, not keystroke time.
  Treat the multiplier as **directional**, not a stopwatch.
- Categories with **no saved artifacts** in the window are reported as **zero**, keeping totals a
  conservative floor.
- Counting stays conservative: ~2 run tasks per session; supporting files folded into the primary task.
