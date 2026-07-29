# Methodology — research-anchored bands + two-clock speed multiplier

The **Typical** value is what the report applies; **Low/High** form the published range. Each Typical is a
per-instance figure from a study × the typical instances per Cowork run — not picked from a range.

| Category | Low | **Typical** | High | Source(s) for the Typical value (slide 12) |
|---|---|---|---|---|
| Analysis & Research | 30 | **71** | 92 | Stanford-WB SSRN 5136877 · OpenAI Deep Research · McKinsey 2023 |
| Document & content creation | 12 | **24** | 42 | Microsoft Research 2026 (Verma·Suri·Counts) — causal-impact DiD, n=72,186 |
| Email workflows | 3 | **7** | 12 | Noy & Zhang Science 2023 · NBER w33795 (Dillon 2025) |
| Meeting workflows | 12 | **31** | 45 | Cambon et al. MSR 2024 · Anthropic Agents 2024 · Forrester TEI 2024 |
| Communication workflows | 2 | **4** | 6 | Microsoft WTI 2024 · NBER w33795 (Dillon 2025) |
| Specialized workflows | 10 | **25** | 40 | Forrester TEI Power Automate 2024 · UK GDS Cross-Government 2025 |
| Write or debug code | 30 | **56** | 96 | Cui et al. CACM 2024 · Peng et al. RCT 2023 · Stanford-WB SSRN 5136877 |
| General assistance / Other | 2 | **5** | 8 | Brynjolfsson, Li & Raymond QJE 2025 / NBER w31161 · Microsoft WTI 2024 |

Source URLs are embedded as clickable links inside the generated report's Glossary (`build_report.py`).

**Two-clock model (v5).** The bands above feed the *expert (unassisted) clock*; the report's headline is a
**speed multiplier** and a **professional-services-equivalent value** — there is no ROI/seat-cost figure
(credit & seat consumption isn't available).
- **Expert clock (min/session)** = Σ analysis-band per analysis task + Σ general-band per general task
  + 12 min to read each input source (5 min/image) + an authoring band per output (deck 45 · doc 40 · sheet/page/code 35 · other 30).
  `document` tasks contribute only via output authoring (no double-count with the analysis band).
- **Assisted clock (min/session)** = 8 (prompt/setup) + 2 × (#inputs + #outputs), floor 4 — a modeled estimate;
  prefer a measured `exec_min` when telemetry (`mine_session.py`) provides one.
- **Speed multiplier** = Σ expert ÷ Σ assisted (rate-independent). **Value** = (Σ expert ÷ 60) × hourly rate.
- **Conservative / Optimistic** re-run the expert clock with the floor/ceiling analysis bands and lighter/heavier read & authoring weights.

The report also renders an **Analyzed → Produced** breakdown (inputs analyzed vs. outputs produced, by type) from the same artifact counts.