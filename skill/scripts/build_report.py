#!/usr/bin/env python3
"""Render the 'What Cowork Did for Me' impact report as a single self-contained,
Microsoft-branded HTML web app. Reads the data payload JSON; the methodology
glossary (source of truth = Cowork Time-Savings Methodology v4) is embedded.
Generic + skill-friendly: pass any payload produced by build_data.py.

Usage: python build_report.py --data working/cowork_roi_data.json --out output/cowork-roi-report.html
"""
import json, argparse, html

# ---- Methodology glossary: per-category research anchors (from the v4 deck) ----
CAT_SOURCES = {
 "Analysis & Research": "Stanford & World Bank 2025 (SSRN 5136877): mean of the 5 research-adjacent O*NET task categories (Critical Thinking 75, Active Learning 50, Quality Control Analysis 67, Judgement & Decision Making 51, Complex Problem Solving 92) = 335÷5 ≈ 67 min saved per task (Typical). LOW (30) = McKinsey 2023, 25–40% uplift on a ~60-min analytical task. HIGH (92) = Stanford-WB Complex Problem Solving ceiling.",
 "Document & content creation": "Microsoft Research causal-impact study (Verma, Suri & Counts 2026; difference-in-differences, n=72,186 Word users): ~6.1 min saved per Word activity instance × ~4 instances per doc run (draft → rewrite → format → polish) ≈ 24 min. Corroborated by UK GDS 2025 (~24 min/drafting task, n=20K).",
 "Email workflows": "Dillon et al., NBER w33795 (2025), RCT n=6,000+ across 56 firms: ~2 hr/week email savings ÷ 14.5 replies/week ≈ 7 min per substantive reply. LOW (3) = Noy & Zhang, Science 2023.",
 "Meeting workflows": "Microsoft Work Trend Index Special Report 2023 (Study #2; Cambon et al., n=57 RCT): recap of a 35-min missed Teams meeting fell from 42m 34s to 11m 13s ≈ 31 min saved per recap (~3.8× faster).",
 "Communication workflows": "Microsoft Work Trend Index 2024: ~14 min/day on comms ÷ 5–7 micro-tasks ≈ 2 min/instance × 2 instances per run (rule + AI draft) ≈ 4 min.",
 "Specialized workflows": "Forrester TEI of Power Automate 2024: 200 hr/yr ÷ 250 days ÷ ~1.5 workflows/day ≈ 32 min/automation, trimmed to 25 (conservative). UK GDS 2025 corroborates ~10 min single-system admin tasks.",
 "Write or debug code": "Cui, Demirer, Jaffe et al., CACM 2024 (n=4,867): ~18 min saved per coding step × 3 steps per run (write + test + debug) ≈ 56 min. Peng et al. RCT 2023 (55.8% faster) sets LOW; Stanford-WB 2025 sets HIGH (96).",
 "General assistance / Other": "Brynjolfsson, Li & Raymond, QJE 2025 / NBER w31161 (n=5,179 agents) + Microsoft WTI 2024: ~5 min saved per single-turn assist/learn episode (no chaining).",
}

# ---- Slide-12 "KEY SOURCE(S) FOR THE TYPICAL VALUE" clickable links (text -> url) ----
CAT_LINKS = {
 "Analysis & Research": [
    ("Stanford-WB SSRN 5136877","https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5136877"),
    ("OpenAI Deep Research","https://openai.com/index/introducing-deep-research/"),
    ("McKinsey 2023","https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights/the-economic-potential-of-generative-ai-the-next-productivity-frontier")],
 "Document & content creation": [
    ("Microsoft Research 2026 (Verma · Suri · Counts)","https://ideas-research-pages.azurewebsites.net/causal-impact-copilot")],
 "Email workflows": [
    ("Noy & Zhang, Science 2023","https://www.science.org/doi/10.1126/science.adh2586"),
    ("NBER w33795 (Dillon 2025)","https://www.nber.org/papers/w33795")],
 "Meeting workflows": [
    ("Cambon et al., MSR 2024","https://www.microsoft.com/en-us/research/publication/early-llm-based-tools-for-enterprise-information-workers-likely-provide-meaningful-boosts-to-productivity/"),
    ("Anthropic Agents 2024","https://www.anthropic.com/research/building-effective-agents"),
    ("Forrester TEI 2024","https://info.microsoft.com/ww-landing-the-tei-of-power-automate-2024.html")],
 "Communication workflows": [
    ("Microsoft WTI 2024","https://www.microsoft.com/en-us/worklab/work-trend-index/2024-annual-report"),
    ("NBER w33795 (Dillon 2025)","https://www.nber.org/papers/w33795")],
 "Specialized workflows": [
    ("Forrester TEI Power Automate 2024","https://info.microsoft.com/ww-landing-the-tei-of-power-automate-2024.html"),
    ("UK GDS Cross-Government 2025","https://www.gov.uk/government/publications/cross-government-copilot-experiment")],
 "Write or debug code": [
    ("Cui et al., CACM 2024","https://cacm.acm.org/research/the-effects-of-generative-ai-on-high-skilled-work-evidence-from-three-field-experiments-with-software-developers/"),
    ("Peng et al. RCT 2023 (arXiv)","https://arxiv.org/abs/2302.06590"),
    ("Stanford-WB SSRN 5136877","https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5136877")],
 "General assistance / Other": [
    ("Brynjolfsson, Li & Raymond QJE 2025 / NBER w31161","https://www.nber.org/papers/w31161"),
    ("Microsoft WTI 2024","https://www.microsoft.com/en-us/worklab/work-trend-index/2024-annual-report")],
}
GITHUB_URL = "https://github.com/microsoft/What-I-Did-Copilot#what-i-did--github-copilot-impact-report"

# All 8 methodology categories with their bands (so the glossary documents every category,
# even those with no tasks in a given window).
ALL_CATS = [
 ("Analysis & Research",30,67,92),
 ("Document & content creation",12,24,42),
 ("Email workflows",3,7,12),
 ("Meeting workflows",12,31,43),
 ("Communication workflows",2,4,11),
 ("Specialized workflows",10,25,40),
 ("Write or debug code",30,56,96),
 ("General assistance / Other",2,5,8),
]

GLOSSARY_TERMS = [
 ("Run task", "One discrete thing you asked Cowork to do that maps to a single methodology category (e.g. build a deck, run an analysis, write a script). A session can contain several run tasks."),
 ("Typical band (min/task)", "The research-anchored minutes-saved value the methodology applies per run task in a category. This report uses the deck's detailed per-category Typical values. Each Typical is computed as a per-instance figure from a published study × the typical number of instances in a Cowork run — not picked from a range."),
 ("Low / High band", "The published floor and ceiling around each Typical. The report shows your total at Low, Typical and High so you can see the conservative-to-optimistic range."),
 ("Hours saved", "Sum of (run tasks × the category's Typical minutes), converted to hours. Hours are fixed by the methodology and do not change with the hourly rate."),
 ("Professional-services value (USD)", "Expert-equivalent hours × your hourly rate — the labour cost a firm would bill to produce the same work unassisted. Adjust the hourly rate at the top to recalculate every dollar figure live."),
 ("Expert clock (unassisted)", "What a professional would take with no AI: the SUM of the research-anchored time-saved band for each task performed (e.g. Analysis 67 + Document 24 = 91 min typical). Every minute traces to a cited study — nothing is assumed for reading or authoring."),
 ("Assisted clock (your time)", "A modeled estimate of your hands-on time with Cowork: a small fixed prompt/setup cost (~8 min/session) plus ~2 min per artifact handled. OneDrive does not record keystroke time, so this is an explicit assumption, not a measurement."),
 ("Speed multiplier", "Expert clock ÷ Assisted clock. '10×' means the same result would have taken an unassisted expert about ten times as long. Rate-independent."),
 ("Artifact", "A concrete deliverable Cowork produced and saved to your OneDrive — a deck, document, spreadsheet, web page, script or package."),
 ("Active day", "A calendar day on which you ran at least one Cowork session in the window."),
 ("Intent / collaboration style", "How you were directing Cowork on each task — e.g. Researching vs. Building — derived from each task's category."),
 ("Skill augmented", "The professional role the task draws on (Data Analyst, Engineer, Content Writer, etc.), with the hours Cowork covered for you in that role."),
]

