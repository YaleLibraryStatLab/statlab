# StatLab Alpha Test Checklist

**Generated:** 2026-06-12 · **Reviewer:** Claude (claude-fable-5)
**Content repo:** `/Users/te272/StatLab/ResearchGuides` (branch `main`)
**Website repo:** `/Users/te272/StatLab/statlab` (branch `flask-experiment`)

Everything below was verified by reading both repos. Where this plan contradicts
your assumptions, the repo is the source of truth — see §F (Risks) for the full list
of surprises found.

---

## Key facts the plan is built on

- **The Flask app serves guides from `temp/`, not `research-guides/`.** `app.py`
  (`list_available_guides`, `guide_index`) reads `temp/<slug>/<slug>.html`. Only
  2 guides are live (`mixed-effects-models`, `multivariate-regression`); guides reach
  `temp/` by manual copy. `tools/build.py` is a **scaffold only** and targets paths
  that don't exist (`app/static/guides/`, `app/guides_manifest.json` — there is no
  `app/` package; `app.py` lives at repo root).
- **`statlab/research-guides/` is a stale snapshot** containing rendered copies of
  11 guides — including two you want excluded (`diffindiff`,
  `research-guide-quarto-template`), one that no longer exists in the source repo
  (`multivariate-regression`), and a leftover `guides/` dir from the old workflow.
- **The statlab repo has no CI at all.** The only workflow is
  `ResearchGuides/.github/workflows/deploy-to-website.yml` (legacy, Quarto-era), which
  pushes rendered HTML *into* the statlab repo's `main` with `rsync --delete`.
- **Language coverage audit** (executed code chunks per `.qmd`, counted 2026-06-12):

  | Guide | Tabsets | Languages present | Missing (target: R, Py, Stata, Julia, AI) |
  |---|---|---|---|
  | diffindiff *(excluded)* | 1 | R, Py, Stata | — |
  | glmms | 8 | R | Py, Stata, Julia, AI |
  | groupwise-comparisons | 3 | R, Py, Stata | Julia, AI |
  | instrumental-variables | 1 | R, Py, Stata | Julia, AI |
  | logit-probit | 1 | R, Py, Stata | Julia, AI |
  | missingdata *(excluded)* | 0 | R | — |
  | mixed-effects-models | 6 | R, Julia | Py, Stata, AI |
  | model-selection | 0 | R | tabsets + Py, Stata, Julia, AI |
  | olsregression | 3 | R, Py, Stata | Julia, AI |
  | panel-regression | 0 | R | tabsets + Py, Stata, Julia, AI |
  | pvalues | 1 | R, Py, Stata | Julia, AI |
  | research-guide-quarto-template *(excluded)* | 1 | Py, Stata | — |
  | standard-errors | 4 | R, Py, Stata | Julia, AI |
  | statisticalpower | 2 | R, Py, Stata | Julia, AI |
  | teststatistics | 1 | R, Py, Stata | Julia, AI |
  | variable-selection | 0 | **none** | everything — prose-only guide |

  **No guide currently has all four languages.** 13 guides need expansion work.
- **Local toolchain (this Mac):** Quarto 1.7.30 ✓ · R 4.5.2 ✓ · `python3` = system
  3.9.6 (legacy CI used 3.12) · **Julia not installed** · Stata installed at
  `/Applications/Stata` but **not on PATH**. Guides use knitr-engine chunks
  (`{stata, echo = T}`, `python.reticulate = T`), so local rendering runs through
  R/knitr with Statamarkdown + reticulate + JuliaCall.
- **`statlab/assets/` is gitignored** (fonts, consultant photos). A fresh clone — or
  any CI build — produces a site with missing fonts and photos.
- The `cross-lang-verify` skill exists as content (provided by you) but **no skill
  file was found in either repo's `.claude/skills/`** — it must be installed before
  it can be invoked.

---

## 1 · Order of operations

Tasks are labeled by workstream (A pipeline, B branches, C languages, D Pages,
E design, F fixes). Dependencies in parentheses.

| # | Task | Why this position |
|---|---|---|
| 1 | **C-2** Local toolchain setup | Everything downstream needs to render guides locally; Julia/Stata/Python gaps block C and A. |
| 2 | **F-1** Quick-hygiene fixes | Cheap, removes landmines (stale snapshot, disabled legacy workflow) before pipeline work begins. |
| 3 | **B-1** Local dev workflow for `flask-experiment` | Establishes how you run/test before code changes pile up. |
| 4 | **A-1** Implement `tools/build.py` with exclusion config (needs 1) | The ingestion pipeline; everything ports through it. |
| 5 | **A-2** Wire `app.py` to the build output (needs 4) | Kills the manual-copy-to-`temp/` step. |
| 6 | **A-3** Render-and-port script: ResearchGuides → statlab (needs 1, 4) | The actual "port"; first end-to-end transfer of all non-excluded guides. |
| 7 | **C-3** Extend `cross-lang-verify` skill to 4 languages + AI-prompt check | Build the gate *before* mass-expanding guides, so expansion work is validated as it lands. |
| 8 | **C-1a** Expand ONE exemplar guide to all 5 tabs (needs 1, 7) | Establishes the pattern + AI-prompt-tab standard on `standard-errors`. |
| 9 | **C-1b** Expand remaining 12 guides (needs 8) | Parallelizable per guide; each gated by C-4. |
| 10 | **C-4** Run validation gate per guide (needs 7; per guide after 9) | VERIFIED/MISMATCH report for every shipped guide. |
| 11 | **D-1** Static export (freeze Flask → `docs/`) (needs 5, 6) | Site must build statically end-to-end before design and launch. |
| 12 | **E** Design — placeholder (needs 11) | Opaque; scoped separately. Slotted after the site works, before launch. |
| 13 | **D-2** GitHub Pages publishing workflow (needs 11) | CI that runs the freeze and publishes. |
| 14 | **B-2** Promote `flask-experiment` → `main` (needs all above) | Final switch, using the promotion checklist in §B-2. |

