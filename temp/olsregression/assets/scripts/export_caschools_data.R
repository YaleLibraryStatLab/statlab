#' Export the AER::CASchools dataset
#'
#' Writes the built-in \code{AER::CASchools} dataset to CSV, untouched,
#' so the guide's examples read from a stable, version-controlled file
#' rather than depending on the AER package being installed and loaded
#' at render time.
#'
#' @return A data frame identical to \code{AER::CASchools}.
#'
#' @examples
#' caschools_raw <- export_caschools_data()
#'
#' @export
export_caschools_data <- function() {
    data("CASchools", package = "AER")
    CASchools
}
