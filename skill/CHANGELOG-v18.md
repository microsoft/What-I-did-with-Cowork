# CHANGELOG — v18

## Cowork-app allow-list harvest (Scout excluded, multi-layout)

**Problem this fixes.** Earlier versions harvested only `Documents/Cowork/sessions/<uuid>/` — the
*legacy* layout. Two failures followed:

1. **Missed real Cowork work.** The product moved to newer layouts
   (`Documents/Cowork/Tasks/<goal>-<date>/` and root `Documents/Cowork/<goal>-<date>/`), so recent
   sessions were invisible and reports under-counted (often to a single session, or zero).
2. **Risked counting non-Cowork work.** A separate product — the **M365 Copilot app running Scout** —
   writes session records under `Documents/Apps/<app-instance>/sessions/` (scheduled heartbeats,
   customer/needs monitors, executive briefings). Naively widening the harvest would have swept those
   in and inflated the numbers.

**The fix — positive allow-list, not a deny-list.**

- **Harvest all three Cowork layouts** under the resolved Cowork folder: `Tasks/<goal>-<date>/`, root
  `<goal>-<date>/`, and legacy `sessions/<uuid>/` (each with `input/` + `output/`).
- **Scope by creator app id.** Count a folder/artifact only when
  `createdBy.application.id == 6ab48b67-cd74-4ad4-81af-5932984589be` (the Cowork product app — stable
  across users and tenants). This is the single user-agnostic Cowork signal.
- **Never enumerate `Documents/Apps/…`.** Skipping that tree excludes Scout for every user with **no
  per-instance name list** to maintain. Scout records are written by the generic *Microsoft Graph* app
  (`99fa64eb-…`), so the creator-id allow-list also rejects them by construction.

**Why not detect-and-subtract Scout?** A deny-list keys on instance names like
`M - Internal Copilot App 1`, which differ per user and break on the next account. Allow-listing
Cowork-app-created artifacts generalises cleanly.

## Counting discipline for persistent task folders

- Cowork `Tasks/` folders are **persistent workspaces** that accumulate artifacts over multiple
  days/runs. Do **not** derive `exec_min` from file-timestamp spans for them (the span is days, not run
  time) — leave `exec_min` null so the modeled assisted clock applies, and prefer a measured telemetry
  `exec_min` when the Stop hook supplied one.
- **Fold supporting files** (QA screenshots/`*.png`, variant `*-7day/-60d/-sample.html`, prompts,
  READMEs, lock files) into the session's primary deliverable. Never count N screenshots as N
  deliverables.

## Unchanged

- Methodology (research-anchored category bands, two-clock speed multiplier), classifier, compute, and
  renderer are unchanged from v15–v16.
- Cost: still **not available** from the web / M365 Copilot app surfaces (the authoritative `/cost`
  figure isn't persisted to any file a hook can read there); the session-cost column auto-hides when no
  cost data exists. Tracked separately.
