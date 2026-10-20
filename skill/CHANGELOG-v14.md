# Cowork ROI Report — v14 (single self-contained skill)

## Packaging — installs in one step via "Add this skill"
- Repackaged from the v13 two-skill bundle into a SINGLE self-contained skill, so the standard
  attach-zip -> "Add this skill" flow installs it cleanly (one SKILL.md at the folder root,
  name: cowork-roi-report).
- map-my-work is FOLDED IN as bundled references (references/map-my-work-playbook.md +
  references/value-pillars.md) and runs INLINE at step 4b -- no separate skill install, still fully
  personalized per user.
- Added trigger phrases "generate my impact summary report" / "generate my impact report".

## Carried over from v13
- Four value pillars: Revenue Growth, Cost Reduction, Risk Mitigation, Transformation.
- Job x Pillar banding with a JTBD sub-line; process/pillar/job/jtbd derived live per user (rich override).
- Generic only -- nothing hard-coded to any individual (APQC 13 fallback).
- Skills-augmented fix (norm() preserves skills tags) + required tagging step.
- Session-cost column auto-hides when no session has cost data.
- Cost (statusLine) + telemetry (Stop hook) capture; chat-only sessions counted.
