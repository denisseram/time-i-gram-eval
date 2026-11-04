#!/usr/bin/env python3
"""Generate the Observable Framework gallery (gallery/src/) from runs/ and results/scores.csv.

One page per example. For every run it shows the live output, the agent's code, the agent's REPORT,
the scores and the evaluator's captures:

  D3           index.html in an iframe (as run by the protocol)
  Vega-Lite    spec.vl.json with vega-embed 7.3.0 / Vega 6.4.0 / Vega-Lite 6.5.0 (local copies)
  ggtime       plot.svg (or plot.png) written by plot.R
  time-i-gram  spec.json with time-i-gram 0.1.0 from npm (local copy)

Usage:
  python3 scripts/build_gallery.py           # from runs/ and results/scores.csv
  python3 scripts/build_gallery.py --demo    # from gallery/fixtures/ (to try the gallery without real runs)
then:  cd gallery && npm install && npm run dev      (or: npm run build, npm run deploy)
"""
import csv
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GALLERY = ROOT / "gallery"
SRC = GALLERY / "src"
DEMO = "--demo" in sys.argv
RUNS = GALLERY / "fixtures/runs" if DEMO else ROOT / "runs"
SCORES = GALLERY / "fixtures/scores.csv" if DEMO else ROOT / "results/scores.csv"

TOOLS = [  # order on the page: name, folder, deliverable, code language
    ("time-i-gram", "time-i-gram", "spec.json", "json"),
    ("D3", "d3", "index.html", "html"),
    ("Vega-Lite", "vega-lite", "spec.vl.json", "json"),
    ("ggtime", "ggtime", "plot.R", "r"),
]
COPY = ["index.html", "spec.vl.json", "spec.json", "plot.R", "plot.svg", "plot.png", "render.png",
        "interaction.gif", "report.txt", "run.md", "console.txt", "meta.json"]
# libraries copied from gallery/node_modules into gallery/src/lib/<name>-<version>.js (versions pinned in package.json)
LIBS = [("vega", "6.4.0", "build/vega.min.js"), ("vega-lite", "6.5.0", "build/vega-lite.min.js"),
        ("vega-embed", "7.3.0", "build/vega-embed.min.js"), ("time-i-gram", "0.1.0", "dist/index.js")]
REQS = [f"R{i}" for i in range(1, 8)]


def front_matter(path):
    m = re.match(r"^---\n(.*?)\n---\n", path.read_text(), re.S)
    return dict(l.split(": ", 1) for l in m.group(1).splitlines() if ": " in l) if m else {}


def safe_md(text):
    """Markdown outside code fences: keep Framework from reading ${...} as an expression."""
    return text.replace("${", "$​{")


def fence(text, lang, run=False):
    """A fenced block. Framework executes js/html/svg/... fences, so shown code gets run=false."""
    ticks = "~~~~"
    while ticks in text:
        ticks += "~"
    info = lang if run else f"{lang} run=false"
    return f"{ticks}{info}\n{text.rstrip()}\n{ticks}"


def load_scores():
    if not SCORES.exists():
        return {}
    with SCORES.open() as f:
        return {row["run_id"]: row for row in csv.DictReader(f)}


def vendor_libs():
    lib = SRC / "lib"
    shutil.rmtree(lib, ignore_errors=True)
    lib.mkdir(parents=True)
    for name, version, path in LIBS:
        src = GALLERY / "node_modules" / name / path
        if not src.exists():
            sys.exit(f"missing {src}: run `npm install` in gallery/ first")
        installed = json.loads((GALLERY / "node_modules" / name / "package.json").read_text())["version"]
        if installed != version:
            sys.exit(f"{name} {installed} installed, {version} expected (see gallery/package.json)")
        shutil.copyfile(src, lib / f"{name}-{version}.js")


def copy_runs():
    dest = SRC / "runs"
    shutil.rmtree(dest, ignore_errors=True)
    runs = {}
    for run_dir in sorted(RUNS.glob("*/*/*/")):
        example, tool, run_id = run_dir.parts[-3:]
        if example.startswith("_"):  # runs/_interrupted: not counted, not shown
            continue
        out = dest / example / tool / run_id
        out.mkdir(parents=True)
        files = [n for n in COPY if (run_dir / n).exists()]
        for n in files:
            shutil.copyfile(run_dir / n, out / n)
        runs.setdefault(example, {}).setdefault(tool, []).append((run_id, files, run_dir))
    return runs