def esc(s): return html.escape(str(s))

def build(data, out_path, anon=False):
    m=data["meta"]; k=data["kpis"]; val=data["value"]; cats=data["categories"]
    disp_user=("Cowork user (anonymized)" if anon else m["user"])
    intents=data["intents"]; roles=data["roles"]; goals=data["goals"]; heat=data["heatmap"]
    skills_aug=data.get("skills_augmented",[]); inventory=data.get("inventory",[])
    deliverables=data.get("deliverables",[])
    rate=m["hourly_rate_default"]; win=m["window"]
    lev=data.get("leverage",{}) or {}

    # ----- category bar chart (SVG, width scaled to max hours) -----
    maxh=max(c["hours_typical"] for c in cats) or 1
    bar_rows=""
    palette=["#0F6CBD","#2899F5","#0B5394","#50AAE8","#823BBD","#107C41","#C19C00","#8A8886"]
    for i,c in enumerate(cats):
        w=int(c["hours_typical"]/maxh*100)
        col=palette[i%len(palette)]
        # 0-task categories carry only authoring/reading time — label them honestly
        if c["tasks"]>0:
            sub=f"{c['tasks']} tasks · {c['typical_per_task']} min/task"
        elif c.get("authored_outputs"):
            n=c["authored_outputs"]
            sub=f"authoring time · {n} deliverable{'s' if n!=1 else ''}"
        else:
            sub="reading &amp; synthesis time"
        bar_rows+=f"""<div class="bar-row">
          <div class="bar-label">{esc(c['label'])}<span class="bar-sub">{sub}</span></div>
          <div class="bar-track"><div class="bar-fill" style="width:{w}%;background:{col}"></div>
            <span class="bar-val" data-hours="{c['hours_typical']}">{c['hours_typical']}h · ${c['value_typical']:,}</span></div>
        </div>"""


    # ----- Roles Cowork assembled for you — the professional roles a billing firm would charge for
    #       this work (from each session's professional_roles; logic ported from
    #       microsoft/What-I-Did-Copilot). ≥0.2h to match the value-at-a-glance count. -----
    def _rolelink(name):
        q=name.replace('&','%26').replace('/','%2F').replace(' ','+')
        return (f'<a href="https://www.linkedin.com/jobs/search/?keywords={q}" target="_blank" '
                f'rel="noopener" style="color:inherit;text-decoration:none;border-bottom:1px dotted #BBB">{esc(name)}</a>')
    role_src = [r for r in roles if r["hours"] >= 0.2] or roles
    maxr=max((r["hours"] for r in role_src), default=1) or 1
    role_rows=""
    for i,r in enumerate(role_src):
        w=int(r["hours"]/maxr*100); col=palette[i%len(palette)]
        role_rows+=f"""<div class="bar-row"><div class="bar-label">{_rolelink(r['role'])}</div>
        <div class="bar-track"><div class="bar-fill" style="width:{max(w,4)}%;background:{col}"></div>
        <span class="bar-val" data-hours="{r['hours']}">{r['hours']}h · ${r['value']:,}</span></div></div>"""

    # ----- deliverables -> skills -> hours table — each artifact, the skills that built it,
    #       and the expert-equivalent hours attributed to it -----
    ICON={"Deck":"\U0001F4CA","Document":"\U0001F4C4","Spreadsheet":"\U0001F4C8","Web page":"\U0001F310",
          "Script":"⚙️","Notebook":"\U0001F4D3","Query":"\U0001F50D","Image":"\U0001F5BC️",
          "Text":"\U0001F4DD","File":"\U0001F4CE"}
    deliv_rows=""
    _skill_set={}
    for d in deliverables:
        d_skills=d.get("skills",[])
        for s in d_skills:
            _skill_set[s]=_skill_set.get(s,0)+1
        sk_pills="".join(f'<span class="pill">{esc(s)}</span>' for s in d_skills) or '<span class="muted-na">—</span>'
        # data-skills carries a lowercased, pipe-delimited list so the filter JS can match
        ds_attr=esc("|".join(s.lower() for s in d_skills))
        deliv_rows+=f"""<tr class="dl-row" data-skills="{ds_attr}">
          <td><div class="g-title">{ICON.get(d['type'],'\U0001F4CE')} {esc(d['name'])}</div><div class="g-meta">{esc(d['type'])} · {esc(d['date'])}</div></td>
          <td>{sk_pills}</td>
          <td class="g-h"><b data-hours="{d['hours']}">{d['hours']}h</b> · <span class="g-v" data-hours="{d['hours']}">${d['value']:,}</span></td>
        </tr>"""
    if not deliv_rows:
        deliv_rows='<tr><td colspan="3"><div class="lead" style="margin:6px 0">No saved deliverables in this window.</div></td></tr>'
    # Skill-filter chips for the Deliverables table (most-used first), built only when ≥2 skills appear
    deliv_filter_html=""
    if len(_skill_set)>=2:
        _chips="".join(
            f'<button class="dl-chip" data-skill="{esc(s.lower())}" onclick="dlFilter(this)">{esc(s)} <span class="dl-c">{n}</span></button>'
            for s,n in sorted(_skill_set.items(), key=lambda kv:(-kv[1], kv[0])))
        deliv_filter_html=(
            '<div class="dl-filter"><span class="dl-filter-l">Filter by skill</span>'
            '<button class="dl-chip active" data-skill="__all__" onclick="dlFilter(this)">All</button>'
            f'{_chips}</div>')

    # ----- heatmap grid (day x hour) -----
    days=sorted({h["date"] for h in heat})
    hours=list(range(8,20))
    hmap={(h["date"],h["hour"]):h["count"] for h in heat}
    maxc=max(hmap.values()) if hmap else 1

    def fmt_hour(h):
        if h==12: return "12pm"
        if h>12:  return f"{h-12}pm"
        return f"{h}am"

    head='<th class="heat-corner">Date &darr; &nbsp; Time &rarr;</th>'+"".join(f"<th>{fmt_hour(hh)}</th>" for hh in hours)
    body=""
    import datetime
    for d in days:
        dd=datetime.date.fromisoformat(d); lbl=dd.strftime("%a %d %b")
        cells=""
        for hh in hours:
            c=hmap.get((d,hh),0)
            if c:
                a=0.18+0.82*(c/maxc)
                cells+=f'<td class="hc" style="background:rgba(15,108,189,{a:.2f})" title="{lbl} · {fmt_hour(hh)} · {c} run task(s)">{c}</td>'
            else:
                cells+='<td class="hc empty"></td>'
        body+=f'<tr><td class="hd">{lbl}</td>{cells}</tr>'
    heat_legend='<div class="heat-legend">Each number = run tasks started in that hour &nbsp;·&nbsp; Shade = relative intensity (darker = more tasks) &nbsp;·&nbsp; Times are local</div>'
    heat_table=f'<table class="heat"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>{heat_legend}'

    # ----- work-by-process table — grouped by value pillar, accent border replaces pill -----
    PILLAR_ORDER  = ["Revenue Growth","Cost Reduction","Risk Mitigation","Transformation"]
    PILLAR_COLORS = {
        "Revenue Growth":  ("#ECF7F0","#107C41"),   # green — tangible · money coming in
        "Cost Reduction":  ("#EFF6FC","#0F6CBD"),   # blue — tangible · money going out
        "Risk Mitigation": ("#FDF3F3","#A4262C"),   # red — intangible · losses avoided
        "Transformation":  ("#F3E8FB","#6B2FA0"),   # purple — intangible · new ways of working
    }
    # Group goals by JOB x PILLAR combination, sorted per-group by hours desc
    JOB_ORDER = ["Quantify & prove value","Build the capability","Lead the team","Other"]
    def _job_idx(j): return JOB_ORDER.index(j) if j in JOB_ORDER else len(JOB_ORDER)
    def _pil_idx(p): return PILLAR_ORDER.index(p) if p in PILLAR_ORDER else len(PILLAR_ORDER)
    combo_groups = {}
    for g in goals:
        if g["minutes_typical"]==0: continue
        key=(g.get("job","Other"), g.get("value_pillar","Transformation"))
        combo_groups.setdefault(key,[]).append(g)

    # Drop the Session-cost column entirely when NO session has captured cost
    has_cost = any(isinstance(g.get("cost_usd"), (int, float)) for g in goals)
    ncols = 4 if has_cost else 3
    cost_th = "<th>Credits · cost</th>" if has_cost else ""
    def _impact(g):
        val=round(g['hours_typical']*rate)
        spd=(f' · {g["speed_x"]}× faster' if g.get("speed_x") else "")
        return (f'<b data-hours="{g["hours_typical"]}">{g["hours_typical"]}h saved</b> · '
                f'<span class="g-v" data-hours="{g["hours_typical"]}">${val:,}</span>{spd}')
    def _cost_tag(g):
        cr=g.get("credits"); cv=g.get("cost_usd")
        if isinstance(cr,(int,float)):
            return f' &middot; <b style="color:var(--blue)">{cr:,.1f} cr</b> <span style="color:var(--mut)">(${cv:,.2f})</span>'
        if isinstance(cv,(int,float)):
            return f' &middot; <b style="color:var(--blue)">${cv:,.2f}</b>'
        return ''

    # jobmap retained ONLY for the anonymized (team rollup) override below — the personal
    # report no longer pivots on Job. (cowork-roi-member / -aggregated migrate to Process later.)
    jobmap={}
    for g in goals:
        if g.get("minutes_typical",0)==0: continue
        job=g.get("job","Other"); proc=g.get("process","General Productivity")
        d=jobmap.setdefault(job,{}).setdefault(proc,{"jtbd":"","hours":0.0,
                            "pillar":g.get("value_pillar","Transformation"),"projects":[]})
        d["hours"]+=g.get("hours_typical",0); d["projects"].append(g)
        if not d["jtbd"] and g.get("jtbd"): d["jtbd"]=g["jtbd"]

    # ===== VIEW 1 (primary): BUSINESS PROCESS ▸ JTBD ▸ the projects beneath each JTBD =====
    # A genuine 3-level ladder: Process (anchor) → one-or-more JTBD → the projects under each.
    # Projects nest under their JTBD, so a process with several JTBDs renders several indented groups.
    procmap={}
    for g in goals:
        if g.get("minutes_typical",0)==0: continue
        proc=g.get("process","General Productivity")
        d=procmap.setdefault(proc,{"hours":0.0,"sessions":0,
                              "pillar":g.get("value_pillar","Transformation"),"jt":{}})
        d["hours"]+=g.get("hours_typical",0); d["sessions"]+=1
        jt=g.get("jtbd","") or "—"
        grp=d["jt"].setdefault(jt,{"hours":0.0,"projects":[]})
        grp["hours"]+=g.get("hours_typical",0); grp["projects"].append(g)
    total_ph=sum(d["hours"] for d in procmap.values()) or 1
    jtbd_tree_html=""
    if procmap:
        tree=""
        for proc in sorted(procmap,key=lambda p:-procmap[p]["hours"]):
            d=procmap[proc]
            _,pfg=PILLAR_COLORS.get(d["pillar"],("#F3F2F1","#605E5C"))
            pct=round(d["hours"]/total_ph*100); pval=round(d["hours"]*rate)
            nproj=sum(len(grp["projects"]) for grp in d["jt"].values())
            # one indented group per JTBD (most-valuable first); projects nest beneath it
            groups=""
            for jt,grp in sorted(d["jt"].items(),key=lambda kv:-kv[1]["hours"]):
                projs=""
                for g in sorted(grp["projects"],key=lambda x:-x["hours_typical"]):
                    cb=' <span class="pill conv">chat-only</span>' if g.get("conversational") else ""
                    projs+=(f'<div class="wbp-proj"><div class="wbp-proj-t">{esc(g["title"])}{cb}</div>'
                            f'<div class="wbp-proj-i">{_impact(g)}{_cost_tag(g)}</div></div>')
                groups+=(f'<div class="wbp-jtg" style="border-left-color:{pfg}">'
                         f'<div class="wbp-jt"><span class="wbp-jt-k" style="color:{pfg}">JTBD</span>'
                         f'<span class="wbp-jt-t">{esc(jt)}</span>'
                         f'<span class="wbp-jt-h">{grp["hours"]:.1f}h</span></div>'
                         f'<div class="wbp-projs">{projs}</div></div>')
            tree+=(f'<details class="wbp-acc"><summary class="wbp-proc-h">'
                   f'<span class="wbp-k2" style="color:{pfg}">PROCESS</span>'
                   f'<span class="wbp-acc-t">{esc(proc)}</span>'
                   f'<span class="wbp-acc-meta">{d["sessions"]} session{"s" if d["sessions"]!=1 else ""} · '
                   f'{nproj} project{"s" if nproj!=1 else ""} · {pct}% of time</span>'
                   f'<span class="wbp-h">{d["hours"]:.1f}h · '
                   f'<span class="g-v" data-hours="{d["hours"]:.1f}">${pval:,}</span></span>'
                   f'<span class="chev">▸</span></summary>'
                   f'<div class="wbp-acc-body">{groups}</div></details>')
        jtbd_tree_html=f'<div class="wbp-tree">{tree}</div>'

    # ===== VIEW 2 (By Business Value Pillar): collapsible accordion per pillar =====
    PILLAR_ORDER_V=["Revenue Growth","Cost Reduction","Risk Mitigation","Transformation"]
    pil_groups={}
    for g in [x for x in goals if x.get("minutes_typical",0)>0]:
        pil_groups.setdefault(g.get("value_pillar","Transformation"),[]).append(g)
    def _pil_order(p): return PILLAR_ORDER_V.index(p) if p in PILLAR_ORDER_V else 9
    pillar_acc_html=""
    for pillar in sorted(pil_groups, key=lambda p:(_pil_order(p), -sum(x["hours_typical"] for x in pil_groups[p]))):
        gs=sorted(pil_groups[pillar], key=lambda x:-x["hours_typical"])
        ph=sum(x["hours_typical"] for x in gs)
        _,fg=PILLAR_COLORS.get(pillar,("#F3F2F1","#605E5C"))
        css=gs[0].get("pillar_css","trans")
        rows=""
        for g in gs:
            cb=' <span class="pill conv">chat-only</span>' if g.get("conversational") else ""
            cv=g.get("cost_usd"); cr=g.get("credits")
            cost_td=((f'<td class="g-h" style="white-space:nowrap">'
                      +(f'<b>{cr:,.1f} cr</b><br><span class="muted">${cv:,.2f}</span>'
                        if isinstance(cr,(int,float))
                        else (f'<b>${cv:,.2f}</b>' if isinstance(cv,(int,float)) else '<span class="muted-na">n/a</span>'))
                      +'</td>') if has_cost else "")
            rows+=(f'<tr style="border-left:4px solid {fg}">'
                   f'<td><div class="g-title">{esc(g["title"])}{cb}</div>'
                   f'<div class="g-meta">{esc(g.get("process","—"))}</div></td>'
                   f'<td class="g-h">{_impact(g)}</td>{cost_td}</tr>')
        pillar_acc_html+=(
            f'<details class="wbp-acc"><summary class="wbp-pillar-h">'
            f'<span class="bvm-pill {css}">{esc(pillar)}</span>'
            f'<span class="wbp-acc-meta">{len(gs)} project{"s" if len(gs)!=1 else ""}</span>'
            f'<span class="wbp-h">{ph:.1f}h</span><span class="chev">▸</span></summary>'
            f'<div class="wbp-acc-body"><div class="card" style="margin:6px 0 0"><table class="tbl">'
            f'<thead><tr><th>Project</th><th>Assistance offered</th>{cost_th}</tr></thead>'
            f'<tbody>{rows}</tbody></table></div></div></details>')

    # ----- glossary -----
    used_labels={c["label"] for c in cats}
    gloss_cat=""
    for label,lo,ty,hi in ALL_CATS:
        src=CAT_SOURCES.get(label,"")
        links=CAT_LINKS.get(label,[])
        link_html=" · ".join(f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)} ↗</a>' for t,u in links)
        src_line=f'<div class="gl-src"><span class="gl-src-l">Sources (slide 12):</span> {link_html}</div>' if link_html else ""
        tag="" if label in used_labels else '<span class="nouse">not used this period</span>'
        gloss_cat+=f"""<div class="gl-cat"><div class="gl-band"><b>{esc(label)}</b>
        <span class="band">{lo} → <b>{ty}</b> → {hi} min/task {tag}</span></div>
        <p>{esc(src)}</p>{src_line}</div>"""
    # consolidated, de-duplicated reference list across ALL 8 categories
    seen=set(); ref_items=""
    for label,lo,ty,hi in ALL_CATS:
        for t,u in CAT_LINKS.get(label,[]):
            if u in seen: continue
            seen.add(u)
            ref_items+=f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)} ↗</a></li>'
    gloss_terms="".join(f"<div class='gl-term'><b>{esc(t)}</b><span>{esc(d)}</span></div>" for t,d in GLOSSARY_TERMS)

    top_roles_str=" · ".join(_rolelink(r["role"]) for r in roles[:3] if r["hours"]>=0.2)

    payload_json=json.dumps({
        "rate":rate,
        "hours":{"low":val["hours_low"],"typical":val["hours_typical"],"high":val["hours_high"]},
    })

    # ---- real-cost ROI: research-anchored value vs real Copilot-credit cost (credits x $0.01 list) ----
    # Coverage-honest: the ROI multiple compares value and cost over the SAME covered sessions only
    # (the ones carrying a real /cost reading), so partial coverage can never inflate the multiple.
    _covered=[g for g in goals if isinstance(g.get("cost_usd"),(int,float))]
    _real_cost=sum(g["cost_usd"] for g in _covered)
    _real_cred=sum(g["credits"] for g in _covered if isinstance(g.get("credits"),(int,float)))
    _roi_val=sum(round(g.get("hours_typical",0)*rate) for g in _covered)   # value of covered sessions only
    _roi_mult=(_roi_val/_real_cost) if _real_cost else None
    _n_total=len([g for g in goals if g.get("minutes_typical",0)>0]) or len(goals)
    _n_cov=len(_covered)
    roi_html=""
    if _real_cost:
        _cov_note=(f'Measured on <b>{_n_cov}</b> of {_n_total} sessions (real /cost). '
                   f'Value &amp; cost both cover those {_n_cov} sessions only — apples-to-apples.'
                   if _n_cov<_n_total else 'All sessions carry a real /cost reading.')
        roi_html=(
            '<div class="card" style="margin-top:14px">'
            '<div style="display:flex;flex-wrap:wrap;gap:16px 30px;align-items:center;justify-content:space-between">'
            '<div><div class="roi-cap">Real cost &mdash; Copilot Credits</div>'
            f'<div class="roi-val" style="color:var(--blue)">${_real_cost:,.2f}</div>'
            f'<div class="roi-cap">{_real_cred:,.0f} credits &times; $0.01 (pay-as-you-go list)</div></div>'
            '<div style="font-size:26px;color:var(--mut);font-weight:300">vs</div>'
            '<div><div class="roi-cap">Professional-services value (covered sessions)</div>'
            f'<div class="roi-val" style="color:var(--green)">${_roi_val:,}</div>'
            '<div class="roi-cap">research-anchored, at your rate</div></div>'
            '<div style="font-size:26px;color:var(--mut);font-weight:300">=</div>'
            '<div><div class="roi-cap">Return on Cowork spend</div>'
            f'<div class="roi-val" style="color:var(--green)">{_roi_mult:.0f}&times;</div>'
            f'<div class="roi-cap">value &divide; real cost</div></div>'
            '</div>'
            f'<div style="margin-top:10px;font-size:11.5px;color:var(--mut);border-top:1px solid var(--line);padding-top:8px">{_cov_note}</div>'
            '</div>')
    # ===== ANONYMIZED (team-safe) overrides =====
    # Strip every identifiable string — project/chat names, JTBD prose, deliverable filenames —
    # leaving only aggregate totals, generic categories, skills, and dates. Used for the team rollup
    # so a manager can combine everyone's report without seeing anyone's specific work.
    if anon:
        # Work-by-business-process · By Job-to-be-Done → Job + total hours/value ONLY (no projects, no JTBD)
        _rows=""
        for i,job in enumerate(sorted(jobmap, key=lambda j:-sum(x["hours"] for x in jobmap[j].values()))):
            jobh=sum(x["hours"] for x in jobmap[job].values())
            nproc=len(jobmap[job]); col=palette[i%len(palette)]
            w=int(jobh/(max((sum(x["hours"] for x in jobmap[jj].values()) for jj in jobmap), default=1) or 1)*100)
            _rows+=(f'<div class="bar-row"><div class="bar-label">{esc(job)}'
                    f'<span class="bar-sub">{nproc} business process{"es" if nproc!=1 else ""}</span></div>'
                    f'<div class="bar-track"><div class="bar-fill" style="width:{max(w,4)}%;background:{col}"></div>'
                    f'<span class="bar-val" data-hours="{jobh:.1f}">{jobh:.1f}h · ${round(jobh*rate):,}</span></div></div>')
        jtbd_tree_html=f'<div class="card">{_rows}</div>'

        # By Business Value Pillar → Pillar + total hours/value ONLY (no project rows)
        _prows=""
        for pillar in sorted(pil_groups, key=lambda p:(_pil_order(p), -sum(x["hours_typical"] for x in pil_groups[p]))):
            ph=sum(x["hours_typical"] for x in pil_groups[pillar]); n=len(pil_groups[pillar])
            css=pil_groups[pillar][0].get("pillar_css","trans")
            _,fg=PILLAR_COLORS.get(pillar,("#F3F2F1","#605E5C"))
            _prows+=(f'<div class="bar-row" style="border-left:4px solid {fg};padding-left:10px">'
                     f'<div class="bar-label"><span class="bvm-pill {css}">{esc(pillar)}</span>'
                     f'<span class="bar-sub">{n} project{"s" if n!=1 else ""} · totals only</span></div>'
                     f'<div class="bar-track"><div class="bar-fill" style="width:{max(int(ph/(max((sum(x["hours_typical"] for x in pil_groups[p]) for p in pil_groups),default=1) or 1)*100),4)}%;background:{fg}"></div>'
                     f'<span class="bar-val" data-hours="{ph:.1f}">{ph:.1f}h · ${round(ph*rate):,}</span></div></div>')
        pillar_acc_html=f'<div class="card">{_prows}</div>'

        # Deliverables → type + date + skills + hours ONLY (no file/chat names)
        deliv_rows=""
        for d in deliverables:
            d_skills=d.get("skills",[])
            sk_pills="".join(f'<span class="pill">{esc(s)}</span>' for s in d_skills) or '<span class="muted-na">—</span>'
            ds_attr=esc("|".join(s.lower() for s in d_skills))
            deliv_rows+=f"""<tr class="dl-row" data-skills="{ds_attr}">
              <td><div class="g-title">{ICON.get(d['type'],'\U0001F4CE')} {esc(d['type'])}</div><div class="g-meta">{esc(d['date'])}</div></td>
              <td>{sk_pills}</td>
              <td class="g-h"><b data-hours="{d['hours']}">{d['hours']}h</b> · <span class="g-v" data-hours="{d['hours']}">${d['value']:,}</span></td>
            </tr>"""
        if not deliv_rows:
            deliv_rows='<tr><td colspan="3"><div class="lead" style="margin:6px 0">No saved deliverables in this window.</div></td></tr>'

    H=f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>What Cowork Did for Me — {esc(disp_user)}</title>
