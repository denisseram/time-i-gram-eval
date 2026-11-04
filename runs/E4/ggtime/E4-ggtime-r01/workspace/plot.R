suppressPackageStartupMessages({
  library(ggtime); library(ggplot2); library(readr); library(dplyr); library(tidyr)
})
url <- "https://raw.githubusercontent.com/denisseram/dataset-snapshots/3731e02e38c75e5d70ae92bf3596a69951866c2d/ubuntu.csv"
# Ragged rows: trailing missing fields become NA
raw <- suppressWarnings(read_csv(url, col_types = cols(.default = col_character()),
                                 show_col_types = FALSE))
d <- raw |>
  mutate(across(created:`eol-legacy`, as.Date),
         type = ifelse(grepl("LTS", version), "LTS releases", "Interim releases"),
         type = factor(type, levels = c("LTS releases", "Interim releases"))) |>
  arrange(release) |>
  mutate(version = factor(version, levels = rev(version)))

yrs <- function(x, ref) as.numeric(x - ref) / 365.25
std_end <- d$eol
srv_end <- pmax(d$eol, d$`eol-server`, na.rm = TRUE)

phases <- bind_rows(
  tibble(d[c("version", "type")], phase = "Development",    start = d$created, end = d$release),
  tibble(d[c("version", "type")], phase = "Standard support", start = d$release, end = std_end),
  tibble(d[c("version", "type")], phase = "Extended server support", start = d$eol,
         end = ifelse(!is.na(d$`eol-server`) & d$`eol-server` > d$eol, d$`eol-server`, NA) |> as.Date()),
  tibble(d[c("version", "type")], phase = "ESM", start = srv_end, end = d$`eol-esm`),
  tibble(d[c("version", "type")], phase = "Legacy support", start = d$`eol-esm`, end = d$`eol-legacy`)
) |>
  filter(!is.na(start), !is.na(end), end > start) |>
  left_join(select(d, version, release), by = "version") |>
  mutate(x0 = yrs(start, release), x1 = yrs(end, release),
         phase = factor(phase, levels = c("Development", "Standard support",
                                          "Extended server support", "ESM", "Legacy support")))

events <- bind_rows(
  tibble(version = d$version, type = d$type, event = "Created (dev. start)", x = yrs(d$created, d$release)),
  tibble(version = d$version, type = d$type, event = "Release", x = 0)
)
today <- Sys.Date()
life_end <- pmax(d$eol, d$`eol-server`, d$`eol-esm`, d$`eol-legacy`, na.rm = TRUE)
future <- d |> mutate(x = yrs(today, release), xmin = yrs(created, release), xmax = yrs(life_end, release)) |>
  filter(x > xmin, x < xmax) |> select(version, type, x)

# Pattern for caption, computed from data
std_len <- d |> mutate(s = yrs(eol, release)) |> group_by(type) |>
  summarise(med = median(s), max_total = median(yrs(pmax(eol, `eol-server`, `eol-esm`, `eol-legacy`, na.rm = TRUE), release)))
lts_std <- std_len$med[std_len$type == "LTS releases"]
int_std <- std_len$med[std_len$type == "Interim releases"]
lts_tot <- max(phases$x1[phases$type == "LTS releases"])
dev_m <- median(yrs(d$release, d$created)) * 12
first_leg <- as.character(d$version[which(!is.na(d$`eol-legacy`))[1]])
cap <- sprintf(paste0("Aligned on release, all releases share a ~%.0f-month development lead-in, but life cycles split in two: ",
                      "interim releases get ~%.0f months of standard support (median), LTS releases ~%.0f years, ",
                      "and from %s on LTS releases add ESM and legacy support out to %.0f years."),
               dev_m, int_std * 12, lts_std, first_leg, lts_tot)
cap <- paste(strwrap(cap, 150), collapse = "\n")

pal <- c("Development" = "#9AA5B1", "Standard support" = "#2A78B5",
         "Extended server support" = "#5BB0A0", "ESM" = "#E39B3C", "Legacy support" = "#B5455A")

p <- ggplot(phases) +
  geom_vline(xintercept = 0, colour = "grey40", linewidth = 0.4) +
  geom_segment(aes(x = x0, xend = x1, y = version, yend = version, colour = phase),
               linewidth = 2.3, lineend = "butt") +
  geom_point(data = future, aes(x = x, y = version), shape = 124, size = 4, colour = "black", inherit.aes = FALSE) +
  geom_point(data = events, aes(x = x, y = version, shape = event), size = 1.5,
             fill = "white", colour = "black", stroke = 0.6) +
  scale_colour_manual(values = pal, name = "Phase", drop = FALSE) +
  scale_shape_manual(values = c("Created (dev. start)" = 21, "Release" = 23), name = "Event") +
  scale_x_continuous(breaks = seq(-1, 16, 1), expand = expansion(mult = 0.01)) +
  facet_grid(type ~ ., scales = "free_y", space = "free_y") +
  labs(title = "Ubuntu release life cycles aligned on each release date",
       subtitle = sprintf("One row per release, ordered by release date (oldest at top). Black tick = today (%s); anything to its right is planned.", today),
       x = "Years relative to release date (0 = release)", y = NULL,
       caption = cap) +
  guides(colour = guide_legend(order = 1, nrow = 1, override.aes = list(linewidth = 4)),
         shape = guide_legend(order = 2)) +
  theme_minimal(base_size = 11) +
  theme(panel.grid.minor = element_blank(), panel.grid.major.y = element_blank(),
        axis.text.y = element_text(size = 7),
        strip.text.y = element_text(angle = -90, face = "bold"),
        legend.position = "top", legend.box = "vertical", legend.box.just = "left", legend.margin = margin(0, 0, 0, 0), legend.spacing.y = unit(0, "pt"),
        plot.title = element_text(face = "bold", size = 15),
        plot.caption = element_text(hjust = 0, size = 10.5),
        plot.title.position = "plot", plot.caption.position = "plot")

ggsave("plot.png", p, width = 1400 / 150, height = 900 / 150, dpi = 150, bg = "white")
ggsave("plot.svg", p, width = 1400 / 150, height = 900 / 150, bg = "white")
