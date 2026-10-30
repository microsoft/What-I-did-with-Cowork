> [!IMPORTANT]
> **Disclaimer:** This is not an official Microsoft Cowork skill. It is an approach to understanding your work and how Cowork enriches it. You can customize the skill to meet your requirements.

# cowork-roi-report

Generates a personal "What Cowork Did for Me" HTML impact report from your own Copilot Cowork history.

- `SKILL.md` — skill definition and workflow (loaded by Cowork)
- `scripts/` — deterministic, standard-library Python pipeline (classify → compute → render, optional CSV)
- `references/` — methodology, classification rules and the map-my-work playbook

Install, usage, version history and docs: https://github.com/microsoft/What-I-did-with-Cowork

> Cowork accepts a skill with `SKILL.md` plus at most 20 other files. Keep this folder within that limit
> (`python tools/build_skill_zip.py` checks it).
