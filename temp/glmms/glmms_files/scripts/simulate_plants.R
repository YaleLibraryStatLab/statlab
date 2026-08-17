#' Simulate plant survival data with farm-level clustering
#'
#' Generates a synthetic plant-level dataset for demonstrating generalized
#' linear mixed models (GLMMs) with a binary outcome. Plants are nested
#' within farms; each farm is randomly assigned one irrigation method
#' (rainfed, overhead, or drip), and each plant is randomly assigned one of
#' four genotypes (G1-G4). Survival is generated from a logistic model with
#' fixed effects for irrigation and genotype, plus a farm-level random
#' intercept, so that farms sharing an irrigation method still differ from
#' one another in overall survival probability.
#'
#' @param seed Integer. Random seed passed
#'
#' @return A data frame with one row per plant and the following columns:
#' \describe{
#'   \item{farm}{Factor with 25 levels (\code{"farm_1"} through
#'     \code{"farm_25"}), identifying the farm a plant belongs to.}
#'   \item{irrigation}{Factor with levels \code{"rainfed"},
#'     \code{"overhead"}, \code{"drip"} (in that order, with
#'     \code{"rainfed"} as the reference level). Constant within farm.}
#'   \item{genotype}{Factor with levels \code{"G1"}, \code{"G2"},
#'     \code{"G3"}, \code{"G4"} (in that order, with \code{"G1"} as the
#'     reference level). Varies plant-by-plant within a farm.}
#'   \item{survival}{Integer, \code{0} or \code{1}, indicating whether the
#'     plant survived.}
#' }
#'
#' @examples
#' plants <- simulate_plants()
#' head(plants)
#'
#' @export
simulate_plants <- function(seed = 123) {
    set.seed(seed)

    # simulation parameters
    n_farms <- 25
    plants_per_farm <- sample(80:100, n_farms, replace = TRUE)

    irrigation_types <- c("rainfed", "overhead", "drip")
    farm_irrigation <- sample(irrigation_types, n_farms, replace = TRUE)

    intercept <- 0.5
    beta_overhead <- 0.20
    beta_drip <- 0.80
    beta_G2 <- 0.50
    beta_G3 <- -0.75
    beta_G4 <- 0.20

    farm_re_sd <- 0.8
    farm_re <- rnorm(n_farms, mean = 0, sd = farm_re_sd)

    plant_list <- lapply(seq_len(n_farms), function(i) {
        n <- plants_per_farm[i]
        genotype <- sample(c("G1", "G2", "G3", "G4"), n, replace = TRUE)

        irr_effect <- switch(farm_irrigation[i],
            overhead = beta_overhead,
            drip = beta_drip,
            0
        )

        geno_effect <- ifelse(genotype == "G2", beta_G2,
            ifelse(genotype == "G3", beta_G3,
                ifelse(genotype == "G4", beta_G4, 0)
            )
        )

        eta <- intercept + irr_effect + geno_effect + farm_re[i]
        p <- plogis(eta)
        survival <- rbinom(n, size = 1, prob = p)

        data.frame(
            farm = paste0("farm_", i),
            irrigation = farm_irrigation[i],
            genotype = genotype,
            survival = survival
        )
    })

    plants <- do.call(rbind, plant_list)

    plants$genotype <- factor(plants$genotype,
        levels = c("G1", "G2", "G3", "G4")
    )
    plants$irrigation <- factor(plants$irrigation,
        levels = c("rainfed", "overhead", "drip")
    )
    plants$farm <- factor(plants$farm)

    plants
}
