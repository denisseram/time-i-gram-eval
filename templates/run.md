# Run <run_id>

Copy this file to `runs/<example>/<tool>/<run_id>/run.md` and fill it in.
`run_id` = `<example>-<tool>-r<NN>`, e.g. `E3-vega-lite-r02`.

## Setup

- Example / tool / repeat:
- Prompt file and sha256 (from `prompts/index.json`):
- Model and version:
- Agent harness and settings (max turns, temperature, tools available, web access):
- Can the agent render its own output? yes / no
- Start / end time (UTC):

## Files in this folder

- `prompt.md`: exact prompt sent (byte-identical copy)
- `transcript.*`: full agent transcript, including tool calls
- deliverable: `index.html` | `spec.vl.json` | `plot.R` (+ `plot.png`, `plot.svg`) | `spec.json`
- `render.png`: screenshot at 1400 × 900 of the deliverable rendered as specified in the prompt
- `interaction.gif` or `interaction-*.png` (E3, E5): the linking/zoom requirement being exercised
- `console.txt`: errors and warnings from rendering
- `report.txt`: the agent's REPORT block, copied verbatim

## Rendering

- Rendered without edits? yes / no
- If no: what was changed (counts as `manual_fixes`; score the unedited version as 0 for anything it breaks):

## Scores (see `rubrics/<example>.md`)

| Req | Score 0/1/2 | Evidence (screenshot or one line) |
|---|---|---|
| R1 | | |
| R2 | | |
| … | | |

- Ground-truth checks failed:
- REPORT mismatches (agent said `done`, score < 2):

## Notes
