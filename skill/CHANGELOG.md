# Cowork ROI Report — Changelog

---

## v41 — Cowork-fit: strict H/M/L/? hierarchy; `?` used sparingly; automation → High

Reworks the deterministic grader into an explicit, evidence-first hierarchy and fixes the
over-use of the "Insufficient evidence" (`?`) grade.

### Cowork-fit classifier (`scripts/compute.py`)
- **Strict hierarchy (first match wins):** (1) **≥2 apps in play** — apps the actions
  touched (verified) unioned with apps inferred from outputs, goal and related sessions —
  → **H**; (2) output shows **code generation, automation/workflow, multi-document
  synthesis, or multiple different output formats** → **H**; (3) purely **conversational**
  → **L**; (4) **multi-format input / many files / platform op** → **M**; (5) single
  app/output a lone Copilot could do → **L**; (6) truly no signal → **`?`**.
- **`?` is now rare.** A missing action trace no longer forces `?` — the grade is still
  inferred from outputs, goal and related sessions. `?` is reserved for a saved output of
  an unrecognized type with no code/automation/multi-format/cross-app signal and no trace.
  (Previously any trace-less session collapsed to `?`.)
- **Automation / workflow is now High** (was floored to Moderate) — inbox triage, channel
  scan, sweep, connector, recurring/workflow runs.
- **Better cross-app inference:** a *sharing / distribution* goal now implies Outlook, so
  e.g. a "value story sharing tracker" saved as `.xlsx` reads as Outlook + Excel → **H**.
- **Moderate is now the true middle:** multi-format *input* (≥2 input formats) or juggling
  a large number of files, or a lightweight Cowork-platform op.
- **AI-review guard** generalized: the review can't silently downgrade a strong **H**
  (verified cross-app, automation/workflow, or build) to **L/`?`** without explicitly
  resolving the conflict (else flagged **AI-review-rejected**).

### Report & docs (`scripts/build_report.py`, `SKILL.md`, `classification-methodology.md`)
- Glossary, legend, KPI copy and methodology rewritten to describe the hierarchy and the
  rare `?` state.

---

## v40 — Cowork-fit: evidence-based grading (assess what Cowork *did*, not just the file)

The classifier now grades the **workflow** — the apps its actions touched, the sources it
reviewed, and its outputs — rather than inferring a single surface from the one file that
was saved.

### Evidence capture (`scripts/mine_session.py`, `scripts/classify.py`)
- Mines and passes through four new per-session fields: **`request`** (the original ask),
  **`actions`** (tool/action sequence, first-seen order), **`apps_accessed`** (apps proven
  by the action trace, e.g. Outlook, Excel, Teams), and **`sources_reviewed`** (count).
- These are populated **only when the action history is available** and left **absent**
  (not `[]`) when it is not — absence is the signal to fall back to Insufficient evidence.

### Cowork-fit classifier (`scripts/compute.py`)
- **Apps drive the grade.** The grader unions **verified** apps (from actions) with apps
  **inferred** from outputs and related sessions. A cross-app workflow (e.g. **Outlook +
  Excel → H**) grades High on evidence, not on the single output file.
- **New `?` — Insufficient evidence.** When there is no action history, a lone output can
  no longer establish an Excel-only (or any single-app) workflow, so the work is left
  **unassessed** instead of defaulting confidently to **L**.
- **Verified vs inferred cross-app.** H is flagged *verified* when the action trace proves
  two or more apps, *inferred* when only outputs imply it.
- **AI-review guardrail.** The review may **not** downgrade **verified cross-app** work to
  **L**, nor **automation** below **M**, unless it explicitly resolves the conflicting
  evidence; a blocked attempt is flagged **AI-review-rejected** (rule grade kept).

### Report & export (`scripts/build_report.py`, `scripts/to_csv.py`)
- Report renders the grey **`?` (Insufficient evidence)** badge, a fourth summary KPI, and
  an evidence-first Cowork-fit glossary entry.
- CSV adds **`cowork_fit_evidence`**, **`cowork_fit_apps`**, and
  **`cowork_fit_verified_cross_app`** columns.

---

## v39 — Cowork-fit: automation floor + Moderate-fit redefinition; date-only output

Three refinements to how work is graded and reported.

### Cowork-fit classifier (`scripts/compute.py`)
- **Automation can never be Low.** A single-surface process that is automation-style —
  inbox triage, channel scan, sweep, workflow, monitor, recurring/batch/bulk, pipeline —
  is now floored from **L → M**. These orchestrate work across items, so they are never a
  one-shot single-app Copilot task.
- **Moderate fit redefined.** A task that one in-app Copilot could technically do is lifted
  **L → M** when it juggles a **large number of files**, performs **multi-file-format
  synthesis** (inputs spanning ≥2 formats), or **generates multiple outputs from
  multi-format inputs**. The **M** grade is now labelled **"Moderate fit"** everywhere
  (badge legend, glossary, CSV, methodology reference).

### Report output (`scripts/build_report.py`, `SKILL.md`)
- **Dates only — no timestamps.** The report footer renders the generated date with the
  clock time stripped, and the workflow now instructs the readout to show dates only.
- **No meta sections.** The readout must not add "Scope", "Evidence Limitations", or
  similar caveat blocks — the standing caveats already live in the report's methodology
  and glossary.

No band, methodology-weight, or schema change; grades only move within the existing H/M/L.

---

## v38 — Fix telemetry undercount for surface-based categories (email/comms/meeting)

Heavy Outlook/Teams/meeting users saw **Email, Communication, and Meeting workflows
undercounted or zero**. The harvest is artifact-based, so inbox-triage, channel-triage,
and meeting-recap sessions that produce no output file were not credited to their category.

### Root cause
`compute.py` trusts each session's telemetry `runs` dict verbatim, but `mine_session.py`'s
`runs_est` only ever emitted `code` and `analysis` runs. Outlook-mail, Teams, and
transcript/calendar tools were lumped into `_RESEARCH`, so artifact-free sessions were
mislabeled as Analysis (or dropped out entirely for Teams), starving the correct band to zero.

### The fix (`scripts/mine_session.py`)
Carved dedicated tool buckets, removed from `_RESEARCH`, each emitting its own run:
- Outlook **mail** tools → `email` (band 3/7/12)
- **Teams** tools → `comms` (band 2/4/11)
- **transcript + calendar** tools → `meeting` (band 12/31/43)

Prefix matching keeps `mcp__outlook_calendar__*` routing to meeting (not email). Divisors
(`/4` email, `/4` comms, `/3` meeting) are conservative, consistent with the existing `/6`
code and `/5` analysis heuristics. No band, methodology, schema, or public-interface change.

---

## Cowork ROI Report — v37

Fixes a confusing Cowork-fit hover label on AI-reviewed grades.

### The bug
When the optional LLM review layer **changed** a project's grade (e.g. upgraded a
data-to-deck project the rule scored Low up to **High**), it overrode the grade and
the "why" sentence but **kept the rule's original label**. Because the report's hover
tooltip is built as `label + ": " + why`, a High badge could read:

> "PowerPoint Copilot could do it: Cross-surface, multi-step … needs Cowork."

— a single-app label contradicting the High grade it now carried.

### The fix (`scripts/compute.py`)
- Added `CF_REVIEW_LABELS = {"H": "Needs Cowork", "M": "Borderline fit",
  "L": "Single-app Copilot could do it"}`.
- In the review layer, when a review **changes** the grade and supplies no label of
  its own, the label is now **regenerated to match the new grade**. An upgraded High
  therefore reads **"Needs Cowork: …"** and leads with the justification for Cowork,
  never the rule's single-app label. An explicit `review.label` still wins; a
  confirmed (unchanged) grade keeps its rule label.

