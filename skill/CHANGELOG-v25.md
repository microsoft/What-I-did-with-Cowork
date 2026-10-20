# Cowork ROI Report — v25

Two areas: a tighter classifier and a cleaner, more legible report layout.
No change to the 8 methodology categories, the research-anchored bands, or the
value model — v25 is precision + presentation, not a new number.

## Classifier (`scripts/classify.py`)
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

## Report layout (`scripts/build_report.py`)
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
