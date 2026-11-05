#!/usr/bin/env python3
"""Score the runs: a local app for the human evaluator, and the summary of all scores (see EVALUATION.md).

  python3 scripts/score.py blind        once: anonymous codes for the screenshots -> results/blind_key.csv
  python3 scripts/score.py serve        the scoring app at http://127.0.0.1:8800 (Ctrl+C to stop)
  python3 scripts/score.py progress     how many scores are in, per phase
  python3 scripts/score.py summary      agreement with the judge, final results/scores.csv, results/summary.md

Phases of the app:
  1 blind   static requirements, on anonymized screenshots (example shown, tool and run hidden)
  2 live    interactive requirements (E3, E5) in the live render, with before/after screenshots, and
            requirements that need the code (E5 R6); the tool is visible here

Scores are saved at every click in results/scores-<evaluator>.csv (long format, one row per requirement).
"""
import argparse
import base64
import csv
import io
import subprocess
import datetime as dt
import json
import math
import random
import re
import os
import statistics
import sys
import tempfile
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCFG = json.loads((ROOT / "scripts/score_config.json").read_text())
RCFG = json.loads((ROOT / "scripts/run_config.json").read_text())
RESULTS = ROOT / "results"
KEY = RESULTS / "blind_key.csv"
LIB = ROOT / "gallery/node_modules"
DELIVERABLE = {"d3": "index.html", "vega-lite": "spec.vl.json", "ggtime": "plot.R", "time-i-gram": "spec.json"}
SCORE_COLS = ["evaluator", "phase", "item", "example", "requirement", "score", "note", "updated"]
WRITE_LOCK = threading.Lock()  # the app saves from several threads; one read-modify-write at a time


# ------------------------------------------------------------------------------------- materials


def requirements(example):
    """[(id, text)] from tasks/<example>.md ("- **R1.** ..." with indented continuation lines)."""
    reqs, cur = [], None
    for line in (ROOT / f"tasks/{example}.md").read_text().splitlines():
        m = re.match(r"^- \*\*(R\d+)\.\*\* (.*)", line)
        if m:
            cur = [m.group(1), m.group(2).strip()]
            reqs.append(cur)
        elif cur and line.startswith("  ") and line.strip():
            cur[1] += " " + line.strip()
        else:
            cur = None
    return [tuple(r) for r in reqs]


def rubric(example):
    """({req: (met, partial)}, ground-truth text) from rubrics/<example>.md."""
    text = (ROOT / f"rubrics/{example}.md").read_text()
    rows = {m.group(1): (m.group(2).strip(), m.group(3).strip())
            for m in re.finditer(r"^\| (R\d+) \| (.*?) \| (.*?) \|$", text, re.M)}
    gt = text.split("## Ground-truth checks", 1)[1].strip() if "## Ground-truth checks" in text else ""
    return rows, gt


def mode(example, req):
    cfg = SCFG["examples"][example]
    return "live" if req in cfg["live"] else "code" if req in cfg["code"] else "static"


def task_question(example):
    m = re.search(r"^question: (.*)$", (ROOT / f"tasks/{example}.md").read_text(), re.M)
    return m.group(1) if m else ""


def done_runs():
    """[(example, tool, run_id, run_dir)] of finished runs in the evaluation examples."""
    out = []
    for status in sorted((ROOT / "runs").glob("E*/*/*/status.json")):
        run_dir = status.parent
        example, tool, run_id = run_dir.parts[-3:]
        if example in RCFG["examples"] and json.loads(status.read_text()).get("status") == "done":
            out.append((example, tool, run_id, run_dir))
    return out


def read_key():
    if not KEY.exists():
        sys.exit("No blind key yet: run `python3 scripts/score.py blind` first.")
    with KEY.open() as f:
        return {r["code"]: r for r in csv.DictReader(f)}


def run_dir_of(run_id):
    example, tool = run_id.split("-")[0], run_id.split("-", 1)[1].rsplit("-", 1)[0]
    return ROOT / "runs" / example / tool / run_id


