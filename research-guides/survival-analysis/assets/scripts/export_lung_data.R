#' Export the survival::lung dataset for cross-language reproducibility
#'
#' Writes the built-in \code{survival::lung} dataset to CSV, untouched and
#' unrecoded, so that every language tab in this guide (R, Python, Stata,
#' Julia) reads byte-identical input data. Recoding of \code{status} (to
#' 0/1) and \code{sex} (to a labeled factor) happens downstream, in each
#' language's own chunk, so the exported file preserves the original
#' package encoding as the single common starting point.
#'
#' @return A data frame identical to \code{survival::lung}.
#'
#' @examples
#' lung_raw <- export_lung_data()
#'
#' @export
export_lung_data <- function() {
    data(lung, package = "survival")
    lung
}