No change to grades, the value model, categories, the report layout, or the CSV.

---

## Cowork ROI Report — v35

Adds a built-in **CSV export** so every report now emits a session-level data file
alongside the HTML.

### New: `scripts/to_csv.py`
- Emits `output/cowork-sessions.csv` — a tidy, **single-grain** export: **one row
  per session** (the atomic unit everything rolls up from). Because it is
  single-grain, `SUM(value_usd)` over the file is the real total with **no
  double-counting** — the category/process/role rollups stay in the report, not
  appended here.
- 28 columns: run/window identity, process, JTBD, value pillar, category (primary +
  full pipe-delimited list), conversational flag, run-task / input / output counts,
  `total_interactions`, skills, professional roles, hours, value, speed, credits,
  cost, and the full **Cowork-fit hybrid** (grade, method, rule_grade, label,
  surfaces, why).
- CSV hygiene: UTF-8 **with BOM** (Excel renders ×, — correctly), every field
  quoted, ISO dates, pipe-delimited multi-value fields, stable column order, a
  `run_id` on every row for safe appends across weekly runs.
- **Blanks are honest n/a:** `credits`/`cost_usd` without cost telemetry;
  `total_interactions` without the live-session telemetry hook.

### Supporting change: `scripts/compute.py`
- Each session (goal) in the payload now also carries `n_inputs`, `n_outputs`,
  `skills`, and `total_interactions` (from a new telemetry-turns lookup =
  user + assistant turns), so `to_csv.py` reads a **single source** (the payload)
  with no re-joining.

### Wiring
- Workflow step 5 now runs `to_csv.py` after `build_report.py`; step 6 tells the
  user both the HTML report and the CSV are saved. `to_csv.py` added to Bundled
  files.

No methodology, category, or grade-logic change. SKILL.md stays under 20,000 chars
with a 2,000 buffer; description 960.

---

## Cowork ROI Report — v34

Category relabeling + a hybrid (rule + LLM) Cowork-fit, answering an honest
critique of the "entirely deterministic" claim.

### Category labels aligned to the report's own names
The methodology reference and `classify.py` comments now use the report's eight
labels consistently (they had drifted to the taxonomy-table wording):
- "Email & communication" → **Email workflows** (Outlook) **and** **Communication
  workflows** (Teams) — kept as two separate categories.
- "Workflow automation" → **Specialized workflows**; "Meeting intelligence" →
  **Meeting workflows**; "Code assistance" → **Write or debug code**; "General
  assistance & Learning" → **General assistance / Other**.

### Communication workflows = Teams-centered
Clarified and enriched: **Communication workflows** covers the same ideas as Email
(synthesizing, posting, triaging, managing) but on **Microsoft Teams** — messages
and channels (chats, channel posts, replies, announcements, @mentions). Email stays
Outlook-centered. `COMMS_SIGNALS` expanded accordingly.

### Cowork-fit is now a two-layer hybrid (rule + LLM review)
Addresses the contradiction of calling a capability judgment "deterministic":
- **Layer 1 — deterministic rule** produces a reproducible baseline grade + reason.
- **Layer 2 — LLM review** may confirm or adjust each grade (per-session
  `cowork_fit_review` in the harvest), because "could another Copilot have done it"
  is judgment, not something a keyword can settle. Each grade is flagged
  **rule-based**, **AI-confirmed**, or **AI-reviewed**, with the rule grade kept for
  transparency (e.g. "M · AI-reviewed [rule said L]"). Every dot's hover now shows
  the reason **and** the method.
- The honesty section is rewritten: category classification is genuinely
  deterministic; Cowork-fit's judgment layer is explicitly *not* infallible and is
  labeled as judgment per project.

### Methodology reference updated
`references/classification-methodology.md` now uses the eight report labels, spells
out Email-vs-Teams, and documents both layers of the Cowork-fit hybrid plus the
corrected honesty/limits.

SKILL.md stays under 20,000 chars with a ≥2,000 buffer; description 960.

---

## Cowork ROI Report — v33

Cowork-fit refinements + a new methodology reference.

### Cowork-fit (`scripts/compute.py`)
- **Specialized workflows now grade High by default.** Automation, connectors,
  scheduled/recurring prompts and skill builds are Cowork-native — no in-app
  Copilot runs them — so they are a High match almost every time. (Previously the
  three skill-management sessions were graded "M / Managing Cowork".)
- **Cross-session orchestration is now detected.** A deliverable built across two
  sessions (e.g. identify the emails in one session, build the Excel tracker in
  another) unions the surfaces from every contributing session, so it reads as
  **cross-surface (H)** in both — fixing "Build the value-story tracker" being
  graded Low when it is really an Outlook→Excel effort.
- Net on the sample window: Cowork-fit moves to **7 H · 0 M · 1 L** (the lone L is
  the single-surface PowerPoint chart redesign).

### Hover reasons (`scripts/build_report.py`)
- Every H/M/L dot already carries a **project-specific reason**; v33 adds a
  `cursor:help` + hover ring so the dots are visibly hoverable, and a new
  "Specialized workflow" reason string.

### New: methodology reference (`references/classification-methodology.md`)
- A plain-language explainer of **both** classifications — how a session is placed
  into a **task category** (Analysis & Research, Document & content creation,
  Specialized workflows, …) per the Cowork usage taxonomy, and how the
  **Cowork-fit H/M/L** grade is decided via the single-surface test. Includes the
  cross-session rule and the honesty/limits section. SKILL.md links to it.

No methodology-band or value-model change. SKILL.md stays under 20,000 chars with
a ≥2,000 buffer; description 960.

---

## Cowork ROI Report — v32

Category assignment now follows the **Cowork usage taxonomy table**, plus Cowork-fit
clarity and several table/heatmap cleanups.

### Category choice is table-driven (`scripts/classify.py`)
Categories are now chosen from the taxonomy's Description/Examples, not the file type:
- **Analysis & Research** is assigned only from goal text describing analytical work
  (synthesizing findings, comparing options, briefings from multiple sources) — **not
  from a spreadsheet extension**. A built **spreadsheet/tracker is now Document &
  content creation** ("creating… organizing files"), where it belongs.
- Fixed a false-positive: the bare keyword **"roi"** no longer forces Analysis (it hit
  every "ROI report / ROI member" goal). Genuine ROI *analysis* still matches.
- Net on the sample window: the two trackers move Analysis → Document, "Install ROI
  member skill" → Specialized, and **Analysis & Research is empty** (correct — none of
  these were analytical work). Totals drop accordingly — more honest, less inflated.

### Cowork-fit clarity (`scripts/compute.py`, `build_report.py`)
- **"Cowork platform op" (unclear) renamed to "Managing Cowork"** with a plain-English
  meaning: *a Cowork admin task — installing, sharing or scheduling a skill or prompt;
  only Cowork can, but it operates the tool rather than producing business work.*
