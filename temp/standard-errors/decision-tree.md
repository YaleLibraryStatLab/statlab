# A Practitioner's Decision Tree for Choosing Standard Errors

---

## The Right Mental Model

Most practitioners approach standard errors the wrong way. They run a regression, notice that residuals look correlated within some grouping, and reach for clustered SEs. This is backwards.

The correct approach starts *before* you look at residuals. The right standard error is determined by two things that are fixed by your research design:

1. **How your sample was drawn** (the sampling mechanism)
2. **How treatment — or your key variable — was assigned** (the design mechanism)

Residual correlation is a symptom, not the cause. Diagnosing the cause is what lets you choose correctly. The practical consequence: two studies with identical residual correlation patterns may need completely different standard errors depending on how the data were generated.

Work through the steps below in order. Each step narrows your options. Most practitioners can stop by Step 5.

---

## Quick Reference

```
Is your data geographic/spatial? ──────────────────────────────► Step 8 (Spatial)
Is your data pure time series? ────────────────────────────────► Step 7 (HAC)

Otherwise:

1. What are you estimating, and for whom?
   Full population observed (all states, all countries)? ──────► Design-based inference;
                                                                  CCV/TSCB only for partial within-cluster treatment
   Small random sample? ──────────────────────────────────────► Continue

2. How was your sample drawn?
   Random sample of clusters? ────────────────────────────────► Cluster at sampling level, then ↓
   Random sample of individuals? ─────────────────────────────► Continue

3. How was treatment assigned? [MOST IMPORTANT]
   Random to individuals + no prior cluster/panel structure ───► HC2/HC3; do NOT cluster
   Random to individuals + sampled clusters/panel ─────────────► Cluster at sampling/repeated unit
   Random to clusters ─────────────────────────────────────────► Cluster at assignment level → Step 5
   Partially clustered ────────────────────────────────────────► CCV or TSCB
   Observational, policy-level ────────────────────────────────► Cluster where treatment is determined → Step 5
   Observational, individual-level only ───────────────────────► HC2/HC3 lower bound + sensitivity

4. At what level should you cluster?
   Primary: assignment, sampling, or repeated-measures unit
   Multi-dimensional: two-way CRVE (not intersection)
   DiD panel: cluster by unit, not unit × time

5. How many clusters (G)?
   G > 50, balanced ───────────────────────────────────────────► Standard CRVE, t(G-1)
   20 < G ≤ 50 ────────────────────────────────────────────────► CR2 + t(G-1); consider wild bootstrap
   10 ≤ G ≤ 20 ────────────────────────────────────────────────► CR2 + Bell-McCaffrey DoF; wild bootstrap
   G < 10 ─────────────────────────────────────────────────────► Wild bootstrap, Webb 6-point weights

6. Is your design balanced? Compute K_BM.
   K_BM ≈ N-p (or G-1) ────────────────────────────────────────► Standard SEs more reliable
   K_BM much smaller ──────────────────────────────────────────► Bell-McCaffrey CIs regardless of raw N/G
```

---

## Step 1: What Are You Estimating, and for Whom?

Be explicit about your estimand and your generalization target before anything else. These determine what *uncertainty* even means in your setting.

**What is your estimand?**

- **Descriptive:** You want to describe a pattern in your data without a causal claim. Uncertainty comes entirely from *sampling* — which units you happened to observe.
- **Causal (sample):** You want to estimate a treatment effect for the units in your sample. Uncertainty comes from *design* — which potential outcome was revealed for each unit.
- **Causal (population):** You want to generalize a treatment effect to a broader population. Uncertainty comes from *both* sampling and design.

**What fraction of the target population do you observe?**

This question has a surprising answer in many applied settings.

