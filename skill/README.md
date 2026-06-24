# Cowork ROI — Personal Impact Report (skill)

Generates a **"What Cowork Did for Me"** single-file HTML report from a user's own
Copilot Cowork session history in OneDrive. It leads with research-anchored **Time Saved**
and its **professional-services-equivalent value**, then maps the work to the user's own
Jobs, Business Processes, and the four Value Pillars.

> **v18 (Cowork-app allow-list harvest; Scout excluded).** The harvest now reads **all three**
> `Documents/Cowork/` layouts — `Tasks/<goal>-<date>/`, root `<goal>-<date>/`, and legacy
> `sessions/<uuid>/` — and counts **only items created by the Cowork app**
> (`createdBy.application.id = 6ab48b67-…`). It **never enumerates `Documents/Apps/…`**, so the M365
> Copilot app running **Scout** (heartbeats, monitors, executive briefings) is excluded for every user
> with no per-instance name list. Persistent `Tasks/` folders leave `exec_min` null (the file-timestamp
> span is days, not run time) so the modeled assisted clock applies; supporting files fold into the
> primary deliverable. Methodology, classifier, compute, and renderer are **unchanged**. See
> [`CHANGELOG-v18.md`](CHANGELOG-v18.md).
>
> **v17 (two-lens work-by-process + professional roles).** The **Work by business process** section
> is one row per **project Cowork delivered** (task-category column dropped) with a toggle between
> two lenses — **By Job-to-be-Done** (indented Job ▸ Business Process ▸ JTBD ▸ Project) and **By
> Business Value Pillar** (Pillar · Project · Assistance). A **Roles Cowork assembled for me** section
> (v16) lists the *exact professional roles a billing firm would charge* (LLM-tagged per session,
> 16-role keyword fallback, ported from `microsoft/What-I-Did-Copilot`). Time Saved remains the **sum
> of the cited per-task bands** with the **speed multiplier as a secondary, directional stat** (v15).
> One self-contained skill; `map-my-work` is **folded in as bundled references** (`references/`) and
> runs **inline** to derive each user's own Jobs ▸ Business Processes ▸ Value Pillars ▸ JTBD. See
> [`CHANGELOG-v18.md`](CHANGELOG-v18.md) (and v17 / v16 / v15 / v14 / v13 / v11 / v6 / v5) for history.

---

## Contents

```
cowork-roi-report/
├── SKILL.md                     # skill definition + workflow (loaded by Cowork)
├── README.md                    # this file
├── CHANGELOG-v18.md             # latest — Cowork-app allow-list harvest (all 3 layouts), Scout excluded
├── CHANGELOG-v17.md             # two-lens (JTBD / Value Pillar) work-by-process
├── CHANGELOG-v16.md             # professional roles a billing firm would charge; process redesign
├── CHANGELOG-v15.md             # purely research-anchored Time Saved; multiplier demoted
├── CHANGELOG-v14.md             # single self-contained skill, four value pillars
├── CHANGELOG-v13.md             # bundle + rich {process, pillar, job, jtbd} override
├── CHANGELOG-v11.md             # TF-IDF APQC classifier, skills-augmented, cost capture
├── CHANGELOG-v6.md / -v5.md     # earlier history
├── references/
│   ├── map-my-work-playbook.md  # derives the user's own taxonomy (runs inline at step 4b)
│   └── value-pillars.md         # four-pillar (OneBVM) crosswalk — single source of truth
├── scripts/
│   ├── mine_session.py          # live-session telemetry (Stop hook): exec_min, tool intensity, artifacts
│   ├── statusline_cost.py       # per-session cost capture (statusLine hook)
│   ├── classify.py              # category + business-process classifier; preserves skills tags
│   ├── compute.py               # applies the methodology -> payload JSON
│   ├── build_report.py          # renders the self-contained HTML report
│   ├── apqc_taxonomy.json       # generic APQC 13 fallback (used when map-my-work isn't run)
│   ├── roles_taxonomy.json      # 16-role keyword fallback for "roles assembled"
│   └── skills_vocabulary.json   # controlled DOMAIN_SKILLS + TECH_SKILLS vocabulary
└── examples/
    └── sample_sessions.json     # synthetic input (safe to share)
```

## Install

1. **Download** `cowork-roi-report-skill-v18.zip` from the latest release. *(No need to unzip — attach it as-is.)*
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

