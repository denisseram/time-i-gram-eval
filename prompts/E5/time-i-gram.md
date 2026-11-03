> **DRAFT, do not run:** the data URL for this example is not pinned and verified yet (see datasets/manifest.json).

# Task E5: Five years of 10-minute weather data, from overview to single readings

Make one visualization with time-i-gram that lets a reader see **five years of 10-minute weather
measurements at a glance and zoom in down to individual 10-minute readings**.

## Data

- URL: TODO: confirm station id (105 = Wien Hohe Warte?) then use https://dataset.api.hub.geosphere.at/v1/station/historical/klima-v2-10min?parameters=tl,rr&station_ids=105&start=2020-01-01T00:00&end=2024-12-31T23:50&output_format=csv or a byte-identical saved copy
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

- Missing measurements are empty fields.

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
