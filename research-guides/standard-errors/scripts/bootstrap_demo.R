# bootstrap_demo.R
#
# Two-panel animation illustrating the pairs bootstrap:
#
#   LEFT  — scatter of the original data, with each bootstrap resample
#           highlighted frame-by-frame. Points are sized by how many
#           times they were drawn; points not selected fade to gray.
#           The bootstrap OLS fit line (blue) updates each frame;
#           the original OLS fit (dashed gray) is shown for reference.
#
#   RIGHT — the distribution of bootstrap slope estimates accumulates
#           as resamples are added. The current estimate is marked;
#           once >= 30 samples exist, a density curve overlays the bars.
#           Final frame shows the 95% percentile-t CI.
#
# The two panels are animated separately and stitched with magick.
#
# Output: images/bootstrap_demo.gif

library(tidyverse)
library(gganimate)
library(gifski)
library(magick)
library(here)

set.seed(42)

yale_blue  <- "#00356B"
yale_light <- "#286dc0"

# ── Data ────────────────────────────────────────────────────────────────────────
n_obs  <- 42
B      <- 90         # bootstrap replicates to animate
beta1  <- 2.0
beta0  <- 0.5

x_orig <- runif(n_obs, 0, 3)
y_orig <- beta0 + beta1 * x_orig + rnorm(n_obs, 0, 1.1)
orig   <- tibble(id = seq_len(n_obs), x = x_orig, y = y_orig)

fit0   <- lm(y ~ x, data = orig)
int0   <- coef(fit0)["(Intercept)"]
slp0   <- coef(fit0)["x"]
se0    <- summary(fit0)$coefficients["x", "Std. Error"]

# ── Bootstrap samples ───────────────────────────────────────────────────────────
boot_fits <- map(seq_len(B), function(b) {
  idx <- sample(n_obs, n_obs, replace = TRUE)
  cnt <- tabulate(idx, nbins = n_obs)
  fit <- lm(y ~ x, data = orig[idx, ])
  list(
    counts = cnt,
    int    = coef(fit)["(Intercept)"],
    slope  = coef(fit)["x"]
  )
})

all_slopes <- map_dbl(boot_fits, "slope")
boot_se    <- sd(all_slopes)
boot_ci    <- quantile(all_slopes, c(0.025, 0.975))

# ── LEFT panel data ─────────────────────────────────────────────────────────────
scatter_df <- map_dfr(seq_len(B), function(b) {
  cnt <- boot_fits[[b]]$counts
  orig |>
    mutate(
      frame    = b,
      cnt      = cnt,
      selected = cnt > 0,
      pt_size  = pmin(cnt, 3),
      pt_color = if_else(cnt > 0, yale_light, "gray78"),
      pt_alpha = if_else(cnt > 0, 0.9,        0.35)
    )
})

lines_df <- map_dfr(seq_len(B), function(b) {
  i <- boot_fits[[b]]$int
  s <- boot_fits[[b]]$slope
  tibble(
    frame = b,
    x0 = 0, x1 = 3,
    y0 = i,           y1 = i + s * 3,     # bootstrap fit
    y0_ols = int0,    y1_ols = int0 + slp0 * 3  # original OLS (constant)
  )
})

# y range for left panel
y_lo_l <- min(orig$y) - 0.8
y_hi_l <- max(orig$y) + 0.8

# ── RIGHT panel data ────────────────────────────────────────────────────────────
# Fixed bin breaks spanning all bootstrap slopes
bin_breaks <- seq(
  floor(min(all_slopes) * 10) / 10 - 0.1,
  ceiling(max(all_slopes) * 10) / 10 + 0.1,
  by = 0.12
)

hist_df <- map_dfr(seq_len(B), function(b) {
  h <- hist(all_slopes[seq_len(b)], breaks = bin_breaks, plot = FALSE)
  tibble(
    frame = b,
    x_mid = h$mids,
    count = h$counts
  )
})

