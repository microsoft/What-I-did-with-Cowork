#!/usr/bin/env python3
"""Cowork ROI — mine the CURRENT session's transcript for real telemetry.

OneDrive only persists file artifacts, so chat-only sessions and true run-time are
invisible to an artifact-only harvest. The live session, however, has its own
transcript (a JSONL under agent-state) plus per-server MCP logs. This script reads
that transcript and emits a compact telemetry record:

  * session id, title/goal
  * start/end timestamps and measured exec_min (REAL wall-clock, not file mtime)
  * tool-call count, breakdown by tool, distinct tool count
  * user/assistant turn counts
  * artifacts written (from Write / file-producing tool calls + output/ scan)
  * produced_artifact flag  -> lets the report COUNT chat-only sessions

Intended use: run at the end of a session and APPEND the record to a durable log in
OneDrive (e.g. Documents/Cowork/sessions/_telemetry.jsonl). Future ROI reports read
that log to (a) include sessions that produced no file, and (b) use measured run
time + tool intensity for leverage instead of guessing from file timestamps.

Usage: python mine_session.py --out working/session_telemetry.json
       (auto-detects the transcript; pass --transcript to override)
"""
import json, argparse, glob, os, datetime

def find_transcript():
    pats=["/mnt/workspace/agent-state/projects/*/*.jsonl",
          os.path.expanduser("~/.claude/projects/*/*.jsonl")]
    hits=[]
    for p in pats: hits+=glob.glob(p)
    # newest by mtime
    return max(hits, key=os.path.getmtime) if hits else None

def find_title():
    try:
        meta=json.load(open("/mnt/workspace/.session-metadata.json"))
        return meta.get("title") or "Cowork session"
    except Exception:
        return "Cowork session"

def parse_ts(s):
    try: return datetime.datetime.fromisoformat(s.replace("Z","+00:00"))
    except Exception: return None

def main(transcript, out, log=None):
    transcript=transcript or find_transcript()
    if not transcript or not os.path.exists(transcript):
        print("No transcript found"); return
    sid=os.path.splitext(os.path.basename(transcript))[0]
    tools={}; ntool=0; nuser=0; nasst=0; ts=[]; artifacts=set()
    for ln in open(transcript):
        try: o=json.loads(ln)
        except Exception: continue
        t=o.get("type")
        if t=="user": nuser+=1
        elif t=="assistant": nasst+=1
        if o.get("timestamp"):
            d=parse_ts(o["timestamp"])
            if d: ts.append(d)
        msg=o.get("message",{}) or {}
        content=msg.get("content")
        if isinstance(content,list):
            for c in content:
                if not isinstance(c,dict): continue
                if c.get("type")=="tool_use":
                    ntool+=1; nm=c.get("name","?"); tools[nm]=tools.get(nm,0)+1
                    inp=c.get("input",{}) or {}
                    fp=inp.get("file_path") or inp.get("out") or ""
                    if isinstance(fp,str) and "/output/" in fp:
                        artifacts.add(os.path.basename(fp))
    # also scan the workspace output dir
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
    _CODE={"Edit","Write","MultiEdit","NotebookEdit"}
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
        "mcp__outlook_calendar__GetEvent","mcp__outlook_calendar__ListEvents"}
    _RESEARCH={"mcp__m365_search__SearchM365","mcp__core__web_search","mcp__core__web_fetch",
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

    rec={
        "id": sid[:8],
        "session_id": sid,
        "goal": find_title(),
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
        "source": "session-transcript",
    }
    json.dump(rec, open(out,"w"), indent=1)
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
