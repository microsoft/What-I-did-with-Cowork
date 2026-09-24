#!/usr/bin/env python3
"""Cowork ROI — CSV exporter.

Emits a single, tidy, atomic-grain CSV: ONE row per session (the unit everything
else rolls up from). Because it is single-grain, SUM(value_usd) over the file is
the real total with no double-counting — the category/process/role rollups live in
the report, not appended here.

Design choices (see references/classification-methodology.md and the schema notes):
  * multi-value fields (categories, skills, professional_roles, surfaces) are
    PIPE-delimited so commas in data never break parsing;
  * UTF-8 with BOM (Excel renders x / -- correctly), every field quoted, ISO dates,
    a stable column order;
  * a run_id on every row makes appends across weekly runs safe;
  * blanks are honest n/a (e.g. credits/cost_usd without cost telemetry;
    total_interactions / interactions_in_period without the live-session telemetry
    hook). total_interactions is the session's LIFETIME user+assistant turn count;
    interactions_in_period is only those turns whose timestamp falls inside the
    report window (so a re-prompted old session shows fewer in-period than lifetime).

This export is OPT-IN because it is an extra deliverable step. Its own credit cost
is ~0 (a local, deterministic script — no model calls, no tool/network calls); the
only credits spent are for the single agent step that runs it and saves the file.
Run `--estimate` to print that estimate before deciding.

Usage:
  python to_csv.py --estimate                                    # print credit estimate, generate nothing
  python to_csv.py --data working/cowork_roi_data.json --out output/cowork-sessions.csv
"""
import json, csv, io, argparse

# --- Credit-cost estimate for DELIVERING this export --------------------------
# The export itself makes NO model calls and NO tool/network calls, so its own
# compute cost is ~0 credits. The only credits spent are for the one lightweight
# agent step that runs the script and publishes the file. Cowork does not expose
# per-step credit metering, so the figures below are an APPROXIMATE range for a
# single step (an estimate, NOT a measurement) — tune to your tenant if you have
# real numbers.
CSV_STEP_CREDITS_LOW = 1
CSV_STEP_CREDITS_HIGH = 5


def estimate_credits():
    return {
        "script_credits": 0,                       # pure local compute
        "delivery_step_credits_low": CSV_STEP_CREDITS_LOW,
        "delivery_step_credits_high": CSV_STEP_CREDITS_HIGH,
        "basis": ("Local export (no model/tool calls) = ~0 credits to compute; "
                  "one agent step to run + save it \u2248 %d\u2013%d credits "
                  "(estimate, not metered)." % (CSV_STEP_CREDITS_LOW, CSV_STEP_CREDITS_HIGH)),
    }

COLUMNS = [
    "run_id", "user_email", "window_label", "date", "title",
    "process", "jtbd", "value_pillar", "primary_category", "categories",
    "conversational", "n_run_tasks", "n_inputs", "n_outputs",
    "total_interactions", "interactions_in_period",
    "skills", "professional_roles",
    "hours_saved_typical", "value_usd", "speed_x", "credits", "cost_usd",
    "cowork_fit_grade", "cowork_fit_method", "cowork_fit_rule_grade",
    "cowork_fit_label", "cowork_fit_surfaces", "cowork_fit_evidence",
    "cowork_fit_apps", "cowork_fit_verified_cross_app", "cowork_fit_why",
]


def _pipe(v):
    return "|".join(str(x) for x in (v or []) if x != "")


def _blank(v):
    return "" if v is None else v


def rows_from(data):
    meta = data.get("meta", {})
    win = meta.get("window", {}) or {}
    rate = meta.get("hourly_rate_default", 72)
    run_id = "%s|%s_%s" % (meta.get("email", "user"), win.get("from", ""), win.get("to", ""))
    out = []
    for g in data.get("goals", []):
        cf = g.get("cowork_fit") or {}
        cats = g.get("categories") or []
        out.append({
            "run_id": run_id,
            "user_email": meta.get("email", ""),
            "window_label": win.get("label", ""),
            "date": g.get("date", ""),
            "title": g.get("title", ""),
            "process": g.get("process", ""),
            "jtbd": g.get("jtbd", ""),
            "value_pillar": g.get("value_pillar", ""),
            "primary_category": cats[0] if cats else "",
            "categories": _pipe(cats),
            "conversational": str(bool(g.get("conversational"))).lower(),
            "n_run_tasks": _blank(g.get("n_tasks")),
            "n_inputs": _blank(g.get("n_inputs")),
            "n_outputs": _blank(g.get("n_outputs")),
            "total_interactions": _blank(g.get("total_interactions")),
            "interactions_in_period": _blank(g.get("interactions_in_period")),
            "skills": _pipe(g.get("skills")),
            "professional_roles": _pipe(g.get("professional_roles")),
            "hours_saved_typical": _blank(g.get("hours_typical")),
            "value_usd": round(g.get("hours_typical", 0) * rate),
            "speed_x": _blank(g.get("speed_x")),
            "credits": _blank(g.get("credits")),
            "cost_usd": _blank(g.get("cost_usd")),
            "cowork_fit_grade": cf.get("grade", ""),
            "cowork_fit_method": cf.get("method", ""),
            "cowork_fit_rule_grade": cf.get("rule_grade", cf.get("grade", "")),
            "cowork_fit_label": cf.get("label", ""),
            "cowork_fit_surfaces": _pipe(cf.get("surfaces")),
            "cowork_fit_evidence": cf.get("evidence", ""),
            "cowork_fit_apps": _pipe(cf.get("apps")),
            "cowork_fit_verified_cross_app": str(bool(cf.get("verified_cross_app"))).lower(),
            "cowork_fit_why": cf.get("why", ""),
        })
    return out


def build(data, out_path):
    rows = rows_from(data)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write("\ufeff" + buf.getvalue())
    n_int = sum(1 for r in rows if r["total_interactions"] != "")
    n_per = sum(1 for r in rows if r["interactions_in_period"] != "")
    print("wrote %s (%d session rows, %d columns; total_interactions on %d, "
          "interactions_in_period on %d)"
          % (out_path, len(rows), len(COLUMNS), n_int, n_per))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="working/cowork_roi_data.json")
    ap.add_argument("--out", default="output/cowork-sessions.csv")
    ap.add_argument("--estimate", action="store_true",
                    help="print the credit estimate and exit without generating anything")
    a = ap.parse_args()
    if a.estimate:
        est = estimate_credits()
        print("CSV export — estimated credits: ~%d\u2013%d (one agent step; the export script itself is ~0)."
              % (est["delivery_step_credits_low"], est["delivery_step_credits_high"]))
        print(est["basis"])
    else:
        build(json.load(open(a.data)), a.out)
        print("Note: the export script itself consumed ~0 credits (local compute; no model calls).")
