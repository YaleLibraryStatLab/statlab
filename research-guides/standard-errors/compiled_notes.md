---
title: "Compiled Reading Notes — Standard Errors Literature"
date_compiled: 2026-05-08
sources:
  - abadie_2023
  - abadie_et_al_2020
  - cameron_miller_2015
  - conley_kelly_2025
  - gelman_2023
  - imbens_2021
  - imbens_kolesar_2016
  - jackson_2019
  - wooldridge_2023
---

# Compiled Reading Notes — Standard Errors Literature

---

## 1. Abadie, Athey, Imbens & Wooldridge (2023) — *When Should You Adjust Standard Errors for Clustering?*
**Journal:** Quarterly Journal of Economics | **Read:** 2026-04-01

### Synthesis

**Research Question:** When should standard errors be clustered, and at what level? Three open questions: (i) why cluster by geography but not by gender? (ii) is the clustered variance estimator valid when a large fraction of clusters are observed? (iii) in what settings does the clustering choice actually matter?

**Method:** Novel finite-population framework adding a *design component* (treatment assignment mechanism) to the standard *sampling component*. Decomposes variance into contributions from: (1) which units are sampled within clusters, (2) which clusters are sampled, and (3) how treatment is assigned. Proposes two new variance estimators: Causal Cluster Variance (CCV, analytic) and Two-Stage Cluster Bootstrap (TSCB).

**Data:** 2000 U.S. Decennial Census PUMS (5%): ~2.6 million individuals, 52 clusters (50 states + DC + Puerto Rico), outcome = log annual earnings, treatment = college attendance.

**Key Findings:**
- Robust SEs can be severely too small when treatment is clustered and clusters explain substantial outcome heterogeneity
- Conventional cluster SEs are always asymptotically conservative (v^cluster ≥ v), but can be massively inflated when many clusters are sampled and between-cluster TE variance is large
- CCV and TSCB substantially outperform both: cluster SE is 7.6× the true SE in baseline simulation; robust SE is 32% of the true SE; CCV is 7% above; TSCB is accurate
- Decision rule: cluster at the level of treatment assignment; do not cluster when sampling and assignment are random

**Practitioner Warnings:**
- No formal asymptotic theory for CCV or TSCB in this paper — simulation evidence only
- CCV degrades noticeably with smaller samples (p_k = 0.1 designs); TSCB preferred in practice
- Knowing q_k (fraction of clusters sampled) is required for both; often unclear in applied work
- The common heuristic "if clustering makes a difference, cluster" is backwards — a large gap often signals cluster SEs are too conservative, not that robust SEs are wrong

**Common Mistakes Addressed:**
- Clustering whenever residuals are correlated within clusters, regardless of sampling or assignment design
- Assuming only two choices exist (robust or cluster); CCV/TSCB offer a middle path
- Clustering with FE because of model-based arguments — design-based view shows FE doesn't eliminate need to account for clustered assignment

**Client Communication:** "Cluster your standard errors at the level where treatment was assigned, not at the level where outcomes happen to look similar. If treatment is assigned randomly to individuals, clustering by state gives you unnecessarily wide confidence intervals — sometimes 20× too wide."

### Reading Notes

**Introduction [pp. 1-8]**
- [RQ] When should standard errors be clustered, and at what level? Three motivating questions: (i) why cluster by state but not by gender? (ii) is the clustered variance estimator valid when a large fraction of clusters is observed? (iii) in what settings does the clustering choice matter?
- [METHOD] Framework adds a *design component* (treatment assignment mechanism) to the standard *sampling component* — allows three sources of variation: which units are sampled within clusters, which clusters are sampled, and which units are treated
- [CONTRIB] Framework shows conventional clustered SEs can be severely inflated when many clusters are sampled; proposes CCV and TSCB that correct this
- [MISTAKES] Three misconceptions: (1) intra-cluster residual correlation implies need to cluster; (2) clustering is always conservative so no harm when unsure — "if clustering makes a difference, cluster" is often wrong; (3) only two choices exist
- [QUOTE] "The presence of such correlation does not imply the need to use cluster adjustments... the harm in clustering in this case is that confidence intervals will be unnecessarily conservative, possibly by a wide margin."
- [TEACH] Estimating a population mean from a random sample is a clean demonstration of when clustering is wrong even when intra-cluster correlation exists [pp. 3]
- [TABLE] Table I — College Effects in Census Sample: robust SE = 0.0012, cluster SE = 0.0269, CCV = 0.0035, TSCB = 0.0036; cluster SEs ~23× larger than robust [SLIDE]

**Framework for Clustering [pp. 8-12]**
- [STATS] Two-stage sampling: clusters sampled with probability q_k; units sampled within clusters with probability p_k. Standard framework = q_k → 0. Random sampling = q_k = 1
- [STATS] Two-stage assignment: cluster-specific treatment probability A_{k,m} with mean μ_k and variance σ²_k. Three regimes: random assignment (σ²_k = 0), clustered assignment (σ²_k = μ_k(1−μ_k)), partially clustered (0 < σ²_k < μ_k(1−μ_k))
- [CONTRIB] Partial clustering — treatment probability varies by cluster but not all units in cluster treated — is a novel intermediate case

**Variance Estimators [pp. 11-16]**
- [STATS] Cluster variance estimator V̂^cluster_k is asymptotically conservative — v^cluster_k ≥ v_k always — but can massively overestimate; excess grows with (a) fraction of population sampled, (b) fraction of clusters sampled, (c) between-cluster TE heterogeneity
- [WARN] Critical implication: "if clustering matters, cluster" is backwards — the gap between cluster and robust SEs being large is precisely when cluster SEs are most likely to be misleadingly conservative

**New Estimators [pp. 17-24]**
- [STATS] CCV: analytic estimator that corrects cluster variance downward by estimating cluster-specific treatment effects; uses sample splitting; V̂^CCV_k = q̂_k × V̂^CCV_k(1) + (1 − q̂_k) × V̂^cluster_k
- [STATS] TSCB: two-stage bootstrap resampling cluster-level treatment fractions (Stage 1) then units within clusters (Stage 2)
- [LIMITS] CCV and TSCB require within-cluster variation in treatment; not applicable when treatment is constant within clusters

