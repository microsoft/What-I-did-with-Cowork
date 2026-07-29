# CHANGELOG — v24

## Per-user taxonomy memory (privacy fix) — stop cross-user leakage

**Fatal flaw fixed:** in v23 the taxonomy memory could leak one user's personal jobs/processes into
another user. A teammate who ran the shared package got back *exactly* the original user's processes
and JTBDs instead of their own. Root cause: personal data was committed **inside the shippable skill
folder**, and there was no per-user identity guard.

### What leaked (now removed)
- The member skill's bundled `cowork-process-registry.seed.json` shipped with real process names + JTBDs,
  and first-run copied it into the next user's memory. **The seed is deleted — no seed ships; first run
  starts with no memory.**
- Both skills' `scripts/process_overrides.json` shipped **populated** with real session→process mappings
  (docs falsely claimed "ships empty"). `classify.py` read it directly. **Reset to `{}`.**
- The aggregated skill wrote personal overrides **into the report skill's `scripts/` folder**. **Now
  writes to `working/` only.**

### The fix
- **Owner-scoped, per-user registry.** The registry is now
  `/mnt/user-config/.claude/cowork-process-registry.<userkey>.json`, where `<userkey>` derives from the
  invoking user's email, and it carries an `owner` field. It lives on the user's own mount (syncs to
  **their** OneDrive `Documents/Cowork/` folder), so the memory is in the user's Cowork folder and is
  theirs alone.
- **Identity guard.** `reconcile_taxonomy.py` **ignores any registry whose `owner` isn't the invoking
  user** (leaked / inherited / unstamped) and starts empty — so a first run mints processes from the
  user's OWN sessions, and a leaked file can never contaminate another user. New `--owner` arg (falls
  back to the harvested `meta.email`); refuses to write an unscoped registry if no owner is resolvable.
- **Per-run scratch out of the bundle.** `reconcile_taxonomy.py` writes overrides to
  `working/process_overrides.json` and `classify.py` reads them via `--overrides` (default `working/…`).
  Personal per-run data can never again land in a shippable `scripts/` folder.
- **Packaging guardrail** added to all three skills' `SKILL.md`: never bundle the registry, any
  `cowork-process-registry*.json`, or a populated `process_overrides.json`; overrides ship as `{}`.

### Migration
Existing users' memory is preserved: the old unscoped `cowork-process-registry.json` is copied to the
owner-scoped filename with an `owner` stamp on first run under v24 (do this before the first run, since
the guard ignores the unstamped file).

### What's unchanged
The v23 process-anchored taxonomy (Process ▸ JTBD ▸ Project), the two-clock methodology, KPIs, pillars,
categories, roles, deliverables/skills, activity heatmap, glossary, live rate, and Download-PDF — all as
before. Numbers still come only from `compute.py`. Alignment logic (project/process match, novel mint)
is byte-for-byte the same; only the registry location, the owner guard, and the overrides path changed.
