# CHANGELOG — v6: business-process stamping + session-aware categories

**Date:** 2026-06-18
**Scope:** `scripts/classify.py`, `scripts/compute.py`, `scripts/build_report.py`
**Back-compatible:** yes — input schema unchanged; one new field (`process`) is added to
classified sessions and to the report payload. Older payloads still render (process falls
back to a default).

---

## TL;DR

1. **Each session is now stamped with a business `process`** (WHAT outcome the work served:
   *Sales & Pre-Sales*, *Finance & Cost Management*, *People & Talent*, …). Labels are
   **derived dynamically per user** — no hardcoded project/person names.
2. **Task categories now reflect the WHOLE session**, not just the output file extension.
   Reading 8 reports and producing a deck is now `analysis + document`, not `document` only.
3. **The report's "Goals & leverage" section is replaced by a "Work by business process"
   table**: *Business process · Task category · Project · Assistance & multiplier*.

---

## 1. Dynamic, personalized business-process labels  (`classify.py`)

Every classified session gains a `process` string. It is resolved in this order:

1. **Universal business-function lexicon** (`PROCESS_LEXICON`) — generic, portable vocabulary
   (proposal/customer → Sales; budget/cost/usage → Finance; team contribution/performance →
   People & Talent; status deck/dashboard/report → Business Reviews & Reporting; …). Contains
   **no** project- or person-specific tokens, so it works for any user.
2. **Synthesized fallback** — if no generic function matches, a label is built from the user's
   **own goal vocabulary** (`salient_phrase()`), suffixed by the category (e.g. a user whose
   goals repeatedly mention "Helios" gets `Helios Triage Analysis`, `Helios Engineering`).
3. **Category default** (`CAT2PROCESS`) — last resort.

Personalization comes from `build_profile(meta, sessions)`, which infers the employer from the
email domain and **mines recurring terms across the user's goals** so repeated initiatives map
to a stable, personalized label. Nothing about one specific user is baked into the code.

## 2. Session-aware task categories  (`classify.py`)

`classify_session()` previously keyed **only** on output file extensions (`EXT2CAT`), so any
user who saves `.pptx`/`.docx` had every session labeled `document`. It now unions three signals:

| Signal | Source | Implies |
|--------|--------|---------|
| What was **produced** | output extensions (`EXT2CAT`) | document / analysis / code / special |
| What the work **was** | goal intent (`goal_categories()`) | analyze/synthesize/ROI/research → `analysis`; debug/script/api → `code`; "review/​build **from** \<report·data·dashboard>" → `analysis` |
| What was **analyzed** | inputs | data files (xlsx/csv/json) or ≥3 sources → `analysis` |

Results are de-duped, ordered by `PRIORITY`, and capped at the 2 highest-signal categories.

## 3. Process carried through compute  (`compute.py`)

* Each goal record now includes `"process"`.
* A new top-level **`processes`** array aggregates sessions/minutes/hours/value per process
  (for any future roll-up view). Purely additive.

## 4. Report: "Work by business process" table  (`build_report.py`)

The `📦 Goals & leverage` section is replaced by `📦 Work by business process`, a 4-column table:

| Business process | Task category | Project | Assistance & multiplier |
|---|---|---|---|
| People & Talent | Analysis & Research + Document & content creation | Synthesize FY26 team contributions deck from 8 reports | 3.2h saved · $230 · 6.4× faster |

The live hourly-rate control still recalculates the dollar column (`.g-v` + `data-hours` hooks
are preserved). The hero "Leverage:" summary note is unchanged.

---

## How to absorb this into your code (migration)

If your fork has diverged, port these self-contained pieces — there are no cross-file schema
changes beyond the additive `process` field.

**A. `scripts/classify.py`**
1. Add the block **`# ---- Business-process stamping (dynamic & personalized)`** through
   `infer_process()` (constants `PROCESS_LEXICON`, `CAT2PROCESS`, `CAT_SUFFIX`, `STOPWORDS`,
   `ACTION_VERBS` and helpers `_tokens`, `_keepers`, `salient_phrase`, `build_profile`,
   `infer_process`). Add `re` to the imports.
2. Replace `classify_session()` with the session-aware version and add the
   **`# ---- Session-aware category signals`** block (`ANALYSIS_SIGNALS`, `REVIEW_VERBS`,
   `SOURCE_PREPS`, `ANALYTICAL_OBJECTS`, `CODE_SIGNALS`, `EMAIL_SIGNALS`, `MEETING_SIGNALS`,
   `DATA_EXT`, `goal_categories()`).
3. In `main()`, build `profile = build_profile(d.get("meta", {}), sessions)` before the loop
   and add `"process": infer_process(s.get("goal",""), tasks, profile)` to each output record.

**B. `scripts/compute.py`**
1. Read `process = s.get("process","General Productivity")` in the session loop.
2. Add `"process": process` to each `goals.append({...})` record.
3. (Optional) add the `proc_count`/`proc_min` counters and the `"processes"` payload array.

**C. `scripts/build_report.py`**
1. Replace the `# ----- goals list -----` builder with the `proc_rows` builder (4 `<td>`s).
2. Swap the `Goals & leverage` section markup for the `Work by business process` table
   (with `<thead>`).
3. Add the two CSS rules: `table.tbl th{…}` and `.pill.proc{…}`.

**Pipeline (unchanged):**
```
python scripts/classify.py     --in working/cowork_raw.json      --out working/cowork_sessions.json
python scripts/compute.py      --in working/cowork_sessions.json --out working/cowork_roi_data.json
python scripts/build_report.py --data working/cowork_roi_data.json --out output/cowork-roi-report.html
```

**Tuning knobs:** reorder `PROCESS_LEXICON` to change tie-breaking between functions; edit the
keyword lists to match your org's process names; adjust `ANALYSIS_SIGNALS`/`ANALYTICAL_OBJECTS`
to change when a session counts as analysis. Everything stays deterministic.
