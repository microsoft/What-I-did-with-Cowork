---
name: cowork-roi-report
description: |
  Generates a Microsoft-branded "What Cowork Did for Me" web-app impact report (single self-contained HTML)
  from the signed-in user's own Copilot Cowork session history in OneDrive. Quantifies leverage as a speed
  multiplier and a professional-services-equivalent value using research-anchored task-category bands plus an
  artifact-scaled two-clock model. The report has a live hourly-rate control, a Download-PDF button,
  an expandable Glossary with clickable research sources, KPIs, a category breakdown, an
  analyzed-vs-produced (inputs/outputs) breakdown, skills-augmented, work-by-business-process table, and an activity heatmap.
  Inspired by microsoft/What-I-Did-Copilot, adapted for Copilot Cowork.

  Use when the user asks to "generate my impact summary report", "generate my impact report",
  "my impact summary", for "my Cowork ROI", "what Cowork did for me", "Cowork impact report",
  "Copilot Cowork ROI report", "how much time has Cowork saved me", "my Cowork value report",
  or any request for a personal impact / ROI / value report on Copilot Cowork usage.
  The skill asks which period to measure (7, 15 or 30 days) and whether to automate it on that cadence
  with an emailed digest (highlights + the HTML attached).

  Do NOT use for: GitHub Copilot / IDE reports, team-wide announcements, single-meeting summaries,
  or daily briefings.
cowork:
  category: analysis
  icon: BarChart4
---

# Cowork ROI — Impact Report Generator

Builds a personal, shareable impact report from the user's **own** Copilot Cowork footprint. Every run is
self-service: it reads the signed-in user's Cowork session workspaces in OneDrive, classifies the work into
the eight methodology categories, applies the research-anchored time-savings bands, and renders a polished,
Microsoft-branded HTML web app. Optionally automates itself and emails a digest.

This skill is generic — it works for **any** signed-in user. No data is hard-coded.

## When to use
- "What did Cowork do for me?" / "My Cowork ROI report" / "Cowork impact report"
- "How much time has Copilot Cowork saved me this month?"
- "Set up a monthly Cowork ROI email"

## When NOT to use
- GitHub Copilot (IDE/code) reports → `microsoft/What-I-Did-Copilot` run locally
- Team announcements → `stakeholder-comms`; single-meeting recaps → `meeting-intel`; daily wrap-up → `daily-briefing`

---

