> **DRAFT, do not run:** the data URL for this example is not pinned and verified yet (see datasets/manifest.json).

# Task E4: Do Ubuntu releases follow the same life cycle once aligned on their release date?

Make one visualization with time-i-gram that answers this question: **once every Ubuntu release is
aligned on its own release date, do their life cycles look alike?** Compare long-term-support (LTS)
releases with interim releases.

## Data

- URL: TODO: pinned raw URL of ubuntu.csv from https://salsa.debian.org/debian/distro-info-data (tag matching package 2026.10.12), or a byte-identical copy hosted by you
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
