# Classification Methodology — Cowork ROI Report

This document explains the two classifications the report applies to every Cowork
session:

1. **Task category** — *what kind of work was it?* (Analysis & Research,
   Document & content creation, Specialized workflows, …)
2. **Cowork-fit (High / Medium / Low)** — *did the work actually need Cowork, or
   could a single in-app Copilot have done it?*

The two are built differently, and it matters:

- **Task category is deterministic** — a mechanical map from artifacts and goal
  keywords to categories. Reproducible; the same session always lands the same way.
- **Cowork-fit is a two-layer hybrid** — a deterministic rule produces a
  reproducible *baseline*, and an **LLM review** can confirm or adjust each grade,
  because "could another Copilot have done it" is a capability judgment, not a fact
  a keyword can settle. Each grade is flagged **rule-based** or **AI-reviewed**.

---

## Part 1 — Task category (deterministic)

Categories follow the **Cowork usage taxonomy** (the product's Description/Examples
definitions). The category describes *the nature of the work*, not just the file
type produced. These are the report's eight labels:

| Category | What it means |
|---|---|
| **Analysis & Research** | Searching org data, synthesizing findings, comparing options, explaining concepts, preparing briefings from multiple sources. |
| **Document & content creation** | Drafting docs/presentations, editing text, creating visuals, organizing files in OneDrive/SharePoint. |
| **Email workflows** | Drafting/replying to emails, summarizing threads, triaging the inbox, managing mail rules — centered on **Outlook**. |
| **Communication workflows** | The same ideas as Email, but centered on **Microsoft Teams**: synthesizing, posting, triaging and managing across Teams **messages and channels** (chats, channel posts, replies, announcements, mentions). |
| **Meeting workflows** | Preparing meeting briefings, recapping transcripts, extracting action items, calendar lookups. |
| **Specialized workflows** | Scheduling calendar events, managing task lists, multi-step M365 workflows, recurring prompts, and connectors (Dynamics 365, ADO Boards, Power BI, Fabric, ServiceNow, Salesforce, SAP). |
| **Write or debug code** | Writing/debugging code, code review, script generation, code analysis. |
| **General assistance / Other** | Product guidance, discovering Copilot capabilities, troubleshooting, learning new skills, casual Q&A. |

**Email vs Communication:** they are deliberately separate. If the synthesis,
posting, triaging or managing happens in **email (Outlook)**, it is **Email
workflows**; if the same kind of work happens in **Teams messages and channels**,
it is **Communication workflows**.

### How a session is assigned

1. **Output file extensions → a category** (a starting hint):
   - `.docx / .pdf / .pptx / images` → **Document & content creation**
   - `.xlsx / .csv` → **Document & content creation** *(a built spreadsheet is
     created content — "creating visuals, organizing files" — not analysis)*
   - `.py / .ps1 / .html / .js / .sql` → **Write or debug code**
   - `.zip / skill package` → **Specialized workflows**

2. **Goal-text signals → a category** (the decisive layer, mirroring the taxonomy
   Description/Examples):
   - **Analysis & Research** is assigned **only** when the goal describes
     analytical work — *synthesize, compare, evaluate, research, benchmark, brief,
     "from multiple sources."* Never from a file type alone.
   - **Specialized workflows** — *automate, connector, recurring/scheduled prompt,
     multi-step, task list,* or a named connector.
   - **Document & content creation** — *draft a doc/deck, edit text, create a
     visual, organize files in OneDrive/SharePoint.*
   - **Email workflows** — *email, inbox, reply, triage, thread, mail rule (Outlook).*
   - **Communication workflows** — *Teams message/chat/channel, post to a channel,
     summarize/triage a channel, announcement, @mention (Teams).*
   - **Meeting**, **Write or debug code**, **General** — matched from the same wording.

3. **Counting discipline:**
   - Cap **~2 categories per session** (the two most significant).
   - A fixed priority breaks ties so the primary category is stable:
     `code → analysis → special → document → comms → meeting → email → general`.
   - Multi-source synthesis (**> 5 inputs**) adds Analysis.
   - A category with **no** matching work is reported as **zero** — the report
     never force-fits a session into a high-value bucket.

### The Document primary-output gate

A session is tagged **Document & content creation** only if it actually
**produced** a genuine content artifact (PowerPoint, Word/PDF, Loop/OneNote,
image, or spreadsheet). An incidental `.md`/`.txt` log or a chat-only session does
not count — this keeps the category honest.

---

## Part 2 — Cowork-fit (High / Medium / Low) — a hybrid

**The guiding question — the "single-surface test":**

> *Could a single surface-specific / in-app Copilot (Excel, Word, PowerPoint,
> Outlook, Teams, or Copilot chat) have done this end-to-end?*

If **yes**, the work didn't need Cowork. Cowork's distinct value is the work no
single in-app Copilot can do: building, automating, or **orchestrating across apps**.

