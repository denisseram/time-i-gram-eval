---
name: ggtime
deliverable: plot.R
deliverable_kind: the R script
---
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
