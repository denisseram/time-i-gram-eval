# Task E2: Do the years follow the same cycle?

Make one visualization with ggtime that answers this question for acute respiratory illness in
Germany: **does every year follow the same yearly cycle?** Use a calendar layout with **one row per year**.

## Data

- URL: https://raw.githubusercontent.com/robert-koch-institut/ARE-Konsultationsinzidenz/65ac2d278c06333808415795d65f0347c54be638/ARE-Konsultationsinzidenz.tsv
- Format: **tab-separated**, one header row.
- Publisher: Robert Koch-Institut (RKI), ARE-Praxis-Sentinel. License: CC BY 4.0.
- Weekly estimates of how many people per 100,000 consulted a doctor's practice for a new acute
  respiratory illness (ARE). Columns:

  | Column | Type | Meaning |
  |---|---|---|
  | `Saison` | text (`YYYY/YY`) | Season: ISO week 40 of the first year to ISO week 39 of the next |
  | `Kalenderwoche` | text (`YYYY-Www`) | Reporting week in ISO 8601 week format |
  | `Bundesland` | text | `Bundesweit` (all of Germany) or one of the 16 states |
  | `Bundesland_ID` | integer | `0` for `Bundesweit`, 1–16 for the states |
  | `Altersgruppe` | text | Age group: `00+` (all ages), `0-4`, `5-14`, `15-34`, `35-59`, `60+` |
  | `ARE_Konsultationsinzidenz` | integer | ARE consultations per 100,000 population in that week |

- **Use only the rows with `Bundesland` = `Bundesweit` and `Altersgruppe` = `00+`.**

## Requirements

- **R1.** One row per **ISO year** that appears in the data, in chronological order from top to bottom.
- **R2.** Within each row, one cell per **ISO week** (week 1 on the left). Some ISO years have 53 weeks;
  week 53 must appear where it exists.
- **R3.** Cell colour encodes `ARE_Konsultationsinzidenz` with a sequential colour scale and a legend that
  states the unit (consultations per 100,000 per week).
- **R4.** Weeks outside the data (before the first and after the last reported week) are left empty, not
  shown as zero.
- **R5.** Week numbers are labelled along the horizontal axis and years along the vertical axis.
- **R6.** The figure has a title and a one-sentence caption stating the main pattern you see.

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
- **How it will be run:** `Rscript plot.R` in an empty directory with internet access and the packages below
  installed. It must finish without errors.
- **Allowed:** ggtime, ggplot2, tsibble, mixtime, readr, dplyr, tidyr, lubridate, scales, and patchwork
  (only to arrange several plots in one figure).
- **Not allowed:** any other package, in particular interactive or web graphics packages (plotly, ggiraph,
  htmlwidgets, shiny, …).
