# Task E5: Five years of 10-minute weather data, from overview to single readings

Make one visualization with ggtime that lets a reader see **five years of 10-minute weather
measurements at a glance and zoom in down to individual 10-minute readings**.

## Data

- URL: https://raw.githubusercontent.com/denisseram/dataset-snapshots/3731e02e38c75e5d70ae92bf3596a69951866c2d/geosphere_wien_10min_2020-2024.csv
- Format: comma-separated, one header row.
- Publisher: GeoSphere Austria, quality-controlled station data in 10-minute resolution (`klima-v2-10min`),
  station Wien Hohe Warte, 2020-01-01 to 2024-12-31. License: CC BY 4.0.
- One row per 10-minute step (about 263,000 rows). Columns:

  | Column | Type | Meaning |
  |---|---|---|
  | `time` | date-time (ISO 8601, UTC offset `+00:00`, e.g. `2020-01-01T00:10+00:00`) | Time stamp of the 10-minute value |
  | `station` | integer | Station id (105) |
  | `tl` | number | Air temperature 2 m above ground, °C |
  | `rr` | number | Precipitation in the 10-minute interval, mm |
  | `substation` | integer | Id of the measuring site within the station |

- A missing measurement would be an empty field.

## Requirements

- **R1.** An **overview** shows the whole period 2020–2024 for `tl` at once.
- **R2.** A **detail** view can show any period down to **individual 10-minute readings**.
- **R3.** Overview and detail are **linked**: selecting a range in the overview sets the period shown in
  the detail view.
- **R4.** Precipitation `rr` is shown in the detail view as its own track or axis, aligned in time with `tl`.
- **R5.** Time axis labels fit the zoom level (years and months in the overview; down to hours and minutes
  in the detail).
- **R6.** All rows are loaded. Aggregating for the overview inside your deliverable is allowed; discarding
  data before loading is not.
- **R7.** Axes are labelled with units (°C, mm per 10 min, UTC). The figure has a title and a one-sentence
  caption stating the main pattern you see.

## Rules

1. Load the data **directly from the URL above, exactly as published**. Do not download, edit, convert,
   reshape or re-save the file outside your deliverable. Any parsing, filtering, aggregation or reshaping
   must happen inside your deliverable (the R script).
2. Compute everything from the data. Do not type data values into the deliverable by hand (for example,
   do not hard-code which week was the peak).
3. Use only ggtime and what the Tool section below allows. Do not add other libraries or packages to
   fill a gap.
4. If ggtime cannot do a requirement, build the closest version it can do, keep going, and record the
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

## Tool: ggtime (R)

- **Tool and version:** R 4.5, ggtime 1.1.0 from CRAN, with ggplot2 and the packages ggtime depends on
  (tsibble, mixtime, …).
- **Documentation:** you may use the web. The official documentation is
  https://pkg.mitchelloharawild.com/ggtime/ (reference and articles), with https://ggplot2.tidyverse.org and
  https://tsibble.tidyverts.org for ggplot2 and tsibble.
- **Deliverable:** one file, `plot.R`. Running it must write the figure to `plot.png` (1400 × 900 px) and
  `plot.svg` in the working directory.
- **How it will be run:** `Rscript plot.R` in a folder containing only `plot.R`, with internet access and the
  packages below installed. It must finish without errors.
- **Allowed:** ggtime, ggplot2, tsibble, mixtime, readr, dplyr, tidyr, lubridate, scales, svglite (only to
  write `plot.svg`), and patchwork (only to arrange several plots in one figure).
- **Not allowed:** any other package, in particular interactive or web graphics packages (plotly, ggiraph,
  htmlwidgets, shiny, …).
