# DEMO fixture for the gallery, not an agent output (the image next to it is a placeholder).
library(readr); library(dplyr); library(tsibble); library(ggplot2); library(ggtime)
url <- "https://raw.githubusercontent.com/robert-koch-institut/ARE-Konsultationsinzidenz/65ac2d278c06333808415795d65f0347c54be638/ARE-Konsultationsinzidenz.tsv"
are <- read_tsv(url) |>
  filter(Bundesland == "Bundesweit", Altersgruppe == "00+") |>
  mutate(week = yearweek(Kalenderwoche)) |>
  as_tsibble(index = week)
p <- autoplot(are, ARE_Konsultationsinzidenz) + labs(title = "DEMO fixture")
ggsave("plot.png", p, width = 14, height = 9, dpi = 100)
ggsave("plot.svg", p, width = 14, height = 9)
