# StatLab — Pre-Alpha Task List

Tracks work that must be complete (or explicitly deferred) before the site is shared with external users.

**Status markers**
- `[ ]` Not started
- `[~]` In progress
- `[x]` Done
- `[-]` Deferred / out of scope for alpha

**Priority**
- `P0` — Blocker. Alpha cannot ship without this.
- `P1` — Important. Ship without only if nothing breaks visibly.
- `P2` — Nice-to-have. Defer if time-constrained.

---

## Infrastructure & Content Pipeline

- [ ] **P0 — Auto-update research guides from source**
  Refactor the pipeline so that committing an updated Quarto HTML to
  `research-guides/<slug>/` is sufficient to publish the guide — no manual
  `cp -R` to `temp/` required.
  - [ ] Write `tools/build.py`: walk `research-guides/`, run extractor smoke-check,
        copy accepted guides to `temp/` (or publish dir)
  - [ ] Decide on staging gate: auto-publish all guides vs. explicit allowlist
  - [ ] Wire build step to git post-commit hook or CI action
  - [ ] Confirm hashed-asset and polyfill filter logic survives a fresh Quarto render

- [ ] **P1 — Seed all remaining research guides**
  Convert every guide under `research-guides/` through the Flask framework and
  spot-check for unstyled markup (callouts, tables, side notes, datatables, etc.).

- [ ] **P1 — Handle guides with no abstract / no date gracefully in the listing**
  `research_guides.html` currently shows only title and link; consider adding
  a short teaser (first sentence of abstract if present, otherwise nothing).

---

## Consultant System

> **Note:** The URL scheme uses `/consultants/<slug>` (not `/authors/<slug>`).
> Template is `consultant.html` (not `author.html`). Data store is `data/consultants.json`.
> Seeded with all 6 current consultants (Ellsworth, Chughtai, Jin, Demiray, Brookson, Elkobi).
> Photos served from `assets/consultant-photos/` via Flask routes; fonts from `assets/yale-font/`.
> `assets/` is gitignored.

- [x] **P0 — Consultant data store** (`data/consultants.json`)
  JSON array. Each record: `slug`, `name`, `role`, `bio`, `short_bio`, `status` (`current`/`former`),
  `guides` (list of guide slugs), `links` (github/website/email), `photo` (filename).
  Loader is `load_consultants()` in `app.py`.
  - [~] `consultation_schedule`: booking links are currently hardcoded in the template
        (same in-person + virtual URLs for all current consultants). Add a per-consultant
        field if individual booking pages are ever needed.
  - [ ] Still needed: `research_areas` tags field per consultant

- [x] **P0 — Consultant page template** (`templates/consultant.html`)
  Extends `base.html`. Includes: photo avatar (initials fallback), "Former Consultant"
  badge only for former, external links, bio, booking CTA, guides list with dates.
  Route: `/consultants/<slug>`.
  - [x] Booking CTA wired up: "Book a consultation" bar with In-Person and Virtual
        links to schedule.yale.edu, shown only for `status == 'current'`
  - [ ] Still needed: research areas tag display

- [x] **P0 — Link author names on guide headers to consultant pages**
  `guide.html` resolves each author name against `consultant_map` (passed from route)
  and wraps in `<a href="/consultants/{{ slug }}">`. Falls back to external URL,
  then plain text.

- [x] **P2 — Consultant index / team page** (`/about/team`)
  `templates/team.html`: card grid of current consultants, compact list of former
  consultants (with graceful empty-state copy). Linked from the "About" nav dropdown.
  - [x] Cards show actual headshots (`aspect-ratio: 4/3`, `object-position: center 15%`);
        `short_bio` used for card copy; initials shown as fallback

- [ ] **P1 — Tag search within research guides**
  - [ ] `/research-guides?tag=<tag>` filters the listing to guides whose
        keywords include that tag
  - [ ] Tag pills on each guide header link to filtered listing
  - [ ] Consultant page "research areas" tags also link to filtered listing

---

## UX & Design

- [ ] **P1 — Mobile nav review**
  Test hamburger menu and sticky lang-switcher on narrow viewports.

- [ ] **P2 — Guide table of contents**
  Auto-generate a sticky side TOC from `<h2>` / `<h3>` headings in
  `guide.main_html` (JS or server-side with BeautifulSoup).

- [ ] **P2 — "Back to Research Guides" breadcrumb on guide pages**

---

## Quality & Reliability

- [ ] **P1 — Asset 404 smoke test**
  Add a check in `tools/build.py` (or a standalone script) that fetches every
  local asset path referenced in the extracted HTML and reports missing files
  before a guide goes live.

- [ ] **P1 — Error pages**
  Custom `404.html` and `500.html` templates that extend `base.html`.

- [ ] **P2 — Cache extracted guide data**
  `extract()` re-parses HTML on every request. Add a simple in-memory or
  file-based cache keyed on `(path, mtime)` to avoid redundant parsing under
  load.

---

## Deployment

- [ ] **P0 — Replace Flask dev server with a production WSGI server**
  (Gunicorn or Waitress). Update startup command / Procfile.

- [ ] **P1 — Environment config**
  Move `debug`, `port`, and any future secrets to environment variables /
  `.env` file. Add `.env.example`.

- [ ] **P2 — Static asset fingerprinting / cache headers**
  Set long-lived cache headers on guide `_files/` assets; bust on Quarto re-render.
