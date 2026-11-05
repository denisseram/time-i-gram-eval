# ARE consultation incidence, Germany (RKI ARE-Praxis-Sentinel): one calendar row per ISO year.
suppressPackageStartupMessages({
  library(ggplot2); library(ggtime); library(mixtime)
  library(readr); library(dplyr)
})

url <- "https://raw.githubusercontent.com/robert-koch-institut/ARE-Konsultationsinzidenz/65ac2d278c06333808415795d65f0347c54be638/ARE-Konsultationsinzidenz.tsv"
raw <- read_tsv(url, col_types = cols(.default = col_character()), progress = FALSE)

are <- raw |>
  filter(Bundesland == "Bundesweit", Altersgruppe == "00+") |>
  mutate(
    inc      = as.integer(ARE_Konsultationsinzidenz),
    iso_year = as.integer(substr(Kalenderwoche, 1, 4)),
    iso_week = as.integer(substr(Kalenderwoche, 7, 8)),
    # Monday of an ISO week = Monday of the week containing 4 January + (week - 1) * 7 days
    jan4     = as.Date(sprintf("%d-01-04", iso_year)),
    monday   = jan4 - (as.integer(format(jan4, "%u")) - 1L) + (iso_week - 1L) * 7L,
    week     = yearweek(monday)          # mixtime ISO-week time point
  ) |>
  arrange(monday)

# Full ISO-year span of the data, so every row starts at week 1 (cells outside the data stay empty)
iso_monday <- function(y, w) {
  jan4 <- as.Date(sprintf("%d-01-04", y))
  jan4 - (as.integer(format(jan4, "%u")) - 1L) + (w - 1L) * 7L
}
span <- yearweek(c(iso_monday(min(are$iso_year), 1L),
                   iso_monday(max(are$iso_year) + 1L, 1L) - 7L))

caption <- paste0(
  "Main pattern: most years repeat the same cycle of a winter peak (Dec-Mar), a summer low and a dip in the Christmas week, ",
  "but 2020-2021 (COVID-19 measures) break it and 2022 adds a summer wave and an early-December surge.")
subtitle <- sprintf(paste0(
  "Weekly ARE consultation incidence, all ages, Germany, %s to %s. One row per ISO year, one cell per ISO week; ",
  "blank cells = no data or no week 53.\nData: Robert Koch-Institut, ARE-Praxis-Sentinel (CC BY 4.0)."),
  are$Kalenderwoche[1], are$Kalenderwoche[nrow(are)])

cal <- coord_calendar(
  cells = cal_isoweek$week(1L), rows = cal_isoweek$year(1L),
  panes = NULL, cols = NULL,
  label_cells = NULL, label_panes = NULL,
  label_rows = "{lin(year)}",
  clip = "off"
)
# Workaround: ggtime 1.1.0 always evaluates the default `panes = month(1L)`, even when
# `panes = NULL`, which fails for the ISO-week calendar (it has no month granule).
orig_specs <- cal$granule_specs
cal$granule_specs <- function(self) { s <- orig_specs(); s$panes$default <- NULL; s }

p <- ggplot(are, aes(x = week, y = 0, fill = inc)) +
  geom_tile(colour = "white", linewidth = 0.2) +
  cal +
  scale_x_mixtime(
    name = "ISO week",
    time_breaks = weeks(1L),
    limits = span,
    # breaks are the cell starts of the longest (53-week) row, so label them 1..n
    labels = function(x) as.character(seq_along(x))
  ) +
  scale_fill_viridis_c(
    option = "magma", direction = -1,
    name = "ARE consultations\nper 100,000\npopulation per week",
    labels = scales::label_comma(),
    guide = guide_colourbar(barheight = unit(14, "lines"))
  ) +
  labs(
    title = "Acute respiratory illness in Germany: does every ISO year follow the same cycle?",
    subtitle = subtitle,
    caption = paste(strwrap(caption, 165), collapse = "\n"),
    y = "ISO year"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    axis.text.y = element_blank(), axis.ticks.y = element_blank(),
    axis.text.x = element_text(size = 8),
    axis.title.y = element_text(margin = margin(r = 40)),
    ggtime.calendar.row.text = element_text(size = 10, hjust = 0, vjust = 0.5,
                                            margin = margin(l = -34)),
    ggtime.calendar.row.background = element_blank(),
    plot.title = element_text(face = "bold"),
    plot.caption = element_text(hjust = 0, size = 11, face = "italic"),
    plot.caption.position = "plot",
    plot.title.position = "plot"
  )

ggsave("plot.png", p, width = 1400, height = 900, units = "px", dpi = 110, bg = "white")
ggsave("plot.svg", p, width = 1400 / 110, height = 900 / 110, units = "in", bg = "white")
