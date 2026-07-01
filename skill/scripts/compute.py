#!/usr/bin/env python3
"""Cowork ROI — compute the methodology payload from a classified-sessions JSON.

v5 (artifact-scaled speed multiplier). The skill harvests the signed-in user's
own Cowork sessions, classifies each into run tasks AND records the distinct
input artifacts analyzed and output artifacts produced. This script applies a
two-clock model:

  Expert clock (unassisted)  = research-anchored analysis/general bands (v4)
                               + per-input reading/triage time
                               + per-output authoring time
  Assisted clock (your time) = a small fixed prompt/setup cost
                               + a per-artifact handling cost (modeled, not measured)

  Speed multiplier            = Expert clock / Assisted clock
  Professional-services value = Expert-clock hours x hourly rate

There is no ROI / seat-cost figure (credit & seat consumption is unavailable),
so value is framed as the professional-services equivalent at the selected rate.

INPUT (working/cowork_sessions.json):
{
  "meta": {"user","email","generated",
           "window":{"from","to","label","months"}, "hourly_rate":72},
  "sessions": [
     {"id","date","hour","goal",
      "inputs":  [{"name":"report-1.pdf","ext":"pdf"}, ...],   # analyzed
      "outputs": [{"name":"deck.pptx","ext":"pptx"}, ...],  # produced
      "tasks":   ["analysis","document"]},                  # category keys
     ...
  ]
}
Usage: python compute.py --in working/cowork_sessions.json --out working/cowork_roi_data.json
"""
import json, argparse, collections

# v4 research-anchored bands (min saved per run task): (low, typical, high, label)
# Updated 2026-06-19 from Cowork_Methodology_Walkthrough 0605.pptx (slide 3 / slide 12):
#   Analysis & Research typical: 71 → 67  (Stanford-WB basket mean 335÷5=67)
#   Meeting workflows high:      45 → 43  (slide 7)
#   Communication workflows high: 6 → 11  (slide 8)
CATS = {
 "analysis":(30,67,92,"Analysis & Research"),
 "document":(12,24,42,"Document & content creation"),
 "email":(3,7,12,"Email workflows"),
 "meeting":(12,31,43,"Meeting workflows"),
 "comms":(2,4,11,"Communication workflows"),
 "special":(10,25,40,"Specialized workflows"),
 "code":(30,56,96,"Write or debug code"),
 "general":(2,5,8,"General assistance / Other"),
}
INTENT={"analysis":"Researching","document":"Building","email":"Communicating",
        "meeting":"Coordinating","comms":"Communicating","special":"Building",
        "code":"Building","general":"Researching"}
# Roles are no longer a fixed category map — they come from each session's professional_roles
# (LLM-tagged "roles a billing firm would charge"; keyword fallback in classify.py).

# ---- model constants ----
# Expert clock = sum of research-anchored CATS bands per task (no read/author heuristics).
# Assisted clock is a small MODELED hands-on estimate (OneDrive can't measure keystroke time).
ASSIST_FIXED   = 8    # min fixed prompt/setup per session (modeled)
ASSIST_PER_ART = 2    # min hands-on handling per artifact (in or out) — modeled
IMG_EXT = {"png","jpg","jpeg","gif","bmp","webp","heic"}
DATA_CAT_EXT = {"xlsx","xls","csv"}                                  # -> Analysis & Research
CODE_CAT_EXT = {"py","js","ps1","ipynb","sh","ts","go","sql"}        # -> Write or debug code
APP_CAT_EXT  = {"html","htm"}                                        # -> Specialized workflows

# friendly artifact-type labels for the Analyzed -> Produced section
TYPE_LABEL = {
 "pdf":"PDF","doc":"Document","docx":"Document","ppt":"Deck","pptx":"Deck",
 "xls":"Spreadsheet","xlsx":"Spreadsheet","csv":"Spreadsheet",
 "html":"Web page","htm":"Web page",
 "png":"Image","jpg":"Image","jpeg":"Image","gif":"Image","bmp":"Image","webp":"Image","heic":"Image",
 "md":"Text","txt":"Text",
 "py":"Script","js":"Script","ps1":"Script","sh":"Script","ts":"Script","go":"Script","sql":"Query","ipynb":"Notebook",
}
def type_label(ext): return TYPE_LABEL.get(ext.lower(),"File")

