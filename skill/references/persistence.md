# v43 persistence adaptation: read, stage, explicitly publish

The user mount `/mnt/user-config` is read-only to Python. Artifact tools are the
only supported writers. `.claude/` is a legacy read source, not a new durable
destination; it may be runtime-private. This patch does not enable hooks, change
settings, schedule jobs, send messages, mine a transcript or harvest user data.

## Paths and backwards compatibility

- Published data: `data/cowork-roi-report/<filename>` on `surface="user"`, read
  through `/mnt/user-config/data/cowork-roi-report/`.
- Legacy fallback: `/mnt/user-config/.claude/<filename>`, only if the corresponding
  canonical file does not exist. No old file is removed, edited, or migrated by
  installation; the first approved snapshot publication performs migration.
- Writable snapshots: `working/cowork-roi-state/<filename>` in this workspace.
- Taxonomy filenames remain `cowork-process-registry.<userkey>.json`, with the
  existing owner stamp and sanitized email key. Confirm the signed-in identity
  and reject non-owner memory exactly as before. Never put personal state in the
  skill folder, a package, a public report, or another person's data namespace.
- `compute.py` resolves cost, credits and telemetry files independently so one
  migrated ledger does not hide another legacy ledger. This patch does not create
  a credit-capture writer or estimate missing credits/costs.

## Taxonomy run

1. Get the signed-in email using `GetMyDetails`; set `meta.email` and `--owner`.
2. Run `reconcile_taxonomy.py --in working/cowork_raw.json --owner <email>`.
   `--registry` now specifies a READ source; `--registry-out` a writable snapshot.
   Defaults read the canonical/legacy registry and write the owner-named snapshot
   under `working/cowork-roi-state/`, plus the same per-run overrides as before.
3. Inspect/rename newly discovered processes only in the working snapshot. For a
   second reconciliation before publication pass `--registry <working snapshot>`.
   Owner mismatch/unstamped memory starts empty; invalid JSON raises a recovery
   error rather than replacing the damaged source. Preserve it and ask the user.
4. Publish ONLY that snapshot (not the whole directory):
   `CopyArtifact(surface="user", source="working/cowork-roi-state/cowork-process-registry.<userkey>.json", destination="data/cowork-roi-report/cowork-process-registry.<userkey>.json", overwrite=true)`.
   Source must start exactly `working/`. Wait for writing to finish, verify
   `copied == 1`, then read the installed JSON and verify owner/content.
5. Approval denial or failed publication means memory was NOT saved. Current
   scratch overrides can still classify this run. Say so explicitly even though
   the normal report readout otherwise keeps methodology caveats in the report.
   On `source not visible yet`, wait then retry the SAME call; do not write the
   mount directly. Resolve a missing source path before retrying.
6. Report write-back honestly: `onedrive.status="synced"` means saved to OneDrive,
   with other sessions picking it up at their next sync; `syncing` means saved in
   this session and still uploading. `not_applicable` means runtime-private:
   do not claim OneDrive persistence. Never claim success on `ok` alone.

## Telemetry and status-line cost capture

`mine_session.py --log <read ledger> --log-out working/cowork-roi-state/cowork-session-telemetry.json`
upserts into a staged ledger. `--log-out` alone auto-selects the canonical/legacy
read source. Old commands with `--log /mnt/user-config/.claude/...` now READ that
path and stage the update instead of attempting to write it. Record fields and
session-key behavior are unchanged. No `--log`/`--log-out` still emits only the
single-session output. Missing transcript does not fabricate a record.

`statusline_cost.py` reads published/legacy costs, retains the maximum observed
cost per session, and stages `working/cowork-roi-state/cowork-session-costs.json`.
It always renders the status line. A staging error is reported on stderr; it
must never be described as saved. Corrupted ledgers are not replaced by empty
logs. Python performs local atomic replacement, not durable publication.

A hook/status-line subprocess has no artifact-tool capability. **It cannot
provide automatic cross-session persistence in this runtime.** An explicit
agent step, with approval, must publish each staged ledger individually to
`data/cowork-roi-report/<same filename>` with `CopyArtifact(surface="user")` and
verify one copied file plus readback. Do this before the next report consumes the
ledger. Without publication the snapshot remains workspace-local; old chat-only
history is not recovered. An existing hook entry alone is not proof of capture
or durable persistence. Do not activate hooks/schedules during installation or
repair; obtain a separate user request for activation.

## Coordination and privacy

Snapshots are single-writer per workspace. Before publishing, compare the read
source with its baseline: if it changed, rebase against the newer published
ledger or stop and ask instead of overwriting concurrent updates. Do not publish
stale scratch from another owner/workspace. For log rebases keep unrelated
sessions and the latest telemetry record, and the maximum cost per session.
Full-file `CopyArtifact` is not a transaction across concurrent sessions; do not
promise global locking. Coordinate concurrent runs explicitly.

Telemetry keeps the existing goal/request/action/artifact evidence; it is NOT
anonymized. Publish it only to the signed-in user's approved private user
surface, never a third party, team channel or shared skill package. Nothing is
published merely because a hook fires. For corrupt input, preserve existing data
and fail the persistence step visibly rather than losing prior sessions.

## Checks and limits

Structural/resource/security checks do not execute any imported third-party
scripts. Focused synthetic tests cover the newly authored staging helper with
fake state only, including merge, corruption, mount rejection, symlinks and
atomic snapshots. They do not run the ROI pipeline, read a live transcript,
activate a hook or test end-to-end OneDrive synchronization. Durable tool writes
are confirmed for the installed CODE, not for real ROI state until the user
actually runs a report and approves publication.
