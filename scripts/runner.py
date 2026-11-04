#!/usr/bin/env python3
"""Run the evaluation agents in batches (see PROTOCOL.md and env/README.md).

  python3 scripts/runner.py check              everything ready? (image, credentials, prompts, data, freeze)
  python3 scripts/runner.py pilot              one pilot run (E0) per tool; --clean deletes them
  python3 scripts/runner.py init               draw the order of all runs once -> results/schedule.csv
  python3 scripts/runner.py batch --blocks 2   run the next 2 blocks (1 block = one example x the 4 tools)
  python3 scripts/runner.py status             progress, time, tokens, cost
  python3 scripts/runner.py render <run dir>   redo the official render of one run

Every run happens in a new container with an empty folder that holds only prompt.md. Progress is kept in
runs/: a finished run has status.json with "status": "done" and is never run again, so a batch can be
stopped at any time and resumed later with the same command. A run cut off by the usage limit (or by any
other error that is not the agent's fault) is moved to runs/_interrupted/ and run again from scratch later.
"""
import argparse
import csv
import datetime as dt
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "scripts/run_config.json").read_text())
RUNS = ROOT / "runs"
INTERRUPTED = RUNS / "_interrupted"
SCHEDULE = ROOT / "results/schedule.csv"
METRICS = ROOT / "results/metrics.csv"
FREEZE_TAG = "v1-frozen"
FROZEN_PATHS = ["prompts", "tasks", "tools", "rubrics", "datasets/manifest.json", "scripts/run_config.json", "env"]
DELIVERABLE = {"d3": "index.html", "vega-lite": "spec.vl.json", "ggtime": "plot.R", "time-i-gram": "spec.json"}
# Testing only: a script that stands in for the agent container (see scripts/tests/fake_agent.py).
FAKE_AGENT = os.environ.get("EVAL_FAKE_AGENT")

# Messages Claude Code gives when the plan's usage limit is reached. Only Claude Code's own messages are
# searched (final result, API errors, stderr), never the agent's work, which may mention rate limits of a data API.
STRONG_LIMIT = re.compile(r"usage limit reached|limit reached\|\d+|hit your (usage |session |weekly )?limit|"
                          r"out of extra usage|limit will reset|resets at", re.I)
WEAK_LIMIT = re.compile(r"rate[ _-]?limit|\b429\b|quota", re.I)
AUTH_ERROR = re.compile(r"invalid api key|authentication[_ ]error|please run /login|not logged in|"
                        r"oauth token.*(expired|invalid)|\b401\b", re.I)
RENDER_CALL = re.compile(r"(^|[\s;&|(])render\s+\S")


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def say(msg=""):
    print(msg, flush=True)


# --------------------------------------------------------------------------------------------- setup


def load_dotenv():
    """KEY=VALUE lines from .env in the repository root (never committed: see .gitignore)."""
    env_file = ROOT / ".env"
    if env_file.exists():
        lines = []
        for line in env_file.read_text().splitlines():
            if lines and line.strip() and "=" not in line and not line.strip().startswith("#"):
                lines[-1] += line.strip()  # continuation of a token pasted over two lines
            else:
                lines.append(line)
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                value = value.strip().strip('"').strip("'")
                if key.strip() in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY"):
                    value = "".join(value.split())  # a pasted token may carry line breaks or spaces
                os.environ.setdefault(key.strip(), value)


def credential():
    """(variable name, value) of the one credential passed to the agent container."""
    if FAKE_AGENT:
        return ("EVAL_FAKE", "1")
    load_dotenv()
    oauth, api = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"), os.environ.get("ANTHROPIC_API_KEY")
    if oauth and api:
        sys.exit("Both CLAUDE_CODE_OAUTH_TOKEN and ANTHROPIC_API_KEY are set. Keep only one: the token uses your\n"
                 "Claude plan, the API key is billed per use (see env/README.md).")
    if not (oauth or api):
        sys.exit("No credentials. Put CLAUDE_CODE_OAUTH_TOKEN=... (from `claude setup-token`) in the file .env\n"
                 "in the repository root (see env/README.md).")
    return ("CLAUDE_CODE_OAUTH_TOKEN", oauth) if oauth else ("ANTHROPIC_API_KEY", api)


