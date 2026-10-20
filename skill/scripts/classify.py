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
is per-run scratch and must NEVER live in the shippable scripts/ folder — that is how a
prior version leaked one user's session→process mappings to everyone who ran the package.

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
# They are NEVER read from the shippable scripts/ folder (that would leak one
# user's session→process mappings into anyone who runs the packaged skill).
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
    # Spreadsheets are CREATED content/data documents ("creating visuals, organizing
    # files") per the taxonomy table -> document. Analysis is assigned from goal text
    # ("synthesizing findings, comparing options, briefings"), never from a file type.
    "xlsx": "document", "xlsm": "document", "xls": "document",
    "csv": "document", "tsv": "document",
    # Write or debug code
    "html": "code", "htm": "code", "py": "code", "ps1": "code",
    "js": "code", "ts": "code", "sql": "code", "ipynb": "code",
    "sh": "code", "yaml": "code", "yml": "code",
    # Specialized workflows
    "zip": "code", "skill": "code",
}

PRIORITY = ["code", "analysis", "special", "document", "comms", "meeting", "email", "general"]

# ---------------------------------------------------------------------------
# Goal-text signal vocabulary — enriched from the Cowork usage taxonomy table
# (Description/Examples column). Each set below deliberately mirrors one row of
# that table so goal phrasing alone can place a session even when no telltale
# file extension was saved. Categories are UNCHANGED (still the 8 methodology
# keys); only the descriptive vocabulary that routes into them is tightened.
# ---------------------------------------------------------------------------

# Analysis & Research — searching org data, synthesizing findings, comparing
# options, explaining concepts, preparing briefings from multiple sources.
ANALYSIS_SIGNALS = (
    "analyz", "analyse", "analysis", "research", "synthes", "investigat",
    "benchmark", "compar", "evaluat", "assess", "audit", "deep dive", "diagnos",
    "forecast", "roi analysis", "roi report", "business case", "cost analysis", "quantif", "calculat",
    "insight", "trend",
    # taxonomy-derived additions:
    "briefing", "brief on", "search", "org data", "explain", "explaining",
    "concept", "option", "findings", "multiple source", "compile", "summariz",
)
REVIEW_VERBS = ("review", "read", "examine", "look at", "go through", "study")
SOURCE_PREPS = ("from", "based on", "using", "out of", "off of", "against")
ANALYTICAL_OBJECTS = (
    "report", "data", "dataset", "findings", "result", "dashboard", "metric",
    "number", "log", "telemetry", "usage", "spreadsheet", "chart", "figure", "source",
)
# Write or debug code — writing/debugging code, code review, script generation, code analysis.
CODE_SIGNALS = (
    "debug", "refactor", " script", "parser", " api", " app ", "application",
    "pipeline", "deploy", "integrat", "function", " bug ", "codebase",
    # taxonomy-derived additions:
    "code review", "script generation", "write code", "writing code",
    "code analysis", "coding",
)
# Email workflows — drafting/replying to emails, summarizing threads, triaging
# inbox, managing mail (Outlook-centered).
EMAIL_SIGNALS = (
    "email", "inbox", "reply to", "e-mail", "outlook",
    "draft email", "drafting email", "summarize thread", "mail rule",
    "triage inbox", "triage email",
)
# Communication workflows — the SAME ideas as Email, but centered on Microsoft
# Teams: synthesizing, posting, triaging and managing across Teams messages and
# channels (chats, channel posts, replies, announcements, mentions).
COMMS_SIGNALS = (
    "teams message", "teams chat", "teams channel", "chat message",
    "post to teams", "post to the channel", "post in teams", "channel message",
    "reply in teams", "teams thread", "summarize the channel", "summarize teams",
    "triage teams", "manage the channel", "communication rule",
    "notify the team", "announcement", "@mention", "mention me",
)
# Document & content creation — drafting docs/presentations, editing text,
# creating visuals, organizing files in OneDrive/SharePoint.
DOC_SIGNALS = (
    "presentation", "deck", "slide", "one-pager", "write-up", "writeup",
    "draft a doc", "drafting doc", "editing text", "edit text", "visual",
    "onedrive", "sharepoint", "organize file", "content creation", "newsletter",
)
# Specialized workflows — scheduling calendar events, managing task lists,
# multi-step M365 workflows, recurring prompts, and connectors (Dynamics 365,
# ADO Boards, Power BI, Fabric, ServiceNow, Salesforce, SAP).
SPECIAL_SIGNALS = (
    "workflow automation", "automat", "recurring prompt", "scheduled prompt",
    "schedule prompt", "task list", "multi-step", "multistep", "connector",
    "dynamics 365", "ado boards", "power bi", "fabric", "servicenow",
    "salesforce", " sap ", "schedule calendar", "scheduling calendar",
    "calendar event", "package", "bundle", "skill",
)
# Meeting workflows — preparing meeting briefings, recapping transcripts,
# extracting action items, calendar lookups.
MEETING_SIGNALS = (
    "meeting", "transcript", "recap", "standup", "minutes", "agenda",
    "action item", "calendar lookup", "meeting brief",
)
# General assistance & learning — kept as the low-priority fallback
# ("product guidance, discovering capabilities, troubleshooting, learning, Q&A").
DATA_EXT = {"xlsx", "xlsm", "xls", "csv", "tsv", "json", "parquet"}

