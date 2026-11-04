# Task E1: How did the water temperature at each depth change month by month?

Make one visualization with time-i-gram that answers this question for a coastal monitoring station
in Nova Scotia, Canada: **how did the water temperature at each sensor depth change, month by month,
from 2018 to 2025?**

## Data

- URL: https://raw.githubusercontent.com/rfordatascience/tidytuesday/6753376ef104727ef0ca3e3db6f2ca580c0d5a7b/data/2026/2026-03-31/ocean_temperature.csv
- Format: comma-separated, one header row.
- Publisher: Centre for Marine Applied Research (CMAR), Coastal Monitoring Program, station Birchy Head.
  Daily means of the sensor readings. License: Open Government Licence – Nova Scotia.
- One row per day and sensor depth. Columns:

  | Column | Type | Meaning |
  |---|---|---|
  | `date` | date (`YYYY-MM-DD`) | Day of the observations |
  | `sensor_depth_at_low_tide_m` | integer | Sensor depth in metres: 2, 5, 10, 15, 20, 30 or 40 |
  | `mean_temperature_degree_c` | number | Mean water temperature that day, °C |
  | `sd_temperature_degree_c` | number | Standard deviation of that day's readings, °C |
  | `n_obs` | integer | Number of readings that day |

- Sensors were sometimes out of the water, so some depths have no data for some days.

## Requirements

- **R1.** Show the **monthly mean** water temperature for **each of the 7 depths**, computed from the daily rows.
- **R2.** The time axis covers the whole record (February 2018 to December 2025) at monthly resolution.
- **R3.** A month in which a depth has no data at all is shown as **missing** (a visible gap or empty cell),
  not interpolated or drawn as zero.
- **R4.** The reader can tell which depth each mark belongs to (legend or direct labels), and depths appear
  in depth order (2 m to 40 m).
- **R5.** The temperature axis or colour scale is labelled with its unit (°C).
- **R6.** The figure has a title and a one-sentence caption stating the main pattern you see.

## Rules

1. Load the data **directly from the URL above, exactly as published**. Do not download, edit, convert,
   reshape or re-save the file outside your deliverable. Any parsing, filtering, aggregation or reshaping
   must happen inside your deliverable (the time-i-gram specification).
2. Compute everything from the data. Do not type data values into the deliverable by hand (for example,
   do not hard-code which week was the peak).
3. Use only time-i-gram and what the Tool section below allows. Do not add other libraries or packages to
   fill a gap.
4. If time-i-gram cannot do a requirement, build the closest version it can do, keep going, and record the
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

## Tool: time-i-gram

- **Tool and version:** time-i-gram 0.1.0, a grammar for time-based data that extends Gosling.js (npm package
  `time-i-gram`). Source: https://github.com/vanessastoiber/time-i-gram at tag `v0.1.0`
  (commit `fa8a247161eafbb67c97bfb4e6af18ac034b0dab`).
- **Documentation:** you may use the web. The official documentation is, at that tag, the repository's
  `README.md`, the JSON schema `src/gosling-schema/gosling.schema.json` and the example specifications under
  `editor/example/`; and the package page https://www.npmjs.com/package/time-i-gram.
- **Deliverable:** one file, `spec.json`, a single time-i-gram specification (JSON).
- **How it will be run:** passed to `embed(element, spec)` from time-i-gram 0.1.0
  (`https://cdn.jsdelivr.net/npm/time-i-gram@0.1.0/dist/index.js`) in Chromium (latest stable), window
  1400 × 900 px. It must render without errors.
- **Allowed:** everything in the time-i-gram specification language, including the time-aware data sources,
  time coordinate systems and linking.
- **Not allowed:** custom JavaScript, editing time-i-gram's source code, or data fetchers other than those
  built in.
