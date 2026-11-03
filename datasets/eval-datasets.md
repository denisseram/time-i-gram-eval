# Evaluation datasets (E1–E6)

Candidate real-world datasets for the time-i-gram vs. Vega-Lite / D3 / ggtime evaluation.
Checked on 2026-11-02 against repo commit `bf79949` (2026-10-09).

**Note.** This survey was written for the time-i-gram repo and moved here; paths like `docs/` refer to that repo.

**How the checks were done.** The sandbox used for this survey could only download from GitHub
(plus the npm/PyPI registries). Each candidate is therefore marked:

- ✅ **downloaded**: the file was fetched from the pinned URL and profiled with pandas (rows, columns, ranges,
  missing values, gaps). Every number below for these files was computed from the file.
- 📄 **docs only**: the host was unreachable. Licence, format and coverage come from the publisher's
  documentation pages. **Download and re-check these before you commit to them.**

**Held-out check.** The repo's examples and README use: seattle-weather (vega and thesis copies),
unemployment-across-industries (vega and the denisseram copy), WHO FluNet USA (`who_flu_usa.csv`), NYC taxi
trip duration, FitBit, solar power 2022 plus the GeoSphere daily weather file (`weather_data_local_2022…`), and
genomics files. None of the recommended files appear there. One caution: the E5 recommendation comes from the
same publisher and API (GeoSphere) as the solar example's weather file. It is a different dataset
(10-minute rather than daily) from a different station, but the column layout will look familiar to the agents.

**Date parsing.** Parsing was tested in each tool:

- **time-i-gram:** read in `src/data-fetchers/time-utils.ts` and `csv-time-data-fetcher.ts`.
- **Vega:** tested with `vega@5` `read()`.
- **D3:** tested with `d3-time-format@4`.
- **tsibble/ggtime:** read in the tsibble source. It was not executed because R is not available in the sandbox.

---

## 1. Summary

| Ex | Recommended dataset | Why | License | Rows | Size | Direct URL (pinned) |
|---|---|---|---|---|---|---|
| **E1** | Coastal ocean temperature by depth, Birchy Head, Nova Scotia (CMAR Coastal Monitoring Program; daily means, TidyTuesday 2026-03-31) ✅ | Daily data for 7.8 years (2018-02-20 to 2025-12-06) at 7 depths, in long format with ISO dates. It has real gaps: the 2 m sensor is missing 348 days (including May–Nov 2024), 5 m is missing 191 and 40 m is missing 225. The month-by-month story is clear: the surface warms to about 17 °C in Aug–Sep while 40 m stays below 7 °C, and all depths converge at 2–4 °C in winter. | Open Government Licence – Nova Scotia (data); TidyTuesday repo CC0 1.0 | 19,165 | 1.0 MB | https://raw.githubusercontent.com/rfordatascience/tidytuesday/6753376ef104727ef0ca3e3db6f2ca580c0d5a7b/data/2026/2026-03-31/ocean_temperature.csv |
| **E2 + E3** | RKI ARE-Konsultationsinzidenz: weekly acute respiratory illness consultation incidence, Germany ✅ | ISO weeks 2012-W40 to 2026-W43: 734 national weeks with no gaps, 14 full seasons, and 53-week years (2015, 2020). The peak falls in ISO weeks 5–12 in most seasons but in week 50 in 2022 and 2023, and in week 44 in 2020, so it crosses the year boundary. Agency source with a DOI. | CC BY 4.0 | 24,756 (734 per series) | 1.0 MB (TSV) | https://raw.githubusercontent.com/robert-koch-institut/ARE-Konsultationsinzidenz/65ac2d278c06333808415795d65f0347c54be638/ARE-Konsultationsinzidenz.tsv |
| ✅ E2/E3 week format | | **Resolved 2026-11-03:** time-i-gram 0.1.0 (npm) reads `YYYY-Www` in `dateFields`. Original note: Weeks are single strings such as `2012-W40`. D3 (`%G-W%V`), Vega-Lite (`parse: "utc:'%G-W%V'"`) and tsibble `yearweek()` read them. **time-i-gram's `csv-time` cannot**: it needs a date, or separate numeric year and week columns. See §2 E2/E3 for the options. | | | | |
| **E4** | Ubuntu release history (`ubuntu.csv` from Debian/Ubuntu `distro-info-data`) ✅ | 46 releases (entities), each with a development start (`created`) and a release date (events). The intervals are the development cycle, standard support (`release`→`eol`) and, for LTS releases, `eol-server`, `eol-esm` and `eol-legacy`. Align on `release`. The pattern: LTS releases get about 5 years of standard support (plus 5 of ESM), while interim releases get 9 months. ISO dates. | ISC | 46 | 3.2 KB | `https://salsa.debian.org/debian/distro-info-data/-/raw/<tag>/ubuntu.csv` (pin a tag; host not reachable from here, verified copy is from package `2026.10.12-0ubuntu0.24.04.1`) |
| **E5** | GeoSphere Austria `klima-v2-10min`, one station (Wien Hohe Warte), air temperature `tl` + precipitation `rr`, 2020–2024 📄 | 10-minute, quality-controlled national-agency data with a DOI and ISO timestamps carrying an explicit `+00:00` offset. The request fits the API's 1,000,000-value CSV limit (2 × 263,088). Expected overview: the seasonal cycle. Expected detail: the diurnal cycle and individual storms. **Not downloaded.** | CC BY 4.0 | 263,088 (computed) | ≈10 MB (estimated) | `https://dataset.api.hub.geosphere.at/v1/station/historical/klima-v2-10min?parameters=tl,rr&station_ids=105&start=2020-01-01T00:00&end=2024-12-31T23:50&output_format=csv` (station id 105 unconfirmed) |
| **E6** | Reuse E2 (RKI ARE). If the week-string blocker stays, use E1's ocean temperature at 10 m instead ✅ | ARE: 14 turns with a strong yearly cycle and a sharp Christmas dip each turn. Ocean 10 m: daily, 7.8 turns, no gaps, peak in Sep, minimum in Feb–Mar. | CC BY 4.0 / OGL–NS | 734 / 2,847 after filter | 1.0 MB / 1.0 MB | as above |

