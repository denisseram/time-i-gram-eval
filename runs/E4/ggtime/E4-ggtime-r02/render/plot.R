suppressPackageStartupMessages({
  library(ggtime); library(ggplot2); library(dplyr); library(tidyr)
  library(readr); library(lubridate); library(svglite)
})
url <- "https://raw.githubusercontent.com/denisseram/dataset-snapshots/3731e02e38c75e5d70ae92bf3596a69951866c2d/ubuntu.csv"
# Ragged rows: trailing omitted fields become NA
raw <- read.csv(url, colClasses = "character", fill = TRUE, check.names = FALSE,
                na.strings = c("", "NA"))
d <- raw |>
  mutate(across(c(created, release, eol, `eol-server`, `eol-esm`, `eol-legacy`), as.Date),
         type = ifelse(grepl("LTS", version), "LTS releases", "Interim releases")) |>
  arrange(release)

yrs <- function(x, ref) time_length(interval(ref, x), "year")

phase_lv <- c("Development", "Standard support", "Extended server support",
              "Expanded Security Maintenance (ESM)", "Legacy support")
srv_end <- ifelse(!is.na(d$`eol-server`) & d$`eol-server` > d$eol, d$`eol-server`, d$eol)
srv_end <- as.Date(srv_end, origin = "1970-01-01")
ph <- bind_rows(
  tibble(version = d$version, type = d$type, phase = phase_lv[1], start = d$created, end = d$release, ref = d$release),
  tibble(version = d$version, type = d$type, phase = phase_lv[2], start = d$release, end = d$eol, ref = d$release),
  tibble(version = d$version, type = d$type, phase = phase_lv[3], start = d$eol,
         end = as.Date(ifelse(!is.na(d$`eol-server`) & d$`eol-server` > d$eol, d$`eol-server`, NA), origin = "1970-01-01"), ref = d$release),
  tibble(version = d$version, type = d$type, phase = phase_lv[4], start = srv_end, end = d$`eol-esm`, ref = d$release),
  tibble(version = d$version, type = d$type, phase = phase_lv[5], start = d$`eol-esm`, end = d$`eol-legacy`, ref = d$release)
) |>
  filter(!is.na(start), !is.na(end), end > start) |>
  mutate(x0 = yrs(start, ref), x1 = yrs(end, ref),
         phase = factor(phase, levels = phase_lv),
         version = factor(version, levels = rev(d$version)))
# long format for ggtime's geom_time_line: each phase is a two-point line
ph_long <- ph |> mutate(id = paste(version, phase)) |>
  pivot_longer(c(x0, x1), values_to = "x")

ev <- d |> transmute(version = factor(version, levels = rev(d$version)), type,
                     `Created (start of development)` = yrs(created, release),
                     Release = 0) |>
  pivot_longer(-c(version, type), names_to = "event", values_to = "x")

today <- Sys.Date()
fut <- d |> mutate(last = pmax(eol, `eol-server`, `eol-esm`, `eol-legacy`, na.rm = TRUE)) |>
  filter(today < last) |>
  transmute(version = factor(version, levels = rev(d$version)), type, x = yrs(today, release))

# Main pattern, computed from data
med <- d |> mutate(sup = yrs(eol, release),
                   last = yrs(pmax(eol, `eol-server`, `eol-esm`, `eol-legacy`, na.rm = TRUE), release)) |>
  group_by(type) |> summarise(lo = min(sup) * 12, hi = max(sup) * 12, sup = median(sup), last = median(last))
mi <- med[med$type == "Interim releases", ]; ml <- med[med$type == "LTS releases", ]
cap <- sprintf(paste0("Aligned on release, interim releases all share one short life of %.0f-%.0f months of standard support, ",
  "while LTS releases get a median %.1f years of standard support and, in recent releases, ESM and legacy add-ons stretching to a median %.0f years in total."),
  mi$lo, mi$hi, ml$sup, ml$last)
cap <- paste0(strwrap(cap, 170), collapse = "\n")
cap <- paste0(cap, "\nDark vertical tick: today (", format(today), "); bars to its right are planned (future) dates; drawn only for releases still in their life cycle. Data: distro-info-data (ubuntu.csv).")

pal <- c("Development" = "#9e9e9e", "Standard support" = "#2a78b5",
         "Extended server support" = "#7fb8e0",
         "Expanded Security Maintenance (ESM)" = "#e08a2a", "Legacy support" = "#b5452a")

p <- ggplot(ph_long, aes(x = x, y = version)) +
  geom_vline(xintercept = 0, colour = "grey40", linewidth = 0.4) +
  geom_time_line(aes(group = id, colour = phase), linewidth = 2.6, lineend = "butt") +
  geom_point(data = fut, aes(x = x, y = version), inherit.aes = FALSE, shape = "|", size = 4.5, colour = "black") +
  geom_point(data = ev, aes(x = x, y = version, shape = event), size = 1.8, fill = "white", colour = "black") +
  scale_colour_manual(values = pal, name = "Phase", drop = FALSE) +
  scale_shape_manual(values = c("Created (start of development)" = 21, Release = 23), name = "Event") +
  scale_x_continuous(breaks = seq(-2, 16, 1), minor_breaks = NULL) +
  facet_grid(type ~ ., scales = "free_y", space = "free_y") +
  labs(title = "Ubuntu release life cycles aligned on each release date",
       subtitle = "One row per release, ordered by release date (oldest at top); 0 = release date",
       x = "Time relative to release date (years)", y = "Version", caption = cap) +
  theme_minimal(base_size = 11) +
  theme(legend.position = "right", panel.grid.major.y = element_blank(),
        axis.text.y = element_text(size = 7), strip.text = element_text(face = "bold", size = 11),
        plot.caption = element_text(hjust = 0, size = 10), plot.caption.position = "plot",
        plot.title = element_text(face = "bold"))

ggsave("plot.png", p, width = 1400, height = 900, units = "px", dpi = 100, bg = "white")
ggsave("plot.svg", p, width = 14, height = 9, bg = "white")
