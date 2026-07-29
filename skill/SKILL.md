---
name: cowork-roi-report
description: |
  Generates a Microsoft-branded "What Cowork Did for Me" self-contained HTML impact report from the
  signed-in user's own Copilot Cowork session history in OneDrive. Quantifies leverage as a speed
  multiplier and a professional-services-equivalent value using research-anchored task-category bands
  and an artifact-scaled two-clock model, with a live hourly-rate control, KPIs, a work-by-business-process
  breakdown, a projects-by-category view, and an activity heatmap.

  Use when the user asks to "generate my impact summary report", "generate my impact report",
  "my impact summary", "my Cowork ROI", "what Cowork did for me", "Cowork impact report",
  "Copilot Cowork ROI report", "how much time has Cowork saved me", "my Cowork value report",
  or any request for a personal impact / ROI / value report on Copilot Cowork usage.

  Do NOT use for: GitHub Copilot / IDE reports, team-wide announcements, single-meeting summaries,
  or daily briefings.
cowork:
  category: analysis
  icon: BarChart4
---

# Cowork ROI — Impact Report Generator

Builds a personal, shareable impact report from the user's **own** Copilot Cowork footprint. Self-service:
reads the signed-in user's Cowork session workspaces in OneDrive, classifies the work into the eight
methodology categories, applies research-anchored time-savings bands, and renders a Microsoft-branded HTML
web app; optionally automates itself and emails a digest. Generic — works for **any** user; no data hard-coded.

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
- **Copilot seat cost:** not used — the report shows a speed multiplier + professional-services value, not an ROI ratio.
- **Default email recipient:** the signed-in user themselves.

---

## Workflow

### 1. Ask the user (one `AskUserQuestion`, two questions)
- **Q1 — Period:** "Which period should the report measure?" → options **Last 7 days**, **Last 15 days**, **Last 30 days**.
- **Q2 — Delivery:** "How do you want to run it?" → options:
  - **Just run it once** (generate the report now, no automation)
  - **Run now & automate every N days, email me a digest** (N matches the period: 7→every 7 days, 15→every 15, 30→every 30; each run emails the highlights with the HTML attached)

Do not schedule until the user explicitly chooses the automate option in Q2 (the platform also shows its own approval dialog).

### 2. Resolve identity & dates
- `GetMyDetails(select="mail,userPrincipalName,displayName")` → user name + email.
- `after` = N days ago 00:00 local; `before` = today 23:59 local; `window.label` = "Last N days", `window.months` = N/30 rounded (legacy).

### 3. Harvest the user's Cowork sessions (the data source)
Cowork persists each session's workspace to OneDrive under **`Documents/Cowork/`** — the artifacts are the
signal (no chat transcript). Harvest **all three** folder layouts (different users/versions sit on different ones):
- **Task folders** (current): `Documents/Cowork/Tasks/<goal-slug>-<YYYY-MM-DD>/` → `input/`+`output/`
- **Root goal folders**: `Documents/Cowork/<goal-slug>-<YYYY-MM-DD>/` → `input/`+`output/`
- **Legacy UUID sessions**: `Documents/Cowork/sessions/<session-uuid>/` → `input/`+`output/`

- `GetDefaultDrive()` → personal OneDrive `drive_id`.
- **Locate the Cowork folder — do NOT assume the name** (may be suffixed/localized: `Cowork 2`, `Colaborar`, …).
  Try `/Documents/Cowork`; on 404 list `/Documents` and pick the child starting `Cowork` (prefer exact, else
  highest-numbered), else drive-root `/Cowork`, else ask once. Carry the resolved name forward.
- **Enumerate all three layouts** (`Tasks/`, root goal-folders, `sessions/`) and **follow pagination**
  (`@odata.nextLink`) to exhaustion — a page caps at ~20–100 items.

- **Allow-list by app id.** Count a folder/artifact ONLY when its `createdBy.application.id` is the **Cowork app
  id `6ab48b67-cd74-4ad4-81af-5932984589be`** (robust across users/tenants) — never key on folder *names*.
