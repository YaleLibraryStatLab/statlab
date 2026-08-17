#' Simulate data for demonstration
#'
#' Generates data illustrating a randomized instrument with imperfect
#' compliance, suitable for demonstrating first-stage, reduced-form, and
#' two-stage least squares (2SLS) estimation. The population includes
#' compliers (whose treatment status follows the instrument), always-takers
#' (who take treatment regardless of assignment), and never-takers (who
#' never take treatment regardless of assignment).
#'
#' @param seed Integer. Random seed for reproducibility. Defaults to 123.
#' @param n Integer. Sample size. Defaults to 2000.
#'
#' @return A data frame with columns \code{Y} (outcome), \code{D} (treatment
#'   received), \code{Z} (instrument, randomly assigned), and \code{X} (an
#'   observed covariate). The true treatment effect used to generate
#'   \code{Y} is 2.0.
#'
#' @examples
#' df <- simulate_iv_data()
#'
#' @export
simulate_iv_data <- function(seed = 123, n = 2000) {
    set.seed(seed)

    Z <- rbinom(n, 1, 0.5)
    X <- rnorm(n)

    always <- rbinom(n, 1, 0.05)
    never <- rbinom(n, 1, 0.10)

    D <- ifelse(always == 1, 1,
        ifelse(never == 1, 0, Z)
    )

    beta <- 2.0
    Y <- 1 + beta * D + 0.5 * X + rnorm(n)

    data.frame(Y, D, Z, X)
}