---

## 2. Per example

### E1: "How did each category change month by month?"

#### E1-A. Coastal ocean temperature by depth, Birchy Head (✅ recommended)

- **Publisher:** Centre for Marine Applied Research (CMAR), Coastal Monitoring Program, for the Nova Scotia
  Department of Fisheries and Aquaculture. The daily-mean file was compiled by CMAR staff (D. Dempsey,
  R. Woodside) for TidyTuesday 2026-03-31 from the *Lunenburg County Water Quality Data* (Nova Scotia Open Data,
  dataset `eda5-aubu`), station "Birchy Head". It drops QC "Fail" readings and takes daily means of the
  raw sensor readings.
- **Landing pages:**
  - https://github.com/rfordatascience/tidytuesday/tree/main/data/2026/2026-03-31
  - https://catalogue.cioosatlantic.ca/dataset/ca-cioos_f12b30fd-0010-3002-9a6b-803aa9925687
- **URL:** see the summary table. It is pinned to tidytuesday commit `6753376e`. sha256 starts `ca9ed1ac30d91c82`.
- **License:** CIOOS catalogue: "Licence: Open Government Licence – Nova Scotia", with the request
  "Please acknowledge the Centre for Marine Applied Research in any published material that uses this data."
  The TidyTuesday repository is CC0 1.0.
- **Citation:** Centre for Marine Applied Research (2026). *Lunenburg County Water Quality Data*, Coastal Monitoring
  Program, station Birchy Head; daily means via TidyTuesday 2026-03-31. Nova Scotia Open Data Portal, `eda5-aubu`.
- **Columns:**
  - `date` (ISO date)
  - `sensor_depth_at_low_tide_m` (int: 2, 5, 10, 15, 20, 30, 40)
  - `mean_temperature_degree_c` (float)
  - `sd_temperature_degree_c` (float)
  - `n_obs` (int, 21–1005 readings per day)
- **Sample rows:**
  ```
  date,sensor_depth_at_low_tide_m,mean_temperature_degree_c,sd_temperature_degree_c,n_obs
  2018-02-20,2,1.5848387096774195,0.041301409801759795,31
  2018-02-20,5,1.4951612903225806,0.04288519307344016,31
  2018-02-20,10,1.4864285714285714,0.030671764586621676,21
  2018-02-20,15,1.627,0.04842932995613299,21
  2018-02-20,20,1.84375,0.042331258945027414,32
  ```
