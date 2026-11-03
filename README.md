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
| `PROTOCOL.md` | How to run and score, settings to keep fixed | evaluators |
| `runs/<E>/<tool>/<run_id>/` | One folder per run: prompt copy, transcript, deliverable, screenshots, `run.md` | evaluators |
| `results/scores.csv` | One row per run | evaluators |
| `templates/run.md` | Template for `run.md` | evaluators |
| `gallery/` | Observable Framework site: every run's output rendered live, with its code, REPORT and scores | evaluators |
| `scripts/` | `build_prompts.py [--check]`, `verify_data.py`, `new_run.py`, `measure.py`, `build_gallery.py` | evaluators |

## Examples

| Ex | Question | Dataset | Prompts |
|---|---|---|---|
| E1 | How did each category change month by month? | Ocean temperature at 7 depths, Nova Scotia (daily, 2018–2025) | ready |
| E2 | Do the years follow the same cycle? (calendar, one row per year) | RKI ARE consultation incidence, Germany (weekly, 2012–2026) | ready |
| E3 | Does the peak happen at the same time each year? (circle + linked linear view) | same as E2 | ready |
| E4 | Do trajectories look alike once aligned to their own event? | Ubuntu release history (46 releases) | **draft**: data URL not pinned |
| E5 | Overview of several years, detail down to minutes | GeoSphere Austria 10-min, Wien Hohe Warte, 2020–2024 | **draft**: data not downloaded |
| E6 | (excluded) Spiral, one turn per year | same as E2 | not run |

## Quick start

```bash
python3 scripts/build_prompts.py --check   # prompts up to date and identical outside the Tool section
python3 scripts/verify_data.py             # pinned data files unchanged
python3 scripts/new_run.py E1 d3           # -> runs/E1/d3/E1-d3-r01/ with prompt.md and run.md
```

After editing anything in `tasks/`, `tools/` or `datasets/manifest.json`, run
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

Library versions are pinned in `gallery/package.json`; `build_gallery.py` copies them into `gallery/src/lib/`.
**Do not deploy the gallery before all runs are done** (the agents have open web access). The agents are not asked to produce Observable notebooks: each writes its tool's
native deliverable, and the gallery collects them, so the comparison stays the same for all four tools.

## Decisions (2026-11-03)

E3 keeps the range brush (R5) · Claude Code + Claude Opus 5.5 · open web for all agents · agents can
check their work with the same `render` command · 3 repeats · 50 turns or 30 min per run · E6 excluded ·
time-i-gram 0.1.0 from npm, source at `vanessastoiber/time-i-gram` tag `v0.1.0`. Details in `PROTOCOL.md`.

## Still to do before running

- [ ] **time-i-gram source on GitHub.** Merge the branch with commit `fa8a247` (the package's source)
      into `vanessastoiber/time-i-gram` **with a merge commit** (not "squash" or "rebase": those change the
      commit hash), then tag `fa8a247` as `v0.1.0` and push the tag. The prompts cite both.
- [ ] **E4 data.** Pin a raw URL of `ubuntu.csv` from salsa.debian.org/debian/distro-info-data (a tag), check
      its sha256 against `datasets/manifest.json`, set `status` to `verified`, run `scripts/build_prompts.py`.
- [ ] **E5 data.** Confirm the GeoSphere station id for Wien Hohe Warte, save one response, record URL,
      size, rows and sha256 in the manifest, check the columns in `tasks/E5.md`, fill `rubrics/E5.md`.
- [ ] **Run environment** (e.g. a Docker image): Node 22, Chromium + Playwright, R 4.5 with ggtime 1.1.0
      and the allowed packages, Claude Code CLI, and the `render` command from `PROTOCOL.md`. The
      evaluation repository must not be inside it. Confirm `packageVersion("ggtime")`.
- [ ] **Runner** (`scripts/run_agent.sh`): fresh folder, copy `prompt.md`, run Claude Code with the fixed
      settings, copy transcript, deliverable and REPORT back into `runs/`.
- [ ] **Keep this repository private** and push it to GitHub.
- [ ] **Pilot**: one run per tool on a dataset that is not part of the evaluation; check the whole pipeline,
      then delete the pilot results.
- [ ] **Freeze**: `scripts/verify_data.py`, `scripts/build_prompts.py --check`, tag `v1-frozen`.