- **Every H/M/L dot now has a project-specific hover reason** (e.g. "This spans Outlook
  + Excel — no single Copilot works across apps"), not a generic label.
- The summary legend spells out H/M/L in color inline.

### Table / heatmap cleanups
- **JTBD removed** from the projects table (added noise, not value).
- **H/M/L badge removed from the Roles × projects heatmap** (it belongs in the projects
  table).
- The **Roles × projects heatmap now replaces the flat role list** directly under "Roles
  Cowork assembled for me" — one place for roles.

SKILL.md stays under 20,000 chars with a ≥2,000 buffer; description 960.

---

## Cowork ROI Report — v31

Refinements to the "Your projects" table and Cowork-fit, plus JTBD restored.

### Cowork-fit badge → colored circle
- The badge is now a simple **colored circle with just the letter**: **H green ·
  M yellow · L red**. No inline label text (the wording "Cowork-platform op" was
  unclear); the meaning is on hover and in the glossary.
- Clearer language everywhere: **M = "Cowork-specific setup/config"** (install,
  share or schedule a skill/prompt) instead of "Cowork-platform op".

### "Your projects" table — leaner
- **Roles column removed** — roles are covered later (Roles list + heatmap), so
  they no longer clutter this table.
- **JTBD restored** — each project row now shows a **"JTBD: …" sub-line** (the
  stakeholder job the work served). This brings back the Job-to-be-Done that was
  dropped when the Process ▸ JTBD ▸ Project ladder was collapsed in v29.
- **Group-by dropdown trimmed to Process / Category** — removed **Pillar**,
  **Cowork-fit**, and **None (flat)** options (Cowork-fit is shown per-row now,
  so grouping by it is redundant).

### Layout
- **Roles × projects heatmap** is now a **visible sub-section directly under
  "Roles Cowork assembled for me"** (no longer a separate collapsed toggle) —
  the connection to the roles list is explicit.
- **"Value at a glance" pillar table removed entirely** (pillar dropped from the
  report per request). Only the Deliverables table remains behind a toggle.

No methodology, band, or grade-logic change. SKILL.md stays under 20,000 chars
with a ≥2,000 buffer; description 960.

---

## Cowork ROI Report — v30

**Bug fix + declutter** for the single "Your projects" table introduced in v29.

### Bug fixed — empty projects table
v29 rendered the table client-side from `DATA.goals`, but the embedded payload
only carried `{rate, hours}` — so `DATA.goals` was empty and the table came up
blank. Fix:
- `compute`/`build_report` now embed a **slim `goals` array** in the client payload.
- Rows are also **rendered server-side** at build time, so the table is populated
  even before any JavaScript runs (never blank). Client JS re-renders only on
  regroup or hourly-rate change.

### Cleaner layout
- **Group-by control is now a single dropdown** (Process default / Category /
  Pillar / Cowork-fit / None) — replaces the row of five buttons.
- **Cowork-fit filter chips removed** — Cowork-fit is still a grouping option and
  every row still carries its H/M/L badge; the separate filter row is gone.
- **"Value at a glance" pillar table is hidden** behind a show/hide toggle (was
  a large always-on block above the projects).
- **Category column dropped** from the table — category is available by grouping,
  so the default list is lighter (Project · Cowork-fit · Roles · Hours · Value).

Net: fewer always-on blocks and controls; the first read is one headline area +
one clean, populated project list. Deep-dives (Value-at-a-glance, heatmap,
deliverables) are all one click away.

SKILL.md stays under the 20,000-char limit with a ≥2,000 buffer; description 960.

---

## Cowork ROI Report — v29

Report-layout overhaul to **stop repeating the project list**. Same data,
methodology and grades as v28 — this is presentation only.

### Problem
The same ~8 projects were enumerated in four places (Work by business process,
Projects by category, the Roles × projects heatmap, and Deliverables & skills),
forcing a lot of scrolling and re-reading of the same list.

### Fix — one canonical "Your projects" table (`scripts/build_report.py`)
- A single **"Your projects" table** is now the only place projects are listed,
  positioned prominently under the KPI cards.
- **Group by** switch — **Process** (default), **Category**, **Pillar**,
  **Cowork-fit**, or **None** — regroups the rows **in place** (group header rows
  show sessions · hours · % of total). No more separate per-dimension sections.
- **Cowork-fit filter chips** (All / H / M / L) filter the same table.
- Columns: Project (+ process sub-line) · Cowork-fit badge · Category tags ·
  Roles · Hours · Value. Value recomputes live from the hourly-rate control.
- Rendered client-side from `DATA.goals` (already embedded); regroup/filter/rate
  changes re-render without adding anything to the page.

### Collapsed deep-dives
- The **Roles × projects heatmap** and **Deliverables & skills** table are now
  behind **show/hide toggles** (`<details>`), collapsed by default — the first
  read is short; the detail is one click away.

### Removed from the default view
- The Process ▸ JTBD ▸ Project accordion and the Projects-by-category fold
  (their content is fully covered by grouping the one table).

Net: ~6 project-listing blocks → **1 table + 2 collapsed panels**.
SKILL.md stays under the 20,000-char limit with a ≥2,000 buffer; description 960.

---

## Cowork ROI Report — v28

Adds a **Cowork-fit H/M/L grade** to every project, answering: *did this project
need Cowork, or could a single surface-specific Copilot have done it?*

### New: the "single-surface test" (`scripts/compute.py`)
Deterministic scorer (`cowork_fit()`) — no LLM. Guiding question: **could one
in-app / surface-specific Copilot have done this end-to-end?**
- **H — Cowork-worthy**: it builds/packages a skill or app, runs a cross-system
  automation/connector/browser task, synthesizes >5 sources, **or spans ≥2
  Copilot surfaces** (e.g. Outlook + Excel) — none of which a single Copilot does.
- **M — Cowork-platform op**: install / share / schedule a skill or prompt.
- **L — Copilot-sufficient**: one surface-specific Copilot (Excel, Word,
  PowerPoint, Outlook, Teams, or chat) could have done it — the surface is named.
- "Produced an artifact" is deliberately **weak** (Copilot agent mode saves files);
  the methodology time-band is **not** used. Out-of-domain specialized roles
  (DevOps, SWE, Frontend, Architect vs a BVA/analytics job) are a supporting signal.
- Emits `cowork_fit` per goal and a `cowork_fit_summary` (H/M/L counts).

### New: badges + portfolio view (`scripts/build_report.py`)
- Every project row in **Projects by category** and the **Projects × Roles heatmap**
  carries an H/M/L badge with a "Could run in … Copilot" / "Cowork-only" /
  "Needs A + B Copilot" tooltip.
- A **portfolio summary** heads the section (e.g. *3 needed Cowork · 3 platform ops
  · 2 single-Copilot*). New glossary entry documents the test and its limits.

### Honest limitation
Grades are **heuristic and directional** — inferred from harvested artifacts,
systems and roles, not from measured tool telemetry (present for only some
sessions). Labeled as such in the report.

### Housekeeping
- SKILL.md documents the feature; kept at 18,000 chars (2,000-char buffer under the
  20,000 plug-in-validation limit); `description` unchanged at 960 (both gates pass).

---

## Cowork ROI Report — v27

Adds a **Projects × Roles heatmap** to the report. No change to the methodology,
the 8 categories, the bands, or the value model — this is an added visualization.

### New: Projects × Roles heatmap (`scripts/build_report.py`, `scripts/compute.py`)
- A heatmap section renders directly **after the "Roles Cowork assembled for me"** list.
- **Projects on the Y axis (rows)** — sorted by hours, and the rows area is **scrollable**
  (`max-height`, sticky header + sticky first column) so it scales to **dozens of projects**
  over a long window without breaking the layout.
- **Roles on the X axis (columns)**, capped at **top 7 by hours**; any remaining roles fold
  into a single **Other** column. (`RP_TOP_N = 7` in `build_report.py` — change it in one place.)
- **Each cell** = that role's expert-equivalent hours in that project. A project's hours are
  split **evenly across the roles it needed** (same rule as the Roles list), so the column
  footers ("Role total") reconcile exactly with the Roles section, and the row totals ("Total")
  reconcile with each project's hours.
- Cell shade scales light→deep blue by hours; a legend and an "Other = …" note sit below.
- **`compute.py`** now emits `professional_roles` on each goal object so the renderer has the
  per-project roles it needs (previously only the rolled-up totals were in the payload).

### Housekeeping
- `import collections` added to `build_report.py` (used by the heatmap aggregation).
- SKILL.md documents the new section; kept at **17,991 chars** — a ≥2,000-char buffer under the
  20,000 limit — and `description` stays 960 chars (both plug-in-validation gates still pass).

---

## Cowork ROI Report — v26

**Fix: skill validation failure when sharing as a plug-in.** No change to runtime
behavior, the pipeline, the 8 categories, the bands, or the report output — v26 is
purely a packaging/size fix so the skill passes plug-in validation.

### Reported issue
Sharing `cowork-roi-report` as a plug-in failed validation on two limits:
- **`description` frontmatter field > 1024 chars** (was 1364 — over by 340).
- **SKILL.md total > 20000 chars** (was ~28462 — over by ~8462).

### Fix
- **Trimmed the frontmatter `description` to 960 chars** (≤1024). Kept every
  trigger phrase and the "Do NOT use" disambiguation that drive routing; removed
  the verbose feature inventory.
- **Reduced SKILL.md to ~17992 chars — a deliberate ≥2000-char buffer under the
  20000 limit**, so future edits don't immediately re-breach:
  - Extracted the deep **methodology bands table + two-clock formulas** into
    `references/methodology.md` (SKILL.md keeps a short summary + pointer).
  - Extracted the **extension/category heuristics table + raw-harvest JSON schema**
    into `references/classification-reference.md` (SKILL.md keeps the key rules).
  - Compressed rationale-heavy prose in the Harvest, Classify, Skills-tagging and
    Taxonomy-memory sections without dropping any operational step.
- **No script, no logic, no output change.** `classify.py` / `compute.py` /
  `build_report.py` are byte-for-byte the v25 versions (including the v25 classifier
  enrichment and the primary-output gate for `document`). The full pipeline was
  re-run end-to-end after the trim to confirm nothing broke.

### Validation (post-fix)
- SKILL.md total: **17,992 / 20,000** (buffer 2,008) — PASS
- `description`:  **960 / 1,024** (buffer 64) — PASS
- All four `references/*.md` links resolve.

---

## Cowork ROI Report — v25

Two areas: a tighter classifier and a cleaner, more legible report layout.
No change to the 8 methodology categories, the research-anchored bands, or the
value model — v25 is precision + presentation, not a new number.

### Classifier (`scripts/classify.py`)
- **Goal-text vocabulary enriched from the Cowork usage taxonomy table**
  (the Description/Examples column). Each signal set now mirrors one row of that
  table, so a session's *goal phrasing* can place it even when no telltale file
  extension was saved.
- **Three categories are now detectable from goal text that previously required a
  matching artifact:** `document` (drafting docs/decks, editing text, creating
  visuals, organizing files in OneDrive/SharePoint), `comms` (Teams messages,
  communication rules), and `special` (workflow automation, recurring/scheduled
  prompts, task lists, multi-step M365 flows, connectors: Dynamics 365, ADO
  Boards, Power BI, Fabric, ServiceNow, Salesforce, SAP).
- **`analysis`, `code`, `email`, `meeting` signal sets extended** with the
  table's wording (e.g. briefings from multiple sources; code review / script
  generation; inbox triage / thread summaries; action-item extraction).