# Genuine "content" deliverables — the forms that legitimately mean
# "Document & content creation" ONLY when one of them is a PRIMARY OUTPUT:
# a PowerPoint, a Word/PDF document, a Loop/OneNote page, or an image.
# Note: .md/.txt are deliberately EXCLUDED — a Markdown/plain-text file is just
# as often an automation byproduct (execution log, README, notes) as authored
# content, so it must not by itself put a session in the Document category.
# The `document` tag survives only if a session actually PRODUCED one of these.
CONTENT_EXT = {
    "pptx", "ppt",                                   # PowerPoint
    "docx", "doc", "pdf", "rtf", "odt",              # documents
    "loop", "one", "onetoc2",                        # Loop / OneNote
    "png", "jpg", "jpeg", "gif", "svg", "eps",       # images
    "webp", "heic", "bmp", "tif", "tiff",
    "xlsx", "xlsm", "xls", "csv", "tsv",             # spreadsheets = created content
}


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
        if isinstance(a, dict) and a.get("created"):
            item["created"] = a["created"]
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
    if any(v in g for v in SPECIAL_SIGNALS):
        cats.append("special")
    if any(v in g for v in DOC_SIGNALS):
        cats.append("document")
    if any(v in g for v in COMMS_SIGNALS):
        cats.append("comms")
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


# v45 — final-output routing for Email (Outlook) and Communication (Teams) workflows.
EMAIL_OUTPUT_ACTIONS = ("sendemail", "senddraftmessage", "createdraftmessage", "createreplydraft",
                        "createreplyalldraft", "createforwarddraft", "replytomessage",
                        "replyalltomessage", "forwardmessage")
INBOX_TRIAGE_ACTIONS = ("movemessage", "flagemail", "updatemessage", "createmailrule", "deletemessage")
EMAIL_GOAL_SIGNALS = EMAIL_SIGNALS + (" mail ", "e-mail", "draft a note to", "send a note", "inbox zero")
TEAMS_POST_ACTIONS = ("postchannelmessage", "postmessage", "replytochannelmessage", "updatechatmessage")
TEAMS_READ_ACTIONS = ("listchannelmessages", "listchatmessages", "getchannel", "getchatmessage", "listchats")
TEAMS_GOAL_SIGNALS = COMMS_SIGNALS + ("teams post", "channel post", "post to channel", "post my",
                                      "across channels", "across teams", "channels")


def final_output_category(s: dict, g: str):
    acts = [str(a).lower().split("__")[-1] for a in (s.get("actions") or [])]
    has = lambda keys: any(any(k == a or a.endswith(k) for k in keys) for a in acts)
    # 1. Email is the final output (or inbox triage) -> email, regardless of sources.
    if has(EMAIL_OUTPUT_ACTIONS) or has(INBOX_TRIAGE_ACTIONS) or any(k in g for k in EMAIL_GOAL_SIGNALS):
        return "email"
    # 2. Posts to Teams, or predominantly Teams-channel synthesis -> comms.
    teams_reads = sum(1 for a in acts if a in TEAMS_READ_ACTIONS)
    data_acts = [a for a in acts if a.startswith(("list", "get", "search", "read", "query"))]
    predominantly_teams = data_acts and teams_reads >= 2 and teams_reads * 2 >= len(data_acts)
    if has(TEAMS_POST_ACTIONS) or any(k in g for k in TEAMS_GOAL_SIGNALS) or predominantly_teams:
        return "comms"
    return None


