#!/usr/bin/env python3
"""Cowork ROI — mine the CURRENT session's transcript for real telemetry.

OneDrive only persists file artifacts, so chat-only sessions and true run-time are
invisible to an artifact-only harvest. The live session, however, has its own
transcript (Copilot events.jsonl, or legacy Claude JSONL). This script reads that
transcript and emits a compact telemetry record:

  * session id, title/goal
  * start/end timestamps and measured exec_min (REAL wall-clock, not file mtime)
  * tool-call count, breakdown by tool, distinct tool count
  * user/assistant turn counts
  * artifacts (output paths / artifact-tool arguments; legacy also scans output/)
  * produced_artifact flag  -> lets the report COUNT chat-only sessions

Intended use: run at the end of a session and APPEND the record to a durable log in
the user folder (/mnt/user-config/.claude/cowork-session-telemetry.json). Future
ROI reports read that log to (a) include sessions that produced no file, and (b) use measured run
time + tool intensity for leverage instead of guessing from file timestamps.

Usage: python mine_session.py --out working/session_telemetry.json
       (auto-detects the transcript; pass --transcript to override)
"""
import json, argparse, glob, os, datetime, re

def find_transcript():
    pats=["/mnt/workspace/.copilot-state/*/session-state/*/events.jsonl",
          "/mnt/workspace/agent-state/projects/*/*.jsonl",
          os.path.expanduser("~/.claude/projects/*/*.jsonl")]
    hits=[]
    for p in pats: hits+=glob.glob(p)
    # newest by mtime
    return max(hits, key=os.path.getmtime) if hits else None

def find_title():
    try:
        with open("/mnt/workspace/.session-metadata.json",encoding="utf-8") as f:
            meta=json.load(f)
        return meta.get("title") or "Cowork session"
    except Exception:
        return "Cowork session"

