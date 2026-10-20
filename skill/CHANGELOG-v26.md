# Cowork ROI Report — v26

**Fix: skill validation failure when sharing as a plug-in.** No change to runtime
behavior, the pipeline, the 8 categories, the bands, or the report output — v26 is
purely a packaging/size fix so the skill passes plug-in validation.

## Reported issue
Sharing `cowork-roi-report` as a plug-in failed validation on two limits:
- **`description` frontmatter field > 1024 chars** (was 1364 — over by 340).
- **SKILL.md total > 20000 chars** (was ~28462 — over by ~8462).

## Fix
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

## Validation (post-fix)
- SKILL.md total: **17,992 / 20,000** (buffer 2,008) — PASS
- `description`:  **960 / 1,024** (buffer 64) — PASS
- All four `references/*.md` links resolve.
