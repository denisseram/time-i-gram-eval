# Task E4: Do Ubuntu releases follow the same life cycle once aligned on their release date?

Make one visualization with ggtime that answers this question: **once every Ubuntu release is
aligned on its own release date, do their life cycles look alike?** Compare long-term-support (LTS)
releases with interim releases.

## Data

- URL: https://raw.githubusercontent.com/denisseram/dataset-snapshots/3731e02e38c75e5d70ae92bf3596a69951866c2d/ubuntu.csv
- Format: comma-separated, one header row. **Rows have different numbers of fields:** trailing fields that
  do not apply to a release are omitted.
- Publisher: `distro-info-data` (Debian and Ubuntu developers), the release table used by Ubuntu's
  `ubuntu-distro-info` tool. License: ISC.
- One row per Ubuntu release. Columns:

  | Column | Type | Meaning |
  |---|---|---|
  | `version` | text | Version, e.g. `22.04 LTS`, `22.10`. LTS releases contain `LTS` |
  | `codename` | text | e.g. `Jammy Jellyfish` |
  | `series` | text | e.g. `jammy` |
  | `created` | date (`YYYY-MM-DD`) | Start of development of the release |
  | `release` | date | Release date |
  | `eol` | date | End of standard support |
  | `eol-server` | date | End of standard support for the server edition (only some LTS releases) |
  | `eol-esm` | date | End of Expanded Security Maintenance (LTS releases only) |
  | `eol-legacy` | date | End of the Legacy support add-on (recent LTS releases only) |

- Some dates are in the future (planned).

## Requirements

- **R1.** One row per release, labelled with its version, ordered by release date.
- **R2.** The horizontal axis is **time relative to each release's own release date** (0 = release), in
  months or years, with the unit in the axis title.
- **R3.** Each row shows its life-cycle **intervals** as bars, each phase in its own colour with a legend:
  development (`created` to `release`), standard support (`release` to `eol`), extended server support
  (`eol` to `eol-server`, only when `eol-server` is later than `eol`), ESM (end of the previous phase to
  `eol-esm`) and legacy (`eol-esm` to `eol-legacy`). Phases with no date are not drawn.
- **R4.** The **events** `created` and `release` are marked on each row (for example as points or ticks).
- **R5.** LTS and interim releases can be told apart (for example by grouping, facet, label or marker).
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
- **How it will be run:** `Rscript plot.R` in a folder containing only `plot.R`, with internet access and the
  packages below installed. It must finish without errors.
- **Allowed:** ggtime, ggplot2, tsibble, mixtime, readr, dplyr, tidyr, lubridate, scales, svglite (only to
  write `plot.svg`), and patchwork (only to arrange several plots in one figure).
- **Not allowed:** any other package, in particular interactive or web graphics packages (plotly, ggiraph,
  htmlwidgets, shiny, …).