- **Range:** 2018-02-20 to 2025-12-06, daily. 19,165 rows, 1,004,292 bytes, UTF-8, no BOM.
- **Missing data:** missing days are absent rows, not NA (there are no NA values in the file).
  - 2 m: 348 days missing. The longest run is 2024-05-03 to 2024-11-20 (202 days); another is 2019-07-13 to 2019-11-21.
  - 5 m: 191 days missing (2023-07-02 to 2023-11-09, and others).
  - 40 m: 225 days missing (2022-11-04 to 2023-05-14, and others).
  - 10, 15, 20 and 30 m: complete.
  - A companion file, `ocean_temperature_deployments.csv`, has 14 deployment intervals (2018–2025).
- **Preprocessing:** none. Categories are numeric depths, so treat them as ordinal or nominal in the spec.
- **Pattern:** the water column stratifies every summer (2 m reaches about 17–18 °C in Aug–Sep, 40 m stays
  below 7 °C) and mixes every winter (all depths at 2–4 °C in Feb–Mar). The months where the lines separate and
  converge are easy to see.

#### E1-B. RKI COVID-19 hospitalisations by age group (✅)

- **Publisher:** Robert Koch-Institut. Landing page: https://github.com/robert-koch-institut/COVID-19-Hospitalisierungen_in_Deutschland
- **URL:** `https://raw.githubusercontent.com/robert-koch-institut/COVID-19-Hospitalisierungen_in_Deutschland/b5d5cc3376e4b3d496a66a3293f9bc639d35f23b/Aktuell_Deutschland_COVID-19-Hospitalisierungen.csv`.
  The file is rewritten daily, so always use a commit-pinned URL.
- **License:** "lizenziert unter der Creative Commons Namensnennung 4.0 International Public License | CC-BY 4.0".
  Citation: Robert Koch-Institut (2026). *COVID-19-Hospitalisierungen in Deutschland* [Data set]. Zenodo.
  https://doi.org/10.5281/zenodo.23877130
- **Columns:**
  - `Datum` (ISO date)
  - `Bundesland` (17 values, including `Bundesgebiet` for the national total)
  - `Bundesland_Id`
  - `Altersgruppe` (`00-04, 05-14, 15-34, 35-59, 60-79, 80+, 00+`)
  - `7T_Hospitalisierung_Faelle`
  - `7T_Hospitalisierung_Inzidenz`
- **Sample rows:**
  ```
  Datum,Bundesland,Bundesland_Id,Altersgruppe,7T_Hospitalisierung_Faelle,7T_Hospitalisierung_Inzidenz
  2026-11-02,Bundesgebiet,00,00-04,21,0.53
  2026-11-02,Bundesgebiet,00,00+,317,0.38
  2026-11-02,Bundesgebiet,00,05-14,1,0.01
  2026-11-02,Bundesgebiet,00,15-34,14,0.07
  2026-11-02,Bundesgebiet,00,35-59,31,0.11
  ```
- **Range:** 2020-03-01 to 2026-11-02, daily. 290,122 rows (17,066 for `Bundesgebiet`), 11.4 MB.
- **Missing data:** none. Every date is present for every group, so there are no gaps.
- **Preprocessing:** none (filter `Bundesgebiet` in the spec).
- **Caveats:**
  - Values are 7-day rolling sums, not daily counts. Say so in the caption.
  - `00+` is the total, not a category.
- **Pattern:** the 80+ group dominates every wave. Its highest monthly mean was in Oct 2022, about 108 per
  100,000 over 7 days.

#### E1-C. Toronto shelter occupancy by sector (✅)

- **Publisher:** City of Toronto Open Data, via TidyTuesday 2020-12-01.
- **URL:** `https://raw.githubusercontent.com/rfordatascience/tidytuesday/6753376ef104727ef0ca3e3db6f2ca580c0d5a7b/data/2020/2020-12-01/shelters.csv`
- **License:** Open Government Licence – Toronto according to the City portal. This was **not verified here**;
  the TidyTuesday readme only names open.toronto.ca.
