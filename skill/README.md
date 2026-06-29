# Cowork ROI — Personal Impact Report (skill)

Generates a Microsoft-branded **"What Cowork Did for Me"** single-file HTML report from your own
Copilot Cowork session history in OneDrive. It leads with **research-anchored Time Saved** and its
**professional-services-equivalent Value**, then maps your work to your own Jobs, Business Processes,
and the four Value Pillars.

> **v22:** removes the Copilot-credits feature (no credits question, no `/cost` browser sweep). The
> report stays the **full, detailed personal impact report** — only credits are gone. See
> [`CHANGELOG-v22.md`](CHANGELOG-v22.md).
>
> **v20:** value model is now **RUNS × BAND**, anchored to the Cowork Time-Savings methodology deck —
> time saved = Σ runs × each run's category band (the band already contains the write→test→debug /
> draft→rewrite→format→polish chain). Run counts come from the agentic tool-chains (telemetry-grounded:
> ~6 code-edits/code-run, ~5 research-calls/analysis-run). No per-LOC, no authoring add-on. See
> [`CHANGELOG-v20.md`](CHANGELOG-v20.md).
>
> **v19:** **real per-session cost** — the agent reads Cowork's `/cost` (Copilot Credits) by driving the
> browser to the web app, screenshotting each session's "N credits used for this task so far," and logging
> it to a durable ledger. The report gains a **"Credits · cost"** column (credits × **1¢/credit**, GA list).
> No estimation — the number can't be recomputed without Microsoft's exact rate card, so it's read live.
> Works whether you use the browser or the native Copilot app. See [`CHANGELOG-v19.md`](CHANGELOG-v19.md).
>
> **v18:** the harvest is now an **allow-list scoped to the Cowork app** — it reads **all three**
> `Documents/Cowork/` layouts (`Tasks/<goal>-<date>/`, root `<goal>-<date>/`, and legacy
> `sessions/<uuid>/`), counts only items created by the Cowork app id, and **never touches
> `Documents/Apps/…`** — so **Scout** activity (M365 Copilot app heartbeats, monitors, executive
> briefings) is excluded for every user with no per-instance name list. See
> [`CHANGELOG-v18.md`](CHANGELOG-v18.md).
>
> **v15:** the expert clock is purely research-anchored — Time Saved = the **sum of the cited per-task
> bands** (e.g. Analysis 67 + Document 24 = 91 min); the speed multiplier is a secondary stat. See
> [`CHANGELOG-v15.md`](CHANGELOG-v15.md).

---

## Get Started in 4 Steps