| Your data | What it implies |
|-----------|-----------------|
| Random sample from a large population (CPS, PSID, survey data) | Standard sampling uncertainty applies. EHW robust SEs are appropriate at baseline. |
| All or most units in a finite population (all 50 states, all EU countries, all districts in a country) | Ordinary sampling uncertainty approaches zero. Remaining uncertainty depends on the estimand and assignment mechanism: design/randomization uncertainty for a defensible policy counterfactual, within-model lower bounds for observational causal claims, and model-based uncertainty for predictive targets. |
| Convenience sample with no clear population | SEs are a lower bound on full uncertainty. Systematic or measurement error may dominate, and more data won't fix it (Gelman 2023). |

**Why this matters:** If you have data on all 50 US states, treating your regression as a sample from an infinite population is usually the wrong starting point. For a causal finite-population estimand, the remaining uncertainty is about the counterfactual assignment. For descriptive or predictive targets, the right uncertainty statement depends on the population or model you are willing to defend.

---

## Step 2: How Was Your Sample Drawn?

**Random sample of individuals from a large population**

Each unit was sampled independently. Sampling uncertainty is the dominant story. EHW robust SEs (HC2 or HC3) are your baseline. Continue to Step 3 to check the assignment mechanism.

**Random sample of clusters, then individuals within clusters**

Example: you sampled 30 counties, then surveyed households within each county. Even with random individual sampling within clusters, the *cluster* was your sampling unit. You need to account for this. Cluster at the sampling level. Then apply Step 3 — if treatment is also clustered, cluster at whichever level is coarser.

**You observe the full population or a large fraction of it (sampling fraction ρ → 1)**

Sampling uncertainty shrinks toward zero as coverage increases. At ρ = 1, the remaining uncertainty depends on the estimand and design. For a known randomized or as-good-as-random assignment mechanism, use the corresponding design/randomization variance. For partial within-cluster treatment variation with a defensible assignment mechanism, consider the Causal Cluster Variance (CCV) estimator or Two-Stage Cluster Bootstrap (TSCB). For observational causal claims, SEs are only within-model lower bounds unless confounding and model uncertainty are addressed separately.

---

## Step 3: How Was Treatment Assigned?

This is the most important question, and the one most often skipped. It overrides residual-based diagnostics.

**Random assignment to individuals**

Each unit was independently assigned to treatment or control.

→ **Use HC2/HC3 robust SEs. Do not cluster.**

The intuition: if a coin was flipped separately for each person, knowing someone's state tells you nothing about their treatment probability. Clustering by state here can inflate your SEs by 20× or more — for no valid reason. The common "if clustering matters, cluster" heuristic is backwards: a large gap between cluster SEs and robust SEs in this setting means cluster SEs are too conservative, not that robust SEs are wrong.

**Random assignment at the cluster level (all units in a cluster receive the same treatment)**

Example: a state passes a law; all residents of that state are "treated." A classroom is randomized to a curriculum; all students in that classroom receive it.

→ **Cluster at the level of treatment assignment.**

The level of treatment assignment — not the level where residuals happen to look correlated — is what determines the correct clustering unit. Continue to Steps 4 and 5 for implementation.

**Partially clustered assignment**

Treatment probability varies by cluster, but not every unit within a cluster is treated identically (e.g., lottery within geographic blocks, or judges assigned to defendants where judge assignment varies within courthouse).

→ **Consider CCV or TSCB rather than standard cluster SEs.** TSCB is generally preferred because CCV degrades with small samples.

**Observational study — no random assignment**

Treatment is observed, not assigned. You cannot determine the uncertainty structure from the assignment mechanism alone. You need to reason about *why* units received different treatments and what correlations that creates.

→ **Cluster at the level where treatment is effectively determined.** If a policy was set at the state level, cluster by state even if treatment is measured on individuals. If firms set wages, cluster by firm even if you have worker-level outcomes.

Continue to Steps 4 and 5 for level and implementation.

---

## Step 4: At What Level Should You Cluster?

Assuming you've concluded clustering is appropriate, the question is now which level.

