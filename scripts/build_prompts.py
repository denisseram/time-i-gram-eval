#!/usr/bin/env python3
"""Build prompts/<example>/<tool>.md from tasks/*.md, tasks/_common.md, tools/*.md and datasets/manifest.json.

Every prompt for one example is the same text except the tool name, the deliverable kind and the Tool
section. Run with --check to verify that (and that the committed prompts are up to date) without writing.

Usage:  python3 scripts/build_prompts.py [--check]
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ["d3", "vega-lite", "ggtime", "time-i-gram"]


def split_front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    meta = dict(line.split(": ", 1) for line in m.group(1).splitlines() if ": " in line)
    return meta, text[m.end():]


def render(task_body, common, tool_meta, tool_body, url):
    text = task_body.replace("{{COMMON}}", common.strip())
    text = text.replace("{{TOOL_SECTION}}", tool_body.strip())
    text = text.replace("{{DATA_URL}}", url)
    text = text.replace("{{TOOL_NAME}}", tool_meta["name"])
    text = text.replace("{{DELIVERABLE_KIND}}", tool_meta["deliverable_kind"])
    left = re.findall(r"\{\{[A-Z_]+\}\}", text)
    if left:
        raise SystemExit(f"unfilled placeholders: {left}")
    return text.strip() + "\n"


def neutralise(text, tool_meta, tool_body):
    """Remove the parts that are allowed to differ, so the rest can be compared across tools."""
    text = text.replace(tool_body.strip(), "<TOOL SECTION>")
    text = text.replace(tool_meta["deliverable_kind"], "<DELIVERABLE KIND>")
    return text.replace(tool_meta["name"], "<TOOL>")


def main():
    check = "--check" in sys.argv
    manifest = json.loads((ROOT / "datasets/manifest.json").read_text())
    common = (ROOT / "tasks/_common.md").read_text()
    tools = {t: split_front_matter((ROOT / f"tools/{t}.md").read_text()) for t in TOOLS}
    index = []
    problems = []

    for task_file in sorted((ROOT / "tasks").glob("E*.md")):
        meta, body = split_front_matter(task_file.read_text())
        ds = manifest[meta["dataset"]]
        draft = ds["status"] != "verified"
        neutral = set()
        for t in TOOLS:
            tmeta, tbody = tools[t]
            text = render(body, common, tmeta, tbody, ds["url"])
            if draft:
                text = ("> **DRAFT, do not run:** the data URL for this example is not pinned and verified yet "
                        "(see datasets/manifest.json).\n\n" + text)
            neutral.add(neutralise(text, tmeta, tbody))
            out = ROOT / f"prompts/{meta['id']}/{t}.md"
            if check:
                if not out.exists() or out.read_text() != text:
                    problems.append(f"out of date: {out.relative_to(ROOT)}")
            else:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(text)
            index.append({
                "example": meta["id"], "tool": t, "prompt": str(out.relative_to(ROOT)),
                "deliverable": tmeta["deliverable"], "dataset": meta["dataset"],
                "status": "draft" if draft else "ready",
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
            })
        if len(neutral) != 1:
            problems.append(f"{meta['id']}: prompts differ outside the tool-specific parts")

    if not check:
        (ROOT / "prompts/index.json").write_text(json.dumps(index, indent=2) + "\n")
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    ready = sum(1 for i in index if i["status"] == "ready")
    print(f"{len(index)} prompts ({ready} ready, {len(index) - ready} draft); identical outside tool parts: OK")


if __name__ == "__main__":
    main()
