# ARE consultation incidence, Germany (RKI ARE-Praxis-Sentinel, CC BY 4.0)
# Circular (ISO-year loop) view linked to a linear view of the full series.
suppressPackageStartupMessages({
  library(ggplot2); library(ggtime); library(mixtime)
  library(readr); library(dplyr); library(patchwork); library(scales)
})

url <- paste0("https://raw.githubusercontent.com/robert-koch-institut/ARE-Konsultationsinzidenz/",
              "65ac2d278c06333808415795d65f0347c54be638/ARE-Konsultationsinzidenz.tsv")
raw <- read_tsv(url, show_col_types = FALSE,
                col_types = cols(.default = col_character(), Bundesland_ID = col_integer(),
                                 ARE_Konsultationsinzidenz = col_integer()))

# ISO 8601 week "YYYY-Www" -> Monday of that week
iso_monday <- function(s) {
  y <- as.integer(substr(s, 1, 4)); w <- as.integer(substr(s, 7, 8))
  jan4 <- as.Date(paste0(y, "-01-04"))
  jan4 - (as.integer(format(jan4, "%u")) - 1L) + 7L * (w - 1L)
}

d <- raw |>
  filter(Bundesland == "Bundesweit", Altersgruppe == "00+") |>
  mutate(date = iso_monday(Kalenderwoche),
         wk = yearweek(date),
         iso_year = factor(as.integer(substr(Kalenderwoche, 1, 4))),
         value = ARE_Konsultationsinzidenz) |>
  arrange(date)

# R3: peak week per season (computed)
peaks <- d |> group_by(Saison) |> slice_max(value, n = 1, with_ties = FALSE) |> ungroup() |>
  mutate(lab = paste0(substr(Saison, 3, 4), "/", substr(Saison, 6, 7), "\n",
                      substr(Kalenderwoche, 6, 8)))

# R5: static "brush" = the three most recent complete seasons (>= 52 weeks reported)
complete <- d |> count(Saison) |> filter(n >= 52) |> pull(Saison) |> sort()
sel_seasons <- tail(complete, 3)
sel_from <- min(d$date[d$Saison %in% sel_seasons])
sel_to   <- max(d$date[d$Saison %in% sel_seasons])
d <- d |> mutate(selected = date >= sel_from & date <= sel_to)
peaks <- peaks |> mutate(selected = date >= sel_from & date <= sel_to)
brush <- data.frame(xmin = yearweek(sel_from), xmax = yearweek(sel_to))
sel_txt <- sprintf("Selection: %s to %s\n(seasons %s)",
                   format(sel_from, "%G-W%V"), format(sel_to, "%G-W%V"),
                   paste(sel_seasons, collapse = ", "))

n_years <- nlevels(d$iso_year)
year_cols <- setNames(viridis_pal(option = "C", end = 0.9)(n_years), levels(d$iso_year))
ylab <- "ARE consultations per 100,000 per week"

# ---- Circular view ---------------------------------------------------------
p_circ <- ggplot(d, aes(wk, value, colour = iso_year)) +
  geom_line(data = filter(d, !selected), alpha = 0.18, linewidth = 0.5) +
  geom_line(data = filter(d, selected), linewidth = 1.1) +
  geom_point(data = filter(peaks, !selected), shape = 21, size = 2.6, stroke = 0.8,
             fill = "white", alpha = 0.45) +
  geom_point(data = filter(peaks, selected), shape = 21, size = 3.6, stroke = 1.3,
             fill = "white") +
  scale_x_mixtime(name = "ISO week of year") +
  scale_y_continuous(name = ylab, labels = label_comma(), limits = c(0, NA)) +
  scale_colour_manual(values = year_cols, name = "ISO year", drop = FALSE) +
  coord_loop(time_loops = years(1L), coord = coord_radial(inner.radius = 0.08)) +
  guides(colour = guide_legend(ncol = 1, override.aes = list(alpha = 1, linewidth = 1.2, shape = NA))) +
  labs(subtitle = "Circular view: one turn per ISO year, week 1 at top, clockwise.\nCircles = peak week of each season (Saison); selected range in bold") +
  theme_minimal(base_size = 12) +
  theme(legend.position = "left", panel.grid.minor = element_blank())

# ---- Linear view -----------------------------------------------------------
p_lin <- ggplot(d, aes(wk, value)) +
  geom_rect(data = brush, aes(xmin = xmin, xmax = xmax, ymin = -Inf, ymax = Inf),
            inherit.aes = FALSE, fill = "grey60", alpha = 0.25) +
  geom_line(aes(colour = iso_year, group = 1), linewidth = 0.6) +
  geom_point(data = peaks, aes(colour = iso_year), shape = 21, fill = "white",
             size = 2.2, stroke = 1) +
  geom_text(data = peaks, aes(label = lab), vjust = -0.4, size = 2.7, lineheight = 0.85,
            colour = "grey25") +
  scale_x_mixtime(name = "Date (ISO week)", time_breaks = years(1L)) +
  scale_y_continuous(name = ylab, labels = label_comma(), limits = c(0, NA), expand = expansion(c(0, 0.12))) +
  scale_colour_manual(values = year_cols, guide = "none") +
  labs(subtitle = paste0("Linear view, ", min(format(d$date, "%Y")), "–", max(format(d$date, "%Y")),
                         ". Grey band = selection\n(shown bold in the circular view). ", sel_txt,
                         ".\nLabels = season and its peak ISO week")) +
  theme_minimal(base_size = 12) +
  theme(panel.grid.minor = element_blank())

# ---- Caption computed from the data ---------------------------------------
pk_wk <- as.integer(substr(peaks$Kalenderwoche, 7, 8))
pre  <- peaks$Saison < "2019/20"                       # seasons before COVID-19
post <- peaks$Saison > "2020/21" & peaks$Saison %in% complete
caption <- sprintf(paste0(
  "No: before 2020 the ARE peak always came in late winter (ISO weeks %d–%d), but since the pandemic ",
  "it has moved around, from week %d (December) to week %d (March)."),
  min(pk_wk[pre]), max(pk_wk[pre]),
  max(pk_wk[post][pk_wk[post] > 26]), max(pk_wk[post][pk_wk[post] <= 26]))

fig <- p_circ + p_lin + plot_layout(widths = c(1.1, 1)) +
  plot_annotation(
    title = "Does the acute respiratory illness (ARE) peak in Germany happen at the same time each year?",
    subtitle = caption,
    caption = "Data: Robert Koch-Institut, ARE-Konsultationsinzidenz (ARE-Praxis-Sentinel), Bundesweit, all ages (00+). CC BY 4.0.",
    theme = theme(plot.title = element_text(face = "bold", size = 16))
  )

ggsave("plot.png", fig, width = 14, height = 9, dpi = 100, bg = "white")
ggsave("plot.svg", fig, width = 14, height = 9, bg = "white")