- **NEVER enumerate `Documents/Apps/…`** — that tree is the M365 Copilot "Scout" product (Graph app
  `99fa64eb-…`), not Cowork. Skipping it excludes Scout for every user with no name list to maintain.

- Keep session folders whose `createdDateTime`/`lastModifiedDateTime` falls in the window.
- For each kept session, `GetDriveChildren` into `output/` (and `input/`) to collect filenames, extensions and
  per-file `createdDateTime` (parallel batches).
- **Counting discipline.** Task folders accumulate artifacts over days — do NOT derive `exec_min` from
  file-timestamp spans (leave null; prefer telemetry). Fold supporting files (screenshots, variant HTML,
  READMEs, lock files) into the session's primary deliverable. Keep output-less sessions (empty `outputs` →
  `classify.py` tags `general`).
- **Live-session telemetry.** `mine_session.py --log /mnt/user-config/.claude/cowork-session-telemetry.json`
  logs each session's measured `exec_min`, tool intensity and artifacts. In the harvest, **merge in any session
  id not covered by a Cowork folder** (`has_folder:false`, `outputs:[]`); prefer telemetry `exec_min` where both
  exist. Forward-only — cannot backfill sessions predating the hook.

### 4. Classify each session into run tasks (the methodology)
A **session** contains one or more **run tasks**; each run task maps to exactly one of the eight categories
below.

**Value model = RUNS × BAND.** Time saved = Σ over runs of each run's category band (minutes saved/run); each
band already sums the activity chain inside one run, so **count runs × band** — never per-LOC or per-artifact
add-ons. Count runs from tool-chains (code run ≈ 6 code-edits; analysis run ≈ 5 research calls); `mine_session.py`
writes a `runs:{category:count}` field. Without telemetry, estimate runs conservatively and label as estimates.
`compute.py` applies `Σ runs × CATS[band]`.

**Use the deterministic classifier — do NOT hand-tag categories.** Write the harvested sessions (with
`inputs`, `outputs` and `exec_min`) to `working/cowork_raw.json`, then run:
`python scripts/classify.py --in working/cowork_raw.json --out working/cowork_sessions.json --overrides working/process_overrides.json`.
It maps each session's real artifact **extensions** to categories (e.g. `.xlsx/.csv`→analysis, `.docx/.pptx/.pdf`→document,
`.html/.py/.ps1`→code, `.zip`→special), caps ~2 run tasks/session, and tags output-less sessions `general`.
This is the fix for the failure mode where every session was stamped with the same category pair and every
goal collapsed to the same hours — **never assign the same default categories to every session.** You may bump
a clearly analytical deliverable (a synthesis report saved as `.docx/.pptx`) to `analysis`, but the extension
map is the default. **Be conservative — credibility matters more than a big number.**

**Goal-text signals (v25) — the classifier also reads the goal phrase, not just the file extension.**
Alongside the extension map, `classify.py` scans each goal against signal vocabularies derived from the
Cowork usage taxonomy table (its Description/Examples column). This lets a session land in the right bucket
even when it saved no telltale file: `document` (drafting docs/decks, editing text, creating visuals,
organizing files in OneDrive/SharePoint), `comms` (Teams messages, communication rules), and `special`
(workflow automation, recurring/scheduled prompts, task lists, multi-step M365 flows, connectors: Dynamics
365, ADO Boards, Power BI, Fabric, ServiceNow, Salesforce, SAP) are now detectable from goal text — as
`analysis`, `code`, `email`, `meeting` already were. The 8 categories, the extension map, the 2-per-session
cap and the PRIORITY tie-break are unchanged; the category path stays fully deterministic (no LLM).

Extension→category heuristics, counting discipline, and the exact `working/cowork_raw.json`
schema `classify.py` consumes are in **[references/classification-reference.md](references/classification-reference.md)**.
Key rules: cap **~2 run tasks/session**, fold supporting files into the primary task, and report
categories with no artifacts as **zero** (a conservative floor).