1. **Download** `cowork-roi-report-skill-v22.zip`. *(No need to unzip — attach it as-is.)*
2. **Open** a new [Copilot Cowork](https://copilot.cloud.microsoft/cowork) session.
3. **Click the ➕ (plus) symbol** to attach the zip file, then send: **Add this skill.**
4. Once it's added, ask: **Generate my impact summary report.**

You'll be asked which period to measure (7, 15 or 30 days), then the report is built. That's it. 🎉

---

## Contents

```
cowork-roi-report/
├── SKILL.md                     # skill definition + workflow (loaded by Cowork)
├── README.md                    # this file
├── CHANGELOG-v22.md             # latest — Copilot-credits feature removed (detailed report unchanged)
├── CHANGELOG-v20.md             # value model = runs × band (methodology-deck-anchored)
├── CHANGELOG-v19.md             # real /cost credits via browser sweep, Credits·cost column
├── CHANGELOG-v18.md             # Cowork-app allow-list harvest, Scout excluded
├── CHANGELOG-v15.md             # (+ v5/v6/v11/v13/v14/v15/v16 history)
├── scripts/
│   ├── classify.py              # deterministic classifier → inputs/outputs + tasks schema
│   ├── compute.py               # applies the methodology → payload JSON
│   ├── build_report.py          # renders the self-contained HTML report
│   ├── mine_session.py          # mines the live session transcript for real run-time (telemetry hook)
│   ├── apqc_taxonomy.json       # generic APQC fallback business-process taxonomy
│   └── skills_vocabulary.json   # controlled vocabulary for "skills augmented"
├── references/
│   ├── map-my-work-playbook.md  # derives your own Jobs ▸ Processes ▸ Workflows (run inline at step 4b)
│   └── value-pillars.md         # the four-pillar crosswalk
└── examples/
    └── sample_sessions.json     # synthetic input (safe to share)
```

`map-my-work` is **folded in** as a reference playbook — there is no second skill to install, and it
runs automatically when the report is generated.

---

## What counts as Cowork activity (harvest scope, v18)

The report measures **only Cowork** work, by **allow-list** — not by trying to recognise and subtract
everything else:

- **Reads only `Documents/Cowork/`**, across **all three** folder layouts the product has used:
  `Tasks/<goal>-<date>/`, root `<goal>-<date>/`, and legacy `sessions/<uuid>/` — each with `input/` +
  `output/`.
- **Counts only items created by the Cowork app** (`createdBy.application.id =
  6ab48b67-cd74-4ad4-81af-5932984589be`) — the same product app id for every user and tenant, so it's a
  robust signal that needs no per-user configuration.
- **Never enumerates `Documents/Apps/…`.** That tree is the **M365 Copilot app running Scout** —
  scheduled heartbeats, customer/needs monitors, and executive briefings (written by the generic
  *Microsoft Graph* app). Those are **not Cowork** and are excluded automatically, with no instance-
  specific name list to maintain.

Why allow-list, not deny-list: a "find Scout and remove it" rule keys on instance names like
`M - Internal Copilot App 1`, which differ per user and break on the next account. Scoping *positively*
to Cowork-app-created artifacts generalises cleanly.

---

## What's in the report

- **Hero** — research-anchored **Time Saved** (conservative / typical / optimistic) + **Value**
- **KPIs** — sessions, run tasks, deliverables, active days, expert-equivalent hours
- **Value at a glance** — the four Value Pillars with example KPIs
- **Work by business process** — an upfront **Job ▸ Business Process ▸ JTBD** visual, then a table you
  can **toggle between Business Process and Job-to-be-Done** (banded by Job × Value Pillar; auto-hiding
  **session-cost** column)
- **Where the time went — by task category** — research-anchored bands
- **Roles Cowork assembled for me** — the **exact professional roles a billing firm would charge** for
  your work (Data Analyst, Management Consultant, Software Engineer, …), each **linked** to a job
  search, with the expert-equivalent hours covered. *(Logic ported from microsoft/What-I-Did-Copilot:
  LLM-tagged per session, 16-role keyword fallback.)*
- **Deliverables & the skills behind them**
- **Methodology & glossary** — every band traceable, with clickable research sources

## The four Value Pillars

| Pillar | Type | Example KPI |
|---|---|---|
| **Revenue Growth** | Tangible · money coming in | Incremental gross revenue |
| **Cost Reduction** | Tangible · money going out | Labor & budget savings |
| **Risk Mitigation** | Intangible · money going out | Penalties & losses avoided |
| **Transformation** | Intangible · money coming in | Adoption, decision quality, retention |

Each session's process, pillar, job, and JTBD are **derived at run time from your own footprint** —
nothing in this skill is specific to any individual. If the playbook isn't run, classification falls
back to a generic APQC taxonomy (Job = "Other").

---

## Methodology — research-anchored time saved

**Time Saved (expert-equivalent)** — what a professional would take with no AI — is simply the
**sum of the research-anchored band for each task** in a session. Nothing else: no read-time or
authoring assumptions, so every minute traces to a cited study.

```
time_saved_min = Σ CATS[task].typical        # e.g. Analysis (67) + Document (24) = 91 min
```

The **Conservative / Optimistic** range re-sums the published **low** / **high** band per task.

**Headline (both fully research-anchored):**

```
Time Saved (hours) = Σ time_saved_min / 60
Value              = Time Saved hours × hourly_rate
```

**Speed multiplier (secondary, directional).** Dividing Time Saved by a *modeled* hands-on clock
gives a speed multiplier. The assisted clock is the one non-research input — OneDrive can't measure
keystroke time — so the multiplier is directional, not a stopwatch (it is *measured* for sessions
where the telemetry hook is enabled):

```
assisted_min     = 8 (prompt/setup) + 2 × (num inputs + outputs)   ·  floor 4   [modeled]
speed_multiplier = Σ time_saved_min / Σ assisted_min               (rate-independent · secondary)
```

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

Full source citations (Stanford-WB, Microsoft Research, NBER, Forrester, etc.) are embedded in the
report's Glossary and in `build_report.py`.

---

## Optional hook — capture chat-only sessions automatically

A `settings.json` hook enriches the report over time (forward-looking — it can't backfill past
sessions). Wire it once, then activate by opening `/hooks` or restarting:

- **Stop hook → `mine_session.py --log …cowork-session-telemetry.json`** records every session
  (run-time, tools, artifacts, `produced_artifact`) so **chat-only / folder-less sessions are
  counted**, not just those that saved a file.

Only the *live* session is minable, so the log builds forward as you use Cowork.

---

## Run the scripts directly (dev)

```bash
python scripts/classify.py     --in working/cowork_raw.json      --out working/cowork_sessions.json
python scripts/compute.py      --in working/cowork_sessions.json --out working/cowork_roi_data.json
python scripts/build_report.py --data working/cowork_roi_data.json --out output/cowork-roi-report.html
```

No third-party dependencies — standard-library Python 3 only.

### Input schema (`cowork_sessions.json`)

Each session carries `inputs`/`outputs` (each with `ext` and optional `skills`), `tasks` (category
keys), and — when the map-my-work playbook runs — `process`, `value_pillar`, `job`, and `jtbd`.
Task category keys: `analysis · document · email · meeting · comms · special · code · general`.

---

## Caveats (state these in any readout)

- **Time Saved & Value are research-anchored** (cited per-task bands). The **speed multiplier's**
  assisted clock is a **modeled** estimate (measured where the telemetry hook is on), so treat the
  multiplier as directional.
- Categories with **no tasks** in the window are reported as **zero**, keeping totals a conservative floor.
- Counting stays conservative: supporting files are folded into the primary task.
- Everything is **derived per user at run time** — nothing in the skill is specific to any individual.