Steps 8–10 form a loop: expand a guide → validate → ship. Steps 11–13 can proceed in
parallel with the guide loop once one guide passes the gate.

---

## 2 · Task sections

## A-1: Implement `tools/build.py` — exclusion-based ingestion pipeline

**Model:** `claude-fable-5` — multi-file implementation with real design decisions
(manifest schema, asset handling) that the rest of the pipeline depends on.
**Persona:** Backend engineer who treats build scripts as production code.
**Goal:** One command turns rendered guide HTML into everything the Flask app needs,
with guide selection driven by an exclusion file.

**On exclusion vs. inclusion (your question):** exclusion is the right call for this
project — the default state of a finished guide should be "published," and the legacy
inclusion array already caused drift (only 2 of 16 guides shipped). Two refinements:
(1) put the list in a config file (`guides.exclude`), never in workflow YAML, so
adding an exclusion is a one-line content commit; (2) have the build **fail loudly**
if an excluded name doesn't match any directory — that's how you catch typos and
renamed guides, the classic failure mode of exclusion lists.

**Prompt:**

> Working dir: `/Users/te272/StatLab/statlab`, branch `flask-experiment`.
> Read `app.py`, `tools/extractor.py`, `tools/build.py` (scaffold), `tools/README.md`,
> and the "Infrastructure & Content Pipeline" section of `ALPHA.md` first.
>
> Implement `tools/build.py` as the single ingestion command:
> 1. Read an exclusion list from a new top-level file `guides.exclude` (one slug per
>    line, `#` comments allowed). Seed it with: `diffindiff`, `missingdata`, `model-selection`,
>    `research-guide-quarto-template`. Error (non-zero exit) on any entry that
>    matches no directory.
> 2. Walk a source directory of rendered guides (default `research-guides/`, flag
>    `--source` to override) for `<slug>/<slug>.html`; skip exclusions and the
>    legacy `guides/` dir.
> 3. For each guide: run `extractor.extract()` as a smoke check (parse failure =
>    guide is skipped with a loud warning, not a crash), copy `<slug>/` (HTML +
>    `<slug>_files/` + data files) into a publish dir (default `temp/`, flag
>    `--dest`), and record `slug`, `title`, `date`, `authors`, `keywords` in
>    `guides_manifest.json` at repo root.
> 4. Add the asset 404 smoke-test from ALPHA.md (P1): verify every local asset path
>    referenced by the extracted HTML exists on disk; report missing files.
> 5. Support `--dry-run` (print manifest, write nothing) and `--clean` (remove
>    publish-dir guides no longer in the source set).
> Fix the scaffold's dead paths (`app/static/guides`, `app/guides_manifest.json`)
> and the broken relative import (`from extractor import …` only works when cwd is
> `tools/`; use a package-relative import that works from repo root).
> Acceptance: `python tools/build.py --dry-run` lists every non-excluded guide in
> `research-guides/`; a real run populates `temp/` and the manifest; excluding a
> nonexistent slug exits non-zero. Do NOT modify `app.py` (that is task A-2) or
> anything in `/Users/te272/StatLab/ResearchGuides`.

---

## A-2: Wire `app.py` to the build output

**Model:** `claude-sonnet-4-6` — contained refactor of one file against a defined
manifest contract.
**Goal:** The Flask app reads `guides_manifest.json` instead of re-scanning and
re-parsing `temp/` on every request.

**Prompt:**

> Working dir: `/Users/te272/StatLab/statlab`, branch `flask-experiment`. Read
> `app.py` and the manifest schema produced by `tools/build.py` (task A-1).
>
> Refactor `app.py` so that:
> 1. `list_available_guides()` reads `guides_manifest.json` (title, slug, date)
>    instead of calling `extract()` on every guide per request.
> 2. `guide_index()` caches `extract()` results keyed on `(path, mtime)` (ALPHA.md
>    P2 item) so repeated views don't re-parse.
> 3. A missing manifest degrades gracefully to the current directory-scan behavior
>    with a logged warning.
> Keep the `temp/` directory name and all route URLs unchanged — templates and the
> static-export task (D-1) depend on them. Acceptance: `flask --app app run` serves
> the guide listing and individual guides identically to before (visually diff one
> guide page), and the listing renders without `extract()` being called. Do not
> touch templates except where a manifest field name forces it.

---

## A-3: Render-and-port script — ResearchGuides → statlab

**Model:** `claude-sonnet-4-6` — scripting task with a clear contract; the judgment
calls were made in A-1.
**Persona:** Release engineer; favors idempotent, re-runnable scripts.
**Goal:** One command renders every non-excluded guide from source and lands it in
the Flask app, replacing both the manual copy and the legacy CI's render loop.

**Prompt:**

> Repos: source `/Users/te272/StatLab/ResearchGuides` (branch `main`), destination
> `/Users/te272/StatLab/statlab` (branch `flask-experiment`). Read
> `ResearchGuides/.github/workflows/deploy-to-website.yml` (legacy render loop,
> lines 68–125), `statlab/tools/build.py`, and `statlab/guides.exclude` first.
>
> Write `statlab/tools/port_guides.py` (or a shell script if cleaner) that:
> 1. Reads `guides.exclude` — the same file build.py uses; one source of truth.
> 2. For each non-excluded guide dir in `ResearchGuides/research-guides/`: run
>    `quarto render <slug>.qmd` in that dir. On render failure, do NOT silently
>    fall back to eval:false like the legacy workflow — record the failure, render
>    nothing, and list all failures in a summary table at the end. (Note: the
>    legacy fallback `--execute-params eval:false` is not even a valid quarto
>    flag — see Risks F-§6.)
> 3. Copy each successfully rendered `<slug>/` (HTML + `_files/` + data, no `.qmd`
>    sources, mirroring the legacy rsync excludes) into
>    `statlab/research-guides/<slug>/`, replacing what's there.
> 4. Invoke `tools/build.py --source research-guides --dest temp` to publish.
> 5. `--only <slug>` flag to re-render a single guide during development.
> Stata chunks require local Stata (task C-2) — if Stata is unavailable, say so per
> guide rather than failing the whole run. Acceptance: a full run ports all 13
> non-excluded guides end-to-end and `flask run` shows them all in the listing;
> render failures are summarized, not swallowed. Expect some guides to fail
> rendering until C-2 completes — that's the summary table's job. Do not commit
> rendered HTML to the ResearchGuides repo.

