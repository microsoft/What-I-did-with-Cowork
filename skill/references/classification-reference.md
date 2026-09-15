# Classification reference — heuristics, counting discipline & raw-harvest schema

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
                 "request":"<original ask>", "actions":["mcp__outlook__ListMessages","Write", ...],
                 "apps_accessed":["Outlook","Excel"], "sources_reviewed":<int>,
                 "has_folder":true, "exec_min":<measured minutes|null>}, ... ] }
```
`classify.py` adds the `tasks` array (categories) and writes `working/cowork_sessions.json`. Where a live
`session_telemetry.json` exists for a session, prefer its measured `exec_min`, tool counts and `produced_artifact`
flag over the file-timestamp estimate.

**Workflow evidence (`request` / `actions` / `apps_accessed` / `sources_reviewed`).** These are the
action-grounded record of *what Cowork did* — mined by `mine_session.py` from the transcript. `compute.py`'s
Cowork-fit unions the **verified** `apps_accessed` with the apps **inferred** from outputs, so a cross-app
workflow (e.g. Outlook + Excel) grades **H** on evidence, not on the single file that landed in OneDrive.
**Populate them only when the action history is actually available; leave them ABSENT (not `[]`) when it is
not** — their absence is the signal that the assessment must fall back to **"Insufficient evidence"** rather
than assume a single-app workflow from a lone output.
