# heteroskedasticity_coverage.R
#
# Animates 95% OLS confidence intervals across two data-generating processes
# (homoskedastic vs. heteroskedastic) as the sample size grows.
#
# Key point: both distributions tighten with n, but under heteroskedasticity
# OLS SEs are inconsistent — coverage stays well below 95% regardless of n.
#
# Output: images/heteroskedasticity_coverage.gif

library(tidyverse)
library(gganimate)
library(gifski)
library(here)

set.seed(42)

yale_blue  <- "#00356B"
yale_light <- "#286dc0"
red_err    <- "#dc2626"

# ── Parameters ─────────────────────────────────────────────────────────────────
beta1_true   <- 1.5          # slope we're trying to estimate
n_sims       <- 400          # simulations per (n, DGP) cell
n_show       <- 90           # CIs to display in each panel
sample_sizes <- c(50, 100, 200, 500, 1000)

# ── Simulate ────────────────────────────────────────────────────────────────────
run_sims <- function(n, dgp) {
  map_dfr(seq_len(n_sims), function(s) {
    x <- runif(n, 0, 4)
    e <- if (dgp == "homo") {
      rnorm(n, 0, 1.5)                          # constant variance
    } else {
      rnorm(n, 0, 0.35 + 0.65 * x)             # variance increases with x
    }
    y   <- 1 + beta1_true * x + e
    fit <- lm(y ~ x)
    b   <- coef(fit)["x"]
    se  <- sqrt(vcov(fit)["x", "x"])
    tibble(
      sim     = s,
      n       = n,
      dgp     = dgp,
      est     = b,
      lo      = b - qnorm(0.975) * se,
      hi      = b + qnorm(0.975) * se,
      covers  = lo <= beta1_true & beta1_true <= hi
    )
  })
}

all_sims <- bind_rows(
  map_dfr(sample_sizes, ~ run_sims(.x, "homo")),
  map_dfr(sample_sizes, ~ run_sims(.x, "hetero"))
)

# ── Coverage annotation ─────────────────────────────────────────────────────────
coverage_ann <- all_sims |>
  group_by(n, dgp) |>
  summarise(rate = mean(covers), .groups = "drop") |>
  mutate(label = sprintf("Coverage: %.0f%%", rate * 100))

# ── Display subset (sorted by estimate within each cell) ───────────────────────
display <- all_sims |>
  group_by(n, dgp) |>
  slice_sample(n = n_show) |>
  arrange(est) |>
  mutate(rank = row_number()) |>
  ungroup() |>
  mutate(
    facet_label  = if_else(dgp == "homo",
                           "Homoskedastic errors",
                           "Heteroskedastic errors"),
    covers_label = if_else(covers, "CI contains true β", "CI misses true β")
  ) |>
  left_join(coverage_ann |> select(n, dgp, label), by = c("n", "dgp"))

# ── Annotation positions ────────────────────────────────────────────────────────
ann_df <- display |>
  distinct(n, dgp, facet_label, label) |>
  mutate(ann_x = 3.2, ann_y = n_show - 3)

# ── Plot ────────────────────────────────────────────────────────────────────────
p <- ggplot(display, aes(y = rank)) +
  # CI lines
  geom_linerange(
    aes(xmin = lo, xmax = hi, color = covers_label),
    linewidth = 0.4, alpha = 0.75
  ) +
  # Centre dot
  geom_point(
    aes(x = est, color = covers_label),
    size = 0.7, alpha = 0.9
  ) +
  # True parameter
  geom_vline(
    xintercept = beta1_true,
    linewidth  = 1.1,
    color      = "black"
  ) +
  # Coverage label (per facet, per frame)
  geom_label(
    data = ann_df,
    aes(x = ann_x, y = ann_y, label = label),
    inherit.aes = FALSE,
    hjust = 1, size = 3.8, fontface = "bold",
    fill = "white", linewidth = 0.3, color = "gray20"
  ) +
  # Colours
  scale_color_manual(
    values = c("CI contains true β" = yale_light,
               "CI misses true β"   = red_err),
    name = NULL
  ) +
  scale_x_continuous(
    limits = c(-0.3, 3.3),
    breaks = c(0, 1, 1.5, 2, 3),
    labels = c("0", "1", "β = 1.5", "2", "3")
  ) +
  facet_wrap(~facet_label) +
  labs(
    title    = "95% OLS confidence intervals  —  n = {closest_state}",
    subtitle = paste(
      "Each line is a 95% CI from one simulated dataset.",
      "The vertical line marks the true slope β = 1.5."
    ),
    x       = expression(hat(β)[1]),
    y       = "Simulation (sorted by estimate)",
    caption = paste(
      "Heteroskedastic errors produce inconsistent standard errors.",
      "Coverage stays below 95% even as n grows.",
      "HC-corrected SEs restore correct coverage."
    )
  ) +
  theme_minimal(base_size = 13) +
  theme(
    strip.text        = element_text(face = "bold", size = 12, color = yale_blue),
    plot.title        = element_text(face = "bold", size = 13, color = yale_blue),
    plot.subtitle     = element_text(size = 10, color = "gray30"),
    plot.caption      = element_text(size = 9, color = "gray40"),
    legend.position   = "bottom",
    legend.text       = element_text(size = 11),
    panel.grid.minor  = element_blank(),
    axis.text.x       = element_text(size = 9)
  ) +
  transition_states(n, transition_length = 2, state_length = 5) +
  ease_aes("cubic-in-out")

# ── Render ──────────────────────────────────────────────────────────────────────
anim <- animate(
  p,
  nframes  = length(sample_sizes) * 30,
  fps      = 12,
  width    = 900,
  height   = 520,
  renderer = gifski_renderer()
)

anim_save(
  here("research-guides/standard-errors/images/heteroskedasticity_coverage.gif"),
  animation = anim
)
