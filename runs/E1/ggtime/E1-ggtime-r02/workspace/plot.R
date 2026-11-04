# Monthly mean water temperature by sensor depth, Birchy Head (CMAR), 2018-2025
suppressPackageStartupMessages({
  library(ggtime); library(ggplot2); library(tsibble)
  library(readr); library(dplyr); library(tidyr); library(scales)
})

url <- "https://raw.githubusercontent.com/rfordatascience/tidytuesday/6753376ef104727ef0ca3e3db6f2ca580c0d5a7b/data/2026/2026-03-31/ocean_temperature.csv"
daily <- read_csv(url, show_col_types = FALSE)

# R1: monthly mean of the daily means, per depth
monthly <- daily |>
  filter(!is.na(mean_temperature_degree_c)) |>
  mutate(month = yearmonth(date)) |>
  group_by(depth = sensor_depth_at_low_tide_m, month) |>
  summarise(temp = mean(mean_temperature_degree_c), .groups = "drop") |>
  as_tsibble(key = depth, index = month) |>
  # R2/R3: full monthly grid over the record; months without data become explicit NA
  fill_gaps(.full = TRUE) |>
  as_tibble()

depths <- sort(unique(monthly$depth))
monthly <- monthly |>
  mutate(depth_f = factor(paste(depth, "m"), levels = rev(paste(depths, "m"))),
         # mixtime month type, which ggtime's scale_x_mixtime understands
         month_mt = mixtime::yearmonth(as.Date(month)))

# Caption facts computed from the data
mon_clim <- monthly |>
  mutate(m = as.integer(format(month, "%m"))) |>
  group_by(depth, m) |> summarise(t = mean(temp, na.rm = TRUE), .groups = "drop")
rng <- mon_clim |> group_by(depth) |>
  summarise(amp = max(t, na.rm = TRUE) - min(t, na.rm = TRUE), .groups = "drop")
shallow <- rng |> filter(depth == min(depth))
deep    <- rng |> filter(depth == max(depth))
peak_m  <- mon_clim |> filter(depth == min(depth)) |> slice_max(t, n = 1) |> pull(m)
peak_m_deep <- mon_clim |> filter(depth == max(depth)) |> slice_max(t, n = 1) |> pull(m)
n_missing <- sum(is.na(monthly$temp))

caption <- sprintf(
  paste0("Every depth warms in summer and cools in winter, but the swing shrinks with depth: ",
         "the average seasonal range is %.0f °C at %d m (peak in %s) versus %.0f °C at %d m (peak in %s)."),
  shallow$amp, shallow$depth, month.name[peak_m],
  deep$amp, deep$depth, month.name[peak_m_deep])

p <- ggplot(monthly, aes(x = month_mt, y = depth_f, fill = temp)) +
  geom_tile(colour = "white", linewidth = 0.2) +
  scale_x_mixtime(name = NULL, time_breaks = mixtime::years(1L), expand = c(0, 0)) +
  scale_y_discrete(name = "Sensor depth at low tide") +
  scale_fill_viridis_c(name = "Monthly mean\ntemperature (°C)", option = "inferno",
                       na.value = "grey88") +
  labs(
    title = "Water temperature by depth, Birchy Head, Nova Scotia, Feb 2018 – Dec 2025",
    subtitle = sprintf("Monthly mean of daily sensor means. Light grey cells = no data that month (%d depth-months).", n_missing),
    caption = paste0(caption,
                     "\nData: Centre for Marine Applied Research (CMAR) Coastal Monitoring Program, via TidyTuesday 2026-03-31.")
  ) +
  theme_minimal(base_size = 15) +
  theme(panel.grid = element_blank(),
        plot.title = element_text(face = "bold"),
        plot.caption = element_text(hjust = 0, size = 12),
        plot.title.position = "plot", plot.caption.position = "plot",
        legend.key.height = unit(1.6, "cm"))

ggsave("plot.png", p, width = 1400, height = 900, units = "px", dpi = 100, bg = "white")
ggsave("plot.svg", p, width = 14, height = 9, bg = "white")