**Fixed Effects [pp. 23-24]**
- [CONTRIB] Design-based view clarifies that the *design* component (clustered assignment) still requires clustering even with FE, despite model-based arguments that FE absorbs cluster-level variation

**Simulations [pp. 27-31]**
- [TABLE] Table II — Average SEs: baseline OLS true SE = 5.91; robust = 1.90 (32% of true), cluster = 44.86 (7.6× true), CCV = 6.32 (7% above), TSCB = 5.80 (accurate) [SLIDE]
- [TABLE] Table III — Coverage rates for 95% CIs: baseline — robust = 0.467, cluster = 1.000, CCV = 0.971, TSCB = 0.947 [SLIDE]
- [FINDINGS] When treatment effects are homogeneous (Design 4): cluster SE performs well; robust SE remains biased — confirms clustering is about assignment mechanism, not TE heterogeneity alone
- [FINDINGS] When assignment is random across clusters (Design 5): robust SE correct; cluster SE massively overcovering

**Implications for Practice [pp. 31-33]**
- [TEACH] Decision tree: (1) Random sample + random assignment → do NOT cluster; (2) Clustered assignment + random sampling → cluster, but use CCV/TSCB if partially clustered; (3) Clustered sampling (q_k ≈ 0) → conventional cluster SE is fine
- [TRANSFER] Judge leniency / examiner designs: since defendants are randomly assigned to judges, do NOT cluster at judge level
- [REPLICATION] Replication data and code at Harvard Dataverse: https://doi.org/10.7910/DVN/27VMOT

---

## 2. Abadie, Athey, Imbens & Wooldridge (2020) — *Sampling-Based versus Design-Based Uncertainty in Regression Analysis*
**Journal:** Econometrica | **DOI:** 10.3982/ECTA12675 | **Read:** 2026-04-01

### Synthesis

**Research Question:** When is standard EHW robust inference appropriate? What is the correct interpretation of SEs when the sample is a non-negligible fraction of a finite population, or when there is no natural infinite population? How should design-based uncertainty — from treatment assignment — be incorporated?

**Method:** Potential-outcomes regression framework with two sources of uncertainty (sampling and design) formalized simultaneously. Three estimands defined: descriptive (θ^descr), causal-sample (θ^causal,sample), causal-population (θ^causal). EHW variance is a special case (ρ=0). Improved, conservative variance estimators exploit fixed attributes to shrink below EHW.

**Key Findings:**
- EHW variance estimator targets V^sampling(ρ=0) — the infinite-population sampling variance — and overstates true variance by S²_θ/n (variance of unit treatment effects)
- EHW is exactly correct when: (a) ρ=0 (negligible sampling fraction), or (b) treatment effects are constant
- At ρ=1 (full population census): θ^descr variance = 0; only design-based variance remains for causal estimand
- V̂^causal achieves near-nominal 95% coverage across all simulation designs; EHW gives up to 100% coverage for θ^descr at ρ=1

**Contributions:**
1. Unified framework nesting sampling-based (EHW) and design-based (Neyman randomization) uncertainty in single variance expression parameterized by ρ
2. Formal proof that EHW is (weakly) conservative; gap equals Δ^μ, positive iff treatment effects are heterogeneous and ρ > 0
3. Attribute-adjusted variance estimators strictly smaller than EHW when attributes predict treatment effect variation
4. Internal validity ↔ design-based uncertainty; external validity ↔ sampling-based uncertainty

