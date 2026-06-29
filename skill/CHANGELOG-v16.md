# Cowork ROI Report — v16 (real professional roles + redesigned process view)

## Roles — "what a billing firm would charge" (ported from microsoft/What-I-Did-Copilot)
- The **"Roles Cowork assembled for me"** section now shows the **exact professional roles** the work
  would have needed (Data Analyst, Management Consultant, Software Engineer, Risk & Compliance Analyst,
  …) — not the old fixed 8-archetype map.
- **Primary path:** the harvest LLM tags `professional_roles` per session ("1–2 roles a billing firm
  would charge for this work"). **Fallback:** a 16-role keyword taxonomy (`scripts/roles_taxonomy.json`)
  when none are tagged.
- `compute.py` rolls up role-hours by splitting each session's expert time across its roles; the fixed
  `ROLE` map is removed. Each role name **links** to a job-title search.

## Work-by-business-process — redesigned
- **Dropped the "Task category" column.**
- **Upfront visual:** a Job ▸ Business Process ▸ JTBD map (per-Job cards with the JTBD and hours bars).
- **Toggle:** flip the table's first column between **Business Process** and **Job-to-be-Done**.

## Carried over from v15
- Research-anchored Time Saved + Value hero; speed multiplier secondary; four value pillars; single
  self-contained skill; map-my-work folded in; auto-hiding cost column; chat-only sessions counted;
  nothing hard-coded to any individual.
