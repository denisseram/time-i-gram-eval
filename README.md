# time-i-gram evaluation

Materials for comparing **time-i-gram** with **D3**, **Vega-Lite** and **ggtime** (R): LLM agents write one
visualization per task with each tool, from identical prompts and the same public data.

Kept separate from the time-i-gram repository so that the agents, which read that repository as
documentation, never see the evaluation datasets, prompts or rubrics.

## Layout

| Path | What | Who sees it |
|---|---|---|
| `prompts/<E>/<tool>.md` | The 20 generated prompts (5 examples × 4 tools). **Send these as-is.** | agents |
| `prompts/index.json` | Prompt list with status (`ready`/`draft`), deliverable name and sha256 | evaluators |
| `tasks/E1.md … E5.md` | Shared task text per example (source of the prompts); `tasks/excluded/` holds E6 | authors |
| `tasks/_common.md` | Rules and REPORT format shared by every prompt | authors |
| `tools/<tool>.md` | The only part that differs between the four prompts of an example | authors |
| `datasets/manifest.json` | Pinned URL, size, sha256, license and citation of each dataset | evaluators |
| `datasets/eval-datasets.md` | How the datasets were chosen and checked; rejected candidates | evaluators |
| `rubrics/` | Scoring per requirement + ground-truth values from the data | evaluators only |
| `EVALUATION.md` | How the runs are scored: blind app, live phase, automatic judge, summary | evaluators |
| `PROTOCOL.md` | How to run and score, settings to keep fixed | evaluators |
| `runs/<E>/<tool>/<run_id>/` | One folder per run: prompt copy, transcript, deliverable, screenshots, `run.md` | evaluators |
| `templates/run.md` | Template for `run.md` | evaluators |
| `gallery/` | Observable Framework site: every run's output rendered live, with its code, REPORT and scores | evaluators |
| `env/` | Docker image of the run environment and the `render` command; setup in `env/README.md` | evaluators |
| `scripts/` | `runner.py` (runs the agents in batches), `score.py` (scoring app and summary), `judge.py` (automatic judge), `build_prompts.py [--check]`, `verify_data.py`, `pin_data_repo.py`, `measure.py`, `build_gallery.py`, `new_run.py` (manual runs); `tests/` | evaluators |
| `results/` | `schedule.csv` (order of runs), `metrics.csv` (from the runner), `scores.csv` (from the evaluators) | evaluators |

## Examples

| Ex | Question | Dataset | Prompts |
|---|---|---|---|
| E1 | How did each category change month by month? | Ocean temperature at 7 depths, Nova Scotia (daily, 2018–2025) | ready |
| E2 | Do the years follow the same cycle? (calendar, one row per year) | RKI ARE consultation incidence, Germany (weekly, 2012–2026) | ready |
| E3 | Does the peak happen at the same time each year? (circle + linked linear view) | same as E2 | ready |
| E4 | Do trajectories look alike once aligned to their own event? | Ubuntu release history (46 releases) | ready |
| E5 | Overview of several years, detail down to minutes | GeoSphere Austria 10-min, Wien Hohe Warte, 2020–2024 | ready |
| E6 | (excluded) Spiral, one turn per year | same as E2 | not run |

## Running the evaluation

Setup (Docker image, login token, smoke test) is in [`env/README.md`](env/README.md). Then, from the
repository root:

```bash
python3 scripts/runner.py check               # what is ready and what is missing
python3 scripts/runner.py pilot               # E0, one run per tool: tests the whole pipeline
python3 scripts/runner.py pilot --clean       # delete the pilot runs after looking at them
python3 scripts/build_prompts.py --check && python3 scripts/verify_data.py
git tag v1-frozen && git push origin v1-frozen    # freeze (batch refuses to run without it)
python3 scripts/runner.py init                # draw the order of the 60 runs once
caffeinate -i python3 scripts/runner.py batch --blocks 2    
python3 scripts/runner.py status              # progress, time, tokens
```

A **block** is one example with its four tools in random order. `batch` runs whole blocks, skips runs that
are done, and stops when the usage limit is reached: the cut-off run is moved to `runs/_interrupted/`
(kept for the record, not counted) and is run again from scratch next time. `caffeinate -i` (macOS) keeps
the computer awake while a batch runs. Commit `runs/` and `results/` after each batch.

Each finished run folder holds the exact prompt, the full transcript, the agent's whole working folder,
the deliverable, the official render (`render.png`, `console.txt`), the agent's REPORT and `meta.json`
(versions, times, turns, tool calls, `render` self-checks, tokens). `results/metrics.csv` collects
`meta.json` of all runs. Scoring: see [`EVALUATION.md`](EVALUATION.md).

After editing anything in `tasks/`, `tools/` or `datasets/manifest.json` (before the freeze only), run
`python3 scripts/build_prompts.py` and commit the regenerated `prompts/`.

## Results gallery (Observable)

`gallery/` is an [Observable Framework](https://observablehq.com/framework/) project with one page per
example. Each run is shown live (D3 in an iframe, Vega-Lite with vega-embed 7.3.0, time-i-gram with
`time-i-gram@0.1.0` from npm, ggtime as the SVG its script wrote), followed by its code, the
agent's REPORT, the scores from `results/scores.csv` and the evaluator's captures.

```bash
cd gallery && npm install && cd ..
python3 scripts/build_gallery.py          # or --demo to try it with the fixtures in gallery/fixtures/
cd gallery && npm run dev                 # local preview; `npm run build` or `npm run deploy` (Observable Cloud)
```