<style>
:root{{--blue:#0F6CBD;--blue2:#2899F5;--ink:#201F1E;--mut:#605E5C;--line:#EDEBE9;--bg:#FAF9F8;--card:#fff;--green:#107C41}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:'Segoe UI','Segoe UI Web',system-ui,-apple-system,Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.5}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 24px 64px}}
header.hero{{background:linear-gradient(135deg,#0B3C6E 0%,#0F6CBD 55%,#2899F5 100%);color:#fff;padding:40px 0 56px;margin-bottom:-32px}}
.logo{{display:inline-grid;grid-template-columns:11px 11px;grid-gap:2px;vertical-align:middle;margin-right:10px}}
.logo i{{width:11px;height:11px;display:block}}
.logo .r{{background:#F25022}}.logo .g{{background:#7FBA00}}.logo .b{{background:#00A4EF}}.logo .y{{background:#FFB900}}
.brand{{font-size:13px;letter-spacing:.4px;opacity:.95;font-weight:600;text-transform:uppercase}}
h1{{font-size:34px;margin:14px 0 6px;font-weight:700;letter-spacing:-.5px}}
.sub{{opacity:.92;font-size:15px}}
.rate-bar{{display:flex;flex-wrap:wrap;gap:14px;align-items:center;background:rgba(255,255,255,.14);backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,.25);border-radius:10px;padding:12px 16px;margin-top:22px;max-width:640px}}
.rate-bar label{{font-size:13px;font-weight:600}}
.rate-bar input{{width:96px;padding:7px 10px;border-radius:6px;border:1px solid rgba(255,255,255,.5);background:#fff;color:var(--ink);font-size:15px;font-weight:700}}
.rate-bar .note{{font-size:12px;opacity:.85}}
.btn{{cursor:pointer;border:0;border-radius:6px;padding:9px 16px;font-size:13px;font-weight:600;background:#fff;color:var(--blue)}}
.btn.ghost{{background:rgba(255,255,255,.16);color:#fff;border:1px solid rgba(255,255,255,.5)}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:24px;margin:18px 0;box-shadow:0 1px 3px rgba(0,0,0,.04)}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;box-shadow:0 1px 3px rgba(0,0,0,.04)}}
.kpi .n{{font-size:30px;font-weight:700;color:var(--blue);line-height:1.1}}
.kpi .l{{font-size:12.5px;color:var(--mut);margin-top:4px;text-transform:uppercase;letter-spacing:.3px}}
.kpi .s{{font-size:11px;color:var(--mut);margin-top:3px}}
.kpi.accent{{background:linear-gradient(135deg,#F2FAF5,#fff);border-color:#C7E5CD}}
.kpi.accent .n{{color:var(--green)}}
.roi-hero{{display:grid;grid-template-columns:1.1fr 1fr;gap:22px;align-items:center}}
.roi-big{{font-size:64px;font-weight:800;color:var(--green);line-height:1}}
.roi-cap{{font-size:14px;color:var(--mut)}}
.roi-val{{font-size:30px;font-weight:700}}
.range{{display:flex;gap:18px;margin-top:10px;font-size:13px;color:var(--mut)}}
.range b{{color:var(--ink)}}
h2{{font-size:21px;margin:34px 0 6px;font-weight:700}}
h2 .sec{{color:var(--blue)}}
.lead{{color:var(--mut);font-size:14px;margin:0 0 14px}}
.bar-row{{display:grid;grid-template-columns:230px 1fr;gap:14px;align-items:center;margin:9px 0}}
.bar-label{{font-size:13.5px;font-weight:600}}
.bar-sub{{display:block;font-size:11.5px;color:var(--mut);font-weight:400}}
.bar-track{{position:relative;background:#F3F2F1;border-radius:6px;height:30px;display:flex;align-items:center}}
.bar-fill{{height:100%;border-radius:6px;min-width:3px;transition:width .5s}}
.bar-val{{position:absolute;right:10px;font-size:12.5px;font-weight:600}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.donut-wrap{{display:flex;gap:18px;align-items:center;flex-wrap:wrap}}
.lg{{font-size:13px;margin:5px 0}}.dot{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:7px}}
table.tbl{{width:100%;border-collapse:collapse;font-size:13.5px}}
table.tbl td{{border-top:1px solid var(--line);padding:12px 8px;vertical-align:top}}
table.tbl th{{text-align:left;font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);padding:0 8px 8px;border-bottom:2px solid var(--line);white-space:nowrap}}
.pill.proc{{background:#F0F0F0;color:#3C3C3C;border-color:#D0D0D0;font-weight:600}}
.g-title{{font-weight:600}}.g-meta{{font-size:12px;color:var(--mut);margin:3px 0 6px}}
.pill{{display:inline-block;background:#EFF6FC;color:var(--blue);border:1px solid #CFE4F7;border-radius:20px;padding:2px 10px;font-size:11.5px;margin:2px 4px 0 0}}
.g-h{{text-align:right;white-space:nowrap}}.g-v{{color:var(--green);font-weight:600}}
.g-spd{{font-size:11px;color:var(--blue);font-weight:600;margin-top:4px}}.g-spd.muted{{color:#A19F9D;font-weight:400}}
.muted-na{{font-size:12px;color:#A19F9D;font-style:italic}}
.inv-row{{padding:11px 0;border-bottom:1px dashed var(--line)}}
.inv-row:last-child{{border-bottom:0}}
.inv-head{{font-size:14px;margin-bottom:3px}}
.inv-head .inv-n{{display:inline-block;background:#EFF6FC;color:var(--blue);border:1px solid #CFE4F7;border-radius:20px;padding:0 9px;font-size:11.5px;font-weight:700;margin-left:6px}}
.inv-items{{font-size:12.5px;color:var(--mut);line-height:1.7}}
.pill.conv{{background:#F3F2F1;color:#605E5C;border-color:#E1DFDD}}
.heat{{border-collapse:collapse;font-size:11px;width:auto}}
.heat th{{color:var(--mut);font-weight:600;padding:4px 6px;text-align:center;white-space:nowrap}}
.heat th.heat-corner{{text-align:left;font-style:italic;font-size:10px;padding-right:12px;color:var(--mut)}}
.heat td.hd{{color:var(--mut);text-align:right;padding-right:8px;white-space:nowrap;font-size:11.5px}}
.heat td.hc{{width:38px;height:30px;text-align:center;border-radius:4px;color:#fff;font-weight:700;font-size:12px}}
.heat td.hc.empty{{background:#F3F2F1}}
.heat-legend{{margin-top:10px;font-size:11.5px;color:var(--mut);font-style:italic}}
details.gl{{border:1px solid var(--line);border-radius:12px;background:var(--card);margin:14px 0;overflow:hidden}}
details.gl>summary{{cursor:pointer;list-style:none;padding:18px 22px;font-weight:700;font-size:17px;display:flex;justify-content:space-between;align-items:center}}
details.gl>summary::-webkit-details-marker{{display:none}}
details.gl>summary .chev{{transition:transform .2s;color:var(--blue)}}
details.gl[open]>summary .chev{{transform:rotate(90deg)}}
.gl-body{{padding:0 22px 20px;border-top:1px solid var(--line)}}
.gl-cat{{padding:12px 0;border-bottom:1px dashed var(--line)}}
.gl-band{{display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}}
.gl-band .band{{font-size:12.5px;color:var(--mut)}}.gl-band .band b{{color:var(--green)}}
.gl-cat p{{margin:6px 0 0;font-size:13px;color:var(--mut)}}
.gl-term{{padding:10px 0;border-bottom:1px dashed var(--line)}}
.gl-term b{{display:block;font-size:13.5px}}.gl-term span{{font-size:13px;color:var(--mut)}}
.inspired{{margin-top:14px;font-size:12.5px;opacity:.95}}
.inspired a{{color:#D6ECff;font-weight:600;text-decoration:underline}}
a{{color:var(--blue)}}
.gl-src{{margin-top:7px;font-size:12.5px}}
.gl-src-l{{color:var(--mut);font-weight:600;margin-right:4px}}
.gl-src a{{color:var(--blue);text-decoration:none;font-weight:600;border-bottom:1px solid #CFE4F7}}
.gl-src a:hover{{border-bottom-color:var(--blue)}}
.reflist{{margin:8px 0 4px;padding-left:20px}}
.reflist li{{font-size:13.5px;margin:6px 0}}
.reflist a{{color:var(--blue);font-weight:600}}
.nouse{{display:inline-block;background:#F3F2F1;color:#8A8886;border-radius:10px;padding:1px 8px;font-size:10.5px;margin-left:6px;font-weight:600}}
.bvm-pill{{display:inline-block;border-radius:20px;padding:2px 10px;font-size:10.5px;font-weight:700;letter-spacing:.4px;vertical-align:middle;text-transform:uppercase;margin-bottom:8px}}
.bvm-pill.rev{{background:#ECF7F0;color:#107C41;border:1px solid #C7E5CD}}
.bvm-pill.cost{{background:#EFF6FC;color:#0F6CBD;border:1px solid #CFE4F7}}
.bvm-pill.risk{{background:#FDF3F3;color:#A4262C;border:1px solid #F4CCCC}}
.bvm-pill.trans{{background:#F3E8FB;color:#6B2FA0;border:1px solid #E5CCF5}}
.wbp-tree{{margin:4px 0 18px}}
.wbp-job{{margin:0 0 14px;background:#fff;border:1px solid #EAE8E6;border-radius:12px;padding:4px 16px 14px}}
.wbp-job-h{{display:flex;align-items:center;gap:9px;font-size:14.5px;font-weight:700;color:var(--ink);padding:11px 0 8px;border-bottom:1px solid #F0EEEC}}
.wbp-k2{{font-size:10px;font-weight:800;letter-spacing:.6px;background:#EEF2F6;color:var(--mut);border-radius:6px;padding:2px 8px}}
.wbp-proc{{margin:13px 0 0 8px;padding:3px 0 5px 15px}}
.wbp-proc-name{{display:flex;align-items:center;gap:8px}}
.wbp-sub{{font-size:12.5px;color:var(--ink);margin:6px 0 0 2px;line-height:1.5}}
.wbp-k{{display:inline-block;font-size:9.5px;font-weight:800;letter-spacing:.5px;text-transform:uppercase;color:var(--mut);margin-right:8px;min-width:40px}}
.wbp-h{{margin-left:auto;font-size:12px;font-weight:700;color:var(--mut);white-space:nowrap}}
.wbp-toggle{{display:flex;align-items:center;gap:8px;margin-bottom:14px;font-size:12px;color:var(--mut)}}
.wbp-btn{{border:1px solid #CFCFCF;background:#fff;border-radius:14px;padding:3px 12px;font-size:12px;font-weight:600;cursor:pointer;color:var(--mut)}}
.wbp-btn.active{{background:var(--blue);color:#fff;border-color:var(--blue)}}
/* 3-level ladder: Process (accordion header) ▸ JTBD group (indented, bold) ▸ projects (further indented, unbolded) */
.wbp-jtg{{margin:12px 0 0;padding-left:13px;border-left:2px solid #E1DFDD}}
.wbp-jtg:first-child{{margin-top:6px}}
.wbp-jt{{display:flex;align-items:baseline;gap:8px}}
.wbp-jt-k{{font-size:9px;font-weight:800;letter-spacing:.6px;text-transform:uppercase;flex:none}}
.wbp-jt-t{{font-weight:700;font-size:13.5px;color:#322F2D;letter-spacing:-.1px}}
.wbp-jt-h{{margin-left:auto;font-size:11.5px;font-weight:700;color:var(--mut);white-space:nowrap}}
.wbp-projs{{margin:7px 0 2px 9px;padding-left:14px;border-left:1px dotted #D6D4D2}}
.wbp-proj{{display:flex;justify-content:space-between;align-items:baseline;gap:10px;padding:5px 0;border-top:1px dotted #EEE}}
.wbp-proj:first-child{{border-top:none}}
.wbp-proj-t{{font-size:12.5px;font-weight:400;color:#3B3A39}}
.wbp-proj-i{{font-size:12px;color:var(--mut);white-space:nowrap;text-align:right}}
.wbp-pillarview{{display:none}}
#wbpView.mode-pillar .wbp-jtbdview{{display:none}}
#wbpView.mode-pillar .wbp-pillarview{{display:block}}
.wbp-acc{{background:#fff;border:1px solid #EAE8E6;border-radius:12px;margin:0 0 10px;overflow:hidden}}
.wbp-acc>summary{{cursor:pointer;list-style:none;display:flex;align-items:center;gap:9px;padding:13px 16px;font-size:14.5px;font-weight:700;color:var(--ink);border-bottom:0}}
.wbp-acc>summary::-webkit-details-marker{{display:none}}
.wbp-acc>summary:hover{{background:#FAFAFA}}
.wbp-acc>summary .chev{{transition:transform .2s;color:var(--blue);margin-left:4px}}
.wbp-acc[open]>summary{{border-bottom:1px solid #F0EEEC}}
.wbp-acc[open]>summary .chev{{transform:rotate(90deg)}}
.wbp-acc-t{{font-weight:700}}
.wbp-acc-meta{{font-size:11.5px;font-weight:600;color:var(--mut);background:#F3F2F1;border-radius:10px;padding:1px 9px}}
.wbp-acc .wbp-h{{margin-left:auto}}
.wbp-acc-body{{padding:6px 16px 14px}}
.wbp-acc-body .wbp-proc:first-child{{margin-top:8px}}
.wbp-exp{{margin-left:auto;font-size:11.5px}}
.wbp-exp a{{color:var(--blue);text-decoration:none;border-bottom:1px dotted #CFE4F7}}
.dl-filter{{display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin-bottom:16px}}
.dl-filter-l{{font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;color:var(--mut);margin-right:4px}}
.dl-chip{{border:1px solid #CFCFCF;background:#fff;border-radius:14px;padding:3px 11px;font-size:12px;font-weight:600;cursor:pointer;color:var(--mut)}}
.dl-chip:hover{{border-color:var(--blue);color:var(--blue)}}
.dl-chip.active{{background:var(--blue);color:#fff;border-color:var(--blue)}}
.dl-chip .dl-c{{font-size:10.5px;opacity:.8;margin-left:3px}}
.anon-badge{{display:inline-block;margin-top:14px;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.45);border-radius:8px;padding:7px 13px;font-size:12px;font-weight:600}}
.foot{{text-align:center;color:var(--mut);font-size:12px;margin-top:30px}}
.foot a{{color:var(--blue)}}
html{{scroll-behavior:smooth}}
.note-box{{background:#FFF8F0;border:1px solid #F2D9B8;border-radius:8px;padding:12px 16px;font-size:12.5px;color:#7A4F11;margin-top:12px}}
@media(max-width:760px){{.roi-hero,.two{{grid-template-columns:1fr}}.bar-row{{grid-template-columns:1fr}}}}
@media print{{header.hero{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}.rate-bar,.btn{{display:none!important}}.card,.kpi{{box-shadow:none}}details.gl[open]{{break-inside:avoid}}body{{background:#fff}}}}
</style></head>
<body>
<header class="hero"><div class="wrap">
  <div class="brand"><span class="logo"><i class="r"></i><i class="g"></i><i class="b"></i><i class="y"></i></span>Microsoft Copilot Cowork · Impact Report</div>
  <h1>What Cowork Did for Me</h1>
  <div class="sub">{esc(disp_user)} &nbsp;·&nbsp; {esc(win['label'])} ({esc(win['from'])} → {esc(win['to'])}) &nbsp;·&nbsp; Methodology v4</div>
  {('<div class="anon-badge">🔒 Anonymized · team-safe view — no names, prompts, or project titles; only totals, skills, dates &amp; categories</div>') if anon else ''}
  <div class="rate-bar">
    <label>Your hourly rate ($) <input id="rate" type="number" min="1" step="1" value="{rate}"></label>
    <span class="note">Adjust to recalculate every dollar figure live.</span>
    <a class="btn ghost" href="#glossary">📖 Glossary</a>
    <button class="btn" onclick="window.print()">⬇ Download PDF</button>
  </div>
  <div class="inspired">Report inspired from <a href="{esc(GITHUB_URL)}" target="_blank" rel="noopener">“What I Did — GitHub Copilot Impact Report” ↗</a></div>
</div></header>

<div class="wrap">
  <div class="card roi-hero">
    <div>
      <div class="bvm-pill rev">Time Saved</div>
      <div class="roi-cap">Research-anchored expert-equivalent effort</div>
      <div class="roi-big"><b>{val['hours_typical']}</b>h</div>
      <div class="range">
        <span>Conservative <b>{val['hours_low']}</b>h</span>
        <span>Typical <b>{val['hours_typical']}</b>h</span>
        <span>Optimistic <b>{val['hours_high']}</b>h</span>
      </div>
      <div class="roi-cap" style="margin-top:10px">The sum of the published per-task time-saved bands across your sessions — every minute traces to a cited study.</div>
    </div>
    <div>
      <div class="bvm-pill cost">Cost Reduction</div>
      <div class="roi-cap">Professional-services equivalent</div>
      <div class="roi-val" style="color:var(--green)">$<span class="money" data-h="{val['hours_typical']}">{val['value_typical']:,}</span></div>
      <div class="roi-cap" style="margin-top:10px">Assisted value at expert rate — what a specialist would charge for the same deliverables</div>
      <div class="roi-cap" style="margin-top:6px">{val['hours_typical']}h × your rate · range $<span class="money" data-h="{val['hours_low']}">{val['value_low']:,}</span>–$<span class="money" data-h="{val['hours_high']}">{val['value_high']:,}</span></div>
    </div>
  </div>
  {roi_html}

  <div class="card" style="margin-top:18px">
    <div style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--mut);margin-bottom:14px">Value at a glance — {esc(win['label'])}</div>
    <table class="tbl" style="font-size:13.5px">
      <thead><tr>
        <th style="width:160px">Value pillar</th>
        <th>Business outcome <span style="font-weight:400;font-style:italic">(lagging KPI)</span></th>
        <th>Cowork indicator <span style="font-weight:400;font-style:italic">(leading KPI)</span></th>
        <th style="text-align:right;white-space:nowrap">Your result</th>
      </tr></thead>
      <tbody>
        <tr>
          <td><span class="bvm-pill rev">Revenue Growth</span></td>
          <td>Incremental gross revenue — capacity freed for revenue-generating work<div style="font-size:11.5px;color:var(--mut);margin-top:3px;font-style:italic">Tangible · money coming in</div></td>
          <td>Hours redeployed from production to higher-value work</td>
          <td style="text-align:right"><span class="muted-na">not directly measured</span></td>
        </tr>
        <tr>
          <td><span class="bvm-pill cost">Cost Reduction</span></td>
          <td>Labor &amp; budget savings — specialist work delivered without added headcount<div style="font-size:11.5px;color:var(--mut);margin-top:3px;font-style:italic">Tangible · money going out</div></td>
          <td>Professional-services equivalent at your rate</td>
          <td style="text-align:right"><b style="font-size:16px;color:var(--green)">$<span class="money" data-h="{val['hours_typical']}">{val['value_typical']:,}</span></b></td>
        </tr>
        <tr>
          <td><span class="bvm-pill risk">Risk Mitigation</span></td>
          <td>Penalties &amp; losses avoided — earlier, better-supported decisions<div style="font-size:11.5px;color:var(--mut);margin-top:3px;font-style:italic">Intangible · money going out</div></td>
          <td>Faster, evidence-backed analysis &amp; review</td>
          <td style="text-align:right"><span class="muted-na">not directly measured</span></td>
        </tr>
        <tr>
          <td><span class="bvm-pill trans">Transformation</span></td>
          <td>Adoption, decision quality, retention — new AI-assisted ways of working<div style="font-size:11.5px;color:var(--mut);margin-top:3px;font-style:italic">Intangible · money coming in</div></td>
          <td>Speed vs. unassisted expert · professional roles Cowork substituted for<div style="font-size:11px;color:var(--mut);margin-top:4px;font-weight:400">{top_roles_str}</div></td>
          <td style="text-align:right"><b style="font-size:16px;color:#6B2FA0">{val['speed_typical']}×</b> faster · <b style="color:#6B2FA0">{len([r for r in roles if r['hours']>=0.2])}</b> roles substituted</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="kpi-grid">
    <div class="kpi"><div class="n">{k['sessions']}</div><div class="l">Cowork sessions</div></div>
    <div class="kpi"><div class="n">{k['run_tasks']}</div><div class="l">Tasks completed</div></div>
    <div class="kpi"><div class="n">{k['active_days']}</div><div class="l">Active days</div></div>
    <div class="kpi accent"><div class="n">{k['hours_saved_typical']}h</div><div class="l">Expert-equivalent hours</div><div class="s">delivered by Cowork</div></div>
    <div class="kpi"><div class="n">{k['exec_hours']}h</div><div class="l">Hands-on hours</div><div class="s">your time (est.)</div></div>
  </div>
  {(f'<div class="note-box" style="margin-top:14px"><b>Secondary — speed multiplier:</b> your ~{lev.get("human_equiv_hours",0)}h of research-anchored expert-equivalent effort against an estimated ~{lev.get("exec_hours",0)}h of hands-on time is a <b>{lev.get("speed_multiplier","?")}×</b> multiplier. The expert clock is the sum of cited per-task time-saved bands; the assisted clock is a <b>modeled</b> estimate (OneDrive does not record keystroke time; measured where the telemetry hook is enabled), so treat the multiplier as directional, not a stopwatch.</div>') if lev.get('speed_multiplier') else ''}

  <h2><span class="sec">⏱</span> Where the time went — by task category</h2>
  <p class="lead">Each run task is valued at its category's research-anchored <b>Typical</b> minutes saved (methodology v4). Hours are fixed; dollar values follow your hourly rate.</p>
  <div class="card">{bar_rows}</div>

  <h2><span class="sec">🧑‍💼</span> Roles Cowork assembled for me</h2>
  <p class="lead">The professional roles Cowork stood in for — the specialist hats it wore so the work got done without added headcount, with the expert-equivalent hours it covered in each. This is where time saved becomes <b>capability</b>: specialist roles assembled on demand, directly in your workflow.</p>
  <div class="card">{role_rows}</div>

  <h2><span class="sec">📦</span> Work by business process</h2>
  <p class="lead">Your work anchored on the <b>Business Process</b> that produced it — each process carries the <b>Job-to-be-Done</b> it served and the <b>projects</b> beneath it — or seen by the <b>Business Value Pillar</b> it creates value in. Same projects, two lenses. <b>Click any process to expand</b> its JTBD and projects.</p>
  <details class="gl" style="margin:0 0 14px"><summary>How to read this — Process ▸ JTBD ▸ Project &amp; the two lenses <span class="chev">▸</span></summary>
    <div class="gl-body"><div style="font-size:13px;line-height:1.75">
      <p style="margin:0 0 9px">Your work rolls up a three-level ladder, anchored on Process. <b>Value flows up the ladder; work flows down.</b></p>
      <div><b>Business Process</b> &mdash; <i>the repeatable &ldquo;machine&rdquo; that produces an outcome.</i> It has a customer and a metric, and it runs again and again &mdash; not a one-off. This is the anchor everything rolls up to.</div>
      <div style="margin-top:7px">&nbsp;&nbsp;└ <b>Job-to-be-Done (JTBD)</b> &mdash; <i>the specific stakeholder outcome that process is &ldquo;hired&rdquo; to deliver</i> &mdash; what a real person actually needs done, and why.</div>
      <div style="margin-top:7px">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└ <b>Project</b> &mdash; <i>the actual thing Cowork delivered</i> for that JTBD, carrying its <b>impact</b>: expert-equivalent hours saved &middot; value &middot; speed.</div>
      <p style="margin:11px 0 4px"><b>The same projects, seen through two lenses:</b></p>
      <div><b>&middot; By process</b> &mdash; the ladder above. Answers <i>&ldquo;which repeatable capabilities is my time going into, and who do they serve?&rdquo;</i></div>
      <div style="margin-top:4px"><b>&middot; By Business Value Pillar</b> &mdash; the same projects grouped by the kind of value they create &mdash; <b>Revenue Growth</b> (top-line), <b>Cost Reduction</b> (efficiency), <b>Risk Mitigation</b> (losses avoided), <b>Transformation</b> (new ways of working). Answers <i>&ldquo;what business value did this work create?&rdquo;</i></div>
    </div></div>
  </details>
  <div id="wbpView">
    <div class="wbp-toggle"><span>View:</span>
      <button class="wbp-btn active" id="wbpJtbdBtn" onclick="wbpMode(false)">By process</button>
      <button class="wbp-btn" id="wbpPillarBtn" onclick="wbpMode(true)">By pillar</button>
      <span class="wbp-exp"><a href="#" onclick="wbpExpand(event,true)">Expand all</a> · <a href="#" onclick="wbpExpand(event,false)">Collapse all</a></span>
    </div>
    <div class="wbp-jtbdview">{jtbd_tree_html}</div>
    <div class="wbp-pillarview">{pillar_acc_html}
      <p style="margin:14px 0 0;font-size:12px;color:var(--mut)">Each project grouped under the Business Value Pillar it advances &mdash; <b>{k['sessions']} projects</b> across {k['active_days']} active days. Click a pillar to expand its projects.</p>
    </div>
  </div>

  <h2><span class="sec">📦</span> Deliverables &amp; the skills behind them</h2>
  <p class="lead">Every artifact Cowork produced, the professional skills that went into it, and the expert-equivalent hours attributed to each. Use the chips to <b>filter by the skill applied</b>.</p>
  <div class="card">{deliv_filter_html}<table class="tbl">
    <thead><tr><th>Deliverable</th><th>Skills applied</th><th>Expert effort</th></tr></thead>
    <tbody>{deliv_rows}</tbody></table>
    <p class="dl-empty" style="display:none;margin:10px 2px 0;font-size:12.5px;color:var(--mut)">No deliverables match that skill.</p>
    <p style="margin:12px 0 0;font-size:12px;color:var(--mut)">Per-deliverable hours = an equal share of its session's research-anchored expert time, so they sum back to the totals above. Chat-only sessions (no saved file) appear only in the role bars, not here.</p>
  </div>

  <h2 id="glossary"><span class="sec">📐</span> Methodology &amp; glossary</h2>
  <p class="lead">Every number above is traceable. Expand to see how each metric and band is derived — grounded in the Cowork Time-Savings Methodology v4 and its published sources.</p>
  <details class="gl"><summary>How the time-savings bands are derived (per category) <span class="chev">▸</span></summary>
    <div class="gl-body">{gloss_cat}
    <div class="note-box"><b>Data basis:</b> Derived from {k['sessions']} Cowork session workspaces (input/output artifacts) saved to your OneDrive Cowork folder over the window, classified into the 8 methodology categories. Email, Meeting and Communication categories produced no saved artifacts this period, so they are reported as zero — this makes the totals a conservative floor of your true time saved.</div>
    </div>
  </details>
  <details class="gl"><summary>What each metric means <span class="chev">▸</span></summary>
    <div class="gl-body">{gloss_terms}</div>
  </details>
  <details class="gl"><summary>All research sources (clickable) <span class="chev">▸</span></summary>
    <div class="gl-body"><p class="lead" style="margin-top:12px">Every Typical band is justified by the published sources cited on slide 12 of the Cowork Time-Savings Methodology deck. Click to open each.</p>
    <ul class="reflist">{ref_items}</ul></div>
  </details>
  <details class="gl"><summary>How the speed multiplier &amp; value are calculated <span class="chev">▸</span></summary>
    <div class="gl-body"><div class="gl-term"><span>
    <b>Expert clock</b> (per session) = the sum of the research-anchored time-saved band for each task performed (e.g. Analysis 67 + Document 24 = 91 min typical). No read-time or authoring assumptions — every minute is a cited band.<br>
    <b>Assisted clock</b> (per session) = ~8 min prompt/setup + ~2 min per artifact handled (modeled, not measured).<br>
    <b>Speed multiplier</b> (secondary) = Σ Expert clock ÷ Σ Assisted clock. The assisted clock is a <b>modeled</b> hands-on estimate (8 min + 2 min/artifact; measured where the telemetry hook is on), so the multiplier is directional — rate-independent.<br>
    <b>Professional-services value</b> = Expert-clock hours × your hourly rate (default ${rate}/hr). No ROI/seat-cost figure is shown because credit &amp; seat consumption is not available.<br>
    The <b>Conservative / Optimistic</b> figures re-sum the published <b>low</b> / <b>high</b> band for each task.
    </span></div></div>
  </details>

  <div class="foot">Generated {esc(m['generated'])} · Cowork Time-Savings Methodology v4 · Time Saved &amp; Value are research-anchored (cited per-task bands); the speed multiplier's assisted clock is a modeled estimate.<br>
  Report inspired from <a href="{esc(GITHUB_URL)}" target="_blank" rel="noopener">“What I Did — GitHub Copilot Impact Report” ↗</a> · Powered by Copilot Cowork</div>
</div>

<script>
var DATA={payload_json};
function wbpMode(pillar){{
  var v=document.getElementById('wbpView'); if(!v) return;
  v.classList.toggle('mode-pillar', !!pillar);
  document.getElementById('wbpJtbdBtn').classList.toggle('active', !pillar);
  document.getElementById('wbpPillarBtn').classList.toggle('active', !!pillar);
}}
function wbpExpand(e,open){{
  e.preventDefault();
  var v=document.getElementById('wbpView'); if(!v) return;
  var pillar=v.classList.contains('mode-pillar');
  var scope=v.querySelector(pillar?'.wbp-pillarview':'.wbp-jtbdview');
  (scope?scope:v).querySelectorAll('details.wbp-acc').forEach(function(d){{d.open=open;}});
}}
function dlFilter(btn){{
  var sk=btn.dataset.skill;
  document.querySelectorAll('.dl-chip').forEach(function(c){{c.classList.toggle('active',c===btn);}});
  var shown=0;
  document.querySelectorAll('tr.dl-row').forEach(function(r){{
    var list=(r.dataset.skills||'').split('|');
    var match=(sk==='__all__')||list.indexOf(sk)>=0;
    r.style.display=match?'':'none'; if(match) shown++;
  }});
  var em=document.querySelector('.dl-empty'); if(em) em.style.display=shown?'none':'block';
}}
function fmt(n){{return n.toLocaleString('en-US');}}
function recalc(){{
  var rate=parseFloat(document.getElementById('rate').value)||0;
  // every $ element carries data-h (hours) -> value = hours*rate
  document.querySelectorAll('.money').forEach(function(e){{e.textContent=fmt(Math.round(parseFloat(e.dataset.h)*rate));}});
  document.querySelectorAll('.bar-val').forEach(function(e){{if(e.dataset.hours===undefined)return;var h=parseFloat(e.dataset.hours);e.textContent=h+'h · $'+fmt(Math.round(h*rate));}});
  document.querySelectorAll('.g-v').forEach(function(e){{e.textContent='$'+fmt(Math.round(parseFloat(e.dataset.hours)*rate));}});
}}
document.getElementById('rate').addEventListener('input',recalc);
recalc();
</script>
</body></html>"""
    open(out_path,"w",encoding="utf-8").write(H)
    print("wrote",out_path,"(%.0f KB)"%(len(H)/1024))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",default="working/cowork_roi_data.json")
    ap.add_argument("--out",default="output/cowork-roi-report.html")
    ap.add_argument("--anonymize",action="store_true",
                    help="Team-safe view: no person name, no project/chat names, no JTBD/prompt detail — "
                         "Job/Pillar show totals only; Deliverables show type + date + skills only.")
    a=ap.parse_args()
    build(json.load(open(a.data)),a.out,anon=a.anonymize)