## Inputs & defaults
- **Period:** the user picks **7, 15 or 30 days** (asked at the start). Window = period ago 00:00 → today 23:59, user's local time zone.
- **Hourly rate:** default **$72/hr** (blended professional-services rate; also editable live inside the report).
- **Copilot seat cost:** *not used in v5* — the report shows a speed multiplier + professional-services value, not an ROI ratio (credit/seat data isn't available).
- **Default email recipient:** the signed-in user themselves.

---

## Workflow

### 1. Ask the user (one `AskUserQuestion`, two questions)
- **Q1 — Period:** "Which period should the report measure?" → options **Last 7 days**, **Last 15 days**, **Last 30 days**.
- **Q2 — Delivery:** "How do you want to run it?" → options:
  - **Just run it once** (generate the report now, no automation)
  - **Run now & automate every N days, email me a digest** (N matches the period: 7→every 7 days, 15→every 15, 30→every 30; each run emails the highlights with the HTML attached)

Do not proceed to scheduling until the user has explicitly chosen the automate option in Q2 (the platform will also show its own approval dialog).

### 2. Resolve identity & dates
- `GetMyDetails(select="mail,userPrincipalName,displayName")` → user name + email.
- Compute `after` = N days ago at 00:00 local; `before` = today 23:59 local; set `window.label` = "Last N days", `window.months` = N/30 rounded (legacy field; v5 does not use seat cost).

### 3. Harvest the user's Cowork sessions (the data source)
Cowork persists each session's workspace to OneDrive under the **`Documents/Cowork/`** store. There is no
chat transcript in OneDrive — the artifacts are the signal. Over the product's life this store has used
**three folder layouts** — harvest **all three**, because different users (and product versions) sit on
different ones:
- **Task folders** (current): `Documents/Cowork/Tasks/<goal-slug>-<YYYY-MM-DD>/` → `input/` + `output/`
- **Root goal folders**: `Documents/Cowork/<goal-slug>-<YYYY-MM-DD>/` → `input/` + `output/`
- **Legacy UUID sessions**: `Documents/Cowork/sessions/<session-uuid>/` → `input/` + `output/`

- `GetDefaultDrive()` → personal OneDrive `drive_id`.
- **Locate the Cowork folder — do NOT assume the exact name.** Commonly `Cowork`, but often suffixed or
  localized (`Cowork 1`, `Cowork 2`, `Colaborar`, `Documentos/Cowork`, …). Resolve once:
  1. Try `GetDriveChildren(drive_id, item_path="/Documents/Cowork")`.
  2. On 404, **list `/Documents`** and pick the child whose name starts with `Cowork` (case-insensitive) —
     prefer exact `Cowork`, else the highest-numbered `Cowork N`, else any `Cowork*`.
  3. If still nothing, try the drive root `/Cowork`, then `/Documentos/Cowork`.
  4. Only if all fail, ask the user for the folder name once.
  Carry the resolved name forward for later writes (telemetry log) — never re-hardcode `Cowork`.
- **Enumerate all three layouts** under the resolved Cowork folder: the `Tasks/` children, the root
  goal-folder children, and the `sessions/` children. **Follow pagination** (`@odata.nextLink`/`next_link`)
  to exhaustion in every listing — a single page caps at ~20–100 items.

- **Allow-list, never deny-list — scope to what the Cowork app created.** Count a folder/artifact ONLY when
  its `createdBy.application.id` is the **Cowork app id `6ab48b67-cd74-4ad4-81af-5932984589be`**. This is the
  one robust, user-agnostic Cowork signal — the same product app id across users and tenants. Do **not** key
  on store/folder *names*; those are instance-specific.
- **NEVER enumerate `Documents/Apps/…`.** That tree (e.g. `Apps/M - Internal Copilot App 1/sessions/…`) is a
  **different product — the M365 Copilot app running Scout** (scheduled heartbeats, customer/needs monitors,
  executive briefings), written by the generic *Microsoft Graph* app (`99fa64eb-…`), **not Cowork**. Skipping
  the `Apps/` tree entirely excludes Scout for **every** user with no per-instance name list to maintain. Do
  **not** try to detect-and-subtract Scout by folder name — a deny-list is fragile and breaks on the next user.

- Keep session folders whose `createdDateTime` or `lastModifiedDateTime` falls in the window.
- For each kept session, `GetDriveChildren` into its `output/` (and `input/`) subfolders to collect artifact
  filenames, extensions **and per-file `createdDateTime`**. Run these lookups in parallel batches.
- **Counting discipline at harvest.** Task folders are **persistent workspaces** that accumulate artifacts
  over multiple days/runs, so:
  - **Do NOT derive `exec_min` from file-timestamp spans** for them — the span is days, not run time. Leave
    `exec_min` null (the modeled assisted clock applies); prefer a measured telemetry `exec_min` when present.
  - **Fold supporting files** (QA screenshots / `*.png`, variant `*-7day/-60d/-sample.html`, prompts, READMEs,
    lock files) into the session's primary deliverable — never count 17 screenshots as 17 deliverables.
- **Keep output-less sessions.** A folder with only `input/` (or empty) still counts — record empty
  `outputs`; `classify.py` tags it `general` (conversational).
- **Live-session telemetry (Stop hook).** `mine_session.py --log /mnt/user-config/.claude/cowork-session-telemetry.json`
  upserts every session (id, measured `exec_min`, tool intensity, artifacts, `produced_artifact`) into a
  durable log, so **chat-only / folder-less Cowork sessions self-record**. In the harvest, **read this log and
  MERGE IN any session id not already covered by a Cowork folder** (`has_folder:false`, `outputs:[]`, telemetry
  `exec_min`); for sessions in both, prefer the telemetry `exec_min` + `produced_artifact`. Builds forward only
  — it cannot backfill sessions that predate the hook.

### 4. Classify each session into run tasks (the methodology)
A **session** contains one or more **run tasks**; each run task maps to exactly one of the eight categories
below.

**Value model = RUNS × BAND (per the Cowork Time-Savings methodology deck).** Time saved = Σ over **runs**
of each run's **category band** (minutes SAVED per run). Each band already sums the activity-instance chain
inside ONE run (code 56 = write+test+debug = 18min×3; doc 24 = 6.1min×4 = draft→rewrite→format→polish), so
you **count runs and multiply by the band** — never per-LOC, never a per-artifact authoring add-on (those
double-count the chain that's already inside the band). **Count runs from the agentic tool-chains**, grounded
in telemetry: a **code run ≈ 6 code-edit actions** (Edit/Write/MultiEdit), an **analysis run ≈ 5 research-tool
calls** (search/list/read/query). `mine_session.py` writes these as a `runs:{category:count}` field per
session; pass it through the harvest. Where a session has no telemetry, estimate runs conservatively from
deliverables/iterations and label them as estimates. `compute.py` applies `Σ runs × CATS[band]`.

**Use the deterministic classifier — do NOT hand-tag categories.** Write the harvested sessions (with
`inputs`, `outputs` and `exec_min`) to `working/cowork_raw.json`, then run:
`python scripts/classify.py --in working/cowork_raw.json --out working/cowork_sessions.json --overrides working/process_overrides.json`.
It maps each session's real artifact **extensions** to categories (e.g. `.xlsx/.csv`→analysis, `.docx/.pptx/.pdf`→document,
`.html/.py/.ps1`→code, `.zip`→special), caps ~2 run tasks/session, and tags output-less sessions `general`.
This is the fix for the failure mode where every session was stamped with the same category pair and every
goal collapsed to the same hours — **never assign the same default categories to every session.** You may bump
a clearly analytical deliverable (a synthesis report saved as `.docx/.pptx`) to `analysis`, but the extension
map is the default. **Be conservative — credibility matters more than a big number.**

Reference — extension/category heuristics the classifier encodes:
| Signal in the session | Category key |
|---|---|
| Multi-source **synthesis** report — newsletter, weekly/biweekly recap, "Wrapped", briefing, ROI summary, status review (pull data → synthesize → write-up) | `analysis` |
| Data **analysis / validation / metrics / KPI mapping / catalog**, analytical spreadsheet | `analysis` |
| **Deck** (.pptx), **document** (.docx), guide, one-pager, written content, PDF report | `document` |
| **Interactive web app / dashboard / builder / hub** (.html app), or a **script** (.ps1/.py/.js) | `code` |
| **Prompt engineering / skill authoring / packaging** (prompt .md, skill .md, skill .zip), cross-system automation | `special` |
| **Email** sent via Cowork | `email` · **Teams** message | `comms` · **Meeting** scheduled/recapped | `meeting` |
| Quick **Q&A / formatting / lookup / short review** with no saved deliverable | `general` |

Counting discipline:
- Cap **~2 run tasks per session**. Fold supporting files (prompts, how-tos, design specs, READMEs, lock files, zips) into the primary task.
- Genuinely distinct deliverables (e.g., two different customer analyses in one session) → separate tasks.
- Categories with **no** artifacts in the window are reported as **zero** — this keeps totals a conservative floor.

The raw harvest you write to `working/cowork_raw.json` (input to `classify.py`):
```json
{ "meta": {"user":"<name>","email":"<mail>","generated":"<YYYY-MM-DD>",
           "window":{"from":"...","to":"...","label":"Last N days","months":<0.25|0.5|1|2>},
           "hourly_rate":72},
  "sessions": [ {"id":"<uuid8>","date":"YYYY-MM-DD","hour":<0-23>,
                 "goal":"<short verb-first phrase>",
                 "inputs":  [{"name":"report-1.pdf","ext":"pdf"}, ...],
                 "outputs": [{"name":"deck.pptx","ext":"pptx","skills":["Presentation Design","Data Analysis"]}, ...],
                 "skills": ["Data Analysis"],
                 "professional_roles": ["Data Analyst","Management Consultant"],
                 "has_folder":true, "exec_min":<measured minutes|null>}, ... ] }
```
`classify.py` adds the `tasks` array (categories) and writes `working/cowork_sessions.json`. Where a live
`session_telemetry.json` exists for a session, prefer its measured `exec_min`, tool counts and `produced_artifact`
flag over the file-timestamp estimate.

### 4a. Tag the skills behind each deliverable (populates "Skills augmented")

**Required — without it the Skills-augmented and Deliverables tables render empty.** For each output
(and each chat-only session) tag the **professional skills** Cowork exercised, drawn ONLY from the
controlled vocabulary in `scripts/skills_vocabulary.json` (DOMAIN_SKILLS + TECH_SKILLS):
- Write a `skills:[...]` array on each `outputs[]` item; for output-less / chat-only sessions, put a
  session-level `skills:[...]`. `compute.py` rolls these up into the per-deliverable table; hours
  follow the artifact they're tagged on.
- **Also tag `professional_roles:[...]` per session** — the **1–2 roles a billing firm would charge**
  for that work (e.g. *Data Analyst*, *Management Consultant*, *Software Engineer*, *Risk & Compliance
  Analyst*). Name the **exact** role the task would have needed — use `scripts/roles_taxonomy.json` as a
  guide but don't force-fit. These drive the **"Roles Cowork assembled for me"** section. If omitted,
  `classify.py` falls back to keyword matching. *(Logic ported from microsoft/What-I-Did-Copilot.)*
- **Tag conservatively, evidence-based — never invent a skill outside the vocabulary.** Infer from the
  deliverable: a `.pptx` deck → *Presentation Design* (+ *Data Visualization* / *UX Design* if charts);
  a `.docx` guide → *Technical Writing* / *Documentation*; a built skill / `.zip` → *System
  Architecture* / *Prompt Engineering* / *Python*; an analytical `.xlsx` or report review → *Data
  Analysis* / *Business Analysis*.
- For **measured** (not inferred) skills, the live-session telemetry path (`mine_session.py` →
  `_telemetry.jsonl`) supplies real per-session signals; past OneDrive-only sessions can only be
  tagged by inference, so note that in the report.

### 4b. Align to the durable taxonomy memory, then derive process + JTBD (registry-first)

**Business Process is the report's aggregation anchor; JTBD and Project nest under it. The standalone
Job layer has been dropped.** Process and Project NAMES are kept STABLE across runs by a durable
**taxonomy memory**, so the model does not re-invent names each run.

**The memory is PER-USER and never shared.** The registry is scoped to the invoking user:
- Its filename embeds a sanitized key from the user's email —
  `/mnt/user-config/.claude/cowork-process-registry.<userkey>.json` — and it carries an `owner`
  field. `/mnt/user-config/.claude/` is the invoking user's own mount and syncs to **their** OneDrive
  `Documents/Cowork/` folder, so this file lives in the user's Cowork folder and is theirs alone.
- **`reconcile_taxonomy.py` derives the path and owner from the user's email** (harvested into
  `working/cowork_raw.json` `meta.email` in step 2; pass it explicitly with `--owner`). It **ignores
  any registry whose `owner` does not match the invoking user** (a leaked/inherited/unstamped file),
  so a **first run has no memory** and mints processes from the user's OWN sessions.
