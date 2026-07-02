// Decision tree state machine + recommendation library
// Each step has options. Options either point to `next` (another step id) or `terminal` (recommendation id).

// ─── Glossary ────────────────────────────────────────────────────────────────

window.GLOSSARY = {
  cross_sectional: {
    term: "Cross-sectional data",
    definition: "One observation per unit (person, firm, country) at a single point in time. No repeated measures. The classic regression setting."
  },
  panel: {
    term: "Panel / longitudinal data",
    definition: "The same units observed at multiple time periods (e.g., states tracked annually, individuals surveyed each wave). Creates within-unit serial correlation that must be handled."
  },
  cluster: {
    term: "Cluster",
    definition: "A group of units that share a common sampling, assignment, or treatment unit — e.g., students in the same classroom, workers in the same firm, households in the same county. Units within a cluster are not independently drawn or treated."
  },
  exogenous: {
    term: "Exogenous treatment variation",
    definition: "Treatment variation that is independent of potential outcomes — as-good-as-randomly assigned. Arises from natural experiments, randomized trials, regression discontinuities, or instrumental variables. Contrast with endogenous selection."
  },
  endogenous: {
    term: "Endogenous / observational treatment",
    definition: "Treatment status is correlated with potential outcomes (selection bias). You observe who chose or received treatment, but that choice is not random. SEs capture within-model uncertainty only — not confounding bias."
  },
  crve: {
    term: "CRVE — Cluster-Robust Variance Estimator",
    definition: "The 'Liang–Zeger' sandwich estimator that allows arbitrary within-cluster correlation of residuals. Requires G → ∞ for consistency. Often called 'cluster SEs' or vcov(cluster=…)."
  },
  hc2_hc3: {
    term: "HC2 / HC3",
    definition: "Leverage-corrected heteroskedasticity-consistent variance estimators. Each weights observation i's squared residual by ωᵢ: 1 (HC0), n/(n−p) (HC1), 1/(1−hᵢᵢ) (HC2), 1/(1−hᵢᵢ)² (HC3), where hᵢᵢ is observation i's leverage. HC2 and HC3 outperform HC1 (the default 'robust') in small to moderate samples; use HC3 when N is small."
  },
  k_bm: {
    term: "K_BM — Bell-McCaffrey effective degrees of freedom",
    definition: "A coefficient- or contrast-specific Satterthwaite effective degrees of freedom diagnostic: K_BM = (Σλⱼ)² / Σλⱼ², where λⱼ are the weights/eigenvalues from the HC2 or CR2 variance quadratic form. Compare it to N − p in unclustered models and G − 1 in clustered models."
  },
  g_clusters: {
    term: "G — number of clusters",
    definition: "The number of independent sampling, assignment, or repeated-measure units used for clustered inference. All CRVE estimators require G → ∞ for consistency. Small G (10–20) requires explicit corrections; very small G (< 10) requires Webb bootstrap weights."
  },
  hac: {
    term: "HAC — Heteroskedasticity and Autocorrelation Consistent",
    definition: "A variance estimator (e.g., Newey-West) that accounts for both heteroskedasticity and serial autocorrelation in a pure time series. Uses kernel weights to downweight distant lags."
  },
  ccv_tscb: {
    term: "CCV / TSCB — Causal Cluster Variance / Two-Stage Cluster Bootstrap",
    definition: "Methods from Abadie-Athey-Imbens-Wooldridge (2023) that target design variance when the assignment mechanism is defensible, the sampling fraction is known or defensible, and treatment varies within clusters. TSCB is generally preferred in small samples."
  },
  two_way_crve: {
    term: "Two-way CRVE (Cameron–Gelbach–Miller)",
    definition: "Additive formula for two dimensions of dependence: V̂ = V̂_A + V̂_B − V̂_{A×B}. The intersection matrix V̂_{A×B} is a bias correction, not the estimator. Both G_A and G_B must individually be large enough for consistency."
  },
  moulton: {
    term: "Moulton factor",
    definition: "The variance inflation factor from within-cluster correlation of your key regressor (Moulton 1986). Even if residuals look uncorrelated within clusters, high covariate clustering (most variation in X is between clusters) dramatically inflates Type I error. Jackson (2019) shows covariate clustering — not residual clustering — is the key driver of CRSE bias."
  },
  rho_sampling: {
    term: "ρ — sampling fraction",
    definition: "The share of the target population you observe. When ρ → 1 (full population), ordinary sampling uncertainty shrinks and the remaining uncertainty depends on the estimand and assignment mechanism. When ρ ≈ 0 (small survey sample), standard sampling-based SE logic is appropriate."
  },
  convenience_sample: {
    term: "Convenience sample",
    definition: "A sample with no defined sampling frame — participants self-selected, were recruited ad hoc, or come from a platform (MTurk, etc.). No well-defined population exists, so SEs measure only within-model variation and generalization is not statistically justified."
  }
};

// ─── Steps ───────────────────────────────────────────────────────────────────

