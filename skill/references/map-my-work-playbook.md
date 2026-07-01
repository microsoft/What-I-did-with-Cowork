# map-my-work — bundled playbook (run inline by step 4b)

This is the workflow-mapping logic, folded into this skill so no separate skill install is
needed. When the report runs, follow this to derive the signed-in user's own taxonomy.

# Map My Work

Turn the user's real Microsoft 365 activity into a structured map of what they do — not a flat list
of meetings, but a four-layer tree that separates durable accountability from churning execution:

```
Job (why the role exists — the outcome owned)
  └─ Business Process (the repeatable machine that produces the outcome — has a customer + a metric)
       └─ Workflow (how the machine runs — steps, handoffs, tools)   [tagged: stakeholder JTBD]
            └─ Task (the atomic unit of effort)
```

Value flows up; work flows down. Capture at **workflow grain** (that is what telemetry shows —
meetings, mail, files, recordings), then roll up to Process and Job.

## When NOT to Use

- "What's on my plate today" / "what did I miss" → **daily-briefing** (single-day, prioritized).
- "Clean up / triage my calendar" → **calendar-management**.
- "Summarize that meeting" / "action items from the standup" → **meeting-intel**.
- "Draft an update for leadership/the team" → **stakeholder-comms**.
- Quantifying Cowork **time saved / ROI value** (not the shape of the work) → use **cowork-roi-report** (that skill calls *this* one for its process taxonomy).
- A quick lookup answerable in one call (one person, one event, one file) — just answer it.

## Inputs & Options

Read these from the user's request; otherwise use the defaults.

| Option | Default | Notes |
|---|---|---|
| Lookback window | ~1 quarter (last ~90 days) | Resolve to explicit dates from current local time. |
| Scope | All substantive work | If the user says "just project work", de-emphasize admin/expense/OOO/newsletter noise. |
| Output | Inline map | If the user asks for a doc/one-pager/deck, also produce a file (see Output). |
| OKR layer | Off unless provided | Viva Goals is **not reachable**; if the user pastes OKRs, fold them in as an alignment layer. |
| Focus filter | None | e.g. "just my customer-facing work" → restrict the tree to that branch. |

## Deriving the taxonomy (per user — nothing pre-seeded)

There is **no fixed spine**. Derive the **signed-in user's own** Jobs and Business Processes from
*their* observed work — named in their language, from their footprint. Different roles produce
different taxonomies (a clinician's processes are not a marketer's). Keep names stable across that
user's successive maps so they stay comparable, but **never impose another person's categories**.

## Workflow

Create a short task list (`TaskCreate`/`TaskUpdate`) so progress is visible, then:

### 1. Anchor the role (cheap context, run first)
- `mcp__me_profile__GetMyDetails` (title, department, office) — a thin anchor.
- `mcp__me_profile__GetDirectReportsDetails` and `mcp__me_profile__GetManagerDetails` — the org graph
  is the more useful part: it lets you attribute "management" workflows and label collaborators.

### 2. Gather signals across sources (run in PARALLEL — independent calls in one batch)
Strongest signals first; cast wide, then cluster.
- **Sent mail** (highest signal — what the user *drives*): `mcp__outlook__ListMessages` with
  `folder_id="sentitems"`, `received_after=<window start>`, `top=40` then paginate via `next_link`.
- **Received mail** (incoming threads, asks): `mcp__outlook__ListMessages` over the window; ignore
  newsletters/automated noise when scope is "project work".
- **Teams chats**: `mcp__m365_teams__ListChats` (recent 1:1 + group). For active project channels,
  `mcp__m365_teams__ListTeams` → `mcp__m365_teams__ListChannels` → `mcp__m365_teams__ListChannelMessages`.
- **Calendar (recurring-series detection)**: `mcp__outlook_calendar__ListCalendarView` across the
  window. Recurring series = the backbone of workflows (weekly LT, biweekly syncs, monthly 1:1s).
- **Files**: `mcp__m365_search__SearchM365` with `sources=["files"]` using the user's domain keywords;
  recently-modified, user-authored docs reveal active deliverables.
- **Recordings**: `mcp__graph__GetMyRecentTranscripts` over the window — inventory by subject; read a
  few recurring ones with `GetMeetingTranscript` only if you need to confirm what a workflow produces.
- **Power BI artifacts** (useful for analytics/reporting roles): `SearchM365` with
  `sources=["powerbi"]` — owned/used reports are workflows made concrete. Reference with the bracketed
  `[rpt_N]` alias.

Note: To-Do / Planner is **not available** (no permission) — do not attempt it.

### 3. Cluster → build the tree
1. Dedup signals; cluster by theme, scored by **frequency × recency**.
2. Name each cluster as a **Workflow** (a running sequence with a trigger and an output), in the
   user's own language. Keep names consistent with that user's prior maps; never force-fit onto
   another role's categories.
