simulate_insects <- function(plants, seed = 456) {
    set.seed(seed)

    n <- nrow(plants)
    farms <- levels(plants$farm)
    n_farms <- length(farms)

    # counts are on the log scale here, so an intercept of 1.2 corresponds to
    # roughly 3.3 insects on a reference plant before any other effects
    intercept <- 1.2
    beta_G2 <- 0.40
    beta_G3 <- -0.30
    beta_G4 <- 0.15
    beta_overhead <- 0.25
    beta_drip <- -0.50

    farm_re_sd <- 0.5
    farm_re <- rnorm(n_farms, mean = 0, sd = farm_re_sd)
    names(farm_re) <- farms

    # the negative binomial size parameter. small values mean strong
    # overdispersion, and 2 is small enough that a poisson fit will fail its
    # dispersion test loudly, which is the point of this dataset
    theta <- 2

    # structural zeros come from a farm-level pest management effect that we
    # never observe directly. drip farms are much more likely to have it, so
    # the zero-inflation is not uniform across the data
    zi_intercept <- -2.2
    zi_drip <- 1.50

    geno_effect <- ifelse(plants$genotype == "G2", beta_G2,
        ifelse(plants$genotype == "G3", beta_G3,
            ifelse(plants$genotype == "G4", beta_G4, 0)
        )
    )

    irr_effect <- ifelse(plants$irrigation == "overhead", beta_overhead,
        ifelse(plants$irrigation == "drip", beta_drip, 0)
    )

    eta <- intercept + geno_effect + irr_effect + farm_re[as.character(plants$farm)]
    mu <- exp(eta)

    # the count process itself, overdispersed relative to poisson
    counts <- rnbinom(n, size = theta, mu = mu)

    # and then the structural zeros layered on top. a plant drawn as a
    # structural zero has its count set to 0 regardless of what the count
    # process produced
    zi_eta <- zi_intercept + ifelse(plants$irrigation == "drip", zi_drip, 0)
    structural_zero <- rbinom(n, size = 1, prob = plogis(zi_eta))
    counts[structural_zero == 1] <- 0

    insects <- data.frame(
        farm = plants$farm,
        irrigation = plants$irrigation,
        genotype = plants$genotype,
        count = counts
    )

    insects
}