### 4a. Tag the skills behind each deliverable (populates "Skills augmented")

**Required — else the Skills-augmented and Deliverables tables render empty.** Tag each output (and each
chat-only session) with the **professional skills** Cowork exercised, ONLY from `scripts/skills_vocabulary.json`:
a `skills:[...]` array per `outputs[]` item (or session-level for chat-only). Also tag `professional_roles:[...]`
per session — the **1–2 roles a billing firm would charge** (guide: `scripts/roles_taxonomy.json`) — driving the
"Roles Cowork assembled for me" section; if omitted, `classify.py` keyword-matches. **Tag conservatively from the
deliverable** (e.g. `.pptx`→*Presentation Design*; `.docx`→*Technical Writing*; skill `.zip`→*System Architecture*/
*Prompt Engineering*; `.xlsx`→*Data Analysis*) — never invent a skill outside the vocabulary. Past OneDrive-only
sessions are inferred, not measured — note that in the report.

### 4b. Align to the durable taxonomy memory, then derive process + JTBD (registry-first)

**Business Process is the aggregation anchor; JTBD and Project nest under it.** Process/Project names are
kept STABLE across runs by a durable **taxonomy memory**, so the model doesn't re-invent names each run.

**The memory is PER-USER and never shared.** The registry filename embeds a sanitized key from the user's
email (`/mnt/user-config/.claude/cowork-process-registry.<userkey>.json`) and carries an `owner` field on the
user's own mount. `reconcile_taxonomy.py` derives path+owner from `meta.email` (pass `--owner`) and **ignores
any registry whose `owner` ≠ the invoking user**, so a first run mints processes from the user's OWN sessions.
Nothing user-specific is committed to the skill folder; overrides are scratch under `working/`.

1. **Reconcile first — align, create only if novel.** After writing `working/cowork_raw.json` (step 3) and
   BEFORE `classify.py`, run:
   ```
   python scripts/reconcile_taxonomy.py --in working/cowork_raw.json \
       --owner "<signed-in user's mail>" --overrides working/process_overrides.json
   ```
   Per session it (a) matches a **known Project** and reuses `{process,pillar,jtbd}`; else (b) matches an
   **existing Process** by keyword and registers a new project under it; else (c) mints a **new Process**
   (`"new":true`). Writes `working/process_overrides.json` and persists the owner-stamped registry.
2. **Surface anything new (interactive runs).** If the script prints `NEW processes minted`, tell the
   user the new name(s) and offer to rename — edit the registry's `processes`/`projects` and re-run
   `reconcile_taxonomy.py`. On unattended/scheduled runs it auto-creates the flagged entry and never
   blocks. (On a genuine first run EVERY process is new — that is expected, not an error.)
3. `classify.py` then reads the overrides via `--overrides working/process_overrides.json` (each
   session → `{process, pillar, job, jtbd}`; `job` is retained = the process name only for back-compat
   with the not-yet-migrated member skill — it is **not** shown in this report). Pillars follow
   [references/value-pillars.md](references/value-pillars.md); the registry stores each process's pillar.
4. **No-memory fallback:** a first run builds the registry from processes discovered THIS run; if
   `reconcile_taxonomy.py` can't run, `classify.py` falls back to `scripts/apqc_taxonomy.json`. Optional:
   [references/map-my-work-playbook.md](references/map-my-work-playbook.md) to enrich novel process/JTBD naming.

The report's **Work by business process** section pivots on Process: each process is an accordion with
its subtotal (**sessions · hours · value · % of time**), the distinct **JTBD(s)** it served, and the
**projects** beneath it. A secondary **By pillar** toggle groups the same projects by value pillar.
**(v25 layout:** primary lens, rendered directly **under the KPI cards** in a quiet panel (single-caret
rows, whole row clickable). A companion **Projects by category** section folds the same projects into a
collapsible bucket per category; the former task-category and Roles **bar charts are removed** (replaced by
the fold + a clean role list).**)**