- **Columns:**
  - `occupancy_date` (`2017-01-01T00:00:00`)
  - `sector` (Men, Women, Co-ed, Families, Youth)
  - `occupancy`, `capacity` (`capacity` has 343 NA)
  - 9 address and program columns
- **Size and range:** 115,916 rows (one per program per day), 21.4 MB, covering 2017-01-01 to 2019-12-31.
  That is exactly 3 years, the minimum.
- **Preprocessing:** none in the file, but the spec must aggregate programs per sector per day.
- **Pattern:** mean nightly occupancy in the Families sector rose from about 1,500 in 2017 to about 2,700 in 2018.
- **Weaker than A:** the span is the minimum, the license is not verified, and the extra aggregation step
  is a confound.

### E2 + E3: "Do the years follow the same cycle?" / "Does the peak happen at the same time each year?"

#### E2/E3-A. RKI ARE-Konsultationsinzidenz (✅ recommended, with one blocker)

- **Publisher:** Robert Koch-Institut, ARE-Praxis-Sentinel. Landing page: https://github.com/robert-koch-institut/ARE-Konsultationsinzidenz
- **URL:** see the summary table (commit `65ac2d27`, 2026-10-29). sha256 starts `025b5ef613cf5364`.
- **License:** "lizenziert unter der Creative Commons Namensnennung 4.0 International Public License | CC-BY 4.0".
  Citation: Robert Koch-Institut (2026). *ARE-Konsultationsinzidenz* [Data set]. Zenodo.
  https://doi.org/10.5281/zenodo.23758109 (the version DOI at the pinned commit).
- **Columns (tab-separated):**
  - `Saison` (`2012/13`)
  - `Kalenderwoche` (`YYYY-Www`, ISO 8601 per the data dictionary)
  - `Bundesland` (`Bundesweit` plus 16 states)
  - `Bundesland_ID`
  - `Altersgruppe` (`00+, 0-4, 5-14, 15-34, 35-59, 60+`)
  - `ARE_Konsultationsinzidenz` (int, per 100,000)
- **Sample rows:**
  ```
  Saison	Kalenderwoche	Bundesland	Bundesland_ID	Altersgruppe	ARE_Konsultationsinzidenz
  2012/13	2012-W40	Bundesweit	0	00+	970
  2012/13	2012-W41	Bundesweit	0	00+	1115
  2012/13	2012-W42	Bundesweit	0	00+	1163
  2012/13	2012-W43	Bundesweit	0	00+	1074
  2012/13	2012-W44	Bundesweit	0	00+	887
  ```
- **Range:** 2012-W40 to 2026-W43, weekly. 24,756 rows, 1,017,424 bytes, no BOM.
  - National series: 734 weeks per age group with no missing weeks. Includes 2015-W53 and 2020-W53.
  - State series: 212 weeks each, starting later.
- **Missing values:** documented as `NA`; none occur in this version.
- **Preprocessing:** none for D3, Vega-Lite or ggtime. time-i-gram needs a decision (below). The file is
  TSV (set `separator: "\t"` in `csv-time`, use `d3.tsv`, `format: {type: "tsv"}`, or `readr::read_tsv`).
- **Seasonal peak (national, all ages, season W40–W39):**

  | Season | Peak week |
  |---|---|
  | 2012/13 | W08 |
  | 2013/14 | W07 |
  | 2014/15 | W09 |
  | 2015/16 | W07 |
  | 2016/17 | W05 |
  | 2017/18 | W08 |
  | 2018/19 | W07 |
  | 2019/20 | W12 |
  | 2020/21 | 2020-W44 |
  | 2021/22 | W11 |
  | 2022/23 | **2022-W50** |
  | 2023/24 | **2023-W50** |
  | 2024/25 | W07 |
  | 2025/26 | W06 |

- **Pattern for E3:** the peak sits in February in most years, but jumped to mid-December in 2022 and 2023
  (and to autumn in the pandemic season 2020/21).
- **Pattern for E2:** every year has a low summer trough (about 300–1,000) and a sharp dip in ISO week 52
  (for example 2018: W51 = 1,344, W52 = 463, W01 = 901). That dip is a reporting artifact of the Christmas
  practice closures. It is worth a caption, and it means an `argmax` peak is never in W52.