def render_cell(tool, path, files):
    """A JS cell that shows the live output, or an error message in its place."""
    if tool == "d3":
        return fence(f"""{{
  const href = FileAttachment("{path}/index.html").href;
  display(frame(href));
}}""", "js", run=True)
    if tool == "vega-lite":
        return fence(f"""{{
  const spec = await FileAttachment("{path}/spec.vl.json").json();
  display(await live(async (el) => {{ await vegaReady; await window.vegaEmbed(el, spec); }}));
}}""", "js", run=True)
    if tool == "time-i-gram":
        return fence(f"""{{
  const spec = await FileAttachment("{path}/spec.json").json();
  display(await live(async (el) => {{ await timeIGramEmbed(el, spec); }}));
}}""", "js", run=True)
    if tool == "ggtime":
        img = "plot.svg" if "plot.svg" in files else "plot.png" if "plot.png" in files else None
        if img is None:
            return "_No `plot.svg` or `plot.png`: the script did not produce a figure._"
        return fence(f"""display(picture(FileAttachment("{path}/{img}").href, "ggtime output"));""", "js", run=True)
    return ""


HELPERS = """```js
// helpers shared by every run on this page
import {embed as timeIGramEmbed} from "./lib/time-i-gram-0.1.0.js";
function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src; s.onload = resolve; s.onerror = () => reject(new Error(`could not load ${src}`));
    document.head.appendChild(s);
  });
}
const vegaReady = (async () => {
  if (window.vegaEmbed) return;
  await loadScript(FileAttachment("lib/vega-6.4.0.js").href);
  await loadScript(FileAttachment("lib/vega-lite-6.5.0.js").href);
  await loadScript(FileAttachment("lib/vega-embed-7.3.0.js").href);
})();
function box() {
  const el = document.createElement("div");
  el.className = "output";
  return el;
}
async function live(render) {
  const outer = box(), el = document.createElement("div");
  outer.appendChild(el);
  try { await render(el); } catch (error) {
    const pre = document.createElement("pre");
    pre.className = "render-error";
    pre.textContent = `Render error: ${error?.message ?? error}`;
    outer.replaceChildren(pre);
  }
  return outer;
}
function frame(href) {
  const outer = box(), f = document.createElement("iframe");
  Object.assign(f, {src: href, width: 1400, height: 900});
  const a = document.createElement("a");
  Object.assign(a, {href, target: "_blank", textContent: "open full size ↗"});
  outer.append(f, a);
  return outer;
}
function picture(href, alt) {
  const outer = box(), img = document.createElement("img");
  Object.assign(img, {src: href, alt});
  outer.appendChild(img);
  return outer;
}
```

<style>
.output { overflow: auto; max-width: 100%; border: 1px solid var(--theme-foreground-faint); padding: 8px; background: white; }
.output iframe { border: 0; display: block; }
.output img { max-width: 100%; }
.render-error { color: #b00020; white-space: pre-wrap; }
.scores td, .scores th { text-align: center; }
</style>
"""


def score_table(row):
    if not row:
        return "_Not scored yet (no row in `results/scores.csv`)._"
    present = [r for r in REQS if row.get(r, "") != ""]
    head = "| " + " | ".join(present + ["total", "renders as-is", "report mismatches"]) + " |"
    sep = "|" + "---|" * (len(present) + 3)
    vals = [row[r] for r in present] + [f"{row.get('score_sum', '')}/{row.get('score_max', '')}",
                                       row.get("renders_without_edits", ""), row.get("report_mismatches", "")]
    return f'<div class="scores">\n\n{head}\n{sep}\n| ' + " | ".join(vals) + " |\n\n</div>"


