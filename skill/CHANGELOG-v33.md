# Cowork ROI Report — v33

Cowork-fit refinements + a new methodology reference.

## Cowork-fit (`scripts/compute.py`)
- **Specialized workflows now grade High by default.** Automation, connectors,
  scheduled/recurring prompts and skill builds are Cowork-native — no in-app
  Copilot runs them — so they are a High match almost every time. (Previously the
  three skill-management sessions were graded "M / Managing Cowork".)
- **Cross-session orchestration is now detected.** A deliverable built across two
  sessions (e.g. identify the emails in one session, build the Excel tracker in
  another) unions the surfaces from every contributing session, so it reads as
  **cross-surface (H)** in both — fixing "Build the value-story tracker" being
  graded Low when it is really an Outlook→Excel effort.
- Net on the sample window: Cowork-fit moves to **7 H · 0 M · 1 L** (the lone L is
  the single-surface PowerPoint chart redesign).

## Hover reasons (`scripts/build_report.py`)
- Every H/M/L dot already carries a **project-specific reason**; v33 adds a
  `cursor:help` + hover ring so the dots are visibly hoverable, and a new
  "Specialized workflow" reason string.

## New: methodology reference (`references/classification-methodology.md`)
- A plain-language explainer of **both** classifications — how a session is placed
  into a **task category** (Analysis & Research, Document & content creation,
  Specialized workflows, …) per the Cowork usage taxonomy, and how the
  **Cowork-fit H/M/L** grade is decided via the single-surface test. Includes the
  cross-session rule and the honesty/limits section. SKILL.md links to it.

No methodology-band or value-model change. SKILL.md stays under 20,000 chars with
a ≥2,000 buffer; description 960.