3. Tag each workflow with the **stakeholder JTBD** it serves — the outcome a specific stakeholder
   "hires" the work for (e.g. "my manager needs a decision-ready summary"; "a customer needs to
   control their spend") — this separates load-bearing work from busywork.
3a. Tag each workflow with its **value pillar** — Revenue Growth · Cost Reduction · Risk Mitigation · Transformation —
   using the crosswalk in [references/value-pillars.md](references/value-pillars.md) (intent-verb rule
   wins; else the process default). This is the single source of truth for pillar mapping, shared with
   `cowork-roi-report`. Empty pillars render as zero, never hidden.
4. Roll workflows up into **Business Processes** (repeatable machine; name its customer + its metric).
5. Roll processes up into **Jobs** (durable accountability; test: "remove me for a month — what value
   disappears, for whom?").
6. If OKRs were pasted, attach each to the Job/Process it advances and flag any unmapped objective.

### 4. Synthesize & deliver
Present the map (see Output). End with the **operating-model read**: which workflows are candidates to
**automate** (skills/schedules), which processes to **delegate** (set owner + metric), and which jobs
to **keep** (your judgment).

### 5. Handoff to `cowork-roi-report` (when invoked by the ROI report)
When invoked by `cowork-roi-report`, return — for **each session id** passed in — a compact object
`{process, pillar, job, jtbd}`, drawn from the tree you derived for *this* user plus the pillar
crosswalk ([references/value-pillars.md](references/value-pillars.md)). The ROI report writes these
verbatim into the per-run scratch file `working/process_overrides.json` (never into any skill's
`scripts/` folder) and renders them as the Job × Pillar bands. Emit only the runner's own taxonomy —
nothing hard-coded or borrowed from another user.

## Output Format

Default = **inline markdown**, in this order:
1. **Role anchor** — one line (title · org · reports · manager).
2. **The map** — grouped by Job, then Process, then Workflow (with cadence, what it produces, key
   collaborators, a `JTBD:` tag, and a `Pillar:` tag). Keep Tasks as a short illustrative trace, not
   exhaustive. Optionally add a **by-pillar rollup** (Revenue Growth / Cost Reduction / Risk
   Mitigation / Transformation) so work can be read against the business-value pillars.
3. **Objectives** — paste-in OKRs if provided; otherwise *de facto* objectives, clearly labelled as
   inferred and anchored to evidence.
4. **Operating-model read** — automate / delegate / keep.
5. **Sources used** — one line listing which signals were read and any gaps (e.g. "no OKR artifact found").

If the user asks for a file: a one-pager → **docx**; a visual tree / leadership view → **pptx**;
a tracker of workflows×processes → **xlsx**. Save to `output/` and confirm via the delivery gate.

## Failure Handling & Edge Cases

Map gracefully under partial data — a smaller, honest map beats a confident wrong one.

- **A source returns nothing or errors**: retry once; if still empty, continue with the other sources
  and record the gap explicitly in "Sources used" (e.g. "no recordings found in window"). Never
  fabricate to fill a silent source.
- **Partial pagination**: if a source returns `next_link` and the window isn't fully covered, keep
  paging until covered or clearly sufficient. If you stop early, state how many pages / what date
  range you read and offer to continue — never present a partial pull as complete.
- **Throttling or transient tool failure**: wait briefly and retry once; if it persists, note the
  degraded coverage in plain language rather than failing the whole map.
- **Ambiguous person**: resolve via people tools; if multiple equally-likely matches remain, attribute
  to the role/team rather than guessing an individual.
- **Thin signal / short tenure**: if the window holds little activity, widen it once (e.g. to ~6
  months) and say so; do not infer a workflow from one or two data points.
- **No OKRs available**: Viva Goals isn't reachable — present de facto objectives clearly labelled as
  inferred, and invite the user to paste OKRs.
- **Conflicting signals**: surface the conflict and the evidence on each side instead of silently
  picking one.
- **Sparse or ambiguous role**: if the work doesn't cluster cleanly into processes, present the
  clearest few and label the remainder "Other" rather than inventing a tidy taxonomy.
- **File deliverable requested**: after writing to `output/`, confirm the file exists before telling
  the user it's ready; if missing, locate and move it, then re-confirm.

## Guardrails

- **Ground every claim in a tool result.** Never invent workflows, collaborators, dates, or metrics.
  If a source returns nothing, say so — report coverage gaps rather than bridging them.
- **Calendar privacy**: for events marked private/confidential or personal (medical, interview,
  personal appointments), surface only a time block ("Private appointment") — never the raw subject.
- **No performance evaluation**: map work and outcomes, never rank or assess individual people.
- **Paginate** when a source returns `next_link` and coverage is incomplete; disclose how much was read.
- **De-duplicate** the same meeting/thread arriving from multiple sources before counting frequency.
- **Reproducible, not real-time-judgmental**: this maps observed work; it is not a productivity score.
- **Context links**: bracket every alias used in the output (`[rpt_N]`, `[evt_N]`, `[msg_N]`); never
  duplicate the display name next to the chip.
