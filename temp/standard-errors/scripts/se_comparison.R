library(tidyverse)
library(gganimate)
library(gifski)
library(sandwich)
library(lmtest)
library(fixest)
library(haven)
library(here)

nunn <- read_dta(here("research-guides/standard-errors/data/Nunn_Wantchekon_AER_2011.dta"))

# One estimation sample across every method (listwise on the model vars + the
# ethnic-group / district / coordinate variables the paper's SEs require), so the
# comparison is like-for-like.
keep <- c("trust_neighbors", "ln_exports", "murdock_name", "district",
          "centroid_lat", "centroid_long")
nunn  <- nunn[complete.cases(nunn[, keep]), ]
model <- lm(trust_neighbors ~ ln_exports, data = nunn)
b     <- as.numeric(coef(model)["ln_exports"])

# The three schemes Nunn & Wantchekon (2011) actually report side by side:
#   [.] cluster within ethnic groups
#   (.) two-way cluster within ethnic groups AND within districts (their headline)
#   {.} Conley (1999) spatial SEs, uniform window of 5 degrees (Euclidean)
# They found the three essentially identical. We compute them on the simplified
# bivariate model to show SE mechanics, so magnitudes differ from the published
# table (which adds controls and fixed effects).
#
# Pedagogy note (see the guide text): the design-based view (Abadie et al.)
# supports ethnic-group clustering because that is where the regressor varies,
# and Conley-Kelly (2025) caution that a fixed-window Conley correction can be
# anti-conservative for spatially trending regressors -- modern practice adds
# spatial-basis de-trending + a placebo test.
conley_fit <- feols(
  trust_neighbors ~ ln_exports, data = nunn,
  vcov = conley(5, distance = "triangular") ~ centroid_lat + centroid_long
)

method_levels <- c("OLS", "HC3",
                   "Cluster: ethnic group",
                   "Two-way: ethnic x district",
                   "Conley spatial (5 deg)")

se_vec <- c(
  sqrt(diag(vcov(model)))["ln_exports"],
  sqrt(diag(vcovHC(model, "HC3")))["ln_exports"],
  sqrt(diag(vcovCL(model, cluster = ~murdock_name)))["ln_exports"],
  sqrt(diag(vcovCL(model, cluster = ~murdock_name + district)))["ln_exports"],
  se(conley_fit)["ln_exports"]
)

results <- tibble(
  Method   = method_levels,
  Category = c("OLS", "HC", "Clustered", "Clustered", "Spatial"),
  ord      = seq_along(method_levels),
  est      = b,
  SE       = as.numeric(se_vec),
  lo95     = b - qnorm(0.975) * as.numeric(se_vec),
  hi95     = b + qnorm(0.975) * as.numeric(se_vec)
) |>
  mutate(Method = factor(Method, levels = rev(method_levels)))

frames <- map_dfr(
  seq_len(nrow(results)),
  function(i) slice(results, 1:i) |> mutate(frame = i)
)

palette <- c(OLS = "#6b7280", HC = "#286dc0",
             Clustered = "#dc2626", Spatial = "#7c3aed")

x_lim <- c(min(results$lo95) - 0.003, max(results$hi95) + 0.003)

p <- ggplot(frames, aes(y = Method, x = est, color = Category)) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "gray50", linewidth = 0.6) +
  geom_linerange(aes(xmin = lo95, xmax = hi95), linewidth = 1.3) +
  geom_point(size = 4) +
  scale_color_manual(values = palette, name = NULL) +
  scale_x_continuous(limits = x_lim) +
  labs(
    x        = "Coefficient on log slave exports",
    y        = NULL,
    title    = "95% confidence intervals across SE correction methods",
    subtitle = "Nunn & Wantchekon (2011) — outcome: trust in neighbors"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.title       = element_text(face = "bold", size = 15),
    plot.subtitle    = element_text(size = 12, color = "gray30"),
    panel.grid.minor = element_blank(),
    legend.position  = "top"
  ) +
  transition_states(frame, transition_length = 2, state_length = 3) +
  enter_fade()

animate(
  p,
  nframes  = 90,
  fps      = 12,
  width    = 700,
  height   = 400,
  renderer = gifski_renderer()
)

anim_save(here("research-guides/standard-errors/images/se_comparison.gif"))