- **Parsing `2012-W40`:**

  | Tool | Reads it? | How |
  |---|---|---|
  | D3 | ✅ tested | `d3.utcParse("%G-W%V")` gives 2012-10-01 |
  | Vega-Lite | ✅ tested | `format: {parse: {Kalenderwoche: "utc:'%G-W%V'"}}` gives 2012-10-01 |
  | ggtime / tsibble | ✅ by source | `tsibble::yearweek("2012-W40")` accepts a 4-digit year, a 1–2 digit week and the letter `W` |
  | time-i-gram `csv-time` | ❌ | `parseDateOnly` needs three numeric parts and `Date.parse` returns NaN. The `includesCalendarWeek` path needs a separate numeric week column; its regex does not match `W40` inside `2012-W40`. |

- **Options:**
  1. Add ISO-week-string parsing (`YYYY-Www`) to `csv-time` before the evaluation. It is a small change and
     consistent with the grammar's `weekBased` periods, but it changes the system under test.
  2. Use E2/E3-C (WHO FluNet, another country), which has numeric `ISO_YEAR`/`ISO_WEEK` columns.
  3. Accept that time-i-gram fails this input, and report it.

  This is your call. The data itself is the cleanest candidate found.

#### E2/E3-B. RKI lab-confirmed influenza cases (IfSG) (✅)

- **URL:** `https://raw.githubusercontent.com/robert-koch-institut/Influenzafaelle_in_Deutschland/824a3772411ca4800bd4375309862b94eab348b0/IfSG_Influenzafaelle.tsv`
- **License and citation:** CC BY 4.0 (same RKI wording as above). Robert Koch-Institut (2026).
  *Laborbestätigte Influenzafälle in Deutschland*. https://doi.org/10.5281/zenodo.23756965
- **Columns:**
  - `Meldewoche` (`YYYY-Www`, the same blocker as A)
  - `Region` (`Deutschland` plus 16 states)
  - `Region_Id`
  - `Altersgruppe` (`00+, 00-14, 15-59, 60+, Unbekannt`)
  - `Fallzahl`
  - `Inzidenz` (520 `NA`, for `Unbekannt`)
- **Encoding:** UTF-8 **with BOM**. In D3 the first header becomes `﻿Meldewoche`.
- **Sample rows:**
  ```
  Meldewoche	Region	Region_Id	Altersgruppe	Fallzahl	Inzidenz
  2020-W01	Deutschland	00	00+	1536	1.83
  2020-W01	Deutschland	00	00-14	384	3.29
  2022-W50	Deutschland	00	00+	57481	68.65
  2022-W51	Deutschland	00	00+	51719	61.76
  2023-W01	Deutschland	00	00+	14118	16.86
  ```
- **Size and range:** 18,788 rows, 0.7 MB, covering 2020-W01 to 2026-W43 (356 national weeks, no gaps).
  `Fallzahl` is never 0, so weeks with zero cases are absent rows in the regional series.
- **Peaks:**

  | Season | Peak week |
  |---|---|
  | 2019/20 (partial) | 2020-W10 |
  | 2020/21 | no season (maximum 36 cases) |
  | 2021/22 | 2022-W19 |
  | 2022/23 | 2022-W50 |
  | 2023/24 | 2024-W06 |
  | 2024/25 | 2025-W05 |
  | 2025/26 | 2026-W05 |

- **Why it is second:** the pathogen-specific story is the most dramatic one (the December 2022 peak against
  February elsewhere, and a missing season). But the span is only 6.8 years, one of them empty, and it has
  the same parsing blocker.

#### E2/E3-C. WHO FluNet, a non-US northern-hemisphere country such as `DEU` (📄 docs only)

- **Landing page:** https://www.who.int/toolkits/flunet. Full CSV: `https://xmart-api-public.who.int/FLUMART/VIW_FNT?$format=csv`.
  Data dictionary: `VIW_FLU_METADATA`.
