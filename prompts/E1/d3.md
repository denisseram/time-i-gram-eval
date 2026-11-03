# Task E1: How did the water temperature at each depth change month by month?

Make one visualization with D3 that answers this question for a coastal monitoring station
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
   must happen inside your deliverable (the HTML file and its JavaScript).
2. Compute everything from the data. Do not type data values into the deliverable by hand (for example,
   do not hard-code which week was the peak).
3. Use only D3 and what the Tool section below allows. Do not add other libraries or packages to
   fill a gap.
4. If D3 cannot do a requirement, build the closest version it can do, keep going, and record the
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

## Tool: D3

- **Tool and version:** D3 7.9.0, loaded with
  `<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>`.
- **Documentation:** you may use the web. The official documentation is https://d3js.org.
- **Deliverable:** one file, `index.html`, with all markup, CSS and JavaScript inline.
- **How it will be run:** served from a local static web server and opened in Chromium (latest stable),
  window 1400 × 900 px. It must render without console errors.
- **Allowed:** D3 7.9.0 and plain browser JavaScript, HTML, CSS and SVG/Canvas.
- **Not allowed:** any other library (no Vega, Plot, Lodash, Moment, etc.).
