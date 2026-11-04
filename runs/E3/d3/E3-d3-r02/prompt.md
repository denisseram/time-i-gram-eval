# Task E3: Does the peak happen at the same time each year?

Make one visualization with D3 that answers this question for acute respiratory illness in
Germany: **does the yearly peak happen at the same time every year?** Combine a **circular (cyclic) view**
of the year with a **linear view** of the whole series, and link the two.

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

- **R1.** A **circular view**: the angle is the ISO week of the year, **ISO week 1 at the top** (12 o'clock),
  weeks running clockwise, one full turn per ISO year. The radius (or another channel) encodes
  `ARE_Konsultationsinzidenz`.
- **R2.** Each ISO year is a separate line (or ring) in the circular view, and years can be told apart
  (colour or labels, with a legend).
- **R3.** For each **season** (column `Saison`), the week with the highest value is **marked** in the
  circular view.
- **R4.** A **linear view** shows the whole series, 2012 to 2026, on a calendar time axis.
- **R5.** The views are **linked**: selecting a time range in the linear view highlights the
  corresponding weeks in the circular view (the rest is dimmed or hidden).
- **R6.** Axes are labelled: week numbers (or months) around the circle, dates on the linear axis, and the
  value with its unit (consultations per 100,000 per week).
- **R7.** The figure has a title and a one-sentence caption stating the main pattern you see.

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