- **Nothing user-specific is ever committed to the skill folder.** The per-run overrides are scratch
  under `working/`; there is no bundled seed.

1. **Reconcile against the user's own memory — align first, create only if novel.** After writing
   `working/cowork_raw.json` (step 3) and BEFORE `classify.py`, run (pass the signed-in user's email
   from step 2 as `--owner`):
   ```
   python scripts/reconcile_taxonomy.py --in working/cowork_raw.json \
       --owner "<signed-in user's mail>" --overrides working/process_overrides.json
   ```
   For each session it: (a) matches the goal to a **known Project** (exact slug or near-identical
   title) and reuses its `{process, pillar, jtbd}`; else (b) matches the goal to an **existing
   Process** by keyword similarity and reuses `{process, pillar}` + the process default JTBD,
   registering a new project under that existing process; else (c) mints a **new Process** (flagged
   `"new": true`) for genuinely novel work. It writes `working/process_overrides.json` (consumed by
   `classify.py`) and **persists the owner-stamped registry** to the per-user path above.
2. **Surface anything new (interactive runs).** If the script prints `NEW processes minted`, tell the
   user the new name(s) and offer to rename — edit the registry's `processes`/`projects` and re-run
   `reconcile_taxonomy.py`. On unattended/scheduled runs it auto-creates the flagged entry and never
   blocks. (On a genuine first run EVERY process is new — that is expected, not an error.)
