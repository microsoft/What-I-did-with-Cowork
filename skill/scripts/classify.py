#!/usr/bin/env python3
"""Cowork ROI — TF-IDF session classifier v6.

Drop-in replacement for the hand-crafted keyword-lexicon classifier.

BUSINESS-PROCESS LABELS are assigned via TF-IDF cosine similarity against the
APQC Process Classification Framework (PCF) — a vendor-neutral, publicly
maintained business-process taxonomy (~13 top-level categories, ~1 000 sub-
processes). This replaces substring matching against a hand-tuned PROCESS_LEXICON
that suffered from exact-match brittleness (plural/synonym misses, vendor-name
bleed-through, missing abbreviations, English-only vocabulary).

Architecture
------------
  goal text
      │
      ▼
  tokenize()          ← digit-letter boundaries split, lowercase, min-length filter
      │
      ▼
  embed()             ← TF-IDF sparse vector  [SWAP HERE for dense embeddings]
      │
      ▼
  nearest()           ← cosine similarity vs. APQC taxonomy vectors
      │
      ▼
  APQC category label

Upgrading to dense semantic embeddings (Azure OpenAI text-embedding-3-small)
-----------------------------------------------------------------------------
Replace the body of embed() with:

    import requests
    resp = requests.post(
        "https://<your-resource>.openai.azure.com/openai/deployments/"
        "text-embedding-3-small/embeddings?api-version=2024-02-01",
        headers={"api-key": "<key>"},
        json={"input": text},
        timeout=10,
    )
    return resp.json()["data"][0]["embedding"]   # list[float]

Then change cosine() to operate on list[float] instead of dict. Everything
else — build_index(), nearest(), the session loop — stays identical.

Connecting to O*NET Web Services (free, no auth required)
----------------------------------------------------------
O*NET Detailed Work Activities (DWAs) are an occupation-centric alternative
taxonomy. To use them, replace apqc_taxonomy.json entries with O*NET DWA
categories fetched at startup:

    import requests
    dwa = requests.get("https://services.onetcenter.org/ws/dwa_categories",
                       headers={"Accept": "application/json"}).json()
    entries = [{"id": d["code"], "label": d["title"],
                "description": d["description"]} for d in dwa["dwa_category"]]

Same embed() + nearest() call applies; only the taxonomy source changes.
O*NET is better for occupation-level granularity; APQC PCF is better for
pure business-process labeling across roles.

Label overrides
---------------
reconcile_taxonomy.py writes a per-run overrides file to working/process_overrides.json
(session_id -> process label or {process,pillar,job,jtbd}); pass it via --overrides.
The classifier checks it first and skips similarity scoring for matched IDs. This file
is per-run scratch and must NEVER live in the shippable scripts/ folder, so one
user's session→process mappings stay out of the packaged skill.

Usage: python classify.py --in working/cowork_raw.json --out working/cowork_sessions.json
"""
import json, argparse, collections, re, math, os

# ---------------------------------------------------------------------------
# Tokenizer — splits on non-alphanumeric AND on digit↔letter transitions
# so "fy26" → ["fy", "26"], "q4" → ["q", "4"], "api" → ["api"].
# This is the main reason the old lexicon missed "FY26" vs "fy" patterns.
# ---------------------------------------------------------------------------

def tokenize(text: str) -> list:
    t = (text or "").lower()
    t = re.sub(r"([a-z])([0-9])", r"\1 \2", t)  # fy26  → fy 26
    t = re.sub(r"([0-9])([a-z])", r"\1 \2", t)  # 3way  → 3 way
    return [tok for tok in re.split(r"[^a-z0-9]+", t) if len(tok) > 1]


# ---------------------------------------------------------------------------
# TF-IDF "embedding" — pure Python, zero external deps.
# ---------------------------------------------------------------------------

