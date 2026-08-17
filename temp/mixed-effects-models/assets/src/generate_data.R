# Parameters
n_farms <- 5
n_plots_per_farm <- 30
n_total <- n_farms * n_plots_per_farm

# Variance components
farm_effect_sd <- 20 # Between-farm variation (random intercept SD)
residual_sd <- 12 # Within-farm variation (residual SD)

# Generate farm IDs
farm_ids <- rep(1:n_farms, each = n_plots_per_farm)

# Generate random farm effects (random intercepts)
farm_effects <- rnorm(n_farms, mean = 0, sd = farm_effect_sd)

# Generate plot-level data
crop_data <- data.frame(
    farm_id = factor(farm_ids),
    plot_id = 1:n_total
)

# Generate soil pH (varies within and between farms)
crop_data$soil_pH <- rnorm(n_total, mean = 6.5, sd = 0.5)

# Generate yield based on: yield ~ soil_pH + (1|farm)
# Fixed effects
beta_0 <- 100 # Intercept (mean yield at pH = 6.5)
beta_soil_pH <- 15 # Effect of soil pH (bushels per pH unit)

# Generate yield
crop_data$yield <- beta_0 +
    farm_effects[farm_ids] + # Random farm intercept
    beta_soil_pH * (crop_data$soil_pH - 6.5) + # Soil pH effect (centered)
    rnorm(n_total, mean = 0, sd = residual_sd) # Residual error

# Save dataset
readr::write_csv(
    crop_data,
    here::here("./research-guides/mixed-effects-models/data/crop_yield_data.csv")
)
