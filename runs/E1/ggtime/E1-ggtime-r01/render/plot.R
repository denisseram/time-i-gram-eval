suppressPackageStartupMessages({
  library(ggtime); library(ggplot2); library(tsibble); library(readr); library(dplyr); library(lubridate)
})
url <- "https://raw.githubusercontent.com/rfordatascience/tidytuesday/6753376ef104727ef0ca3e3db6f2ca580c0d5a7b/data/2026/2026-03-31/ocean_temperature.csv"
raw <- read_csv(url, show_col_types = FALSE)

# Monthly mean of daily means per depth; months without any data become explicit NA
monthly <- raw |>
  filter(!is.na(mean_temperature_degree_c)) |>
  mutate(month = yearmonth(date), depth = sensor_depth_at_low_tide_m) |>
  group_by(depth, month) |>
  summarise(temp = mean(mean_temperature_degree_c), .groups = "drop") |>
  as_tsibble(key = depth, index = month) |>
  fill_gaps(.full = TRUE) |>
  as_tibble()

depths <- sort(unique(monthly$depth))
monthly <- monthly |>
  mutate(depth_f = factor(paste(depth, "m"), levels = paste(depths, "m")),
         x = mixtime::yearmonth(as.Date(month)))

# Caption numbers computed from data: climatology by calendar month
clim <- monthly |>
  filter(!is.na(temp)) |>
  mutate(m = month(as.Date(month), label = TRUE, abbr = FALSE, locale = "C")) |>
  group_by(depth, m) |>
  summarise(t = mean(temp), .groups = "drop") |>
  group_by(depth) |>
  summarise(lo = min(t), hi = max(t), peak = as.character(m[which.max(t)]))
top <- clim |> filter(depth == min(depth)); bot <- clim |> filter(depth == max(depth))
caption <- sprintf(
  "Every year the %d m water warms from about %.0f °C in winter to %.0f °C in %s, while at %d m the seasonal swing is damped (%.0f–%.0f °C) and peaks later, in %s.",
  top$depth, top$lo, top$hi, top$peak, bot$depth, bot$lo, bot$hi, bot$peak)

p <- ggplot(monthly, aes(x = x, y = depth_f, fill = temp)) +
  geom_tile(height = 0.95) +
  scale_y_discrete(limits = rev) +
  scale_x_mixtime(time_breaks = mixtime::years(1L), expand = c(0, 0)) +
  scale_fill_viridis_c(option = "plasma", name = "Monthly mean\ntemperature (°C)",
                       na.value = NA) +
  labs(title = "Monthly mean water temperature by sensor depth, Birchy Head, Nova Scotia (2018–2025)",
       subtitle = "Each cell = mean of daily means for one depth and month; blank cells = no sensor data that month",
       x = "Month", y = "Sensor depth at low tide",
       caption = paste0(caption, "\nData: CMAR Coastal Monitoring Program, station Birchy Head (Open Government Licence – Nova Scotia).")) +
  theme_minimal(base_size = 14) +
  theme(panel.grid = element_blank(), plot.title = element_text(face = "bold"),
        plot.caption = element_text(hjust = 0, size = 12), plot.caption.position = "plot",
        plot.title.position = "plot", legend.key.height = unit(1.6, "cm"))

ggsave("plot.png", p, width = 1400, height = 900, units = "px", dpi = 100, bg = "white")
ggsave("plot.svg", p, width = 14, height = 9, bg = "white")
