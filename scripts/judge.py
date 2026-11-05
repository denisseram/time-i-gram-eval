#!/usr/bin/env python3
"""Automatic judge: Claude scores the blind screenshots with the same requirements and rubric as the human.

  python3 scripts/judge.py              score every blind screenshot not scored yet (resumable)
  python3 scripts/judge.py --only E3-04 one screenshot (to try it)

For each anonymized screenshot (results/blind_key.csv) it starts a new container from the evaluation image
with only the screenshot and the scoring instructions, runs Claude Code with the judge model, and saves
the scores in results/scores-judge.csv (same long format as the human's) and the raw answers in
results/judge/. Only the static requirements are judged (the live and code ones need a person). It stops
when the plan's usage limit is reached; run it again later to continue.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import runner  # noqa: E402  (credential, image, limit patterns)
import score   # noqa: E402  (requirements, rubric, key)

ROOT = score.ROOT
OUT = ROOT / "results/scores-judge.csv"
RAW = ROOT / "results/judge"
MODEL = score.SCFG["judge_model"]
FAKE = os.environ.get("EVAL_FAKE_JUDGE")  # testing only: random scores, no container

INSTRUCTIONS = """You are an evaluator in a study of visualization tools. The file `screenshot.png` in this folder is a
screenshot (1400 x 900 pixels) of a figure that someone made to answer a question with a public dataset.
Open it with the Read tool and look at it carefully. Do not use any other tool, and do not look for anything
else: score only what you can see in the screenshot.

Question the figure should answer: {question}

Score each requirement below with 2 (met), 1 (partial) or 0 (not met), using its rubric. If the figure shows
something that contradicts a ground-truth check, give that requirement at most 1. If there is no figure at
all, every requirement scores 0.

{requirements}

Ground-truth checks (computed from the data):

{ground_truth}

Answer with ONLY a JSON object, no other text, in this form:
{{{example_json}}}
"""


def build_prompt(example, reqs, rubric_rows, gt):
    blocks = []
    for req, text in reqs:
        met, partial = rubric_rows.get(req, ("", ""))
        blocks.append(f"{req}. {text}\n   2 when: {met}\n   1 if: {partial}")
    example_json = ", ".join(f'"{r}": {{"score": 2, "reason": "one short sentence"}}' for r, _ in reqs)
    return INSTRUCTIONS.format(question=score.task_question(example), requirements="\n\n".join(blocks),
                               ground_truth=gt, example_json=example_json)


def parse_answer(text, reqs):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except ValueError:
        return None
    out = {}
    for req, _ in reqs:
        v = obj.get(req)
        s = v.get("score") if isinstance(v, dict) else v
        if str(s) not in ("0", "1", "2"):
            return None
        out[req] = (str(s), (v.get("reason", "") if isinstance(v, dict) else "")[:300])
    return out


def judge_one(code, k, var, secret):
    example = k["example"]
    reqs = [(i, t) for i, t in score.requirements(example) if score.mode(example, i) == "static"]
    rubric_rows, gt = score.rubric(example)
    prompt = build_prompt(example, reqs, rubric_rows, gt)
    shot = score.run_dir_of(k["run_id"]) / "render.png"
    if FAKE:
        import random
        rng = random.Random(code)
        text = json.dumps({r: {"score": rng.choice([0, 1, 2, 2, 2]), "reason": "fake"} for r, _ in reqs})
        result = {"result": text, "is_error": False, "subtype": "success"}
    elif not shot.exists():
        result = {"result": json.dumps({r: {"score": 0, "reason": "no screenshot"} for r, _ in reqs}),
                  "subtype": "success", "note": "no screenshot: scored 0 without calling the model"}
    else:
        work = Path(tempfile.mkdtemp(prefix=f"judge-{code}-"))
        os.chmod(work, 0o777)
        shutil.copyfile(shot, work / "screenshot.png")
        (work / "prompt.md").write_text(prompt)
        cmd = ["docker", "run", "--rm", "-v", f"{work}:/work", "-w", "/work", "-e", var, runner.CONFIG["image"],
               "bash", "-c", f'timeout 600 claude -p "$(cat prompt.md)" --model {MODEL} --max-turns 4 '
               f'--output-format json --dangerously-skip-permissions '
               f'--disallowedTools Bash WebFetch WebSearch Edit Write NotebookEdit Task']
        r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, **{var: secret}), timeout=900)
        shutil.rmtree(work, ignore_errors=True)
        try:
            result = json.loads(r.stdout)
        except ValueError:
            result = {"result": r.stdout[-2000:], "is_error": True, "stderr": r.stderr[-2000:]}
        texts = [str(result.get("result", "")), r.stderr]
        if any(runner.STRONG_LIMIT.search(t) for t in texts) or (
                result.get("is_error") and any(runner.WEAK_LIMIT.search(t) for t in texts)):
            return "limit", None
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{code}.json").write_text(json.dumps({"code": code, "model": MODEL, "prompt": prompt, "answer": result},
                                                 indent=2))
    scores = parse_answer(result.get("result", ""), reqs)
    if scores is None:
        return "error", None
    return "done", scores


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--only", nargs="*", help="blind codes to judge (default: all not judged yet)")
    args = p.parse_args()
    key = score.read_key()
    var, secret = ("EVAL_FAKE", "1") if FAKE else runner.credential()
    if not FAKE:
        runner.image_versions()
    judged = {r["item"] for r in score.read_scores(OUT) if r["score"] != ""}
    todo = [c for c in key if (args.only and c in args.only) or (not args.only and c not in judged)]
    print(f"Judge {MODEL}: {len(todo)} screenshots to score ({len(judged)} already done).")
    for n, code in enumerate(todo, 1):
        status, scores = judge_one(code, key[code], var, secret)
        if status == "limit":
            print("Usage limit reached. Run the same command again after it resets; it continues where it stopped.")
            sys.exit(2)
        if status == "error":
            print(f"  {code}: could not read a valid answer (see results/judge/{code}.json); skipped, try again later.")
            continue
        now = dt.datetime.now().isoformat(timespec="seconds")
        for req, (s, reason) in scores.items():
            score.upsert(OUT, dict(evaluator=f"judge-{MODEL}", phase="blind", item=code, example=key[code]["example"],
                                   requirement=req, score=s, note=reason, updated=now))
        print(f"  [{n}/{len(todo)}] {code}: " + " ".join(f"{r}={s}" for r, (s, _) in scores.items()))
    print("Done. Next: python3 scripts/score.py summary")


if __name__ == "__main__":
    main()
