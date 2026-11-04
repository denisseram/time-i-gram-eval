# Task E0: How did traffic on the A64 vary during May 2021?

Make one visualization with Vega-Lite that answers this question for four traffic sensors on the A64
road in England: **how did the traffic volume at each sensor vary during May 2021?**

## Data

- URL: https://raw.githubusercontent.com/rfordatascience/tidytuesday/6753376ef104727ef0ca3e3db6f2ca580c0d5a7b/data/2024/2024-12-03/A64_traffic.csv
- Format: comma-separated, one header row.
- Publisher: National Highways (WebTRIS traffic sensors), compiled for TidyTuesday 2024-12-03.
- One row per sensor and 15-minute interval. The columns used here:

  | Column | Type | Meaning |
  |---|---|---|
  | `SiteId` | integer | Sensor id (4 sensors) |
  | `Report Date` | date-time (`YYYY-MM-DDT00:00:00`) | Day of the measurement (the time part is always midnight) |
  | `Time Period Ending` | time (`HH:MM:SS`) | End of the 15-minute interval within that day |
  | `Total Volume` | number | Number of vehicles in the interval |
  | `Name` | text | Description of the sensor's location |

- The file has more columns (vehicle lengths and speeds); they are not needed. Some intervals have no
  value (empty `Total Volume`).

## Requirements

- **R1.** One line per sensor showing `Total Volume` over the whole month at 15-minute resolution
  (the time of each value combines `Report Date` and `Time Period Ending`).
- **R2.** Intervals without a value are shown as gaps, not as zero and not bridged by a line.
- **R3.** The sensors can be told apart (legend or labels with `SiteId`).
- **R4.** The figure has a title and a one-sentence caption stating the main pattern you see.

## Rules

1. Load the data **directly from the URL above, exactly as published**. Do not download, edit, convert,
   reshape or re-save the file outside your deliverable. Any parsing, filtering, aggregation or reshaping
   must happen inside your deliverable (the Vega-Lite specification).
2. Compute everything from the data. Do not type data values into the deliverable by hand (for example,
   do not hard-code which week was the peak).
3. Use only Vega-Lite and what the Tool section below allows. Do not add other libraries or packages to
   fill a gap.
4. If Vega-Lite cannot do a requirement, build the closest version it can do, keep going, and record the
   gap in your report. Do not drop the rest of the task because one requirement is not possible.
5. Do not ask questions. Where the task is ambiguous, choose a reasonable reading and record it under
   `assumptions` in your report.
6. Deliver exactly one deliverable file (named as in the Tool section). It must run or render as-is, with no
   manual edits.
7. Check your work with the `render` command: `render <deliverable>` runs or renders your file exactly as
   described in the Tool section, saves the result as `render.png` (1400 × 900 px) and prints any errors and
   warnings. Use it as often as you like.
8. You have at most 50 turns and 30 minutes. Make sure your deliverable is saved before the limit; what is
   saved at the end is what will be evaluated.

## Report

End your answer with this block, filled in. Keep each line short. Use the requirement ids from this task.

```
REPORT
deliverable: <file name>
requirements:
  R1: done | partial | not possible - <one line>
  R2: ...
assumptions:
  - <one line each, or "none">
limitations:
  - <anything the reader should know about the figure, or "none">
```

## Tool: Vega-Lite

- **Tool and version:** Vega-Lite 6.5.0; the specification must declare
  `"$schema": "https://vega.github.io/schema/vega-lite/v6.json"`.
- **Documentation:** you may use the web. The official documentation is https://vega.github.io/vega-lite/docs/
  and the example gallery is https://vega.github.io/vega-lite/examples/.
- **Deliverable:** one file, `spec.vl.json`, a single Vega-Lite specification (JSON).
- **How it will be run:** rendered with vega-embed 7.3.0 (Vega 6.4.0) in Chromium (latest stable), window
  1400 × 900 px, with default embed options. It must render without errors or warnings that change the figure.
- **Allowed:** everything in the Vega-Lite specification language, including transforms, parameters and
  expressions.
- **Not allowed:** a compiled or hand-written Vega (non-Lite) specification, custom JavaScript, or changes to
  the embed options.