# v46 — systems OUTSIDE Microsoft 365 (CRM / line-of-business apps reached via a
# connector or a third-party MCP server) -> Specialized workflows.
M365_INTERNAL_SERVERS = {"outlook", "outlook_calendar", "m365_teams", "m365_search", "m365_copilot",
                         "sharepoint_onedrive", "me_profile", "graph", "pbi_fabricaihub",
                         "core", "host", "memory", "appbuilder", "simple_browser", "powerplatform"}
CONNECTOR_ACTIONS = ("invokeconnectoroperation", "hydrateconnector", "createconnection")
EXTERNAL_GOAL_SIGNALS = (" crm", "salesforce", "dynamics 365", "d365", "servicenow", "service now",
                         "jira", "workday", "sap ", "hubspot", "zendesk", "github", "snowflake",
                         "databricks", "connector", " mcp", "third-party", "external system")


def touches_external_system(s: dict, g: str) -> bool:
    for a in (s.get("actions") or []):
        a = str(a).lower()
        if a.split("__")[-1] in CONNECTOR_ACTIONS:
            return True
        if a.startswith("mcp__"):
            server = a.split("__")[1]
            if server not in M365_INTERNAL_SERVERS:
                return True
    if any(str(x).lower() not in ("outlook", "teams", "excel", "word", "powerpoint", "onenote",
                                  "sharepoint", "onedrive", "loop", "planner", "calendar",
                                  "power bi", "copilot")
           for x in (s.get("apps_accessed") or [])):
        return True
    return any(k in g for k in EXTERNAL_GOAL_SIGNALS)


# v47 — FINAL OUTPUT FORMAT is the tie-breaker. When more than one category fits a
# session, the format of its final deliverable decides; PRIORITY is only the
# fallback when there is no deliverable (or its format maps to no candidate).
SUPPORTING_EXT = {"md", "txt", "json", "log", "lock", "png", "jpg", "jpeg", "gif", "svg"}


def final_output(outputs: list):
    """The session's final deliverable: latest-created primary file (supporting files
    such as notes, logs, screenshots are skipped unless they are all there is)."""
    if not outputs:
        return None
    primary = [a for a in outputs if a["ext"] not in SUPPORTING_EXT] or outputs
    if any(a.get("created") for a in primary):
        return max(primary, key=lambda a: a.get("created") or "")
    return primary[-1]


# v48 — RESEARCH vs CONTENT: "who did the thinking?"
# Research almost always ends in a deck or doc, so file type cannot separate it.
# A session is Analysis & Research when (a) the goal states research INTENT and
# (b) — when an action history exists — it shows real GATHERING. Otherwise the
# deck/doc is content creation and the final-output format decides as usual.
RESEARCH_INTENT = ("research", "compare", "comparison", "investigat", "evaluat", "synthes",
                   "analyz", "analyse", "analysis", "benchmark", "assess", "deep dive",
                   "explore options", "pros and cons", "landscape", "competitive",
                   "options for", "trade-off", "tradeoff", "which is better")
CONTENT_INTENT = ("draft", "design", "format", "refresh", "polish", "redesign", "visual",
                  "build a deck", "build deck", "slide", "template", "rewrite", "edit ",
                  "proofread", "convert", "update deck")
GATHER_ACTIONS = ("search", "web_fetch", "bing", "readfilecontent", "getmessage", "listmessages",
                  "listchannelmessages", "listchatmessages", "getmeetingtranscript", "querygraph",
                  "searchdrive", "executequery", "browser_actions")
RESEARCH_MIN_SOURCES = 3
RESEARCH_CONTAINER_CATS = ("document", "analysis", None)  # deck/doc/sheet, or no saved file


def research_evidence(s: dict, inputs: list):
    """True / False when an action history exists; None when it does not (goal decides)."""
    if s.get("sources_reviewed") is not None:
        return int(s["sources_reviewed"]) >= RESEARCH_MIN_SOURCES
    acts = s.get("actions")
    if acts is None:
        return None
    gathers = sum(1 for a in acts if any(k in str(a).lower() for k in GATHER_ACTIONS))
    data_inputs = [a for a in inputs if a["ext"] not in SUPPORTING_EXT]
    return gathers >= RESEARCH_MIN_SOURCES or len(data_inputs) >= RESEARCH_MIN_SOURCES


