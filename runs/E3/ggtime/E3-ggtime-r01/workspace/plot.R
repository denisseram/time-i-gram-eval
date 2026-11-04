# E3: Does the ARE peak happen at the same time each year? (RKI ARE-Praxis-Sentinel)
suppressPackageStartupMessages({
  library(ggplot2); library(ggtime); library(dplyr); library(readr)
  library(tsibble); library(lubridate); library(scales); library(patchwork)
})

url <- "https://raw.githubusercontent.com/robert-koch-institut/ARE-Konsultationsinzidenz/65ac2d278c06333808415795d65f0347c54be638/ARE-Konsultationsinzidenz.tsv"
raw <- read_tsv(url, show_col_types = FALSE,
                col_types = cols(.default = col_character(),
                                 Bundesland_ID = col_integer(),
                                 ARE_Konsultationsinzidenz = col_double()))

d <- raw |>
  filter(Bundesland == "Bundesweit", Altersgruppe == "00+") |>
  mutate(yw    = tsibble::yearweek(Kalenderwoche),          # ISO 8601 week
         date  = as.Date(yw),                               # Monday of the ISO week
         t     = mixtime::yearweek(yw),                     # mixtime index for ggtime
         isoyr = as.integer(substr(Kalenderwoche, 1, 4)),
         isowk = as.integer(substr(Kalenderwoche, 7, 8)),
         value = ARE_Konsultationsinzidenz) |>
  arrange(date)

# ---- Peak week per season (computed) ---------------------------------------
peaks <- d |> group_by(Saison) |> slice_max(value, n = 1, with_ties = FALSE) |>
  ungroup() |> mutate(lab = sprintf("%s\nW%02d", Saison, isowk))

# ---- "Brush": the selected time range in the linear view -------------------
# Static stand-in for an interactive brush. Default: the most recent complete
# season (week 40 .. week 39), derived from the data.
season_n <- d |> count(Saison)
sel_season <- max(season_n$Saison[season_n$n >= 52])
sel <- d |> filter(Saison == sel_season)
sel_start <- min(sel$date); sel_end <- max(sel$date) + 6
d <- d |> mutate(selected = date >= sel_start & date <= sel_end)

# ---- Caption computed from the data -----------------------------------------
pk_full <- peaks |> filter(Saison %in% season_n$Saison[season_n$n >= 52])
pre  <- pk_full |> filter(date <  as.Date("2020-03-01"))
post <- pk_full |> filter(date >= as.Date("2020-03-01"))
caption_txt <- sprintf(
  "No: up to %s the peak fell every season in a narrow window (ISO weeks %d-%d, Feb-Mar), but since the COVID-19 pandemic its timing has scattered (peak weeks by season: %s).",
  max(pre$Saison), min(pre$isowk), max(pre$isowk),
  paste(sprintf("W%02d", post$isowk), collapse = ", "))

yr_lim <- range(d$isoyr)
col_scale <- scale_colour_viridis_c(name = "ISO year", option = "turbo",
                                    limits = yr_lim, breaks = seq(yr_lim[1], yr_lim[2], 2),
                                    guide = guide_colourbar(title.vjust = 0.8))
unit_lab <- "ARE consultations per 100,000 per week"

# ---- Circular view ----------------------------------------------------------

p_circ <- ggplot(d, aes(t, value, colour = isoyr, group = 1)) +
  geom_line(aes(alpha = selected, linewidth = selected)) +
  geom_point(data = peaks, aes(t, value), shape = 21, fill = "white",
             size = 2.6, stroke = 1.2, inherit.aes = FALSE,
             colour = "black") +
  geom_point(data = peaks, aes(t, value, colour = isoyr), size = 1.4,
             inherit.aes = FALSE) +
  scale_alpha_manual(values = c(`FALSE` = 0.18, `TRUE` = 1), guide = "none") +
  scale_linewidth_manual(values = c(`FALSE` = 0.4, `TRUE` = 1.3), guide = "none") +
  scale_x_mixtime(name = "ISO week", time_breaks = mixtime::weeks(4L),
                  labels = function(x) sub("^.*(W[0-9]+).*$", "\\1", format(x))) +
  scale_y_continuous(name = unit_lab, limits = c(0, max(d$value)), breaks = breaks_pretty(4),
                     labels = label_comma()) +
  col_scale +
  coord_loop(time_loops = mixtime::years(1L), coord = coord_radial(expand = FALSE)) +
  labs(subtitle = sprintf("Cyclic view: one turn per ISO year, week 1 at top, clockwise.\nHighlighted: selected range (season %s); ○ = peak week of each season",
                          sel_season)) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "bottom", plot.subtitle = element_text(size = 10.5),
        axis.text.x = element_text(size = 10),
        legend.key.width = unit(4, "lines"), legend.key.height = unit(0.6, "lines"))

# ---- Linear view ------------------------------------------------------------
p_lin <- ggplot(d, aes(date, value)) +
  annotate("rect", xmin = sel_start, xmax = sel_end, ymin = -Inf, ymax = Inf,
           fill = "grey50", alpha = 0.2) +
  annotate("text", x = sel_end, y = Inf, vjust = 1.3, hjust = 1,
           label = paste("selected:", sel_season), size = 3.4) +
  geom_line(aes(colour = isoyr, group = 1), linewidth = 0.5) +
  geom_point(data = peaks, aes(colour = isoyr), shape = 21, fill = "white",
             size = 2.6, stroke = 1.2, colour = "black") +
  geom_text(data = peaks, aes(label = sprintf("W%02d", isowk)),
            vjust = -1, size = 3) +
  scale_x_date(name = "Date (ISO week start)", date_breaks = "1 year",
               date_labels = "%Y", expand = expansion(mult = c(0.01, 0.025))) +
  scale_y_continuous(name = unit_lab, labels = label_comma(),
                     expand = expansion(mult = c(0.02, 0.12))) +
  col_scale + guides(colour = "none") +
  labs(subtitle = "Linear view, 2012-2026. Shaded band = selected time range, highlighted in the cyclic view.\n○ with label = peak ISO week of each season (W40-W39)") +
  theme_minimal(base_size = 12) +
  theme(plot.subtitle = element_text(size = 10.5), panel.grid.minor = element_blank())

fig <- (p_circ | p_lin) + plot_layout(widths = c(1, 1.3)) +
  plot_annotation(
    title = "Does acute respiratory illness in Germany peak at the same time every year?",
    caption = paste0(paste(strwrap(caption_txt, 230), collapse = "\n"),
                     "\nData: Robert Koch-Institut, ARE-Praxis-Sentinel (ARE-Konsultationsinzidenz), Bundesweit, all ages; CC BY 4.0."),
    theme = theme(plot.title = element_text(size = 17, face = "bold"),
                  plot.caption = element_text(size = 11, hjust = 0)))

ggsave("plot.png", fig, width = 1400, height = 900, units = "px", dpi = 100, bg = "white")
ggsave("plot.svg", fig, width = 14, height = 9, bg = "white")
