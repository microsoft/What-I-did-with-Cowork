# CHANGELOG — v5: artifact-scaled speed multiplier

**Date:** 2026-06-08
**Scope:** `scripts/compute.py`, `scripts/build_report.py` (input schema + report framing)

---

## TL;DR

1. **Speed multiplier is now the headline**, derived from the number of **distinct artifacts
   analyzed and produced** in each session.
2. **Value is framed as a professional-services equivalent** (expert-hours × rate).
3. **ROI / Copilot-seat-cost removed** — credit & seat consumption isn't available, so a
   ROI ratio couldn't be grounded.

---

## Why we changed it

**Problem 1 — multi-artifact sessions were undercounted.** v4 applied a *flat* per-task band
(analysis = 71 min, document = 24 min) regardless of how many sources went in or deliverables
came out. A session that synthesized **8 PDFs into a deck** scored identically to one that used
a single PDF. That erased the user's real leverage.

**Problem 2 — the ROI figure wasn't grounded.** v4's "ROI multiple = human value ÷ $30 seat cost"
implied a precision we can't support: Cowork credit/seat consumption isn't exposed, so the
denominator was a placeholder. We removed it rather than present a number we can't defend.

---

## The new model (two clocks)

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

## Before / after (worked example)

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

## File-level changes

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

## v5.1 — "Analyzed → Produced" replaces the collaboration donut

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

## Migration

Re-harvest sessions with the new `inputs`/`outputs` arrays to get the artifact-scaled multiplier
**and** the Analyzed → Produced breakdown. Old payloads (single `artifacts[]`) still run but won't
reflect artifact volume or the I/O split.

## Honest caveat to keep

The **assisted clock is modeled**, not measured. The multiplier is **directional**. The only way
to tighten it is to capture real hands-on time per session.