The skill harvests Cowork session workspaces from OneDrive under `Documents/Cowork/` across **all
three** layouts — `Tasks/<goal>-<date>/`, root `<goal>-<date>/`, and legacy `sessions/<uuid>/` (each
with `input/` + `output/`) — counting **only** artifacts whose `createdBy.application.id` is the Cowork
app (`6ab48b67-…`), and **never** enumerating `Documents/Apps/…` (Scout). It writes this:

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
      "professional_roles": ["Data Analyst", "Management Consultant"], // roles a billing firm would charge
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
- **Professional roles (for the *Roles assembled* section).** Tag each session with 1–2
  `professional_roles` — the roles a billing firm would charge for that work. When none are tagged,
  `compute.py` falls back to the 16-role keyword taxonomy in `scripts/roles_taxonomy.json`; expert
  time is split across a session's roles.
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

## Methodology — research-anchored Time Saved

**Time Saved (expert-equivalent)** — what a professional would take with no AI — is simply the
**sum of the research-anchored band for each task** in a session. Nothing else: no read-time or
authoring assumptions, so every minute traces to a cited study.

```
time_saved_min = Σ CATS[task].typical        # e.g. Analysis (67) + Document (24) = 91 min
```

The **Conservative / Optimistic** range re-sums the published **low** / **high** band per task.

**Headline metrics (both fully research-anchored):**

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

Full source citations (Stanford-WB, Microsoft Research, NBER, Forrester, etc.) are embedded
in the report's Glossary and in `build_report.py`.

---

## Output (HTML report sections)

- **Hero** — research-anchored **Time Saved** (conservative/typical/optimistic) + professional-services **Value**, with a live hourly-rate control and a Download-PDF button. The **speed multiplier** rides alongside as a clearly-labelled secondary, directional stat.
- **Value at a glance** — business-value table mapping impact to the **four value pillars** (Revenue Growth · Cost Reduction · Risk Mitigation · Transformation), each pairing a business outcome (lagging KPI) with a Cowork indicator (leading KPI) and your result
- **KPIs** — Cowork sessions, tasks completed, active days, expert-equivalent hours, hands-on hours
- **Work by business process — two lenses, one toggle.** One row per **project Cowork delivered** (the task-category column is gone from this section). Toggle between:
  - **By Job-to-be-Done** — an indented **Job ▸ Business Process ▸ JTBD ▸ Project** hierarchy (each level chip-labelled JOB / PROCESS / JTBD / PROJECTS), each project showing its assistance inline (expert-equivalent hours saved · value · speed).
  - **By Business Value Pillar** — a 3-column table: **Business value pillar · Project · Assistance offered** (pillar shown once per group).
  The taxonomy is **derived live per user** by the bundled map-my-work playbook (from their own M365 footprint) — nothing hard-coded; falls back to the generic APQC framework if the playbook isn't run. A **session-cost column** shows actual Cowork spend where captured, and **auto-hides** when no session has cost data. **Chat-only sessions** (no saved file) are counted via telemetry.
- **By category** — where the expert-equivalent time went (research-anchored bars)
- **Roles Cowork assembled for me** — the **exact professional roles a billing firm would charge** for the work (Data Analyst, Management Consultant, Software Engineer, Risk & Compliance Analyst, …), each **linked** to a job-title search, with the expert-equivalent hours covered. Roles are **LLM-tagged per session** (`professional_roles`), with a 16-role keyword taxonomy (`scripts/roles_taxonomy.json`) as fallback. *(Ported from `microsoft/What-I-Did-Copilot`.)*
- **Skills augmented** — the professional skills Cowork put to work (Presentation Design, Technical Writing, Data Analysis, Financial Modelling, Frontend Development, …), each with the expert-equivalent hours covered — turning time saved into *capability* without added headcount
- **Deliverables & the skills behind them** — every artifact produced, the skills that went into it, and the expert effort attributed to each (per-deliverable hours = an equal share of the session's expert time, so they sum back to the total)
- **Analyzed → Produced** — sources you fed in vs. deliverables produced, shown as **counts by type** (the assumption-based ingest/analyze/author minute split was dropped in v15)
- **Methodology & glossary** — every band traceable, with clickable research sources

---

## Business value — the four value pillars

Every session's impact is expressed in one shared vocabulary based on Microsoft's
**[OneBVM (One Business Value Model)](https://aka.ms/OneBVM)** methodology, defined once in
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
- **Time Saved & Value are research-anchored** (cited per-task bands). The **speed multiplier's**
  assisted clock is **modeled**, not measured — OneDrive records artifacts, not keystroke time —
  so treat the multiplier as **directional**, not a stopwatch.
- Categories with **no tasks** in the window are reported as **zero**, keeping totals a
  conservative floor.
- Counting stays conservative: ~2 run tasks per session; supporting files folded into the primary task.