- **Primary-output gate for `document`.** A session is tagged
  *Document & content creation* ONLY when it actually PRODUCED a genuine content
  artifact as output — a PowerPoint, Word/PDF doc, Loop/OneNote page, or an image
  (`CONTENT_EXT`). An incidental `.md`/`.txt` file (execution log, README, notes)
  no longer, by itself, puts a session in the Document bucket, and a chat-only
  session with no saved deliverable can't be Document either. Net effect: fewer,
  truer Document entries; the headline becomes slightly more conservative.
- The 8 categories, the extension→category map, the 2-categories-per-session cap,
  and the PRIORITY tie-break are all **unchanged**. This is deterministic — no LLM
  in the category path — so results stay reproducible.

### Report layout (`scripts/build_report.py`)
- **"Work by business process" promoted to the primary lens** and moved directly
  under the KPI cards. Quiet styling (thin left accent, small-caps kicker) — it
  leads by position, not by loud chrome.
- **Per-process drill affordance simplified** to a single quiet caret; the whole
  row is the click target. Removed the per-row "Drill in" pills, the dashed cue
  banner, the solid "Primary lens" badge, and the per-row "PROCESS" tag.
- **New "Projects by category" section** — a collapsible bucket per methodology
  category, listing the projects folded into it (a project appears in up to two
  buckets, matching the 2-category cap). Header carries the authoritative
  per-category hours/value.
- **Two bar charts removed.** The "by task category" bar chart is replaced by the
  category fold above; the "Roles" bar chart is replaced by a clean inline list
  (name · hours · value). Reduces visual density.

---

## CHANGELOG — v24

### Per-user taxonomy memory (privacy fix) — stop cross-user leakage

**Fatal flaw fixed:** in v23 the taxonomy memory could leak one user's personal jobs/processes into
another user. A teammate who ran the shared package got back *exactly* the original user's processes
and JTBDs instead of their own. Root cause: personal data was committed **inside the shippable skill
folder**, and there was no per-user identity guard.

### What leaked (now removed)
- The member skill's bundled `cowork-process-registry.seed.json` shipped with real process names + JTBDs,
  and first-run copied it into the next user's memory. **The seed is deleted — no seed ships; first run
  starts with no memory.**
- Both skills' `scripts/process_overrides.json` shipped **populated** with real session→process mappings
  (docs falsely claimed "ships empty"). `classify.py` read it directly. **Reset to `{}`.**
- The aggregated skill wrote personal overrides **into the report skill's `scripts/` folder**. **Now
  writes to `working/` only.**

### The fix
- **Owner-scoped, per-user registry.** The registry is now
  `/mnt/user-config/.claude/cowork-process-registry.<userkey>.json`, where `<userkey>` derives from the
  invoking user's email, and it carries an `owner` field. It lives on the user's own mount (syncs to
  **their** OneDrive `Documents/Cowork/` folder), so the memory is in the user's Cowork folder and is
  theirs alone.
- **Identity guard.** `reconcile_taxonomy.py` **ignores any registry whose `owner` isn't the invoking
  user** (leaked / inherited / unstamped) and starts empty — so a first run mints processes from the
  user's OWN sessions, and a leaked file can never contaminate another user. New `--owner` arg (falls
  back to the harvested `meta.email`); refuses to write an unscoped registry if no owner is resolvable.
- **Per-run scratch out of the bundle.** `reconcile_taxonomy.py` writes overrides to
  `working/process_overrides.json` and `classify.py` reads them via `--overrides` (default `working/…`).
  Personal per-run data can never again land in a shippable `scripts/` folder.
- **Packaging guardrail** added to all three skills' `SKILL.md`: never bundle the registry, any
  `cowork-process-registry*.json`, or a populated `process_overrides.json`; overrides ship as `{}`.

### Migration
Existing users' memory is preserved: the old unscoped `cowork-process-registry.json` is copied to the
owner-scoped filename with an `owner` stamp on first run under v24 (do this before the first run, since
the guard ignores the unstamped file).

### What's unchanged
The v23 process-anchored taxonomy (Process ▸ JTBD ▸ Project), the two-clock methodology, KPIs, pillars,
categories, roles, deliverables/skills, activity heatmap, glossary, live rate, and Download-PDF — all as
before. Numbers still come only from `compute.py`. Alignment logic (project/process match, novel mint)
is byte-for-byte the same; only the registry location, the owner guard, and the overrides path changed.

