# Five years of 10-minute weather data at Wien Hohe Warte (GeoSphere Austria, CC BY 4.0)
# Overview (daily aggregate of all 10-min tl readings) linked to a detail view of raw 10-min readings.
suppressPackageStartupMessages({
  library(ggtime); library(ggplot2); library(tsibble); library(readr)
  library(dplyr); library(lubridate); library(scales); library(patchwork)
})

url <- "https://raw.githubusercontent.com/denisseram/dataset-snapshots/3731e02e38c75e5d70ae92bf3596a69951866c2d/geosphere_wien_10min_2020-2024.csv"
raw <- read_csv(url, col_types = cols(time = col_character(), station = col_integer(),
                                      tl = col_double(), rr = col_double(),
                                      substation = col_integer()))

stopifnot(all(grepl("\\+00:00$", raw$time)))
wx <- raw |>
  mutate(time = ymd_hm(sub("\\+00:00$", "", raw$time), tz = "UTC")) |>
  as_tsibble(index = time, key = station)
n_rows <- nrow(wx)
n_gaps <- nrow(count_gaps(wx))
message(sprintf("rows loaded: %d, missing tl: %d, missing rr: %d, implicit gaps: %d",
                n_rows, sum(is.na(wx$tl)), sum(is.na(wx$rr)), n_gaps))

# ---- Selection ("brush") for the detail view --------------------------------
# Static figure: the linked range is set here. Default = 3 days centred on the day
# with the largest daily precipitation total (computed from the data).
# Set DETAIL_START / DETAIL_END env vars (e.g. "2023-07-01 00:00") to choose any period.
daily <- wx |>
  index_by(day = as_date(time)) |>
  summarise(tmin = min(tl, na.rm = TRUE), tmax = max(tl, na.rm = TRUE),
            tmean = mean(tl, na.rm = TRUE), rr = sum(rr, na.rm = TRUE),
            .groups = "drop") |>
  as_tibble()
wet_day <- daily$day[which.max(daily$rr)]
sel_start <- Sys.getenv("DETAIL_START", "")
sel_end   <- Sys.getenv("DETAIL_END", "")
sel_start <- if (nzchar(sel_start)) ymd_hm(sel_start, tz = "UTC") else as_datetime(wet_day - 1, tz = "UTC")
sel_end   <- if (nzchar(sel_end))   ymd_hm(sel_end,   tz = "UTC") else as_datetime(wet_day + 2, tz = "UTC")

detail <- wx |> filter(time >= sel_start, time < sel_end) |> as_tibble()
peak10 <- detail[which.max(detail$rr), ]

# ---- Caption computed from data ---------------------------------------------
yr <- daily |> mutate(y = year(day), m = month(day)) |>
  group_by(m) |> summarise(t = mean(tmean))
warm_m <- month.name[yr$m[which.max(yr$t)]]; cold_m <- month.name[yr$m[which.min(yr$t)]]
caption_txt <- sprintf(paste0(
  "Temperature follows a strong annual cycle (warmest month on average: %s %.1f °C, coldest: %s %.1f °C) ",
  "with daily swings on top; the detail shows the wettest day (%s, %.1f mm) where rain fell in short bursts of up to %.1f mm per 10 min."),
  warm_m, max(yr$t), cold_m, min(yr$t), format(wet_day, "%d %b %Y"), max(daily$rr), peak10$rr)
caption_full <- paste0(paste(strwrap(caption_txt, 210), collapse = "\n"), "\nData: GeoSphere Austria klima-v2-10min, station Wien Hohe Warte (105), ",
                       format(n_rows, big.mark = ","), " 10-min rows, CC BY 4.0.")

col_t <- "#c0392b"; col_r <- "#2471a3"; col_sel <- "#f4d03f"

# ---- Overview -----------------------------------------------------------------
p_over <- ggplot(daily, aes(x = as_datetime(day, tz = "UTC"))) +
  annotate("rect", xmin = sel_start, xmax = sel_end, ymin = -Inf, ymax = Inf,
           fill = col_sel, alpha = 0.6, colour = "#b7950b", linewidth = 0.6) +
  geom_ribbon(aes(ymin = tmin, ymax = tmax), fill = col_t, alpha = 0.25) +
  geom_time_line(aes(y = tmean), colour = col_t, linewidth = 0.3) +
  annotate("label", x = sel_start, y = max(daily$tmax), hjust = 1.05, vjust = 1, size = 3.2,
           label = "selected range → detail") +
  scale_x_datetime(date_breaks = "1 year", date_minor_breaks = "3 months",
                   labels = label_date_short(), expand = expansion(0.005)) +
  labs(x = "Date (UTC)", y = "Air temperature (°C)",
       subtitle = "Overview 2020–2024: daily mean (line) and min–max range (band) of all 10-min readings; yellow = selected range") +
  theme_minimal(11)

# ---- Detail (raw 10-minute readings) -----------------------------------------
span_h <- as.numeric(difftime(sel_end, sel_start, units = "hours"))
step_h <- if (span_h <= 12) 1 else if (span_h <= 48) 3 else if (span_h <= 24 * 7) 6 else 24
brk <- seq(floor_date(sel_start, "day"), sel_end, by = paste(step_h, "hours"))
brk <- brk[brk >= sel_start & brk < sel_end]
lab <- ifelse(hour(brk) == 0 & minute(brk) == 0 | seq_along(brk) == 1,
              format(brk, "%H:%M\n%a %d %b %Y"), format(brk, "%H:%M"))
xsc <- scale_x_datetime(limits = c(sel_start, sel_end), breaks = brk, labels = lab,
                        date_minor_breaks = "1 hour", expand = expansion(0.005))
p_tl <- ggplot(detail, aes(x = time, y = tl)) +
  geom_time_line(colour = col_t, linewidth = 0.4) +
  geom_point(colour = col_t, size = 0.7) +
  xsc +
  labs(x = NULL, y = "Air temperature (°C)",
       subtitle = sprintf("Detail %s – %s UTC: every 10-min reading (points)",
                          format(sel_start, "%d %b %Y %H:%M"), format(sel_end, "%d %b %Y %H:%M"))) +
  theme_minimal(11) +
  theme(panel.background = element_rect(fill = alpha(col_sel, 0.12), colour = NA),
        axis.text.x = element_blank())
p_rr <- ggplot(detail, aes(x = time + minutes(5), y = rr)) +   # bar centred on its 10-min interval
  geom_col(width = 600 * 0.85, fill = col_r) +
  xsc +
  labs(x = "Time (UTC)", y = "Precipitation\n(mm per 10 min)") +
  theme_minimal(11) +
  theme(panel.background = element_rect(fill = alpha(col_sel, 0.12), colour = NA))

fig <- p_over / p_tl / p_rr + plot_layout(heights = c(1.1, 1, 0.6)) +
  plot_annotation(
    title = "Wien Hohe Warte, 10-minute weather 2020–2024: five-year overview and single 10-minute readings",
    caption = caption_full,
    theme = theme(plot.title = element_text(face = "bold", size = 15),
                  plot.caption = element_text(hjust = 0, size = 10)))

ggsave("plot.png", fig, width = 1400 / 100, height = 900 / 100, dpi = 100, bg = "white")
ggsave("plot.svg", fig, width = 14, height = 9, bg = "white")