# Cumulative density for overlay (activate once b >= 15)
dens_df <- map_dfr(seq(15, B), function(b) {
  d <- density(all_slopes[seq_len(b)],
               from = min(bin_breaks), to = max(bin_breaks), n = 256)
  # Scale density to histogram counts
  bw <- diff(bin_breaks)[1]
  tibble(frame = b, x_d = d$x, y_d = d$y * b * bw)
})

# Current estimate marker
current_df <- tibble(
  frame = seq_len(B),
  beta_b = all_slopes
)

# ── LEFT animation ──────────────────────────────────────────────────────────────
p_left <- ggplot() +
  # Data points (colored by selection status)
  geom_point(
    data = scatter_df,
    aes(x = x, y = y, size = I(pt_size * 1.8 + 0.5),
        color = I(pt_color), alpha = I(pt_alpha))
  ) +
  # Original OLS line (constant across frames)
  geom_segment(
    data = lines_df,
    aes(x = x0, xend = x1, y = y0_ols, yend = y1_ols, group = frame),
    color = "gray55", linetype = "dashed", linewidth = 0.7
  ) +
  # Bootstrap OLS line (changes each frame)
  geom_segment(
    data = lines_df,
    aes(x = x0, xend = x1, y = y0, yend = y1, group = frame),
    color = yale_light, linewidth = 1.2
  ) +
  coord_cartesian(xlim = c(0, 3), ylim = c(y_lo_l, y_hi_l)) +
  labs(
    title    = "Resample {frame} of {nframes}",
    subtitle = "Blue = drawn (size ∝ count); gray = not selected.\nDashed = original OLS.",
    x = "x", y = "y"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title        = element_text(face = "bold", color = yale_blue, size = 12),
    plot.subtitle     = element_text(size = 8, color = "gray40"),
    panel.grid.minor  = element_blank()
  ) +
  transition_manual(frame)

gif_left <- animate(
  p_left,
  nframes  = B,
  fps      = 10,
  width    = 440,
  height   = 420,
  renderer = gifski_renderer()
)

# ── RIGHT animation ─────────────────────────────────────────────────────────────
p_right <- ggplot() +
  # Accumulating histogram bars
  geom_col(
    data = hist_df,
    aes(x = x_mid, y = count),
    fill = yale_light, alpha = 0.55, width = diff(bin_breaks)[1] * 0.92
  ) +
  # Density curve overlay (once >= 15 samples)
  geom_line(
    data = dens_df,
    aes(x = x_d, y = y_d),
    color = yale_blue, linewidth = 1.1
  ) +
  # Current estimate vertical line
  geom_vline(
    data = current_df,
    aes(xintercept = beta_b),
    color = "#dc2626", linewidth = 0.9, linetype = "solid"
  ) +
  # True OLS estimate
  geom_vline(
    xintercept = slp0,
    color = "gray40", linewidth = 0.8, linetype = "dashed"
  ) +
  # CI bounds appear once all reps are in (last 5 frames)
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
    title    = "Bootstrap distribution  (B = {frame})",
    subtitle = "Red line = current β̂boot; dashed = original OLS.\nDotted = 95% percentile CI (final frames).",
    x        = expression(hat(β)[bootstrap]),
    y        = "Count"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title        = element_text(face = "bold", color = yale_blue, size = 12),
    plot.subtitle     = element_text(size = 8, color = "gray40"),
    panel.grid.minor  = element_blank(),
    panel.grid.major.x = element_blank()
  ) +
  transition_manual(frame)

gif_right <- animate(
  p_right,
  nframes  = B,
  fps      = 10,
  width    = 440,
  height   = 420,
  renderer = gifski_renderer()
)

# ── Stitch panels side by side with magick ──────────────────────────────────────
img_left  <- image_read(gif_left)
img_right <- image_read(gif_right)

combined_frames <- map(seq_len(B), function(i) {
  image_append(c(img_left[i], img_right[i]), stack = FALSE)
})

final_gif <- image_animate(
  image_join(combined_frames),
  fps = 10, loop = 0     # magick requires fps to be a factor of 100
)

image_write(
  final_gif,
  here("research-guides/standard-errors/images/bootstrap_demo.gif")
)
