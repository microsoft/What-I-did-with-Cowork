# v47 — Final output format breaks ties

- When more than one category fits a session, the **format of its final deliverable decides** (latest-created primary output; notes, logs, JSON and screenshots are skipped unless nothing else exists). PRIORITY is only the fallback when there is no deliverable or its format matches none of the candidates.
- Outside-M365 systems (v46) are now a Specialized *candidate*, not an override: CRM data that ends in a deck → Document & content creation; CRM work with no saved deliverable → Specialized workflows.
- Unchanged hard rules: email final output / inbox triage → Email; Teams post / mainly Teams synthesis → Communication; skill build/attach/install/review → Write or debug code.
- `classify.py` now carries each output's `created` timestamp through so the final output can be identified.
