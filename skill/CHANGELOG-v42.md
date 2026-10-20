# Cowork ROI Report — v42

Shared current-runtime capture fix with `cowork-dashboard-member` v26.

## Fixed
- `scripts/mine_session.py` is identical in both skills. It discovers current Copilot
  `.copilot-state/*/session-state/*/events.jsonl` (newest by modification time), retains legacy
  discovery and parsing, and leaves `--transcript`, `--out`, and `--log` unchanged.
- Parse current event timestamps, session id (parent-directory fallback), first user-message title
  (attachment/date tags stripped, first line, at most 80 characters), message counts, tool starts,
  and output artifacts from shutdown changes and host artifact-tool arguments.
- Normalize `server-Tool` names before the existing category/app/source rules; count Outlook as
  email, Teams as communication, calendar/transcripts as meeting, edits as code, and research as
  analysis. Tool requests/completions do not duplicate starts. Duration is wall-clock, not active time.
- Current events use transcript artifact evidence rather than unrelated workspace outputs.
  Working/user-surface artifact writes and recursive folder destinations are not deliverable files.
- The shared user settings use `/mnt/user-config/skills/cowork-roi-report/scripts/` for both
  `mine_session.py` and `statusline_cost.py`. The telemetry log stays at
  `/mnt/user-config/.claude/cowork-session-telemetry.json`; other settings are preserved.

## Documentation and limits
- Added a brief first-run telemetry-hook check to SKILL.md §3 and current installed paths in the
  README hooks section. Missing/nonexistent Stop-hook targets mean forward capture is not active.
- Neither sibling ever had historical chat-only harvesting in this script: OneDrive holds file
  artifacts and the log builds forward. Historical recovery requires consent-based enumeration of
  the Cowork app's title/date session list; member v26 supplies the detailed privacy-gated §3b flow.
- This update does not execute a report, harvest, post, schedule, credits collection, or historical
  backfill. Taxonomy, channel memory, telemetry and credits records are not modified.
- A corrected hook path still depends on runtime activation/support; automatic Stop execution is
  not verified by a parser-only test.