# Per-artifact AUTHORING anchor (min a professional would spend producing ONE deliverable),
# by friendly type — (low, typical, high). Scales the expert clock with the NUMBER of artifacts.
# Images use a deliberately small anchor so auto-generated QA screenshots/variants don't inflate.
AUTHOR_BAND = {
 "Deck":(30,45,60),"Document":(25,40,55),"Spreadsheet":(25,35,50),
 "Web page":(25,35,50),"Script":(25,35,50),"Notebook":(25,35,50),
 "Query":(15,25,35),"Image":(2,5,10),"Text":(10,20,30),"File":(15,30,45),
}
# Per-input READ/triage anchor (min to analyze ONE source) — scales with analyses performed.
READ_DOC=(8,12,18); READ_IMG=(2,5,8)
# Per LOGIC-LINE-OF-CODE anchor (min an unassisted professional spends per finished, reviewed SLOC).
# (low, typical, high) = 40 / 30 / 20 LOC per hour — industry range for production-quality code.
LOC_MIN=(1.5,2.0,3.0)
# Only SUBSTANTIVE produced artifacts earn an authoring anchor — Word docs, decks, spreadsheets, written
# specs. Code is valued separately by its logic LOC; generated web/HTML output, images, and QA/variant
# files are TRIVIAL and earn nothing (per user direction: ignore trivial artifacts).
SUBSTANTIVE_AUTHOR={"Document","Deck","Spreadsheet","Text"}
# Task bands that still apply on top (the analysis/coordination "thinking"); code & special are valued
# via LOC / authoring, so their flat bands are dropped to avoid double-counting.
KEEP_BANDS={"analysis","document","email","meeting","comms","general"}
READ_SOURCE_EXT=DATA_CAT_EXT|{"pdf","docx","doc","pptx","ppt"}
import re
REVISION_WEIGHT=0.3   # later versions of the SAME artifact = revisions, not fresh authoring
_VER_TAIL=re.compile(r'[-_ ]?v?\d+(\.\d+)?$')
_VER_WORD=re.compile(r'[-_ ](v\d+|\d+d|\d+day|sample|draft|final|copy|mockup|backup|old|new)$')
def art_base(name):
    """Normalize an artifact name to its version-independent base so v6/v11/v17 (or report-v1/v2/final)
    collapse to ONE artifact — used so iterative versions aren't counted as distinct deliverables."""
    n=str(name).lower().rsplit('.',1)[0]
    for _ in range(4):
        n2=_VER_WORD.sub('',_VER_TAIL.sub('',n))
        if n2==n: break
        n=n2
    return n.strip('-_ ') or str(name).lower()

def hrs(m): return round(m/60,1)
def round_to_total(parts_min, total_hours):
    """Round each part (minutes) to 1-decimal hours so the parts sum EXACTLY to total_hours."""
    import math
    tt=round(total_hours*10)
    raw=[(m/60.0)*10 for m in parts_min]
    fl=[math.floor(x) for x in raw]
    rem=int(tt-sum(fl))
    order=sorted(range(len(raw)), key=lambda i: raw[i]-fl[i], reverse=True)
    for i in range(max(rem,0)): fl[order[i%len(order)]]+=1
    return [round(t/10.0,1) for t in fl]
def out_cat(ext):
    e=ext.lower()
    if e in DATA_CAT_EXT: return "Analysis & Research"
    if e in CODE_CAT_EXT: return "Write or debug code"
    if e in APP_CAT_EXT:  return "Specialized workflows"
    return "Document & content creation"

def _ext(a):
    if isinstance(a,dict): return (a.get("ext") or a.get("name","").split(".")[-1] or "file").lower()
    s=str(a); return (s.split(".")[-1] if "." in s else "file").lower()
def _name(a):
    return a.get("name","artifact") if isinstance(a,dict) else str(a)

def session_expert(runs, idx):
    """Deck-anchored expert clock (Cowork Time-Savings Methodology): the SUM over RUNS of each run's
    category band — minutes SAVED per run. Each band already sums the activity-instance chain inside ONE
    run (e.g. code 56 = write+test+debug = 18min x 3 steps; doc 24 = 6.1min x 4 instances), so we count
    RUNS and multiply by the band — never per-LOC, never a per-artifact authoring add-on (that would
    double-count the chain). `runs` is {category: run_count}. idx: 0=low, 1=typical, 2=high."""
    return sum(n * CATS.get(c, CATS["general"])[idx] for c, n in (runs or {}).items())