- **Not downloaded:** the full CSV failed through the web reader, and the host is blocked from the shell.
- **Columns (from the dictionary):** `ISO_WEEKSTARTDATE` (date), `ISO_YEAR` (int), `ISO_WEEK` (int), `MMWR_*`,
  `COUNTRY_CODE`, `ORIGIN_SOURCE` (`SENTINEL`/`NONSENTINEL`/`NOTDEFINED`), `SPEC_PROCESSED_NB`,
  `INF_A`, `INF_B`, `INF_ALL`, …, 53 columns in total.
- **License:** the FluNet page states none and links to WHO's data policy. data.who.int says its datasets are
  CC BY 4.0 with additional WHO terms. Whether that covers the xMart FluNet export is **unconfirmed**.
- **Issues:**
  - A country has several rows per week (one per `ORIGIN_SOURCE`), so the spec must filter or sum.
  - A single-country file needs an OData `$filter` URL.
  - It is the same table and schema as the repo's `who_flu_usa.csv`, so the agents have effectively seen the
    format (held-out in data, not in structure).
- **Pattern (expected, not checked):** the same December-vs-February shift as RKI for European countries.

### E4: "Do trajectories look alike once aligned to their own event?"

#### E4-A. Ubuntu release history (✅ recommended)

- **Publisher:** `distro-info-data`, maintained by Debian and Ubuntu developers (B. Drung, S. Rivera), and used by
  Ubuntu's own `ubuntu-distro-info` tool. Home: https://salsa.debian.org/debian/distro-info-data.
  The verified copy is `/usr/share/distro-info/ubuntu.csv` from Ubuntu package `distro-info-data
  2026.10.12-0ubuntu0.24.04.1`. sha256 starts `4d885d8ebe21b268`.
- **URL:** salsa raw file at a pinned tag. The host is unreachable from here, so confirm the tag name and check
  the file against the sha256 above.
- **License:** ISC: "Permission to use, copy, modify, and/or distribute this software for any purpose with or
  without fee is hereby granted…".
- **Citation:** Drung, B., Rivera, S. et al. *distro-info-data* (ubuntu.csv), Debian, version 2026.10.12.
  This is a software-package citation, not an agency or DOI citation; that is the weak point.
- **Columns:**
  - `version` (`24.04 LTS`, and so on)
  - `codename`, `series`
  - `created`, `release`, `eol` (ISO dates, always present)
  - `eol-server` (11 rows), `eol-esm` (8 rows), `eol-legacy` (7 rows)
- **Sample rows:**
  ```
  version,codename,series,created,release,eol,eol-server,eol-esm,eol-legacy
  20.04 LTS,Focal Fossa,focal,2019-10-17,2020-04-23,2025-05-29,2025-05-29,2030-04-23,2035-04-26
  20.10,Groovy Gorilla,groovy,2020-04-23,2020-10-22,2021-07-22
  21.04,Hirsute Hippo,hirsute,2020-10-22,2021-04-22,2022-01-20
  21.10,Impish Indri,impish,2021-04-22,2021-10-14,2022-07-14
  22.04 LTS,Jammy Jellyfish,jammy,2021-10-14,2022-04-21,2027-06-01,2027-06-01,2032-04-21,2037-04-30
  ```
- **Size and range:** 46 rows, 3,165 bytes, covering 4.10 (2004) to 27.04 (planned release 2027-04-22).
  Several end dates are in the future.
- **Missing values:** encoded as **absent trailing fields** (ragged rows with 6, 7, 8 or 9 fields). d3-dsv
  returns `""` for these (tested), and Vega parses them to `null` (tested). time-i-gram's parser gets `""` and
  returns NaN with a one-time warning, so the row is kept. readr fills NA with a parsing warning.
- **Preprocessing:** none.
- **Structure for E4:**
  - Events: `created`, `release`.
  - Intervals: development (`created`→`release`), standard support (`release`→`eol`), extended support for
    LTS releases.
  - Align on: `release`.
- **Pattern:** aligned on release, the 35 interim releases end after a median of 9.2 months, while the
  11 LTS releases run a median of 60 months (plus ESM to +10 years). Development cycles are uniform at about
  6 months (median 182 days interim, 189 LTS).

#### E4-B. Debian release history (`debian.csv`, same package) (✅)

