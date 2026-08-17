# Review edits — synthetic-control.qmd

Edits applied to `synthetic-control.qmd` in response to the panel review. Each is a
small, self-contained change. Tick to **keep**, or revert the specific edit if you
disagree. Nothing structural was changed; the guide's flow is untouched.

Applied on branch `su26/synthetic-controls`. To see them all: `git diff synthetic-control.qmd`.

---

## Must-fix — applied

- [ ] **1. Factual error: "eighteen" → "nineteen" pre-treatment years.**
  Location: `prop99-paths` fig-cap (~line 526). 1970–1988 inclusive is 19 annual
  observations, not 18.

- [ ] **2. Contradiction: softened "the pre-treatment fit *is* the identifying argument."**
  Location: Introduction, "Two features..." (~line 71). The original flatly equated
  pre-fit with identification, which the guide itself later walks back to "necessary
  but not sufficient" (gsynth section, ~line 819). Now reads "...is where the
  identifying argument becomes visible..." with a forward pointer. Wording only — no
  change to the claim made later.

- [ ] **3. Contradiction: "subsumes" → "generalizes" classical SCM.**
  Location: Factor-model view (~line 615). The later section "Does the General Tool
  Replace the Specific One?" argues gsynth and classical SCM are *different*
  estimators that disagree; "subsumes" contradicted that. Now flags they can disagree.

- [ ] **4. Code terminology: Synth V-optimization is not "cross-validation."**
  Location: "The Optimizer's Answer Is Not Always Unique" callout (~line 580). In the
  shown spec `time.optimize.ssr` is the full pre-period, so there is no holdout.
  Changed "the cross-validation procedure used to choose V" → "the nested
  optimization used to choose V." (The later `CV = TRUE` in `fect` is genuine
  cross-validation and was left alone.)

- [ ] **5. Code comment: "projected gradient descent" was inaccurate.**
  Location: `prop-sim` chunk, `scm_weights` (~line 956). Clip-negatives-and-renormalize
  is not Euclidean projection onto the simplex. Comment now describes what the code
  actually does. **Code behavior unchanged** — only the comment. The crude convex
  solver still produces a valid convex combination, which is all the illustration
  needs; not replaced with a QP solver.

- [ ] **6. Accessibility: added `fig-alt` to all 13 plots.**
  Locations: every chunk with a `#| fig-cap:` now also has a `#| fig-alt:` line
  directly beneath it (`fig-paths`, `fig-gaps`, `prop99-paths`, `prop99-gap`,
  `fig-placebo`, `fig-loo`, `fig-gsynth-gap`, `fig-gsynth-factors`,
  `fig-turnout-status`, `fig-turnout-gap`, `fig-gsynth-vs-scm`, `fig-augsynth`,
  `fig-prop`). Screen-reader text for web publication; captions were left as-is.

---

## Not applied — deliberately left for you to decide

Optional improvements from the review that were *not* made, because they add scope
rather than fix a defect. Listed so you can pick them up if you want.

- [ ] **Soften "That is overfitting" on the real Prop 99 data** (~line 786). On real
  data the untreated path is unknown, so this is strictly the *signature* of
  overfitting, not proof; the known-truth simulation is where it's proven. One-word
  change if you want it (`That is overfitting` → `That pattern is the signature of
  overfitting`).

- [ ] **Prop 99 estimand / design card** (~line 442). A short callout naming the
  estimand (mean post-1988 gap), the outcome (recorded packs sold per capita, not
  smoking or health), treated unit, and first exposed year (1989). ~6 lines.

- [ ] **Placebo + leave-one-out on the *real* Prop 99 fit**, not only the simulation.
  Highest-payoff addition (it's the iconic Abadie result and closes the
  practice-what-you-preach gap), but it's a new code chunk — real work, not a tweak.

## Rejected as out of scope (my recommendation: do not do these for a web guide)

Recorded so the decision is explicit, not forgotten:

- Full structural reorder into a "design firewall / freeze-then-reveal" workflow.
- The "distinctive features" battery (assumption ledger, donor dossier, credibility
  dashboard, researcher-degrees-of-freedom lab, health-data failure labs, estimand
  translator).
- Formal placebo "contract" / minimum attainable p-value / multiplicity machinery —
  the guide already reframes placebo p-values as design-based ranks in three places.
- Multi-replication augmentation failure lab — the "best case" caveat is already
  present (~line 906).
- Backdated-treatment tests, alternative effective dates, concurrent-policy timeline,
  SATT/PATT taxonomy expansion — paper-level, not practitioner-guide level.

---

## After deciding

Re-render to confirm the guide still builds and the `fig-alt` lines are valid YAML:

```
quarto render synthetic-control.qmd
```
