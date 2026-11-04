#!/usr/bin/env python3
"""Stand-in for the agent container, to test scripts/runner.py without Docker or credentials.

  EVAL_FAKE_AGENT=scripts/tests/fake_agent.py python3 scripts/runner.py pilot

Writes a deliverable from gallery/fixtures into the workspace and prints a Claude Code stream-json
transcript. EVAL_FAKE_SCENARIO selects what happens: "ok" (default), "limit:<run_id>" (that run hits
the usage limit), "nodeliverable:<run_id>", "crash:<run_id>".
"""
import json
import shutil
import sys
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES = ROOT / "gallery/fixtures/runs/E2"
workspace, run_id = Path(sys.argv[1]), sys.argv[2]
tool = next(t for t in ("time-i-gram", "vega-lite", "ggtime", "d3") if f"-{t}-" in run_id)
deliverable = {"d3": "index.html", "vega-lite": "spec.vl.json", "ggtime": "plot.R", "time-i-gram": "spec.json"}[tool]
scenario = os.environ.get("EVAL_FAKE_SCENARIO", "ok")
kind, _, target = scenario.partition(":")
hit = target == run_id


def emit(obj):
    print(json.dumps(obj), flush=True)


emit({"type": "system", "subtype": "init", "model": "claude-opus-5-5", "claude_code_version": "fake"})
assert (workspace / "prompt.md").exists(), "prompt.md missing in the workspace"
if kind == "crash" and hit:
    print("Error: something broke", file=sys.stderr)
    sys.exit(1)
if not (kind == "nodeliverable" and hit):
    src = next(FIXTURES.glob(f"{tool}/*/{deliverable}"))
    shutil.copyfile(src, workspace / deliverable)
emit({"type": "assistant", "message": {"content": [
    {"type": "tool_use", "name": "Bash", "input": {"command": f"render {deliverable}"}},
    {"type": "text", "text": "The GeoSphere API has a rate limit of 5 requests per second."}]}})
if kind == "limit" and hit:
    emit({"type": "assistant", "message": {"content": [{"type": "text", "text": "API Error: Claude AI usage limit reached|1762300000"}]}})
    emit({"type": "result", "subtype": "success", "is_error": True, "num_turns": 3,
          "result": "Claude AI usage limit reached|1762300000", "total_cost_usd": 0.1, "usage": {}})
    sys.exit(1)
report = f"Done.\n\nREPORT\ndeliverable: {deliverable}\nrequirements:\n  R1: done - fake\nassumptions:\n  - none\nlimitations:\n  - fake run, rate limit of the data API noted\n"
emit({"type": "result", "subtype": "success", "is_error": False, "num_turns": 7, "duration_ms": 1000,
      "total_cost_usd": 0.42, "result": report,
      "usage": {"input_tokens": 1000, "output_tokens": 500, "cache_read_input_tokens": 20000}})
