#!/usr/bin/env python3
"""Cowork ROI — taxonomy memory reconciler (align-first, create-if-novel).

Runs BEFORE classify.py. Reads the harvested sessions (working/cowork_raw.json)
and the invoking user's durable, PER-USER PROCESS/PROJECT registry, then for each
session:

  1. PROJECT match  — if the goal matches a project already in the registry
                      (exact slug, or high token overlap with a known title),
                      reuse that project's {process, pillar, jtbd}.
  2. PROCESS match  — else score the goal against each registry process's
                      keywords (TF-IDF cosine, reusing classify.py's helpers);
                      above a threshold, reuse that {process, pillar} + the
                      process default_jtbd, and register the session as a NEW
                      project under that EXISTING process.
  3. NOVEL          — else mint a NEW process (name derived from the goal,
                      pillar Transformation, flagged "new": true) and a new
                      project under it.

It then writes the per-run overrides (session_id -> {process, pillar, job, jtbd};
`job` is kept = process name purely for back-compat with the not-yet-migrated
member skill) to a WORKING path, and PERSISTS the updated registry. Process is the
stable aggregation anchor; Jobs are no longer a layer in the report.

PER-USER MEMORY (privacy):
  The registry is scoped to the invoking user. Its filename embeds a sanitized
  key derived from the user's email, and the file carries an "owner" field. A
  registry whose owner does not match the invoking user (a leaked/inherited/
  unstamped file) is IGNORED — the run starts from an empty registry and mints
  processes from the user's OWN sessions. Nothing user-specific is ever written
  into the shippable skill folder: the registry lives under the per-user
  /mnt/user-config/.claude mount (which syncs to that user's OneDrive Cowork
  folder) and the overrides are a per-run scratch file under working/.

Memory-first by design: stable names come from the registry, so the model does
not re-invent process/project names each run. Only truly novel work adds a name.

Usage:
  python reconcile_taxonomy.py --in working/cowork_raw.json --owner "user@contoso.com" \
      [--registry <path>]                 # default: derived owner-scoped path (below) \
      [--overrides working/process_overrides.json]
  # --owner defaults to the harvested meta.email; if neither is present the run
  # refuses to write an unscoped registry.
"""
import json, argparse, os, sys, re

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)
# Reuse the SAME tokenizer + TF-IDF matcher the classifier uses, so alignment
# is consistent with how processes are scored everywhere else.
from classify import tokenize, build_index, embed, cosine  # noqa: E402

# Per-user registry lives under this per-user mount (syncs to the user's OneDrive
# Cowork folder). The filename embeds a sanitized owner key — see userkey().
REGISTRY_DIR = "/mnt/user-config/.claude"
# Per-run scratch — NEVER inside the shippable scripts/ folder.
DEFAULT_OVERRIDES = "working/process_overrides.json"
PILLAR_CSS = {"Revenue Growth": "rev", "Cost Reduction": "cost",
              "Risk Mitigation": "risk", "Transformation": "trans"}
PROC_THRESHOLD = 0.16    # min cosine to align a goal to an existing process
PROJ_THRESHOLD = 0.80    # min token Jaccard to align a goal to a known project title
                         # (exact-slug repeats already match at 1.0; this only catches
                         #  near-identical rewordings, so siblings stay distinct)
_STOP = {"the", "a", "an", "my", "our", "your", "of", "for", "to", "and", "with",
         "from", "into", "on", "in", "at", "by", "this", "that", "is", "are"}


def userkey(owner):
    """Sanitize an owner email/UPN into a filesystem-safe per-user key:
    lowercase; every run of non-[a-z0-9] chars (incl. '@' and '.') -> '-';
    strip leading/trailing '-'. e.g. Alice.Smith@contoso.com -> alice-smith-contoso-com"""
    return re.sub(r"[^a-z0-9]+", "-", (owner or "").strip().lower()).strip("-")