import os
COST_LOG = "/mnt/user-config/.claude/cowork-session-costs.json"
def load_cost_lookup():
    """Map session id (full UUID and 8-char prefix) -> actual $ cost captured by the
    statusLine hook. Empty if the log doesn't exist yet (older sessions have no cost)."""
    try:
        with open(COST_LOG) as f:
            d=json.load(f)
        out={}
        for k,v in (d.items() if isinstance(d,dict) else []):
            amt = v.get("total_cost_usd") if isinstance(v,dict) else None
            if isinstance(amt,(int,float)):
                out[k]=amt; out[k[:8]]=amt
        return out
    except Exception:
        return {}

CREDITS_LOG = "/mnt/user-config/.claude/cowork-session-credits.json"
def load_credits_lookup():
    """Map session id (full + 8-char) -> real AiCredits from /cost readings (durable ledger)."""
    try:
        with open(CREDITS_LOG) as f:
            d=json.load(f)
        out={}
        for k,v in (d.get("sessions",{}) or {}).items():
            amt = v.get("credits") if isinstance(v,dict) else v
            if isinstance(amt,(int,float)):
                out[k]=amt; out[k[:8]]=amt
        return out
    except Exception:
        return {}

def main(inp,out):
    d=json.load(open(inp)); meta=d["meta"]; sessions=d["sessions"]
    rate=meta.get("hourly_rate",72)
    win=meta.get("window",{"label":"Window","from":"","to":"","months":1})
    cost_lookup=load_cost_lookup()
    credits_lookup=load_credits_lookup()

    tasks=[]; goals=[]; afiles=[]; artifacts=[]
    catmin=collections.Counter(); ccount=collections.Counter()
    icount=collections.Counter(); rmin=collections.Counter()
    heat=collections.Counter(); active=set()
    exp_t=exp_l=exp_h=0; assist_tot=0; conv=0
    in_types=collections.Counter(); out_types=collections.Counter()
    proc_count=collections.Counter(); proc_min=collections.Counter()
    skillmin=collections.Counter(); skillsessions=collections.Counter(); cauthored=collections.Counter()
    skilldeliv=collections.Counter()    # how many deliverables a skill helped produce
    deliverables=[]                     # per-output: name, type, skills, hours, value
    inv=collections.defaultdict(list)   # artifact inventory: type label -> [items]

    for s in sessions:
        sid=s["id"]; date=s["date"]; hour=int(s.get("hour",12))
        goal=s.get("goal","Cowork session")
        process=s.get("process","General Productivity")
        cats=s.get("tasks",[]) or ["general"]
        inputs=s.get("inputs",[]) or []
        outputs=s.get("outputs",[]) or []
        active.add(date)

        # RUNS per category (the deck's unit). Explicit telemetry-grounded counts when harvested;
        # else fall back to one run per classified task.
        runs = s.get("runs") or {c:1 for c in cats}
        runs = {(c if c in CATS else "general"):int(n) for c,n in runs.items() if int(n)>0}
        if not runs: runs={"general":1}
        e_t=session_expert(runs,1)
        e_l=session_expert(runs,0)
        e_h=session_expert(runs,2)
        assist=max(ASSIST_FIXED + ASSIST_PER_ART*(len(inputs)+len(outputs)), 4)
        exp_t+=e_t; exp_l+=e_l; exp_h+=e_h; assist_tot+=assist
        spd = round(e_t/assist,1) if assist else 0
        proc_count[process]+=1; proc_min[process]+=e_t
        # roll up role-hours: split the session's expert time across the professional roles a
        # billing firm would charge for this work (LLM-tagged; keyword fallback in classify.py)
        prof_roles = [r for r in (s.get("professional_roles") or []) if r]
        if prof_roles:
            rshare = e_t / len(prof_roles)
            for rname in prof_roles:
                rmin[rname] += rshare

        # expert clock = Σ RUNS × the research-anchored band per category (deck methodology)
        for c,n in runs.items():
            tasks.append({"session":sid,"category":c,"runs":n})
            ccount[c]+=n; icount[INTENT.get(c,"Researching")]+=n
            catmin[CATS.get(c,CATS["general"])[3]] += n*CATS.get(c,CATS["general"])[1]
        for a in inputs:
            in_types[type_label(_ext(a))] += 1

        # ---- per-deliverable hours: an equal share of the session's research-anchored
        #      expert time, so deliverables sum back to e_t. ----
        dmin = (e_t / len(outputs)) if outputs else 0
        sess_skills=[x for x in (s.get("skills") or []) if x]   # fallback for outputs w/o own tags
        for a in outputs:
            cauthored[out_cat(_ext(a))] += 1
            out_types[type_label(_ext(a))] += 1
            afiles.append(_name(a)); artifacts.append({"session":sid,"name":_name(a),"ext":_ext(a),"date":date})
            inv[type_label(_ext(a))].append({"name":_name(a),"date":date,"ext":_ext(a)})
            # deliverable record: hours + per-deliverable skills (semantic; falls back to session tags)
            dskills = [x for x in (a.get("skills") or []) if x] or sess_skills
            deliverables.append({"name":_name(a),"type":type_label(_ext(a)),"ext":_ext(a),"date":date,
                                 "session":sid,"skills":dskills,"hours":hrs(dmin),
                                 "value":round(hrs(dmin)*rate)})
            # roll skill hours up FROM the deliverable (hours-weighted)
            if dskills:
                share=dmin/len(dskills)
                for name in dskills:
                    skillmin[name]+=share; skilldeliv[name]+=1

        # ---- chat-only sessions (no deliverable): still credit their session-level skills ----
        if not outputs and sess_skills:
            share=e_t/len(sess_skills)
            for name in sess_skills:
                skillmin[name]+=share; skillsessions[name]+=1

        heat[(date,hour)] += len(cats)
        goals.append({"session":sid,"date":date,"title":goal,"process":process,
                      "value_pillar":s.get("value_pillar","Transformation"),
                      "pillar_css":s.get("pillar_css","trans"),
                      "job":s.get("job","Other"),"jtbd":s.get("jtbd",""),
                      "credits":credits_lookup.get(sid),
                      "cost_usd":(round(credits_lookup[sid]*0.01,2) if credits_lookup.get(sid) is not None else cost_lookup.get(sid)),
                      "minutes_typical":round(e_t),"hours_typical":hrs(e_t),
                      "categories":sorted({CATS.get(c,CATS["general"])[3] for c in cats}),
                      "n_tasks":int(sum(runs.values())),"artifacts":[_name(a) for a in outputs],
                      "speed_x":spd,"exec_min":assist,
                      "conversational":(len(outputs)==0)})
        if not outputs: conv+=1

    nday=len(active) or 1
    H_t,H_l,H_h=hrs(exp_t),hrs(exp_l),hrs(exp_h)
    ex_h=hrs(assist_tot)
    spd_t=round(exp_t/assist_tot,1) if assist_tot else 0
    spd_l=round(exp_l/assist_tot,1) if assist_tot else 0
    spd_h=round(exp_h/assist_tot,1) if assist_tot else 0
    val_t=round(H_t*rate); val_l=round(H_l*rate); val_h=round(H_h*rate)

    categories=[]
    for k in CATS:
        label=CATS[k][3]
        if ccount[k]==0 and catmin[label]==0: continue
        mn=catmin[label]
        categories.append({"key":k,"label":label,"low_per_task":CATS[k][0],
            "typical_per_task":CATS[k][1],"high_per_task":CATS[k][2],
            "tasks":ccount[k],"authored_outputs":cauthored[label],"minutes_typical":round(mn),
            "hours_typical":hrs(mn),"value_typical":round(hrs(mn)*rate)})
    categories.sort(key=lambda c:-c["hours_typical"])

    # ---- skills augmented (controlled vocabulary, hours rolled up from per-deliverable tags) ----
    skills_aug=[{"skill":n,"hours":hrs(m),"value":round(hrs(m)*rate),
                 "deliverables":skilldeliv[n],"sessions":skillsessions[n]}
                for n,m in skillmin.most_common()]
    # ---- categorized artifact inventory (what Cowork actually produced) ----
    INV_ORDER=["Deck","Document","Spreadsheet","Web page","Script","Notebook","Query","Image","Text","File"]
    INV_ICON={"Deck":"\U0001F4CA","Document":"\U0001F4C4","Spreadsheet":"\U0001F4C8","Web page":"\U0001F310",
              "Script":"⚙️","Notebook":"\U0001F4D3","Query":"\U0001F50D","Image":"\U0001F5BC️",
              "Text":"\U0001F4DD","File":"\U0001F4CE"}
    inventory=[]
    for lbl in INV_ORDER+[k for k in inv if k not in INV_ORDER]:
        items=inv.get(lbl)
        if not items: continue
        inventory.append({"type":lbl,"icon":INV_ICON.get(lbl,"\U0001F4CE"),"count":len(items),
                          "items":[{"name":it["name"],"date":it["date"]} for it in items]})

    n_in=sum(in_types.values()); n_out=sum(out_types.values())
    io={"inputs_total":n_in,"outputs_total":n_out,
        "expert_hours":H_t,
        "per_deliverable":(round(n_in/n_out,1) if n_out else None),
        "inputs_by_type":[{"label":l,"count":c} for l,c in in_types.most_common()],
        "outputs_by_type":[{"label":l,"count":c} for l,c in out_types.most_common()]}

    payload={
     "meta":{"user":meta.get("user","User"),"email":meta.get("email",""),
             "generated":meta.get("generated",""),"window":win,
             "methodology":"Cowork Time-Savings Methodology v4 + v5 artifact-scaled speed multiplier",
             "hourly_rate_default":rate,"seat_cost_month":0},
     "kpis":{"sessions":len(sessions),"run_tasks":sum(ccount.values()),
             "artifacts":len({art_base(n) for n in afiles}),"active_days":len(active),
             "hours_saved_typical":H_t,"hours_per_active_day":round(H_t/nday,1),
             "speed_multiplier":spd_t,"exec_hours":ex_h,
             "timed_sessions":len(sessions),"conversational_sessions":conv},
     "value":{"hourly_rate":rate,
              "hours_typical":H_t,"hours_low":H_l,"hours_high":H_h,
              "value_typical":val_t,"value_low":val_l,"value_high":val_h,
              "speed_typical":spd_t,"speed_low":spd_l,"speed_high":spd_h,
              "human_equiv_hours":H_t,"exec_hours":ex_h},
     "leverage":{"timed_sessions":len(sessions),"human_equiv_hours":H_t,
                 "exec_hours":ex_h,"speed_multiplier":spd_t},
     "io":io,
     "categories":categories,
     "intents":[{"intent":i,"tasks":c} for i,c in icount.most_common()],
     "processes":[{"process":p,"sessions":proc_count[p],"minutes_typical":round(proc_min[p]),
                   "hours_typical":hrs(proc_min[p]),"value_typical":round(hrs(proc_min[p])*rate),
                   "pct_time":(round(proc_min[p]/exp_t*100) if exp_t else 0)}
                  for p,_ in proc_min.most_common()],
     "roles":[{"role":r,"hours":hrs(mn),"value":round(hrs(mn)*rate)} for r,mn in rmin.most_common()],
     "skills_augmented":skills_aug,
     "inventory":inventory,
     "deliverables":sorted(deliverables,key=lambda x:-x["hours"]),
     "heatmap":[{"date":dd,"hour":h,"count":c} for (dd,h),c in sorted(heat.items())],
     "goals":sorted(goals,key=lambda g:-g["minutes_typical"]),
     "tasks":tasks,"artifacts":artifacts,
    }
    json.dump(payload,open(out,"w"),indent=1)
    print(f"Sessions={len(sessions)} Tasks={sum(ccount.values())} Outputs={len(afiles)} ActiveDays={len(active)}")
    print(f"Expert(human-equiv)={H_t}h  Assisted={ex_h}h  Speed={spd_t}x (range {spd_l}x-{spd_h}x)")
    print(f"Professional-services value=${val_t:,} @${rate}/hr (range ${val_l:,}-${val_h:,})")
    print("wrote",out)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--in",dest="inp",default="working/cowork_sessions.json")
    ap.add_argument("--out",default="working/cowork_roi_data.json")
    a=ap.parse_args(); main(a.inp,a.out)