---

## B-1: Local dev & test workflow for `flask-experiment`

**Model:** `claude-sonnet-4-6` — environment/docs task, modest judgment.
**Goal:** A documented, reproducible way to develop and test the Flask branch
without touching `main` or deploying anything.

**Prompt:**

> Working dir: `/Users/te272/StatLab/statlab`, branch `flask-experiment`. Read
> `app.py`, `requirements.txt`, `.gitignore`, `ALPHA.md`.
>
> 1. Create a project venv (`python3.12` if available via Homebrew, else newest
>    local Python ≥3.10 — the system 3.9 predates `dataclass` patterns used in
>    `tools/`; verify `from __future__ import annotations` coverage or just require
>    ≥3.10). Pin `requirements.txt` with versions (currently just `Flask`,
>    `beautifulsoup4`, unpinned).
> 2. Add a `Makefile` (or `justfile`) with targets: `make dev` (flask debug server,
>    port 5001), `make port` (run `tools/port_guides.py`), `make build`
>    (`tools/build.py`), `make freeze` (placeholder until D-1).
> 3. Document in `README.md` (create — the repo has none at root): branch layout
>    (`main` = legacy Quarto site, `flask-experiment` = this app), the
>    assets-not-in-git caveat (fonts/photos in `assets/` are gitignored — new
>    machines need them copied manually; see Risks F-§2), and the dev loop:
>    edit guide in ResearchGuides → `make port` → check at
>    `localhost:5001/guides/<slug>/`.
> 4. Add a minimal pytest smoke test: app boots, `/`, `/research-guides`, and one
>    guide route return 200. `make test` runs it.
> Acceptance: fresh terminal → `make dev` works; `make test` passes. Stay on
> `flask-experiment`; no pushes.

### Branching against a moving `main` (ResearchGuides)

Another team member merges guide-update PRs to ResearchGuides `main` continuously.
Policy for this plan's work in that repo:

- **F-1 (disarm legacy workflow): commit directly to `main`, first.** The dangerous
  trigger lives on `main`; a side branch gives no protection against teammate
  merges firing it.
- **Guide expansions (C-1a/C-1b): one short-lived branch per guide**
  (`expand/<slug>`), merged back to `main` as soon as the guide passes the C-4
  gate. Do NOT accumulate expansions on a long-lived branch — teammate edits to
  the same `.qmd` files make prose conflicts grow with branch age, and after F-1,
  `main` deploys nothing, so early merges are free. Before starting a guide,
  check open PRs and prefer guides nobody is editing.
- **Skill + logs** (`.claude/skills/`, `VALIDATION-LOG.md`, `EXPANSION-NOTES.md`):
  low-conflict paths; ride along with F-1 or any small PR.
- **Re-render rule:** when a teammate's content PR lands on an already-expanded
  guide, that guide is stale (their merge includes no local re-render — see Risks
  §8). Re-run `tools/port_guides.py --only <slug>` and the C-4 gate before the
  next freeze.

---

## B-2: Promotion — `flask-experiment` becomes `main`

**Model:** `claude-sonnet-4-6` — careful execution of an explicit checklist; the
checklist itself is below and should be followed literally.
**Persona:** Release manager. Verifies each step before the next; never force-pushes.
**Goal:** `main` in the statlab repo serves the Flask-built site; nothing legacy
fires afterward.

**The promotion checklist** (execute in order — this is the deliverable you asked
to have ready "when the branch becomes the main"):

1. **Preconditions:** all 13 guides ported and validated (C-4 green); static export
   works (D-1); Pages workflow tested on `flask-experiment` (D-2).
2. **In ResearchGuides repo — disarm the legacy cannon first.** Delete (or fully
   neuter) `.github/workflows/deploy-to-website.yml`. It triggers on every push to
   `main` touching `research-guides/**` and `rsync --delete`s into the statlab
   repo — left alive, it will clobber the new site's `research-guides/` tree the
   first time you edit a guide. If F-1 already disabled it, delete it now.
3. **In statlab repo:** archive the Quarto-era tree somewhere recoverable —
   `main` still holds `_quarto.yml`, `_site/`, `site_libs/`, `*.qmd` at root.
   Tag it: `git tag quarto-site-final main`.
4. Merge: `git checkout main && git merge flask-experiment` (expect the merge to be
   effectively a replacement; resolve in favor of `flask-experiment` everywhere,
   then delete leftover Quarto root files: `_quarto.yml`, `index.qmd`, `about.qmd`,
   `research-guides.qmd`, `statlab.scss`, `styles.css`, `_site/`, `site_libs/`,
   `search.json`, stale root `*.html`).