**Practitioner Warnings:**
- Improvement over EHW only realized when attributes predict treatment effect heterogeneity (ψ'ψ > 0)
- ρ must be known or estimable; for convenience samples ρ is not well-defined
- V̂^causal,sample is conservative for θ^causal — smaller SEs are still upper bounds, not greater precision

**Common Mistakes Addressed:**
- Applying EHW SEs when sample is a large fraction of (or the entire) population
- Treating "all US states" or "all countries" as a random sample from an infinite population
- Interpreting bootstrap SEs as a solution — bootstrap in expectation equals EHW

**Client Communication:** "Standard errors in most regressions assume you're looking at a tiny random slice of a huge population. If you have data on all 50 states, that assumption is wrong. When you have the whole population and ask 'what would have happened under a different policy?', the only uncertainty left is about the counterfactual — not about who's in your sample."

### Reading Notes

**Introduction [pp. 1-4]**
- [TEACH] Opening framing: "data for all 50 states" or "all visits to a website" — what population are you sampling from? If there is no sensible infinite population, what do your SEs mean? [SLIDE]
- [CONTRIB] Formal separation of sampling vs. design uncertainty clarifies internal/external validity in regression settings
- [TEACH] Tables I and II: contrast sampling uncertainty (which units observed?) vs. design uncertainty (which potential outcome revealed?) in a clean 2-table layout [SLIDE]

**Simple Example [pp. 4-8]**
- [STATS] Total variance = S²₁/N₁ + S²₀/N₀ − S²_θ/(n₀+n₁); EHW = S²₁/N₁ + S²₀/N₀ = V^sampling, overstates true variance
- [FINDINGS] EHW is conservative; gap to V^total is S²_θ/n — the unidentified variance of treatment effects
- [TEACH] Comment 5: internal validity ↔ random assignment (design-based); external validity ↔ random sampling (sampling-based) [SLIDE]
- [WARN] S²_θ (variance of individual treatment effects) is not identified from observed data; EHW conservatism cannot be corrected without additional assumptions

**General Case [pp. 9-16]**
- [STATS] Theorem 3 (main result): θ^causal asymptotic variance = Γ^{-1}(ρΔ^cond + (1−ρ)Δ^ehw)Γ^{-1}; at ρ=0 reduces to EHW; at ρ=1 reduces to pure design-based variance
- [FINDINGS] Theorem 4: Under constant treatment effects, EHW SEs are valid regardless of sampling fraction
- [TEACH] Comment 11: CPS/PSID → standard EHW is fine. All US states or all countries → must use design-based variance [SLIDE]
- [CLIENT] "If you have all 50 states or all countries, sampling-based SEs are literally zero — the only remaining uncertainty is design-based."
- [WARN] Comment 7 (Table III): Without Assumption 7 (linear propensity score), the causal OLS estimand can be nonzero even when ALL unit-level causal effects are zero

**Variance Estimation [pp. 18-19]**
- [STATS] V̂^causal,sample = Γ̂^{-1}Δ̂^Z_n Γ̂^{-1}; V̂^causal = ρ̂_n V̂^causal,sample + (1−ρ̂_n) V̂^ehw; both conservative but smaller than V̂^ehw

**Simulations [pp. 19-21]**
- [TABLE] Table IV — Coverage: at ρ=1, EHW gives 100% coverage for θ^descr; V̂^causal achieves ~95% across all designs [SLIDE]

---

## 3. Cameron & Miller (2015) — *A Practitioner's Guide to Cluster-Robust Inference*
**Journal:** Journal of Human Resources | **Read:** 2026-04-02

### Synthesis

**Research Question:** When data are grouped with errors correlated within but independent across clusters, how should empiricists perform valid statistical inference?

**Method:** Survey and practitioner synthesis. Derives CRVE analytically, reviews literature systematically, validates with Monte Carlo using CPS data.

**Data:** March 2012 CPS (N=65,685, G=51 states); March 1997-2012 CPS panel (N=1,836 state-year obs, G=51 states). Both use randomly-generated placebo policy dummy.

**Key Findings:**
- Default SEs routinely understate uncertainty; ρᵤ=0.032 with cluster-invariant regressors → 3–5× SE inflation
- Cross-section: CRVE = 5.5× default (SE 0.0229 vs 0.0042); panel: CRVE = 3.6× default after state+year FEs
- Monte Carlo hierarchy at G=6: White HC → ~45% rejection; CRVE+T(G-1) → ~12%; CR2+T(v*) or CR3+T(G-1) → ~5%; pairs bootstrap → ~1% (under-rejection); wild bootstrap (Webb 6-pt) → ~8%
- For panel DiD, wild bootstrap reliable even at G=6; pairs bootstrap collapses

**Practitioner Warnings:**
- CRVE highly variable with few clusters: SD of CRVE ≈ 12% of mean at G=50
- Unbalanced clusters worsen few-cluster problem: effective G can be far below nominal G
- Stata command matters: `regress` uses T(G-1); `xt` commands use N(0,1) by default
- Fixed effects do NOT fix clustering: residual within-cluster correlation typically remains

**Common Mistakes Addressed:**
- Clustering at intersection (state-year) rather than separately on each dimension
- Using LSDV instead of within estimator for FE+CRVE — overstates SEs when N_g is small
- Using standard Hausman test or weak-instrument F-stat under clustering — invalid
- Clustering on state-year in DiD panels (misses serial correlation within state across years)

**Client Communication:** "Your standard errors are probably too small — by several times — if your treatment varies at the group level but you're using individual-level data. State-level policy variation with individual workers: one state is one data point for inference purposes, regardless of how many workers you observe."

### Reading Notes

**Introduction [pp. 2-3]**
- [TEACH] Core intuition: failure to account for within-cluster error correlation → SEs too small → CIs too narrow → t-stats too large → over-rejection of nulls
- [MISTAKES] Bertrand, Duflo & Mullainathan (2004): many DiD studies failed to cluster, or clustered at wrong level
- [WARN] "Few" clusters is hardest complication; no clear threshold — "few" may range from <20 to <50

**Cluster-Robust Variance [pp. 3-12]**
- [STATS] Moulton variance inflation factor: τₖ ≈ 1 + ρ_xₖ · ρᵤ · (N̄_g − 1); March CPS: ρᵤ=0.032, G=49 states → τₖ≈13.3 → cluster SEs 3.7× default [SLIDE]
- [TEACH] Three forces that increase V_clu[β̂] over V_het[β̂]: (1) within-cluster regressor correlation, (2) within-cluster error correlation, (3) cluster size
- [TEACH] "Magic" of CRVE: each cluster's ûgû'g is a terrible estimate individually, but averaging across G clusters yields a consistent estimate — hence the G→∞ requirement
- [STATS] Consistency requires G→∞; also valid for long panels (N_g→∞) per Hansen (2007a)
- [WARN] Finite-sample corrections reduce but do not eliminate downward bias with few clusters
- [LIMITS] FGLS default SEs valid only under correct specification of Ω_g; always add `vce(robust)` or `vce(cluster)` to FGLS commands

**Fixed Effects [pp. 12-16]**
- [WARN] Fixed effects do NOT fully control for within-cluster error correlation — always use CRVE after FE
- [WARN] With small cluster sizes, LSDV and within estimators yield different CRVE; LSDV can be ~2× too large when N_g=2
- [REPLDIFF] Correct: `xtreg y x, fe vce(robust)`; NOT `regress y x i.id_clu, vce(cluster id_clu)`
- [STATS] Standard Hausman test invalid under clustering; use cluster-robust Hausman via `xtoverid`

**What to Cluster Over [pp. 17-19]**
- [DECISIONS] Two guiding principles: (1) cluster broadly enough to capture where both regressors AND errors are correlated; (2) need enough clusters G so V̂_clu converges
- [WARN] Stock & Watson (2008): standard White HC SE is inconsistent for FE models when N_g is small; use CRVE

**Multi-way Clustering [pp. 19-23]**
- [MISTAKES] Common error: clustering at intersection (e.g., state-year) rather than each dimension separately — equivalent to HC SEs if data is at state-year level
- [STATS] Two-way CRVE (CGM 2011): V̂_2way = V̂_1 + V̂_2 − V̂_{1∩2}; run three separate one-way clustered regressions
- [WARN] Two-way V̂_2way NOT guaranteed PSD — can produce negative variances
- [STATS] Trade data: two-way clustering on 98-country pairs gives SEs 36% larger than one-way, 230% larger than HC [SLIDE]

**Few Clusters [pp. 23-32]**
- [FINDINGS] Simulation rejection rates at nominal .05: G=50→.063, G=20→.058, G=10→.080, G=6→.115
- [FINDINGS] Unbalanced clusters: G=10 with half N_g=50 → rejection rate .183 vs .126 for balanced G=10
- [STATS] CR2VE (Bell & McCaffrey): replace û_g with [I − H_gg]^{-1/2} û_g; literature consensus: prefer CR2VE
- [STATS] Wild cluster bootstrap: estimate model under H₀; assign each cluster random weight d_g ∈ {-1,+1}; repeat B times
- [WARN] Pairs bootstrap failure modes: outlier cluster → bimodal histogram; limited treatment variation → zero SEs
- [STATS] Webb (2013): with G<10 use six-point weight distribution {±√1.5, ±√1, ±√0.5}
- [STATS] Bell & McCaffrey data-determined DoF: use T(v*) where v* = (Σλ_j)²/(Σλ_j²); Carter et al. effective cluster count G* = G/(1+δ); test distortion when G* < 20

**Empirical Examples [pp. 39-44]**
- [TABLE] Table 1: March 2012 CPS: default SE=0.0042 → t=−5.42 (false rejection); CRVE SE=0.0229 → t=−0.99 (correct) [SLIDE]
- [TABLE] Table 2: Monte Carlo rejection rates: HC → ~0.46-0.50 regardless of G; best performers at few clusters: CR3+T(G-1) and CR2+T(IK DOF) [SLIDE]
- [TABLE] Table 3: State-year panel DiD: default SE=0.0037 → p≈0.000; CRVE SE=0.0119 → p≈0.20; CRVE is 3.6× default even after FEs [SLIDE]
- [TABLE] Table 4: Panel DiD Monte Carlo: wild bootstrap works at G=6; pairs bootstrap collapses (rejection rate 0.005) [SLIDE]

---

## 4. Conley & Kelly (2025) — *The Standard Errors of Persistence*
**Journal:** Journal of International Economics | **Read:** 2026-03-26

### Synthesis

**Research Question:** Do unusually large t-statistics in historical persistence regressions reflect genuine deep historical processes, or are they statistical artifacts of uncontrolled spatial trends and autocorrelation?

**Method:** Re-analysis of 30 persistence studies. Two new diagnostic tests: (1) simulation-based placebo test replacing real treatment with synthetic spatial noise; (2) synthetic outcomes test of the null that outcomes are generated by trend + spatially correlated noise. New procedure: augment with spatial basis (principal components of lat/lon tensor spline, selected by BIC), then apply BCH large-cluster SEs (~4 k-medoids clusters) or IM cluster inference.

**Key Findings:**
- Adding simple spatial trend controls: 10 of 30 studies lose significance at 5%; median nominal p rises from 0.002 to 0.02
- After spatial basis + BCH: only 1 of 30 studies significant at 5%; 5 more between 6-9%
- Synthetic outcome test: only 1 of 30 rejects null at 5%
- HC SEs over-reject severely: 38% of noise-on-noise simulations yield |t| > 2; 21% > 3; 8% > 4
- In 18 of 27 studies, at least one geographic cluster has a treatment estimate with opposite sign to the full sample

**Common Mistakes Addressed:**
- Using HC or small-cluster SEs with spatially correlated data
- Failing to control for spatial trends before applying SE corrections
- Using many small clusters — worsens performance because of cross-cluster correlation
- Standard placebo tests (randomly shuffling treatments) destroy spatial structure; inappropriate for spatial data

**Practitioner Warnings:**
- Non-significance under proper spatial inference does not imply zero effect — only that data are too noisy/trending with available observations
- BCH with ~4 clusters means critical value for 5% test is 3.2, not 1.96 — wide CIs are expected and appropriate

**Client Communication:** "We found that nearly all 30 well-known historical persistence studies lose their statistical significance once we properly account for the fact that nearby places tend to look alike. Think of it like regressing temperature in January on temperature in July across European cities — both trend north-to-south, so you'd find a spurious correlation even if the two were actually unrelated."

### Reading Notes

**Introduction [pp. 1-4]**
- [TEACH] Core intuition: spatial data violate the "independent observations" assumption; regressing two spatially autocorrelated noise series routinely produces t-statistics > 4 — the spatial analogue of spurious regression in time series [SLIDE]
- [MISTAKES] In simulations with realistic spatial correlation, 38% of noise-on-noise regressions yield |t| > 2; 21% > 3; 8% > 4
- [FIG] Fig. 1 — Regression of one empirically realistic noise series on another: t = -3.8, nominal p = 0.0001, but Monte Carlo p = 0.10 [SLIDE]
- [FIG] Fig. 2 — Rejection frequencies of nominal 5% tests: BCH-4/6 flat-lines near 5%; all others deteriorate sharply as spatial correlation grows [SLIDE]

**Spatial Diagnostic Tests [pp. 5-7]**
- [METHOD] Placebo test: de-trend treatment, estimate spatial correlation structure, draw synthetic treatments independent of outcomes by construction
- [METHOD] Synthetic outcomes test: estimate "trend + spatially correlated noise" model for outcomes; test whether real t-statistic is distinguishable from noise
- [STATS] Gaussian additive model: V(s) = μ(s) + ψ(s) + η(s), where ψ ~ N(0, τ²K) with Matérn exponential kernel K(si,sj) = exp(-h/θ)
- [TEACH] Placebo simulations serve double duty: (1) reference distribution for testing; (2) calibration check on inference method

**Motivation: Persistence Regressions with Trend Controls [pp. 7-10]**
- [TABLE] Table 1 — Nominal p, Placebo p, Synthetic p for all 30 studies: median nominal p rises from 0.002 to 0.02 after adding simple trends; 10 of 30 lose significance [SLIDE]
- [TABLE] Table 2 — Spatial parameters for treatment and outcome variables: most treatments have ρ ≈ 1 (nearly pure spatial signal) [SLIDE]

**Spatial Basis Regression [pp. 10-12]**
- [METHOD] Augment regression with first L principal components of a tensor spline in lat/lon, selected by BIC; then apply BCH (~4 k-medoids clusters) or IM inference
- [DECISIONS] BCH cluster number: start at 6 clusters, reduce if placebo rejection rate > 8%; most studies end at 4 clusters
- [FIG] Fig. 4 — 6×6 tensor product B-spline in lat/lon capturing 80% of variance in 19th century German literacy [SLIDE]

**Main Results [pp. 13-16]**
- [TABLE] Table 3 — Full results for all 30 studies: HC p, BCH p, placebo p, synthetic outcome p, Moran z-score [SLIDE]
- [FINDINGS] Only 1 of 30 studies significant at 5% after spatial basis + BCH; near-universal non-significance
- [FIG] Fig. 7 — Scatter of spatial basis regression p-values across all 30 studies [SLIDE]

**Coefficient Stability [pp. 17-19]**
- [STATS] IM procedure: estimate cluster-specific slopes, treat as i.i.d. observations, t-test with C-1 d.f. — conservative but robust to cross-cluster heterogeneity
- [TABLE] Table 5 — IM 95% CIs: only 1 significant at 5%, 2 more at 10%; agrees with BCH
- [FIG] Fig. 8 — Cluster-specific effects: in 18 of 27 studies, at least one cluster has opposite sign; one study shows Simpson's Paradox (all clusters opposite sign) [SLIDE]
- [QUOTE] "Two thirds of studies have at least one region where the treatment effect is opposite in sign to the full sample."
- [REPLICATION] R package `spatInfer`: https://github.com/morganwkelly/spatInfer

---

## 5. Gelman (2023) — *What is a Standard Error?*
**Journal:** Journal of Econometrics | **Read:** 2026-04-02

### Synthesis

**Research Question:** What does a standard error actually measure in practice? When and why does the textbook formula become misleading, and what should replace it?

**Method:** Three illustrative examples (bathroom scale, 50-state regression, election polls) used to argue that the correct SE is determined by the generalization of interest and the model of variation implied by the inferential goal.

**Key Findings:**
- When unknown bias is present (bathroom scale), a precise SE from many observations is meaningless
- With whole-population data (all 50 states), SE is not zero or undefined; it reflects the implied model of variation for the intended generalization
- In election polling, observed errors are ~2× reported SEs; reporting sampling-only SEs implicitly sets nonsampling error to zero
- The SE from standard formulas should be treated as a lower bound: it measures within-model variation, not full uncertainty relative to the real-world target

**Contributions:** Reframes the SE as a *model choice problem* analogous to the estimand choice in causal inference: the right SE requires specifying what population you want to generalize to and what model of variation that implies.

**Client Communication:** "The SE your model reports measures how much the estimate would vary if you redrew the sample — but it doesn't account for whether the measurement instrument itself is off, or whether your sample is the wrong unit of analysis. More observations make the SE smaller, but if the source of uncertainty is systematic, more data doesn't help."

### Reading Notes

**Bathroom Scale [pp. 1]**
- [FINDINGS] After 46 measurements: mean = 67.1 kg, SE = 0.1, yielding 95% CI of 67.1 ± 0.2 — but interval is meaningless because systematic bias is unknown
- [WARN] Adding more observations drives SE to zero while doing nothing to address systematic error; applies to any observational data context with unmeasured confounding
- [TEACH] Ideal pedagogical example: intuitive, concrete, immediately shows limits of the SE formula

**50 States [pp. 1-2]**
- [FINDINGS] SE is not zero even with exhaustive population data; remains meaningful as a measure of variation for a predictive/generalization model (e.g., treating one year's data as a sample from a population of state-years)
- [WARN] "Just because you have an exhaustive sample, that does not mean that the standard error is undefined or meaningless" — SE is a model-dependent quantity, not a fact about the data
- [XREF] Direct connection to abadie_et_al_2020 and cameron_miller_2015

**Election Polls [pp. 2]**
- [FINDINGS] Empirical SD of poll errors ≈ 2× the reported SE from standard sampling formulas — nonsampling error dominates
- [FLAG] Standard pollster practice reports sampling-based SE, implicitly setting nonsampling error to zero
- [TEACH] Election polls are a rare "ground truth" case — useful for teaching the difference between internal precision and external validity of uncertainty estimates

**Summary [pp. 2]**
- [QUOTE] "The appropriate standard error depends not just on the data and sampling model but also on the generalization of interest, and the model of variation across units and over time corresponding to the uses to which the estimate will be put."
- [TEACH] Summary reframes SE as a model-choice problem analogous to identifying the estimand in causal inference

---

## 6. Imbens (2021) — *Statistical Significance, p-Values, and the Reporting of Uncertainty*
**Journal:** Journal of Economic Perspectives | **Read:** 2026-04-02

### Synthesis

**Research Question:** Should empirical researchers report p-values and statistical significance indicators, and if so, when and how? Organizes the debate around three concerns: (1) p-values are irrelevant to most estimation questions, (2) p-values are a weak tool even for genuine hypothesis testing, (3) p-values are structurally abused via p-hacking and publication bias.

**Key Findings:**
- In decision/policy contexts, p-values are irrelevant; treating insignificant results as true zeros is the key practical harm
- In genuine sharp null testing, p-values are *necessary* but not *sufficient* to reject a null with strong prior probability
- Banning p-values does not improve reporting quality; BASP's ban increased overclaiming (Fricker et al. 2019)
- Standardized 5% threshold is unjustifiable; Benjamin et al. (2018) propose 0.005 for "override a strong prior" settings

**Common Mistakes Addressed:**
- Treating a statistically insignificant estimate as evidence of zero effect
- Using p < 0.05 as the decision rule for policy implementation rather than examining magnitude, cost, and uncertainty
- Assuming removing p-values from reporting improves inferential quality (the BASP counterexample)

**Practitioner Warnings:**
- "Report CIs instead of p-values" is sound in most OLS contexts but requires care in IV settings with weak instruments
- Lindley's paradox: with large samples and diffuse alternative priors, a statistically significant result can coexist with a high posterior probability of the null

**Client Communication:** "p-values can be the wrong question, an imperfect tool even for the right question, or an actively gamed metric. Suggested substitute: 'We estimate the effect is X, with a margin of uncertainty of ±Y.'"

### Reading Notes

**Introduction [pp. 1-3]**
- [CONTRIB] First concern (p-values don't answer the estimation question) is most compelling; recommends CIs and ideally Bayesian posterior intervals; retains limited role for p-values in genuine hypothesis testing
- [QUOTE] Wasserstein, Schirm & Lazar (2019): "It is time to stop using the term 'statistically significant' entirely."

**Estimation versus Hypothesis Testing [pp. 6]**
- [TEACH] Key distinction: estimation problems (what is the magnitude?) vs. hypothesis testing (does this null hold?); most economics questions are estimation problems miscast as tests
- [CLIENT] "What is of interest is the magnitude and uncertainty of the estimates, not whether the data allow for the rejection of a zero effect."

**Decision Making [pp. 7-8]**
- [METHOD] Formal decision-theoretic setup: policy decision = f(point estimate τ̂, uncertainty σ, prior beliefs, cost of errors) — p-value plays no role
- [STATS] CIs approximately valid as Bayesian posterior intervals via Bernstein-Von Mises theorem (with caveats for weak IV, unit roots)
- [WARN] "Just report CIs" works when B-vM holds, but not in IV settings with weak instruments

**Hypothesis Testing [pp. 9-10]**
- [WARN] Lindley's paradox: for large samples with diffuse alternative priors, can have significant p-value with high posterior probability of null
- [TEACH] Precognition / Bem (2011) example: illustrates why significant p-value cannot override strongly held prior

**Publication Bias and p-hacking [pp. 11-14]**
- [FINDINGS] InterMune/Harkonen: overall trial p = 0.08; post-hoc subgroup search produced p = 0.004; follow-up trial failed; CEO convicted — extreme example of p-hacking incentives
- [FINDINGS] Garden of forking paths (Gelman & Loken 2013): even without deliberate fishing, specification choices collectively inflate false positive rates
- [CONTRIB] Pre-analysis plans (PAPs) as structural solution; AEA registry for RCTs

**Conclusion [pp. 14-15]**
- [FINDINGS] BASP's ban increased overclaiming — Fricker et al. (2019); banning a probability calculation is an extreme response
- [CONTRIB] Final hierarchy: point estimates + SEs always; prefer CIs over significance stars; prefer Bayesian posterior intervals where feasible
- [QUOTE] "In many cases, the p-value or the measure of statistical significance is not the relevant output from an analysis of a dataset."

---

## 7. Imbens & Kolesár (2016) — *Robust Standard Errors in Small Samples: Some Practical Advice*
**Journal:** Review of Economics and Statistics | **Read:** 2026-04-02

### Synthesis

**Research Question:** Do EHW/LZ confidence intervals perform adequately in small and moderately sized samples? Challenges the claim that 50+ units or clusters is sufficient; argues for the Bell-McCaffrey (BM) adjustment as a principled, routine replacement.

**Method:** Theoretical analysis connecting BM to the classical Behrens-Fisher problem via Welch (1951). Monte Carlo using Angrist-Pischke and Cameron-Gelbach-Miller benchmark designs. Proposes IK modification using a random-effects estimate of within-cluster covariance.

**Key Findings:**
- Unbalanced Angrist-Pischke design (N=30, N₁=3): K_BM = 2.5; EHW coverage = 77-87%; BM coverage = 94-99%
- CGM 10-cluster designs: LZ+S-1 dof = 85-91% coverage; BM = 94-96%
- 50-cluster designs with log-normal regressors: LZ = 86%, BM = 97%; with only 3 treated clusters: LZ = 76-84%, BM = 94-99%
- K_BM is the key diagnostic: when K_BM << N-2 (or S-1), EHW/LZ SEs are unreliable regardless of sample size

**Contributions:**
1. BM is a principled extension of Welch (1951) to general OLS, not an ad hoc fix
2. Skewness of the covariate distribution — not just N or number of clusters — determines when corrections matter
3. K_BM as a routine diagnostic
4. K_IK as a slight improvement for the clustering case

**Practitioner Warnings:**
- K_BM should be computed routinely; if substantially smaller than N-2 or S-1, switch to BM CIs
- Design skewness (not sample size) is the operative criterion; N=500 with 3 treated units → K_BM ≈ 2
- Wild bootstrap with null imposed (wild0): computationally intensive and produces very wide CIs

**Common Mistakes Addressed:**
- Using t_{N-2} with HC2 — no assumptions under which this is exactly correct
- Relying on "N>50 clusters is enough" without checking covariate distribution
- Treating STATA's default clustered SE adjustment as sufficient

**Client Communication:** "Standard robust SEs assume you have a lot of data. When most observations fall in one group (90% control, 10% treated), those SEs are too small. The Bell-McCaffrey adjustment figures out how many independent pieces of information you really have for each coefficient."

### Reading Notes

**Behrens-Fisher Setup [pp. 2-5]**
- [STATS] V_HC2: σ̂²(d) = (1/(N_d-1))Σ(Y_i − Ȳ_d)²; unbiased for V in the binary regressor case
- [STATS] K_BM special cases: if N_0 >> N_1, K_BM ≈ N_1-1; if N_0 = N_1, K_BM = N-2 (standard dof fine for balanced designs)
- [TABLE] Table 1 — Unbalanced BF (N_0=27, N_1=3, normal errors): BM dominates all methods; wild0 competitive but ~45% wider [SLIDE]
- [TABLE] Table 2 — Log-normal errors: EHW coverage falls to 67-91%; BM = 87-100% [SLIDE]
- [TABLE] Table 3 — Balanced design (N_0=N_1=15): all methods near nominal; corrections only matter for unbalanced/skewed designs [SLIDE]

**General Regression [pp. 6-8]**
- [STATS] HC2 general case: residuals divided by sqrt(1−P_ii) where P_ii is leverage; removes all bias under homoskedasticity, partial under heteroskedasticity
- [STATS] K_BM general case: (Σλ_i)²/Σλ_i² where λ_i are eigenvalues; depends only on regressors
- [DESIGN] Practical diagnostic: compute K_BM routinely; if K_BM << N-2, EHW CIs likely unreliable

**Clustering [pp. 8-10]**
- [STATS] V_LZ2: cluster-level analog of HC2 using (I_{N_s}−P_{ss})^{-1/2} transformation
- [STATS] K_IK modification: estimate within-cluster correlation ρ̂; use random-effects Ω̂ rather than σ²I_N
- [TABLE] Table 4 — 10-cluster designs: BM and IK clearly superior to LZ/STATA [SLIDE]
- [TABLE] Table 5 — 50-cluster designs: even 50 clusters insufficient with log-normal regressors or very few treated clusters; BM/IK robust throughout [SLIDE]
- [REPLDIFF] R code: https://github.com/kolesarm/Robust-Small-Sample-Standard-Errors

---

## 8. Jackson (2019) — *Corrected Standard Errors with Clustered Data*
**Journal:** Political Analysis | **Read:** 2026-04-02

### Synthesis

**Research Question:** Do cluster robust standard errors (CRSE) systematically underestimate coefficient standard errors in OLS models with grouped data? Can a new estimator (CESE) that directly recovers within-cluster error covariance provide more reliable inference?

**Method:** (1) Analytical derivation of CRSE bias conditions; (2) Monte Carlo simulation (G = 12–96, covariate clustering 0–0.9, normal/exponential/chi-squared errors); (3) Empirical illustration with state politics (G=50) and comparative politics (G=51 countries) datasets.

**Key Findings:**
- CRSE underestimates SEs even under ideal conditions (G=48: 3% bias, 6.5% rejection rate); severe with small G and high covariate clustering (G=12, clustering=0.9: amse = −0.40, rejection rate >50%)
- CESE consistently outperforms CRSE and CBSE; near-nominal rejection rates with G≥24 under most conditions
- Bootstrap instability: CBSE rejection rate varies >1% across seeds — CESE more reproducible
- Empirical: CRSE endorses presidential power hypothesis at p=0.007; CESE fails to reject at p=0.150

**Contributions:**
- Identifies *covariate clustering* (between-cluster variance share of total X variance) as the dominant but overlooked driver of CRSE bias
- CESE is the first method that directly estimates Σ_g (the "meat"), enabling Wald tests of joint hypotheses
- CESE dominates cluster bootstrapping in accuracy and reproducibility

**Practitioner Warnings:**
- CRSE rejection rates exceed 50% with G=12 and high covariate clustering — modal comparative politics panel, not a tail scenario
- Bootstrap instability: papers using CBSE with different seeds may reach different conclusions from identical data
- CESE homogeneity assumption may be consequential when within-cluster correlation varies substantially across clusters

**Common Mistakes Addressed:**
- Using CRSE without checking number of clusters or degree of covariate clustering
- Believing bootstrap-corrected CIs fully solve the problem
- Citing the "rule of 42" as a reliable threshold

**Client Communication:** "In the presidential power example, the 'significant' result with standard clustered SEs becomes non-significant with corrected SEs — not because the relationship changed, but because the uncertainty was being hidden."

### Reading Notes

**Methodological Issues with CRSE [pp. 1-3]**
- [STATS] Three necessary conditions for CRSE consistency: (a) G→∞; (b) homogeneity across clusters; (c) equal observations per cluster
- [STATS] Key bias source: underestimation grows with (a) fewer clusters, (b) unequal cluster sizes, (c) high covariate clustering
- [FINDINGS] "Covariate clustering" = between-cluster variance as proportion of total X variance — largely overlooked; high in PolSci datasets where institutions vary across but not within countries

**Cluster Estimated Standard Errors [pp. 4-5]**
- [METHOD] CESE: exploit that E(e_g e_g') = σ²Q1_g + ρQ2_g; stack across clusters; solve via OLS on residual products to recover σ̂² and ρ̂
- [STATS] Two adjustments: CESE2 (hc2) and CESE3 (hc3); hc3 preferred under heteroskedasticity
- [TEACH] Elegant: directly estimates parameters of within-cluster error structure — conceptually like method-of-moments

**Monte Carlo [pp. 5-15]**
- [FINDINGS] CRSE with ideal data: never reaches nominal 5% even at G=96 (rejection rate 6.5%)
- [FINDINGS] MacKinnon-Webb "rule of 42" not supported — G=48 shows 6.5% rejection rate with ideal data
- [FINDINGS] CRSE worst case (G=12, covariate clustering=0.9): amse = −0.40, rejection rate >50%
- [FLAG] Bootstrap instability: >1% rejection rate swing with two different seeds at G=24
- [FIG] Figure 2 — amse and rejection rates across G and covariate clustering levels; dramatic CRSE degradation at high clustering/low G clearly visible [SLIDE]
- [FIG] Figure 5 — CESE vs CBSE across scenarios: CESE flatlines while CBSE degrades from scenario C onward [SLIDE]

**Empirical Examples [pp. 15-17]**
- [FINDINGS] State voter registration (G=50): CRSE finds 4 significant coefficients; CBSE finds 2; CESE finds 1
- [FINDINGS] Comparative politics (G=51): CRSE Wald test χ²=9.88 (p=0.007); CBSE χ²=4.78 (p=0.092); CESE χ²=3.80 (p=0.150)
- [EFFECTSIZE] Presidential power β = −0.63; SE from 0.201 (CRSE) to 0.372 (CESE) — 85% larger
- [WARN] Flagship comparative politics finding that CRSE endorses at p<0.01 but CESE does not support — downstream claims may be fragile
- [REPLICATION] Harvard Dataverse: https://doi.org/10.7910/DVN/IABJEB

---

## 9. Wooldridge (2023) — *What is a Standard Error?*
**Journal:** Journal of Econometrics | **Read:** 2026-04-02

### Reading Notes

**Introduction [pp. 1-3]**
- [RQ] What is a standard error, and how should it be computed? Paper argues there is no widespread agreement on the proper definition, let alone on computation in non-IID settings
- [CONTRIB] Distinguishes clearly between (1) the sampling standard deviation — unknown population quantity SD(X̄) = σ/√n — and (2) the standard error SE(X̄) = S/√n, an estimator of that quantity
- [TABLE] Table 1 — Terminology: σ = pop SD; S/s = sample SD; σ/√n = sampling SD; S/√n = standard error — useful for courses where students conflate population and sample quantities [SLIDE]
- [STATS] SE(X̄) is not unbiased for SD(X̄) by Jensen's inequality (downward bias; no unbiased estimator exists), but is consistent
- [WARN] Finite population correction rarely taught in econometrics; highly relevant when units are counties, states, or countries — researcher is often observing the entire population
- [XREF] Finite population / no-sampling-uncertainty case elaborated in abadie_et_al_2020 via design-based framework

**Model-Based Approach [pp. 3-6]**
- [STATS] Under Gauss-Markov: σ̂² = SSR/(n−k) yields standard OLS SEs; asymptotic sandwich formula: V = [E(X'X/n)]⁻¹ · E(X'UU'X/n) · [E(X'X/n)]⁻¹
- [TEACH] Core insight on why naive plug-in fails: OLS first-order conditions force X'Û = 0, so X'ÛÛ'X/n = 0 always — can't estimate B_n by substituting residuals without imposing structure
- [STATS] White (1980) HC0: consistently estimates B_n by substituting squared OLS residuals
- [WARN] Truncation lag choice for HAC is not innocuous: estimates can differ meaningfully across reasonable lag selections even in moderately large samples
- [STATS] Spatial extensions: Conley (1999) extends HAC to two-dimensional grids; Driscoll-Kraay (1998) handles both cross-sectional and time-series dependence

**Model-Based Approach and Clustering [pp. 4-6]**
- [FLAG] The cluster level choice is not statistically resolvable under the MB approach: county vs. state vs. census division produces different SEs, and differences persist as n grows
- [WARN] "Keep clustering until it stops mattering" is not principled; will systematically over-cluster when TE heterogeneity or X heterogeneity is present across clusters
- [TABLE] Table 2 — SE simulations: population N=100,000; 10% sample; G=50 fine / H=10 coarse clusters; three designs varying TE heterogeneity and X distribution [SLIDE]
- [FINDINGS] Design 2 (constant TE, heterogeneous X): OLS clustered SEs >3× sampling SD at G=50; >7× at H=10; FE clustered SEs fine
- [FINDINGS] Design 3 (heterogeneous TE, homogeneous X): OLS clustered SE at g-level >4× sampling SD; FE clustered SE 8.5× — coarser clustering even worse
- [TEACH] Key insight: high estimated within-cluster correlation can be an artifact of TE heterogeneity across clusters — using correlation as a clustering diagnostic leads you astray in exactly this case
- [XREF] AAIW (2023) Table II: clustering SEs can be on average >20× the true sampling SD in similar simulation designs

**Design-Based and Sampling-Based Approach [pp. 7-8]**
- [CONTRIB] AAIW (2020/2023) key result: when ρ_n = 1 (full population) and assignments independent across i, cluster-robust variance estimators are inappropriate — no sampling uncertainty, only assignment uncertainty
- [FINDINGS] AAIW (2023): LZ estimator always ≥ correct asymptotic variance; with homogeneous ATE → LZ correct; with heterogeneous ATE + all clusters observed → LZ can be very conservative
- [STATS] CCV estimator lies between conservative LZ and correct variance; applicable when cluster sizes are large and clusters have sufficient treated and control units
- [TEACH] Practical diagnostic from DB/SB: ask (1) Do we observe the full population or a sample? (2) Was assignment independent or correlated within clusters? More principled than correlogram-based tests
- [CLIENT] "If you're studying all US states and the policy varies independently across states, clustering at the state level inflates your standard errors for no valid reason."
- [XREF] Xu (2021) extends AAIW DB/SB framework to M-estimation; Xu & Wooldridge (2022) extends to spatial correlation

**Conclusion [pp. 8]**
- [DECISIONS] Recommends combining DB and SB approaches rather than defaulting to MB clustering: forces researcher to think explicitly about whether the full population is observed and what drives variation in key explanatory variables

---

## Cross-Cutting Themes

### When to Cluster
- Cluster at the level of **treatment assignment**, not at the level where residuals happen to be correlated (Abadie 2023, Wooldridge 2023)
- If treatment is randomly assigned to individuals, do not cluster even if residuals are within-cluster correlated (Abadie 2023)
- If the full population (or most of it) is observed, conventional cluster SEs are likely too conservative; consider CCV or TSCB (Abadie 2023, Abadie et al. 2020)
- "Keep clustering until it stops mattering" is not a principled rule; large cluster–robust SE gaps often indicate over-clustering, not under-clustering (Wooldridge 2023, Abadie 2023)
- High estimated within-cluster correlation can be an artifact of TE heterogeneity, not actual error correlation — using correlation as a clustering diagnostic leads you astray (Wooldridge 2023)

### Few Clusters
- CRVE consistency requires G→∞; corrections are needed regardless of total N (Cameron & Miller 2015, Imbens & Kolesár 2016)
- Best performers with few clusters: CR2+T(v*) [Imbens & Kolesár] or CR3+T(G-1) [Cameron & Miller]
- Wild cluster bootstrap (Rademacher; Webb 6-point for G<10) is preferred over pairs bootstrap, which collapses with few clusters or limited treatment variation
- CESE outperforms CRSE and CBSE in accuracy and reproducibility (Jackson 2019)
- K_BM is a key diagnostic: K_BM << N-2 signals unreliable EHW/LZ CIs regardless of sample size (Imbens & Kolesár 2016)
- Covariate clustering (between-cluster share of total X variance) is the dominant but overlooked driver of CRSE bias (Jackson 2019)
- MacKinnon-Webb "rule of 42" (G≥42 sufficient) is not supported — G=48 still shows above-nominal rejection rates under ideal conditions (Jackson 2019)

### Spatial Data
- HC and small-cluster SEs are severely unreliable with spatially correlated data (Conley & Kelly 2025)
- Two-step approach: (1) augment with spatial basis (tensor spline PCs selected by BIC); (2) apply BCH (~4 large k-medoids clusters) or IM inference (Conley & Kelly 2025)
- Nearly all 30 persistence studies surveyed by Conley & Kelly lose significance under proper spatial inference
- Conley (1999) spatial-HAC with a fixed bandwidth still over-rejects under high spatial correlation; large-cluster methods (BCH, IM) are more reliable

### What Standard Errors Measure
- The SE formula gives a lower bound: it measures within-model variation, not full uncertainty relative to the real-world target (Gelman 2023)
- The right SE requires specifying the estimand and the generalization of interest (Abadie et al. 2020, Gelman 2023, Wooldridge 2023)
- At ρ=0 (negligible sampling fraction), EHW is fine; at ρ=1 (full population), only design-based variance remains; EHW overstates for intermediate ρ when TEs are heterogeneous (Abadie et al. 2020)
- SE is not unbiased for the sampling SD (Jensen's inequality), but is consistent; this is rarely taught and matters when observing the entire population (Wooldridge 2023)

### p-Values and Reporting
- Most economics questions are estimation problems (magnitude and uncertainty), not hypothesis testing problems — p-values are irrelevant to estimation (Imbens 2021)
- Report point estimates + SEs; prefer CIs over significance stars; prefer Bayesian posterior intervals where feasible (Imbens 2021)
- Treating insignificant results as true zeros is the key practical harm of over-reliance on p-values (Imbens 2021)
- p-value bans backfire: BASP's ban increased overclaiming because authors overstated conclusions when the p-value discipline was removed (Imbens 2021)
