library(ggtime)
library(ggplot2)
library(readr)
library(dplyr)
library(tidyr)
library(svglite)

url <- "https://raw.githubusercontent.com/denisseram/dataset-snapshots/3731e02e38c75e5d70ae92bf3596a69951866c2d/ubuntu.csv"
# ragged rows: fill = TRUE turns omitted trailing fields into NA
raw <- read.csv(url, colClasses = "character", fill = TRUE,
                na.strings = "", check.names = FALSE)
names(raw) <- gsub("-", "_", names(raw))
d <- raw |>
  mutate(across(created:eol_legacy, as.Date),
         type = if_else(grepl("LTS", version), "LTS releases", "Interim releases"),
         type = factor(type, c("LTS releases", "Interim releases"))) |>
  arrange(release) |>
  mutate(version = factor(version, levels = rev(version)))

yrs <- function(x, ref) as.numeric(x - ref) / 365.25
today <- Sys.Date()

phases <- c("Development", "Standard support", "Extended server support",
            "Expanded Security Maintenance (ESM)", "Legacy support")

iv <- d |>
  mutate(server_end = if_else(!is.na(eol_server) & eol_server > eol, eol_server, as.Date(NA)),
         esm_start  = pmax(eol, server_end, na.rm = TRUE)) |>
  transmute(version, type, release,
            Development_s = created, Development_e = release,
            `Standard support_s` = release, `Standard support_e` = eol,
            `Extended server support_s` = eol, `Extended server support_e` = server_end,
            `Expanded Security Maintenance (ESM)_s` = esm_start,
            `Expanded Security Maintenance (ESM)_e` = eol_esm,
            `Legacy support_s` = eol_esm, `Legacy support_e` = eol_legacy) |>
  pivot_longer(-c(version, type, release), names_to = c("phase", ".value"),
               names_sep = "_(?=[se]$)") |>
  filter(!is.na(s), !is.na(e), e > s) |>
  mutate(phase = factor(phase, phases))

# split each interval at today's date into elapsed vs planned parts
past <- iv |> filter(s < today) |> mutate(e = pmin(e, today), status = "Elapsed")
fut  <- iv |> filter(e > today) |> mutate(s = pmax(s, today), status = "Planned (after today)")
seg <- bind_rows(past, fut) |>
  mutate(x = yrs(s, release), xend = yrs(e, release))

ev <- d |>
  select(version, type, release, created) |>
  mutate(Created = yrs(created, release), Release = 0) |>
  pivot_longer(c(Created, Release), names_to = "event", values_to = "x")

# numbers for the caption, computed from the data
dur <- d |> mutate(std = yrs(eol, release),
                   last = yrs(pmax(eol, eol_server, eol_esm, eol_legacy, na.rm = TRUE), release),
                   dev = yrs(release, created))
med <- dur |> group_by(type) |> summarise(std = median(std), last = median(last), dev = median(dev))
lts_recent <- dur |> filter(type == "LTS releases", !is.na(eol_legacy)) |> arrange(release)
int <- dur |> filter(type == "Interim releases") |> arrange(release) |>
  mutate(short = std < 1, regime = cumsum(short != lag(short, default = first(short))))
int_new <- int |> filter(regime == max(regime))
int_old <- int |> filter(regime < max(regime))
cap <- sprintf(paste0(
  "Aligned on release, life cycles are near-identical within each type: every release has ~%.1f years of development, ",
  "interim releases get a median %.1f years of standard support (%.1f before %s) and then end, while LTS releases get a median %.1f years ",
  "and (since %s) stack ESM and Legacy phases out to %.0f years after release."),
  median(dur$dev), median(int_new$std), median(int_old$std), as.character(int_new$version[1]), med$std[med$type == "LTS releases"],
  as.character(lts_recent$version[1]), median(lts_recent$last))

pal <- c("Development" = "#9E9E9E", "Standard support" = "#2A7AB0",
         "Extended server support" = "#7FB7DE",
         "Expanded Security Maintenance (ESM)" = "#E08A2E", "Legacy support" = "#B23A48")

p <- ggplot() +
  geom_vline(xintercept = 0, colour = "grey40", linewidth = 0.3) +
  geom_segment(data = seg, aes(x = x, xend = xend, y = version, yend = version,
                               colour = phase, alpha = status),
               linewidth = 3.2, lineend = "butt") +
  geom_point(data = ev, aes(x = x, y = version, shape = event),
             size = 1.6, fill = "white", colour = "black", stroke = 0.5) +
  facet_grid(type ~ ., scales = "free_y", space = "free_y") +
  scale_colour_manual(values = pal, name = "Phase", drop = FALSE) +
  scale_alpha_manual(values = c("Elapsed" = 1, "Planned (after today)" = 0.4),
                     name = sprintf("Status (today = %s)", format(today))) +
  scale_shape_manual(values = c(Created = 21, Release = 24), name = "Event",
                     labels = c("Created (development start)", "Release")) +
  scale_x_continuous(breaks = seq(-2, 16, 1), expand = expansion(mult = 0.01)) +
  labs(title = "Ubuntu release life cycles aligned on each release date",
       subtitle = "Rows ordered by release date (oldest at top); LTS and interim releases in separate panels",
       x = "Years relative to release date (0 = release)", y = "Version",
       caption = paste0(strwrap(cap, 190), collapse = "\n")) +
  guides(colour = guide_legend(order = 1, override.aes = list(linewidth = 4)),
         shape = guide_legend(order = 2), alpha = guide_legend(order = 3)) +
  theme_minimal(base_size = 11) +
  theme(panel.grid.major.y = element_blank(), panel.grid.minor = element_blank(),
        strip.text.y = element_text(face = "bold", angle = 270),
        axis.text.y = element_text(size = 7),
        legend.position = "right", plot.caption = element_text(hjust = 0, size = 10),
        plot.title = element_text(face = "bold", size = 15))

ggsave("plot.png", p, width = 1400, height = 900, units = "px", dpi = 110, bg = "white")
ggsave("plot.svg", p, width = 1400 / 110, height = 900 / 110, bg = "white")
