# Standard Errors Guide (`standard-errors.qmd`) — Master Edit List

Consolidated from two independent skeptical reviews of the full guide:
- **Neitzche** (senior statistician) — formula completeness/correctness, clean code, tight accurate prose.
- **Nash** (econometric wizard) — practitioner experience, honest caveats, reproducibility, resource quality, terminal-code hunting.

Each edit lists a **paste-ready fix** and an **agent proposal** (persona / model / prompt) where additional scrutiny — verifying a package/API, finding a cleaner method, confirming citation metadata — adds value. Where the fix is already verified, it is marked **Direct apply**.

---

## GRADE

| Reviewer | Grade | One-line verdict |
|----------|-------|------------------|
| **Neitzche** | **B / B−** | Correct conceptual spine and strong code apparatus, but several *displayed formulas* a PhD student would copy are imprecise or wrong (HAC kernel/bandwidth self-contradiction, K_BM mis-defined, Conley kernel undefined) plus one R code bug. Fix the formula precision + two code bugs → **A−**. |
| **Nash** | **B / B−** | Serious, well-structured, honest caveats and excellent core references, but the flagship terminal-code case (Abadie CCV/TSCB) sends readers to clone a repo, three code chunks are subtly wrong/non-reproducible, and a few caveats are incomplete. Fix the terminal case, the wrong chunks, and K_BM → **A−**. |

**Both reviewers independently land at B/B− and name the same path to A−.** Three Criticals and ~7 Majors stand between this guide and publication-grade.

---

## RE-AUDIT (Round 2) — after the A− + A/A+ passes

Both reviewers re-read the full revised guide from scratch and **independently re-graded A−** (up from B/B−). Both verified that every prior Critical was fixed *correctly* (HAC formula, K_BM, CR2, coeftest, CRVE formula, HC0 label, null-imposed wild bootstrap, percentile-t rates, Conley kernel) and that the Monte Carlo table matches the committed CSV row-by-row. Remaining punch list to reach a clean **A**:

**Consensus (both reviewers):**
- ✅ **R2-1 (Major) · Ship the Monte Carlo at M=2000.** DONE: rerun at M=2000/B=999 (MCSE ≈ 0.005), caption + prose updated, numeric contrasts restricted to well-resolved small-G cells.
  - **A+ upgrade also applied (user-directed):** the table was **moved into the spine** (new `## Does the choice matter? A simulation` section between Bootstrap and Interpretation — it's the centerpiece, no longer buried in the Appendix) and is now **rendered from the committed `scripts/se_monte_carlo_results.csv`** via an executable chunk (`#| label: tbl-montecarlo`), so the numbers can't drift from the code. A collapsible "How this table was generated" callout shows the seeded DGP + loop (`eval=FALSE`). This closes the "static table taken on faith" item that was holding A+.
- **R2-2 (Major→Minor) · Worked-walk number collision.** The HC SE prints as "0.003," the same glyph as β̂=0.003, blunting the "order of magnitude smaller than the 0.029 clustered SE" punchline. Neitzche verified the arithmetic is correct (it's a genuine coincidence); fix is to disambiguate (flag the coincidence) and/or use inline R so numbers can't drift from the eval'd chunks. *(Nash IW-1, Neitzche #9)*

**Neitzche — newly-introduced math errors (Major):**
- **R2-3 · MLE/GLM sandwich sign.** "$\mathbf{A}^{-1}\mathbf{B}\mathbf{A}^{-1}$, where $\mathbf{A}$ is the (expected) Hessian" omits the sign: $\mathbf{A} = -\mathbb{E}[\partial^2\ell/\partial\theta\partial\theta^\top]$ (the information matrix). Fix: "(expected) **negative** Hessian — the information matrix." *(GLM FAQ)*
- **R2-4 · IV/2SLS "exactly as to OLS" overstates.** Asymptotic sandwich carries over, but it uses first-stage-**projected** regressors and HC2/HC3/CR2 do **not** transfer mechanically. Fix: say "asymptotic sandwich logic carries over… finite-sample leverage corrections do not transfer mechanically; use an IV-specific CR2 (`clubSandwich` supports `ivreg`)."
- **R2-5 · CCV "closed form" overclaims exactness.** The convex blend $V_{robust}+(1-\rho)(V_{cluster}-V_{robust})$ is an **interpolation/approximation**, not the exact AAIW CCV (which comes from the potential-outcomes decomposition). *(Note: Nash supplied this formula in round 1; Neitzche flags the exactness claim. Resolution: relabel as "a convenient approximation to CCV," keep it, verify against AAIW 2023.)* ρ-limits are directionally correct.

**Merged Minors:**
- **R2-6** · `sandwich::vcovCL` default factor is $G/(G-1)$ only, not the full Stata $\tfrac{G}{G-1}\tfrac{N-1}{N-k}$ — don't lump "Stata/`sandwich`" on that constant. *(Neitzche #8)*
- **R2-7** · `psmatch2` does **not** report Abadie–Imbens SEs by default — credit only `teffects nnmatch`. *(Nash FAQ-2)*
- **R2-8** · RI FAQ cross-reference promises a test-inversion snippet in the near-census FAQ, which has none — add a 3-line test-inversion sketch to the RI FAQ itself. *(Nash FAQ-3)*
- **R2-9** · `xtscc` (Driscoll–Kraay, Stata) is user-written — mark `ssc install xtscc` in the Appendix table, as done for `acreg`/`boottest`. *(Nash FAQ-1)*
- **R2-10** · Delete orphaned weak bib entries `tsiebelStataPython` + `stataJournalClusterSE` (uncited, harmless, but invite re-citation). *(Nash REF-1)*
- **R2-11** · Heiss tutorial link now points to blog root, not the SE post — deep-link or swap for Grant McDermott's notes. *(Nash REF-2)*
- **R2-12** · Driscoll–Kraay "consistent as" cell under-specified vs the HAC row: add "($L\to\infty$, $L/T\to0$; cross-section $N$ may be fixed)." *(Neitzche #5)*
- **R2-13** · Assumptions-table "Assumes (independence)" column: Conley/HAC cells describe structure, not independence — rename column "Independence / structural assumption" (or reword the two cells). *(Neitzche #6)*
- **R2-14** · BJS imputation estimator named without a citation while CS/SA are cited — add Borusyak–Jaravel–Spiess (2024) to bib or drop the named attribution. *(Neitzche #10)*
- **R2-15** · Name the CCV reference concretely (Harvard Dataverse DOI) instead of "distributed by the authors' teams." *(Nash TN-1)*
- **R2-16** · Confirm `renv.lock`/`requirements.txt` actually exist and the pinned versions resolve (the reproducibility claim is otherwise aspirational). *(Nash MC-2)*
- **R2-17** · Optional: convenience-sample Appendix row could add "if the sample still has internal grouping (sites, batches), cluster on it — HC is a floor." *(Nash P-3)*
- **R2-18** · Optional: staggered-DiD Python parenthetical — `differences` (Callaway–Sant'Anna), `pyfixest` (Sun–Abraham). *(Nash FAQ-4)*

**Verdict:** both say fix the Majors (R2-1, R2-3, R2-4, R2-5) + the worked-walk numbers and rerun the simulation at M=2000 → clean **A**; A+ ceiling held mainly by the table being static rather than executed-at-render.

---

## ✅ Running-example reframe (added during the A− pass, user-directed)

Beyond the listed edits, the Nunn & Wantchekon running example was **reframed around the paper's actual SE schemes** (decision: "paper's schemes replace country framing" + "explicit fidelity caveat"):

- **`scripts/se_comparison.R`** rewritten: the figure now shows OLS, HC3, and the three schemes the authors actually report — cluster by ethnic group (G ≈ 185), two-way ethnic × district, and Conley spatial with a 5° uniform window — on one like-for-like estimation sample. **Gif regenerated** (`images/se_comparison.gif`); the three design-aware methods come out ~identical (≈ 0.029) and ~9× wider than OLS/HC3 (≈ 0.003), reproducing the paper's own "essentially identical" finding. *(The committed script keeps the gganimate approach like the guide's other gifs; the asset here was rendered via a gifski fallback because the sandbox's ggplot2 4.0.2 breaks gganimate — re-running in a normal env regenerates the animated version.)*
- **Decision Walkthrough** rewritten into three beats: *what the authors did* (reported all three, found them identical, settled on two-way), *how we'd reason from scratch* (cluster at the ethnic-group level where the regressor varies; modern spatial practice = basis de-trending + placebo per Conley–Kelly 2025), and *a note on cluster count* (country-level G=16 is the deliberate few-cluster teaching contrast for the Bootstrap section).
- **Interpretation** rewritten to match the five-method figure, state the "all design-aware ≈ identical" lesson, give the current-practice pick, and carry the **fidelity caveat** (bivariate model → magnitudes differ from the paper's controlled/fixed-effects estimates).
- **Pedagogy stance** (user-directed): this is a teaching guide, not a replication — show the authors' tools and approach honestly, then be explicit about how current advice (design-based clustering; Conley–Kelly on spatial false positives) updates the 2011 choices.

## Cross-cutting note
Line numbers reference the `standard-errors.qmd` source as read during review. Several fixes touch both prose and the adjacent code chunk — apply together. Where a fix mirrors something already corrected in the decision tree (`decision-tree/decision-tree-edits.md`), it is noted so the two artifacts stay consistent.

**Model legend:** `opus` = hardest judgment / method correctness / resource curation; `sonnet` = package/API/citation verification with web search or a quick R/Python run; `haiku` = mechanical text/metadata fix; `fable` = fast drafting.

---

## 🔴 TIER 0 — Critical (mathematically wrong / flagship terminal code)

### ✅ SE-T0-1 · Bell–McCaffrey $K_{BM}$ is mis-defined — **APPLIED** (qmd FAQ; added `bellMcCaffrey2002` to .bib)
- **Location:** FAQ "cluster count 20–50," line 975. Quote: "$K_{BM} = (\sum \lambda_i)^2 / \sum \lambda_i^2$ (where the $\lambda_i$ are eigenvalues of the hat matrix restricted to treated observations)."
- **Source:** Neitzche #16 + Nash H1 (**convergence**)
- **Issue:** The parenthetical is wrong. The $\lambda_j$ are eigenvalues of the matrix governing the sampling distribution of the *target contrast's* CR2 variance estimator — **not** "eigenvalues of the hat matrix restricted to treated observations" (the hat matrix has a $\{0,1\}$-ish spectrum unrelated to this). A reader copies a definition that yields a different, undefined quantity. The companion decision tree already states it correctly.
- **Edit:** replace the parenthetical:
  > "where the $\lambda_j$ are the eigenvalues of the matrix governing the sampling distribution of the contrast's CR2 variance estimator (Bell & McCaffrey 2002; Imbens & Kolesár 2016). It is computed automatically by `clubSandwich::coef_test()`; you do not form it by hand. Roughly, $K_{BM}$ counts how many clusters effectively carry information about your target coefficient."
- **Agent:** Direct apply — no agent needed. (Both reviewers converged; matches tree glossary fix T1-10/k_bm.)

### ✅ SE-T0-2 · HAC long-run variance formula is internally inconsistent — **APPLIED**
- **Location:** "HAC Standard Errors," lines 632–634. Quote: "$\hat{S} = \sum_{j=-L}^{L} k(j/(L+1)) \hat{\Gamma}_j$ … weight of $1 - j/(L+1)$, declining linearly from 1 at $j=0$ to 0 at $j=L$."
- **Source:** Neitzche #1
- **Issue:** With Bartlett $k(z)=1-|z|$ and argument $j/(L+1)$, the weight at $j=L$ is $1/(L+1)\neq 0$ — contradicting "to 0 at $j=L$." Also $\hat\Gamma_{-j}=\hat\Gamma_j^\top$ is never stated though the sum runs over negative $j$, and $\hat\Gamma_0$ should be flagged as the HC term so HAC visibly nests HC.
- **Edit:** state one consistent convention:
  $$\hat{S} = \hat{\Gamma}_0 + \sum_{j=1}^{L} k\!\left(\tfrac{j}{L+1}\right)\left(\hat{\Gamma}_j + \hat{\Gamma}_j^\top\right), \qquad \hat{\Gamma}_j = \frac{1}{T}\sum_{t=j+1}^{T} \mathbf{x}_t \mathbf{x}_{t-j}^\top\, \hat{e}_t\, \hat{e}_{t-j}.$$
  Prose: "The Newey–West (1987) estimator uses the Bartlett kernel $k(z)=1-|z|$ for $|z|\le1$ (else 0), giving lag-$j$ autocovariance the weight $1-j/(L+1)$, which declines linearly from 1 at $j=0$ to $1/(L+1)$ at the last included lag $j=L$ and is exactly 0 for $j>L$. This tapering guarantees $\hat S$ is positive semi-definite. The $\hat\Gamma_0$ term is the heteroskedasticity-robust (HC) component, so HAC nests HC."
- **Agent:** Direct apply — no agent needed. (Neitzche verified; standard Newey–West 1987.)

### ✅ SE-T0-3 · CCV/TSCB terminal code — sends reader to clone replication repo — **APPLIED** (closed-form CCV in R+Python + full TSCB pseudocode + inline design caveat; repo pointer kept general. NOTE: Dataverse DOI still worth verifying via the proposed agent before final publish.)
- **Location:** FAQ "I observe most or all of the relevant clusters," lines 999–1014. Quote: "available in the authors' replication code rather than as a single base-package argument."
- **Source:** Nash T1 (Critical) + Neitzche #19 (sketch caveat) (**convergence**)
- **Issue:** The guide's intellectual foundation is Abadie et al., yet the one place a reader must *run* CCV/TSCB gives a four-line prose sketch + a repo pointer. The sketch omits the sampling fraction ρ (the whole point), Stage 1 is too vague to implement, and it ignores that CCV has a closed form and maintained implementations now exist. Mirrors decision-tree T0-3.
- **Edit:** replace the sketch with (a) runnable closed-form CCV in R + Python, then (b) a fully-specified TSCB algorithm as labeled pseudocode with the ρ assumption and empty-cell guards, then (c) honest reference pointers. Use the exact blocks from `decision-tree/decision-tree-edits.md` §T0-3 (CCV closed-form + TSCB pseudocode), adapted to the guide's prose. Add Neitzche's inline caveat to Stage 1: `# Stage 1 must mirror the ACTUAL assignment design (fixed # treated clusters, blocking/strata); a uniform permutation is valid only under complete cluster randomization.`
- **Agent (recommended — verify the reference pointer):**
  - **Persona:** Nash.
  - **Model:** `sonnet` (web search).
  - **Prompt:** "Verify and return citable strings: (1) the AAIW (2023, QJE) replication archive — confirm the Dataverse DOI (candidate: 10.7910/DVN/27VMOT) resolves and is the right paper; (2) whether a maintained Stata `ccv`/`tscb` package exists, its authors, and install command. Do NOT invent. If a pointer is wrong, give the correct one or tell me to drop it. (Same verification feeds decision-tree T0-3 — reuse the answer.)"

---

## 🟠 TIER 1 — Major

### ✅ SE-T1-1 · R HC chunk passes `type="HC2"` to `coeftest` — **APPLIED** (both HC and cluster chunks → explicit computed-matrix form)
- **Location:** Robust SE, R tab, lines 330–332. Quote: `lmtest::coeftest(regression, vcov = sandwich::vcovHC, type = "HC2")`.
- **Source:** Neitzche #4 + Nash H2 (**convergence**)
- **Issue:** Passing the bare function + `type=` relies on `...`-forwarding through `coeftest` into `vcovHC`. It works in current versions but is fragile, opaque, and inconsistent with the Stata/Python tabs and the cluster example (line 448, same pattern). Reader can't see that `type` is a `vcovHC` argument.
- **Edit:** use the explicit computed-matrix form everywhere:
  ```r
  regression_robust <- lmtest::coeftest(
    regression, vcov = sandwich::vcovHC(regression, type = "HC2")
  )
  regression_robust
  ```
  and for clustering (line 448): `vcov = sandwich::vcovCL(regression, cluster = ~isocode)`.
- **Agent (light — confirm what the current call returns):**
  - **Persona:** Neitzche.
  - **Model:** `haiku` (or `sonnet` if running R).
  - **Prompt:** "In current `lmtest`/`sandwich`, does `coeftest(fit, vcov = sandwich::vcovHC, type='HC2')` actually return HC2, or does `vcovHC`'s own default (HC3) win? Confirm whether `type` is forwarded. One-paragraph answer; this decides whether SE-T1-1 is a correctness bug or a style fix."

### ✅ SE-T1-2 · Cluster-Robust section gives NO variance formula — **APPLIED** (added Liang–Zeger formula + finite-sample factor; added `liangZeger1986` to .bib)
- **Location:** entire "Cluster-Robust Standard Errors" section, lines 418–501.
- **Source:** Neitzche #8
- **Issue:** Every other correction section displays its estimator (HC line 294, spatial 509, HAC 628). The most-used correction in social science gets prose + code but no Liang–Zeger formula and no small-sample factor.
- **Edit:** add after line 420:
  $$\hat V_{CR}(\hat{\boldsymbol\beta}) = (\mathbf X^\top\mathbf X)^{-1}\!\left(\sum_{g=1}^{G}\mathbf X_g^\top \hat{\mathbf e}_g \hat{\mathbf e}_g^\top \mathbf X_g\right)\!(\mathbf X^\top\mathbf X)^{-1},$$
  > "where $g=1,\dots,G$ indexes clusters, $\mathbf X_g$ stacks cluster $g$'s rows and $\hat{\mathbf e}_g$ its residual vector; the meat allows *arbitrary* within-cluster correlation while assuming independence *across* clusters. Software multiplies by a finite-sample factor $c=\tfrac{G}{G-1}\cdot\tfrac{N-1}{N-k}$ (the Stata/`sandwich` default), and inference uses $t_{G-1}$. Consistency requires $G\to\infty$."
- **Agent:** Direct apply — no agent needed.

### ✅ SE-T1-3 · Displayed sandwich is HC0 but never labeled as such — **APPLIED** (labeled HC0 + standardized $k$)
- **Location:** Robust SE, lines 294–296.
- **Source:** Neitzche #5
- **Issue:** $\hat V$ with $\hat\Omega=\mathrm{diag}(\hat e_i^2)$ is exactly HC0; the variant table then reweights the diagonal, so without the label HC2/HC3 look like different estimators rather than reweightings. Also parameter-count symbol drifts ($k$ vs $p$ vs $n-k$ vs $G-1$).
- **Edit:** after the formula: "This displayed form, with $\hat\Omega=\mathrm{diag}(\hat e_1^2,\dots,\hat e_n^2)$, is the HC0 estimator. The variants below leave the sandwich structure unchanged and only reweight the diagonal to correct HC0's finite-sample downward bias." Standardize on $k$ (or $p$) for parameter count throughout.
- **Agent:** Direct apply — no agent needed.

### ✅ SE-T1-4 · Wild bootstrap: omits that small-$G$ validity needs the NULL-IMPOSED version — **APPLIED**
- **Location:** "Wild Bootstrap," lines 753–757; R chunk line 831 (`boottest`).
- **Source:** Neitzche #12
- **Issue:** The prose describes the *unrestricted* wild bootstrap ($y^*=\hat y+w_i\hat e_i$) then says it's preferred for $G<30$ and shows `boottest` — which actually imposes the null and inverts a bootstrap-$t$. Reader thinks the unrestricted recipe fixes small-$G$; it's the restricted version that does.
- **Edit:** add after line 757:
  > "For small-$G$ cluster inference, the recommended variant imposes the null when generating pseudo-outcomes — residuals are taken from the model re-estimated under $H_0:\beta_k=0$ — and inference inverts the bootstrap $t$-statistic rather than reading off an SD (Cameron, Gelbach & Miller 2008; Roodman et al. 2019). This restricted version is what `fwildclusterboot::boottest` and Stata's `boottest` compute; the simpler unrestricted $y_i^*=\hat y_i+w_i\hat e_i$ form is adequate for heteroskedasticity but not for the few-cluster problem."
- **Agent:** Direct apply — no agent needed.

### ✅ SE-T1-5 · Percentile-$t$ accuracy rates attached to the wrong interval type — **APPLIED** (one-sided vs two-sided rates; added `hall1992` to .bib)
- **Location:** Bootstrap, line 784. Quote: "$O(n^{-1})$ coverage error versus $O(n^{-1/2})$ for simple percentile intervals."
- **Source:** Neitzche #14
- **Issue:** Those are the *one-sided* rates. Two-sided equal-tailed intervals (what the guide builds) enjoy error cancellation: percentile is already $O(n^{-1})$ and percentile-$t$ is $O(n^{-3/2})$ (Hall 1992). The headline numbers are too pessimistic for the interval being discussed.
- **Edit:**
  > "By standardizing each bootstrap estimate by its own standard error, percentile-$t$ achieves higher-order accuracy: for one-sided intervals the coverage error is $O(n^{-1})$ versus $O(n^{-1/2})$ for the basic percentile interval; for the two-sided equal-tailed intervals reported here, symmetry improves both — to $O(n^{-3/2})$ for percentile-$t$ versus $O(n^{-1})$ for the percentile interval (Hall 1992)."
- **Agent:** Direct apply — no agent needed.

### ✅ SE-T1-6 · Conley spatial formula leaves kernel/bandwidth undefined — **APPLIED**
- **Location:** Spatial SE, lines 509–511.
- **Source:** Neitzche #10
- **Issue:** Formula uses $k(d_{ij}/h)$ but prose calls $h$ "the distance cutoff" and $k$ "downweights distant pairs" — conflating cutoff (hard zero beyond $h$) with smooth decay. Reader can't tell which. $d_{ij}=d_{ji}$ (symmetry) and the $i=j$ HC0 diagonal also unstated.
- **Edit:**
  > "where $d_{ij}=d_{ji}$ is the distance between units $i$ and $j$, $h$ is the bandwidth (distance cutoff), and $k(\cdot)$ is a kernel with $k(0)=1$ and $k(u)=0$ for $u>1$, so pairs farther apart than $h$ get zero weight. The uniform kernel $k(u)=\mathbf 1\{u\le1\}$ gives Conley's original hard-cutoff form; the Bartlett kernel $k(u)=(1-u)_+$ lets correlation decay linearly to zero at $h$ and guarantees a positive-semidefinite $\hat V$. The $i=j$ terms reproduce the heteroskedasticity-robust (HC0) diagonal."
- **Agent:** Direct apply — no agent needed.

### ✅ SE-T1-7 · Python "Conley" tab silently computes Kelejian–Prucha — **APPLIED** (prominent top-of-tab note added; mid-code note already present). Optional verification agent (mature Python Conley?) still available.
- **Location:** Spatial, Python tab, lines 564–573.
- **Source:** Nash S1
- **Issue:** Header/prose/R/Stata tabs all promise Conley; the Python tab delivers K–P spatial HAC (honestly noted in a buried comment). Cross-language comparison — the point of the tabs — yields non-comparable numbers.
- **Edit:** add at the top of the Python tab:
  ```python
  # NOTE: There is no mature drop-in Conley (1999) estimator in Python.
  # spreg below computes the Kelejian-Prucha spatial HAC — related but NOT
  # identical to Conley. For Conley SEs proper, use fixest::feols(vcov=conley())
  # in R (see R tab), or compute the distance-kernel sandwich manually.
  ```
  (Or rename the tab content "Spatial HAC (Kelejian–Prucha).")
- **Agent (verify the Python landscape):**
  - **Persona:** Nash.
  - **Model:** `sonnet` (web search).
  - **Prompt:** "Is there a maintained Python package that computes the genuine Conley (1999) spatial HAC SE (not Kelejian–Prucha)? Check `pysal`/`spreg`, `econtools`, and any newer package. If one exists, give the exact call; if not, confirm the honest 'use R `fixest`' note is the right move."

### ✅ SE-T1-8 · Surface the maintained `spatInfer` package — **APPLIED** (confirmed in .bib; mentioned in Spatial section + decision walkthrough)
- **Location:** Spatial section, after line 520; `.bib kelly2025` records `github.com/morganwkelly/spatInfer`.
- **Source:** Nash T2
- **Issue:** The exact paper the guide leans on for spatial-SE credibility ships a maintained R package implementing its placebo workflow — never surfaced. Leaving the author-blessed reproducible tool on the table.
- **Edit:** add:
  > "For the placebo-based spatial inference of Conley and Kelly (2025) specifically — spatial-basis de-trending plus a synthetic-treatment placebo test — the authors maintain the `spatInfer` R package ([github.com/morganwkelly/spatInfer](https://github.com/morganwkelly/spatInfer)), which automates basis selection and the placebo reference distribution."
- **Agent (verify maintenance + usage):**
  - **Persona:** Nash.
  - **Model:** `sonnet`.
  - **Prompt:** "Confirm `spatInfer` (github.com/morganwkelly/spatInfer) exists, is reasonably maintained, and give the minimal worked call (basis selection + placebo test). Also reconcile authorship: is the 2025 spatial paper solo-Kelly or Conley–Kelly? (Feeds SE-T2 citation fix.)"

### ✅ SE-T1-9 · Weights/WLS + CRVE consistency caveat missing — **APPLIED** (new bullet in key design questions)
- **Location:** Cluster-Robust, "key design questions," lines 425–430.
- **Source:** Nash C1
- **Issue:** With survey weights or WLS, the ordinary cluster sandwich (`vcovCL`, `feols` default) is **not consistent**; you need `clubSandwich` CR2. The guide recommends `vcovCL` as default and never warns weighted-regression users.
- **Edit:** add a bullet after line 430:
  > "**Weights change the variance estimator.** If you run WLS or use survey/probability weights, the ordinary cluster sandwich is not consistent for the weighted estimator. Use `clubSandwich::coef_test(fit, vcov = 'CR2', cluster = ~ g)` (or a survey-design estimator), not `vcovCL` — the leverage correction is what restores validity under non-constant weights."
- **Agent:** Direct apply — no agent needed. (Consistent with tree T1-1 survey branch.)

### ✅ SE-T1-10 · Python cluster tab reports normal (z) critical values — **APPLIED** (warning comment added to chunk)
- **Location:** Cluster-Robust, Python tab, lines 455–465.
- **Source:** Nash C3
- **Issue:** `statsmodels` `cov_type="cluster"` reports z inference and a different small-sample adjustment than R/Stata; at G=16 this understates the interval versus the $t(G-1)$ the guide's own caveat implies. Python reader gets anti-conservative p-values with no warning.
- **Edit:** add to the Python chunk + a sentence below:
  ```python
  # NOTE: statsmodels reports normal (z) critical values and a different small-sample
  # adjustment than R/Stata. With few clusters this understates uncertainty. Apply
  # t(G-1) critical values manually, and prefer the wild cluster bootstrap at G=16
  # (see Bootstrap section); pyfixest offers CRV3 and wild bootstrap natively.
  ```
- **Agent:** Direct apply — no agent needed. (Verify `pyfixest` CRV naming via tree T2-21 agent.)

### ✅ SE-T1-11 · Two weak/fragile "tutorial" resources below the bar — **APPLIED** (removed Medium post + anonymous Stata Journal; added Zeileis-Köll-Graham 2020 JSS + clubSandwich vignette; de-rotted Heiss link. NOTE: A+ resource curation — MNW 2023, Roth et al — is deferred to the Path-to-A+ section.)
- **Location:** References → Tutorials, lines 1036, 1038; `.bib` `tsiebelStataPython` (a Medium post), `heissRobustSE` (rotting course URL); also under-specified `gelman2023`, anonymous `stataJournalClusterSE` (line 1040).
- **Source:** Nash R1
- **Issue:** A guide is judged by the company its citations keep. A Medium post and a course-specific URL that rots are not resources to stake a PhD student's understanding on when authoritative, maintained alternatives exist.
- **Edit:**
  - Replace the Medium post with the **`sandwich` JSS papers** (Zeileis 2004, "Econometric Computing with HC and HAC…"; Zeileis, Köll & Graham 2020, "Various Versatile Variances") — authoritative, maintained, on point for R↔Stata equivalence.
  - Replace the rotting Heiss course URL with his stable blog version, or lean on the `fixest`/`clubSandwich` vignettes.
  - Fill missing DOIs/pages for `gelman2023`, `wooldridge2023`.
  - Replace the anonymous `stataJournalClusterSE` with a proper citation (Cameron–Miller 2015, already cited, or Nichols & Schaffer).
- **Agent (curation — judgment + lookups):**
  - **Persona:** Nash.
  - **Model:** `opus`.
  - **Prompt:** "Audit the Tutorials/References section of `standard-errors.qmd` against `standard-errors.bib`. For each weak entry (Medium post, rotting course URL, anonymous Stata Journal PDF, under-specified gelman2023/wooldridge2023), propose the best authoritative replacement with full citation + DOI/stable URL + one-line 'why better.' Prioritize peer-reviewed/maintained sources. Return paste-ready .bib entries."

---

## 🟡 TIER 2 — Minor

> **A− pass status (applied to `standard-errors.qmd` / `.bib` unless noted):**
> ✅ SE-T2-1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 16, 17, 18, 19, 20 — applied.
> ✅ SE-T2-10 — already present in the guide (studentized-parity comment in the Python bootstrap chunk); left as-is.
> ➖ SE-T2-15 — no action needed: `.bib` already credits **Conley & Kelly (2025)**, so `@kelly2025` renders correctly and matches the tree.
> ⏸ SE-T2-13 (cross-tab NA handling) — **deferred**: still wants the proposed `sonnet` verification agent (does R `lm` / Stata `regress` / statsmodels `from_formula` listwise-delete identically here?) before touching every eval'd chunk.
> Notes: SE-T2-18 (G=16) was absorbed into the larger figure reframe below; SE-T2-20 removed the fake author URL and set StatLab → `statlab.yale.edu`.

| # | Item | Location | Fix | Source | Agent |
|---|------|----------|-----|--------|-------|
| SE-T2-1 | HAC bandwidth rule lacks rate caveat | qmd:636, 939 | "$L=\lfloor 4(T/100)^{2/9}\rfloor$ (Newey–West 1994)… MSE-optimal Bartlett bandwidth grows at rate $T^{1/3}$" | Neitzche #2 | Direct apply |
| SE-T2-2 | `NeweyWest()` prewhitens by default — two NW lines differ in 2 ways | qmd:676 vs 679 | Comment: "NeweyWest() prewhitens by default; explicit-lag call turns it off for a like-for-like comparison" (+ optionally `prewhite=FALSE` in auto call) | Neitzche #3 | Direct apply (`haiku`) |
| SE-T2-3 | Python HAC: no auto-bandwidth; `use_correction` unexplained | qmd:690-694 | Comment: maxlags is rule-of-thumb L; no Andrews auto; `use_correction=True` = small-sample dof adj; compute `floor(4*(T/100)**(2/9))` for data-driven L | Nash HA2 | Direct apply |
| SE-T2-4 | Driscoll–Kraay small-T caveat missing | qmd:643 | Append: "DK relies on a long time dimension; with short T it is unreliable — two-way clustering or time FE are safer." | Nash HA1 | Direct apply |
| SE-T2-5 | Two-way non-PD failure named without a fix | qmd:430 | Append eigenvalue-flooring note + fallback to one-way on larger dimension / wild bootstrap with min(G_A,G_B) | Nash C2 | Direct apply |
| SE-T2-6 | HC4/HC5 named in table + AI prompt but never defined | qmd:306, 283 | Either define (HC4: $(1-h_{ii})^{\delta_i}$, $\delta_i=\min(4,h_{ii}/\bar h)$, Cribari-Neto 2004) or scope prompt/table to HC0–HC3 | Neitzche #6 | Direct apply |
| SE-T2-7 | "HC3 most conservative" not uniformly true (HC4/HC5 exist in table) | qmd:305, 310; Nash H3 | Scope: "most conservative of HC0–HC3"; add to HC2 row "Exact under homoskedastic randomized assignment (Imbens-Kolesár 2016)" | Neitzche #7 + Nash H3 | Direct apply |
| SE-T2-8 | 30–50 cluster threshold reads as hard line | qmd:426 | Append: heuristic, not threshold; what governs reliability is effective DoF ($K_{BM}$), can be ≪ G−1 | Neitzche #9 | Direct apply |
| SE-T2-9 | Percentile-CI pseudocode off-by-one / index base mixed | qmd:780-781 | Make 1-based: $\beta_{(\lfloor0.025(B+1)\rfloor)}$, $\beta_{(\lceil0.975(B+1)\rceil)}$ (B=999 → 25th & 975th order stats) | Neitzche #13 | Direct apply |
| SE-T2-10 | Python bootstrap gives only percentile CI; R tab gives studentized | qmd:846-859; Nash B1 | Add sentence: "To match the R studentized interval, also store each resample's SE (`fit.bse[1]`) and standardize before quantiles"; add `boot.ci(type="stud")` self-warn comment (qmd:811-822) | Nash B1 + Neitzche #15 | Direct apply |
| SE-T2-11 | Two inconsistent $K_{BM}$ thresholds | qmd:975 ($\ll G-1$) vs 991 ($<G/3$) | Unify: "much smaller than $G-1$ — say below $G/3$" once, then reference | Neitzche #17 | Direct apply |
| SE-T2-12 | `clubSandwich` two-step call is the less-documented path | qmd:985-988 | Collapse to one-liner: `coef_test(fit, vcov="CR2", cluster=nunn$isocode)` | Neitzche #18 | Direct apply |
| SE-T2-13 | NA handling inconsistent across language tabs | qmd:164-168/188-189/223/457/842 | Drop NAs once, explicitly, on model vars at top of every tab; state N and G once | Neitzche #20 | **Agent:** Neitzche/`sonnet` — "Confirm whether R `lm`, Stata `regress`, and statsmodels `from_formula` listwise-delete identically on this dataset (does Zimbabwe drop in all?). If yes, a one-line note suffices; if no, give explicit dropna for each tab so N matches." |
| SE-T2-14 | Julia Q-Q uses raw resids vs scaled normal; `std_res` unused there | qmd:249, 255 | Standardize residuals in all four Q-Q plots, or document Julia uses raw vs fitted-scale normal | Neitzche #21 | Direct apply |
| SE-T2-15 | `kelly2025` vs tree's "Conley & Kelly (2025)" attribution mismatch | qmd:513; tree footer | Reconcile authorship across both artifacts | Neitzche #11 | **Agent:** Nash/`haiku` — "Confirm exact authorship/year of `kelly2025` in the bib and the actual paper; make the guide and decision tree cite it identically." (Fold into SE-T1-8 agent.) |
| SE-T2-16 | `jackson2019` volume/year mismatch | `.bib`:200-209 (vol 28, no.2, year 2019 — PA vol 28 is 2020) | Correct to *Political Analysis* 28(2), 2020 | Nash R2 | Direct apply (`haiku`) |
| SE-T2-17 | `fixest::conley()` cutoff units + centroid column names unverified | qmd:531-536 | Comment: "cutoff 500 is in KM because distance='spherical'"; verify `centroid_lat/long` match the .dta | Nash S2 | **Agent:** Neitzche/`haiku` — "Confirm the Nunn-Wantchekon `.dta` column names used in the conley() call exist; if not, give the correct names." |
| SE-T2-18 | G=16 example may read as the recommended answer | qmd:434-438, 921 | Add to Interpretation: "Because G=16 is below the reliable threshold, the clustered interval shown is illustrative; for this paper the wild cluster bootstrap interval is the one we would actually report." | Nash D1 | Direct apply |
| SE-T2-19 | "Two-way clustering has become the default" overstates current practice | qmd:945 | Soften: "common choice when both unit dependence and common time shocks are present, but not an automatic default — cluster where the design introduced dependence" | Nash D2 | Direct apply |
| SE-T2-20 | Author affiliation/links are template placeholders | qmd:6, 21 | Replace `authorwebpage1.com` / `yourinstitutionwebsite.com` with real URLs or remove | Neitzche #22 | Direct apply — **author input needed** |

---

## Convergence & notes
- **Both reviewers independently flagged:** the Bell–McCaffrey $K_{BM}$ mis-definition (SE-T0-1), the CCV/TSCB terminal code (SE-T0-3), the R `coeftest` `type=` issue (SE-T1-1), and "HC3 most conservative" (SE-T2-7). Treat those as settled.
- **Praise-adjacent, no action:** the `fwildclusterboot >= 0.13` global-seed version note (qmd:829) — exactly the version-awareness both reviewers want; keep it.
- **Consistency with the decision tree:** SE-T0-1 (K_BM), SE-T0-3 (CCV/TSCB), SE-T1-9 (weights/CR2), and SE-T2-15 (Conley–Kelly attribution) should be applied so the guide and `decision-tree/` agree.

## What both reviewers genuinely praised (earned)
- **King–Roberts callout** (qmd:410-419) — large robust-vs-OLS gap as a *misspecification diagnostic*, not a fix. Rare and correct.
- **"Why B=999" box** (qmd:786-794) — derives the odd-number convention correctly, well-sourced.
- **Non-Standard Errors callout** (qmd:80-90, Menkveld et al. 2024) — sophisticated, honest, usually omitted.
- **Near-census / CCV–TSCB FAQ** — correctly notes TSCB-narrower-than-CRVE is *not* guaranteed under treatment-effect heterogeneity.
- **Design-first framing throughout** and **honesty about bandwidth/cluster fragility** (G=16 warning, sensitivity reporting).
- **Bibliography core** is excellent — Abadie 2020/2023, Imbens–Kolesár, Cameron–Miller, Conley–Kelly, Roodman et al. with DOIs. This foundation is what makes B/B− recoverable to A−.

## Suggested implementation order
1. **Tier 0** (SE-T0-1, SE-T0-2, SE-T0-3) — run the SE-T0-3 reference-verification agent, then apply. These three are the difference between B− and a credible draft.
2. **Tier 1** — formula/code fixes (SE-T1-1…SE-T1-6) first, then the spatial/resource items (SE-T1-7…SE-T1-11) with their verification agents.
3. **Tier 2** — batch the direct-apply text fixes; run the focused `haiku`/`sonnet` agents for SE-T2-13/15/16/17.

**Both reviewers agree: fix the three Criticals + the ~7 Majors and this guide is an A−.**

---

# PATH TO A / A+

The Tier 0–2 fixes above get the guide to **A−** by correcting what is *wrong*. Reaching **A / A+** is a different axis — **depth, evidence, and unification on the existing scope**, not breadth into new estimators. This section was drafted by the orchestrator and **approved (with rebalancing) by both Neitzche and Nash**.

> **Shared verdict.** Both reviewers independently named the same load-bearing trio for the A→A+ jump, and the same trims. The throughline (Neitzche): *unify the math, make the mapping inspectable, state the assumptions, nail the notation, and prove the central claims with one rigorous reproducible simulation.* The practitioner test (Nash): *does a real researcher get something here they can't easily get elsewhere, and will they trust it?*

## Load-bearing core (do these or it stays A−/A)
- **A6 — Reproducible Monte Carlo coverage study** (the A+ differentiator; both reviewers ranked #1).
- **A1 — Master "design → estimand → estimator → software" table** (both ranked #2).
- **A2 — Fully worked end-to-end recommendation on the running data** (Nash #3; Neitzche "strong fourth").
- **A4 — Unified notation glossary** (Neitzche: *disqualifying* if absent — fixes the $k/p/n{-}k/G{-}1$ drift).
- **A9 — Per-estimator assumptions table** + **A11 — one-paragraph sandwich derivation** (Neitzche's highest-value omissions; he ranks A9 above most of A3 and would put A11 in the load-bearing tier for a *true* A+).

## Agreed trims (avoid scope creep / bloat)
- **FE-vs-RE SE** → one FAQ sentence (it's an estimator choice, not an SE choice). *Both.*
- **GMM SEs** → defer to a fenced "Beyond OLS" pointer, not a section. *Both.*
- **A8 sensitivity** → a single Oster-δ box framed as "the uncertainty SEs do *not* capture"; one-line Rosenbaum pointer. *Both.*
- **Mistakes gallery (A7)** → cap at 4–6 entries, each a *decision* error, not a typo. *Both.*
- **Wooldridge panel serial-correlation test** → FAQ paragraph, not a section. *Both.*

---

## 🟢 A-TIER ADDITIONS (completeness & coherence — earns the solid A)

### ✅ A1 · Master table: design → estimand → estimator → software *(load-bearing)* — **APPLIED** (12-row reference table `#tbl-se-map`; rows mirror the tree terminals; honest Python-gap notes. **Moved to a new `# Appendix` (`#appendix-se-map`)** wrapped in an `overflow-x:auto` horizontal scroller; a one-line pointer under the decision tree cross-references it.)
- **What:** a single ~10–12 row table mapping the design/sampling situation to the estimand, the recommended estimator, the small-sample caveat, and the current function in R/Python/Stata. The guide's thesis made inspectable in 30 seconds.
- **Constraint (both):** keep to ~10–12 rows; resist exhaustiveness. Rows should mirror the decision-tree terminals so the two artifacts agree.
- **Agent (recommended — assemble + cross-check against tree):**
  - **Persona:** Nash. **Model:** `opus`.
  - **Prompt:** "Build the master table for `standard-errors.qmd`: columns = [Data/design situation | Estimand | Recommended estimator | Key small-sample caveat | R | Python | Stata]. Rows must align 1:1 with the decision-tree terminals in `decision-tree/decisions.js` (cross-sectional HC2/HC3, cluster-randomized CRVE, small-G CR2/wild bootstrap, two-way, HAC, spatial/Conley, CCV/TSCB, survey design, convenience). Use only current maintained functions; where Python has no honest tool, write 'no mature tool — use R/Stata.' Return paste-ready Quarto markdown."

### ✅ A2 · Worked end-to-end recommendation on the running dataset *(load-bearing)* — **APPLIED** ("A worked decision walk" subsection closing the Interpretation: 5-step traversal of the tree → primary = ethnic-group cluster-robust SE, reported interval ≈ [−0.053, 0.059] (β̂=0.003, SE=0.029), spatial check alongside; contrasts the naive individual-HC SE (0.003, ~10× too small). Fulfills the conclusion promise made in the intro.)
- **What:** finish the collapsed "Decision Walkthrough" (qmd:122–131), which currently stops at naming features. Walk Nunn-Wantchekon through the actual tree to **a single recommended interval with the number**, and show explicitly why the naive clustered SE (G=16) is *not* the one to report.
- **Why (Nash):** "Without it the guide diagnoses but never prescribes." Closes the loop from diagnosis to a defensible reported number.
- **Agent:** Direct apply after the data fixes — uses the running example already in the guide. (Optionally `sonnet` to run the final numbers.)

### ✅ A3 (revised) · Targeted coverage additions — **APPLIED as FAQ entries** (user steer: keep the method spine focused). Five new FAQs: randomization inference (A3a; ri2/ritest, honest Python gap), IV/2SLS + weak instruments (A3b; AR/CLR, ivmodel/weakiv, Python gap), robust SEs for GLM/MLE + delta method (A3c; sandwich on glm, marginaleffects/margins) with a GMM pointer (A3f), Wooldridge panel serial-correlation test (A3d; pwartest/xtserial), and FE-vs-RE-vs-SEs (A3e, one entry). No new bib keys needed (package/method names only).
Reconciled from both reviewers (Neitzche: cut breadth; Nash: keep the high-demand practitioner pieces, compact):
- **A3a · Randomization inference as a first-class section.** *Both APPROVE.* Already implied by the design-based thesis and the CCV/TSCB FAQ; currently homeless. R `ri2`/`randomizr`, Stata `ritest`/`randcmd`; **Python has no mature finite-population RI package — say so and point to R/Stata.**
- **A3b · IV/2SLS standard errors (incl. weak-instrument-robust).** *Nash APPROVE; Neitzche defer.* **Decision: include, compact.** Frequently botched. R `fixest::feols(y ~ x | iv)`, `ivreg`, weak-IV `ivmodel` (AR/CLR); Python `linearmodels.IV2SLS` (**weak-IV-robust is weak in Python — flag it**); Stata `ivreg2`, `weakiv`, `rivtest`.
- **A3c · Robust/clustered SEs for MLE/GLM + delta method.** *Nash APPROVE compact; Neitzche defer.* **Decision: include, compact** — logit/Poisson clustered SEs are everywhere. R `sandwich::vcovHC/vcovCL` on `glm` + `marginaleffects` (best-in-class delta-method SEs); Python `statsmodels` `cov_type=` + `.get_margeff()`; Stata `vce(robust|cluster)` + `margins`.
- **A3d · Wooldridge panel serial-correlation test.** *Both: FAQ paragraph only.* (`plm::pwartest`/`pbgtest`.)
- **A3e · FE-vs-RE SE.** *Both: one sentence.* Out of scope as an SE question.
- **A3f · GMM.** *Both: one-paragraph pointer, no section.*
- **Agent (verify package currency for A3a–c):** Nash / `sonnet` — "Confirm current maintained status + exact call for: `ivmodel` (R weak-IV AR/CLR), `linearmodels.IV2SLS`, `marginaleffects` delta-method SE syntax, `ri2::conduct_ri` + `randomizr::declare_ra`. Flag any stale package. Confirm the 'no mature RI in Python' and 'weak-IV-robust weak in Python' caveats are still accurate."

### ✅ A4 · Unified notation glossary *(load-bearing — Neitzche: disqualifying if absent)* — **APPLIED** (collapsible "Notation used throughout" table before the method sections; renamed kernel `$k(\cdot)$ → $\kappa(\cdot)$` in HAC + spatial so `$k$` is unambiguously the parameter count; confirmed `$\rho$` is only the sampling fraction and parameters are uniformly `$k$`)
- **What:** one notation table at the front fixing symbol drift: parameter count ($k$ vs $p$ vs $n-k$), cluster count ($G$, $G-1$), $h_{ii}$, $\hat\Omega$, kernel $k(\cdot)$ vs bandwidth $h$, $\rho$ (ICC vs sampling fraction — currently overloaded). Pick one symbol per concept and use it everywhere.
- **Agent:** Direct apply — no agent needed. (Neitzche specified the conflicts; standardize on $k$ for parameters, $h$ for bandwidth, distinguish ICC $\rho$ from sampling fraction.)

### ✅ A5 · Reproducibility infrastructure *(mandatory for the "authoritative reference" claim)* — **APPLIED** (Appendix "Reproducibility" subsection with real pinned versions — R 4.5.2 / Python 3.12.13 + key packages; seed convention; the `fwildclusterboot ≥ 0.13` global-seed caveat; data provenance + Zimbabwe note; figure-regeneration via `scripts/`)
- **What:** `set.seed()` in every stochastic chunk; a `sessionInfo()`/`renv.lock` note with pinned package versions (your bug-fix list already flagged `fwildclusterboot` version-sensitivity); explicit data provenance (source, vintage, N, G stated once).
- **Both:** table stakes for the A grade, not an A+ flourish.
- **Agent:** Direct apply — no agent needed.

---

## 🔵 A+-TIER ADDITIONS (evidence & originality — earns the +)

### ✅ A6 · Reproducible Monte Carlo coverage study *(THE centerpiece — both reviewers' #1)* — **APPLIED** (`scripts/se_monte_carlo.R` per Neitzche's design; results table `#tbl-montecarlo` in the Appendix with REAL numbers — at ρ=0.3, OLS/HC1 reject ~50%, CRVE 0.14→0.05 as G grows, CR2 & wild bootstrap ~5% throughout; ρ=0 calibration control noted. Preview config M=400/B=499; committed script documents M=2000/B=999 for publication. **Empirical size only (Experiment 1); the CI-coverage experiment (Exp 2) is described in the design but not yet run.**)
- **Why:** the guide repeatedly *asserts* "rejects ~8–12% at nominal 5%," "anti-conservative," "under-covers" without producing one number from its own code. A small seeded simulation that *prints the actual rejection rates* converts assertion into demonstrated fact — genuinely original for a teaching guide.
- **Design (Neitzche, statistically vetted):**
  - **DGP — cluster-randomized, random-intercept (the canonical small-G failure case).** $G$ clusters × $n_g=30$ units; cluster-level treatment $D_g\in\{0,1\}$ (half treated) so $x_{ig}=D_g$ (maximizes the Moulton problem = honest worst case); errors $\epsilon_{ig}=u_g+v_{ig}$, $u_g\sim N(0,\rho\sigma^2)$, $v_{ig}\sim N(0,(1-\rho)\sigma^2)$, ICC $\rho$ swept. Outcome $y_{ig}=\beta_0+\beta_1 D_g+\epsilon_{ig}$.
  - **Sweeps:** $G\in\{6,10,20,50\}$, $\rho\in\{0,0.1,0.3\}$ (the $\rho=0$ row is the calibration control).
  - **Estimators (one row each, $H_0:\beta_1=0$, two-sided, nominal 5%):** (1) OLS classical, (2) HC1, (3) CRVE/CR1 with $t_{G-1}$, (4) CR2 Bell–McCaffrey Satterthwaite (`clubSandwich`), (5) wild cluster bootstrap Rademacher null-imposed (`fwildclusterboot`).
  - **Two experiments:** Exp 1 — empirical *size* with true $\beta_1=0$ (target 0.05, headline table); Exp 2 — empirical *CI coverage* with true $\beta_1=0.3$ (target 0.95).
  - **Reproducibility-grade:** $M=2000$ reps (MCSE near 0.05 ≈ $\sqrt{.05\cdot.95/2000}\approx0.005$ — **report it**, A12), $B=999$ (coheres with the guide's own box), `set.seed` once + per-rep seeding (`furrr_options(seed=TRUE)`).
  - **Headline shape (Exp 1, $\rho=0.3$) — illustrative, do NOT hard-code:** monotone columns showing OLS/HC1 catastrophic, CRVE→CR2→wild progressively calibrated as $G$ shrinks; include the $\rho=0$ row to prove the harness itself hits 5% under independence.
- **R sketch (Neitzche — enough to implement):**
  ```r
  library(clubSandwich); library(fwildclusterboot); library(sandwich)
  library(lmtest); library(dplyr); library(furrr)
  plan(multisession)

  sim_once <- function(G, n_g, rho, beta1, sigma = 1, B = 999) {
    g <- rep(1:G, each = n_g)
    D <- rep(rbinom(G, 1, 0.5), each = n_g)            # cluster-level treatment
    # guard: re-draw D if a treatment arm is empty (omitted for brevity)
    u <- rep(rnorm(G, 0, sqrt(rho) * sigma), each = n_g)
    v <- rnorm(G * n_g, 0, sqrt(1 - rho) * sigma)
    y <- beta1 * D + u + v
    dat <- data.frame(y, D, g = factor(g)); fit <- lm(y ~ D, data = dat)
    p_ols  <- coef(summary(fit))["D", 4]
    p_hc1  <- coeftest(fit, vcov = vcovHC(fit, "HC1"))["D", 4]
    p_crve <- coeftest(fit, vcov = vcovCL(fit, cluster = ~g, type = "HC1"), df = G - 1)["D", 4]
    ct_cr2 <- coef_test(fit, vcov = "CR2", cluster = dat$g)
    p_cr2  <- ct_cr2$p_val[ct_cr2$Coef == "D"]
    p_wcb  <- boottest(fit, param = "D", clustid = "g", B = B, type = "rademacher")$p_val
    c(OLS = p_ols, HC1 = p_hc1, CRVE = p_crve, CR2 = p_cr2, WildBS = p_wcb) < 0.05
  }

  run_cell <- function(G, rho, M = 2000, n_g = 30, beta1 = 0) {
    set.seed(20240601)
    reps <- future_map(1:M, ~ sim_once(G, n_g, rho, beta1), .options = furrr_options(seed = TRUE))
    rate <- rowMeans(do.call(cbind, reps)); mcse <- sqrt(rate * (1 - rate) / M)
    tibble(G = G, rho = rho, estimator = names(rate), reject = rate, mcse = mcse)
  }
  grid <- tidyr::expand_grid(G = c(6,10,20,50), rho = c(0,0.1,0.3))
  size_results <- purrr::pmap_dfr(grid, run_cell)        # Exp 1 (beta1 = 0)
  # Exp 2: rerun with beta1 = 0.3, record "truth in 95% CI" instead of the p-value test.
  ```
  Implementer notes: guard degenerate treatment draws; for Exp 2 swap the `< 0.05` test for a CI-coverage indicator per estimator; keep the $\rho=0$ calibration row.
- **Agent (recommended — this is a build, run it isolated):**
  - **Persona:** Neitzche (rigor) — implement, run, and tabulate.
  - **Model:** `opus`. **Isolation:** `worktree`.
  - **Prompt:** "Implement Neitzche's Monte Carlo design as a self-contained, seeded Quarto chunk (or sourced `.R` + cached results) for `standard-errors.qmd`. Run both experiments, produce the two `gt`/`kable` tables with captions stating nominal α, M, and MCSE, and confirm the $\rho=0$ rows are calibrated to ~0.05. Report the actual numbers back; flag any estimator that doesn't behave as the guide claims (that itself is publishable honesty). Do not hard-code the illustrative magnitudes."

### ✅ A7 · One-page cheat-sheet + capped mistakes gallery — **APPLIED** (cheat-sheet = the A1 selection table `#tbl-se-map`; mistakes gallery folded into a "most common standard-error mistakes" FAQ, 7 decision-errors, capped)
- **Cheat-sheet:** a printable one-page flowchart/decision summary cross-linked to the interactive decision tree — "how busy people actually use a guide" (Nash). The printable companion to A1.
- **Mistakes gallery:** 4–6 *decision* errors, before/after (e.g., clustering at the wrong level; reading robust-vs-OLS gap as license to cluster; clustering at the firm×year intersection; naive SEs after matching; TWFE clustered SEs in staggered DiD). Cap hard — both reviewers warned it becomes a listicle otherwise.
- **Agent:** Direct apply (cheat-sheet derives from A1; gallery from the guide's own warnings).

### ✅ A8 (narrowed) · Sensitivity / "SEs ≠ causal uncertainty" — **APPLIED as FAQ** ("tight CI around a confounded estimate is precisely measured nonsense"; Oster δ (`robomit`/`psacalc`) + Cinelli–Hazlett `sensemakr` (R+Python); report alongside SEs for any causal claim. Cites: oster2019, cinelliHazlett2020.)
- **What:** a single worked Oster-δ example framed explicitly as "this is the uncertainty your SE does *not* capture," + one-line Rosenbaum-bounds pointer. R `sensemakr`/`robomit`; Python `sensemakr` (port exists); Stata `sensemakr`/`psacalc`.
- **Both:** keep compact; do not let it metastasize into a causal-inference section.
- **Agent:** Direct apply.

---

## 🧭 PRACTITIONER GAPS (Nash — "currently leave real people stranded"; must-add for applied-micro trust)

### ✅ G1 · Staggered-adoption DiD + its SEs *(Nash: CRITICAL)* — **APPLIED as FAQ** ("fix the estimator before the SE"; Callaway–Sant'Anna / Sun–Abraham / BJS imputation; cluster at unit; event-study = same machinery; R `did`/`fixest::sunab`/`didimputation`, Stata `csdid`/`eventstudyinteract`/`did_imputation`, Python `differences`/`pyfixest` with "verify inference" caveat. Cites added: callawaySantanna2021, sunAbraham2021, rothEtal2023.)
- **Issue:** Post-2020 the most common applied-micro setting. The decision tree mentions Callaway–Sant'Anna / Sun–Abraham but the paper never covers it. A researcher clustering TWFE SEs in a staggered design has a **biased estimator**, not just a bad SE.
- **Content:** lead with "fix the estimator before the SE"; name the modern estimators and their clustered/bootstrap inference; fold event-study SEs in here (same machinery).
- **Tooling:** R `did` (Callaway–Sant'Anna), `fixest::sunab` (Sun–Abraham), `didimputation` (BJS); Python `differences`, `pyfixest` (sunab support emerging — verify); Stata `csdid`, `eventstudyinteract`, `did_imputation`.
- **Agent (verify Python currency + exact calls):** Nash / `sonnet` — "Confirm the current state of staggered-DiD tooling: R `did`/`fixest::sunab`/`didimputation` calls and their default inference; whether Python `differences` and `pyfixest` now cleanly support Callaway–Sant'Anna and Sun–Abraham with valid SEs (don't overpromise); Stata `csdid`/`eventstudyinteract`. Return paste-ready snippets + honest caveats."

### ✅ G2 · The genuine few-cluster last resort *(Nash: CRITICAL)* — **APPLIED as FAQ** (honest ladder: Webb wild bootstrap → randomization inference → report the CI and stop over-claiming; explicit "don't manufacture clusters / don't fall back to HC"; pooling as the only real fix. Cites: mackinnonNielsenWebb2023, cameronGelbachMiller2008.)
- **Issue:** The guide escalates CR2 → wild bootstrap → Webb weights but never answers: *"I have 5 clusters and cannot get more — what do I actually report?"*
- **Content:** an honest decision rule — randomization inference, design-based bounds, or "report the CI and stop pretending the p-value is meaningful." No new tools needed (it's a decision rule over `fwildclusterboot`/`ri2`/`clubSandwich` already in the guide).
- **Agent:** Direct apply — Nash can draft; consistent with decision-tree `crve_tinyG`.

### ✅ G3 · SEs after matching / PSM (Abadie–Imbens) *(Nash: MAJOR)* — **APPLIED as FAQ** (matching adds its own variability; report AI variance; R `Matching::Match`/`MatchIt`+`marginaleffects`, Stata `teffects nnmatch`/`psmatch2`; honest "Python thin — use R/Stata"; warns NN-matching SEs aren't bootstrap-consistent. Cite: abadieImbens2006.)
- **Issue:** People use naive regression SEs that ignore the matching step; the matching estimator's variance is not the regression variance.
- **Tooling:** R `Matching::Match` (AI SEs native), `MatchIt` + `marginaleffects`; **Python tooling weak/stale (`causalinference`)** — say so; Stata `teffects nnmatch`/`psmatch2`.
- **Agent (verify):** Nash / `sonnet` — confirm `Matching` AI-SE behavior and the honest Python gap.

### ✅ G4 · Multiple-hypothesis-testing adjustments *(Nash: MAJOR)* — **APPLIED as FAQ** (threshold not SE changes; Romano–Wolf stepdown exploits cross-test dependence; R `wildrwolf`, Stata `rwolf`/`wyoung`, Python only independence-based — use R/Stata; pre-specify family, report adjusted + unadjusted. Cite: romanoWolf2005.)
- **Issue:** Researchers running many outcomes/subgroups need this; Romano–Wolf respects cross-test dependence (unlike Bonferroni).
- **Tooling:** R `wildrwolf` (Romano–Wolf), `multcomp`; **Python: `statsmodels.stats.multitest` (Bonferroni/BH only — no R-W)** — flag; Stata `rwolf`, `wyoung`.
- **Agent (verify):** Nash / `sonnet` — confirm `wildrwolf`/`rwolf` currency and the Python R-W gap.

### Leave out (both): Bayesian credible intervals, GMM beyond a pointer, multilevel/mixed-model SEs, spatial-panel-specific estimators beyond what exists.

---

## 🧱 UNIFICATION & RIGOR ITEMS (Neitzche — "what separates an authoritative reference from a recipe book")

### ✅ A9 · Per-estimator assumptions table *(Neitzche: ranks above A8 and most of A3)* — **APPLIED** (`#tbl-assumptions` in the Appendix, horizontal scroller: 11 rows × [assumes / relaxes / consistent as / finite-sample behavior]; closing line ties each "relaxes" to off-diagonal meat terms, linking back to the A11 unification box. Placed in Appendix for page-fit, consistent with A1.)
- **What:** one table, one row per estimator: **assumes / relaxes / consistency condition / finite-sample behavior.** E.g. CRVE: "assumes independence across clusters; relaxes within-cluster correlation arbitrarily; consistent as $G\to\infty$; over-rejects at small $G$." Directly fixes the recurring hand-waving-on-assumptions risk.
- **Agent:** Direct apply — Neitzche specified the structure; populate per section.

### ✅ A10 · Finite-sample-vs-asymptotic framing box — **APPLIED** (callout-note "Consistency, not unbiasedness" right after the A11 box: robust SEs buy consistency not unbiasedness; every small-sample fix is a patch on the same asymptotic object; large-count → choice rarely matters, small-count → wider interval, not more confidence)
- **What:** one box stating the organizing principle the guide currently leaves implicit: *robust SEs buy consistency, not unbiasedness; every small-sample correction (HC2/HC3, CR2, $t_{G-1}$, Webb) is a finite-sample patch on an asymptotic object.* Reference it from each section. Pairs with A9.
- **Agent:** Direct apply.

### ✅ A11 · One-paragraph sandwich derivation *(Neitzche: load-bearing for a true A+)* — **APPLIED** (callout-tip "The sandwich is one structure; every correction just changes the filling" in the HC section: $\sqrt{n}(\hat\beta-\beta)\to\mathcal N(0,Q^{-1}\Omega Q^{-1})$, bread vs meat, with HC/cluster/HAC/spatial as different meats; meat written precisely as the asymptotic score variance, reducing to $\mathbb E[\epsilon_i^2 x_i x_i^\top]$ under independence)
- **What:** show $\sqrt{n}(\hat\beta-\beta)\to N(0,\,Q^{-1}\Omega Q^{-1})$ with $Q=E[x_ix_i^\top]$, $\Omega=E[x_ix_i^\top\epsilon_i^2]$, and note the **meat $\Omega$ is what every variant estimates differently** — HC, cluster, HAC, spatial/Conley are all "same bread, different meat." This single unifying observation gives the guide its spine ("oh, *that's* the structure").
- **Agent:** Direct apply — no agent needed.

### ✅ A12 · Report the Monte Carlo's own MCSE + calibration row — **APPLIED** (table caption states M and MCSE ≈ 0.011; the ρ=0 calibration check is reported in the surrounding prose)
- **What:** state the MCSE and include the $\rho=0$ "harness is calibrated under independence" sanity row. Methodological honesty — a simulation that doesn't report its own uncertainty commits the sin the guide warns against. Mandatory if A6 is in.
- **Agent:** folded into A6.

---

## 📚 RESOURCE CURATION (Nash — "ones I'd defend in front of a skeptical committee")
Add these and *replace* (not supplement) the weak Tutorials entries from SE-T1-11:
1. **MacKinnon, Nielsen & Webb (2023), "Cluster-robust inference: A guide to empirical practice," *J. Econometrics*** — the definitive modern clustering survey; backs the wild-bootstrap/Webb escalation the guide already recommends.
2. **Roth, Sant'Anna, Bilinski & Poe (2023), "What's trending in difference-in-differences?," *J. Econometrics*** — best entry point to the staggered-DiD literature (anchors gap G1); maintained companion code.
3. **Abadie, Athey, Imbens & Wooldridge (2023, QJE)** — already cited; *elevate* from a buried FAQ to a named "further reading" anchor (it's the guide's intellectual foundation).
4. **`fixest` vignette (Bergé) + `clubSandwich` vignette (Pustejovsky)** — promote to first-class "if you implement one thing, read this"; the `clubSandwich` vignette is the correct home for the CR2/Bell–McCaffrey material.
5. **Cunningham, *Causal Inference: The Mixtape*** (or Huntington-Klein, *The Effect*) — one free, maintained, trusted book-length anchor for surrounding causal context the guide deliberately doesn't reteach.

---

## The honesty principle (both reviewers, emphatic)
Wherever Python has **no honest tool** — weak-IV-robust inference, finite-population randomization inference, Abadie–Imbens matching SEs, Romano–Wolf — **say so plainly and point to R/Stata** rather than faking a Python tab. Nash: *"that candor is itself the mark of the guide a researcher trusts completely."* This is the same anti-terminal-code principle that drove the CCV/TSCB fix.

## Grade ladder (reconciled)
| Do | Reaches |
|----|---------|
| Tier 0–2 fixes | **A−** |
| + A1, A2, A4, A5, A9, A10, A11 (completeness, notation, unification, reproducibility) | **A** |
| + A6 (Monte Carlo evidence), A7 cheat-sheet, G1 staggered DiD, G2 few-cluster last resort | **A+** |

**Both reviewers' bottom line:** the A→A+ jump is carried by **A6 + A1 + A2**, made airtight by **A4 + A9 + A11**, and made trustworthy to applied researchers by closing **G1 (staggered DiD)** and **G2 (few-cluster last resort)** — with honest "no good Python tool" caveats wherever they apply.