window.STEPS = {
  data_structure: {
    n: 1,
    short: "Data structure",
    title: "What is the structure of your data?",
    why: "Spatial and pure time-series data require different machinery and short-circuit the rest of the tree.",
    options: [
      {
        id: "cross",
        label: "Cross-sectional",
        desc: "One observation per unit at a single point in time.",
        next: "coverage",
        tooltip: ["cross_sectional"],
      },
      {
        id: "panel",
        label: "Panel / longitudinal",
        desc: "Same units observed across multiple periods.",
        next: "coverage",
        tooltip: ["panel"],
      },
      {
        id: "timeseries",
        label: "Pure time series",
        desc: "A single series tracked across time — macro aggregates, financial returns.",
        terminal: "hac",
        tooltip: ["hac"],
      },
      {
        id: "spatial",
        label: "Spatial / geographic",
        desc: "Observations indexed by location with possible spatial autocorrelation.",
        next: "spatial_structure",
      },
    ],
  },

  spatial_structure: {
    n: 2,
    short: "Spatial structure",
    title: "Is your spatial data a single cross-section or a spatial panel?",
    why: "Spatial panels carry BOTH cross-sectional spatial autocorrelation and within-unit serial correlation over time. De-trend spatially first, then handle the temporal dimension separately.",
    options: [
      {
        id: "spatial_cross",
        label: "Spatial cross-section",
        desc: "One observation per location at a single point in time.",
        terminal: "spatial",
      },
      {
        id: "spatial_panel",
        label: "Spatial panel",
        desc: "Locations observed over multiple periods.",
        terminal: "spatial",
        flag: "panel",
      },
    ],
  },

  coverage: {
    n: 2,
    short: "Population coverage",
    title: "How much of your target population do you observe?",
    why: "Sampling fraction (ρ) determines how much ordinary sampling uncertainty remains. With near-full coverage, the right variance depends on the estimand and assignment mechanism.",
    options: [
      {
        id: "random_sample",
        label: "Random sample from a large population",
        desc: "A simple random sample from a large population frame; sampling fraction is small.",
        next: "sampling",
        tooltip: ["rho_sampling"],
      },
      {
        id: "full_population",
        label: "Full or near-full population",
        desc: "All 50 states, all EU countries, all districts in a country — you observe the entire target population, so ρ → 1. (If you actually want to generalize to other periods or conditions, these are a sample from a superpopulation and this branch does not apply.)",
        next: "assignment_pop",
        tooltip: ["rho_sampling"],
      },
      {
        id: "convenience",
        label: "Convenience sample",
        desc: "No clear sampling frame; participants self-selected or were collected ad hoc.",
        terminal: "convenience",
        tooltip: ["convenience_sample"],
      },
    ],
  },

  sampling: {
    n: 3,
    short: "Sampling unit",
    title: "How was your sample drawn?",
    why: "If clusters were the sampling unit, the cluster (not the individual) is the unit of independent variation.",
    options: [
      {
        id: "individuals",
        label: "Random sample of individuals",
        desc: "Each unit was sampled independently from the population.",
        next: "assignment",
      },
      {
        id: "clusters",
        label: "Random sample of clusters, then units within",
        desc: "You sampled, e.g., 30 counties, then surveyed households inside each.",
        next: "assignment",
        flag: "sampled_clusters",
        tooltip: ["cluster"],
      },
      {
        id: "complex_survey",
        label: "Complex survey design (weights, strata, PSUs)",
        desc: "CPS, PSID, NHANES, DHS — a published sampling design with weights, stratification, and primary sampling units.",
        terminal: "survey_design",
        flag: "sampled_clusters",
      },
    ],
  },

  assignment: {
    n: 4,
    short: "Assignment mechanism",
    title: "How was treatment (or your key regressor) assigned?",
    why: "This is the most important question in the tree — it overrides residual-correlation diagnostics. Most practitioners skip it and reach for cluster SEs reflexively.",
    options: [
      {
        id: "rand_individual",
        label: "Randomly to individuals",
        desc: "A coin was flipped separately for each unit. Knowing a unit's cluster tells you nothing about its treatment probability.",
        terminal: "hc23",
        routes: [
          { ifAnyFlag: ["sampled_clusters", "panel"], next: "cluster_dimensions" },
        ],
        tooltip: ["exogenous"],
      },
      {
        id: "rand_cluster",
        label: "Randomly at the cluster level",
        desc: "All units in a cluster received the same assignment — a state passed a law, a classroom got a curriculum.",
        next: "cluster_dimensions",
        flag: "clustered",
        tooltip: ["cluster", "exogenous"],
      },
      {
        id: "partial",
        label: "Partially clustered",
        desc: "Treatment probability varies by cluster, but units within a cluster are not all treated identically (e.g., a within-block lottery, or randomized encouragement assigned at the individual level inside cluster-defined strata).",
        terminal: "ccv_tscb",
        tooltip: ["ccv_tscb"],
      },
      {
        id: "observational",
        label: "Observational — not assigned",
        desc: "Treatment was observed, not randomized. You must reason about why units differ.",
        next: "exogeneity",
        tooltip: ["endogenous"],
      },
    ],
  },

  exogeneity: {
    n: 5,
    short: "Treatment exogeneity",
    title: "Is there a plausible source of exogenous variation in treatment?",
    why: "Exogenous variation (natural experiments, DiD, IV, RD) puts you in the design-based framework — SEs measure causal uncertainty. Purely observational selection means SEs are a lower bound on total uncertainty, not a measure of causal variation.",
    options: [
      {
        id: "exogenous",
        label: "Yes — plausibly exogenous variation",
        desc: "DiD policy shock, regression discontinuity, instrumental variable, or other natural experiment isolates variation that is as-good-as-random.",
        next: "obs_level",
        flag: "exogenous",
        tooltip: ["exogenous"],
      },
      {
        id: "confounded",
        label: "No — endogenous / observational selection",
        desc: "Selection into treatment correlates with potential outcomes. No design element isolates exogenous variation.",
        next: "obs_level",
        flag: "observational_confounded",
        tooltip: ["endogenous"],
      },
    ],
  },

  obs_level: {
    n: 6,
    short: "Where treatment is determined",
    title: "At what level is treatment effectively determined?",
    why: "Cluster at the level where the treatment-generating decision actually happens — even if your outcome is measured on finer units.",
    options: [
      {
        id: "policy_level",
        label: "At a policy or jurisdiction level",
        desc: "Wage rules set by firm, policy set by state, curriculum chosen by school.",
        next: "cluster_dimensions",
        tooltip: ["cluster"],
      },
      {
        id: "individual_level",
        label: "At the individual unit level",
        desc: "Treatment differences arise from individual-specific factors, not group-level decisions.",
        terminal: "hc23_observational",
        routes: [
          { ifAnyFlag: ["sampled_clusters", "panel"], next: "cluster_dimensions" },
        ],
      },
    ],
  },

  assignment_pop: {
    n: 4,
    short: "Assignment mechanism",
    title: "How was treatment assigned?",
    why: "With near-full population coverage, ordinary sampling uncertainty is small. The remaining uncertainty depends on whether treatment was randomized, partially clustered, or observational.",
    options: [
      {
        id: "rand_individual",
        label: "Randomly to individuals",
        desc: "Independent assignment within the observed population.",
        terminal: "hc23_pop",
        routes: [
          { ifAnyFlag: ["panel"], next: "cluster_dimensions" },
        ],
        tooltip: ["exogenous"],
      },
      {
        id: "rand_cluster",
        label: "Randomly at the cluster level",
        desc: "Treatment shared by all units in each cluster.",
        terminal: "cluster_randomization_pop",
        tooltip: ["cluster"],
      },
      {
        id: "partial",
        label: "Partially clustered",
        desc: "Within-cluster assignment heterogeneity.",
        terminal: "ccv_tscb",
        tooltip: ["ccv_tscb"],
      },
      {
        id: "observational",
        label: "Observational",
        desc: "Treatment observed, not randomized.",
        terminal: "observational_full_pop",
        tooltip: ["endogenous"],
      },
    ],
  },

  cluster_dimensions: {
    n: 7,
    short: "Clustering dimensions",
    title: "Along how many dimensions does dependence run?",
    why: "Two-way dependence (e.g., panel by unit and by time, or workers by firm and by industry) requires an additive cluster-robust estimator — not the intersection, and not just one dimension.",
    options: [
      {
        id: "one_way",
        label: "Single dimension",
        desc: "Dependence runs along one grouping variable (e.g., state, firm, school).",
        next: "num_clusters",
        tooltip: ["cluster"],
      },
      {
        id: "two_way",
        label: "Two dimensions",
        desc: "Shocks correlated within units over time AND within cross-sectional groups in the same period (e.g., panel by firm and by year; patents cited by both citing-firm and technology-class; students clustered by both school and neighborhood when the two cross-cut).",
        terminal: "crve_twoway",
        flag: "twoway",
        tooltip: ["two_way_crve"],
      },
    ],
  },

  num_clusters: {
    n: 8,
    short: "Number of clusters",
    title: "How many clusters (G) do you have?",
    why: "All CRVE estimators require $G \\to \\infty$ for consistency. Small G needs explicit corrections — over-rejection and under-coverage are the rule, not the exception.",
    options: [
      {
        id: "large",
        label: "G > 50, reasonably balanced",
        desc: "Plenty of clusters; sizes within roughly an order of magnitude.",
        terminal: "crve_standard",
        tooltip: ["g_clusters", "moulton"],
      },
      {
        id: "medium",
        label: "20 < G ≤ 50",
        desc: "Mid-range. Standard CRVE likely under-covers.",
        terminal: "crve_cr2",
        tooltip: ["g_clusters", "k_bm"],
      },
      {
        id: "small",
        label: "10 ≤ G ≤ 20",
        desc: "Small-G regime — standard rejection rates can hit 8–12% at nominal 5%.",
        terminal: "crve_smallG",
        tooltip: ["g_clusters", "k_bm"],
      },
      {
        id: "tiny",
        label: "G < 10",
        desc: "Very few clusters. Discreteness in the bootstrap distribution becomes the binding constraint.",
        terminal: "crve_tinyG",
        tooltip: ["g_clusters"],
      },
    ],
  },
};