> **Memory-first + packaging:** each run locates the user's own owner-scoped registry and aligns to it (only
> novel work adds a name). NEVER bundle the registry, any `cowork-process-registry*.json`, or a populated
> `process_overrides.json` when sharing — overrides ship as `{}`. Personal processes leaking into another
> user's run is a fatal flaw the owner guard + `working/` overrides path exist to prevent.

### 5. Compute & render (bundled scripts — no hand arithmetic)
- `python scripts/compute.py --in working/cowork_sessions.json --out working/cowork_roi_data.json`
- `python scripts/build_report.py --data working/cowork_roi_data.json --out output/cowork-roi-report.html`
- Verify: `Glob output/cowork-roi-report.html`. If missing, locate and move into `output/`.
- **Run each pipeline script as its own command** — never append an inline schema-guessing `python -c`; a wrong
  guess exits non-zero and marks the whole step Failed even when the script succeeded. Trust each script's printed
  summary; inspect output with a separate defensive read. (`compute.py` holds the bands; `build_report.py` renders.)

### 6. Show highlights & verify
Present a short highlights summary (or a `render_ui` card): speed multiplier, expert-equivalent hours,
professional-services value, top 3 categories and top goals. Tell the user the report is saved to their files.

### 7. Automate (only if the user chose it in Q2)
`SetupScheduledPrompt` with `execution_mode="inline"`, frequency **Day**, **interval = N** (7/15/30), hours
`["8"]`, name "Cowork ROI report (every N days)", and a **self-contained** description that restates the full
workflow (harvest my Cowork sessions for the last N days → classify → two-clock model at $72/hr → render HTML
to output/ → email me the highlights with the HTML attached). Confirm: "Done — I'll rebuild every N days and email the digest."

### 8. Email digest (if automating, or if asked to email it)
`SendEmailWithAttachments(to=[<user's own email>], subject="My Copilot Cowork impact — <window label>",
body="<highlights as HTML>", content_type="HTML", direct_attachment_file_paths=["output/cowork-roi-report.html"])`.
Send to a different recipient only if the user explicitly names one.

---

## Methodology (summary)
The report applies each category's research-anchored **Typical** minutes-saved band (Low/High form the
published range); an **expert clock** (Σ bands + read + authoring) vs a modeled **assisted clock** yields the
**speed multiplier**, and **value** = expert-hours × rate. No ROI/seat-cost figure (credit data unavailable).
Full bands table, per-category sources, and the two-clock formulas: **[references/methodology.md](references/methodology.md)**.
`compute.py` holds the authoritative constants — never hand-compute.

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
- `scripts/mine_session.py` — telemetry: measured run time, tool intensity, artifacts per session.
- `scripts/reconcile_taxonomy.py` — per-user taxonomy memory (align-first, create-if-novel); runs BEFORE `classify.py`; takes `--owner`.
- `scripts/classify.py` — deterministic ext→category classifier; reads `--overrides`; emits the schema `compute.py` consumes.
- `scripts/compute.py` — research-anchored bands + two-clock model → payload JSON (Process rollup carries `pct_time`).
- `scripts/build_report.py` — renders the single-file HTML (Process-anchored work-by-process, projects-by-category, glossary, live rate, PDF).

## Durable files (outside the skill, persist across sessions — PER-USER, never bundled)
- `/mnt/user-config/.claude/cowork-process-registry.<userkey>.json` — the user's **own** owner-stamped taxonomy memory (Processes + Projects + JTBDs); `<userkey>` from email, on the per-user mount. Read/aligned/persisted by `reconcile_taxonomy.py` each run; any file whose `owner` ≠ invoking user is ignored. Member/aggregated skills use the same scheme.
- `/mnt/user-config/.claude/cowork-session-telemetry.json` · `…-credits.json` · `…-session-costs.json` — measured run-time / credit / cost logs (optional).