def registry_path_for(owner):
    return os.path.join(REGISTRY_DIR, f"cowork-process-registry.{userkey(owner)}.json")


def slugify(text):
    """Stable slug from a goal, using the classifier's tokenizer (lowercase,
    digit/letter split, min-length filter) so the same goal always maps to the
    same project key across runs."""
    return "-".join(tokenize(text)) or "session"


def jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def name_process(goal):
    """Derive a readable Title-Case process name for genuinely novel work
    (flagged for the agent/user to rename)."""
    toks = [t for t in re.split(r"[^A-Za-z0-9]+", goal or "") if t and t.lower() not in _STOP]
    toks = toks[:5] or ["General", "Productivity"]
    return " ".join(w[:1].upper() + w[1:] for w in toks)


def load_registry(path, owner):
    """Load the invoking user's registry. Any file that is missing an `owner`
    field or whose owner != the invoking user (leaked/inherited/unstamped) is
    IGNORED and treated as a first run — this is what keeps the memory per-user.
    `owner` is expected already lowercased/stripped by the caller."""
    reg = None
    if os.path.exists(path):
        try:
            with open(path) as f:
                reg = json.load(f)
        except Exception:
            reg = None
        if reg is not None and reg.get("owner") != owner:
            reg = None  # not this user's registry — do not align to it
    if reg is None:
        reg = {"version": 1, "owner": owner, "updated": "", "processes": {}, "projects": {}}
    reg["owner"] = owner
    reg.setdefault("processes", {})
    reg.setdefault("projects", {})
    return reg


def build_proc_index(procs):
    """TF-IDF index over existing processes: 'document' = name + keywords."""
    entries = [{"label": name, "description": " ".join(info.get("keywords", []))}
               for name, info in procs.items()]
    if not entries:
        return entries, [], {}
    vectors, idf = build_index(entries)
    return entries, vectors, idf


