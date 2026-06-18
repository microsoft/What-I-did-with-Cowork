# What Cowork Did for Me

> A personal impact report skill for **Microsoft Copilot Cowork** — quantifies your leverage as a speed multiplier and professional-services equivalent value.

![Report Hero](images/report-hero.png)

---

## What is this?

**"What Cowork Did for Me"** is a skill for [Copilot Cowork](https://copilot.cloud.microsoft/cowork) that generates a polished, Microsoft-branded **single-file HTML report** from your own Cowork session history stored in OneDrive. It answers the question: *"How much time and value has Cowork given me?"*

The skill:
- Harvests your Cowork session artifacts (inputs analyzed & outputs produced) from OneDrive
- Classifies work into 8 research-anchored task categories
- Applies an **artifact-scaled two-clock model** to compute your speed multiplier
- Renders a self-contained, interactive HTML report you can share or print to PDF

Inspired by [microsoft/What-I-Did-Copilot](https://github.com/microsoft/What-I-Did-Copilot), adapted for Copilot Cowork.

---

## Report Highlights

### Speed Multiplier & Value
The report leads with a **speed multiplier** (how much faster Cowork made you vs. working unassisted) and a **professional-services equivalent** (what that expert time would cost at your hourly rate).

![KPIs and Speed Multiplier](images/report-kpis.png)

### Category Breakdown & Analyzed → Produced
See where your time went across 8 task categories, plus a breakdown of what you fed Cowork vs. what it produced.

![Categories and Artifacts](images/report-categories.png)

### Full Report Sections
- **Hero** — speed multiplier (conservative/typical/optimistic) + professional-services value
- **KPIs** — sessions, tasks, artifacts, active days, expert-equiv hours, hands-on hours
- **By category** — research-anchored time-savings bars
- **Analyzed → Produced** — sources in vs. deliverables out, with ingest/synthesize/author split
- **Skills augmented** — professional roles Cowork covered for you
- **Goals & leverage** — per-session goal with hours, value, and speed multiplier
- **Activity heatmap** — day × hour collaboration pattern
- **Methodology & glossary** — every band traceable, with clickable research sources
- **Live hourly-rate control** — recalculates all dollar figures; speed multiplier is rate-independent
- **Download PDF** button

---

## Installation

 Let Cowork install it for you.

1. **Download** the [`cowork-roi-report-skill.zip`](https://github.com/Fepilot/What-Cowork-did-for-me/releases/latest/download/cowork-roi-report-skill.zip) from the latest release
2. **Open** [Copilot Cowork](https://copilot.cloud.microsoft/cowork)
3. **Attach** the zip file to the chat and send this prompt:

   > **Install the attached Cowork ROI Report skill into my personal skills.**

4. Cowork will unpack and place the skill in the right location for you
5. **Done!** In the same session (or a new one), ask: *"What did Cowork do for me?"*

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
| Analysis & Research | 30 | **71** | 92 |
| Document & content creation | 12 | **24** | 42 |
| Email workflows | 3 | **7** | 12 |
| Meeting workflows | 12 | **31** | 45 |
| Communication workflows | 2 | **4** | 6 |
| Specialized workflows | 10 | **25** | 40 |
| Write or debug code | 30 | **56** | 96 |
| General assistance / Other | 2 | **5** | 8 |

Sources: Stanford-WB, Microsoft Research, NBER, Forrester — all clickable in the report's Glossary.

---

## What's in the Skill

```
cowork-roi-report-skill/
├── SKILL.md              # Skill definition + workflow (loaded by Cowork)
├── README.md             # Technical documentation
├── CHANGELOG-v5.md       # What changed in v5 and why
├── scripts/
│   ├── mine_session.py   # Mines the live session transcript
│   ├── classify.py       # Deterministic ext→category classifier
│   ├── compute.py        # Applies the methodology → payload JSON
│   └── build_report.py   # Renders the self-contained HTML report
└── examples/
    ├── sample_sessions.json   # Synthetic input (safe to share)
    └── sample-report.html     # Rendered from the synthetic input
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
