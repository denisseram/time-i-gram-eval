#!/usr/bin/env python3
"""Size of each deliverable under runs/, for the deliverable_lines / deliverable_chars columns.

Counts non-blank lines and characters, without comments (// and /* */ for HTML/JS, # for R; JSON has none).
JSON is re-serialised compactly first, so formatting style does not change its size.

Usage:  python3 scripts/measure.py            -> CSV on stdout: run_dir,deliverable,lines,chars
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DELIVERABLES = ["index.html", "spec.vl.json", "plot.R", "spec.json"]


def strip(path, text):
    if path.suffix == ".json":
        compact = json.dumps(json.loads(text), separators=(",", ":"))
        pretty = json.dumps(json.loads(text), indent=1)
        return pretty, compact
    if path.suffix == ".R":
        lines = [re.sub(r"(^|\s)#.*$", "", l) for l in text.splitlines()]
    else:
        text = re.sub(r"/\*.*?\*/|<!--.*?-->", "", text, flags=re.S)
        lines = [re.sub(r"(^|\s)//.*$", "", l) for l in text.splitlines()]
    body = "\n".join(l.rstrip() for l in lines if l.strip())
    return body, re.sub(r"\s+", " ", body)


writer = sys.stdout
writer.write("run_dir,deliverable,lines,chars\n")
for run_dir in sorted(ROOT.glob("runs/*/*/*/")):
    for name in DELIVERABLES:
        p = run_dir / name
        if p.exists():
            lines_text, chars_text = strip(p, p.read_text())
            n_lines = sum(1 for l in lines_text.splitlines() if l.strip())
            writer.write(f"{run_dir.relative_to(ROOT)},{name},{n_lines},{len(chars_text)}\n")
