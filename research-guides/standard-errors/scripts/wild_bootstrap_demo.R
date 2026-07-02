# wild_bootstrap_demo.R
#
# Two-panel animation of the wild bootstrap:
#
#   LEFT  — original data (open gray circles) fixed in place; perturbed y* values
#           overlaid as filled dots colored by the Rademacher weight applied:
#           blue  = w = +1 (residual kept as-is, point shifts slightly up/down
#                           from its original position)
#           red   = w = −1 (residual flipped, point moves to the opposite side
#                           of the fitted line)
#           Short vertical segments connect each original y to the perturbed y*.
#           The bootstrap OLS fit through y* (dark blue) shifts each frame;
#           the original OLS fit (dashed gray) remains fixed.
#
#           KEY visual: the x-coordinates of every point are frozen — only y
#           is perturbed. This contrasts directly with the pairs bootstrap,
#           where both x and y vary across resamples.
#
#   RIGHT — accumulating distribution of wild bootstrap slope estimates.
#           Structure mirrors bootstrap_demo.R for direct comparison.
#
# Output: images/wild_bootstrap_demo.gif

library(tidyverse)
library(gganimate)
library(gifski)
library(magick)
library(here)

set.seed(42)

yale_blue  <- "#00356B"
yale_light <- "#286dc0"
red_err    <- "#dc2626"

# ── Data (same seed/DGP as bootstrap_demo.R for comparability) ────────────────
n_obs  <- 42
B      <- 90
beta1  <- 2.0
beta0  <- 0.5

x_orig <- runif(n_obs, 0, 3)
y_orig <- beta0 + beta1 * x_orig + rnorm(n_obs, 0, 1.1)
orig   <- tibble(id = seq_len(n_obs), x = x_orig, y = y_orig)

fit0   <- lm(y ~ x, data = orig)
int0   <- coef(fit0)["(Intercept)"]
slp0   <- coef(fit0)["x"]
yhat   <- fitted(fit0)
ehat   <- resid(fit0)

# ── Wild bootstrap samples ─────────────────────────────────────────────────────
# Rademacher weights: w_i ~ {-1, +1} with equal probability
# y*_i = ŷ_i + w_i * ê_i
wild_fits <- map(seq_len(B), function(b) {
  w      <- sample(c(-1L, 1L), n_obs, replace = TRUE)
  y_star <- as.numeric(yhat + w * ehat)
  df_b   <- orig |> mutate(y_star = y_star)
  fit    <- lm(y_star ~ x, data = df_b)
  list(
    w      = w,
    y_star = y_star,
    int    = coef(fit)["(Intercept)"],
    slope  = coef(fit)["x"]
  )
})

all_slopes <- map_dbl(wild_fits, "slope")
boot_ci    <- quantile(all_slopes, c(0.025, 0.975))

# ── LEFT panel: scatter data ───────────────────────────────────────────────────
scatter_df <- map_dfr(seq_len(B), function(b) {
  w      <- wild_fits[[b]]$w
  y_star <- wild_fits[[b]]$y_star
  tibble(
    frame   = b,
    id      = seq_len(n_obs),
    x       = x_orig,
    y_orig  = y_orig,
    y_star  = y_star,
    w_label = if_else(w == 1L, "w = +1  (keep)", "w = −1  (flip)")
  )
})

lines_df <- map_dfr(seq_len(B), function(b) {
  tibble(
    frame  = b,
    x0 = 0, x1 = 3,
    y0     = wild_fits[[b]]$int,
    y1     = wild_fits[[b]]$int + wild_fits[[b]]$slope * 3,
    y0_ols = int0,
    y1_ols = int0 + slp0 * 3
  )
})

y_pad  <- 0.6
y_lo_l <- min(c(y_orig, unlist(map(wild_fits, "y_star")))) - y_pad
y_hi_l <- max(c(y_orig, unlist(map(wild_fits, "y_star")))) + y_pad

# ── RIGHT panel: accumulating histogram ───────────────────────────────────────
bin_breaks <- seq(
  floor(min(all_slopes) * 10) / 10 - 0.15,
  ceiling(max(all_slopes) * 10) / 10 + 0.15,
  by = 0.14
)

hist_df <- map_dfr(seq_len(B), function(b) {
  h <- hist(all_slopes[seq_len(b)], breaks = bin_breaks, plot = FALSE)
  tibble(frame = b, x_mid = h$mids, count = h$counts)
})

dens_df <- map_dfr(seq(15, B), function(b) {
  d  <- density(all_slopes[seq_len(b)],
                from = min(bin_breaks), to = max(bin_breaks), n = 256)
  bw <- diff(bin_breaks)[1]
  tibble(frame = b, x_d = d$x, y_d = d$y * b * bw)
})

