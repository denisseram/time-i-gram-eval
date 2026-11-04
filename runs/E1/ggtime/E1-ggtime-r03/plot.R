suppressPackageStartupMessages({
  library(ggtime); library(ggplot2); library(tsibble); library(readr)
  library(dplyr); library(tidyr); library(scales)
})
url <- "https://raw.githubusercontent.com/rfordatascience/tidytuesday/6753376ef104727ef0ca3e3db6f2ca580c0d5a7b/data/2026/2026-03-31/ocean_temperature.csv"
raw <- read_csv(url, show_col_types = FALSE)

depths <- sort(unique(raw$sensor_depth_at_low_tide_m))
monthly <- raw |>
  filter(!is.na(mean_temperature_degree_c)) |>
  mutate(month = yearmonth(date)) |>
  group_by(depth = sensor_depth_at_low_tide_m, month) |>
  summarise(temp = mean(mean_temperature_degree_c), .groups = "drop") |>
  as_tsibble(key = depth, index = month) |>
  # make every depth span the full record; missing months become explicit NA
  fill_gaps(.full = TRUE) |>
  mutate(depth_f = factor(paste(depth, "m"), levels = paste(depths, "m")))

rng <- range(monthly$month)
# summary for caption: computed from data
seas <- monthly |> as_tibble() |> filter(!is.na(temp)) |>
  group_by(depth) |> summarise(amp = diff(range(temp)))
shallow <- seas$amp[seas$depth == min(depths)]
deep <- seas$amp[seas$depth == max(depths)]

p <- ggplot(monthly, aes(x = month, y = depth_f, fill = temp)) +
  geom_tile(colour = "white", linewidth = 0.1) +
  scale_y_discrete(limits = rev, name = "Sensor depth at low tide") +
  scale_x_yearmonth(date_breaks = "1 year", date_labels = "%Y",
                    expand = expansion(0), name = NULL) +
  scale_fill_viridis_c(option = "plasma", na.value = "grey80",
                       name = "Monthly mean\ntemperature (°C)") +
  labs(
    title = sprintf("Monthly mean water temperature by depth, Birchy Head, Nova Scotia (%s – %s)",
                    format(rng[1]), format(rng[2])),
    subtitle = "Each cell = mean of daily means for that month and depth; grey = no data that month",
    caption = paste0(
      "Shallow water warms strongly every summer and the seasonal swing fades with depth (range of monthly means: ",
      sprintf("%.1f °C at %d m vs %.1f °C at %d m).", shallow, min(depths), deep, max(depths)),
      "\nSource: CMAR Coastal Monitoring Program, via TidyTuesday 2026-03-31. Open Government Licence – Nova Scotia.")
  ) +
  theme_minimal(base_size = 14) +
  theme(panel.grid = element_blank(), legend.key.height = unit(1.6, "cm"),
        plot.caption = element_text(hjust = 0, size = 11),
        plot.title.position = "plot", plot.caption.position = "plot")

ggsave("plot.png", p, width = 1400, height = 900, units = "px", dpi = 110, bg = "white")
ggsave("plot.svg", p, width = 1400 / 110, height = 900 / 110, bg = "white")