**Primary rule: cluster at the level of treatment assignment.**

If a wage subsidy was offered at the firm level, cluster at the firm level even though your outcome is on workers. If a judge is randomly assigned to defendants, do *not* cluster at the judge level — clustering inflates SEs with no design justification.

**Secondary rule: cluster broadly enough that both your key regressor and the errors are correlated within the same unit.**

If your regressor varies only at the state level but you're clustering at the county level, you're under-clustering relative to where regressor variation actually lives. When in doubt, a coarser level captures more correlation — but see the anti-patterns section for why "coarser is always safer" is wrong.

**Multi-way clustering (two or more dimensions of dependence):**

Example: panel data where errors correlate within firms over time *and* across firms within each year.

- Use two-way CRVE: V̂ = V̂_firm + V̂_year − V̂_{firm×year}
- **Do not cluster at the intersection** (e.g., firm-year). That misses serial correlation within firms and cross-sectional correlation within years.
- Two-way CRVE is not guaranteed to be positive semi-definite — it can produce negative variance estimates. If this happens, use the Cameron-Gelbach-Miller (2011) adjustment or a design-appropriate alternative such as Driscoll-Kraay when the panel is long enough for its assumptions.

**DiD designs with staggered treatment:**

- Cluster by the unit whose treatment status changes over time (e.g., state), not by state-year.
- Bertrand, Duflo & Mullainathan (2004) showed that clustering at the state-year level in DiD misses serial correlation within states across years, producing severely over-rejected nulls.

---

## Step 5: How Many Clusters Do You Have?

All CRVE estimators require G → ∞ for consistency. Small G requires corrections.

**G > 50, reasonably balanced cluster sizes:**

Standard CRVE with t(G−1) critical values is adequate. Still worth checking *covariate clustering* — the share of your key regressor's variance that falls between clusters rather than within. High covariate clustering with few clusters is the worst-case scenario for CRVE. Cameron & Miller (2015) document that even G=51 can show 6.5% rejection rates at a nominal 5% threshold.

**20 < G ≤ 50:**

Standard CRVE likely under-covers. Prefer:
- CR2 (Bell-McCaffrey) residual adjustment: replace ûg with [I − Hgg]^{−1/2} ûg to reduce small-sample bias
- t(G−1) degrees of freedom rather than normal critical values
- In R: `clubSandwich::coef_test()` with `vcov = "CR2"`; in Stata: `xttest3` or third-party packages

Run wild cluster bootstrap as a robustness check.

**10 ≤ G ≤ 20:**

CRVE rejection rates can substantially exceed nominal levels: G=10 → ~8% at nominal 5%; G=6 → ~12%.

Use CR2 with the Imbens-Kolesár (IK) modification: estimate within-cluster correlation ρ̂ using random effects and incorporate it into the effective degrees-of-freedom calculation. This is available in `clubSandwich` in R. In DiD and event-study settings, nominal G is the total number of independent clusters, but the effective information for the treatment contrast can be much closer to the number of treated or switching clusters.

Alternatively, use the **wild cluster bootstrap** (more below in Step 9). Wild bootstrap outperforms pairs bootstrap in almost all few-cluster scenarios.

**G < 10:**

Use Webb's 6-point weight distribution {±√1.5, ±√1, ±√0.5} for the wild bootstrap instead of Rademacher weights. Rademacher {−1, +1} has too few possible bootstrap distributions at very small G, causing discreteness problems.

Effective degrees of freedom will be very low. Confidence intervals will be wide. This is correct, not a failure — it accurately reflects that you have very little information about between-cluster variance.

Consider also CESE (Jackson 2019), which directly estimates the within-cluster error covariance structure via method-of-moments. CESE consistently outperforms CRSE and cluster bootstrap in accuracy and reproducibility at small G.

**Unbalanced clusters:**