**Evidence-first.** The test is applied to *what Cowork actually did* — the **workflow
evidence** (the apps its actions touched, the sources it reviewed, and its outputs),
not merely the file it saved. An Excel-only *output* does **not** establish an
Excel-only *workflow*. The grader unions the **verified** apps from the action trace
(`apps_accessed`) with the apps **inferred** from outputs and related sessions; a
cross-app workflow (e.g. Outlook + Excel) is **H**. A missing action trace does **not**
by itself force abstention — the grader still infers the fit from the outputs, goal and
related sessions. Only when there is **no basis at all** (a saved artifact of an
unrecognized type, with no build / automation / multi-file / cross-app signal and no
trace) is the assessment left as **"? — Insufficient evidence"** rather than guessed.
This is deliberately **rare**.

| Grade | Colour | Meaning |
|---|---|---|
| **H — High** | Green | Cowork was genuinely needed: **≥2 apps in play**, or the output shows **code generation, automation/workflow, multi-document synthesis, or multiple different output formats**. Cross-app confirmed by the action trace is *verified*. |
| **M — Moderate** | Yellow | Moderate fit — a single-surface task that still means **multi-format input** (reading two or more formats) or juggling a **large number of files**, or a lightweight Cowork-platform op. |
| **L — Low** | Red | One in-app Copilot could have done it end-to-end — a single app/output, or a purely conversational task. |
| **? — Insufficient evidence** | Grey | **Rare.** Only when there is no basis at all — an unrecognized output type with no code/automation/multi-format/cross-app signal and no action trace. A missing trace alone does not trigger this; the grader still infers from outputs/goal/related sessions. |

### Layer 1 — the deterministic rule (baseline)

The rule walks a strict **hierarchy**, taking the first grade that matches:

1. **≥2 apps in play → High.** Count the apps: those the actions *touched* (verified,
   e.g. Outlook + Excel) unioned with those *inferred* from outputs, goal (a
   "sharing"/distribution goal implies Outlook), and related sessions. Two or more → High
   immediately.
2. **Output signals → High.** Otherwise, if the work involved **code generation**, an
   **automation / workflow** (inbox triage, channel scan, sweep, connector, recurring
   run, Specialized workflow), **multi-document synthesis** (several docs across ≥2
   formats, or >5 sources), or **multiple different output formats** → High.
   *An automation-style process is never graded below High.*
3. **Purely conversational → Low.** No output and no other app needed — Copilot chat
   would have covered it.
4. **Moderate multi-format / volume → Moderate.** A single-surface task that still reads
   **two or more input formats**, juggles a **large number of files**, or is a
   lightweight **Cowork-platform op** (install / share / schedule a skill or prompt).
5. **Single app a lone Copilot could do → Low.** Exactly one surface/output.
6. **Truly no signal → "?"** (rare) — see the grade table above.

**Cross-session orchestration.** A deliverable built across two sessions — e.g.
identify the emails in one session, build the Excel tracker in another — unions the
surfaces from every contributing session, so it reads as **cross-surface (H)** in
both. This is why "Build the value-story tracker" grades High even though that one
session only wrote an `.xlsx`.

### Layer 2 — the LLM review (judgment)

The rule above is a fast, reproducible **proxy** for the real question. But "could
another Copilot have done this?" is a *capability judgment*, and a keyword rule
cannot settle it with certainty. So the agent reviews each project against the
single-surface test and may **confirm or adjust** the rule grade:

- When the reviewed grade **matches** the rule, it is flagged **AI-confirmed**.
- When it **differs**, the reviewed grade is shown and flagged **AI-reviewed**, with
  the rule's grade preserved for transparency (e.g. *"M — AI-reviewed [rule said
  L]"*).
- When no review is recorded, the **rule grade stands**, flagged **rule-based**.

**Guardrail on downgrades.** The review may not quietly overturn action-grounded
evidence. It **cannot** downgrade a **verified cross-app** workflow to **L**, nor an
**automation** run below **M**, unless it explicitly **resolves the conflicting
evidence** (records a `conflict` / `resolves_evidence` note). A downgrade that fails
this test is rejected: the rule grade is kept and the attempt is flagged
**AI-review-rejected**, with the proposed grade and reason preserved for transparency.

Every H/M/L dot in the report is hoverable and shows its **project-specific reason
and its method** (rule-based vs AI-reviewed), so you can always see *why* a grade
was given and *how* it was decided.

*Example.* A chat-only session that redesigns a chart's visual layout from a
screenshot is mechanically **L** (one surface = PowerPoint). But nuanced,
iterative visual-design isn't a clean single-Copilot task, so AI review may adjust
it to **M** — shown as "M · AI-reviewed [rule said L]."

---

## Honesty and limits

- **Task category is genuinely deterministic and reproducible** — a mechanical map
  from file types and goal keywords to the eight categories. No LLM decides a
  category.
- **Cowork-fit is a hybrid, and its judgment layer is not infallible.** The rule
  baseline is reproducible; the LLM review is *judgment*, explicitly labeled as
  such per project. It is directional, not a definitive verdict on what another
  Copilot can or cannot do — you can disagree with any grade, and the tooltip shows
  the reasoning so you can.
- **Heuristic inputs.** Grades are inferred from harvested artifacts, goals,
  systems and roles — not from measured tool telemetry (which exists for only some
  sessions).
- **Conservative by design.** Categories with no matching work show zero;
  "produced a file" is a weak Cowork-fit signal (in-app Copilots save files too);
  the methodology time-bands are not used to decide Cowork-fit. The goal is a
  credible floor, not an inflated number.
