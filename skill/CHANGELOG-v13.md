# Cowork ROI Report — v13 (bundle)

## Bundled & auto-invoked
- Ships **both** `cowork-roi-report` and `map-my-work` in one package. The ROI report **auto-invokes**
  `map-my-work` (step 4b) — the user never runs it separately.

## Fully portable — personalized to whoever runs it
- **Rich override handoff:** `map-my-work` returns `{process, pillar, job, jtbd}` per session;
  `process_overrides.json` carries the full tuple; `classify.py` consumes it **directly** (live).
  `pillar_css` is derived from the pillar name. Plain-string overrides still accepted (back-compat).
- **No personal data:** removed all user-specific seed taxonomy, process lists, and JTBD examples.
  `apqc_taxonomy.json` is the generic APQC 13 only — the fallback when `map-my-work` isn't present.
  `map-my-work` derives the signed-in user's own Jobs / Processes / Pillars / JTBDs from their footprint.

## Carried over from v12
- Work-by-business-process table **bands by Job × Pillar** with a JTBD sub-line per row.
- **Skills-augmented bug fixed:** `classify.py` `norm()` now preserves per-deliverable + session-level
  `skills` tags (v11 silently dropped them), so the Skills-augmented and Deliverables tables populate.
- SKILL.md step 4a makes skills-tagging a required harvest step.