3. `classify.py` then reads the overrides via `--overrides working/process_overrides.json` (each
   session → `{process, pillar, job, jtbd}`; `job` is retained = the process name only for back-compat
   with the not-yet-migrated member skill — it is **not** shown in this report). Pillars follow
   [references/value-pillars.md](references/value-pillars.md); the registry stores each process's pillar.
4. **No-memory fallback:** on a first run (or when the owner guard ignores a non-matching file) the
   registry starts empty and is built from the processes THIS run discovers; if `reconcile_taxonomy.py`
   cannot run, `classify.py` falls back to the generic APQC taxonomy in `scripts/apqc_taxonomy.json`.
   The optional [references/map-my-work-playbook.md](references/map-my-work-playbook.md) can still be
   used to enrich process/JTBD naming for novel work before it is written to the registry.

The report's **Work by business process** section pivots on Process: each process is an accordion with
its subtotal (**sessions · hours · value · % of time**), the distinct **JTBD(s)** it served, and the
**projects** beneath it. A secondary **By pillar** toggle groups the same projects by value pillar.

> **Memory-first rule:** a run a week from now must locate the invoking user's own
> `/mnt/user-config/.claude/cowork-process-registry.<userkey>.json` and align to it; only truly novel
> work adds a name. `reconcile_taxonomy.py` enforces this deterministically and per-user.

