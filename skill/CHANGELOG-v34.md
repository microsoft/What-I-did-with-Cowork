# Cowork ROI Report — v34

Category relabeling + a hybrid (rule + LLM) Cowork-fit, answering an honest
critique of the "entirely deterministic" claim.

## Category labels aligned to the report's own names
The methodology reference and `classify.py` comments now use the report's eight
labels consistently (they had drifted to the taxonomy-table wording):
- "Email & communication" → **Email workflows** (Outlook) **and** **Communication
  workflows** (Teams) — kept as two separate categories.
- "Workflow automation" → **Specialized workflows**; "Meeting intelligence" →
  **Meeting workflows**; "Code assistance" → **Write or debug code**; "General
  assistance & Learning" → **General assistance / Other**.

## Communication workflows = Teams-centered
Clarified and enriched: **Communication workflows** covers the same ideas as Email
(synthesizing, posting, triaging, managing) but on **Microsoft Teams** — messages
and channels (chats, channel posts, replies, announcements, @mentions). Email stays
Outlook-centered. `COMMS_SIGNALS` expanded accordingly.

## Cowork-fit is now a two-layer hybrid (rule + LLM review)
Addresses the contradiction of calling a capability judgment "deterministic":
- **Layer 1 — deterministic rule** produces a reproducible baseline grade + reason.
- **Layer 2 — LLM review** may confirm or adjust each grade (per-session
  `cowork_fit_review` in the harvest), because "could another Copilot have done it"
  is judgment, not something a keyword can settle. Each grade is flagged
  **rule-based**, **AI-confirmed**, or **AI-reviewed**, with the rule grade kept for
  transparency (e.g. "M · AI-reviewed [rule said L]"). Every dot's hover now shows
  the reason **and** the method.
- The honesty section is rewritten: category classification is genuinely
  deterministic; Cowork-fit's judgment layer is explicitly *not* infallible and is
  labeled as judgment per project.

## Methodology reference updated
`references/classification-methodology.md` now uses the eight report labels, spells
out Email-vs-Teams, and documents both layers of the Cowork-fit hybrid plus the
corrected honesty/limits.

SKILL.md stays under 20,000 chars with a ≥2,000 buffer; description 960.