def valid(row):
    return (row.get("phase") in ("blind", "live") and row.get("item") and row.get("requirement")
            and (row.get("score") or "") in ("", "0", "1", "2"))


def read_scores(path, keep_invalid=False):
    """Rows of a scores file; malformed rows (e.g. from an interrupted write) are skipped."""
    if not path.exists():
        return []
    with path.open(newline="") as f:
        rows = [{k: (v if v is not None else "") for k, v in r.items() if k is not None} for r in csv.DictReader(f)]
    return rows if keep_invalid else [r for r in rows if valid(r)]


def write_scores(path, rows):
    rows = sorted((r for r in rows if valid(r)), key=lambda r: (r["phase"], r["item"], r["requirement"]))
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    with os.fdopen(fd, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SCORE_COLS, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)  # atomic: a reader sees the old file or the new one, never half of it


def upsert(path, row):
    with WRITE_LOCK:
        rows = [r for r in read_scores(path)
                if not (r["phase"] == row["phase"] and r["item"] == row["item"] and r["requirement"] == row["requirement"])]
        if row.get("score", "") != "" or row.get("note", ""):
            rows.append({c: row.get(c, "") for c in SCORE_COLS})
        write_scores(path, rows)


# ------------------------------------------------------------------------------------- commands


def cmd_blind(args):
    if KEY.exists() and not args.force:
        sys.exit(f"{KEY.relative_to(ROOT)} exists. It is drawn once; scores refer to its codes.")
    runs = done_runs()
    missing = [r for r in runs if not (r[3] / "render.png").exists()]
    rng = random.Random(SCFG["blind_seed"])
    rows = []
    for example in RCFG["examples"]:
        ex_runs = [r for r in runs if r[0] == example]
        rng.shuffle(ex_runs)
        for n, (ex, tool, run_id, _) in enumerate(ex_runs, 1):
            rows.append({"code": f"{ex}-{n:02d}", "run_id": run_id, "example": ex, "tool": tool})
    RESULTS.mkdir(exist_ok=True)
    with KEY.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["code", "run_id", "example", "tool"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} runs -> {KEY.relative_to(ROOT)} (do not open it before you finish the blind phase)")
    if missing:
        print(f"{len(missing)} runs have no render.png (shown as 'no image' and scored as such): "
              + ", ".join(r[2] for r in missing[:5]))


def items(phase, evaluator):
    """What the app shows for a phase, with the evaluator's saved scores."""
    saved = {(r["phase"], r["item"], r["requirement"]): r for r in read_scores(RESULTS / f"scores-{evaluator}.csv")}
    out = []
    if phase == "blind":
        for code, k in read_key().items():
            reqs = [(i, t) for i, t in requirements(k["example"]) if mode(k["example"], i) == "static"]
            out.append(dict(item=code, example=k["example"], title=code, reqs=reqs))
    else:
        for example, tool, run_id, run_dir in done_runs():
            reqs = [(i, t) for i, t in requirements(example) if mode(example, i) != "static"]
            if reqs:
                out.append(dict(item=run_id, example=example, title=f"{run_id}", tool=tool, reqs=reqs,
                                evidence=[n for n in ("interaction-before.png", "interaction-after.png")
                                          if (run_dir / n).exists()]))
    for it in out:
        rows, gt = rubric(it["example"])
        it["question"] = task_question(it["example"])
        it["groundTruth"] = gt
        it["reqs"] = [dict(id=i, text=t, mode=mode(it["example"], i), met=rows.get(i, ("", ""))[0],
                           partial=rows.get(i, ("", ""))[1],
                           score=saved.get((phase, it["item"], i), {}).get("score", ""))
                      for i, t in it["reqs"]]
        it["note"] = saved.get((phase, it["item"], "_note"), {}).get("note", "")
    return out


