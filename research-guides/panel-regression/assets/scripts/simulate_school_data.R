simulate_school_data <- function(seed = 123, n_schools = 40, n_years = 12) {
    set.seed(seed)

    total_obs <- n_schools * n_years

    school_id <- rep(1:n_schools, each = n_years)
    year <- rep(1:n_years, times = n_schools)

    school_types <- sample(c("Public", "Private"),
        size = n_schools,
        replace = TRUE,
        prob = c(0.6, 0.4)
    )
    school_type <- rep(school_types, each = n_years)

    school_random_effects <- rnorm(n_schools, mean = 0, sd = 8)

    school_mean_funding <- rnorm(n_schools,
        mean = ifelse(school_types == "Private", 55, 45),
        sd = 12
    )
    funding_means <- rep(school_mean_funding, each = n_years)

    within_school_variation <- rnorm(total_obs, mean = 0, sd = 6)
    funding <- funding_means + within_school_variation

    within_effect <- 0.6
    between_effect <- 1.8
    school_type_effect <- 10

    test_scores <- 500 +
        rep(school_random_effects, each = n_years) +
        within_effect * (funding - funding_means) +
        between_effect * funding_means +
        school_type_effect * (school_type == "Private") +
        rnorm(total_obs, mean = 0, sd = 7)

    data.frame(
        school_id = as.factor(school_id),
        year = year,
        school_type = as.factor(school_type),
        funding = funding,
        test_score = test_scores
    )
}
