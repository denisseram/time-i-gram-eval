# ARE consultation incidence in Germany: one calendar row per ISO year, one cell per ISO week.
suppressPackageStartupMessages({
  library(readr); library(dplyr); library(ggplot2); library(mixtime); library(ggtime)
})

url <- "https://raw.githubusercontent.com/robert-koch-institut/ARE-Konsultationsinzidenz/65ac2d278c06333808415795d65f0347c54be638/ARE-Konsultationsinzidenz.tsv"
raw <- read_tsv(url, show_col_types = FALSE)

are <- raw |>
  filter(Bundesland == "Bundesweit", Altersgruppe == "00+") |>
  mutate(iso_year = as.integer(substr(Kalenderwoche, 1, 4)),
         iso_week = as.integer(substr(Kalenderwoche, 7, 8))) |>
  arrange(Kalenderwoche)

# Pad the first ISO year from week 1 up to the first reported week with empty (NA) cells,
# so every calendar row starts at week 1 and the year label sits at the left edge.
first_year <- min(are$iso_year)
first_week <- min(are$iso_week[are$iso_year == first_year])
pad <- if (first_week > 1) {
  tibble(Kalenderwoche = sprintf("%d-W%02d", first_year, seq_len(first_week - 1)),
         ARE_Konsultationsinzidenz = NA_real_)
} else NULL
plot_data <- bind_rows(select(are, Kalenderwoche, ARE_Konsultationsinzidenz), pad) |>
  mutate(week = yearweek(Kalenderwoche))

# ---- caption, computed from the data -------------------------------------------------------
peaks <- are |>
  group_by(iso_year) |>
  filter(n() >= 52) |>                       # complete ISO years only
  summarise(peak_week = iso_week[which.max(ARE_Konsultationsinzidenz)],
            q1_mean   = mean(ARE_Konsultationsinzidenz[iso_week <= 13]))
winter <- filter(peaks, peak_week <= 13)
late   <- filter(peaks, peak_week > 13)
no_wave <- peaks$iso_year[which.min(peaks$q1_mean)]
caption <- sprintf(paste0(
  "Most years share one cycle, a late-winter peak (weeks %d–%d in %d of %d complete years) and a summer low, ",
  "but not all: %d had no winter wave, and %s peaked in weeks %d–%d instead."),
  min(winter$peak_week), max(winter$peak_week), nrow(winter), nrow(peaks),
  no_wave, paste(late$iso_year, collapse = ", "), min(late$peak_week), max(late$peak_week))

# ---- calendar coordinate -------------------------------------------------------------------
cal <- coord_calendar(cells = week(1L), rows = year(1L), panes = NULL, cols = NULL,
                      label_cells = NULL, label_rows = "{lin(year)}", label_panes = NULL,
                      clip = "off")
# Workaround for ggtime 1.1.0: coord_calendar() always evaluates its default `panes = month(1L)`,
# which fails for ISO-week (cal_isoweek) time axes that have no month granule.
# Re-declare the granule specs without that default.
assign("granule_specs", envir = cal, function(self) list(
  cells = list(quo = self$cells_quo), rows = list(quo = self$rows_quo),
  blocks = list(quo = self$blocks_quo), panes = list(quo = self$panes_quo),
  cols = list(quo = self$cols_quo)))

# Axis labels: week number within the ISO year (breaks are consecutive weeks from week 1
# of the first row, so weeks 52 and 53 are labelled correctly).
week_labels <- function(x) {
  n <- as.numeric(x)
  start <- as.integer(sub(".*W(\\d+).*", "\\1", format(x[1])))
  lab <- as.character(start + round(n - n[1]))
  lab[is.na(n)] <- ""
  lab
}

p <- ggplot(plot_data, aes(x = week, y = 0, fill = ARE_Konsultationsinzidenz)) +
  geom_tile(colour = "white", linewidth = 0.3) +
  cal +
  scale_x_mixtime(time_breaks = weeks(1L), labels = week_labels) +
  scale_fill_viridis_c(option = "magma", direction = -1, na.value = NA,
                       name = "ARE consultations\nper 100,000\nper week",
                       labels = scales::label_comma()) +
  labs(title = "Acute respiratory illness in Germany: does every year follow the same cycle?",
       subtitle = "Weekly ARE consultation incidence, all ages, Germany (ARE-Praxis-Sentinel); one row per ISO year, one cell per ISO week",
       x = "ISO week", y = "ISO year",
       caption = paste0(caption, "\nData: Robert Koch-Institut, ARE-Konsultationsinzidenz (CC BY 4.0). Blank cells: no data reported.")) +
  theme_minimal(base_size = 13) +
  theme(axis.text.y = element_blank(), axis.ticks.y = element_blank(),
        axis.title.y = element_text(margin = margin(r = 48)),
        axis.text.x = element_text(size = 8),
        ggtime.calendar.row.text = element_text(hjust = 0, vjust = 0.5, size = 11,
                                                margin = margin(l = -38)),
        ggtime.calendar.cell.line = element_blank(),
        plot.title = element_text(face = "bold"),
        plot.caption = element_text(hjust = 0, size = 11),
        plot.caption.position = "plot", plot.title.position = "plot",
        plot.margin = margin(10, 10, 10, 10))

ggsave("plot.png", p, width = 14, height = 9, dpi = 100, bg = "white")
ggsave("plot.svg", p, width = 14, height = 9, bg = "white")