---

## CHANGELOG — v23

### Process-anchored taxonomy + durable taxonomy memory

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

---

## CHANGELOG — v22

### Removed Copilot-credits (no credits question, no `/cost` sweep)

This version drops the live Copilot-credits feature that v21 added. The report stays the **full, detailed
personal impact report** — project names, deliverables, the Job ▸ Process ▸ JTBD work-by-process view, roles,
and skills are all shown, exactly as before. The only change is that credits are gone.

### What's removed
- **The credits question.** The opening `AskUserQuestion` is back to **two** questions — **Period**
  (7 / 15 / 30 days) and **Delivery** (run once / run + automate + email). The v21 "Live cost (Copilot
  Credits)" question is gone.
- **The `/cost` browser sweep (old step 3b).** The skill no longer drives the browser to read
  "N credits used for this task so far", no longer writes the credits ledger, and never prompts you to
  paste/screenshot `/cost`.
- **No credits / cost line in the report.** With no live reading, the **Credits · cost** column and the
  ROI banner stay hidden (the renderer already auto-hides them when there's no cost data). Nothing is
  fabricated.

### What's unchanged (still the full detailed report)
- Speed multiplier + professional-services value, KPIs, Value-at-a-glance pillar table.
- Where-the-time-went by task category, Roles Cowork assembled, Work by business process
  (Job ▸ Process ▸ JTBD ▸ projects, and the By-Pillar view), Deliverables & the skills behind them,
  activity heatmap, methodology glossary with clickable sources.
- The artifact-scaled two-clock methodology (v4 bands), the Cowork-app allow-list harvest across all three
  `Documents/Cowork/` layouts, version-base dedup, and the classifier/compute logic.

- `SKILL.md` — step 1 back to two questions; the step-3b `/cost` sweep section removed; no credits/cost
  references in the workflow, scheduling, or email steps.
- `scripts/build_report.py` — unchanged renderer (the dormant `--anonymize` team-safe mode remains available
  but is **not** used by this personal skill).

---

## CHANGELOG — v21

### Opening questions now ask about the live cost sweep

The skill's first `AskUserQuestion` is now **three** questions instead of two:
1. **Period** — 7 / 15 / 30 days (unchanged).
2. **Live cost (Copilot Credits)** — *new* — "Include the live `/cost` credit sweep so the report shows
   your real per-session cost and ROI?" Options: **Skip it (faster)** *(default)* or **Yes — read my real
   credits live**. Only when the user picks **Yes** does the agent run the step-3b `/cost` browser sweep
   before rendering (it's opt-in because it's slower and drives the browser). When skipped, the report shows
   research-anchored Time Saved + Value and the **Credits · cost** column auto-hides.
3. **Delivery** — run once / run + automate + email (the old Q2).

Guardrail added: never run the `/cost` sweep unless Q2 = Yes; on a headless scheduled run, reuse the ledger
or skip the cost column, never block.

- `SKILL.md` — step 1 rewritten to three questions; opt-in gate documented.

### Report redesign — section order, collapsible process views, deliverables skill filter

### New section order (after *Value at a glance*)
1. **Where the time went — by task category**
2. **Roles Cowork assembled for me**
3. **Work by business process**
4. **Deliverables & the skills behind them**

(Previously *Work by business process* led the four; it now sits third, directly before *Deliverables*.)

### Work by business process — collapsible groups
- **By Job-to-be-Done:** each **Job** is now a collapsible accordion showing only the job title, project
  count, and total hours; an **expand arrow** reveals the Processes ▸ JTBDs ▸ projects beneath it (the full
  detail shown previously).
- **By Business Value Pillar:** each **Pillar** is now its own collapsible accordion (pillar name + project
  count + total hours + arrow); expanding shows the project table for that pillar.
- Added **Expand all / Collapse all** controls next to the view toggle. Groups start collapsed for a clean
  overview.

### Deliverables & the skills behind them — filter by skill
- Added a **skill-filter chip bar** above the table (rendered when ≥2 distinct skills appear). Each chip shows
  a skill and its count; clicking filters the table to deliverables that used that skill. An **All** chip
  resets. A friendly "no deliverables match" line shows when a filter empties the table.
- Each row carries a `data-skills` attribute; filtering is pure client-side JS (no rebuild needed).

- `scripts/build_report.py` — section reorder; `<details>` accordions for both process views
  (`.wbp-acc`), `wbpExpand()` expand/collapse-all, per-pillar grouping (`pillar_acc_html` replaces the flat
  `pillar_rows` table), deliverables `dl-filter` chips + `dlFilter()` JS, supporting CSS.

### Unchanged
- v18–v20 methodology: RUNS × BAND value model, Cowork-app allow-list harvest (all three `Documents/Cowork/`
  layouts, never `Apps/`), version-base dedup, the real-credit `/cost` ledger + ROI banner (now gated behind
  the Q2 opt-in), classifier and compute logic.

---

## CHANGELOG — v20

### Value model finalized: RUNS × BAND (anchored to the Cowork Time-Savings methodology deck)

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

### Carried forward from v18–v19
- **Real per-session cost** — the `/cost` browser sweep reads Copilot Credits live and logs them; the report
  shows a **Credits · cost** column (credits × $0.01 list) and an **ROI banner** (value ÷ real cost) in both
  the JTBD and pillar views.
- **Cowork-app allow-list harvest** — all three `Documents/Cowork/` layouts, scoped by the Cowork app id,
  never `Apps/…` (Scout excluded).
- **Version-base dedup** — iterative versions of the same artifact (v6/v11/v17, report-v1/v2) collapse to one
  distinct deliverable.

### Files
- `scripts/compute.py` — `session_expert = Σ runs × band`; runs from `s["runs"]` (fallback 1 run/task).
- `scripts/mine_session.py` — emits `runs` from the write/test/debug & research tool-chains.
- `scripts/classify.py` — passes `runs` through.
- `SKILL.md` — step 4 documents runs × band + the run-counting rule.

---

## CHANGELOG — v19

### Real per-session cost: the `/cost` browser sweep + Credits·cost column

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

### Files touched
- `SKILL.md` — new **step 3b** (the `/cost` browser sweep + ledger + fallbacks).
- `scripts/compute.py` — `load_credits_lookup()`; attaches `credits` and `cost_usd` (credits × $0.01) per session.
- `scripts/build_report.py` — **"Credits · cost"** column (credits with the dollar equivalent beneath).

### Unchanged
- v18 harvest (Cowork-app allow-list, all three `Documents/Cowork/` layouts, never `Apps/`).
- Methodology bands, classifier, value model.

### Display additions (cost surfaced everywhere)
- **Per-project cost in the Job-to-be-Done view** — each project in the Job ▸ Process ▸ JTBD tree now shows its real `credits · $cost` next to hours/value/speed (the Pillar view already had the column).
- **ROI banner** — real Copilot-credit cost vs research-anchored value, with the return multiple (value ÷ cost) and net %.

### Value model corrected to RUNS × BAND (methodology-deck-anchored)
- Per the Cowork Time-Savings methodology deck, every category band is **minutes saved per RUN**, with the
  activity-instance chain already summed inside it (code 56 = write+test+debug = 18min×3; doc 24 = 6.1×4).
  So the expert clock = **Σ runs × band** — no per-LOC valuation, no per-artifact authoring add-on (both
  double-count the chain). Reverted the interim LOC/authoring experiments.
- **Run counts come from the agentic tool-chains** (telemetry-grounded): code run ≈ 6 code-edits,
  analysis run ≈ 5 research-tool calls. `mine_session.py` now emits a `runs:{category:count}` field;
  `classify.py` passes it through; `compute.py` applies `Σ runs × CATS[band]`. Sessions without telemetry
  use conservative estimates, labeled as such.
- Iterative versions of the same artifact still collapse to one distinct deliverable (version-base dedup).

---

## CHANGELOG — v18

### Cowork-app allow-list harvest (Scout excluded, multi-layout)

**Problem this fixes.** Earlier versions harvested only `Documents/Cowork/sessions/<uuid>/` — the
*legacy* layout. Two failures followed:

1. **Missed real Cowork work.** The product moved to newer layouts
   (`Documents/Cowork/Tasks/<goal>-<date>/` and root `Documents/Cowork/<goal>-<date>/`), so recent
   sessions were invisible and reports under-counted (often to a single session, or zero).
2. **Risked counting non-Cowork work.** A separate product — the **M365 Copilot app running Scout** —
   writes session records under `Documents/Apps/<app-instance>/sessions/` (scheduled heartbeats,
   customer/needs monitors, executive briefings). Naively widening the harvest would have swept those
   in and inflated the numbers.

**The fix — positive allow-list, not a deny-list.**

- **Harvest all three Cowork layouts** under the resolved Cowork folder: `Tasks/<goal>-<date>/`, root
  `<goal>-<date>/`, and legacy `sessions/<uuid>/` (each with `input/` + `output/`).
- **Scope by creator app id.** Count a folder/artifact only when
  `createdBy.application.id == 6ab48b67-cd74-4ad4-81af-5932984589be` (the Cowork product app — stable
  across users and tenants). This is the single user-agnostic Cowork signal.
- **Never enumerate `Documents/Apps/…`.** Skipping that tree excludes Scout for every user with **no
  per-instance name list** to maintain. Scout records are written by the generic *Microsoft Graph* app
  (`99fa64eb-…`), so the creator-id allow-list also rejects them by construction.

**Why not detect-and-subtract Scout?** A deny-list keys on instance names like
`M - Internal Copilot App 1`, which differ per user and break on the next account. Allow-listing
Cowork-app-created artifacts generalises cleanly.

### Counting discipline for persistent task folders

- Cowork `Tasks/` folders are **persistent workspaces** that accumulate artifacts over multiple
  days/runs. Do **not** derive `exec_min` from file-timestamp spans for them (the span is days, not run
  time) — leave `exec_min` null so the modeled assisted clock applies, and prefer a measured telemetry
  `exec_min` when the Stop hook supplied one.
- **Fold supporting files** (QA screenshots/`*.png`, variant `*-7day/-60d/-sample.html`, prompts,
  READMEs, lock files) into the session's primary deliverable. Never count N screenshots as N
  deliverables.

### Unchanged

- Methodology (research-anchored category bands, two-clock speed multiplier), classifier, compute, and
  renderer are unchanged from v15–v16.
- Cost: still **not available** from the web / M365 Copilot app surfaces (the authoritative `/cost`
  figure isn't persisted to any file a hook can read there); the session-cost column auto-hides when no
  cost data exists. Tracked separately.

---

## Cowork ROI Report — v16 (real professional roles + redesigned process view)

### Roles — "what a billing firm would charge" (ported from microsoft/What-I-Did-Copilot)
- The **"Roles Cowork assembled for me"** section now shows the **exact professional roles** the work
  would have needed (Data Analyst, Management Consultant, Software Engineer, Risk & Compliance Analyst,
  …) — not the old fixed 8-archetype map.
- **Primary path:** the harvest LLM tags `professional_roles` per session ("1–2 roles a billing firm
  would charge for this work"). **Fallback:** a 16-role keyword taxonomy (`scripts/roles_taxonomy.json`)
  when none are tagged.
- `compute.py` rolls up role-hours by splitting each session's expert time across its roles; the fixed
  `ROLE` map is removed. Each role name **links** to a job-title search.

### Work-by-business-process — redesigned
- **Dropped the "Task category" column.**
- **Upfront visual:** a Job ▸ Business Process ▸ JTBD map (per-Job cards with the JTBD and hours bars).
- **Toggle:** flip the table's first column between **Business Process** and **Job-to-be-Done**.

### Carried over from v15
- Research-anchored Time Saved + Value hero; speed multiplier secondary; four value pillars; single
  self-contained skill; map-my-work folded in; auto-hiding cost column; chat-only sessions counted;
  nothing hard-coded to any individual.

---

## Cowork ROI Report — v15 (defensible, research-anchored methodology)

### Expert clock is now PURELY research-anchored
- Time Saved per session = the **sum of the cited per-task bands** (e.g. Analysis 67 + Document 24 =
  91 min typical; Conservative/Optimistic re-sum the published low/high bands).
- **REMOVED** the un-cited read-time (12 min/doc, 5/img) and authoring-time (deck 45, doc 40, …)
  heuristics from the expert clock — they were presented as "research-anchored" but were flat
  assumptions. Now every expert minute traces to a study.

### Report leads with Time Saved + Value
- Hero is now **Time Saved (hours)** + **Value ($)** — both fully research-anchored.
- The **speed multiplier is demoted to a secondary, clearly-labeled stat**; its denominator
  (hands-on time) is a modeled estimate (measured where the telemetry hook is on), so it is framed
  as directional, not a stopwatch.
- Footer + glossary corrected: no longer claim the whole figure is "research-anchored."

### Simplifications
- Per-deliverable hours = an equal share of the session's expert time (still sums back to the total).
- Per-category and role minutes come straight from the task bands.
- "Analyzed → Produced" shows source/deliverable **counts by type** (dropped the assumption-based
  ingest/analyze/author minute split).

### Carried over from v14
- Single self-contained skill; map-my-work folded in; four value pillars; auto-hiding cost column;
  chat-only sessions counted; nothing hard-coded to any individual.

---

## Cowork ROI Report — v14 (single self-contained skill)

### Packaging — installs in one step via "Add this skill"
- Repackaged from the v13 two-skill bundle into a SINGLE self-contained skill, so the standard
  attach-zip -> "Add this skill" flow installs it cleanly (one SKILL.md at the folder root,
  name: cowork-roi-report).
- map-my-work is FOLDED IN as bundled references (references/map-my-work-playbook.md +
  references/value-pillars.md) and runs INLINE at step 4b -- no separate skill install, still fully
  personalized per user.
- Added trigger phrases "generate my impact summary report" / "generate my impact report".

### Carried over from v13
- Four value pillars: Revenue Growth, Cost Reduction, Risk Mitigation, Transformation.
- Job x Pillar banding with a JTBD sub-line; process/pillar/job/jtbd derived live per user (rich override).
- Generic only -- nothing hard-coded to any individual (APQC 13 fallback).
- Skills-augmented fix (norm() preserves skills tags) + required tagging step.
- Session-cost column auto-hides when no session has cost data.
- Cost (statusLine) + telemetry (Stop hook) capture; chat-only sessions counted.

---

## Cowork ROI Report — v13 (bundle)

### Bundled & auto-invoked
- Ships **both** `cowork-roi-report` and `map-my-work` in one package. The ROI report **auto-invokes**
  `map-my-work` (step 4b) — the user never runs it separately.

### Fully portable — personalized to whoever runs it
- **Rich override handoff:** `map-my-work` returns `{process, pillar, job, jtbd}` per session;
  `process_overrides.json` carries the full tuple; `classify.py` consumes it **directly** (live).
  `pillar_css` is derived from the pillar name. Plain-string overrides still accepted (back-compat).
- **No personal data:** removed all user-specific seed taxonomy, process lists, and JTBD examples.
  `apqc_taxonomy.json` is the generic APQC 13 only — the fallback when `map-my-work` isn't present.
  `map-my-work` derives the signed-in user's own Jobs / Processes / Pillars / JTBDs from their footprint.

### Carried over from v12
- Work-by-business-process table **bands by Job × Pillar** with a JTBD sub-line per row.
- **Skills-augmented bug fixed:** `classify.py` `norm()` now preserves per-deliverable + session-level
  `skills` tags (v11 silently dropped them), so the Skills-augmented and Deliverables tables populate.
- SKILL.md step 4a makes skills-tagging a required harvest step.

---

## Cowork ROI Report — v11 changelog

Cumulative changes since v6, consolidated into the v11 package.

### Classification & business value
- **TF-IDF APQC classifier** (`classify.py` + `apqc_taxonomy.json`) replaces the hand-tuned
  keyword lexicon. Business processes are matched by cosine similarity against the APQC Process
  Classification Framework (13 categories) — handles plurals, synonyms, abbreviations.
- **Value pillar is data-driven**: each APQC category carries a `value_pillar` + `pillar_css`
  field in the taxonomy (Improved Performance / Cost Savings / Innovation / Risk Mitigation).
  No hardcoded pillar map in the renderer.

### Methodology
- Bands aligned to **Cowork_Methodology_Walkthrough 0605**: Analysis Typical 71→**67**
  (Stanford-WB basket mean), Meeting High 45→**43**, Communication High 6→**11**.

### Skills augmented (method borrowed from microsoft/What-I-Did-Copilot)
- `skills_vocabulary.json` — controlled DOMAIN_SKILLS + TECH_SKILLS vocabulary.
- Skills are tagged **per deliverable** by the in-loop agent (mirrors their gpt-4o-mini step;
  no external API). Aggregate skill-hours roll up from the per-deliverable tags.

### Report sections
- **Value-at-a-glance summary table** (Improved Performance / Cost Savings / Innovation) modeled
  on the BVM Value Ladder (lagging KPI / leading KPI / your result).
- **Work by business process** grouped by value pillar with colored section headers; neutral-gray
  process pills, teal Improved-Performance accent (no color collisions).
- **Session cost column** — shows the real `/usage` figure captured by the statusLine hook, or
  "data not available" for sessions predating cost logging.
- **Skills augmented** moved up (after "Where the time went").
- **Deliverables & the skills behind them** — per-artifact table: deliverable → skills → expert
  hours (hours sum back to session totals; chat-only sessions appear only in the skill bars).
- **Activity heatmap removed**; circular phase-breakdown removed.
- 0-task categories relabeled honestly ("authoring time · N deliverables").

### Cost capture (statusLine)
- `statusline_cost.py` taps the harness-provided `cost.total_cost_usd` on every render and writes
  a de-duplicated per-session log (`/mnt/user-config/.claude/cowork-session-costs.json`). No
  calculation; latest cumulative wins on session re-entry. Wired via `settings.json` statusLine.

### Robustness fixes
- **Cowork folder discovery**: locate `/Documents/Cowork*` dynamically (handles `Cowork 1`,
  localized names) instead of assuming a fixed path; glossary text no longer hardcodes a folder.
- SKILL.md guardrail: run each pipeline script as its own command (avoids false "Failed" markers
  from bundled schema-guessing snippets).

---

## CHANGELOG — v6: business-process stamping + session-aware categories

**Date:** 2026-06-18
**Scope:** `scripts/classify.py`, `scripts/compute.py`, `scripts/build_report.py`
**Back-compatible:** yes — input schema unchanged; one new field (`process`) is added to
classified sessions and to the report payload. Older payloads still render (process falls
back to a default).

---

### TL;DR

1. **Each session is now stamped with a business `process`** (WHAT outcome the work served:
   *Sales & Pre-Sales*, *Finance & Cost Management*, *People & Talent*, …). Labels are
   **derived dynamically per user** — no hardcoded project/person names.
2. **Task categories now reflect the WHOLE session**, not just the output file extension.
   Reading 8 reports and producing a deck is now `analysis + document`, not `document` only.
3. **The report's "Goals & leverage" section is replaced by a "Work by business process"
   table**: *Business process · Task category · Project · Assistance & multiplier*.

---

### 1. Dynamic, personalized business-process labels  (`classify.py`)

Every classified session gains a `process` string. It is resolved in this order:

1. **Universal business-function lexicon** (`PROCESS_LEXICON`) — generic, portable vocabulary
   (proposal/customer → Sales; budget/cost/usage → Finance; team contribution/performance →
   People & Talent; status deck/dashboard/report → Business Reviews & Reporting; …). Contains
   **no** project- or person-specific tokens, so it works for any user.
2. **Synthesized fallback** — if no generic function matches, a label is built from the user's
   **own goal vocabulary** (`salient_phrase()`), suffixed by the category (e.g. a user whose
   goals repeatedly mention "Helios" gets `Helios Triage Analysis`, `Helios Engineering`).
3. **Category default** (`CAT2PROCESS`) — last resort.

Personalization comes from `build_profile(meta, sessions)`, which infers the employer from the
email domain and **mines recurring terms across the user's goals** so repeated initiatives map
to a stable, personalized label. Nothing about one specific user is baked into the code.

### 2. Session-aware task categories  (`classify.py`)

`classify_session()` previously keyed **only** on output file extensions (`EXT2CAT`), so any
user who saves `.pptx`/`.docx` had every session labeled `document`. It now unions three signals:

| Signal | Source | Implies |
|--------|--------|---------|
| What was **produced** | output extensions (`EXT2CAT`) | document / analysis / code / special |
| What the work **was** | goal intent (`goal_categories()`) | analyze/synthesize/ROI/research → `analysis`; debug/script/api → `code`; "review/​build **from** \<report·data·dashboard>" → `analysis` |
| What was **analyzed** | inputs | data files (xlsx/csv/json) or ≥3 sources → `analysis` |

Results are de-duped, ordered by `PRIORITY`, and capped at the 2 highest-signal categories.

### 3. Process carried through compute  (`compute.py`)

* Each goal record now includes `"process"`.
* A new top-level **`processes`** array aggregates sessions/minutes/hours/value per process
  (for any future roll-up view). Purely additive.

### 4. Report: "Work by business process" table  (`build_report.py`)

The `📦 Goals & leverage` section is replaced by `📦 Work by business process`, a 4-column table:

| Business process | Task category | Project | Assistance & multiplier |
|---|---|---|---|
| People & Talent | Analysis & Research + Document & content creation | Synthesize FY26 team contributions deck from 8 reports | 3.2h saved · $230 · 6.4× faster |

The live hourly-rate control still recalculates the dollar column (`.g-v` + `data-hours` hooks
are preserved). The hero "Leverage:" summary note is unchanged.

---

### How to absorb this into your code (migration)

If your fork has diverged, port these self-contained pieces — there are no cross-file schema
changes beyond the additive `process` field.

**A. `scripts/classify.py`**
1. Add the block **`# ---- Business-process stamping (dynamic & personalized)`** through
   `infer_process()` (constants `PROCESS_LEXICON`, `CAT2PROCESS`, `CAT_SUFFIX`, `STOPWORDS`,
   `ACTION_VERBS` and helpers `_tokens`, `_keepers`, `salient_phrase`, `build_profile`,
   `infer_process`). Add `re` to the imports.
2. Replace `classify_session()` with the session-aware version and add the
   **`# ---- Session-aware category signals`** block (`ANALYSIS_SIGNALS`, `REVIEW_VERBS`,
   `SOURCE_PREPS`, `ANALYTICAL_OBJECTS`, `CODE_SIGNALS`, `EMAIL_SIGNALS`, `MEETING_SIGNALS`,
   `DATA_EXT`, `goal_categories()`).
3. In `main()`, build `profile = build_profile(d.get("meta", {}), sessions)` before the loop
   and add `"process": infer_process(s.get("goal",""), tasks, profile)` to each output record.

**B. `scripts/compute.py`**
1. Read `process = s.get("process","General Productivity")` in the session loop.
2. Add `"process": process` to each `goals.append({...})` record.
3. (Optional) add the `proc_count`/`proc_min` counters and the `"processes"` payload array.

**C. `scripts/build_report.py`**
1. Replace the `# ----- goals list -----` builder with the `proc_rows` builder (4 `<td>`s).
2. Swap the `Goals & leverage` section markup for the `Work by business process` table
   (with `<thead>`).
3. Add the two CSS rules: `table.tbl th{…}` and `.pill.proc{…}`.

**Pipeline (unchanged):**
```
python scripts/classify.py     --in working/cowork_raw.json      --out working/cowork_sessions.json
python scripts/compute.py      --in working/cowork_sessions.json --out working/cowork_roi_data.json
python scripts/build_report.py --data working/cowork_roi_data.json --out output/cowork-roi-report.html
```

**Tuning knobs:** reorder `PROCESS_LEXICON` to change tie-breaking between functions; edit the
keyword lists to match your org's process names; adjust `ANALYSIS_SIGNALS`/`ANALYTICAL_OBJECTS`
to change when a session counts as analysis. Everything stays deterministic.

---

## CHANGELOG — v5: artifact-scaled speed multiplier

**Date:** 2026-06-08
**Scope:** `scripts/compute.py`, `scripts/build_report.py` (input schema + report framing)

---

### TL;DR

1. **Speed multiplier is now the headline**, derived from the number of **distinct artifacts
   analyzed and produced** in each session.
2. **Value is framed as a professional-services equivalent** (expert-hours × rate).
3. **ROI / Copilot-seat-cost removed** — credit & seat consumption isn't available, so a
   ROI ratio couldn't be grounded.

---

### Why we changed it

**Problem 1 — multi-artifact sessions were undercounted.** v4 applied a *flat* per-task band
(analysis = 71 min, document = 24 min) regardless of how many sources went in or deliverables
came out. A session that synthesized **8 PDFs into a deck** scored identically to one that used
a single PDF. That erased the user's real leverage.

**Problem 2 — the ROI figure wasn't grounded.** v4's "ROI multiple = human value ÷ $30 seat cost"
implied a precision we can't support: Cowork credit/seat consumption isn't exposed, so the
denominator was a placeholder. We removed it rather than present a number we can't defend.

---

### The new model (two clocks)

| Clock | Definition |
|---|---|
| **Expert (unassisted)** | research-anchored analysis/general bands **+ 12 min per source document read** (5 min/image) **+ an authoring band per deliverable** (deck 45 · doc 40 · sheet/page/code 35 · other 30) |
| **Assisted (your time)** | `8 min + 2 min × (#inputs + #outputs)`, floor 4 min — a **modeled** estimate of hands-on time |

```
speed_multiplier            = Σ expert_min / Σ assisted_min        (rate-independent)
professional_services_value = (Σ expert_min / 60) × hourly_rate
```

The Conservative/Optimistic range re-runs the expert clock with the published floor/ceiling
analysis bands and lighter/heavier read & authoring weights.

---

### Before / after (worked example)

A session that **analyzed 8 source PDFs (+1 screenshot) and produced 2 decks**, tagged
`["analysis","document"]`:

| | v4 (flat) | **v5 (artifact-scaled)** |
|---|---|---|
| Expert-equivalent effort | 1.6 h | **~4.4 h** |
| Session speed multiplier | — (not computed) | **~8.7×** |
| Reading 8 sources counted? | ❌ no | ✅ yes (8 × 12 min) |
| Authoring 2 decks counted? | partially (1 band) | ✅ yes (2 × 45 min) |

At the report level the headline shifts from a single ROI multiple to a **speed multiplier** plus a
**professional-services-equivalent value**, and multi-source synthesis sessions regain the leverage the
flat model erased. The multiplier holds steady across window lengths because it no longer depends on a
prorated seat cost. (Actual figures depend entirely on each user's own session history — see
`examples/sample-report.html` for a synthetic run.)

---

### File-level changes

### `scripts/compute.py`
- **Input schema:** sessions now read `inputs[]` and `outputs[]` (each `{name, ext}`) instead of a
  single `artifacts[]`. (`tasks[]` category keys unchanged.)
- **New:** `session_expert()` computes the expert clock at typical/low/high band settings; per-session
  assisted clock; per-session and overall **speed multiplier**.
- **New payload keys:** `value` (hours, professional-services value, speed low/typical/high) and
  `leverage`; `goals[]` now carry `speed_x` and `exec_min`.
- **Removed:** the `roi` block and all seat-cost math (`seat_cost_month` retained as `0` for
  backward compatibility only).
- **Constants** (tunable at the top of the file): `READ_DOC=12`, `READ_IMG=5`, `AUTHOR` map,
  `ASSIST_FIXED=8`, `ASSIST_PER_ART=2`.

### `scripts/build_report.py`
- **Hero** now shows the **speed multiplier** (conservative/typical/optimistic) and the
  **professional-services-equivalent** value, instead of the ROI multiple vs. seat cost.
- **KPIs:** added "Speed multiplier" and "Hands-on hours (est.)"; "Hours saved" relabeled
  "Expert-equiv hours".
- **Glossary:** replaced the "Copilot seat cost" and "ROI multiple" terms with
  "Professional-services value", "Expert clock", "Assisted clock", "Speed multiplier"; the
  calc panel now documents the two-clock model.
- **JS:** removed the ROI recalculation (`roiMult` / `.roi-x`); the live rate control still
  recalculates every dollar figure, and the multiplier is rate-independent.
- Reworded the leverage note and per-goal tooltip from "measured" to "estimated/modeled" to
  reflect that the assisted clock is an assumption, not telemetry.

---

### v5.1 — "Analyzed → Produced" replaces the collaboration donut

The old **collaboration-style donut** was inherited from GitHub Copilot, where it's derived from
**transcript** modes (building vs. course-correcting vs. reviewing). Cowork has no transcript — only
artifacts — so the donut was just the 8 task categories re-bucketed into 4 coarser labels: redundant
with the category breakdown, and it collapsed to ~2 slices.

It's replaced by **Analyzed → Produced**, a genuinely different (and fully measured) lens: the
**inputs you fed in** (by type) vs. the **deliverables produced** (by type), plus the ingest-vs-author
time split and a "sources distilled per deliverable" ratio. This maps directly to the two clocks
(read-time vs. author-time) and surfaces the high-leverage "many-in, few-out" synthesis shape.

- `compute.py`: new `io` payload block — `inputs_total`, `outputs_total`, `ingest/author hours`,
  `per_deliverable`, and `inputs_by_type` / `outputs_by_type` tallies (friendly labels via `TYPE_LABEL`).
- `build_report.py`: the donut SVG + intent legend are gone; the slot now renders the facing
  Analyzed/Produced bars. **Skills augmented** (roles) is retained — it re-frames the categories as
  "the team you'd have hired", which earns its place as narrative for a finance audience.

### Migration

Re-harvest sessions with the new `inputs`/`outputs` arrays to get the artifact-scaled multiplier
**and** the Analyzed → Produced breakdown. Old payloads (single `artifacts[]`) still run but won't
reflect artifact volume or the I/O split.

### Honest caveat to keep

The **assisted clock is modeled**, not measured. The multiplier is **directional**. The only way
to tighten it is to capture real hands-on time per session.

