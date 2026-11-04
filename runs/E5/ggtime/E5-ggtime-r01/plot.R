# Five years of 10-minute weather data at Wien Hohe Warte (GeoSphere Austria, CC BY 4.0)
# Overview (2020-2024) -> linked detail week -> linked 10-minute zoom.
# Static output: the "brush" is the range in `select_range` / `zoom_range` below.
# Set them to any POSIXct range (UTC) to re-link all panels; NULL = choose from data.
suppressPackageStartupMessages({
  library(ggtime); library(ggplot2); library(tsibble); library(readr)
  library(dplyr); library(lubridate); library(scales); library(patchwork)
})

select_range <- NULL   # e.g. as.POSIXct(c("2021-07-15", "2021-07-22"), tz = "UTC")
zoom_range   <- NULL   # e.g. as.POSIXct(c("2021-07-17 12:00", "2021-07-17 20:00"), tz = "UTC")

url <- "https://raw.githubusercontent.com/denisseram/dataset-snapshots/3731e02e38c75e5d70ae92bf3596a69951866c2d/geosphere_wien_10min_2020-2024.csv"
raw <- read_csv(url, col_types = cols(time = col_character(), station = col_integer(),
                                      tl = col_double(), rr = col_double(),
                                      substation = col_integer()))
stopifnot(all(endsWith(raw$time, "+00:00")))   # all stamps are UTC
wx <- raw |>
  mutate(time = as.POSIXct(substr(time, 1, 16), format = "%Y-%m-%dT%H:%M", tz = "UTC")) |>
  as_tsibble(index = time, key = station) |>
  fill_gaps()                       # implicit gaps become NA -> lines break there
n_rows <- nrow(raw)

# ---- overview aggregate (daily, all rows used) ----
daily <- wx |> as_tibble() |>
  mutate(day = as.POSIXct(floor_date(time, "day"))) |>
  group_by(day) |>
  summarise(tmin = min(tl, na.rm = TRUE), tmax = max(tl, na.rm = TRUE),
            tmean = mean(tl, na.rm = TRUE), .groups = "drop")

# ---- default selections, computed from data: the wettest 10-minute reading ----
peak <- wx |> as_tibble() |> slice_max(rr, n = 1, with_ties = FALSE)
if (is.null(select_range)) select_range <- floor_date(peak$time, "day") + days(c(-3, 4))
if (is.null(zoom_range))   zoom_range   <- peak$time + hours(c(-4, 4))

sel  <- wx |> as_tibble() |> filter(time >= select_range[1], time <= select_range[2])
zoom <- wx |> as_tibble() |> filter(time >= zoom_range[1],   time <= zoom_range[2])

# ---- styling ----
c_t <- "#C0392B"; c_r <- "#2E6DB4"; c_sel <- "#F2B134"
th <- theme_minimal(base_size = 12) +
  theme(panel.grid.minor = element_blank(), plot.title.position = "plot",
        plot.subtitle = element_text(size = 10, colour = "grey30"))
sel_rect  <- function(r) annotate("rect", xmin = r[1], xmax = r[2], ymin = -Inf, ymax = Inf,
                                  fill = c_sel, alpha = 0.35)

# ---- A: overview ----
pA <- ggplot(daily, aes(day)) +
  sel_rect(select_range) +
  geom_ribbon(aes(ymin = tmin, ymax = tmax), fill = c_t, alpha = 0.25) +
  geom_time_line(aes(y = tmean), colour = c_t, linewidth = 0.3) +
  scale_x_datetime(date_breaks = "6 months", date_minor_breaks = "1 month",
                   labels = label_date_short(), expand = expansion(0.005)) +
  labs(subtitle = sprintf("A  Overview 2020-2024: daily mean (line) and min-max range (band) of %s 10-min readings; yellow = range shown in B",
                          format(n_rows, big.mark = ",")),
       x = "Time (UTC)", y = "Air temp. (°C)") + th