def main(inp, registry_path, overrides_path, owner):
    raw = json.load(open(inp))
    sessions = raw.get("sessions", [])
    meta = raw.get("meta", {}) or {}
    generated = meta.get("generated", "") or ""

    # Resolve the invoking user; fall back to the harvested email so a forgotten
    # --owner still scopes correctly rather than silently sharing.
    owner = (owner or meta.get("email", "") or "").strip().lower()
    if not owner:
        sys.exit("reconcile_taxonomy: no owner (pass --owner or set meta.email); "
                 "refusing to write an unscoped registry.")
    if not registry_path:
        registry_path = registry_path_for(owner)

    reg = load_registry(registry_path, owner)
    procs = reg["processes"]
    projects = reg["projects"]
    entries, vectors, idf = build_proc_index(procs)

    overrides = {}
    aligned, created_proj, created_proc = [], [], []

    for s in sessions:
        sid = s.get("id", "")
        goal = s.get("goal", "") or "Cowork session"
        gtok = tokenize(goal)
        gslug = slugify(goal)
        process = pillar = jtbd = None
        how = None

        # 1) PROJECT match — exact slug, then fuzzy title overlap
        if gslug in projects:
            pinfo = projects[gslug]
            process = pinfo.get("process")
            jtbd = pinfo.get("jtbd", "")
            how = "project"
        else:
            best_key, best_js = None, 0.0
            for pkey, pinfo in projects.items():
                js = jaccard(gtok, tokenize(pinfo.get("title", "")))
                if js > best_js:
                    best_js, best_key = js, pkey
            if best_key and best_js >= PROJ_THRESHOLD:
                pinfo = projects[best_key]
                process = pinfo.get("process")
                jtbd = pinfo.get("jtbd", "")
                how = "project"

        # 2) PROCESS match — TF-IDF cosine vs registry process keywords
        if process is None and vectors:
            q = embed(goal, idf)
            scored = sorted(((lab, cosine(q, vec)) for lab, vec in vectors),
                            key=lambda x: x[1], reverse=True)
            if scored and scored[0][1] >= PROC_THRESHOLD:
                process = scored[0][0]
                jtbd = procs.get(process, {}).get("default_jtbd", "")
                how = "process"
                projects[gslug] = {"title": goal, "process": process, "jtbd": jtbd,
                                   "first_seen": generated, "last_seen": generated,
                                   "session_ids": [sid] if sid else []}
                created_proj.append((sid, goal, process))

        # 3) NOVEL — mint a new process + project
        if process is None:
            process = name_process(goal)
            # never clobber an existing process name
            base, n = process, 2
            while process in procs:
                process = f"{base} ({n})"
                n += 1
            procs[process] = {"pillar": "Transformation", "pillar_css": "trans",
                              "keywords": [t for t in gtok[:10]],
                              "default_jtbd": "", "first_seen": generated,
                              "last_seen": generated, "new": True}
            jtbd = ""
            projects[gslug] = {"title": goal, "process": process, "jtbd": jtbd,
                               "first_seen": generated, "last_seen": generated,
                               "session_ids": [sid] if sid else []}
            created_proc.append((sid, goal, process))
            how = "new"
            # rebuild the index so later sessions in THIS run can align to it
            entries, vectors, idf = build_proc_index(procs)

        # bookkeeping: bump last_seen + session_ids on the resolved project/process
        if how == "project":
            pj = projects.get(gslug)
            if pj is None:
                # fuzzy-matched under a different slug key; find it
                pj = next((projects[k] for k in projects
                           if projects[k].get("title") == goal
                           or jaccard(gtok, tokenize(projects[k].get("title", ""))) >= PROJ_THRESHOLD), None)
            if pj is not None:
                pj["last_seen"] = generated
                pj.setdefault("session_ids", [])
                if sid and sid not in pj["session_ids"]:
                    pj["session_ids"].append(sid)
            aligned.append((sid, goal, process))
        if process in procs:
            procs[process]["last_seen"] = generated

        pillar = procs.get(process, {}).get("pillar", "Transformation")
        overrides[sid] = {"process": process, "pillar": pillar,
                          "job": process,  # back-compat for the not-yet-migrated member skill
                          "jtbd": jtbd or ""}

    # persist (registry carries the owner stamp; overrides are per-run scratch)
    reg["updated"] = generated
    reg["owner"] = owner
    os.makedirs(os.path.dirname(os.path.abspath(registry_path)), exist_ok=True)
    with open(registry_path, "w") as f:
        json.dump(reg, f, indent=2)
    ov_dir = os.path.dirname(os.path.abspath(overrides_path))
    os.makedirs(ov_dir, exist_ok=True)
    with open(overrides_path, "w") as f:
        json.dump(overrides, f, indent=2)

    print(f"Reconciled {len(sessions)} session(s) against the taxonomy memory (owner={owner}).")
    print(f"  aligned to existing: {len(aligned)} (projects/processes already known)")
    print(f"  new projects under existing processes: {len(created_proj)}")
    if created_proc:
        print(f"  NEW processes minted ({len(created_proc)}) — review/rename if needed:")
        for sid, goal, proc in created_proc:
            print(f"    + \"{proc}\"  <-  {goal}")
    print(f"wrote {overrides_path}")
    print(f"updated registry {registry_path} "
          f"({len(procs)} processes, {len(projects)} projects)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="working/cowork_raw.json")
    ap.add_argument("--registry", default=None,
                    help="registry path; default = owner-scoped path under "
                         "/mnt/user-config/.claude/cowork-process-registry.<userkey>.json")
    ap.add_argument("--overrides", default=DEFAULT_OVERRIDES)
    ap.add_argument("--owner", default=None,
                    help="invoking user's email/UPN; defaults to harvested meta.email")
    a = ap.parse_args()
    main(a.inp, a.registry, a.overrides, a.owner)
