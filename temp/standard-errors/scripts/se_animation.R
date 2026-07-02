library(tidyverse)
library(gganimate)
library(gifski)
library(here)

yale_blue  <- "#00356B"
yale_light <- "#286dc0"

sigma    <- 1
mu       <- 0
n_values <- c(5, 10, 25, 50, 100, 250, 500, 1000)
x_range  <- 4 * sigma / sqrt(min(n_values))

dat <- map_dfr(n_values, function(n) {
  se <- sigma / sqrt(n)
  tibble(
    x     = seq(-x_range, x_range, length.out = 1000),
    y     = dnorm(x, mean = mu, sd = se),
    n     = n,
    label = paste0("n = ", formatC(n, big.mark = ","), "   SE = ", round(se, 3))
  )
})

p <- ggplot(dat, aes(x = x, y = y)) +
  geom_area(fill = yale_blue, alpha = 0.15) +
  geom_line(color = yale_blue, linewidth = 1.1) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "gray50", linewidth = 0.5) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  labs(
    title    = "The Sampling Distribution Narrows as N Grows",
    subtitle = "{closest_state}",
    x        = expression(bar(x)),
    y        = "Density"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.title    = element_text(face = "bold", color = yale_blue, size = 15),
    plot.subtitle = element_text(size = 13, color = "gray30"),
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.title.x  = element_text(face = "italic")
  ) +
  transition_states(label, transition_length = 3, state_length = 2) +
  ease_aes("cubic-in-out")

animate(
  p,
  nframes   = 160,
  fps       = 16,
  width     = 700,
  height    = 440,
  renderer  = gifski_renderer()
)

anim_save(here("research-guides/standard-errors/images/se_animation.gif"))
