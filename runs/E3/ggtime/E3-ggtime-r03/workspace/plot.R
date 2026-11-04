suppressPackageStartupMessages({
  library(readr); library(dplyr); library(ggplot2); library(ggtime)
  library(mixtime); library(patchwork); library(scales)
})

url <- "https://raw.githubusercontent.com/robert-koch-institut/ARE-Konsultationsinzidenz/65ac2d278c06333808415795d65f0347c54be638/ARE-Konsultationsinzidenz.tsv"
raw <- read_tsv(url, show_col_types = FALSE)

d <- raw |>
  filter(Bundesland == "Bundesweit", Altersgruppe == "00+") |>
  mutate(
    iso_year = as.integer(substr(Kalenderwoche, 1, 4)),
    iso_week = as.integer(substr(Kalenderwoche, 7, 8)),
    jan4 = as.Date(paste0(iso_year, "-01-04")),
    monday = jan4 - (as.integer(format(jan4, "%u")) - 1L) + 7L * (iso_week - 1L),
    wk = yearweek(monday),
    value = ARE_Konsultationsinzidenz,
    year_f = factor(iso_year)
  ) |>
  arrange(monday)

# Complete seasons only (a season is W40..W39, >= 52 weeks)
season_n <- count(d, Saison)
complete <- season_n$Saison[season_n$n >= 52]

peaks <- d |>
  filter(Saison %in% complete) |>
  group_by(Saison) |>
  slice_max(value, n = 1, with_ties = FALSE) |>
  ungroup() |>
  mutate(lab = paste0(Saison, ": W", sprintf("%02d", iso_week)))

# Static "brush": the selected range = the last three complete seasons
sel_seasons <- tail(sort(complete), 3)
sel <- d |> filter(Saison %in% sel_seasons) |>
  summarise(start = min(monday), end = max(monday))
d <- d |> mutate(selected = monday >= sel$start & monday <= sel$end)
peaks <- peaks |> mutate(selected = monday >= sel$start & monday <= sel$end)
sel_rect <- data.frame(xmin = yearweek(sel$start), xmax = yearweek(sel$end))

years_pal <- scale_colour_viridis_d(option = "turbo", begin = 0.05, end = 0.95,
                                    name = "ISO year", drop = FALSE)
unit_lab <- "ARE consultations per 100,000 per week"

# week-number breaks around the circle (placed in the first loop = first ISO year)
ref_year <- min(d$iso_year)
circ_wks <- c(1, seq(5, 49, by = 4))
circ_breaks <- yearweek(as.Date(paste0(ref_year, "-01-04")) -
  (as.integer(format(as.Date(paste0(ref_year, "-01-04")), "%u")) - 1L) + 7L * (circ_wks - 1L))

# ---- Circular view ----------------------------------------------------------
p_circ <- ggplot(d, aes(wk, value, colour = year_f, group = iso_year)) +
  geom_line(aes(alpha = selected), linewidth = 0.6) +
  geom_point(data = peaks, aes(alpha = selected), shape = 21, fill = "white",
             size = 2.8, stroke = 1.3, show.legend = FALSE) +
  scale_alpha_manual(values = c(`TRUE` = 1, `FALSE` = 0.18), guide = "none") +
  years_pal +
  scale_x_mixtime(breaks = circ_breaks, labels = sprintf("W%02d", circ_wks), name = NULL) +
  scale_y_continuous(labels = label_comma(), name = unit_lab) +
  coord_loop(time_loops = years(1L), coord = coord_radial(expand = FALSE)) +
  labs(subtitle = "Cyclic view: one ring per ISO year (W01 at top, clockwise).\nCircles = peak week of each season; full colour = selected range") +
  theme_minimal(base_size = 12) +
  theme(legend.position = "right", legend.key.height = unit(0.9, "lines"))

# ---- Linear view ------------------------------------------------------------
p_lin <- ggplot(d, aes(wk, value)) +
  geom_rect(data = sel_rect, aes(xmin = xmin, xmax = xmax, ymin = -Inf, ymax = Inf),
            inherit.aes = FALSE, fill = "grey60", alpha = 0.25) +
  geom_line(aes(colour = year_f, group = 1, alpha = selected), linewidth = 0.5) +
  geom_point(data = peaks, aes(colour = year_f, alpha = selected), shape = 21,
             fill = "white", size = 2.2, stroke = 1.1) +
  geom_text(data = peaks, aes(label = lab, alpha = selected), vjust = -1,
            size = 2.8, colour = "grey20", check_overlap = TRUE) +
  annotate("label", x = sel_rect$xmax, y = Inf, vjust = 1.2, hjust = 1.02, size = 3.2,
           label = paste0("Selected range: ", format(sel$start, "%d %b %Y"), " – ",
                          format(sel$end, "%d %b %Y"))) +
  scale_alpha_manual(values = c(`TRUE` = 1, `FALSE` = 0.35), guide = "none") +
  years_pal + guides(colour = "none") +
  scale_x_mixtime(name = "Calendar time (ISO week)", time_breaks = years(1L)) +
  scale_y_continuous(labels = label_comma(), name = unit_lab,
                     expand = expansion(mult = c(0.02, 0.15))) +
  labs(subtitle = "Linear view: whole series; grey band = selected range highlighted in the circle") +
  theme_minimal(base_size = 12)

# ---- Caption computed from data ---------------------------------------------
start_yr <- as.integer(substr(peaks$Saison, 1, 4))
pre  <- peaks |> filter(start_yr < 2020)
post <- peaks |> filter(start_yr >= 2022)
cap <- sprintf(
  "No: before 2020 the season peak fell in ISO weeks %02d-%02d (Feb-Mar), but since 2022/23 it has jumped between December and February (%s), so the peak week shifts from year to year.",
  min(pre$iso_week), max(pre$iso_week),
  paste(sprintf("W%02d", post$iso_week), collapse = ", "))
cap <- paste0(cap, "\nData: Robert Koch-Institut, ARE-Praxis-Sentinel (CC BY 4.0), Germany, all ages. Static figure: the 'selection' is fixed to the last three complete seasons.")

fig <- (p_circ | p_lin) + plot_layout(widths = c(1, 1.35)) +
  plot_annotation(
    title = "Does the acute respiratory illness (ARE) peak in Germany fall in the same week every year?",
    caption = cap,
    theme = theme(plot.title = element_text(face = "bold", size = 16),
                  plot.caption = element_text(hjust = 0, size = 11))
  )

ggsave("plot.png", fig, width = 1400, height = 900, units = "px", dpi = 100, bg = "white")
ggsave("plot.svg", fig, width = 14, height = 9, bg = "white")
