simulate_plants <- function(seed = 123) {
    set.seed(seed)

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

    plants$genotype <- factor(plants$genotype, levels = c("G1", "G2", "G3", "G4"))
    plants$irrigation <- factor(plants$irrigation, levels = c("rainfed", "overhead", "drip"))
    plants$farm <- factor(plants$farm)

    plants
}