def prompt_entry(example, tool):
    index = json.loads((ROOT / "prompts/index.json").read_text())
    entry = next((e for e in index if e["example"] == example and e["tool"] == tool), None)
    if entry is None:
        sys.exit(f"no prompt for {example}/{tool}: run scripts/build_prompts.py")
    if entry["status"] != "ready":
        sys.exit(f"{entry['prompt']} is a draft (its dataset is not verified)")
    return entry


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)


def freeze_problem():
    """None if the frozen materials are unchanged since the freeze tag, else the reason."""
    if git("rev-parse", "-q", "--verify", f"refs/tags/{FREEZE_TAG}").returncode != 0:
        return f"tag {FREEZE_TAG} does not exist yet"
    changed = git("diff", "--name-only", FREEZE_TAG, "--", *FROZEN_PATHS).stdout.split()
    untracked = git("ls-files", "--others", "--exclude-standard", "--", *FROZEN_PATHS).stdout.split()
    if changed or untracked:
        return f"changed since {FREEZE_TAG}: {', '.join((changed + untracked)[:5])}"
    return None


def image_versions():
    if FAKE_AGENT:
        return "fake agent (test mode)"
    r = subprocess.run(["docker", "run", "--rm", CONFIG["image"], "cat", "/opt/versions.txt"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Docker image {CONFIG['image']} not available. Build it first: docker build -t {CONFIG['image']} env/\n"
                 f"{r.stderr.strip()[:500]}")
    return r.stdout.strip()


# ----------------------------------------------------------------------------------------- one run


def agent_command(workspace, run_id, var):
    if FAKE_AGENT:
        return [sys.executable, FAKE_AGENT, str(workspace), run_id]
    claude = (f'timeout --signal=TERM --kill-after=30 {CONFIG["timeout_seconds"]} claude -p "$(cat prompt.md)" '
              f'--model {CONFIG["model"]} --max-turns {CONFIG["max_turns"]} '
              f'--output-format stream-json --verbose --dangerously-skip-permissions')
    return ["docker", "run", "--rm", "--name", f"eval-{run_id}", "-v", f"{workspace}:/work", "-w", "/work",
            "-e", var, CONFIG["image"], "bash", "-c", claude]


def render_command(folder, deliverable):
    if FAKE_AGENT:
        return ["node", str(ROOT / "env/render/render.mjs"), str(folder / deliverable)]
    return ["docker", "run", "--rm", "-v", f"{folder}:/work", "-w", "/work", CONFIG["image"], "render", deliverable]


def parse_transcript(path):
    info = {"result": None, "model": None, "claude_code_version": None, "tool_calls": 0, "render_calls": 0,
            "api_errors": [], "last_text": ""}
    for line in path.read_text(errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        kind = obj.get("type")
        if kind == "system" and obj.get("subtype") == "init":
            info["model"] = obj.get("model")
            info["claude_code_version"] = obj.get("claude_code_version")
        elif kind == "assistant":
            for block in (obj.get("message") or {}).get("content") or []:
                if block.get("type") == "text":
                    text = block.get("text", "")
                    info["last_text"] = text
                    if text.startswith("API Error") or STRONG_LIMIT.search(text[:300]):
                        info["api_errors"].append(text[:500])
                elif block.get("type") == "tool_use":
                    info["tool_calls"] += 1
                    command = (block.get("input") or {}).get("command", "")
                    if block.get("name") == "Bash" and RENDER_CALL.search(command):
                        info["render_calls"] += 1
        elif kind == "result":
            info["result"] = obj
    return info


def classify(exit_code, info, stderr):
    """done | limit | error, and a one-line reason."""
    result = info["result"] or {}
    claude_texts = [*info["api_errors"], stderr]
    if result:
        claude_texts.append(str(result.get("result", ""))[:1000])
    failed = bool(result.get("is_error")) or result.get("subtype") not in (None, "success", "error_max_turns")
    if any(STRONG_LIMIT.search(t) for t in claude_texts) or (
            (failed or not result) and any(WEAK_LIMIT.search(t) for t in claude_texts)):
        return "limit", "usage limit reached"
    if any(AUTH_ERROR.search(t) for t in claude_texts) and (failed or not result):
        return "error", "authentication failed"
    if exit_code in (124, "host-timeout"):
        return "done", f"stopped at the {CONFIG['timeout_seconds'] // 60}-minute limit"
    if not result:
        return "error", f"no result from Claude Code (exit code {exit_code})"
    if result.get("subtype") == "error_max_turns":
        return "done", f"stopped at the {CONFIG['max_turns']}-turn limit"
    if result.get("subtype") == "success":
        return "done", "finished"
    return "error", f"Claude Code ended with {result.get('subtype')}"


def extract_report(text):
    i = text.rfind("REPORT")
    return text[i:].replace("```", "").strip() + "\n" if i >= 0 else ""


def scrub(folder, secret):
    """Remove the credential from every saved text file (an agent could print its environment)."""
    if not secret or len(secret) < 8:
        return
    for f in folder.rglob("*"):
        if f.is_file() and f.stat().st_size < 50_000_000:
            try:
                text = f.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            if secret in text:
                f.write_text(text.replace(secret, "***"))


def copy_workspace(workspace, dest):
    """Everything the agent left in its folder, except large files (usually downloaded data)."""
    limit = CONFIG["keep_workspace_file_max_mb"] * 1_000_000
    skipped = []
    for f in sorted(workspace.rglob("*")):
        rel = f.relative_to(workspace)
        if any(part.startswith(".") for part in rel.parts) or not f.is_file():
            continue
        if f.stat().st_size > limit:
            skipped.append(f"{rel} ({f.stat().st_size // 1_000_000} MB)")
            continue
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest / rel)
    return skipped


def official_render(run_dir, tool):
    """Render the deliverable exactly as the Tool section says, in a separate folder; keep the outputs."""
    deliverable = DELIVERABLE[tool]
    folder = run_dir / "render"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir()
    os.chmod(folder, 0o777)
    shutil.copy2(run_dir / deliverable, folder / deliverable)
    r = subprocess.run(render_command(folder, deliverable), capture_output=True, text=True, timeout=900)
    (run_dir / "console.txt").write_text(r.stdout + (("\n" + r.stderr) if r.stderr.strip() else ""))
    for name in ("render.png", "plot.png", "plot.svg"):
        if (folder / name).exists():
            shutil.copy2(folder / name, run_dir / name)
    return r.returncode == 0


def run_one(example, tool, run_id, versions):
    """Run one agent end to end. Returns the status: done | limit | error."""
    run_dir = RUNS / example / tool / run_id
    status_file = run_dir / "status.json"
    if status_file.exists() and json.loads(status_file.read_text()).get("status") == "done":
        return "done"
    stamp = now().strftime("%Y%m%dT%H%M%SZ")
    if run_dir.exists():  # left over from a crash of this script: keep it aside, start again
        INTERRUPTED.mkdir(parents=True, exist_ok=True)
        shutil.move(str(run_dir), str(INTERRUPTED / f"{run_id}-{stamp}-incomplete"))

    entry = prompt_entry(example, tool)
    var, secret = credential()
    run_dir.mkdir(parents=True)
    shutil.copyfile(ROOT / entry["prompt"], run_dir / "prompt.md")
    template = (ROOT / "templates/run.md").read_text().replace("<run_id>", run_id, 1)
    (run_dir / "run.md").write_text(template)

    workspace = Path(tempfile.mkdtemp(prefix=f"{run_id}-"))
    os.chmod(workspace, 0o777)
    shutil.copyfile(run_dir / "prompt.md", workspace / "prompt.md")
    started = now()
    say(f"  {run_id}: running (started {started.astimezone():%H:%M}, at most "
        f"{CONFIG['timeout_seconds'] // 60} min) ...")
    env = dict(os.environ, **{var: secret})
    with open(run_dir / "transcript.jsonl", "w") as out, open(run_dir / "agent-stderr.txt", "w") as err:
        try:
            exit_code = subprocess.run(agent_command(workspace, run_id, var), stdout=out, stderr=err, env=env,
                                       timeout=CONFIG["timeout_seconds"] + 180).returncode
        except subprocess.TimeoutExpired:
            exit_code = "host-timeout"
            if not FAKE_AGENT:
                subprocess.run(["docker", "kill", f"eval-{run_id}"], capture_output=True)
    finished = now()

    skipped = copy_workspace(workspace, run_dir / "workspace")
    shutil.rmtree(workspace, ignore_errors=True)
    scrub(run_dir, secret)
    info = parse_transcript(run_dir / "transcript.jsonl")
    status, reason = classify(exit_code, info, (run_dir / "agent-stderr.txt").read_text(errors="replace"))

    deliverable = DELIVERABLE[tool]
    has_deliverable = (run_dir / "workspace" / deliverable).exists()
    if has_deliverable:
        shutil.copy2(run_dir / "workspace" / deliverable, run_dir / deliverable)
    final_text = str((info["result"] or {}).get("result") or info["last_text"])
    (run_dir / "report.txt").write_text(extract_report(final_text) or "(no REPORT block in the agent's answer)\n")

    render_ok = official_render(run_dir, tool) if status == "done" and has_deliverable else False
    result = info["result"] or {}
    usage = result.get("usage") or {}
    meta = {
        "run_id": run_id, "example": example, "tool": tool, "status": status, "reason": reason,
        "started": started.isoformat(), "finished": finished.isoformat(),
        "wall_seconds": int((finished - started).total_seconds()), "exit_code": exit_code,
        "prompt_sha256": entry["sha256"], "model_requested": CONFIG["model"], "model": info["model"],
        "claude_code_version": info["claude_code_version"], "max_turns": CONFIG["max_turns"],
        "timeout_seconds": CONFIG["timeout_seconds"], "turns": result.get("num_turns"),
        "tool_calls": info["tool_calls"], "render_calls": info["render_calls"],
        "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
        "cache_read_tokens": usage.get("cache_read_input_tokens"),
        "cache_creation_tokens": usage.get("cache_creation_input_tokens"),
        "cost_usd_reported": result.get("total_cost_usd"), "credential": var,
        "deliverable_present": has_deliverable, "render_ok": render_ok,
        "workspace_files_not_kept": skipped, "image_versions": versions,
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    status_file.write_text(json.dumps({"status": status, "reason": reason, "finished": finished.isoformat()}) + "\n")

    if status != "done":
        INTERRUPTED.mkdir(parents=True, exist_ok=True)
        shutil.move(str(run_dir), str(INTERRUPTED / f"{run_id}-{stamp}-{status}"))
    mins = meta["wall_seconds"] // 60
    say(f"  {run_id}: {status} - {reason}; {mins} min, {meta['turns']} turns, render "
        f"{'OK' if render_ok else 'failed' if status == 'done' and has_deliverable else '-'}"
        f"{'' if has_deliverable or status != 'done' else ', NO deliverable'}")
    write_metrics()
    return status


# ------------------------------------------------------------------------------------ bookkeeping


def read_schedule():
    if not SCHEDULE.exists():
        sys.exit("No schedule yet: run `python3 scripts/runner.py init` first.")
    with SCHEDULE.open() as f:
        return list(csv.DictReader(f))


def run_status(row):
    f = RUNS / row["example"] / row["tool"] / row["run_id"] / "status.json"
    return json.loads(f.read_text()).get("status") if f.exists() else "pending"


def all_meta():
    for f in sorted(RUNS.glob("*/*/*/meta.json")):
        if not f.parts[-4].startswith("_"):
            yield json.loads(f.read_text())


def write_metrics():
    cols = ["run_id", "example", "tool", "status", "reason", "started", "wall_seconds", "turns", "tool_calls",
            "render_calls", "input_tokens", "output_tokens", "cache_read_tokens", "cache_creation_tokens",
            "cost_usd_reported", "deliverable_present", "render_ok", "model", "claude_code_version", "credential"]
    METRICS.parent.mkdir(exist_ok=True)
    with METRICS.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for meta in all_meta():
            w.writerow(meta)


# --------------------------------------------------------------------------------------- commands


def cmd_check(_args):
    ok = True
    def line(good, text):
        nonlocal ok
        ok &= good
        say(f"  [{'ok' if good else '!!'}] {text}")
    say("Checks before running:")
    r = subprocess.run([sys.executable, str(ROOT / "scripts/build_prompts.py"), "--check"], capture_output=True, text=True)
    line(r.returncode == 0, "prompts up to date and identical outside the Tool section"
         if r.returncode == 0 else f"prompts: {r.stdout.strip()[:300]}")
    index = json.loads((ROOT / "prompts/index.json").read_text())
    drafts = sorted({e["example"] for e in index if e["status"] != "ready" and e["example"] in CONFIG["examples"]})
    line(not drafts, "all evaluation prompts ready" if not drafts else f"draft prompts: {', '.join(drafts)}")
    r = subprocess.run([sys.executable, str(ROOT / "scripts/verify_data.py")], capture_output=True, text=True)
    line(r.returncode == 0, "data files unchanged (verify_data.py)" if r.returncode == 0
         else f"data: {r.stdout.strip()[-300:]}")
    problem = freeze_problem()
    line(problem is None, f"frozen at tag {FREEZE_TAG}" if problem is None
         else f"not frozen: {problem} (needed for `batch`, not for `pilot`)")
    try:
        var, _ = credential()
        line(True, f"credential: {var}")
    except SystemExit as e:
        line(False, str(e).splitlines()[0])
    try:
        versions = image_versions()
        line(True, f"image {CONFIG['image']}: " + "; ".join(versions.splitlines()[:3]))
    except SystemExit as e:
        line(False, str(e).splitlines()[0])
    line(SCHEDULE.exists(), "schedule drawn (results/schedule.csv)" if SCHEDULE.exists()
         else "no schedule yet (`init`)")
    sys.exit(0 if ok else 1)


def cmd_init(args):
    if SCHEDULE.exists() and not args.force:
        sys.exit(f"{SCHEDULE.relative_to(ROOT)} exists already. The order is drawn once; use --force only before any run.")
    rng = random.Random(CONFIG["seed"])
    blocks = [(e, r) for e in CONFIG["examples"] for r in range(1, CONFIG["repeats"] + 1)]
    rng.shuffle(blocks)
    rows, order = [], 0
    for b, (example, rep) in enumerate(blocks, 1):
        tools = list(CONFIG["tools"])
        rng.shuffle(tools)
        for tool in tools:
            order += 1
            rows.append({"order": order, "block": b, "example": example, "repeat": rep, "tool": tool,
                         "run_id": f"{example}-{tool}-r{rep:02d}"})
    SCHEDULE.parent.mkdir(exist_ok=True)
    with SCHEDULE.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    say(f"{len(rows)} runs in {len(blocks)} blocks (seed {CONFIG['seed']}) -> {SCHEDULE.relative_to(ROOT)}")
    say("First blocks: " + ", ".join(f"{e} r{r}" for e, r in blocks[:4]) + ", ...")


def cmd_batch(args):
    problem = freeze_problem()
    if problem and not args.allow_unfrozen:
        sys.exit(f"Not frozen: {problem}.\nFreeze first (see README), or use --allow-unfrozen for a test.")
    rows = read_schedule()
    credential()
    versions = image_versions()
    blocks = {}
    for row in rows:
        blocks.setdefault(int(row["block"]), []).append(row)
    todo = [b for b in sorted(blocks) if any(run_status(r) != "done" for r in blocks[b])][: args.blocks]
    if not todo:
        say("All runs are done.")
        return
    for b in todo:
        rows_b = blocks[b]
        say(f"Block {b}/{len(blocks)}: {rows_b[0]['example']} repeat {rows_b[0]['repeat']} "
            f"({', '.join(r['tool'] for r in rows_b)})")
        for row in rows_b:
            if run_status(row) == "done":
                continue
            status = run_one(row["example"], row["tool"], row["run_id"], versions)
            if status == "limit":
                say("\nUsage limit reached. The interrupted run was set aside in runs/_interrupted/ and will be run "
                    "again from scratch.\nRun the same command again after your limit resets "
                    "(claude.ai -> Settings -> Usage shows when).")
                sys.exit(2)
            if status == "error":
                say("\nThe run failed for a reason that is not the agent's work (see runs/_interrupted/, file "
                    "agent-stderr.txt). Stopped; fix it and run the same command again.")
                sys.exit(3)
    say("")
    cmd_status(args)


def cmd_pilot(args):
    pilot = CONFIG["pilot_example"]
    if args.clean:
        shutil.rmtree(RUNS / pilot, ignore_errors=True)
        write_metrics()
        say(f"Deleted runs/{pilot}/.")
        return
    versions = image_versions()
    for tool in args.tools or CONFIG["tools"]:
        n = 1
        while (RUNS / pilot / tool / f"{pilot}-{tool}-p{n:02d}").exists():
            n += 1
        status = run_one(pilot, tool, f"{pilot}-{tool}-p{n:02d}", versions)
        if status != "done":
            say("Pilot stopped (see runs/_interrupted/).")
            sys.exit(2)
    say("Pilot done. Look at runs/E0/*/*/ (render.png, console.txt, report.txt, meta.json) and at the gallery.")


def cmd_status(_args):
    rows = read_schedule() if SCHEDULE.exists() else []
    if rows:
        statuses = [run_status(r) for r in rows]
        done = statuses.count("done")
        say(f"Runs done: {done}/{len(rows)}")
        say("            " + "  ".join(f"{t:>12}" for t in CONFIG["tools"]))
        for e in CONFIG["examples"]:
            cells = []
            for t in CONFIG["tools"]:
                rs = [s for r, s in zip(rows, statuses) if r["example"] == e and r["tool"] == t]
                cells.append(f"{rs.count('done')}/{len(rs)}".rjust(12))
            say(f"  {e:<9} " + "  ".join(cells))
        nxt = next((r for r, s in zip(rows, statuses) if s != "done"), None)
        if nxt:
            say(f"Next: block {nxt['block']} ({nxt['example']} repeat {nxt['repeat']}), starting with {nxt['run_id']}")
    else:
        say("No schedule yet (`init`).")
    metas = [m for m in all_meta() if m["example"] in CONFIG["examples"]]
    if metas:
        hours = sum(m["wall_seconds"] for m in metas) / 3600
        cost = sum(m["cost_usd_reported"] or 0 for m in metas)
        tokens = sum((m["input_tokens"] or 0) + (m["output_tokens"] or 0) for m in metas)
        say(f"Agent time {hours:.1f} h, tokens (in+out, without cache) {tokens:,}, cost reported by Claude Code "
            f"${cost:.2f} (with a plan token this is an estimate, not a charge)")
    interrupted = sorted(p.name for p in INTERRUPTED.glob("*")) if INTERRUPTED.exists() else []
    if interrupted:
        say(f"Set aside (not counted, run again): {len(interrupted)}, e.g. {interrupted[-1]}")


def cmd_render(args):
    run_dir = Path(args.run_dir).resolve()
    tool = run_dir.parent.name
    if tool not in DELIVERABLE or not (run_dir / DELIVERABLE[tool]).exists():
        sys.exit(f"{run_dir} is not a run folder with a deliverable")
    ok = official_render(run_dir, tool)
    say((run_dir / "console.txt").read_text())
    sys.exit(0 if ok else 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check").set_defaults(func=cmd_check)
    p = sub.add_parser("init")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("batch")
    p.add_argument("--blocks", type=int, default=1, help="number of blocks (4 runs each) to run now")
    p.add_argument("--allow-unfrozen", action="store_true", help="for tests only")
    p.set_defaults(func=cmd_batch)
    p = sub.add_parser("pilot")
    p.add_argument("--clean", action="store_true", help="delete the pilot runs")
    p.add_argument("--tools", nargs="*", choices=list(DELIVERABLE))
    p.set_defaults(func=cmd_pilot)
    sub.add_parser("status").set_defaults(func=cmd_status)
    p = sub.add_parser("render")
    p.add_argument("run_dir")
    p.set_defaults(func=cmd_render)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