def is_research(s: dict, g: str, inputs: list, outputs: list) -> bool:
    if not any(k in g for k in RESEARCH_INTENT):
        return False
    fo = final_output(outputs)
    if (EXT2CAT.get(fo["ext"]) if fo else None) not in RESEARCH_CONTAINER_CATS:
        return False          # research that ends in an app/script: the build decides
    if any(k in g for k in CONTENT_INTENT) and not any(k in g for k in ("research", "investigat", "compare", "evaluat", "synthes")):
        return False          # mainly a content/design task that mentions analysis
    ev = research_evidence(s, inputs)
    return ev is not False    # evidence present, or no action history (goal decides)


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
    # Multi-source synthesis = analysis ("preparing briefings from multiple sources").
    # A single data-file input is NOT analysis on its own.
    if len(inputs) >= 3 and "analysis" not in cats:
        cats.append("analysis")
    # Primary-output gate for Document & content creation: keep `document` ONLY
    # when a genuine content artifact (deck / doc / PDF / Loop / image) was
    # actually PRODUCED. This stops an incidental .md/.txt log — or a chat-only
    # session with no saved deliverable — from landing in the Document bucket.
    if "document" in cats and not any(a["ext"] in CONTENT_EXT for a in outputs):
        cats.remove("document")
    g = " " + (s.get("goal", "") or "").lower() + " "
    # v45 GUIDING RULE — attribute the session to its FINAL OUTPUT.
    #  1. Ends in an email (send / draft / reply / forward) or is inbox triage
    #     -> Email workflows, even if it synthesized Teams, channels or meetings.
    #  2. Else posts to Teams, or predominantly synthesizes across Teams
    #     channels/chats -> Communication workflows.
    #  3. Else skill build -> code.
    #  3b. Else research intent + gathering evidence -> analysis (v48).
    #  4. Else candidates (outside-M365 system -> special, goal text, file types);
    #     a TIE is broken by the FINAL OUTPUT FORMAT, then PRIORITY.
    final = final_output_category(s, g)
    if final:
        return ([final], "" if outputs else "conversational (no saved artifact)")
    # v46: touches a system outside M365 (CRM etc. via connector / MCP) -> special
    # is a CANDIDATE (v47): if the session also produced a deliverable of another
    # type, the final output format breaks the tie.
    if touches_external_system(s, g) and "special" not in cats:
        cats.append("special")
    # v44: skill creation / attachment / packaging / install / quality review is
    # BUILD work -> "Write or debug code" (it was splitting into analysis + special).
    is_skill_build = (" skill" in g or " plugin" in g
                      or any(a["ext"] in ("zip", "skill") for a in inputs + outputs))
    if is_skill_build:
        return (["code"], "" if outputs else "conversational (no saved artifact)")
    # v48: research intent + gathering evidence -> Analysis & Research, even when the
    # findings land in a deck or doc (the deck is the container, not the work).
    if is_research(s, g, inputs, outputs):
        return (["analysis"], "" if outputs else "conversational (no saved artifact)")
    # Research intent WITHOUT the evidence (or a content task) is not analysis.
    if "analysis" in cats and (outputs and any(EXT2CAT.get(a["ext"]) == "document" for a in outputs)):
        cats.remove("analysis")
    if not cats:
        return (["general"], "conversational (no saved artifact)")
    # v47: tie -> the final output's format decides.
    if len(cats) > 1:
        fo = final_output(outputs)
        fo_cat = EXT2CAT.get(fo["ext"]) if fo else None
        if fo_cat in cats:
            return ([fo_cat], "")
    cats.sort(key=lambda c: PRIORITY.index(c) if c in PRIORITY else 99)
    # v44: ONE category per session. Time saved is attributed to the primary
    # category only, so no session is listed (or counted) under two categories.
    return (cats[:1], "" if outputs else "conversational (no saved artifact)")


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
        for _ev in ("request", "actions", "apps_accessed", "sources_reviewed"):
            if s.get(_ev) is not None:
                rec[_ev] = s[_ev]
        if s.get("cowork_fit_review") is not None:
            rec["cowork_fit_review"] = s["cowork_fit_review"]
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