- **Contents:** 22 releases, Debian 1.1 "Buzz" (1996) to planned future releases.
- **Columns:** `version`, `codename`, `series`, `created`, `release`, `eol`, `eol-lts`, `eol-elts`.
- **Format:** ragged rows (4–8 fields); future releases have no release date.
- **Comparison with A:** irregular release cadence, so less striking, but usable as a second-domain check.

#### E4-C. Wikidata, US presidents since 1901 (📄 query drafted, not executed)

The Wikidata query service is blocked from this sandbox. Draft query (CC0 data; pin it by saving the query
URL and the export date):

```sparql
SELECT ?person ?personLabel ?what ?start ?end WHERE {
  ?person p:P39 ?pres . ?pres ps:P39 wd:Q11696 ; pq:P580 ?presStart .
  FILTER(?presStart >= "1901-01-01T00:00:00Z"^^xsd:dateTime)
  { ?person p:P39 ?st . ?st ps:P39 ?pos ; pq:P580 ?start . OPTIONAL { ?st pq:P582 ?end }
    ?pos rdfs:label ?what . FILTER(LANG(?what) = "en") }
  UNION { ?person wdt:P569 ?start . BIND("birth" AS ?what) }
  UNION { ?person wdt:P570 ?start . BIND("death" AS ?what) }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

- **Expected:** about 21 people; intervals for positions held (governor, senator, vice president,
  president); events for birth and death; align on the first presidency start.
- **Risks:**
  - Long position lists (for example one "member of the House" statement per term).
  - Inconsistent qualifiers.
  - Day-precision dates are exported as `…T00:00:00Z`.
- **Status:** run and check it before choosing it.

### E5: "Overview of several years, detail down to minutes"

#### E5-A. GeoSphere Austria `klima-v2-10min`, Wien Hohe Warte, `tl` + `rr`, 2020–2024 (📄 recommended, re-check)

- **Publisher:** GeoSphere Austria (formerly ZAMG).
- **Landing page:** https://data.hub.geosphere.at/en/dataset/klima-v2-10min.
- **DOI:** https://doi.org/10.60669/8fya-7x87
- **License:** the data hub lists "Creative Commons Attribution 4.0 International". The API docs state that
  "All data that requires no authentication is licensed under the Creative Commons Attribution 4.0".
- **Coverage:** 10-minute, quality-controlled data from 1992 to the present, for about 260 stations.
- **API limits:** 1,000,000 values per CSV request (`JSON_LIMIT` in `Geosphere-Austria/dataset-api-docs`
  `src/conf.py`), 5 requests/s and 240 requests/h.
- **Request:** 2020-01-01T00:00 to 2024-12-31T23:50 is 1,827 days × 144 = 263,088 time steps. With 2
  parameters that is 526,176 values, so one request is enough.
- **Expected columns:** `time,station,tl,rr`. The time format seen in the repo's existing GeoSphere CSV from the
  same API is `2022-01-01T00:00+00:00`, which all four tools parse (time-i-gram keeps the explicit zone).
  Missing values appear as empty fields in that file.
- **To confirm before use:**
  1. that station id 105 is Wien Hohe Warte in `klima-v2-*`. This comes from a third-party page; check
     `/v1/station/historical/klima-v2-10min/metadata`.
  2. the row count and file size.
  3. that the response is a plain CSV with no comment lines.
  4. that the URL is stable. It is an API URL, so save one response's sha256.
- **Pattern (expected, not checked against the data):** the overview should show the annual temperature cycle
  and the summer heat waves. Zooming in should show the diurnal cycle and individual thunderstorm bursts in `rr`
  at 10-minute resolution.
- **Caveat:** the solar example in this repo uses the same publisher and API, so the format is familiar to the agents.

#### E5-B. Environment Agency Hydrology API, 15-minute river flow or level (📄)

- **Publisher:** Environment Agency (England).
- **Landing page:** https://environment.data.gov.uk/hydrology. About 7,000 stations, mainly 15-minute data,
  with CSV output.
- **License:** Open Government Licence v3.0.
- **Size:** 10 years at 15 minutes is about 350,000 rows for one measure.
- **Not checked:** the CSV columns (expected `dateTime`, `value`, `quality`, `completeness`), the per-request
  limit, and which measure to use.
- **Why consider it:** a different domain from E1–E4 and from the repo's existing data. Storm hydrographs
  make the minutes-level zoom meaningful.

#### E5-C. Open Power System Data, `time_series_15min_singleindex.csv` (📄)

- **Versioning:** DOI 10.25832/time_series/2020-10-06.
- **Contents:** 15-minute data from 2015 to mid-2020, in a wide layout of 61 columns (load, solar and wind for
  AT, BE, DE (+TSOs), HU, LU, NL). ISO UTC timestamps in `utc_timestamp`.
- **License:** the README gives an attribution format but **no explicit data license** (data comes from mixed
  sources such as ENTSO-E and TSOs).
- **Fit:** good for E5 on a single column, but the license is not clear enough.

### E6 (optional): one spiral turn per year

- **Recommended:** reuse E2 (RKI ARE, national, `00+`). 14 turns, a strong cycle, and the week-52 dip makes a
  visible notch on every turn. It has the same parsing blocker as E2/E3.
- **Alternative:** E1's ocean temperature filtered to 10 m. Daily, 2,847 days with no gaps, peak around Sep
  (about 15.5 °C), minimum in Feb–Mar (about 2.3 °C), ISO dates. This option avoids the blocker.

---

## 3. Considered and rejected

- **ECDC ERVISS** (`EU-ECDC/Respiratory_viruses_weekly_data`, ✅): starts 2022-W25 (under 5 years), uses `YYYY-Www` strings, and is licensed EUPL-1.2.
- **RKI GrippeWeb** (✅): 2011-W22 to 2026-W43, CC BY 4.0. It is participatory self-reports, so it is less standard than ARE, and has the same week-string issue. It is a fallback for E2.
- **RKI AMELAG wastewater** (✅): weekly rather than daily, and influenza is only reported from 2023-11.
- **RKI SARI hospitalisation incidence** (✅ header only): the same week-string format and a shorter series than ARE.
- **TidyTuesday Himalayan expeditions** (✅): contains cp1252 bytes that are invalid UTF-8; 54% of `BCDATE` and 62% of `TERMDATE` are missing; the Himalayan Database license is unclear.
- **TidyTuesday US federal judges (FJC)** (✅): dates are `MM/DD/YYYY`, and the copy is frozen at 2014 (the live FJC export also uses `mm/dd/yyyy`).
- **Node.js release schedule** (`nodejs/Release` `schedule.json`): a nested JSON object keyed by version, not a flat array.
- **TidyTuesday Roman emperors:** BCE dates (negative years) break the parsers, and the data comes from Wikipedia.
- **TidyTuesday A64 traffic, 15-minute** (✅): only one month (May 2021).
- **TidyTuesday Hornborgasjön cranes** (✅): irregular counts limited to the spring and autumn seasons, and the source (hornborga.com) license is unclear.
- **UCI household power consumption:** semicolon-separated, `?` for missing values, `dd/mm/yyyy`, zipped, and 127 MB.
- **Jena climate, 10-minute:** dates are `dd.mm.yyyy HH:MM:SS`, and the license is unclear.
- **ETTm1/ETTm2:** licensed CC BY-ND 4.0, only 69,680 rows, and the columns are anonymised.
- **OPSD household data:** cumulative kWh counters that need differencing.
- **MeteoSwiss OGD 10-minute:** semicolon-separated with `dd.mm.yyyy HH:MM` timestamps.
- **DWD 10-minute:** zipped, with `yyyymmddHHMM` timestamps.
- **Swiss FOPH `INFLUENZA_oblig`:** the download was blocked, the format is unknown, and the opendata.swiss page shows no license.
- **UKHSA dashboard API:** paginated, and could not be checked here.
- **Sentinelles (France):** has a leading comment line and `yyyyww` weeks.
- **CDC FluView/NREVSS:** uses MMWR weeks, not ISO, and the US is already used.
- **Google COVID-19 Community Mobility:** wide format, under 3 years, and a very large file.
- **MTA daily ridership (data.ny.gov):** could not be checked here, and it is NYC data next to the excluded taxi set.
- **Munich bike counters:** one CSV per month, so it would need concatenating.
- **Montréal bike counters:** wide format, one column per counter.
- **datahub `exchange-rates` daily:** more than 20 countries, too many categories.