> **Packaging guardrail (privacy):** NEVER bundle the registry, any
> `cowork-process-registry*.json` (including the per-user file), or a populated
> `process_overrides.json` when zipping/sharing this skill. Overrides must ship as `{}`. Personal
> jobs/processes leaking into another user's run is a fatal flaw — the per-user owner guard and the
> `working/` overrides path exist specifically to prevent it.

### 5. Compute & render (bundled scripts — no hand arithmetic)
- `python scripts/compute.py --in working/cowork_sessions.json --out working/cowork_roi_data.json`
- `python scripts/build_report.py --data working/cowork_roi_data.json --out output/cowork-roi-report.html`
- Verify: `Glob output/cowork-roi-report.html`. If missing, locate and move into `output/`.
- **Run each pipeline script as its own command.** Do NOT append an inline schema-guessing inspection (e.g. a `python -c` that indexes keys you assume exist) to the same command — if the snippet's guess is wrong it exits non-zero and the *whole step shows as Failed* even though the script succeeded. Trust each script's own printed summary line; inspect output only with a separate, defensive read.

(The scripts are in this skill's `scripts/` folder. `compute.py` holds the methodology bands; `build_report.py`
is the renderer and embeds the glossary + clickable slide-12 sources.)

### 6. Show highlights & verify
Present a short highlights summary (or a `render_ui` card via the `render-ui` skill): speed multiplier,
expert-equivalent hours, professional-services value, top 3 categories and top goals. Tell the user the report is saved to their files.

### 7. Automate (only if the user chose it in Q2)
Call `SetupScheduledPrompt` with **execution_mode="inline"**, frequency **Day**, **interval = N** (7/15/30),
hours `["8"]`, name "Cowork ROI report (every N days)", and a **self-contained** description such as:
> "Generate my Copilot Cowork impact report for the last N days: harvest my Cowork sessions from OneDrive (the inputs I analyzed and outputs I produced per session), classify them, apply the artifact-scaled two-clock model to produce a speed multiplier and a professional-services-equivalent value at $72/hr, render the HTML report to output/, then email me the highlights with the HTML file attached."

Confirm in plain language: "Done — I'll rebuild this every N days and email you the digest."

### 8. Email digest (if automating, or if the user asks to email it)
`SendEmailWithAttachments(to=[<user's own email>], subject="My Copilot Cowork impact — <window label>",
body="<highlights as HTML: speed multiplier, expert-equivalent hours, professional-services value, top categories/goals>",
content_type="HTML", direct_attachment_file_paths=["output/cowork-roi-report.html"])`.
Send to a different recipient only if the user explicitly names one.

---

## Methodology — research-anchored bands + v5 two-clock speed multiplier
The **Typical** value is what the report applies; **Low/High** form the published range. Each Typical is a
per-instance figure from a study × the typical instances per Cowork run — not picked from a range.

| Category | Low | **Typical** | High | Source(s) for the Typical value (slide 12) |
|---|---|---|---|---|
| Analysis & Research | 30 | **71** | 92 | Stanford-WB SSRN 5136877 · OpenAI Deep Research · McKinsey 2023 |
| Document & content creation | 12 | **24** | 42 | Microsoft Research 2026 (Verma·Suri·Counts) — causal-impact DiD, n=72,186 |
| Email workflows | 3 | **7** | 12 | Noy & Zhang Science 2023 · NBER w33795 (Dillon 2025) |
| Meeting workflows | 12 | **31** | 45 | Cambon et al. MSR 2024 · Anthropic Agents 2024 · Forrester TEI 2024 |
| Communication workflows | 2 | **4** | 6 | Microsoft WTI 2024 · NBER w33795 (Dillon 2025) |
| Specialized workflows | 10 | **25** | 40 | Forrester TEI Power Automate 2024 · UK GDS Cross-Government 2025 |
| Write or debug code | 30 | **56** | 96 | Cui et al. CACM 2024 · Peng et al. RCT 2023 · Stanford-WB SSRN 5136877 |
| General assistance / Other | 2 | **5** | 8 | Brynjolfsson, Li & Raymond QJE 2025 / NBER w31161 · Microsoft WTI 2024 |