5. **GitHub Pages settings** (repo Settings → Pages): confirm source = `main` +
   `/docs` (matching D-1's output dir), or switch to the Actions-based deploy from
   D-2. The old site also published from `main` — until the merge lands, do not
   change settings, so the public site stays up.
6. **Secrets:** if the new Pages workflow lives in the statlab repo (D-2 default),
   `DEPLOY_TOKEN` in ResearchGuides is obsolete — revoke the PAT. If a
   render-trigger workflow remains in ResearchGuides, scope a fresh fine-grained
   token to the statlab repo only.
7. Update any branch references: D-2 workflow `on.push.branches` from
   `flask-experiment` → `main`; README branch table from B-1.
8. Verify the live Pages URL (https://yalelibrarystatlab.github.io/statlab/)
   renders the new site, then delete the `flask-experiment` branch on origin.
9. **Rollback plan:** the tag from step 3 plus Pages settings pointing back at the
   old `docs/` restores the Quarto site in minutes.

**Prompt:**

> Execute the promotion checklist in §B-2 of
> `~/Downloads/alpha-test-checklist.md` step by step, in both
> `/Users/te272/StatLab/ResearchGuides` and `/Users/te272/StatLab/statlab`.
> Confirm each precondition with evidence (run the validation gate summary, load
> the frozen site locally) before merging. Pause and ask before: deleting the
> legacy workflow, pushing `main`, changing Pages settings, revoking tokens.
> Acceptance: public Pages URL serves the Flask-built site; legacy workflow gone;
> rollback tag exists.

---

## C-2: Local toolchain setup (do this first)

**Model:** `claude-sonnet-4-6` — environment work with verification at each step.
**Goal:** R, Python, Stata, and Julia chunks all execute in a local
`quarto render` on this Mac.

Verified state: Quarto 1.7.30 ✓ · R 4.5.2 ✓ · `python3` is system 3.9.6 ·
Julia **absent** · Stata at `/Applications/Stata` but not on PATH.

**Prompt:**

> Machine: macOS (Darwin 24.6). Working dir: `/Users/te272/StatLab/ResearchGuides`.
> Guides are knitr-engine Quarto docs using `{stata}` chunks (Statamarkdown),
> `{python}` via reticulate, `{julia}` via JuliaCall — see
> `research-guides/standard-errors/standard-errors.qmd` and
> `research-guides/mixed-effects-models/mixed-effects-models.qmd` for real usage.
>
> 1. **Stata:** locate the binary inside `/Applications/Stata` (StataMP/SE/BE —
>    check which .app exists), symlink it onto PATH or set the Statamarkdown
>    `stata.engine.path` knitr option, and verify with a one-chunk test render.
> 2. **Julia:** install (juliaup via Homebrew preferred), add the packages the
>    legacy CI used (DataFrames, GLM, MixedModels, Distributions, StatsBase,
>    Plots, RCall) plus IJulia; verify JuliaCall finds it from R.
> 3. **Python:** create a dedicated env (3.12 to match legacy CI) with pandas,
>    numpy, statsmodels, scipy, matplotlib, seaborn, scikit-learn; point
>    reticulate at it via `RETICULATE_PYTHON` or `.Rprofile`.
> 4. **R packages:** install the legacy CI list (line 56 of
>    `.github/workflows/deploy-to-website.yml`): Statamarkdown, reticulate,
>    JuliaCall, fixest, lmtest, sandwich, lme4, tidyverse, haven, broom,
>    effectsize, pwr, knitr, rmarkdown, etc.
> 5. **Acceptance:** create a scratch 4-chunk test qmd OUTSIDE both repos (e.g.
>    `/tmp/lang-test.qmd`) with one trivial chunk per language; `quarto render`
>    completes with all four executing. Then render one real guide
>    (`standard-errors`) successfully. Record exact versions and any env vars
>    needed in a short note — B-1's README will absorb it.
> Do not commit anything; this is machine setup.

---

## C-3: Extend the `cross-lang-verify` skill

**Model:** `claude-opus-4-8` — this is verification-procedure design; rigor and
edge-case reasoning matter more than code volume. (The skill's own frontmatter
should also be bumped from `claude-opus-4-7` to `claude-opus-4-8`.)
**Persona:** Keep the skill's existing persona: rigorous statistical programmer,
formal verification audit, conservative about discrepancies.
**Goal:** The skill verifies numerical agreement across R, Python, Stata, and Julia,
and audits (without numerically verifying) the AI-prompt tab.

**Where it lives:** no skill file was found in either repo. Install the current
content at `/Users/te272/StatLab/ResearchGuides/.claude/skills/cross-lang-verify/SKILL.md`
(it gates content, so it belongs in the content repo) before extending it.

**Prompt:**

> Install the existing `cross-lang-verify` skill content (provided separately) at
> `.claude/skills/cross-lang-verify/SKILL.md` in
> `/Users/te272/StatLab/ResearchGuides`, then extend it:
>
> 1. **Four-language matrix.** Replace the R↔Python pairing rule: the primary
>    language is whichever the guide's prose treats as canonical (usually R);
>    replicate in every *other* language that has equivalent packages, and compare
>    each replication against the primary. Extend the package-equivalence table:
>    - regression/GLM: R `stats`/`fixest` ↔ Python `statsmodels` ↔ Stata
>      `regress`/`logit`/`ivregress` ↔ Julia `GLM.jl`
>    - mixed models: `lme4` ↔ `statsmodels.mixedlm` ↔ `mixed` ↔ `MixedModels.jl`
>    - robust/clustered SEs: `sandwich`/`fixest` ↔ `cov_type=` ↔ `vce()` ↔
>      `CovarianceMatrices.jl`
>    Where a language lacks a true equivalent (e.g., no Julia analogue for a
>    specialized routine), the skill must say "NOT REPLICABLE: <reason>" rather
>    than force a bad comparison.
> 2. **Tolerance policy.** Keep 4 d.p. as the default but add a documented
>    exception list (e.g., REML vs ML defaults, different df corrections —
>    HC1 vs HC3, Satterthwaite vs residual df) where the skill must state which
>    default each package uses before declaring MISMATCH.
> 3. **Execution details.** Replications are written to
>    `verify_<original>.<R|py|do|jl>` and run via the local toolchain from C-2
>    (Stata via the CLI binary; document the invocation). Stata is
>    local-only — the skill must note when Stata verification was skipped for
>    environment reasons vs. failed.
> 4. **AI-prompt tab — in scope, NOT numerically verified.** Add a step: for each
>    guide section, check the AI-prompt tab against a concreteness standard — it
>    must name (a) the target language, (b) the specific package/tool, (c) the
>    data file or structure, (d) the expected output/quantity. Example of
>    passing: "Write an R script that fits a mixed-effects model on `sleep.csv`
>    using `lme4::lmer` and report the random-intercept variance." Failing:
>    "Ask an AI to help with mixed models." The skill repairs failing prompts and
>    reports them as `PROMPT REPAIRED` line items — never as numerical MISMATCH.
> 5. Update the report format to a per-language matrix (✓ / MISMATCH /
>    NOT REPLICABLE / SKIPPED-ENV) plus the prompt-audit lines.
> Acceptance: run the extended skill on `standard-errors` (after C-1a) and produce
> a full matrix report. Only modify the skill file and write `verify_*` scratch
> files inside the guide's directory (gitignore them).

### Notes — experiment: concreteness-check vs. execute-and-check (DECIDE LATER)

Two ways the skill can treat the AI-prompt tab. **Default (decided): concreteness
check** — validate/repair the prompt text against the four-part standard above.
**Alternative: execute-and-check** — actually feed each AI-prompt tab to a coding
agent (e.g. `claude -p "<tab text>"` headless), run the script it produces, and
sanity-check its output against the guide's other tabs.

Design for the deciding experiment (do not run during this plan):

- **Setup:** pick 3 guides spanning difficulty — `pvalues` (simple),
  `standard-errors` (medium, many SE variants), `mixed-effects-models` (hard,
  REML/ML trapdoors). Run both modes on all three.
- **Measure:** (a) real defects caught by execute-and-check that the concreteness
  check missed (prompt is well-formed but produces wrong/divergent results);
  (b) false alarms (execute-and-check flags benign variation — seeds, print
  precision); (c) cost — tokens + wall-clock per guide for each mode;
  (d) flakiness — re-run execute-and-check twice per guide; count
  non-deterministic verdict flips.
- **Decision rule (suggested):** if (a) ≥ 2 real catches across the three guides
  and flakiness ≤ 1 flip, promote execute-and-check to an occasional deep-audit
  mode (e.g., before each launch milestone) while keeping concreteness as the
  per-guide gate. If (a) = 0, drop execute-and-check entirely. Full replacement
  of the default is only justified if (b) and (d) are both ~zero — unlikely,
  since agent-generated scripts add a second source of nondeterminism on top of
  the statistical comparisons.
- **Expectation to test against:** the concreteness check is cheap and
  deterministic but can't catch a well-formed prompt that's statistically wrong
  (e.g., names the wrong variance component). Execute-and-check can, but at
  roughly 10–50× token cost and with verdicts that depend on agent behavior.
  The experiment exists to find out whether that failure mode occurs in practice
  in these guides.

---

## C-1a: Expand one exemplar guide (`standard-errors`) to the full 5-tab pattern

**Model:** `claude-opus-4-8` — this run *defines the pattern* (tabset structure,
chunk options, AI-prompt style) that 12 other guides will copy; statistical
correctness across four languages is the hard part.
**Persona:** Statistical programmer + technical editor; values pedagogical parity
across languages over line-by-line translation.
**Goal:** Every tabset in `standard-errors.qmd` has R, Python, Stata, Julia, and
AI-prompt tabs, all executing and rendering cleanly.

**Prompt:**

> Working dir: `/Users/te272/StatLab/ResearchGuides`, file
> `research-guides/standard-errors/standard-errors.qmd`. Toolchain from C-2 is
> ready. Read the whole guide first; it has 4 tabsets (lines ~77, 223, 266, 299)
> currently covering R/Python/Stata.
>
> For every tabset: add a **Julia** tab (GLM.jl / CovarianceMatrices.jl
> equivalents) and an **AI Prompt** tab. Keep existing R/Python/Stata code as-is
> unless broken. AI-prompt tabs contain a short fenced text block meeting the
> concreteness standard (language, package, data, expected output — see the
> skill spec in C-3) phrased so a student can paste it into any coding agent;
> where the guide section is conceptual (no computation), the prompt should ask
> the agent to *demonstrate* the concept on the guide's dataset.
> Normalize tab header names exactly to: `R`, `Python`, `Stata`, `Julia`,
> `AI Prompt` (these become the site-wide convention).
> Render with `quarto render standard-errors.qmd` — all chunks must execute
> (Stata included, locally). Then run the extended `cross-lang-verify` skill
> (C-3) and resolve any MISMATCH before finishing.
> Acceptance: clean render; skill matrix all ✓ / documented NOT REPLICABLE; the
> rendered HTML's tabsets show 5 tabs. Record any reusable chunk-option patterns
> (e.g., Stata data-handoff via `haven`/`export delimited`) in a short
> `research-guides/EXPANSION-NOTES.md` for C-1b agents. Do not restructure the
> guide's prose.

---

## C-1b: Expand the remaining 12 guides

**Model:** `claude-sonnet-4-6` — pattern application per guide, one agent run per
guide; escalate a guide to `claude-opus-4-8` only if its statistics are subtle
(`mixed-effects-models`, `glmms` qualify — REML/ML and GLMM-family defaults differ
across packages).
**Goal:** All 13 ported guides follow the 5-tab pattern and pass the gate.

Per-guide workload (from the audit table): most guides add Julia + AI tabs to
existing 3-language tabsets. The heavy lifts: **glmms** (8 tabsets, R-only),
**mixed-effects-models** (6 tabsets, needs Python *and* Stata added),
**model-selection / panel-regression** (no tabsets — code must be restructured
into tabsets first), **variable-selection** (no code at all — needs code authored
from prose, treat as new-content task and budget accordingly).

**Prompt (template — run once per guide, substituting `<slug>`):**

> Working dir: `/Users/te272/StatLab/ResearchGuides`, file
> `research-guides/<slug>/<slug>.qmd`. Read it fully, plus
> `research-guides/EXPANSION-NOTES.md` and one rendered example of the pattern:
> `research-guides/standard-errors/standard-errors.qmd` (post-C-1a).
> Bring every code-bearing section to the 5-tab standard (`R`, `Python`, `Stata`,
> `Julia`, `AI Prompt`), creating tabsets where code currently sits bare.
> Statistical results must be equivalent across tabs — match estimator defaults
> deliberately (document choices in chunk comments only where a package default
> differs). Render clean with `quarto render`, then run the `cross-lang-verify`
> skill and fix MISMATCHes. Acceptance: clean render, gate report attached,
> 5 tabs visible in HTML. Don't touch other guides; don't edit prose beyond
> what tab restructuring requires.

---

## C-4: Per-guide validation gate

**Model:** `claude-sonnet-4-6` — running the skill is mechanical, but adjudicating
MISMATCH causes needs statistical judgment.
**Goal:** A standing record that every shipped guide passed cross-language
verification.

**Prompt:**

> Working dir: `/Users/te272/StatLab/ResearchGuides`. For each guide listed in
> `statlab/guides.exclude`'s complement (i.e., every non-excluded guide), run the
> `cross-lang-verify` skill and append its matrix report to
> `research-guides/VALIDATION-LOG.md` under a dated heading. Any MISMATCH: do not
> fix code yourself — file it as an entry in the log flagged `NEEDS REVIEW` with
> the skill's likely-cause analysis, and continue to the next guide. Acceptance:
> one dated section per guide; summary table at top (guide × status). This gate
> re-runs after any guide edit and before promotion (B-2 precondition).

---

## D-1: Static export — freeze the Flask site for GitHub Pages

**Model:** `claude-fable-5` — touches routes, templates, build tooling, and the
freeze configuration together; route/URL correctness across the whole site.
**Goal:** `make freeze` produces a fully static `docs/` tree that serves the entire
site with no Python running.

**Architecture critique (per your invitation):** static is the right call for
alpha — the app has zero server-side state (no forms, no auth; booking links go to
schedule.yale.edu) and GitHub Pages is free and already wired to this org. The real
costs you're accepting: (1) the tag-search feature planned in ALPHA.md
(`/research-guides?tag=`) can't be a server-side query — it must become client-side
JS filtering at freeze time; (2) every guide update requires a re-freeze-and-push
rather than appearing live; (3) Flask becomes purely a templating engine, at which
point a static-site generator would do the same job with less machinery — keep
Flask anyway for now since the extractor/template work is done, but revisit if the
site ever needs accounts, submissions, or live data. The current `app.py` is
freeze-friendly with one exception: `inject_now()` stamps freeze-time, fine; the
dynamic per-request `extract()` is the thing D-1 bakes out.

**Prompt:**

> Working dir: `/Users/te272/StatLab/statlab`, branch `flask-experiment`. Read
> `app.py`, all templates, and `tools/build.py`. A `.nojekyll` already exists at
> repo root (move/copy it into the output).
>
> 1. Add Frozen-Flask (`flask-frozen`) and implement `tools/freeze.py`: a URL
>    generator for every route — `/`, `/about`, `/consultations`, `/about/team`,
>    `/research-guides`, `/guides/<slug>/` for each manifest entry,
>    `/guides/<slug>/<asset>` for every file in each guide dir, all
>    `/consultants/<slug>`, and the three `/assets/...` routes (fonts,
>    consultant photos, statlab photos).
> 2. Output to `docs/` with `FREEZER_RELATIVE_URLS` *off* — the site will live
>    under the `/statlab/` project-pages prefix, so set `FREEZER_BASE_URL` /
>    template URL generation accordingly; verify every `url_for` in templates
>    survives the prefix (this is the classic project-pages bug).
> 3. The 301 redirect route `guide_no_slash` can't freeze — either exclude it or
>    emit an HTML meta-refresh stub.
> 4. `make freeze` target; acceptance: `python -m http.server --directory docs`
>    (mounted under a `/statlab/` prefix to simulate Pages — document how) serves
>    every page with no 404s in the browser console, tabsets and MathJax work on
>    a guide page, fonts and photos load. Diff a guide page against the live
>    Flask version for visual parity.
> Note: `assets/` is gitignored — decide nothing here; D-2/F-2 handle whether
> frozen copies in `docs/` may be committed. Just ensure the freeze *includes*
> them so the question is forced.

---

## D-2: GitHub Pages publishing workflow

**Model:** `claude-sonnet-4-6` — single workflow file against a working local
build.
**Goal:** Pushing guide updates publishes the frozen site to
https://yalelibrarystatlab.github.io/statlab/ without manual steps.

**Prompt:**

> Working dir: `/Users/te272/StatLab/statlab`, branch `flask-experiment`. D-1's
> freeze works locally. Create `.github/workflows/publish.yml` (this repo
> currently has NO workflows):
>
> 1. Trigger: push to `flask-experiment` touching `research-guides/**`, `temp/**`,
>    `templates/**`, `app.py`, `tools/**`, plus `workflow_dispatch`. (B-2 step 7
>    flips the branch to `main` at promotion.)
> 2. Steps: checkout → setup Python (pinned from B-1's requirements) →
>    `pip install -r requirements.txt` → `tools/build.py` → `tools/freeze.py` →
>    deploy via `actions/upload-pages-artifact` + `actions/deploy-pages`
>    (Actions-based Pages, NOT committing `docs/` — avoids both repo bloat and
>    the gitignored-assets contradiction).
> 3. **Constraint:** CI cannot render guides (no Stata; R/Julia toolchain not
>    worth CI minutes for alpha). The workflow freezes *committed rendered HTML*
>    only — rendering stays local via `tools/port_guides.py`. Fail with a clear
>    message if `temp/` or the manifest is missing/empty.
> 4. **Assets:** fonts/photos are gitignored, so CI won't have them. For alpha:
>    add an explicit allowlist exception (`!assets/consultant-photos/` etc.) ONLY
>    after the licensing question (Open Questions §3) is answered; until then the
>    workflow must tolerate missing assets and the deployment summary must list
>    what was absent.
> 5. Repo Settings change (document, don't assume): Pages → Source → GitHub
>    Actions. Note the old Quarto site currently publishes from `main`; deploying
>    from `flask-experiment` via Actions will REPLACE the live site — confirm
>    with the team before first run, or keep the workflow `workflow_dispatch`-only
>    until promotion (recommended; the prompt-runner should choose this default).
> Acceptance: `workflow_dispatch` run goes green and the Pages URL serves the
> frozen site (or, if holding until promotion, the run goes green with deploy
> step skipped on non-main).

---

## E: Design — placeholder, do not plan here

**Reserved position:** step 12 of the order of operations (after the site builds
statically end-to-end, before the Pages workflow is finalized and before
promotion).

Design will be scoped as a distinct task with its own brief. Nothing in this
checklist constrains it except mechanics: templates live in `templates/` extending
`base.html`; guide pages inject Quarto-rendered `main_html` (so guide-internal
styling is Quarto's, themed by which Quarto assets `_STRIP_ASSET_PATTERNS` lets
through); fonts are the gitignored Yale faces in `assets/yale-font/`. Treat
ALPHA.md's "UX & Design" items (mobile nav, TOC, breadcrumbs) as inputs to that
brief, not as decided work.

**Intentionally opaque. Do not let pipeline tasks make design decisions "while
they're in there."**

---

## F: Risks & problems found

Each item: what's wrong → suggested fix. F-1 below is the only one promoted to a
task (step 2 in the order); the rest are absorbed into tasks noted in brackets.

1. **The legacy workflow is a loaded gun aimed at the new site.** Any push to
   ResearchGuides `main` touching `research-guides/**` renders 2 hardcoded guides
   and `rsync --delete`s into the statlab repo, then commits to its `main` — it
   would overwrite/delete the Flask branch's `research-guides/` content the moment
   it lands on main. → **Task F-1 (`claude-haiku-4-5-20251001`, mechanical):**
   immediately add `if: false` to the job (or comment out the push trigger,
   keeping `workflow_dispatch`) in `deploy-to-website.yml`, commit with a message
   explaining it's disarmed pending the Flask migration. Deleted for good at B-2
   step 2. Also remove the now-stale `mixed-effects-models`/`standard-errors`
   hardcoding comment at line 21 ("Update with your actual website repo" — it was
   never updated).
2. **`assets/` is gitignored but the site depends on it.** Fonts and consultant
   photos exist only on this machine; any CI build or fresh clone produces a
   broken-looking site, and the freeze output's committability is ambiguous.
   → Decide via Open Question 3 (font licensing); then either track
   `assets/consultant-photos/` + self-host-able assets with an allowlist, or have
   CI pull them from a private location. [D-1, D-2]
3. **Stale guide snapshot in `statlab/research-guides/`.** Contains excluded
   guides (`diffindiff`, `research-guide-quarto-template`), a guide with no source
   (`multivariate-regression` — also one of only two currently *live* in `temp/`),
   and the legacy `guides/` dir. → A-3's first real run replaces the tree; F-1
   should delete `guides/`; multivariate-regression needs Open Question 4.
4. **Two sources of truth for "what's published."** Legacy: inclusion array
   duplicated *twice inside the YAML* (lines 76 and 276 — they can drift). Flask:
   whatever was hand-copied to `temp/`. → A-1's `guides.exclude` + manifest
   becomes the single source. [A-1]
5. **The legacy workflow generates the guide index page from a hardcoded
   `case` statement in YAML** (descriptions for exactly 2 guides, fallback boilerplate
   for the rest). Unmaintainable and already superseded by
   `templates/research_guides.html`. → Dies with the workflow at B-2. [B-2]
6. **The legacy render fallback is silently broken:** `quarto render
   --execute-params eval:false` is not a valid Quarto invocation (`--execute-params`
   takes a YAML file; this string is not one), so the "render without execution"
   fallback path has likely never worked — failures fell through to the ❌ echo
   while the job still exited 0 (no `set -e`, no failure propagation). Guides
   could "deploy" missing. → A-3 replaces this with explicit failure reporting.
7. **Local env gaps block the multi-language goal today:** no Julia, Stata off
   PATH, system Python 3.9 vs CI's 3.12, nothing pinned (no renv/venv lockfiles
   anywhere). → C-2, then B-1 pins. [C-2, B-1]
8. **Stata can never run on free GitHub runners** (license). The pipeline must
   treat Stata output as locally-rendered, committed artifact — which D-2's
   "freeze committed HTML only" design does — but this means **a guide edited
   without a local re-render publishes stale Stata output silently.** → A-3's
   summary table + C-4 gate re-run after every guide edit are the control;
   consider a build.py check comparing qmd mtime vs html mtime. [A-3, C-4]
9. **`build.py` scaffold bugs** (dead `app/` paths, import that only works from
   `tools/` cwd) — fixed by A-1. **`extract()` per-request with no cache** — fixed
   by A-2; moot after D-1 freezes. [A-1, A-2]
10. **13 of 13 portable guides fail the 4-language standard**; 3 need structural
    work (no tabsets) and 1 (`variable-selection`) has no code at all — that one
    is authoring work, not translation, and will dominate C-1b's budget if not
    scoped consciously. → C-1b flags it; consider deferring it to post-alpha via
    `guides.exclude`. [C-1b]
11. **`mixed-effects-models` is the only Julia guide and one of two live guides** —
    yet it's missing Python and Stata; the *other* live guide
    (`multivariate-regression`) has no source qmd in ResearchGuides at all. The
    two guides closest to "shipped" are among the furthest from the standard.
    [C-1b, Open Q4]
12. **No skill file for `cross-lang-verify` exists on disk** in either repo
    despite the skill being part of the stated QA process. → Installed by C-3.
13. **Chunk-option style is legacy-Rmd** (`{stata, echo = T, eval = T}`,
    `python.reticulate = T`) rather than Quarto hash-pipe (`#| echo: true`).
    Works via knitr, but C-1a/C-1b agents must keep the existing style per guide —
    mixing styles in one document is where chunk options silently stop applying.
    Standardize wholesale post-alpha if desired, not during expansion. [C-1a/b]
14. **Repo hygiene:** `.DS_Store` tracked in statlab; `temp/` (the actual publish
    dir!) name suggests disposability — rename to `published/` post-alpha or at
    least document it; ResearchGuides has rendered HTML committed alongside
    sources (fine for the Stata strategy in §8, but `_files/` dirs will bloat
    history — consider Git LFS post-alpha). [F-1 for .DS_Store; rest post-alpha]
15. **`DEPLOY_TOKEN` PAT** in ResearchGuides has push rights to the statlab repo
    and outlives its purpose after promotion. → Revoked at B-2 step 6. [B-2]

---

## Open questions (need your decision, not an agent's)

1. **Confirm the publish-at-promotion sequencing:** D-2 recommends keeping the new
   Pages workflow `workflow_dispatch`-only until B-2, meaning the public site
   stays the old Quarto site until promotion day. OK, or do you want a parallel
   staging URL (would require a second repo or a `gh-pages`-branch hack)?
2. **Where should rendering ultimately live?** This plan keeps `quarto render`
   local (Stata constraint) with CI only freezing committed HTML. Alternative:
   CI renders R/Python/Julia and only Stata is local. More CI complexity, fresher
   guides. Alpha says local; revisit at launch.
3. **Yale font licensing:** can `assets/yale-font/` files be committed to a public
   repo / served from public Pages? If no, the site needs a fallback stack and
   the freeze must treat fonts as optional. Blocks the final answer to F-2.
4. **`multivariate-regression`:** live on the Flask site but has no source in
   ResearchGuides. Recover/move its `.qmd` into ResearchGuides, or drop it from
   alpha?
5. **`variable-selection`:** prose-only. Author code for it (large task) or
   exclude from alpha?
6. **Defer-list candidates:** you said more exclusions are likely. `glmms`
   (8 R-only tabsets) and `model-selection`/`panel-regression` (no tabsets) are
   the most expensive expansions — worth excluding any of them from alpha to
   protect the launch date?
7. **The C-3 experiment** (concreteness vs execute-and-check) — schedule it after
   three guides have passed the gate, or defer past alpha?

---

*Plan complete — no INCOMPLETE section needed. All 14 ordered steps have task
sections; every prompt is self-contained and runnable as written, in order.*


---

## Addendum — 2026-06-12 (post-A-3)

### Policy change: branch-based readiness replaces the exclusion list

Decided after A-3 landed: **unfinished guides no longer live on ResearchGuides
`main`** — they were moved to per-guide branches, and `main` contains only
publish-ready guides (currently `glmms`, `mixed-effects-models`,
`panel-regression`, plus the never-published template). Consequences:

- `guides.exclude` shrinks to a single permanent entry
  (`research-guide-quarto-template`). Readiness is now expressed by *merging a
  guide's branch to main*, not by editing the exclusion file.
- This supersedes Open Question 6 (defer-list) and the per-guide exclusion
  churn anticipated in C-1b. The C-1b workflow becomes: expand the guide on
  its branch → pass the C-4 gate → merge to main → `make port` (or
  `port-render`) in statlab.
- Open Question 4 is resolved: `multivariate-regression` (no upstream source)
  was deleted from the statlab working tree; recoverable from git history if
  ever needed.
- The site was synced to this state on 2026-06-12: 3 guides ported
  (`--no-render`, committed HTML), 7 stale guides evicted from `temp/` via
  `build.py --clean`, tests green.

### Automation between the repos — DECIDE LATER

There is deliberately **no automatic connection** from ResearchGuides to
statlab: `tools/port_guides.py` is a pull-on-demand command, because rendering
requires local Stata and "finished" is a human judgment (now expressed by
merging to main). Two upgrade options were discussed, both deferred:

1. **Local git hook (cheap, alpha-friendly):** a `post-commit`/`post-merge`
   hook in ResearchGuides that runs
   `port_guides.py --only <changed slugs> --no-render` whenever a commit on
   main touches `research-guides/**`. Removes the manual copy step on this
   machine; rendering must still have happened. With the new branch policy
   the natural trigger is `post-merge` (a guide branch merging into main).
2. **Cross-repo CI (post-promotion):** a ResearchGuides workflow that, on push
   to main, performs the `--no-render` port of committed HTML into statlab via
   PR, which then triggers statlab's publish workflow (D-2). Buys convenience
   for multi-person merges, but re-introduces a cross-repo token (see Risks
   §15) and only moves HTML someone already rendered locally. Folds into Open
   Question 2.

Decision deferred until the per-guide expansion loop (C-1b/C-4) is running and
the merge cadence to main is known — pick option 1 if the friction is mostly
local, option 2 only if teammate merges to main regularly outpace local ports.