// ─── Recommendations ────────────────────────────────────────────────────────

window.RECS = {
  hc23: {
    headline: "HC2 or HC3 robust standard errors",
    tagline: "Heteroskedasticity-robust, no clustering.",
    body:
      "Treatment was assigned independently per unit, and no clustered sampling or repeated-measures structure was selected. Residual correlation by group is not, by itself, a clustering signal — it reflects covariate or outcome similarities that have no design basis for inflating SEs. Clustering here can inflate your standard errors substantially — by an order of magnitude when within-cluster covariate correlation is high — for no valid design reason (the Moulton inflation $\\sqrt{1+(\\bar n_g-1)\\rho_x\\rho_u}$; Abadie et al. 2023). The estimator is the Eicker–Huber–White sandwich $\\hat V = (X'X)^{-1}\\!\\left(\\sum_i \\omega_i\\,\\hat u_i^2\\, x_i x_i'\\right)\\!(X'X)^{-1}$ with $\\omega_i = 1/(1-h_{ii})$ for HC2 and $\\omega_i = 1/(1-h_{ii})^2$ for HC3, where $h_{ii}=x_i'(X'X)^{-1}x_i$ is leverage.",
    primary: "HC2 (or HC3 for small N) Eicker–Huber–White robust variance.",
    code: [
      ["R", "lmtest::coeftest(fit, vcov = sandwich::vcovHC(fit, type = \"HC2\"))"],
      ["Stata", "regress y x, vce(hc3)   // vce(robust) is HC1; use hc2 or hc3 explicitly"],
      ["Python", "import statsmodels.formula.api as smf\nfit = smf.ols('y ~ x', data=df).fit(cov_type='HC2')\nfit.summary()"],
    ],
    checks: [
      "Compute coefficient-specific Bell–McCaffrey/Satterthwaite DoF. If it is much smaller than $N-p$ (skewed design, few treated units), switch to Bell–McCaffrey CIs even with large N.",
      "Resist the heuristic that a large gap between robust and clustered SEs justifies clustering — here it usually means the cluster SE is the broken one.",
    ],
  },

  hc23_observational: {
    headline: "HC2/HC3 for within-model uncertainty — plus sensitivity analysis",
    tagline: "Individual-level observational treatment, no cluster mechanism selected.",
    body:
      "Treatment varies at the individual level and no clustered sampling, panel, or group-level treatment mechanism was selected. HC2/HC3 measures within-model sampling uncertainty, but it does not address confounding, selection, measurement error, or model misspecification.",
    primary: "HC2/HC3 robust variance for the regression; sensitivity analysis for any causal claim.",
    code: [
      ["R", "lmtest::coeftest(fit, vcov = sandwich::vcovHC(fit, type = \"HC2\"))"],
      ["Python", "fit = smf.ols('y ~ x', data=df).fit(cov_type='HC2')\nfit.summary()"],
    ],
    checks: [
      "Do not interpret the SE as causal uncertainty unless the identifying assumptions are defended separately.",
      "Report sensitivity analysis for confounding or selection, such as Oster's δ or Rosenbaum bounds when appropriate.",
      "If a sampling cluster, panel unit, or other dependence unit actually exists, revise the path and cluster at that design level.",
    ],
  },

  hc23_pop: {
    headline: "HC2/HC3 — and remember, EHW is conservative here",
    tagline: "Full population + individual-level assignment.",
    body:
      "If your estimand is the effect within this observed finite population, ordinary sampling uncertainty is essentially zero and the only remaining uncertainty is design-based: which potential outcome was revealed for each unit. (If instead you want to generalize to a broader superpopulation, sampling-type uncertainty does not vanish — treat this as a sampling problem, not a full-population one.) Under that design-based view, EHW robust SEs are generally conservative for the average treatment effect (Abadie, Athey, Imbens & Wooldridge 2020); they coincide with the design-based variance only when effects are constant.",
    primary: "HC2/HC3 as a conservative benchmark.",
    code: [
      ["R", "lmtest::coeftest(fit, vcov = sandwich::vcovHC(fit, type = \"HC2\"))"],
      ["Python", "fit = smf.ols('y ~ x', data=df).fit(cov_type='HC2')\nfit.summary()"],
    ],
    checks: [
      "If you have a strong design argument (assignment was random within strata), report design-based SEs alongside.",
      "Frame your inference language around counterfactual policy variation, not population sampling.",
      "If your data are a panel (units observed over time), do not stop at HC2/HC3 — serial correlation within units remains even at full population coverage. Cluster by the unit, or use the two-way path if time shocks also matter.",
    ],
  },

  ccv_tscb: {
    headline: "Causal Cluster Variance (CCV) or Two-Stage Cluster Bootstrap (TSCB)",
    tagline: "For defensible partial clustering with within-cluster treatment variation.",
    body:
      "Standard CRVE can be too conservative when you observe a large fraction of clusters; HC SEs can be too aggressive when assignment has cluster structure. CCV and TSCB target the actual design variance when the assignment mechanism is defensible, the sampling fraction is known or defensible, and treatment varies within clusters. TSCB is generally preferred — CCV degrades in small samples.",
    primary: "TSCB: resample cluster treatment fractions (Stage 1), then units within clusters (Stage 2), only when within-cluster treatment variation supports the design.",
    code: [
      ["R — closed form (runnable)", `# CCV (Causal Cluster Variance), Abadie-Athey-Imbens-Wooldridge (2023, QJE).
# Combine cluster-robust and heteroskedastic-robust variances, discounting the
# cluster term by the sampling fraction rho = fraction of each cluster's target
# population you observe (rho -> 1 means you nearly observe the whole cluster).
library(sandwich)
V_cluster <- vcovCL(fit, cluster = df$g)   # Liang-Zeger
V_robust  <- vcovHC(fit, type = "HC2")     # heteroskedastic-robust
V_ccv     <- V_robust + (1 - rho) * (V_cluster - V_robust)
se_ccv    <- sqrt(diag(V_ccv))[target]     # use t(G - 1) critical values`],

      ["Python — closed form (runnable)", `# CCV closed form, AAIW (2023). statsmodels gives both vcovs directly.
import numpy as np, statsmodels.formula.api as smf
fit_cl = smf.ols('y ~ x', data=df).fit(cov_type='cluster', cov_kwds={'groups': df['g']})
fit_hc = smf.ols('y ~ x', data=df).fit(cov_type='HC2')
rho    = 0.1   # fraction of each cluster's target population observed
V_ccv  = fit_hc.cov_params() + (1 - rho) * (fit_cl.cov_params() - fit_hc.cov_params())
se_ccv = np.sqrt(np.diag(V_ccv))[list(fit_hc.params.index).index('x')]  # t(G-1) crit vals`],

      ["R — TSCB pseudocode (NOT runnable)", `# Two-Stage Cluster Bootstrap, AAIW (2023, QJE). Conceptual sketch, not code.
# ASSUMPTION: sampling fraction rho per cluster is known or defensible.
#   rho ~ 0  -> behaves like standard cluster bootstrap (sampling uncertainty)
#   rho ~ 1  -> design uncertainty dominates; Stage-1 cluster resampling shrinks.
# Requires WITHIN-cluster treatment variation (treated AND control units per cluster).

theta_hat <- coef(fit_fun(df))[target]
clusters  <- unique(df$g)
G         <- length(clusters)

theta_star <- numeric(B)
for (b in 1:B) {
  # ---- STAGE 1: resample clusters (scaled by 1 - rho) ----
  drawn <- sample(clusters, size = G, replace = TRUE)

  boot_rows <- list()
  for (i in seq_along(drawn)) {
    g0      <- drawn[i]
    rows_g  <- df[df$g == g0, ]
    treated <- rows_g[rows_g$d == 1, ]
    control <- rows_g[rows_g$d == 0, ]

    # ---- GUARD: skip clusters with an empty treated or control cell ----
    if (nrow(treated) == 0 || nrow(control) == 0) next

    # ---- STAGE 2: resample units within the cluster, PRESERVING the split ----
    n_t <- nrow(treated); n_c <- nrow(control)
    samp_t <- treated[sample(n_t, n_t, replace = TRUE), ]
    samp_c <- control[sample(n_c, n_c, replace = TRUE), ]
    block  <- rbind(samp_t, samp_c)
    block$g_boot <- paste0("bootclust_", i)
    boot_rows[[length(boot_rows) + 1]] <- block
  }

  if (length(boot_rows) < 2) { theta_star[b] <- NA; next }

  boot          <- do.call(rbind, boot_rows)
  theta_star[b] <- coef(fit_fun(boot))[target]
}

theta_star <- theta_star[!is.na(theta_star)]
se_tscb    <- sd(theta_star)
ci_tscb    <- quantile(theta_star, c(0.025, 0.975))
# Reference: consult the AAIW (2023) QJE replication materials for an
# implementation; the algorithm above is enough to reproduce the method.`],

      ["Python — TSCB pseudocode (NOT runnable)", `# Two-Stage Cluster Bootstrap, AAIW (2023). Conceptual sketch, not code.
import numpy as np, pandas as pd

theta_hat = fit_fun(df)[target]
clusters  = df['g'].unique()
G         = len(clusters)
theta_star = []

for b in range(B):
    drawn = np.random.choice(clusters, size=G, replace=True)   # STAGE 1
    blocks = []
    for i, g0 in enumerate(drawn):
        rows_g  = df[df['g'] == g0]
        treated = rows_g[rows_g['d'] == 1]
        control = rows_g[rows_g['d'] == 0]
        if len(treated) == 0 or len(control) == 0:             # GUARD
            continue
        samp_t = treated.sample(len(treated), replace=True)     # STAGE 2
        samp_c = control.sample(len(control), replace=True)
        block  = pd.concat([samp_t, samp_c]); block['g_boot'] = f'bootclust_{i}'
        blocks.append(block)
    if len(blocks) < 2:
        continue
    theta_star.append(fit_fun(pd.concat(blocks))[target])

theta_star = np.array(theta_star)
se_tscb    = theta_star.std(ddof=1)
ci_tscb    = np.quantile(theta_star, [0.025, 0.975])`],
    ],
    checks: [
      "Do not use CCV/TSCB for cluster-constant treatment with no within-cluster treatment variation.",
      "State the assumed sampling fraction $q_k$ or explain why it is defensible.",
      "Report standard CRVE alongside as a (likely too-large) upper bound.",
      "If sample is small, compare CCV and TSCB; prefer TSCB.",
    ],
  },

  cluster_randomization_pop: {
    headline: "Finite-population cluster-randomization inference",
    tagline: "Full population + cluster-constant randomized assignment.",
    body:
      "Sampling uncertainty is essentially zero, and treatment is constant within each randomized cluster. CCV/TSCB is not the right default here because there is no within-cluster treatment variation. The variance target comes from the known or defensible assignment mechanism.",
    primary:
      "Use the design/randomization variance for the actual cluster assignment design. Under complete, blocked, or stratified cluster randomization, use the corresponding finite-population/randomization inference; report conservative cluster-level Neyman or CRVE-style benchmarks only as checks.",
    code: [
      ["R — design-based SE (cluster-level Neyman)", `# Aggregate to one value per cluster, then difference-in-means with the
# Neyman (conservative) cluster-level variance.
agg <- aggregate(y ~ cluster_id + z, data = df, FUN = mean)
yt  <- agg$y[agg$z == 1]; yc <- agg$y[agg$z == 0]
tau_hat   <- mean(yt) - mean(yc)
se_neyman <- sqrt(var(yt)/length(yt) + var(yc)/length(yc))   # conservative
ci <- tau_hat + c(-1, 1) * qt(0.975, df = length(yt) + length(yc) - 2) * se_neyman
# Design-aware alternative:
# estimatr::difference_in_means(y ~ z, blocks = block_id, clusters = cluster_id, data = df)`],

      ["R — CI by test inversion (randomization inference)", `# Invert the RI test over a grid; the CI is the set of tau0 NOT rejected at 5%.
library(ri2)
decl <- declare_ra(clusters = df$cluster_id, m = treated_clusters)
grid <- seq(-2, 2, by = 0.02)
keep <- sapply(grid, function(tau0) {
  df$y_adj <- df$y - tau0 * df$z
  out <- conduct_ri(y_adj ~ z, declaration = decl, assignment = "z",
                    sharp_hypothesis = 0, data = df)
  summary(out)$two_tailed_p_value > 0.05
})
ci_ri <- range(grid[keep])`],

      ["Python — no clean RI package; manual design-based SE", `import numpy as np, pandas as pd
agg = df.groupby(['cluster_id', 'z'])['y'].mean().reset_index()
yt = agg.loc[agg.z == 1, 'y'].values; yc = agg.loc[agg.z == 0, 'y'].values
tau_hat   = yt.mean() - yc.mean()
se_neyman = np.sqrt(yt.var(ddof=1)/len(yt) + yc.var(ddof=1)/len(yc))
# Test-inversion RI: loop tau0, permute cluster-level z under the actual design,
# recompute tau on y - tau0*z, keep tau0 not rejected at 5%.`],
    ],
    checks: [
      "Do not pick a universal variance formula without stating the assignment design.",
      "If assignment was not actually randomized or as-good-as-random, revise to the observational full-population case.",
      "If treatment varies within clusters, revise to the partial-clustering path for CCV/TSCB.",
    ],
  },

  crve_standard: {
    headline: "Cluster-robust SEs at the design level",
    tagline: "G > 50, balanced — the textbook case.",
    body:
      "Cluster at the level where the design creates independent units: treatment assignment, sampled cluster, or repeated-measures unit. Do not cluster at finer levels where errors merely look correlated, and do not cluster at the intersection of two dimensions. Use $t(G-1)$ critical values rather than the normal.",
    primary: "Liang–Zeger CRVE clustered at the relevant design level, $t(G-1)$ critical values.",
    code: [
      ["R", "fixest::feols(y ~ x | fe, cluster = ~ design_unit)"],
      ["Stata", "regress y x, vce(cluster design_unit)"],
      ["Python", "import statsmodels.formula.api as smf\nfit = smf.ols('y ~ x', data=df).fit(\n    cov_type='cluster', cov_kwds={'groups': df['design_unit']})\nprint(fit.summary())\n# Panel with entity FE: linearmodels.PanelOLS(..., cov_type='clustered', cluster_entity=True)"],
    ],
    checks: [
      "Inspect covariate clustering (Moulton factor): the share of your key regressor's variance falling between clusters. High covariate clustering even at G ≈ 50 can produce 6.5% rejection at nominal 5%.",
      "Run wild cluster bootstrap as a robustness check.",
      "If two-way dependence is plausible (panel by firm and by year), use additive two-way CRVE — never cluster at firm-year intersection.",
      "If your panel uses DiD with staggered rollout, two-way FE is biased for treatment effect heterogeneity. Consider Callaway-Sant'Anna or Sun-Abraham estimators before interpreting clustered SEs.",
      "With survey weights or WLS, use clubSandwich::coef_test() with CR2 rather than sandwich — standard CRVE is not consistent with non-constant weights.",
    ],
  },

  crve_cr2: {
    headline: "CR2 (Bell–McCaffrey) cluster-robust SEs",
    tagline: "20 < G ≤ 50 — small-sample correction is required.",
    body:
      "Standard CRVE under-covers in this range. The CR2 (Bell–McCaffrey) estimator pre-multiplies each cluster's residual vector $\\hat{\\mathbf{u}}_g$ (length $n_g$) by a cluster-specific symmetric matrix $\\mathbf{A}_g$: $\\tilde{\\mathbf{u}}_g = \\mathbf{A}_g\\hat{\\mathbf{u}}_g$, where $\\mathbf{A}_g$ satisfies $\\mathbf{A}_g(\\mathbf{I}_{n_g} - \\mathbf{H}_{gg})\\mathbf{A}_g = \\mathbf{I}_{n_g} - \\mathbf{H}_{gg}$ and $\\mathbf{H}_{gg} = \\mathbf{X}_g(\\mathbf{X}'\\mathbf{X})^{-1}\\mathbf{X}_g'$ is the cluster's block of the hat matrix. It reduces exactly to the HC2 weight $(1-h_{ii})^{-1/2}$ when each cluster is one observation. Inference uses $t$ with Bell–McCaffrey/Satterthwaite DoF, not $G-1$ blindly.",
    primary: "CR2 residual adjustment + $t(G-1)$ or Bell–McCaffrey DoF.",
    code: [
      ["R", "clubSandwich::coef_test(fit, vcov = \"CR2\", cluster = ~ design_unit)"],
      ["Stata", "* Stata does not provide a universal built-in CR2 path.\n* Use a validated CR2-capable package for your estimator,\n* or reproduce the result with R's clubSandwich::coef_test()."],
    ],
    checks: [
      "Run wild cluster bootstrap with Rademacher weights and the null imposed as a robustness check.",
      "Compute coefficient-specific Bell–McCaffrey/Satterthwaite DoF. If it is much smaller than $G-1$, your effective information is even thinner than nominal.",
      "Avoid pairs bootstrap — it can collapse silently when treated clusters are scarce.",
    ],
  },

  crve_smallG: {
    headline: "CR2 (Bell–McCaffrey/Satterthwaite DoF) + wild cluster bootstrap",
    tagline: "10 ≤ G ≤ 20 — over-rejection is severe without correction.",
    body:
      "In the cluster-randomization simulations summarized by Cameron & Miller (2015), standard CRVE can reject ~8% at nominal 5% near G ≈ 10, rising toward ~12% near G ≈ 6. Use CR2 with the Imbens–Kolesár modification — within-cluster correlation is estimated and folded into the effective DoF — and back it up with wild cluster bootstrap. In a DiD panel, nominal G is the total number of independent clusters, but the effective DoF for the treatment contrast can be close to the number of treated or switching clusters; compute BM/IK DoF or check with wild bootstrap/randomization inference.",
    primary: "CR2 with Bell–McCaffrey/Satterthwaite DoF; wild cluster bootstrap with Rademacher weights, null imposed.",
    code: [
      ["R", "clubSandwich::coef_test(fit, vcov = \"CR2\", cluster = ~ g)  # Satterthwaite (Bell-McCaffrey) DoF\nset.seed(1)  # fwildclusterboot >= 0.13 sets the seed globally\nfwildclusterboot::boottest(fit, clustid = \"g\", param = \"x\", B = 9999, impose_null = TRUE)"],
      ["Stata", "boottest x, cluster(g) reps(9999) weighttype(rademacher)"],
    ],
    checks: [
      "CIs will be wide. That is correct, not a failure.",
      "If you have heterogeneous treatment effects or unbalanced cluster sizes, expect further widening.",
      "Report CI alongside p-values — significance stars hide the uncertainty here.",
    ],
  },

  crve_tinyG: {
    headline: "Wild cluster bootstrap with Webb 6-point weights",
    tagline: "G < 10 — the bootstrap distribution itself becomes coarse.",
    body:
      "Rademacher weights $\\{\\pm 1\\}$ give $2^G$ weight vectors — 64 at G = 6 — but symmetry under the imposed null leaves only $2^{G-1} = 32$ distinct two-sided bootstrap statistics, and the attainable p-value grid is coarser still. Webb's 6-point distribution $\\{\\pm\\sqrt{1.5},\\, \\pm 1,\\, \\pm\\sqrt{0.5}\\}$ has $6^G$ draws and avoids discreteness artifacts. CESE (Jackson 2019) can be a useful optional reading/check when its covariance-structure assumptions fit the design.",
    primary: "Wild cluster bootstrap, Webb 6-point weights, null imposed.",
    code: [
      ["R", "fwildclusterboot::boottest(fit, clustid = \"g\", param = \"x\",\n  B = 9999, type = \"webb\", impose_null = TRUE)"],
      ["Stata", "boottest x, cluster(g) reps(9999) weighttype(webb)"],
    ],
    checks: [
      "Effective DoF will be very low. Wide CIs are honest, not a bug.",
      "Pairs bootstrap will fail silently here — Cameron & Miller show it collapses at G = 6 for DiD.",
      "Consider whether you can pool with related units to gain G; if not, lean into the CIs.",
    ],
  },

  crve_twoway: {
    headline: "Additive two-way cluster-robust SEs (Cameron–Gelbach–Miller)",
    tagline: "Two dimensions of dependence — additive formula, not intersection.",
    body:
      "Compute three separate CRVE matrices and combine: $\\hat{V} = \\hat{V}_A + \\hat{V}_B - \\hat{V}_{A \\times B}$. Never cluster at the intersection directly — $\\hat{V}_{A \\times B}$ in the formula is a bias-correction term, not the final estimator. Consistency is driven by the smaller of the two, i.e. $\\min(G_A,G_B)\\to\\infty$; each dimension having ~30+ groups is a rough adequacy guide. The number of intersection cells $G_{A \\times B}$ is typically large and is not what protects you — small $\\min(G_A,G_B)$ is the binding constraint.",
    primary: "$\\hat{V} = \\hat{V}_A + \\hat{V}_B - \\hat{V}_{A \\times B}$, with $t(\\min(G_A, G_B) - 1)$ critical values.",
    code: [
      ["R", "# fixest handles two-way clustering natively:\nfixest::feols(y ~ x | fe, cluster = ~ unit + time)\n\n# Or via lfe:\nlfe::felm(y ~ x | fe | 0 | unit + time)"],
      ["Stata", "reghdfe y x, absorb(fe) vce(cluster unit time)"],
    ],
    checks: [
      "Both $G_A$ and $G_B$ must individually be large enough (each > ~30). If one is small, the two-way CRVE inherits that dimension's small-G problem — use CR2 corrections.",
      "If $G_B = T$ (time periods) is small (e.g., T = 10 with large N), do not treat Driscoll–Kraay as a small-T fix. Consider whether time fixed effects, randomization inference, or design-specific robustness checks better match the design; use Driscoll–Kraay only for panels with enough time periods.",
      "Check that your two dimensions are genuinely crossed, not nested. If schools are nested within districts, cluster at the district level only — not two-way.",
      "Wild cluster bootstrap for two-way settings uses $\\min(G_A, G_B)$ as the effective cluster count.",
      "If your DiD uses staggered rollout, two-way FE is biased for heterogeneous treatment effects. See Callaway-Sant'Anna or Sun-Abraham before interpreting these SEs.",
    ],
  },

  hac: {
    headline: "Newey–West HAC standard errors",
    tagline: "Pure time series — autocorrelation up to bandwidth L.",
    body:
      "The sandwich is extended with kernel weights to absorb autocovariance. Bandwidth choice is not innocent — estimates can shift meaningfully across reasonable lag lengths even at large T.",
    primary: "Newey–West with Bartlett or Quadratic Spectral kernel; report robustness across bandwidths.",
    code: [
      ["R", "lmtest::coeftest(fit, vcov = sandwich::NeweyWest(fit, lag = floor(0.75 * nobs(fit)^(1/3)), prewhite = FALSE))"],
      ["Stata", "newey y x, lag(L)"],
      ["Python", "fit = smf.ols('y ~ x', data=df).fit(cov_type='HAC', cov_kwds={'maxlags': L})\nfit.summary()"],
    ],
    checks: [
      "Two common deterministic rules differ: the Newey–West (1994) plug-in-free $L = \\lfloor 4(T/100)^{2/9} \\rfloor$ and the rate-optimal $\\lfloor 0.75 \\cdot T^{1/3} \\rfloor$; they can give materially different $L$, so report sensitivity.",
      "Quadratic Spectral with Andrews (1991) data-driven bandwidth is a strong alternative.",
      "HAC does not fix nonstationarity or misspecified dynamics; Driscoll–Kraay is not a generic small-T panel fix.",
      "If two-way dependence exists (panel + time), use Driscoll–Kraay rather than HAC.",
    ],
  },

  spatial: {
    headline: "De-trend with a spatial basis, then BCH or Conley SEs",
    tagline: "Geographic data — the SE correction matters less than the de-trending.",
    body:
      "Conley & Kelly (2025) document that with conventional standard errors, ~38% of regressions of one spatial-noise variable on another yield |t| > 2 — versus the 5% a valid test would give — once realistic spatial autocorrelation is present. Standard HC SEs are severely anti-conservative. The first move is not a different SE — it's adding a spatial basis as controls.",
    primary:
      "Step 1: de-trend with a 2-D spatial smooth — `mgcv::te(lat, lon)` is the simplest correct route (or principal components of a row-wise tensor-product B-spline, selected by BIC). Step 2: BCH cluster-robust SEs on ~4–6 k-medoids partitions, or Conley SEs with a defended cutoff.",
    code: [
      ["R — mgcv tensor smooth (recommended)", `# Step 1: de-trend with a 2-D spatial smooth; df/penalty chosen by REML/BIC.
library(mgcv)
fit <- gam(y ~ x + te(lat, lon, k = 10), data = d, method = "REML")
# te() builds the row-wise tensor-product basis correctly and penalizes wiggliness.
# Step 2: few-cluster-robust spatial SEs on k-medoids partitions.
g <- cluster::pam(cbind(d$lat, d$lon), k = 6)$clustering
clubSandwich::coef_test(fit, vcov = "CR2", cluster = g)`],

      ["R — manual tensor basis + explicit BIC", `# Build a ROW-WISE tensor product, not %x% (Kronecker).
library(splines)
Blat <- bs(d$lat, df = K); Blon <- bs(d$lon, df = K)
B <- do.call(cbind, lapply(seq_len(ncol(Blat)), function(j) Blat[, j] * Blon))
pc <- prcomp(B, scale. = TRUE)
bic <- sapply(seq_len(ncol(pc$x)), function(k)
         BIC(lm(d$y ~ d$x + pc$x[, 1:k, drop = FALSE])))
k_bic <- which.min(bic)
fit <- lm(y ~ x + pc$x[, 1:k_bic], data = d)
g <- cluster::pam(cbind(d$lat, d$lon), k = 6)$clustering
clubSandwich::coef_test(fit, vcov = "CR2", cluster = g)`],

      ["Python — spline de-trend + Conley/HAC", `import numpy as np, pandas as pd, statsmodels.formula.api as smf
from patsy import dmatrix
B = dmatrix("bs(lat, df=5):bs(lon, df=5)", d, return_type="dataframe")
Xd = pd.concat([d[['y','x']].reset_index(drop=True), B.reset_index(drop=True)], axis=1)
fit = smf.ols("y ~ x + " + " + ".join(B.columns.map(lambda c: f'Q("{c}")')), data=Xd).fit()
# Step 2: Conley/Kelejian-Prucha spatial HAC via spreg, or k-medoids cluster SEs.`],

      ["Stata — Conley via acreg", `* ssc install acreg
acreg y x, lat(lat) lon(lon) dist(500) spherical
* Add spatial controls (polynomials in lat/lon) before acreg for de-trending.`],
    ],
    checks: [
      "Run a placebo test: de-trend treatment, simulate synthetic treatments with the same spatial structure, compare your t-stat to the reference distribution.",
      "Start at 6 BCH clusters; reduce to 4 if the placebo rejection rate exceeds 8%.",
      "With ~4 clusters, the effective 5% critical value is closer to 3.2 than 1.96. Wide CIs are expected.",
      "Conley SEs require a defended cutoff distance — report robustness across cutoffs.",
      "For spatial panel data: de-trend spatially first, then address temporal serial correlation within units using cluster SEs by unit rather than Conley SEs alone.",
    ],
  },

  convenience: {
    headline: "SEs are a lower bound — address systematic uncertainty",
    tagline: "Convenience sample, no clear population.",
    body:
      "Any SE you compute reflects within-model variation only. With no sampling frame, measurement error and selection bias dominate, and more data will not fix them (Gelman 2023). Reporting an SE without acknowledging this is misleading.",
    primary:
      "Report HC2/HC3 as a within-model lower bound; pair it with explicit discussion of selection, measurement, and external validity.",
    code: [
      ["R", "lmtest::coeftest(fit, vcov = sandwich::vcovHC(fit, type = \"HC2\"))"],
      ["Python", "fit = smf.ols('y ~ x', data=df).fit(cov_type='HC2')\nfit.summary()"],
    ],
    checks: [
      "Add sensitivity analysis: how badly would selection bias have to be for your finding to flip?",
      "Avoid significance language. Report effect sizes and CIs as descriptive of this sample only.",
      "Be explicit about generalization target — or its absence.",
      "If the convenience sample still has internal grouping (students in shared classrooms, repeated platform/batch IDs), cluster at that level instead of HC2/HC3. HC2/HC3 is a floor, not a ceiling.",
    ],
  },

  survey_design: {
    headline: "Survey-design (Horvitz–Thompson) variance estimation",
    tagline: "Published complex survey with weights, strata, and PSUs.",
    body:
      "When the data come from a documented probability sample (CPS, PSID, NHANES, DHS), inference must use the survey design: probability weights, stratification, and primary sampling units. Plain HC or one-way cluster SEs ignore stratification (which shrinks variance) and unequal weighting (which can inflate or deflate it). Use a survey-design variance estimator with the published design variables.",
    primary:
      "Taylor-linearization or replicate-weight variance using the survey's weight, strata, and PSU variables. Do not substitute ad hoc clustering for the documented design.",
    code: [
      ["R", `library(survey)
des <- svydesign(ids = ~psu, strata = ~stratum, weights = ~wt, data = df, nest = TRUE)
fit <- svyglm(y ~ x, design = des)
summary(fit)   # design-based SEs`],
      ["Stata", `svyset psu [pweight = wt], strata(stratum)
svy: regress y x`],
      ["Python", `# statsmodels has limited complex-survey support; use samplics for full
# Taylor-linearization / replicate-weight variance.
from samplics.estimation import TaylorEstimator
est = TaylorEstimator(parameter="mean")
est.estimate(df["y"], samp_weight=df["wt"], stratum=df["stratum"], psu=df["psu"])
# Regression with survey weights: statsmodels WLS gives point estimates but NOT
# design-correct SEs; prefer R survey or Stata svy.`],
    ],
    checks: [
      "Use the design's own replicate weights (BRR/jackknife) when supplied — they encode confidentiality-protected design detail linearization cannot.",
      "Stratification typically REDUCES variance; ignoring it makes SEs too large. Clustering/PSUs typically INCREASE it. The net effect is the design effect (DEFF) — report it.",
      "Subpopulation analysis must use svyby / subpop options, not a filtered dataset — dropping rows breaks the variance estimator.",
      "If you only have weights (no strata/PSU), weighted regression with HC SEs is a fallback, but state that you could not use the full design.",
    ],
  },

  observational_full_pop: {
    headline: "No single SE fixes full-population observational uncertainty",
    tagline: "Near-census data, treatment observed rather than assigned.",
    body:
      "When you observe the full finite population, descriptive sampling uncertainty may be close to zero. But for observational causal claims, standard errors remain a lower bound because confounding, selection, measurement error, and model choice dominate. For predictive or superpopulation claims, uncertainty depends on the generalization model you are willing to defend.",
    primary:
      "Report HC2/HC3 or design-level clustered SEs only as within-model uncertainty; pair them with explicit estimand language and sensitivity analysis. Do not use CCV/TSCB unless a defensible assignment mechanism and within-cluster treatment variation are present.",
    code: [
      ["R", "lmtest::coeftest(fit, vcov = sandwich::vcovHC(fit, type = \"HC2\"))"],
      ["Python", "fit = smf.ols('y ~ x', data=df).fit(cov_type='HC2')\nfit.summary()"],
    ],
    checks: [
      "State whether the estimand is descriptive for the finite population, causal for those units, or predictive for a broader population.",
      "For causal language, report sensitivity analysis for confounding and model misspecification.",
      "If treatment was actually assigned by a known policy or randomized mechanism, revise the path to the corresponding design-based branch.",
    ],
  },
};