Source URLs are embedded as clickable links inside the generated report's Glossary (`build_report.py`).

**Two-clock model (v5).** The bands above feed the *expert (unassisted) clock*; the report's headline is a
**speed multiplier** and a **professional-services-equivalent value** — there is no ROI/seat-cost figure
(credit & seat consumption isn't available).
- **Expert clock (min/session)** = Σ analysis-band per analysis task + Σ general-band per general task
  + 12 min to read each input source (5 min/image) + an authoring band per output (deck 45 · doc 40 · sheet/page/code 35 · other 30).
  `document` tasks contribute only via output authoring (no double-count with the analysis band).
- **Assisted clock (min/session)** = 8 (prompt/setup) + 2 × (#inputs + #outputs), floor 4 — a modeled estimate;
  prefer a measured `exec_min` when telemetry (`mine_session.py`) provides one.
- **Speed multiplier** = Σ expert ÷ Σ assisted (rate-independent). **Value** = (Σ expert ÷ 60) × hourly rate.
- **Conservative / Optimistic** re-run the expert clock with the floor/ceiling analysis bands and lighter/heavier read & authoring weights.

The report also renders an **Analyzed → Produced** breakdown (inputs analyzed vs. outputs produced, by type) from the same artifact counts.

---

## Guardrails
- **No fabricated work.** Every run task traces to a real session/artifact. If a category has zero artifacts, show zero — never invent.
- **Conservative counting.** Cap ~2 tasks/session; fold supporting files into the primary task. Prefer credible over impressive.
- **No hand arithmetic.** All numbers come from `compute.py`.
- **Privacy.** Show artifact filenames and short goal phrases only — never file contents.
- **Per-user memory — never leak it.** The taxonomy registry is owner-scoped and owner-stamped;
  `reconcile_taxonomy.py` ignores any file that isn't the invoking user's. NEVER bundle the registry,
  any `cowork-process-registry*.json`, or a populated `process_overrides.json` when packaging/sharing
  the skill — overrides ship as `{}` and live under `working/` at runtime.
- **Send/automate only on approval.** Show the report first; only schedule or email after the user opts in (Q2).
- **Fail open.** If the OneDrive Cowork folder is missing/404, note it and ask for the folder name rather than aborting.

## Bundled files
- `scripts/mine_session.py` — mines the live session transcript for measured run time, tool intensity and artifacts (telemetry).
- `scripts/reconcile_taxonomy.py` — **per-user taxonomy memory** (align-first, create-if-novel): reads the invoking user's owner-scoped registry (ignoring any file that isn't theirs), aligns each session to an existing Process/Project, mints new only for novel work, writes `working/process_overrides.json` + persists the owner-stamped registry. Runs BEFORE `classify.py`. Takes `--owner`.
- `scripts/classify.py` — deterministic ext→category classifier; reads the per-run overrides via `--overrides working/process_overrides.json`; emits the schema compute.py consumes.
- `scripts/compute.py` — applies the research-anchored bands + v5 two-clock speed-multiplier model → payload JSON (Process rollup carries `pct_time`).
- `scripts/build_report.py` — renders the single-file HTML report. **Work-by-process is Process-anchored** (Process ▸ JTBD ▸ Project; Job layer dropped), plus speed multiplier, Analyzed→Produced, glossary, clickable sources, live rate, PDF.

## Durable files (outside the skill, persist across sessions — PER-USER, never bundled)
- `/mnt/user-config/.claude/cowork-process-registry.<userkey>.json` — the invoking user's **own** taxonomy memory (canonical Processes + Projects + JTBDs), carrying an `owner` field. `<userkey>` is derived from the user's email; the file lives on the user's per-user mount (syncs to their OneDrive Cowork folder). Read first, aligned to, and persisted by `reconcile_taxonomy.py` every run. Each user has their own file; `reconcile_taxonomy.py` ignores any file whose `owner` isn't the invoking user. The member / aggregated skills use the same per-user, owner-scoped scheme.
- `/mnt/user-config/.claude/cowork-session-telemetry.json` · `…-credits.json` · `…-session-costs.json` — measured run-time / credit / cost logs (optional inputs).
