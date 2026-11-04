# Calendar heatmap of weekly ARE consultation incidence in Germany (RKI ARE-Praxis-Sentinel)
# One row per ISO year, one cell per ISO week. Built with ggtime::coord_calendar().
suppressPackageStartupMessages({
  library(ggtime)
  library(ggplot2)
  library(dplyr)
  library(readr)
  library(tidyr)
})

url <- paste0(
  "https://raw.githubusercontent.com/robert-koch-institut/ARE-Konsultationsinzidenz/",
  "65ac2d278c06333808415795d65f0347c54be638/ARE-Konsultationsinzidenz.tsv"
)
raw <- read_tsv(url, show_col_types = FALSE,
                col_types = cols(.default = col_character()))

# Monday of ISO week 1 of a given ISO year (week 1 contains 4 January)
iso_week1_monday <- function(y) {
  jan4 <- as.Date(sprintf("%d-01-04", y))
  jan4 - (as.integer(format(jan4, "%u")) - 1L)
}

are <- raw |>
  filter(Bundesland == "Bundesweit", Altersgruppe == "00+") |>
  transmute(
    iso_year = as.integer(substr(Kalenderwoche, 1, 4)),
    iso_week = as.integer(substr(Kalenderwoche, 7, 8)),
    inc      = as.numeric(ARE_Konsultationsinzidenz)
  ) |>
  mutate(monday = iso_week1_monday(iso_year) + 7L * (iso_week - 1L))
stopifnot(all(format(are$monday, "%G-W%V") ==
                sprintf("%d-W%02d", are$iso_year, are$iso_week)))

# Pad to complete ISO years so every row starts at week 1; padded weeks get NA
# (drawn transparent = empty, not zero).
all_mondays <- seq(iso_week1_monday(min(are$iso_year)),
                   iso_week1_monday(max(are$iso_year) + 1L) - 7L, by = "week")
cal <- tibble(monday = all_mondays) |>
  left_join(are |> select(monday, inc), by = "monday") |>
  mutate(Time = monday + 3.5)   # tile centre: Monday 00:00 + 3.5 days

# Caption: computed from the data
yr <- are |>
  group_by(iso_year) |>
  summarise(n = n(),
            peak_week = iso_week[which.max(inc)],
            early = mean(inc[iso_week <= 10]),
            .groups = "drop")
full_years <- filter(yr, n >= 52)
winter <- function(w) w >= 40 | w <= 12
n_winter <- sum(winter(full_years$peak_week))
no_wave  <- full_years$iso_year[which.min(full_years$early)]
top      <- are[which.max(are$inc), ]
caption_txt <- sprintf(paste0(
  "Main pattern: every year repeats a winter-high / summer-low cycle (the peak of %d of %d complete ISO years ",
  "falls in weeks 40–12), but timing and strength vary: the early-year wave is missing in %d, ",
  "and the highest value (%s) is in week %d of %d."),
  n_winter, nrow(full_years), no_wave,
  format(top$inc, big.mark = ","), top$iso_week, top$iso_year)
source_txt <- paste0(
  "Data: Robert Koch-Institut, ARE-Praxis-Sentinel, ARE-Konsultationsinzidenz (CC BY 4.0); ",
  "Germany (Bundesweit), all ages (00+). Empty cells: weeks not covered by the data.")

iw <- mixtime::cal_isoweek

p <- ggplot(cal, aes(x = Time, y = 1, fill = inc)) +
  geom_tile(width = 7, height = 1, colour = "white", linewidth = 0.2) +
  coord_calendar(
    cells = iw$week(1L), rows = iw$year(1L),
    panes = NULL, cols = NULL,
    label_cells = NULL, label_panes = NULL,
    label_rows = "{lin(mixtime::cal_isoweek$year)}",
    clip = "off"
  ) +
  # breaks: ISO weeks of the reference row, labelled by position in the row (1..53)
  scale_x_mixtime(time_breaks = iw$week(1L),
                  labels = function(x) seq_along(x)) +
  scale_fill_viridis_c(
    option = "viridis", na.value = NA,
    labels = scales::label_comma(),
    name = "ARE consultations\nper 100,000\npopulation per week",
    guide = guide_colourbar(barheight = unit(12, "lines"))
  ) +
  labs(
    title = "Acute respiratory illness in Germany: does every year follow the same cycle?",
    subtitle = "Weekly ARE consultation incidence, one row per ISO year (top = earliest), one cell per ISO week",
    x = "ISO week", y = NULL,
    caption = paste(strwrap(caption_txt, 190), collapse = "\n") |> paste(source_txt, sep = "\n")
  ) +
  theme_minimal(base_size = 13) +
  theme(
    axis.text.y = element_blank(), axis.ticks.y = element_blank(),
    axis.text.x = element_text(size = 9),
    ggtime.calendar.row.text = element_text(hjust = -0.035, vjust = 0.5, size = 11),
    ggtime.calendar.cell.line = element_blank(),
    ggtime.calendar.row.line = element_blank(),
    panel.background = element_rect(fill = "grey97", colour = NA),
    plot.title = element_text(face = "bold"),
    plot.caption = element_text(hjust = 0, size = 11),
    plot.caption.position = "plot",
    plot.title.position = "plot",
    plot.margin = margin(10, 10, 10, 50)
  )

ggsave("plot.png", p, width = 14, height = 9, dpi = 100, bg = "white")
ggsave("plot.svg", p, width = 14, height = 9, bg = "white")