def parse_ts(s):
    try:
        d=datetime.datetime.fromisoformat(s.replace("Z","+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)
    except Exception: return None

def normalize_tool_name(name):
    """Keep legacy names; map server-Tool to the existing MCP matching vocabulary."""
    if not isinstance(name,str) or not name: return "?"
    if name.startswith("mcp__"): return name
    server, sep, tool=name.partition("-")
    return f"mcp__{server}__{tool}" if sep and server and tool else name

def as_dict(value):
    """Tool arguments may be an object or a serialized JSON object; never execute them."""
    if isinstance(value,str):
        try: value=json.loads(value)
        except (ValueError,TypeError): return {}
    return value if isinstance(value,dict) else {}

def event_tool_name(data, field="toolName"):
    name=data.get(field)
    if not name and data.get("mcpServerName") and data.get("mcpToolName"):
        name=f"{data['mcpServerName']}-{data['mcpToolName']}"
    return normalize_tool_name(name)

def prompt_title(content):
    if not isinstance(content,str): return "Cowork session"
    text=re.sub(r"<(attached_files|current_datetime)\b[^>]*>.*?</\1\s*>",
                "",content,flags=re.IGNORECASE|re.DOTALL).strip()
    return text.splitlines()[0].strip()[:80] if text else "Cowork session"

def output_artifact(path, artifacts):
    if isinstance(path,dict):
        path=path.get("path") or path.get("filePath") or path.get("file_path")
    if not isinstance(path,str) or not path.strip(): return
    path=os.path.normpath(path.replace("\\","/"))
    if path.startswith("output/") or "/output/" in path:
        artifacts.add(os.path.basename(path))

def artifact_arguments(name, arguments, artifacts):
    """Only published output/live destinations count, not user/working skill edits."""
    if name not in {"mcp__host__CreateArtifact","mcp__host__CopyArtifact"}: return
    args=as_dict(arguments)
    path=args.get("destination") if name.endswith("__CopyArtifact") else args.get("path")
    if not isinstance(path,str) or not path.strip() or args.get("recursive"): return
    surface=args.get("surface")
    if surface in {"output","live"}:
        artifacts.add(os.path.basename(path.replace("\\","/")))
    elif not surface:
        output_artifact(path,artifacts)

def main(transcript, out, log=None):
    transcript=transcript or find_transcript()
    if not transcript or not os.path.exists(transcript):
        print("No transcript found"); return
    sid=os.path.splitext(os.path.basename(transcript))[0]
    tools={}; ntool=0; nuser=0; nasst=0; ts=[]; artifacts=set(); action_seq=[]
    event_format=False; event_sid=None; title=None
    event_types={"session.start","session.resume","session.shutdown","user.message",
                 "assistant.message","tool.execution_start","tool.execution_complete"}
    with open(transcript,encoding="utf-8") as stream:
        for ln in stream:
            try: o=json.loads(ln)
            except (ValueError,TypeError): continue  # tolerate an incomplete live tail
            if not isinstance(o,dict): continue
            t=o.get("type")
            d=parse_ts(o.get("timestamp"))
            if d: ts.append(d)  # every event participates in the wall-clock span
            if not isinstance(t,str): continue
            if t in event_types:
                event_format=True
                data=as_dict(o.get("data"))
                if t=="session.start" and not event_sid:
                    value=data.get("sessionId")
                    if isinstance(value,str) and value: event_sid=value
                elif t=="user.message":
                    nuser+=1
                    if nuser==1: title=prompt_title(data.get("content"))
                elif t=="assistant.message":
                    nasst+=1
                    requests=data.get("toolRequests") or []
                    if isinstance(requests,list):
                        for req in requests:
                            if isinstance(req,dict):
                                artifact_arguments(event_tool_name(req,"name"),
                                                   req.get("arguments"),artifacts)
                elif t=="tool.execution_start":
                    nm=event_tool_name(data)
                    ntool+=1; tools[nm]=tools.get(nm,0)+1; action_seq.append(nm)
                    artifact_arguments(nm,data.get("arguments"),artifacts)
                elif t=="session.shutdown":
                    changes=as_dict(data.get("codeChanges")).get("filesModified") or []
                    if isinstance(changes,list):
                        for path in changes: output_artifact(path,artifacts)
                # Requests and completions do not double-count actual tool starts.
                continue
            # Legacy Claude JSONL remains supported.
            if t=="user": nuser+=1
            elif t=="assistant": nasst+=1
            content=as_dict(o.get("message")).get("content")
            if isinstance(content,list):
                for c in content:
                    if not isinstance(c,dict) or c.get("type")!="tool_use": continue
                    ntool+=1; nm=normalize_tool_name(c.get("name"))
                    tools[nm]=tools.get(nm,0)+1; action_seq.append(nm)
                    inp=as_dict(c.get("input"))
                    output_artifact(inp.get("file_path") or inp.get("out"),artifacts)
                    artifact_arguments(nm,inp,artifacts)
    if event_format:
        sid=event_sid or os.path.basename(os.path.dirname(os.path.abspath(transcript)))
        title=title or "Cowork session"
    else:
        title=find_title()
        # Retain the legacy workspace scan; events use transcript evidence only so
        # an unrelated existing output cannot turn a chat-only session into a file task.
        for f in glob.glob("/mnt/workspace/output/**/*", recursive=True):
            if os.path.isfile(f): artifacts.add(os.path.basename(f))

    exec_min=None
    if len(ts)>=2:
        exec_min=round((max(ts)-min(ts)).total_seconds()/60,1)
    # ---- runs per category (the deck's unit), from tool-chains ----
    # Surface-based categories (email/comms/meeting) each get their OWN bucket so artifact-free
    # triage/recap sessions credit the RIGHT category instead of being swallowed by the analysis
    # bucket or dropping out of the harvest entirely. compute.py trusts the telemetry `runs` dict
    # verbatim, so any category not emitted here is starved to zero once telemetry exists.
    #   code run     ~ write->test->debug chain      ~ 6 code-edit actions/run   (band 30/56/96)
    #   analysis run ~ 5-phase cognitive chain        ~ 5 research-tool calls/run (band 30/67/92)
    #   email run    ~ one reply/triage cycle         ~ 4 Outlook-mail calls/run  (band 3/7/12)
    #   comms run    ~ one Teams synth/triage/post    ~ 4 Teams calls/run         (band 2/4/11)
    #   meeting run  ~ one recap/prep/calendar lookup ~ 3 transcript/cal calls/run(band 12/31/43)
    _CODE={"Edit","Write","MultiEdit","NotebookEdit","apply_patch","edit","write",
           "mcp__functions__apply_patch"}
    # Outlook MAIL tools = email workflow (drafting/replying/triaging), NOT generic research.
    _EMAIL={"mcp__outlook__ListMessages","mcp__outlook__GetMessage","mcp__outlook__SendMail",
        "mcp__outlook__CreateDraft","mcp__outlook__ReplyToMessage","mcp__outlook__CreateMessage",
        "mcp__outlook__SendMessage","mcp__outlook__MoveMessage","mcp__outlook__UpdateMessage"}
    # Microsoft Teams tools = communication workflow (synthesize/post/triage chats & channels).
    _TEAMS={"mcp__m365_teams__ListChats","mcp__m365_teams__ListTeams","mcp__m365_teams__ListChannels",
        "mcp__m365_teams__ListChannelMessages","mcp__m365_teams__ListChatMessages",
        "mcp__m365_teams__SendChatMessage","mcp__m365_teams__SendChannelMessage",
        "mcp__m365_teams__PostMessage","mcp__m365_teams__ReplyToChannelMessage"}
    # Meeting workflow = recap transcripts, prep briefings, calendar lookups (NOT generic research).
    _MEETING={"mcp__graph__GetMyRecentTranscripts","mcp__outlook_calendar__ListCalendarView",
        "mcp__graph__GetMeetingTranscript","mcp__graph__ListMeetingTranscripts",
        "mcp__outlook_calendar__GetEvent","mcp__outlook_calendar__ListEvents"}
    _RESEARCH={"mcp__m365_search__SearchM365","mcp__core__web_search","mcp__core__web_fetch",
        "mcp__host__web_search","mcp__host__web_fetch","mcp__host__bing_search",
        "web_search","web_fetch",
        "mcp__graph__QueryGraph",
        "mcp__sharepoint_onedrive__SearchDrive","mcp__sharepoint_onedrive__ReadFileContent"}
    _ce=sum(v for k,v in tools.items() if k in _CODE)
    _rs=sum(v for k,v in tools.items() if k in _RESEARCH)
    # Match each explicit set plus its server-name variants by prefix, so tool-name drift still
    # routes to the right category. Order matters: calendar prefix is checked before mail because
    # mcp__outlook_calendar__ also starts with mcp__outlook_ (mail is mcp__outlook__, double-underscore).
    _mt=sum(v for k,v in tools.items()
            if k in _MEETING or k.startswith("mcp__outlook_calendar__"))
    _em=sum(v for k,v in tools.items()
            if k in _EMAIL or (k.startswith("mcp__outlook__") and k not in _MEETING))
    _cm=sum(v for k,v in tools.items()
            if k in _TEAMS or k.startswith("mcp__m365_teams__"))
    runs_est={}
    if _ce: runs_est["code"]=max(1,round(_ce/6))
    if _rs: runs_est["analysis"]=max(1,round(_rs/5))
    if _em: runs_est["email"]=max(1,round(_em/4))
    if _cm: runs_est["comms"]=max(1,round(_cm/4))
    if _mt: runs_est["meeting"]=max(1,round(_mt/3))

    # ---- multi-app evidence (which apps the action trace PROVES were touched) ----
    # A prefix map turns raw tool names into the apps actually accessed. Order matters:
    # the calendar prefix is tested BEFORE the mail prefix (both share the mcp__outlook_ stem).
    TOOL_APP = [("mcp__outlook_calendar__", "Teams"),          # calendar BEFORE mail
                ("mcp__graph__GetMyRecentTranscripts", "Teams"),
                ("mcp__graph__GetMeetingTranscript", "Teams"),
                ("mcp__graph__ListMeetingTranscripts", "Teams"),
                ("mcp__m365_teams__", "Teams"),
                ("mcp__outlook__", "Outlook"),
                ("mcp__excel", "Excel"), ("mcp__word", "Word"),
                ("mcp__powerpoint", "PowerPoint")]
    _SOURCE_PREFIXES = ("mcp__m365_search__", "mcp__core__web_search", "mcp__core__web_fetch",
                        "mcp__host__web_search", "mcp__host__web_fetch", "mcp__host__bing_search",
                        "web_search", "web_fetch",
                        "mcp__graph__QueryGraph", "mcp__sharepoint_onedrive__SearchDrive",
                        "mcp__sharepoint_onedrive__ReadFileContent")
    apps=set(); sources=0
    for k,v in tools.items():
        for pre,app in TOOL_APP:
            if k==pre or k.startswith(pre):
                apps.add(app); break
        if any(k==p or k.startswith(p) for p in _SOURCE_PREFIXES):
            sources+=v
    # distinct action names in first-seen order (the deduped workflow trace)
    _seen=set()
    actions=[a for a in action_seq if not (a in _seen or _seen.add(a))]

    rec={
        "id": sid[:8],
        "session_id": sid,
        "goal": title,
        "start": min(ts).isoformat() if ts else None,
        "end": max(ts).isoformat() if ts else None,
        "exec_min": exec_min,
        "tool_calls": ntool,
        "tools_by_name": dict(sorted(tools.items(), key=lambda x:-x[1])),
        "distinct_tools": len(tools),
        "runs": runs_est,
        "turns": {"user": nuser, "assistant": nasst},
        "artifacts": sorted(artifacts),
        "produced_artifact": bool(artifacts),
        # -- evidence fields: emitted here because a transcript WAS parsed (the action
        #    trace is available). Downstream, the ABSENCE of these fields on a session
        #    is what flips grading to "Insufficient evidence" instead of a confident Low.
        "request": title,
        "actions": actions,
        "apps_accessed": sorted(apps),
        "sources_reviewed": sources,
        "source": "session-transcript",
    }
    with open(out,"w",encoding="utf-8") as f:
        json.dump(rec,f,indent=1)
    if log:
        # Upsert this session into a durable log (keyed by 8-char id, latest wins) so
        # chat-only / folder-less sessions are still counted by future ROI reports.
        try:
            try:
                with open(log) as f: db=json.load(f)
            except Exception: db={}
            if not isinstance(db, dict): db={}
            db[rec["id"]] = rec
            os.makedirs(os.path.dirname(log) or ".", exist_ok=True)
            tmp=log+".tmp"
            with open(tmp,"w") as f: json.dump(db, f, indent=1)
            os.replace(tmp, log)
            print(f"telemetry logged -> {log} ({len(db)} sessions)")
        except Exception as e:
            print("telemetry log skipped:", e)
    print(f"Session {rec['id']}: exec={exec_min} min, {ntool} tool calls "
          f"({len(tools)} distinct), {len(artifacts)} artifact(s), "
          f"{'produced files' if artifacts else 'CHAT-ONLY'}.")
    print("wrote", out)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--transcript", default=None)
    ap.add_argument("--out", default="working/session_telemetry.json")
    ap.add_argument("--log", default=None, help="durable telemetry log (JSON dict) to upsert into")
    a=ap.parse_args(); main(a.transcript,a.out,a.log)
