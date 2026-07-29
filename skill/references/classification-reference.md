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
                 "has_folder":true, "exec_min":<measured minutes|null>}, ... ] }
```
`classify.py` adds the `tasks` array (categories) and writes `working/cowork_sessions.json`. Where a live
`session_telemetry.json` exists for a session, prefer its measured `exec_min`, tool counts and `produced_artifact`
flag over the file-timestamp estimate.
