#!/usr/bin/env python3
"""Cowork ROI — statusLine cost capture (auto, no calculation, no /usage needed).

The harness invokes the configured statusLine command on every render and pipes
it a JSON payload that ALREADY contains the live session cost:

  { "session_id": "...",
    "cost": { "total_cost_usd": 2.39, "total_duration_ms": ... },
    "model": { "display_name": "Opus 4.8" }, ... }

This script taps that feed: it persists the authoritative cost (verbatim from the
harness — we do NOT compute it) to a durable, de-duplicated log, then prints a
short status string so the status bar still works.

Auto-trigger & de-dupe:
  * statusLine fires continuously, so the cost is captured without anyone running
    /usage. The value only grows within a session, so the LAST write per session
    id is the full cumulative cost.
  * Re-entering a session keeps the same session_id → the same log key keeps
    updating to the latest cumulative total. Each session appears once, final cost.

Durable log: /mnt/user-config/.claude/cowork-session-costs.json
  { "<session_id>": {"session_id","total_cost_usd","model","updated_at",
                     "duration_ms","lines_added","lines_removed"} , ... }

Runs in the render loop — must be fast and never crash. All errors are swallowed;
it always prints something and exits 0.
"""
import sys, os, json, datetime

LOG_PATH = "/mnt/user-config/.claude/cowork-session-costs.json"


def load_log():
    try:
        with open(LOG_PATH) as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def main():
    try:
        raw = sys.stdin.read()
        p = json.loads(raw) if raw.strip() else {}
    except Exception:
        p = {}

    cost = p.get("cost") or {}
    total = cost.get("total_cost_usd")
    sid = p.get("session_id", "")
    model = (p.get("model") or {}).get("display_name", "")

    # Persist (only if the harness actually gave us a cost + a session id)
    if sid and isinstance(total, (int, float)):
        try:
            log = load_log()
            prev = log.get(sid, {})
            # Guard against a transient lower reading: keep the max seen for the session
            prev_total = prev.get("total_cost_usd", 0) or 0
            best = total if total >= prev_total else prev_total
            log[sid] = {
                "session_id": sid,
                "total_cost_usd": round(best, 4),
                "model": model or prev.get("model", ""),
                "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
                "duration_ms": cost.get("total_duration_ms"),
                "lines_added": cost.get("total_lines_added"),
                "lines_removed": cost.get("total_lines_removed"),
            }
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            tmp = LOG_PATH + ".tmp"
            with open(tmp, "w") as f:
                json.dump(log, f, indent=2)
            os.replace(tmp, LOG_PATH)   # atomic — render loop writes frequently
        except Exception:
            pass

    # Always render a status line
    if isinstance(total, (int, float)):
        sys.stdout.write(f"\U0001F4B0 ${total:.2f}" + (f" · {model}" if model else ""))
    else:
        sys.stdout.write(model or "Cowork")


if __name__ == "__main__":
    main()
    sys.exit(0)
