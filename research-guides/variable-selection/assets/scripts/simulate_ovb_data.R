#' Simulate data illustrating omitted variable bias
#'
#' Generates data in which C is a common cause of A and Y, satisfying both
#' conditions for omitted variable bias (C predicts Y conditional on A, and
#' C is associated with A). Used to demonstrate that the bias from omitting
#' C from a regression of Y on A equals exactly beta2 * delta1, and reused
#' for a Cinelli-Hazlett sensitivity analysis on the same fitted model.
#'
#' @param seed Integer. Random seed for reproducibility. Defaults to 123.
#' @param n Integer. Sample size. Defaults to 5000.
#'
#' @return A data frame with columns \code{A} (exposure), \code{C}
#'   (omitted confounder), and \code{Y} (outcome). The true effect of A on
#'   Y, adjusted for C, is 2; C's effect on both A (delta1) and Y (beta2)
#'   is 0.3.
#'
#' @examples
#' df <- simulate_ovb_data()
#'
#' @export
simulate_ovb_data <- function(seed = 123, n = 5000) {
    set.seed(seed)

    C <- rnorm(n)
    A <- 0.3 * C + rnorm(n)
    Y <- 2 * A + 0.3 * C + rnorm(n)

    data.frame(A, C, Y)
}