Nominal G overstates effective G when cluster sizes vary widely. A few very large clusters dominate inference and make the effective G much smaller than it looks. Apply small-G corrections based on effective G, not nominal G. Carter et al.'s G* = G/(1 + δ) gives a usable estimate.

---

## Step 6: Is Your Design Balanced? The K_BM Diagnostic

Even with many observations, a highly imbalanced design behaves like a small sample for inference purposes.

**Compute coefficient-specific Bell-McCaffrey/Satterthwaite effective degrees of freedom:**

$$K_{BM} = \frac{\left(\sum_i \lambda_i\right)^2}{\sum_i \lambda_i^2}$$

where the λᵢ are the weights/eigenvalues from the HC2 or CR2 variance quadratic form for the coefficient or contrast being tested. Compare the result to N−p for unclustered models and to G−1 (or S−1) for clustered models. In practice, `clubSandwich` in R reports Satterthwaite degrees of freedom for CR2 tests.

| K_BM relative to N−p or G−1 | What it signals | What to do |
|----------------------|-----------------|------------|
| K_BM close to nominal df | Balanced design; adequate information | Standard EHW/LZ CIs are more reliable |
| K_BM noticeably smaller than nominal df | Skewed design (e.g., few treated units, unbalanced groups) | Switch to Bell-McCaffrey CIs |
| K_BM ≈ 2–5 | Extreme skew (3 treated clusters, 90/10 treatment split) | BM CIs; EHW severely under-covers |

**The key insight:** N=500 with 3 treated units gives K_BM ≈ 2. Adding more control units doesn't fix this. The diagnostic is about effective information for estimation, not raw sample size. Design skewness — not N — is the operative criterion.

When K_BM is small, use Bell-McCaffrey CIs or impose the null in your wild cluster bootstrap.

---

## Step 7: Temporal Correlation

**Panel data — within-unit serial correlation:**

After clustering by unit, errors may still be autocorrelated *within unit over time*. For DiD and related designs, cluster by unit (not unit × time) to capture this. For long panels (large T relative to G), consider HAC-type corrections within clusters or Driscoll-Kraay SEs.

**Pure time series:**

Use HAC (Newey-West) standard errors. The sandwich formula is extended with kernel weights to account for autocorrelation up to bandwidth L:

$$\hat{V}_{HAC} = (X'X)^{-1}\left(\hat{\Gamma}_0 + \sum_{j=1}^{L} w_j(\hat{\Gamma}_j + \hat{\Gamma}_j')\right)(X'X)^{-1}$$

where $\hat{\Gamma}_j = \sum_{t=j+1}^{T} x_t x_{t-j}' \hat{e}_t \hat{e}_{t-j}$.

Bandwidth choice matters and is not innocent — estimates can differ meaningfully across reasonable lag selections even in large samples. Common rules of thumb:
- Bartlett kernel: L = floor(4(T/100)^{2/9}) or L = floor(0.75 T^{1/3})
- Quadratic Spectral kernel: data-driven bandwidth via Andrews (1991)

Always check robustness to bandwidth choice and report it.

**Two-way dependence (within-unit and within-period):**

Use two-way CRVE (cluster on unit and on time period separately) or Driscoll-Kraay SEs, which handle both cross-sectional and time-series dependence nonparametrically.

---

## Step 8: Spatial Correlation

Spatial data require special treatment. Standard HC and small-cluster SEs are severely misleading when observations are geographically proximate and treatment or outcomes are spatially autocorrelated.

**The core problem:**

Nearby observations tend to look alike for reasons unrelated to your treatment — shared climate, institutions, culture, geography. With realistic spatial correlation, Conley & Kelly (2025) show that 38% of noise-on-noise regressions yield |t| > 2, and 21% yield |t| > 3. Nearly all 30 historical persistence studies they re-examined lose significance once spatial correlation is properly addressed.

**Step 8a: De-trend first (this step matters more than the SE correction itself)**

Before applying any SE correction, add a spatial basis to your regression:
1. Compute principal components of a tensor product B-spline in latitude × longitude coordinates.
2. Select the number of components by BIC.
3. Include these as additional controls in your regression.

The spatial basis removes spatially trending confounders that masquerade as treatment effects. Skipping this step and jumping straight to spatial SEs will not fix spurious findings caused by uncontrolled spatial trends.

**Step 8b: Apply spatial SE corrections after de-trending**

*BCH approach (Conley & Kelly's recommended default):*
- Partition observations into ~4–6 large geographic clusters using k-medoids.
- Apply cluster-robust SEs at this level.
- Start at 6 clusters; reduce to 4 if placebo rejection rate exceeds 8%.
- Because G is small (~4), the effective critical value for a 5% test is ~3.2, not 1.96. Wide CIs are expected and appropriate.

*IM (Ibragimov-Müller) inference:*
- Estimate cluster-specific slopes; treat as i.i.d. observations; apply t-test with C−1 degrees of freedom.
- Conservative, but robust to cross-cluster treatment effect heterogeneity.

*Conley (1999) SEs (for continuous space):*
- Specify a cutoff distance d* within which errors are assumed to correlate.
- Analogous to Newey-West but in two-dimensional space.
- Sensitive to cutoff choice; report robustness across values.

**Spatial diagnostic tests (run before finalizing):**

1. *Placebo test:* De-trend the treatment variable, estimate its spatial correlation structure, draw synthetic treatments independent of outcomes by construction. Compare your actual t-statistic against this reference distribution.
2. *Synthetic outcomes test:* Generate outcomes from a "spatial trend + spatially correlated noise" null; test whether your real t-statistic is distinguishable from pure noise.

These tests serve double duty: they provide a reference distribution for inference *and* calibrate whether your SE correction is working.

---

## Step 9: Bootstrap — When and Which

Bootstrapping is a fallback when parametric assumptions are suspect, not a default approach.

**When to use bootstrap:**
- Cluster count is small (G < 20) and parametric corrections are uncertain.
- Nonlinear models (logit, probit, IV) where sandwich formulas may behave poorly.
- You want to check whether analytic SEs are being driven by a single influential cluster.
- You are computing nonlinear functions of coefficients (marginal effects at the mean, interaction terms).

**Which bootstrap to use:**

| Situation | Recommended approach |
|-----------|----------------------|
| Clustered data, G ≥ 10 | Wild cluster bootstrap, Rademacher weights {−1, +1}, null imposed |
| Clustered data, G < 10 | Wild cluster bootstrap, Webb 6-point weights {±√1.5, ±√1, ±√0.5} |
| Partially clustered assignment | Two-Stage Cluster Bootstrap (TSCB): resample cluster treatment fractions (Stage 1), then units within clusters (Stage 2) |
| Panel DiD | Wild cluster bootstrap by unit (not by unit-period) |

**Avoid pairs (nonparametric) bootstrap when:**
- You have few clusters — one outlier cluster can dominate resamples and produce bimodal SE distributions.
- Treatment variation is limited — many resampled datasets may have zero treated clusters, producing undefined or zero SEs.
- Near-multicollinearity is present — pairs bootstrap can produce artificially inflated SEs.

Pairs bootstrap failure is subtle: it can converge to a stable number while being completely wrong. Cameron & Miller (2015) show that pairs bootstrap collapses at G=6 for DiD designs (rejection rate drops to 0.005 — extreme under-rejection). Wild bootstrap remains reliable.

---

## Common Mistakes and Anti-Patterns

These heuristics sound reasonable but lead practitioners astray.

---

**"If clustering makes a difference, cluster."**

This is backwards. A large gap between cluster SEs and robust SEs often means cluster SEs are massively *too conservative*, not that robust SEs are wrong. The right question is whether *assignment* was clustered, not whether the gap is large. Abadie et al. (2023) document cases where cluster SEs are 7.6× the true SE; in those cases, "the gap being large" signals over-clustering.

---

**"Keep clustering until it stops mattering."**

Not principled. Wooldridge (2023) shows that with heterogeneous treatment effects or heterogeneous regressors, coarser clustering systematically over-inflates SEs — in some designs by more than 8×. This heuristic will systematically over-cluster when TE heterogeneity or X heterogeneity is present.

---

**"G > 42 clusters means CRVE is safe."**

The "rule of 42" is not reliable. Jackson (2019) shows 6.5% rejection rates at G=48 under ideal conditions. With high covariate clustering — treatment that varies mostly *between* clusters rather than *within* — CRVE can fail severely even at G=50. The combination of few clusters and high covariate clustering is the worst case; it's also the modal scenario in comparative politics research.

---

**"Fixed effects absorb the cluster correlation."**

Fixed effects do not fix clustering. Residual within-cluster correlation typically remains after FE. Always use CRVE after FE. Also: with small cluster sizes, LSDV and within-estimator FE produce different CRVE estimates due to different degrees-of-freedom corrections. LSDV can overstate SEs by ~2× when Ng = 2. Use the within estimator (`xtreg, fe` in Stata, `plm` in R) rather than the demeaned OLS approach.

---

**"More observations means my SEs are valid."**

The SE formula measures within-model variation — how much the estimate would move if you redrew the sample. It does not account for systematic bias, model misspecification, or measurement error. Adding more observations drives SEs toward zero while doing nothing to address systematic uncertainty (Gelman 2023). N=500 with 3 treated units still has K_BM ≈ 2.

---

**"I'll cluster at the intersection of my two dimensions."**

Clustering at state-year instead of clustering separately on state and year misses serial correlation within states across years *and* cross-sectional correlation within years. Use two-way CRVE, not intersection clustering.

---

**"HC standard errors are fine for geographic data."**

HC SEs assume independent errors. With spatially autocorrelated data, HC SEs are severely anti-conservative — 38% of pure-noise regressions yield |t| > 2 (Conley & Kelly 2025). Never use HC SEs as your primary approach with geographic or historical cross-country data.

---

## What to Report

Regardless of which estimator you use:

1. **Point estimates and standard errors** — always.
2. **Confidence intervals** — preferred over significance stars for communicating uncertainty. A non-significant result with a narrow CI is more informative than one with a wide CI.
3. **The SE estimator and its design justification** — not just "we use cluster-robust SEs" but *why*: which mechanism (sampling or assignment) is clustered, at what level, and why that level.
4. **Robustness checks** — at least one alternative SE approach. If conclusions change, report that. Sensitivity to SE choice is a substantive finding.
5. **Significance as context, not conclusion** — an insignificant result does not mean the effect is zero. The effect magnitude and CI are what matter for most applied questions (Imbens 2021).

---

## Sources

- Abadie, Athey, Imbens & Wooldridge (2023). *When Should You Adjust Standard Errors for Clustering?* Quarterly Journal of Economics.
- Abadie, Athey, Imbens & Wooldridge (2020). *Sampling-Based versus Design-Based Uncertainty in Regression Analysis.* Econometrica.
- Cameron & Miller (2015). *A Practitioner's Guide to Cluster-Robust Inference.* Journal of Human Resources.
- Conley & Kelly (2025). *The Standard Errors of Persistence.* Journal of International Economics.
- Gelman (2023). *What is a Standard Error?* Journal of Econometrics.
- Imbens (2021). *Statistical Significance, p-Values, and the Reporting of Uncertainty.* Journal of Economic Perspectives.
- Imbens & Kolesár (2016). *Robust Standard Errors in Small Samples: Some Practical Advice.* Review of Economics and Statistics.
- Jackson (2019). *Corrected Standard Errors with Clustered Data.* Political Analysis.
- Wooldridge (2023). *What is a Standard Error?* Journal of Econometrics.