def build_index(entries: list) -> tuple:
    """Pre-compute TF-IDF vectors for every taxonomy entry.

    Returns (vectors, idf) where:
        vectors: list of (label, {token: weight})
        idf:     dict {token: idf_value}  — shared vocabulary
    """
    N = len(entries)
    df: dict = collections.defaultdict(int)
    tok_lists = []
    for e in entries:
        toks = tokenize(e["label"] + " " + e["description"])
        tok_lists.append(toks)
        for t in set(toks):
            df[t] += 1

    # Smoothed IDF: log((N+1)/(df+1)) + 1  — avoids zero for unseen terms
    idf = {t: math.log((N + 1.0) / (c + 1.0)) + 1.0 for t, c in df.items()}

    vectors = []
    for i, e in enumerate(entries):
        tf = collections.Counter(tok_lists[i])
        total = len(tok_lists[i]) or 1
        vec = {t: (cnt / total) * idf[t] for t, cnt in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vectors.append((e["label"], {t: v / norm for t, v in vec.items()}))

    return vectors, idf


def embed(text: str, idf: dict) -> dict:
    """Sparse TF-IDF vector for a query string.

    SWAP THIS FUNCTION to use dense semantic embeddings — see module docstring.
    The signature and return type (dict) can change to list[float] if you also
    update cosine() accordingly; nothing else needs to change.
    """
    toks = tokenize(text)
    tf = collections.Counter(toks)
    total = len(toks) or 1
    # Unknown tokens (not in training corpus) get idf = 1.0 as a neutral weight
    vec = {t: (cnt / total) * idf.get(t, 1.0) for t, cnt in tf.items()}
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {t: v / norm for t, v in vec.items()}


def cosine(a: dict, b: dict) -> float:
    """Dot product of two normalized sparse vectors = cosine similarity."""
    return sum(a.get(t, 0.0) * w for t, w in b.items())


def nearest(goal: str, cat_hint: str, vectors: list, idf: dict) -> str:
    """Return the best-matching APQC label.

    cat_hint: primary methodology category (analysis/document/code/…) used as
    a lightweight tiebreaker — it narrows ambiguous goals (e.g. 'document'
    boosts 'Sales & Customer Engagement' slightly over 'Analytics & Reporting'
    for a deck-centric goal).
    """
    # Combine goal text with a single hint token so category vocabulary can tip ties
    query = embed(goal + " " + cat_hint, idf)
    scored = sorted(
        ((label, cosine(query, vec)) for label, vec in vectors),
        key=lambda x: x[1],
        reverse=True,
    )
    return scored[0][0]  # always return best match; score is available if needed


# ---------------------------------------------------------------------------
# Taxonomy loader + optional override file
# ---------------------------------------------------------------------------

_DIR = os.path.dirname(__file__)
_TAXONOMY_PATH = os.path.join(_DIR, "apqc_taxonomy.json")
# Per-run overrides are scratch, written by reconcile_taxonomy.py under working/.
# They are NEVER read from the shippable scripts/ folder, so one user's
# session→process mappings stay out of the packaged skill.
_OVERRIDES_PATH = "working/process_overrides.json"
_ROLES_PATH = os.path.join(_DIR, "roles_taxonomy.json")
_PILLAR_CSS = {"Revenue Growth": "rev", "Cost Reduction": "cost",
               "Risk Mitigation": "risk", "Transformation": "trans"}


def load_taxonomy() -> tuple:
    with open(_TAXONOMY_PATH) as f:
        entries = json.load(f)
    pillar_lookup = {
        e["label"]: (e.get("value_pillar", "Transformation"),
                     e.get("pillar_css", "perf"))
        for e in entries
    }
    job_lookup = {
        e["label"]: (e.get("job", "Other"), e.get("jtbd", ""))
        for e in entries
    }
    # Returns ((vectors, idf), pillar_lookup, job_lookup)
    return build_index(entries), pillar_lookup, job_lookup


def load_overrides(path: str = _OVERRIDES_PATH) -> dict:
    """Optional {session_id: process_label|obj} hard overrides — the per-run
    scratch file written by reconcile_taxonomy.py under working/ (never inside
    the shippable scripts/ folder)."""
    if path and os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


# ---------------------------------------------------------------------------
# Methodology category logic — unchanged from v5.
# This answers HOW the work was done (analysis / code / document / …).
# The APQC lookup above answers WHAT business process it served.
# ---------------------------------------------------------------------------

EXT2CAT = {
    # Document & content creation
    "docx": "document", "doc": "document", "pdf": "document",
    "md": "document", "txt": "document", "rtf": "document",
    "pptx": "document", "ppt": "document",
    "png": "document", "jpg": "document", "jpeg": "document",
    "svg": "document", "eps": "document", "gif": "document",
    # Analysis & research
    "xlsx": "analysis", "xlsm": "analysis", "xls": "analysis",
    "csv": "analysis", "tsv": "analysis", "json": "analysis", "parquet": "analysis",
    # Write or debug code
    "html": "code", "htm": "code", "py": "code", "ps1": "code",
    "js": "code", "ts": "code", "sql": "code", "ipynb": "code",
    "sh": "code", "yaml": "code", "yml": "code",
    # Specialized workflows
    "zip": "special", "skill": "special",
}

PRIORITY = ["code", "analysis", "special", "document", "comms", "meeting", "email", "general"]

ANALYSIS_SIGNALS = (
    "analyz", "analyse", "analysis", "research", "synthes", "investigat",
    "benchmark", "compar", "evaluat", "assess", "audit", "deep dive", "diagnos",
    "forecast", "roi", "business case", "cost analysis", "quantif", "calculat",
    "insight", "trend",
)
REVIEW_VERBS = ("review", "read", "examine", "look at", "go through", "study")
SOURCE_PREPS = ("from", "based on", "using", "out of", "off of", "against")
ANALYTICAL_OBJECTS = (
    "report", "data", "dataset", "findings", "result", "dashboard", "metric",
    "number", "log", "telemetry", "usage", "spreadsheet", "chart", "figure", "source",
)
CODE_SIGNALS = (
    "debug", "refactor", " script", "parser", " api", " app ", "application",
    "automation", "pipeline", "deploy", "integrat", "function", " bug ", "codebase",
)
EMAIL_SIGNALS = ("email", "inbox", "reply", "e-mail")
MEETING_SIGNALS = ("meeting", "transcript", "recap", "standup", "minutes", "agenda")
DATA_EXT = {"xlsx", "xlsm", "xls", "csv", "tsv", "json", "parquet"}


def ext_of(name: str) -> str:
    n = str(name)
    return n.split(".")[-1].lower() if "." in n else ""


def norm(items) -> list:
    out = []
    for a in items or []:
        if isinstance(a, dict):
            name = a.get("name", "artifact")
            ext = (a.get("ext") or ext_of(name)).lower()
        else:
            name = str(a)
            ext = ext_of(name)
        if str(name).startswith("(input)"):
            continue
        item = {"name": name, "ext": ext}
        if isinstance(a, dict) and a.get("skills"):
            item["skills"] = [x for x in a["skills"] if x]
        out.append(item)
    return out


def goal_categories(goal: str) -> list:
    g = " " + (goal or "").lower() + " "
    cats = []
    has_object = any(o in g for o in ANALYTICAL_OBJECTS)
    if (
        any(v in g for v in ANALYSIS_SIGNALS)
        or (has_object and any(v in g for v in REVIEW_VERBS))
        or (has_object and any(p + " " in g for p in SOURCE_PREPS))
    ):
        cats.append("analysis")
    if any(v in g for v in CODE_SIGNALS):
        cats.append("code")
    if any(v in g for v in EMAIL_SIGNALS):
        cats.append("email")
    if any(v in g for v in MEETING_SIGNALS):
        cats.append("meeting")
    return cats


def load_roles_taxonomy():
    """16-role keyword taxonomy + default, ported from microsoft/What-I-Did-Copilot."""
    try:
        with open(_ROLES_PATH) as f:
            d = json.load(f)
        return d.get("roles", []), d.get("default", "Knowledge Worker")
    except Exception:
        return [], "Knowledge Worker"


def assign_roles(text: str, taxonomy: list, default: str) -> list:
    """Keyword FALLBACK — the professional roles a billing firm would charge for this work.
    Used only when the harvest LLM did not already tag professional_roles."""
    t = (text or "").lower()
    hits = []
    for entry in taxonomy:
        if entry["role"] not in hits and any(kw.lower() in t for kw in entry.get("keywords", [])):
            hits.append(entry["role"])
    return hits[:2] or [default]


def classify_session(s: dict) -> tuple:
    outputs = norm(s.get("outputs") if s.get("outputs") is not None else s.get("artifacts", []))
    inputs = norm(s.get("inputs", []))
    cats = []
    for a in outputs:
        c = EXT2CAT.get(a["ext"])
        if c and c not in cats:
            cats.append(c)
    for c in goal_categories(s.get("goal", "")):
        if c not in cats:
            cats.append(c)
    if (any(a["ext"] in DATA_EXT for a in inputs) or len(inputs) >= 3) and "analysis" not in cats:
        cats.append("analysis")
    if not cats:
        return (["general"], "conversational (no saved artifact)")
    cats.sort(key=lambda c: PRIORITY.index(c) if c in PRIORITY else 99)
    return (cats[:2], "" if outputs else "conversational (no saved artifact)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(inp: str, out: str, overrides_path: str = _OVERRIDES_PATH) -> None:
    d = json.load(open(inp))
    sessions = d.get("sessions", [])

    (vectors, idf), pillar_lookup, job_lookup = load_taxonomy()
    overrides = load_overrides(overrides_path)
    roles_tax, roles_default = load_roles_taxonomy()

    classified = []
    conv = 0

    for s in sessions:
        tasks, note = classify_session(s)
        if note:
            conv += 1
        inputs = norm(s.get("inputs", []))
        outputs = norm(
            s.get("outputs") if s.get("outputs") is not None else s.get("artifacts", [])
        )
        sid = s.get("id", "")
        primary = tasks[0] if tasks else "general"

        # Overrides may be a plain process label (str) OR a rich object carrying the
        # signed-in user's own {process, pillar, job, jtbd} derived live by map-my-work.
        ov = overrides.get(sid)
        if isinstance(ov, dict):
            process = ov.get("process")
        elif isinstance(ov, str):
            process = ov
        else:
            process = None
        if not process:
            process = "General Productivity" if primary == "general" else nearest(s.get("goal", ""), primary, vectors, idf)

        # Pillar / Job / JTBD: prefer values carried on a RICH override (personalized to whoever
        # runs the report); else resolve from the static taxonomy by label; else default.
        t_pillar, t_css = pillar_lookup.get(process, ("Transformation", "trans"))
        t_job, t_jtbd = job_lookup.get(process, ("Other", ""))
        if isinstance(ov, dict):
            value_pillar = ov.get("pillar") or t_pillar
            job = ov.get("job") or t_job
            jtbd = ov.get("jtbd") if ov.get("jtbd") is not None else t_jtbd
        else:
            value_pillar, job, jtbd = t_pillar, t_job, t_jtbd
        pillar_css = _PILLAR_CSS.get(value_pillar, t_css)

        rec = {
            "id": sid,
            "date": s.get("date", ""),
            "hour": int(s.get("hour", 12)),
            "goal": s.get("goal", "Cowork session"),
            "inputs": inputs,
            "outputs": outputs,
            "tasks": tasks,
            "process": process,
            "value_pillar": value_pillar,
            "pillar_css": pillar_css,
            "job": job,
            "jtbd": jtbd,
            "skills": [x for x in (s.get("skills") or []) if x],
            "professional_roles": ([x for x in (s.get("professional_roles") or []) if x]
                                   or assign_roles(
                                       " ".join([s.get("goal", "")] + tasks
                                                + [x for x in (s.get("skills") or [])]),
                                       roles_tax, roles_default)),
        }
        if s.get("exec_min") is not None:
            rec["exec_min"] = s["exec_min"]
        if s.get("code_loc") is not None:
            rec["code_loc"] = s["code_loc"]
        if s.get("runs") is not None:
            rec["runs"] = s["runs"]
        if note:
            rec["note"] = note
        classified.append(rec)

    payload = {"meta": d["meta"], "sessions": classified}
    json.dump(payload, open(out, "w"), indent=1)

    print(f"Classified {len(classified)} sessions ({conv} conversational/no-artifact).")
    proc = collections.Counter(r["process"] for r in classified)
    print("Processes:", ", ".join(f"{p} x{n}" for p, n in proc.most_common()))
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="working/cowork_raw.json")
    ap.add_argument("--out", default="working/cowork_sessions.json")
    ap.add_argument("--overrides", default=_OVERRIDES_PATH,
                    help="per-run overrides scratch file (default working/process_overrides.json)")
    a = ap.parse_args()
    main(a.inp, a.out, a.overrides)
