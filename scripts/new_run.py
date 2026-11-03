#!/usr/bin/env python3
"""Create runs/<example>/<tool>/<run_id>/ with the exact prompt and an empty run.md.

Usage:  python3 scripts/new_run.py E3 vega-lite      -> runs/E3/vega-lite/E3-vega-lite-r01/ (next free number)
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

example, tool = sys.argv[1], sys.argv[2]
entry = next((e for e in json.loads((ROOT / "prompts/index.json").read_text())
              if e["example"] == example and e["tool"] == tool), None)
if entry is None:
    sys.exit(f"no prompt for {example}/{tool}; run scripts/build_prompts.py first")
if entry["status"] != "ready":
    sys.exit(f"{entry['prompt']} is a draft: pin and verify its dataset first")

base = ROOT / "runs" / example / tool
n = 1
while (base / f"{example}-{tool}-r{n:02d}").exists():
    n += 1
run_dir = base / f"{example}-{tool}-r{n:02d}"
run_dir.mkdir(parents=True)
shutil.copyfile(ROOT / entry["prompt"], run_dir / "prompt.md")
run_md = (ROOT / "templates/run.md").read_text().replace("<run_id>", run_dir.name, 1)
(run_dir / "run.md").write_text(run_md)
print(f"{run_dir.relative_to(ROOT)}  (prompt sha256 {entry['sha256'][:12]}, deliverable {entry['deliverable']})")
