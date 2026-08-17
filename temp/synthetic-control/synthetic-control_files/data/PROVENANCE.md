# Data provenance — synthetic-control guide

These CSVs are local caches of datasets that ship inside R packages, exported so the
guide can render from flat files instead of depending on `data(...)` calls. They are
**copies**, not new data collection. Regenerate with the script at the bottom.

Exported 2026-07-22 from: `tidysynth` 0.2.1, `fect` 2.4.5 (R export via `write.csv`,
`row.names = FALSE`).

---

## smoking.csv
- **Source package:** `tidysynth::smoking` (v0.2.1).
- **Original source:** Abadie, Diamond & Hainmueller (2010), "Synthetic Control
  Methods for Comparative Case Studies: Estimating the Effect of California's
  Tobacco Control Program," *JASA* 105(490):493–505. The canonical Proposition 99 panel.
- **Shape:** 1209 rows = 39 states × 31 years (1970–2000).
- **Columns:** `state` (name), `year`, `cigsale` (per-capita cigarette packs sold),
  `lnincome`, `beer` (per-capita beer consumption, observed 1984–), `age15to24`
  (population share), `retprice` (retail cigarette price).
- **Notes:** Donor pool already excludes states that ran their own large tobacco-control
  programs. `state` is a name; the guide derives a numeric `state_id` at read time.

## simgsynth.csv
- **Source package:** `fect::simgsynth` (v2.4.5).
- **Original source:** simulated panel distributed with `fect` / `gsynth`
  (Xu 2017; Liu, Wang & Xu 2022), generated from an interactive fixed-effects
  (factor) model with a **known** treatment effect, used for ground-truth checks.
- **Shape:** 1500 rows.
- **Columns used by the guide:** `id`, `time`, `Y` (outcome), `D` (treatment
  indicator), `X1`, `X2` (covariates), `eff` (true effect). Additional columns
  (`error`, `mu`, `alpha`, `xi`, `F1`, `L1`, `F2`, `L2`) expose the true factors and
  loadings and are retained as-is.

## turnout.csv
- **Source package:** `fect::turnout` (v2.4.5).
- **Original source:** US state-level voter turnout and election-day registration
  (EDR) adoption, the staggered-adoption panel used in the `gsynth`/`fect` literature
  (Xu 2017 and the EDR studies it draws on).
- **Shape:** 1128 rows.
- **Columns:** `abb` (state abbreviation), `year`, `turnout`, `policy_edr` (EDR in
  effect), `policy_mail_in`, `policy_motor`.

---

## Regenerate

Run from the repo root with `tidysynth` and `fect` installed:

```r
dir <- "research-guides/synthetic-control/synthetic-control_files/data"
data(smoking,   package = "tidysynth")
data(simgsynth, package = "fect")
data(turnout,   package = "fect")
write.csv(smoking,   file.path(dir, "smoking.csv"),   row.names = FALSE)
write.csv(simgsynth, file.path(dir, "simgsynth.csv"), row.names = FALSE)
write.csv(turnout,   file.path(dir, "turnout.csv"),   row.names = FALSE)
```

Round-trip verified: reading each CSV back reproduces the package data on every column
the guide uses (only a cosmetic `row.names` attribute on `turnout` differs).
