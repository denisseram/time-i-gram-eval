suppressPackageStartupMessages({
  library(ggtime); library(ggplot2); library(readr); library(dplyr)
  library(lubridate); library(scales); library(patchwork); library(tsibble)
})
url <- "https://raw.githubusercontent.com/denisseram/dataset-snapshots/3731e02e38c75e5d70ae92bf3596a69951866c2d/geosphere_wien_10min_2020-2024.csv"
raw <- read_csv(url, col_types = cols(time = col_character(), station = col_integer(),
                tl = col_double(), rr = col_double(), substation = col_integer()))
wx <- raw |>
  mutate(time = ymd_hm(sub("\\+00:00$", "", time), tz = "UTC")) |>
  arrange(time)
stopifnot(all(endsWith(raw$time, "+00:00")), !anyNA(wx$time))
wx_ts <- as_tsibble(wx, index = time)          # all rows, regular 10-min tsibble
stopifnot(nrow(wx_ts) == nrow(raw))

# ---- Overview: daily min / mean / max of tl (aggregated in-script) ----
daily <- wx |>
  mutate(date = as_datetime(as_date(time), tz = "UTC")) |>
  summarise(tmin = min(tl, na.rm = TRUE), tmean = mean(tl, na.rm = TRUE),
            tmax = max(tl, na.rm = TRUE), .by = date)

# ---- Selected range (computed from data): 48 h centred on the wettest 10-min reading ----
peak <- wx |> slice_max(rr, n = 1, with_ties = FALSE)
sel_start <- floor_date(peak$time, "hour") - hours(24)
sel_end   <- sel_start + hours(48)
detail <- wx |> filter(time >= sel_start, time <= sel_end)

col_t <- "#B2452F"; col_r <- "#2C6CA3"; col_sel <- "#E8A33D"
base_theme <- theme_minimal(base_size = 13) +
  theme(panel.grid.minor = element_blank(), plot.title.position = "plot")

p_over <- ggplot(daily, aes(x = date)) +
  geom_ribbon(aes(ymin = tmin, ymax = tmax), fill = col_t, alpha = 0.25) +
  geom_time_line(aes(y = tmean), colour = col_t, linewidth = 0.3) +
  annotate("rect", xmin = sel_start - days(4), xmax = sel_end + days(4),
           ymin = -Inf, ymax = Inf, fill = col_sel, alpha = 0.35) +
  annotate("text", x = sel_start - days(8), y = max(daily$tmax),
           label = "selected range\n(shown below) \u2192", hjust = 1, vjust = 1, size = 3.5,
           colour = "grey20", lineheight = 0.9) +
  scale_x_datetime(breaks = seq(floor_date(min(daily$date), "year"),
                                ceiling_date(max(daily$date), "year"), by = "3 months"),
                   minor_breaks = NULL,
                   labels = function(x) ifelse(month(x) == 1, format(x, "%b\n%Y"), format(x, "%b")),
                   expand = expansion(0.005)) +
  labs(x = "Date (UTC)", y = "Air temperature (°C)",
       subtitle = "Overview 2020–2024: daily mean (line) and daily min–max range (band) of 10-min air temperature") +
  base_theme + theme(panel.grid.minor.x = element_line(colour = "grey92"))

det_lim <- c(sel_start, sel_end)
det_breaks <- seq(ceiling_date(sel_start, "6 hours"), sel_end, by = "6 hours")
p_tl <- ggplot(detail, aes(x = time, y = tl)) +
  geom_time_line(colour = col_t, linewidth = 0.5) +
  geom_point(colour = col_t, size = 0.9) +
  scale_x_datetime(limits = det_lim, breaks = det_breaks, date_minor_breaks = "1 hour", expand = expansion(0)) +
  labs(x = NULL, y = "Air temp. (°C)",
       subtitle = sprintf("Detail %s – %s UTC: every 10-minute reading (points)",
                          format(sel_start, "%d %b %Y %H:%M"), format(sel_end, "%d %b %Y %H:%M"))) +
  base_theme + theme(axis.text.x = element_blank(),
                     panel.grid.minor.x = element_line(colour = "grey92"))

p_rr <- ggplot(detail, aes(x = time, y = rr)) +
  geom_col(fill = col_r, width = 600 * 0.85, just = 1) +   # bar covers its 10-min interval
  scale_x_datetime(limits = det_lim + c(-600, 0), breaks = det_breaks, date_minor_breaks = "1 hour",
                   labels = function(x) ifelse(hour(x) == 0, format(x, "%H:%M\n%d %b %Y"), format(x, "%H:%M")),
                   expand = expansion(0)) +
  scale_y_continuous(expand = expansion(c(0, 0.05))) +
  labs(x = "Time (UTC)", y = "Precip.\n(mm per 10 min)") +
  base_theme + theme(panel.grid.minor.x = element_line(colour = "grey92"))

caption <- sprintf(
  "Temperature follows a strong annual cycle (daily means from %.0f °C to %.0f °C); the wettest 10 minutes (%.1f mm, %s UTC) came with a sharp temperature drop.",
  min(daily$tmean), max(daily$tmean), peak$rr, format(peak$time, "%d %b %Y %H:%M"))

fig <- p_over / p_tl / p_rr + plot_layout(heights = c(1.3, 1, 0.6)) +
  plot_annotation(
    title = "Vienna Hohe Warte, 10-minute weather 2020–2024: overview and detail",
    subtitle = sprintf("%s 10-minute records loaded. Shaded band in the overview marks the period shown in the detail tracks.",
                       format(nrow(wx), big.mark = ",")),
    caption = paste0(caption, "\nData: GeoSphere Austria, klima-v2-10min, station 105 (CC BY 4.0)."),
    theme = theme(plot.title = element_text(face = "bold", size = 17),
                  plot.caption = element_text(hjust = 0, size = 11)))

ggsave("plot.png", fig, width = 1400, height = 900, units = "px", dpi = 100, bg = "white")
ggsave("plot.svg", fig, width = 14, height = 9, bg = "white")