def live_page(run_id):
    run_dir = run_dir_of(run_id)
    tool = run_dir.parent.name
    base = f"/runfile/{urllib.parse.quote(run_id)}/"
    if tool == "d3":  # the agent's own page, as the protocol renders it
        return f'<!doctype html><html><head><meta http-equiv="refresh" content="0; url={base}index.html"></head></html>'
    if tool == "vega-lite":
        return f"""<!doctype html><html><head><meta charset="utf-8">
<script src="/lib/vega/build/vega.min.js"></script><script src="/lib/vega-lite/build/vega-lite.min.js"></script>
<script src="/lib/vega-embed/build/vega-embed.min.js"></script></head><body style="margin:0"><div id="vis"></div>
<script>fetch("{base}spec.vl.json").then(r=>r.json()).then(s=>vegaEmbed("#vis",s)).catch(e=>document.body.append("Render error: "+e));</script></body></html>"""
    if tool == "time-i-gram":
        return f"""<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0"><div id="vis"></div>
<script type="module">import {{embed}} from "/lib/time-i-gram/dist/index.js";
try {{ await embed(document.getElementById("vis"), await (await fetch("{base}spec.json")).json()); }}
catch (e) {{ document.body.append("Render error: " + e); }}</script></body></html>"""
    img = "plot.svg" if (run_dir / "plot.svg").exists() else "render.png"
    return f'<!doctype html><html><body style="margin:0;background:#fff"><p style="font:14px sans-serif">ggtime output is a static image (no interaction).</p><img src="{base}{img}" style="max-width:1400px"></body></html>'


APP = (Path(__file__).resolve().parent / "score_app.html")


class Handler(BaseHTTPRequestHandler):
    evaluator = "denisse"

    def log_message(self, *a):
        pass

    def send(self, body, ctype="text/html; charset=utf-8", code=200):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("content-type", ctype)
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def file(self, path):
        types = {".png": "image/png", ".svg": "image/svg+xml", ".json": "application/json", ".html": "text/html",
                 ".js": "text/javascript", ".css": "text/css", ".csv": "text/csv", ".R": "text/plain"}
        if not path.exists() or not path.is_file():
            return self.send("not found", "text/plain", 404)
        self.send(path.read_bytes(), types.get(path.suffix, "application/octet-stream") + (
            "; charset=utf-8" if path.suffix in (".js", ".html", ".css", ".json", ".R") else ""))

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        parts = [urllib.parse.unquote(p) for p in url.path.split("/") if p]
        q = urllib.parse.parse_qs(url.query)
        if not parts:
            return self.send(APP.read_text().replace("__EVALUATOR__", self.evaluator))
        if parts[0] == "api" and parts[1:] == ["items"]:
            return self.send(json.dumps(items(q.get("phase", ["blind"])[0], self.evaluator)), "application/json")
        if parts[0] == "img" and len(parts) == 2:  # blind screenshot by code only
            k = read_key().get(parts[1].removesuffix(".png"))
            return self.file(run_dir_of(k["run_id"]) / "render.png") if k else self.send("", "text/plain", 404)
        if parts[0] == "live" and len(parts) == 2:
            return self.send(live_page(parts[1]))
        if parts[0] == "code" and len(parts) == 2:
            run_dir = run_dir_of(parts[1])
            return self.file(run_dir / DELIVERABLE[run_dir.parent.name])
        if parts[0] == "runfile" and len(parts) >= 3:
            base = run_dir_of(parts[1]).resolve()
            path = (base / "/".join(parts[2:])).resolve()
            return self.file(path) if str(path).startswith(str(base)) else self.send("", "text/plain", 403)
        if parts[0] == "lib":
            path = (LIB / "/".join(parts[1:])).resolve()
            return self.file(path) if str(path).startswith(str(LIB.resolve())) else self.send("", "text/plain", 403)
        self.send("not found", "text/plain", 404)

    def do_POST(self):
        try:
            self.post()
        except Exception as e:  # never leave the browser without an answer
            print(f"Error while saving: {e!r}", file=sys.stderr)
            self.send(json.dumps({"error": str(e)}), "application/json", 500)

    def post(self):
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"{}")
        path = urllib.parse.urlparse(self.path).path
        now = dt.datetime.now().isoformat(timespec="seconds")
        if path == "/api/score":
            if body.get("phase") not in ("blind", "live") or str(body.get("score", "")) not in ("", "0", "1", "2"):
                return self.send('{"error":"bad request"}', "application/json", 400)
            upsert(RESULTS / f"scores-{self.evaluator}.csv",
                   dict(evaluator=self.evaluator, phase=body["phase"], item=body["item"], example=body["example"],
                        requirement=body["requirement"], score=str(body.get("score", "")),
                        note=body.get("note", ""), updated=now))
            return self.send('{"ok":true}', "application/json")
        if path == "/api/evidence":
            which = body.get("which")
            if which not in ("before", "after") or not body.get("dataurl", "").startswith("data:image/png;base64,"):
                return self.send('{"error":"send a PNG"}', "application/json", 400)
            out = run_dir_of(body["item"]) / f"interaction-{which}.png"
            out.write_bytes(base64.b64decode(body["dataurl"].split(",", 1)[1]))
            return self.send('{"ok":true}', "application/json")
        self.send("not found", "text/plain", 404)


