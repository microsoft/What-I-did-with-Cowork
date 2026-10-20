# Cowork ROI Report — v36

Makes the CSV export **opt-in** and shows an estimated credit cost.

## CSV export is now opt-in
- The report generation (step 5) **no longer emits the CSV by default** — only the
  HTML report is produced automatically.
- After showing the report (step 6), the skill **offers** the optional session-level
  CSV and states its **estimated credit cost** before generating; it runs
  `to_csv.py` only if the user opts in.

## Honest credit estimate (`scripts/to_csv.py --estimate`)
- New `--estimate` mode prints the cost and generates nothing.
- The estimate is transparent about what actually costs credits: **the export
  script itself is ~0 credits** — it is local, deterministic compute with no model
  calls and no tool/network calls. The only credits spent are for the **single
  agent step** that runs it and saves the file, estimated at **~1–5 credits**.
- The figures are clearly labeled an **estimate, not a measurement** (Cowork does
  not expose per-step credit metering) and are tunable via two constants
  (`CSV_STEP_CREDITS_LOW`/`HIGH`) in the script.
- When run for real, `to_csv.py` also prints a one-line note that the script's own
  cost was ~0.

No change to the report, categories, grades, or the CSV schema. SKILL.md stays
under 20,000 chars with a ≥2,000 buffer; description 960.
