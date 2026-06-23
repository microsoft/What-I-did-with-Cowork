# What Cowork Did for Me

> A personal impact report skill for **Microsoft Copilot Cowork** — quantifies your leverage as a speed multiplier and professional-services equivalent value.

![What Cowork Did for Me — sample report](images/cowork-roi-report-sample.gif)

---

## Get Started in 4 Steps

1. **Download** [`cowork-roi-report-skill-v14.zip`](../../releases/latest) from the latest release. *(No need to unzip — attach it as-is.)*
2. **Open** a new [Copilot Cowork](https://copilot.cloud.microsoft/cowork) session.
3. **Click the ➕ (plus) symbol** to attach the zip file, then send this prompt:

   > **Add this skill.**

4. Once it's added, ask:

   > **Generate my impact summary report.**

   It'll ask one quick question — which period to measure (**7, 15, or 30 days**) — then build your report.

That's it. 🎉

---

## What you get out of it — your leverage, quantified

**With Cowork, you operate like a multidisciplinary team.** You steer; Cowork brings in best-in-class experts from across fields, produces quality output, and does it at a pace far beyond what humans alone could match. This skill makes that leverage visible and defensible across three dimensions:

- **⚡ Speed** — a research-anchored **speed multiplier** showing how much faster you moved *with* Cowork versus doing the same work unassisted (conservative / typical / optimistic).
- **🎯 Quality** — the kind of **expert-grade outputs** Cowork helped you ship: analyst-style research syntheses, executive decks and documents, interactive dashboards and apps, scripts, and polished communications — each traced to a real artifact you produced.
- **🧠 Expert assistance** — the professional **skills Cowork put to work for you** — Presentation Design, Technical Writing, Data Analysis, Financial Modelling, Frontend Development, and more — rolled up into a **professional-services-equivalent dollar value** at your hourly rate.

Every figure traces back to your own session artifacts in OneDrive — nothing is invented, and categories with no work in the window report zero. The result is a credible, shareable answer to *"What has Cowork actually done for me?"*

---

## What is this?

**"What Cowork Did for Me"** is a skill for [Copilot Cowork](https://copilot.cloud.microsoft/cowork) that generates a polished **single-file HTML report** from your own Cowork session history stored in OneDrive. It answers the question: *"How much time and value has Cowork given me?"*

The skill:
- Harvests your Cowork session artifacts (inputs analyzed & outputs produced) from OneDrive
- Classifies work into 8 research-anchored task categories
- Applies an **artifact-scaled two-clock model** to compute your speed multiplier
- Renders a self-contained, interactive HTML report you can share or print to PDF

Inspired by [microsoft/What-I-Did-Copilot](https://github.com/microsoft/What-I-Did-Copilot), adapted for Copilot Cowork.

---

## Report Highlights

### Speed Multiplier & Value
The report leads with a **speed multiplier** (how much faster Cowork made you vs. an unassisted expert, shown as conservative / typical / optimistic) and a **professional-services equivalent** (what that expert time would cost at your hourly rate). A live hourly-rate control recalculates every dollar figure, and a **Download PDF** button exports the whole thing.

![KPIs and Speed Multiplier](images/report-kpis.png)

### Value at a Glance
A business-value table maps your impact to the **four value pillars** — **Revenue Growth**, **Cost Reduction**, **Risk Mitigation**, and **Transformation** — each pairing a business outcome (lagging KPI) with a Cowork indicator (leading KPI) and your result. Headline KPIs follow: Cowork sessions, tasks completed, active days, expert-equivalent hours, and your estimated hands-on hours.

### Work by Business Process & Task Category
Each session is mapped to the **business process** it advanced and **banded by Job × Value Pillar**, with a *job-to-be-done (JTBD)* sub-line per row. The process taxonomy is **derived live for whoever runs the report** (from their own Microsoft 365 footprint via the bundled map-my-work playbook) — nothing is hard-coded to any individual; if the playbook isn't run, it falls back to the generic APQC business-process framework. Rows also show the task category, deliverables, and hours/value/speed. A **session-cost column** shows actual Cowork spend where captured, and **auto-hides** when no cost data is available. **Chat-only sessions** (no saved file) are counted too, via telemetry.

![Work Process](images/WorkProcess.png)

### Where the Time Went, Skills Augmented & Deliverables
- **By task category** — research-anchored time-savings bars across the 8 categories.
- **Skills augmented** — the professional skills Cowork put to work (Presentation Design, Technical Writing, Data Analysis, Financial Modelling, Frontend Development, …), each with the expert-equivalent hours it covered — turning time saved into *capability* without added headcount.
- **Deliverables & the skills behind them** — every artifact Cowork produced, the skills that went into it, and the expert effort attributed to each.

![Categories and Artifacts](images/report-categories.png)

### Methodology & Glossary
Every number is traceable: an expandable methodology section and glossary explain each band and metric, with clickable links to the published research behind them.

---

## The Four Value Pillars

Every session's impact is expressed in a shared business-value vocabulary, so leverage reads the same way across teams:

| Pillar | Type | What it captures |
|---|---|---|
| **Revenue Growth** | Tangible · money coming in | Demand created, converted, and monetised — new opportunities, win rates, pricing, faster deal cycles. |
| **Cost Reduction** | Tangible · money going out | Inefficiencies eliminated, manual work automated, spend optimised — direct savings or capacity redeployed. |
| **Risk Mitigation** | Intangible · losses avoided | Issues detected earlier, controls improved, faster correction — financial, operational, and compliance risk reduced. |
| **Transformation** | Intangible · new ways of working | Better/faster decisions, more responsive operations, stronger collaboration, and greater AI-workflow adoption. |

The pillar for each session is set by an intent-verb rule (the work's job-to-be-done), falling back to the process default — never force-fit. Pillars with no qualifying work in the window render as zero, not hidden.

---

## How to Use

Once installed, trigger the skill by asking Cowork:
- *"What did Cowork do for me?"*
- *"My Cowork ROI report"*
- *"Cowork impact report"*
- *"How much time has Copilot Cowork saved me this month?"*

The skill will:
1. **Ask** which period to measure (7, 15, or 30 days) and whether to automate
2. **Harvest** your Cowork session files from OneDrive
3. **Classify** each session using the deterministic extension-based classifier
4. **Compute** the two-clock model (expert clock vs. assisted clock)
5. **Render** a beautiful HTML report
6. **Optionally automate** on a recurring schedule with email digest

---

## Methodology

The skill uses a **two-clock model** anchored in published research:

| Clock | What it measures |
|---|---|
| **Expert (unassisted)** | How long a professional would take without AI — research-anchored category bands + reading time per source + authoring time per deliverable |
| **Assisted (your time)** | Modeled hands-on effort: `8 min + 2 min × (inputs + outputs)`, floor 4 min |

```
speed_multiplier            = Σ expert_min / Σ assisted_min        (rate-independent)
professional_services_value = (Σ expert_min / 60) × hourly_rate
```

### Research-anchored category bands (min saved / task)

| Category | Low | Typical | High |
|---|---:|---:|---:|
| Analysis & Research | 30 | **67** | 92 |
| Document & content creation | 12 | **24** | 42 |
| Email workflows | 3 | **7** | 12 |
| Meeting workflows | 12 | **31** | 43 |
| Communication workflows | 2 | **4** | 11 |
| Specialized workflows | 10 | **25** | 40 |
| Write or debug code | 30 | **56** | 96 |
| General assistance / Other | 2 | **5** | 8 |

Sources: Stanford-WB, Microsoft Research, NBER, Forrester — all clickable in the report's Glossary.

---

## What's in the Skill

```
cowork-roi-report-skill/
├── SKILL.md                    # Skill definition + workflow (loaded by Cowork)
├── README.md                   # Technical documentation
├── CHANGELOG-v14.md            # Latest — plus v5 / v6 / v11 / v13 changelogs
├── references/
│   ├── map-my-work-playbook.md # Derives each user's Jobs ▸ Processes ▸ Pillars ▸ JTBD (runs inline)
│   └── value-pillars.md        # Four-pillar crosswalk (single source of truth)
├── scripts/
│   ├── mine_session.py         # Live-session telemetry (Stop hook)
│   ├── statusline_cost.py      # Per-session cost capture (statusLine hook)
│   ├── classify.py             # Category + business-process classifier
│   ├── compute.py              # Applies the methodology → payload JSON
│   ├── build_report.py         # Renders the self-contained HTML report
│   ├── apqc_taxonomy.json      # Generic APQC business-process fallback
│   └── skills_vocabulary.json  # Controlled DOMAIN + TECH skills vocabulary
└── examples/
    └── sample_sessions.json    # Synthetic input (safe to share)
```

No third-party dependencies — **standard-library Python 3 only**.

---

## Caveats

- The **assisted clock is modeled**, not measured — OneDrive records artifacts, not keystroke time. Treat the multiplier as **directional**, not a stopwatch.
- Categories with **no saved artifacts** in the window report **zero** — keeping totals a conservative floor.
- Counting stays conservative: ~2 run tasks per session; supporting files folded into the primary task.

---

## License

MIT

---

## Credits

- Inspired by [microsoft/What-I-Did-Copilot](https://github.com/microsoft/What-I-Did-Copilot)
- Powered by [Microsoft Copilot Cowork](https://copilot.cloud.microsoft/cowork)
