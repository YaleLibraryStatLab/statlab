# Monte Carlo: empirical size of SE estimators under cluster-randomized assignment.
# Demonstrates the guide's central claims with actual rejection rates.
# Design (Neitzche): random-intercept errors, cluster-level treatment (worst case
# for the Moulton problem). H0: beta1 = 0 is true, so every rejection is a false
# positive; the target is the nominal 5%.
#
# The committed defaults (M = 2000, B = 999) reproduce the table in the guide.
# Lower M and B at the top of the script for a fast preview while iterating.

suppressMessages({
  library(clubSandwich); library(fwildclusterboot); library(sandwich)
  library(lmtest); library(dplyr); library(tidyr); library(purrr); library(here)
})

M    <- 2000    # replications per cell (lower to ~400 for a fast preview)
B    <- 999     # wild-bootstrap draws (lower to ~499 for a fast preview)
n_g  <- 30      # units per cluster
GRID <- expand_grid(G = c(6, 12, 30, 50), rho = c(0, 0.3))

sim_once <- function(G, n_g, rho, beta1 = 0, sigma = 1, B = 499) {
  g <- rep(seq_len(G), each = n_g)
  repeat {                                   # guard: both treatment arms non-empty
    Dg <- rbinom(G, 1, 0.5)
    if (any(Dg == 1) && any(Dg == 0)) break
  }
  D <- rep(Dg, each = n_g)
  u <- rep(rnorm(G, 0, sqrt(rho) * sigma), each = n_g)
  v <- rnorm(G * n_g, 0, sqrt(1 - rho) * sigma)
  y <- beta1 * D + u + v
  dat <- data.frame(y, D, g = factor(g))
  fit <- lm(y ~ D, data = dat)

  p_ols  <- coef(summary(fit))["D", 4]
  p_hc1  <- coeftest(fit, vcov = vcovHC(fit, "HC1"))["D", 4]
  p_crve <- coeftest(fit, vcov = vcovCL(fit, cluster = ~g, type = "HC1"),
                     df = G - 1)["D", 4]                   # t_{G-1}
  ct_cr2 <- coef_test(fit, vcov = "CR2", cluster = dat$g)  # Satterthwaite dof
  p_cr2  <- ct_cr2$p_Satt[ct_cr2$Coef == "D"]
  p_wcb  <- suppressMessages(
    boottest(fit, param = "D", clustid = "g", B = B, type = "rademacher")$p_val
  )                                                        # null imposed by default

  c(OLS = p_ols, HC1 = p_hc1, `CRVE (t_{G-1})` = p_crve,
    `CR2 (BM)` = p_cr2, `Wild cluster BS` = p_wcb) < 0.05
}

run_cell <- function(G, rho) {
  set.seed(20240601 + G * 10 + round(rho * 100))
  reps <- replicate(M, sim_once(G, n_g, rho, beta1 = 0, B = B))  # estimators x M
  rate <- rowMeans(reps)
  tibble(G = G, rho = rho, estimator = names(rate),
         reject = rate, mcse = sqrt(rate * (1 - rate) / M))
}

results <- pmap_dfr(GRID, run_cell)

# Headline: empirical rejection rate at nominal 5% (rho = 0.3 cells), wide format.
size_tbl <- results |>
  mutate(estimator = factor(estimator,
           levels = c("OLS", "HC1", "CRVE (t_{G-1})", "CR2 (BM)", "Wild cluster BS"))) |>
  select(G, rho, estimator, reject) |>
  pivot_wider(names_from = estimator, values_from = reject) |>
  arrange(rho, G)

cat(sprintf("\nEmpirical rejection rate at nominal 5%%  (M = %d, B = %d, n_g = %d)\n",
            M, B, n_g))
cat(sprintf("Monte Carlo SE near 0.05 is about %.3f\n\n",
            sqrt(0.05 * 0.95 / M)))
print(as.data.frame(size_tbl), digits = 3)

write.csv(results, here("research-guides/standard-errors/scripts/se_monte_carlo_results.csv"),
          row.names = FALSE)
