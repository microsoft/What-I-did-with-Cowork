# Cowork ROI Report — v37

Fixes a confusing Cowork-fit hover label on AI-reviewed grades.

## The bug
When the optional LLM review layer **changed** a project's grade (e.g. upgraded a
data-to-deck project the rule scored Low up to **High**), it overrode the grade and
the "why" sentence but **kept the rule's original label**. Because the report's hover
tooltip is built as `label + ": " + why`, a High badge could read:

> "PowerPoint Copilot could do it: Cross-surface, multi-step … needs Cowork."

— a single-app label contradicting the High grade it now carried.

## The fix (`scripts/compute.py`)
- Added `CF_REVIEW_LABELS = {"H": "Needs Cowork", "M": "Borderline fit",
  "L": "Single-app Copilot could do it"}`.
- In the review layer, when a review **changes** the grade and supplies no label of
  its own, the label is now **regenerated to match the new grade**. An upgraded High
  therefore reads **"Needs Cowork: …"** and leads with the justification for Cowork,
  never the rule's single-app label. An explicit `review.label` still wins; a
  confirmed (unchanged) grade keeps its rule label.

No change to grades, the value model, categories, the report layout, or the CSV.
