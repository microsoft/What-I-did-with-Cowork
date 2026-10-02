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

## Part 2 — Cowork-fit (H / M / L / ?) — a hybrid

**The guiding question — the "single-surface test":**

> *Could a single surface-specific / in-app Copilot (Excel, Word, PowerPoint,
> Outlook, Teams, or Copilot chat) have done this end-to-end?*

If **yes**, the rule grades the work Low. Cowork's strongest fit is work no single
in-app Copilot spans: building, automating, multi-document handling, or orchestration
across apps.

| Grade | Colour | Meaning |
|---|---|---|
| **H — High** | Green | Cross-app work, a build, automation/Specialized work, multi-document synthesis, or multiple output formats. |
| **M — Moderate** | Yellow | Non-chat work with at least two input formats or at least three inputs/outputs, after no High rule matched. |
| **L — Low** | Red | Chat-only work, or remaining work that maps to one recognized app. |
| **? — Insufficient evidence** | Grey | A remaining output maps to no recognized app and has no stronger signal. |

### What the baseline actually reads

The deterministic baseline in `scripts/compute.py` uses:

- Goal text and classified task categories.
- Input/output extensions and file counts.
- Verified app names from `apps_accessed`.
- Inferred app names from outputs and selected goal/category keywords.
- Surfaces from another session only when both sessions share the same output
  basename.

The current rule does **not** branch on raw `actions`, `sources_reviewed`, or
professional roles. An action trace affects the baseline only through the derived
`apps_accessed` list.

### Layer 1 — exact first-match order

The first matching branch wins:

1. **Two or more apps → H.** Union verified `apps_accessed`, apps inferred from
   outputs and goal/category signals, and apps from sessions sharing an output
   basename.
2. **Build → H.** ZIP/code/HTML output, an explicit skill/package build, or an
   explicit web-app/site/dashboard build.
3. **Automation or Specialized workflow → H.** Executed connector/browser/sweep
   work, an automation keyword (`triage`, `workflow`, `recurring`, `batch`,
   `pipeline`, and similar), or the **Specialized workflows** category.
4. **Multi-document synthesis → H.** At least **3 inputs across at least 2 file
   formats**, or **more than 5 inputs**.
5. **Multiple output formats → H.** At least **2 distinct output extensions**.
6. **No outputs → L.** Chat-only work reaches this branch unless a High rule matched.
7. **Moderate file handling → M.** At least **2 input formats**, or at least
   **3 inputs** or **3 outputs**.
8. **One recognized app → L.**
9. **Anything remaining → ?**

This order is significant: chat-only installation, sharing, or scheduling requests
are currently **L**, not M, unless an earlier automation or Specialized-workflow rule
makes them H.

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

Every H/M/L dot in the report is hoverable and shows its **project-specific reason
and its method** (rule-based vs AI-reviewed), so you can always see *why* a grade
was given and *how* it was decided.

**Review guard.** If H is backed by verified cross-app evidence, a build, or
automation/Specialized work, review cannot lower it to L or ? without a `conflict`
or `resolves_evidence` note. Moving H to M is allowed. High grades based only on
multi-document or multi-output rules are not covered by this guard.

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
- **Heuristic inputs.** Grades are inferred from files, goals/categories, and
  verified/inferred app names. Raw actions, source counts, and professional roles
  do not currently affect the grade.
- **Conservative by design.** Categories with no matching work show zero;
  "produced a file" is a weak Cowork-fit signal (in-app Copilots save files too);
  the methodology time-bands are not used to decide Cowork-fit. The goal is a
  credible floor, not an inflated number.
