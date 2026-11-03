# Evaluation protocol

## What is compared

Four agents get the **same task text, the same data URL and the same rules** for each example. Only the
Tool section differs (name, pinned version, official documentation, deliverable, how it is run). This is
enforced by `scripts/build_prompts.py --check`.

| Tool | Deliverable | Rendered with |
|---|---|---|
| D3 7.9.0 | `index.html` | static server + Chromium, 1400 × 900 |
| Vega-Lite 6.5.0 | `spec.vl.json` | vega-embed 7.3.0 (Vega 6.4.0) + Chromium, 1400 × 900 |
| ggtime 1.1.0 (R 4.5) | `plot.R` → `plot.png`, `plot.svg` | `Rscript plot.R` |
| time-i-gram 0.1.0 (npm) | `spec.json` | `embed(element, spec)` from `time-i-gram@0.1.0` + Chromium, 1400 × 900 |

Examples: **E1–E5**. E6 (spiral) is excluded; its task and rubric are kept in `tasks/excluded/` and
`rubrics/excluded/`.

## Fixed settings (decided 2026-11-03; identical for all four tools)

| Setting | Value |
|---|---|
| Agent | Claude Code, headless (`claude -p`); record the CLI version in every `run.md` |
| Model | Claude Opus 5.5 (`claude-opus-5-5`) |
| Limit per run | 50 turns (`--max-turns 50`) or 30 minutes wall time, whichever comes first; the deliverable saved at that point is evaluated |
| Web | open for all agents |
| Self-check | yes: every agent has the same `render` command (below) |
| Repeats | 3 per example × tool (`r01`–`r03`): 5 × 4 × 3 = **60 runs** |
| Order | the four tools of one example in random order; a new conversation for every run |

## The `render` command (same for all tools)

Installed in the run environment and used both by the agents (self-check) and by the evaluators.

```
render <deliverable>      # index.html | spec.vl.json | plot.R | spec.json, chosen by file name
```

- Renders the file exactly as the Tool section says (table above), waits until rendering finishes
  (network idle plus a fixed delay, or a timeout of 60 s), and writes `render.png` (1400 × 900) next to it.
- Prints every console error and warning (browser) or R error, warning and message, and exits non-zero if
  the deliverable could not be rendered.
- Has no tool-specific hints: the output format is identical for all four tools.

## Isolation (important for held-out data)

- Each run starts in a **fresh, empty folder** with only `prompt.md` in it.
- Because the web is open, the agents must not be able to find the evaluation materials online:
  **keep this repository private** and **do not deploy the gallery** until all runs are done.
- The time-i-gram agent reads the time-i-gram repository at tag `v0.1.0`. That commit contains none of the
  evaluation data or files.

## Per run

1. `python3 scripts/verify_data.py` (once per batch): pinned files unchanged.
2. `python3 scripts/new_run.py <example> <tool>`: creates the run folder with the exact prompt.
3. Run the agent on `prompt.md` in a fresh folder with the fixed settings. Save the full transcript
   (`transcript.jsonl`), the deliverable and the REPORT block (`report.txt`) in the run folder.
4. Render the deliverable with `render`. **No manual edits.** If it only works after an edit, record the
   edit, but score the unedited version.
5. Keep `render.png` and the console output (`console.txt`); for E3 and E5 also record the interaction
   (`interaction.gif` or before/after screenshots).
6. Score with `rubrics/<example>.md`, fill `run.md`, and add one row to `results/scores.csv`.
7. `python3 scripts/measure.py` fills the deliverable size columns (`deliverable_lines`, `deliverable_chars`).
8. `python3 scripts/build_gallery.py` and `cd gallery && npm run dev` to see all outputs with their code.

## Scoring

- Requirements R1…Rn: 0 / 1 / 2 per `rubrics/README.md`, scored on the rendered output.
- `score_sum` / `score_max` per run; compare tools by mean and spread over the 3 repeats.
- Report per requirement, and separate "the tool cannot express it" (e.g. interaction in ggtime) from
  "the agent failed".
- Efficiency: deliverable size, agent turns, tool calls, `render` calls, tokens, wall time.
- Honesty: `report_mismatches` = requirements the agent marked `done` that score below 2.
- Ideally two evaluators score independently; resolve disagreements and note them.
- Evaluators should not know which tool made an output when that is possible (it usually is not for
  ggtime vs. the browser tools; record it as a limitation).

## Freeze

Before the first real run, tag this repository (e.g. `v1-frozen`). If a prompt, rubric or tool version
changes after any results have been seen, re-run all four tools for the affected examples and record why.