current_df <- tibble(frame = seq_len(B), beta_b = all_slopes)

# ── LEFT animation ─────────────────────────────────────────────────────────────
p_left <- ggplot() +
  # Original y positions (fixed open circles — the key visual anchor)
  geom_point(
    data = scatter_df,
    aes(x = x, y = y_orig),
    color = "gray70", size = 1.8, shape = 1, stroke = 0.6
  ) +
  # Segments from original y to perturbed y*
  geom_segment(
    data = scatter_df,
    aes(x = x, xend = x, y = y_orig, yend = y_star, color = w_label),
    alpha = 0.4, linewidth = 0.5
  ) +
  # Perturbed y* values (filled, colored by weight)
  geom_point(
    data = scatter_df,
    aes(x = x, y = y_star, color = w_label),
    size = 2.0, alpha = 0.85
  ) +
  # Original OLS line (constant reference)
  geom_segment(
    data = lines_df,
    aes(x = x0, xend = x1, y = y0_ols, yend = y1_ols, group = frame),
    color = "gray55", linetype = "dashed", linewidth = 0.75
  ) +
  # Wild bootstrap OLS fit (updates each frame)
  geom_segment(
    data = lines_df,
    aes(x = x0, xend = x1, y = y0, yend = y1, group = frame),
    color = yale_blue, linewidth = 1.15
  ) +
  scale_color_manual(
    values = c("w = +1  (keep)" = yale_light, "w = −1  (flip)" = red_err),
    name   = NULL
  ) +
  coord_cartesian(xlim = c(0, 3), ylim = c(y_lo_l, y_hi_l)) +
  labs(
    title    = "Wild bootstrap — resample {frame} of {nframes}",
    subtitle = "Open circles = original y  |  Filled = y* = ŷ + w·ê\nx is frozen; only y is perturbed. Dashed = original OLS.",
    x = "x", y = "y"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title       = element_text(face = "bold", color = yale_blue, size = 12),
    plot.subtitle    = element_text(size = 8, color = "gray35"),
    panel.grid.minor = element_blank(),
    legend.position  = "bottom",
    legend.text      = element_text(size = 9)
  ) +
  transition_manual(frame)

gif_left <- animate(
  p_left,
  nframes  = B,
  fps      = 10,
  width    = 440,
  height   = 430,
  renderer = gifski_renderer()
)

# ── RIGHT animation ────────────────────────────────────────────────────────────
p_right <- ggplot() +
  geom_col(
    data = hist_df,
    aes(x = x_mid, y = count),
    fill = yale_blue, alpha = 0.5, width = diff(bin_breaks)[1] * 0.9
  ) +
  geom_line(
    data = dens_df,
    aes(x = x_d, y = y_d),
    color = yale_blue, linewidth = 1.1
  ) +
  geom_vline(
    data = current_df,
    aes(xintercept = beta_b),
    color = red_err, linewidth = 0.9
  ) +
  geom_vline(
    xintercept = slp0,
    color = "gray45", linewidth = 0.8, linetype = "dashed"
  ) +
  geom_vline(
    data = current_df |> filter(frame > B - 5),
    aes(xintercept = boot_ci[1]),
    color = yale_blue, linewidth = 1.0, linetype = "dotted"
  ) +
  geom_vline(
    data = current_df |> filter(frame > B - 5),
    aes(xintercept = boot_ci[2]),
    color = yale_blue, linewidth = 1.0, linetype = "dotted"
  ) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.08))) +
  labs(
    title    = "Wild bootstrap distribution  (B = {frame})",
    subtitle = "Red = current estimate; dashed = original OLS.\nDotted = 95% percentile CI (final frames).",
    x        = expression(hat(β)[wild]),
    y        = "Count"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title         = element_text(face = "bold", color = yale_blue, size = 12),
    plot.subtitle      = element_text(size = 8, color = "gray40"),
    panel.grid.minor   = element_blank(),
    panel.grid.major.x = element_blank()
  ) +
  transition_manual(frame)

gif_right <- animate(
  p_right,
  nframes  = B,
  fps      = 10,
  width    = 440,
  height   = 430,
  renderer = gifski_renderer()
)

# ── Stitch left + right with magick ───────────────────────────────────────────
img_left  <- image_read(gif_left)
img_right <- image_read(gif_right)

combined <- image_animate(
  image_join(
    map(seq_len(B), ~ image_append(c(img_left[.x], img_right[.x]), stack = FALSE))
  ),
  fps = 10, loop = 0
)

image_write(
  combined,
  here("research-guides/standard-errors/images/wild_bootstrap_demo.gif")
)
