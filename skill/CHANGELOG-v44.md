# v44 — One category per session

- `classify.py`: each session now maps to exactly ONE category (was up to 2), chosen by the PRIORITY tie-break.
- `classify.py`: skill creation, attachment, install, packaging and quality review (goal mentions a skill/plugin, or a .zip/.skill input or output) is classified as **Write or debug code**; `.zip`/`.skill` now map to code instead of Specialized workflows.
- `compute.py`: time saved is attributed to the session's single category only; telemetry runs logged under other categories are dropped (not reassigned), so no session is double-counted.
- Docs (SKILL.md, classification-methodology.md) updated to match.