def cmd_serve(args):
    read_key()
    if not (LIB / "vega").exists() or not (LIB / "time-i-gram").exists():
        sys.exit("The live phase needs the pinned libraries: run `cd gallery && npm install` once.")
    Handler.evaluator = args.evaluator
    ThreadingHTTPServer.request_queue_size = 64
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Scoring app for '{args.evaluator}': http://127.0.0.1:{args.port}   (Ctrl+C to stop; scores are saved at every click)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


def cmd_repair(args):
    path = RESULTS / f"scores-{args.evaluator}.csv"
    if not path.exists():
        sys.exit(f"{path.relative_to(ROOT)} does not exist.")
    raw = path.read_text(errors="replace")
    rows = read_scores(path, keep_invalid=True)
    good = [r for r in rows if valid(r)]
    bad = [r for r in rows if not valid(r)]
    backup = path.with_name(f"{path.stem}.backup-{dt.datetime.now():%Y%m%dT%H%M%S}.csv")
    backup.write_text(raw)
    write_scores(path, good)
    print(f"Backup of the original: {backup.relative_to(ROOT)}")
    print(f"Kept {len(good)} valid scores; removed {len(bad)} malformed rows:")
    for r in bad:
        print("  ", {k: v for k, v in r.items() if v})
    print("Run `python3 scripts/score.py progress` and re-score anything still missing in the app.")


def cmd_progress(args):
    key = read_key()
    rows = [r for r in read_scores(RESULTS / f"scores-{args.evaluator}.csv") if r["score"] != ""]
    blind_total = sum(len([i for i, _ in requirements(k["example"]) if mode(k["example"], i) == "static"]) for k in key.values())
    live_total = sum(len([i for i, _ in requirements(e) if mode(e, i) != "static"]) for e, *_ in done_runs())
    print(f"{args.evaluator}: blind {sum(r['phase'] == 'blind' for r in rows)}/{blind_total}, "
          f"live/code {sum(r['phase'] == 'live' for r in rows)}/{live_total}")
    judge = read_scores(RESULTS / "scores-judge.csv")
    print(f"judge: blind {sum(r['score'] != '' for r in judge)}/{blind_total}")


# --------------------------------------------------------------------------------------- summary


def weighted_kappa(pairs, k=3):
    """Quadratic-weighted Cohen's kappa for ordinal scores 0..k-1."""
    n = len(pairs)
    if n == 0:
        return float("nan")
    obs = [[0] * k for _ in range(k)]
    for a, b in pairs:
        obs[a][b] += 1
    ra = [sum(obs[i]) for i in range(k)]
    rb = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    w = [[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)]
    num = sum(w[i][j] * obs[i][j] for i in range(k) for j in range(k)) / n
    den = sum(w[i][j] * ra[i] * rb[j] for i in range(k) for j in range(k)) / n / n
    return 1 - num / den if den else float("nan")


