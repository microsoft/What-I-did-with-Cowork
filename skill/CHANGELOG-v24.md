# CHANGELOG — v24

## Per-user taxonomy memory — owner-scoped registry

v24 makes the durable taxonomy memory **per-user and owner-scoped**, so each person's process and
project names are derived from and stored against their own identity, and stay in their own space.

### What changed
- **Owner-scoped, per-user registry.** The registry is now
  `/mnt/user-config/.claude/cowork-process-registry.<userkey>.json`, where `<userkey>` derives from the
  invoking user's email, and it carries an `owner` field. It lives on the user's own mount (syncs to
  **their** OneDrive `Documents/Cowork/` folder), so each user's taxonomy memory is theirs alone.
- **Identity guard.** `reconcile_taxonomy.py` only uses a registry whose `owner` matches the invoking
  user; otherwise it starts empty and mints processes from the user's own sessions. New `--owner` arg
  (falls back to the harvested `meta.email`); it won't write an unscoped registry if no owner is
  resolvable.
- **Per-run scratch out of the bundle.** `reconcile_taxonomy.py` writes overrides to
  `working/process_overrides.json` and `classify.py` reads them via `--overrides` (default `working/…`),
  keeping per-run data out of the shippable `scripts/` folder.
- **First run starts clean.** No registry seed ships, and the bundled `scripts/process_overrides.json`
  ships as `{}` — a first run mints processes from the user's own sessions.
- **Packaging guardrail** added to all three skills' `SKILL.md`: never bundle the registry, any
  `cowork-process-registry*.json`, or a populated `process_overrides.json`; overrides ship as `{}`.

### Migration
Existing memory is preserved: an old unscoped `cowork-process-registry.json` is copied to the
owner-scoped filename with an `owner` stamp on first run under v24 (do this before the first run, since
the guard uses only the owner-stamped file).

### What's unchanged
The v23 process-anchored taxonomy (Process ▸ JTBD ▸ Project), the two-clock methodology, KPIs, pillars,
categories, roles, deliverables/skills, activity heatmap, glossary, live rate, and Download-PDF — all as
before. Numbers still come only from `compute.py`. Alignment logic (project/process match, novel mint)
is unchanged; only the registry location, the owner guard, and the overrides path changed.
