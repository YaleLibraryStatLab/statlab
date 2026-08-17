#' Simulate data for a sharp regression discontinuity design
#'
#' Generates data mimicking a close-election setup for demonstrating sharp
#' regression discontinuity (RD) estimation. A running variable (margin of
#' victory for a hypothetical "high-education" candidate) determines
#' treatment deterministically at a cutoff of zero, and an outcome variable
#' (GDP growth) is constructed with both a smooth trend in the running
#' variable and a discontinuous jump at the cutoff. A predetermined lagged
#' outcome is also generated, intended for use in placebo/falsification
#' tests, and is constructed to have no jump at the cutoff by design.
#'
#' @param seed Integer. Random seed for reproducibility. Defaults to 123.
#' @param n Integer. Sample size. Defaults to 500.
#'
#' @return A data frame with columns \code{margin_victory} (numeric, the
#'   running variable, uniform on -100 to 100), \code{high_educ_win}
#'   (integer, 1 if \code{margin_victory >= 0} else 0, the treatment
#'   indicator), \code{gdp_growth} (numeric outcome, with a true jump of
#'   2.5 at the cutoff and a slope of 0.05 in the running variable), and
#'   \code{lagged_gdp_growth} (numeric, a predetermined outcome with the
#'   same slope but no discontinuity, for placebo testing).
#'
#' @examples
#' df <- simulate_rdd_data()
#'
#' @export
simulate_rdd_data <- function(seed = 123, n = 500) {
    set.seed(seed)
    library(magrittr)

    df <- data.frame(margin_victory = runif(n, -100, 100))

    df <- df %>%
        dplyr::mutate(high_educ_win = ifelse(margin_victory >= 0, 1, 0))

    df <- df %>%
        dplyr::mutate(
            gdp_growth = 5 + 0.05 * margin_victory + 2.5 * high_educ_win + rnorm(n, sd = 2.5),
            lagged_gdp_growth = 4.8 + 0.04 * margin_victory + rnorm(n, sd = 2.3)
        )

    df
}