def example_page(example, task_meta, tools_runs, scores):
    out = [f"---\ntitle: {json.dumps(example + ' ' + task_meta.get('title', ''))}\ntoc: true\n---\n",
           f"# {example}: {task_meta.get('question', '')}\n",
           f"Prompts: `prompts/{example}/<tool>.md` · rubric: `rubrics/{example}.md`" +
           (" · **DEMO fixtures, not agent output**" if DEMO else "") + "\n", HELPERS]
    for label, tool, deliverable, lang in TOOLS:
        out.append(f"## {label}\n")
        runs = tools_runs.get(tool, [])
        if not runs:
            out.append("_No runs yet._\n")
            continue
        for run_id, files, run_dir in runs:
            path = f"runs/{example}/{tool}/{run_id}"
            out.append(f"### {run_id}\n")
            out.append(score_table(scores.get(run_id)) + "\n")
            if "meta.json" in files:
                m = json.loads((run_dir / "meta.json").read_text())
                out.append(f"<small>Agent: {m.get('reason', '')}; {m.get('wall_seconds', 0) // 60} min, "
                           f"{m.get('turns')} turns, {m.get('tool_calls')} tool calls, "
                           f"{m.get('render_calls')} self-checks with <code>render</code>; official render "
                           f"{'OK' if m.get('render_ok') else 'failed'}.</small>\n")
            if deliverable not in files:
                out.append(f"_No `{deliverable}` in this run._\n")
            else:
                out.append(render_cell(tool, path, files) + "\n")
                code = (run_dir / deliverable).read_text()
                n = len([l for l in code.splitlines() if l.strip()])
                out.append(f"<details><summary>Code: <code>{deliverable}</code> ({n} lines)</summary>\n\n"
                           f"{fence(code, lang)}\n\n</details>\n")
            if "console.txt" in files:
                out.append("<details><summary>Official render log (console.txt)</summary>\n\n"
                           f"{fence((run_dir / 'console.txt').read_text(), 'text')}\n\n</details>\n")
            if "report.txt" in files:
                out.append("<details><summary>Agent's REPORT</summary>\n\n"
                           f"{fence((run_dir / 'report.txt').read_text(), 'text')}\n\n</details>\n")
            captures = [n for n in ("render.png", "interaction.gif") if n in files]
            if captures:
                imgs = "\n".join(f'${{picture(FileAttachment("{path}/{n}").href, "{n}")}}' for n in captures)
                out.append(f"<details><summary>Evaluator captures</summary>\n\n{imgs}\n\n</details>\n")
            if "run.md" in files:
                out.append("<details><summary>Run notes (run.md)</summary>\n\n"
                           f"{safe_md((run_dir / 'run.md').read_text())}\n\n</details>\n")
    return "\n".join(out)


def index_page(runs, scores, metas):
    lines = ["---\ntitle: Overview\ntoc: false\n---\n", "# time-i-gram evaluation: results\n"]
    if DEMO:
        lines.append("> **DEMO:** pages built from `gallery/fixtures/`, not from agent runs.\n")
    lines.append("Mean score (sum of requirement scores / maximum) per example and tool, over all scored runs. "
                 "Each example page shows every run live, with its code, report and scores.\n")
    head = "| Example | Question | " + " | ".join(t[0] for t in TOOLS) + " |"
    lines += [head, "|---|---|" + "---|" * len(TOOLS)]
    for example in sorted(metas):
        cells = []
        for _, tool, _, _ in TOOLS:
            rows = [scores[r] for r, _, _ in runs.get(example, {}).get(tool, []) if r in scores]
            rows = [r for r in rows if r.get("score_sum") and r.get("score_max")]
            n = len(runs.get(example, {}).get(tool, []))
            if rows:
                mean = sum(float(r["score_sum"]) / float(r["score_max"]) for r in rows) / len(rows)
                cells.append(f"{mean:.0%} ({len(rows)}/{n} scored)")
            else:
                cells.append(f"{n} runs, not scored" if n else "–")
        lines.append(f"| [{example}](./{example}) | {safe_md(metas[example].get('question', ''))} | " +
                     " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main():
    vendor_libs()
    for page in SRC.glob("E*.md"):
        page.unlink()
    runs = copy_runs()
    scores = load_scores()
    metas = {front_matter(p)["id"]: front_matter(p) for p in sorted((ROOT / "tasks").glob("E*.md"))}
    for example, meta in metas.items():
        (SRC / f"{example}.md").write_text(example_page(example, meta, runs.get(example, {}), scores))
    (SRC / "index.md").write_text(index_page(runs, scores, metas))
    n = sum(len(v) for t in runs.values() for v in t.values())
    print(f"gallery/src: {len(metas)} example pages, {n} runs" + (" (DEMO)" if DEMO else ""))


if __name__ == "__main__":
    main()