def report_done(run_dir):
    f = run_dir / "report.txt"
    text = f.read_text() if f.exists() else ""
    return {m.group(1) for m in re.finditer(r"^\s*(R\d+):\s*done\b", text, re.M | re.I)}


def deliverable_size(path):
    text = path.read_text(errors="replace")
    if path.suffix == ".json":
        try:
            obj = json.loads(text)
            return len(json.dumps(obj, indent=1).splitlines()), len(json.dumps(obj, separators=(",", ":")))
        except ValueError:
            pass
    comment = r"(^|\s)#.*$" if path.suffix == ".R" else r"(^|\s)//.*$"
    text = re.sub(r"/\*.*?\*/|<!--.*?-->", "", text, flags=re.S) if path.suffix != ".R" else text
    lines = [re.sub(comment, "", l).rstrip() for l in text.splitlines()]
    lines = [l for l in lines if l.strip()]
    return len(lines), len(re.sub(r"\s+", " ", "\n".join(lines)))


def fmt(x, d=1):
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"


def cmd_summary(args):
    key = read_key()
    human_name = args.evaluator
    human = {(r["phase"], r["item"], r["requirement"]): r for r in read_scores(RESULTS / f"scores-{human_name}.csv")}
    judge = {(r["item"], r["requirement"]): r for r in read_scores(RESULTS / "scores-judge.csv")}
    # Agreement must use the human's scores from BEFORE seeing the judge: a git commit of the scores file.
    initial, initial_ref = None, args.initial
    if initial_ref:
        shown = subprocess.run(["git", "-C", str(ROOT), "show", f"{initial_ref}:results/scores-{human_name}.csv"],
                               capture_output=True, text=True)
        if shown.returncode != 0:
            sys.exit(f"Cannot read results/scores-{human_name}.csv at {initial_ref}: {shown.stderr.strip()}")
        rows0 = [{k: (v or "") for k, v in r.items() if k} for r in csv.DictReader(io.StringIO(shown.stdout))]
        initial = {(r["phase"], r["item"], r["requirement"]): r for r in rows0 if valid(r)}
    agree_with = initial if initial is not None else human
    code_of = {k["run_id"]: c for c, k in key.items()}

    # agreement on the blind (static) requirements
    pairs, disagreements, per_example = [], [], {}
    for code, k in key.items():
        for req, _ in requirements(k["example"]):
            if mode(k["example"], req) != "static":
                continue
            h, j = agree_with.get(("blind", code, req), {}).get("score", ""), judge.get((code, req), {}).get("score", "")
            if h != "" and j != "":
                pairs.append((int(h), int(j)))
                per_example.setdefault(k["example"], []).append((int(h), int(j)))
                if h != j:
                    disagreements.append({"code": code, "example": k["example"], "requirement": req, "human": h,
                                          "judge": j, "judge_reason": judge[(code, req)].get("note", "")})
    with (RESULTS / "disagreements.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["code", "example", "requirement", "human", "judge", "judge_reason"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(disagreements)

    # final scores per run (the human's, after reviewing disagreements)
    template_cols = (RESULTS / "scores.csv").read_text().splitlines()[0].split(",")
    rows, missing = [], []
    for example, tool, run_id, run_dir in done_runs():
        meta = json.loads((run_dir / "meta.json").read_text()) if (run_dir / "meta.json").exists() else {}
        reqs = [i for i, _ in requirements(example)]
        scores = {}
        for req in reqs:
            phase, item = ("blind", code_of.get(run_id, "")) if mode(example, req) == "static" else ("live", run_id)
            s = human.get((phase, item, req), {}).get("score", "")
            scores[req] = s
            if s == "":
                missing.append(f"{run_id} {req}")
        done = report_done(run_dir)
        lines, chars = deliverable_size(run_dir / DELIVERABLE[tool]) if (run_dir / DELIVERABLE[tool]).exists() else ("", "")
        row = {c: "" for c in template_cols}
        row.update(run_id=run_id, example=example, tool=tool, repeat=run_id.rsplit("-r", 1)[-1],
                   model=meta.get("model", ""), agent_harness=f"Claude Code {meta.get('claude_code_version', '')} headless",
                   date=meta.get("started", "")[:10], prompt_sha256=meta.get("prompt_sha256", ""),
                   renders_without_edits="yes" if meta.get("render_ok") else "no", manual_fixes="0",
                   score_sum=sum(int(v) for v in scores.values() if v != ""), score_max=2 * len(reqs),
                   report_mismatches=sum(1 for r in done if scores.get(r, "") not in ("", "2")),
                   deliverable_lines=lines, deliverable_chars=chars, agent_turns=meta.get("turns", ""),
                   tool_calls=meta.get("tool_calls", ""), self_renders=meta.get("render_calls", ""),
                   input_tokens=meta.get("input_tokens", ""), output_tokens=meta.get("output_tokens", ""),
                   wall_seconds=meta.get("wall_seconds", ""), evaluator=human_name,
                   notes=(human.get(("blind", code_of.get(run_id, ""), "_note"), {}).get("note", "") + " "
                          + human.get(("live", run_id, "_note"), {}).get("note", "")).strip())
        row.update({k: v for k, v in scores.items() if k in template_cols})
        rows.append(row)
    with (RESULTS / "scores.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=template_cols, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # results table
    tools = RCFG["tools"]
    out = ["# Results", "", f"Generated by `scripts/score.py summary` on {dt.date.today()} from {len(rows)} runs. "
           f"Scores: {human_name} (final). Requirements scored 0/1/2 (see rubrics/).", ""]
    if missing:
        out += [f"**Incomplete:** {len(missing)} requirement scores missing (e.g. {', '.join(missing[:3])}).", ""]
    out += ["## Score per example and tool", "",
            "Mean of score_sum / score_max over the repeats (± standard deviation; n runs).", "",
            "| Example | " + " | ".join(tools) + " |", "|---|" + "---|" * len(tools)]
    for example in RCFG["examples"]:
        cells = []
        for tool in tools:
            vals = [r["score_sum"] / r["score_max"] for r in rows if r["example"] == example and r["tool"] == tool]
            cells.append(f"{statistics.mean(vals):.0%} ± {statistics.pstdev(vals):.0%} (n={len(vals)})" if vals else "–")
        out.append(f"| {example} | " + " | ".join(cells) + " |")
    out += ["", "## Requirements met (score 2), per tool", "", "| Example | Req | " + " | ".join(tools) + " |",
            "|---|---|" + "---|" * len(tools)]
    for example in RCFG["examples"]:
        for req, _ in requirements(example):
            cells = []
            for tool in tools:
                vals = [r[req] for r in rows if r["example"] == example and r["tool"] == tool and r.get(req, "") != ""]
                cells.append(f"{sum(v == '2' for v in vals)}/{len(vals)}" if vals else "–")
            out.append(f"| {example} | {req} ({mode(example, req)}) | " + " | ".join(cells) + " |")
    out += ["", "## Effort per run (median over all examples, except where a total is stated)", "",
            "| Measure | " + " | ".join(tools) + " |", "|---|" + "---|" * len(tools)]
    for label, col, scale in [("Wall time (min)", "wall_seconds", 60), ("Turns", "agent_turns", 1),
                              ("Tool calls", "tool_calls", 1), ("Self-checks with render", "self_renders", 1),
                              ("Output tokens", "output_tokens", 1),
                              ("Deliverable size (characters, no comments or extra whitespace)", "deliverable_chars", 1),
                              ("Renders without edits (count)", "renders_without_edits", None),
                              ("REPORT claims 'done' that scored below 2 (total)", "report_mismatches", "sum")]:
        cells = []
        for tool in tools:
            vals = [r[col] for r in rows if r["tool"] == tool and r[col] != ""]
            if scale is None:
                cells.append(f"{sum(v == 'yes' for v in vals)}/{len(vals)}")
            elif scale == "sum":
                cells.append(f"{sum(int(v) for v in vals)} (in {sum(int(v) > 0 for v in vals)} of {len(vals)} runs)")
            elif vals:
                cells.append(fmt(statistics.median(float(v) / scale for v in vals), 1 if scale == 60 else 0))
            else:
                cells.append("–")
        out.append(f"| {label} | " + " | ".join(cells) + " |")
    exact = sum(a == b for a, b in pairs) / len(pairs) if pairs else float("nan")
    if initial is not None:
        changed = [k for k, r in human.items() if k[2] != "_note" and initial.get(k, {}).get("score", "") != r["score"]]
        changed_blind = [k for k in changed if k[0] == "blind"]
        basis = (f"Computed with the human's **initial** scores (git `{initial_ref}`, before seeing the judge). After "
                 f"reviewing the disagreements, the human changed {len(changed_blind)} blind scores "
                 f"({len(changed) - len(changed_blind)} live/code scores changed as well); the final scores are used everywhere else.")
    else:
        basis = ("**Computed with the human's final scores.** If any score was changed after seeing the judge, this "
                 "overstates agreement: run `summary --initial <commit>` with the commit of the scores before the judge ran.")
    out += ["", "## Agreement with the automatic judge (blind, static requirements)", "", basis, "",
            f"{len(pairs)} paired scores; exact agreement {fmt(exact * 100, 0)} %; quadratic-weighted Cohen's kappa "
            f"{fmt(weighted_kappa(pairs), 2)} (– when both raters used a single score). Disagreements: "
            f"`results/disagreements.csv` ({len(disagreements)}).", "",
            "| Example | pairs | exact agreement | weighted kappa |", "|---|---|---|---|"]
    for example in RCFG["examples"]:
        p = per_example.get(example, [])
        ex = sum(a == b for a, b in p) / len(p) * 100 if p else float("nan")
        out.append(f"| {example} | {len(p)} | {fmt(ex, 0)} % | {fmt(weighted_kappa(p), 2)} |")
    out += ["", f"The judge is {SCFG['judge_model']}, the same model family that produced the outputs; it saw the same "
            "screenshot, requirements and rubric as the human, without the tool name. Its scores are not used in the "
            "final scores."]
    (RESULTS / "summary.md").write_text("\n".join(out) + "\n")
    print(f"results/scores.csv ({len(rows)} runs), results/summary.md, results/disagreements.csv ({len(disagreements)})")
    if missing:
        print(f"Missing scores: {len(missing)} (e.g. {', '.join(missing[:3])}). Finish them in the app and run summary again.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("blind")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_blind)
    s = sub.add_parser("serve")
    s.add_argument("--evaluator", default=SCFG["human_evaluator"])
    s.add_argument("--port", type=int, default=8800)
    s.set_defaults(func=cmd_serve)
    s = sub.add_parser("repair", help="remove malformed rows from a scores file (keeps a backup)")
    s.add_argument("--evaluator", default=SCFG["human_evaluator"])
    s.set_defaults(func=cmd_repair)
    s = sub.add_parser("progress")
    s.add_argument("--evaluator", default=SCFG["human_evaluator"])
    s.set_defaults(func=cmd_progress)
    s = sub.add_parser("summary")
    s.add_argument("--evaluator", default=SCFG["human_evaluator"])
    s.add_argument("--initial", metavar="GIT_REF",
                   help="commit with the human's scores before seeing the judge (agreement is computed with these)")
    s.set_defaults(func=cmd_summary)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