// ─── Universal addenda based on flags collected during the walk ──────────────

window.ADDENDA = {
  panel: {
    title: "Panel-data note",
    body:
      "Cluster by the unit whose treatment status changes over time (e.g., state), not by unit × time. Bertrand–Duflo–Mullainathan (2004) showed that intersection clustering misses serial correlation within units across years and severely over-rejects nulls. If two-way dependence is plausible, use additive two-way CRVE ($\\hat{V}_{\\mathrm{unit}} + \\hat{V}_{\\mathrm{time}} - \\hat{V}_{\\mathrm{unit}\\times\\mathrm{time}}$). The within and LSDV (dummy-variable) estimators are algebraically equivalent for the coefficients; what matters for small clusters is the variance/degrees-of-freedom correction, so make sure your software applies the cluster $G-1$ adjustment.",
  },
  sampled_clusters: {
    title: "Sampled-clusters note",
    body:
      "Because clusters were the sampling unit, the cluster is your unit of independent variation — even if treatment is also at the cluster level, or finer. If sampling and assignment are at different levels, cluster at whichever is coarser. If the design includes survey weights, strata, or PSUs, use a survey-design variance estimator rather than treating this as simple clustered sampling.",
  },
  k_bm: {
    title: "Check effective degrees of freedom",
    body:
      "Compute coefficient-specific Bell–McCaffrey/Satterthwaite effective DoF: $K_{BM} = (\\sum_j \\lambda_j)^2 / \\sum_j \\lambda_j^2$, where $\\lambda_j$ come from the HC2/CR2 variance quadratic form for the target coefficient or contrast. Compare it to $N-p$ for unclustered models and to $G-1$ for clustered models. If it is much smaller, use Bell–McCaffrey CIs regardless of raw N or nominal G.",
  },
  exogenous: {
    title: "Exogenous design — design-based uncertainty",
    body:
      "Your SEs quantify uncertainty about the causal effect of the policy or assignment mechanism, not just within-model variation. Cluster at the level of the design element (the policy, the RD threshold jurisdiction, the IV instrument source). Design-based variance is the right conceptual frame: you are asking what would happen if the assignment had gone differently, not if you had drawn a different sample.",
  },
  observational_confounded: {
    title: "Confounded observational study — SEs are a lower bound",
    body:
      "Standard errors capture within-model sampling uncertainty but not confounding bias or model misspecification. Report SEs and CIs, but be explicit that they do not measure causal uncertainty. Sensitivity analysis — e.g., Oster's δ for coefficient stability, or Rosenbaum bounds for binary treatment — is essential here and should accompany any causal claim.",
  },
};
