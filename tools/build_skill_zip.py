"""Validate the skill/ folder against Cowork's upload limits and build the release zip.

Cowork rejects a skill archive with more than SKILL.md + 20 other files.

    python tools/build_skill_zip.py            # validate only
    python tools/build_skill_zip.py --out cowork-roi-report-skill-v49.zip
"""
import argparse
import pathlib
import sys
import zipfile

MAX_OTHER_FILES = 20
ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL = ROOT / "skill"


def skill_files():
    return sorted(
        p for p in SKILL.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    )


def validate(files):
    errors = []
    rel = [p.relative_to(SKILL).as_posix() for p in files]
    if "SKILL.md" not in rel:
        errors.append("skill/SKILL.md is missing")
    others = [r for r in rel if r != "SKILL.md"]
    if len(others) > MAX_OTHER_FILES:
        errors.append(
            f"skill/ has {len(others)} files besides SKILL.md; Cowork allows at most {MAX_OTHER_FILES}"
        )
    return rel, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="zip path to write (files only, no directory entries)")
    args = ap.parse_args()

    files = skill_files()
    rel, errors = validate(files)
    for r in rel:
        print(" ", r)
    print(f"{len(rel)} files (SKILL.md + {len(rel) - 1} others, limit {MAX_OTHER_FILES})")
    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        return 1

    if args.out:
        out = pathlib.Path(args.out)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for p, r in zip(files, rel):
                z.write(p, r)
        with zipfile.ZipFile(out) as z:
            n = len(z.namelist())
        print(f"wrote {out} ({n} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