# ---- B: detail (selected week) ----
xs_B <- scale_x_datetime(limits = select_range, date_breaks = "1 day",
                         date_minor_breaks = "6 hours", labels = label_date("%a %d %b"),
                         expand = expansion(0.01))
pB_t <- ggplot(sel, aes(time, tl)) + sel_rect(zoom_range) +
  geom_time_line(colour = c_t, linewidth = 0.4) + xs_B +
  labs(subtitle = sprintf("B  Detail %s to %s (10-min readings); yellow = range shown in C",
                          format(select_range[1], "%d %b %Y"), format(select_range[2], "%d %b %Y")),
       x = NULL, y = "Air temp. (°C)") +
  th + theme(axis.text.x = element_blank())
pB_r <- ggplot(sel, aes(time, rr)) + sel_rect(zoom_range) +
  geom_col(fill = c_r, width = 600, na.rm = TRUE) + xs_B +
  labs(x = "Time (UTC)", y = "Precip.\n(mm/10 min)") + th

# ---- C: zoom to individual 10-minute readings ----
xs_C <- scale_x_datetime(limits = zoom_range + minutes(c(-5, 5)), date_breaks = "1 hour",
                         date_minor_breaks = "10 min", labels = label_date("%H:%M"),
                         expand = expansion(0))
pC_t <- ggplot(zoom, aes(time, tl)) +
  geom_time_line(colour = c_t, linewidth = 0.4) +
  geom_point(colour = c_t, size = 1.2, na.rm = TRUE) + xs_C +
  labs(subtitle = sprintf("C  Zoom %s: every point/bar is one 10-minute reading",
                          paste(format(zoom_range, "%d %b %Y %H:%M"), collapse = " to ")),
       x = NULL, y = "Air temp. (°C)") +
  th + theme(axis.text.x = element_blank(),
             panel.grid.minor.x = element_line(colour = "grey92", linewidth = 0.3))
pC_r <- ggplot(zoom, aes(time, rr)) +
  geom_col(fill = c_r, width = 540, na.rm = TRUE) + xs_C +
  labs(x = "Time (UTC)", y = "Precip.\n(mm/10 min)") +
  th + theme(panel.grid.minor.x = element_line(colour = "grey92", linewidth = 0.3))

# ---- caption computed from data ----
mon <- daily |> mutate(m = month(day)) |> group_by(m) |> summarise(t = mean(tmean))
warm <- mon |> slice_max(t, n = 1); cold <- mon |> slice_min(t, n = 1)
t_drop <- zoom |> filter(time <= peak$time) |> summarise(d = max(tl, na.rm = TRUE) - min(tl[time >= peak$time - hours(1)], na.rm = TRUE))
caption <- sprintf(
  "Temperature follows a strong annual cycle (mean %s %.1f °C vs %s %.1f °C) with daily swings of several degrees; the wettest 10 minutes (%.1f mm, %s UTC) came in a short burst during which air temperature fell by about %.1f °C.",
  month.name[warm$m], warm$t, month.name[cold$m], cold$t,
  peak$rr, format(peak$time, "%d %b %Y %H:%M"), t_drop$d)

fig <- pA / (pB_t / pB_r + plot_layout(heights = c(2, 1))) /
  (pC_t / pC_r + plot_layout(heights = c(2, 1))) +
  plot_layout(heights = c(1, 1.3, 1.3)) +
  plot_annotation(
    title = "Wien Hohe Warte, 10-minute air temperature and precipitation, 2020-2024",
    subtitle = NULL,
    caption = paste0(paste(strwrap(caption, 190), collapse = "\n"), "\nData: GeoSphere Austria, klima-v2-10min, station 105 (CC BY 4.0). All times UTC."),
    theme = theme(plot.title = element_text(face = "bold", size = 16),
                  plot.caption = element_text(hjust = 0, size = 10.5), plot.margin = margin(8, 25, 8, 8)))

ggsave("plot.png", fig, width = 1400, height = 900, units = "px", dpi = 100, bg = "white")
ggsave("plot.svg", fig, width = 14, height = 9, bg = "white")
