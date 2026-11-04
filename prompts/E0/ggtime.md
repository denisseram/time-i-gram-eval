# Task E0: How did traffic on the A64 vary during May 2021?

Make one visualization with ggtime that answers this question for four traffic sensors on the A64
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
