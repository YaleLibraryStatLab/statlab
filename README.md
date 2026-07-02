# StatLab

Flask app serving the Yale StatLab site, including research guides converted
from Quarto.

## Branches

- `main` — legacy static Quarto site (archived HTML output).
- `flask-experiment` — this Flask app. All active development happens here.

## Setup

Requires Python **3.10+** (the repo uses `from __future__ import annotations`
and PEP 585 generics in `tools/`; the system `python3` on macOS may be 3.9, so
install a newer interpreter — e.g. `brew install python@3.12`).

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

### Assets caveat

`assets/` (fonts, consultant photos, StatLab photos, Yale logo) is
**gitignored** — it is not tracked publicly. On a fresh clone this directory
will be missing, and pages that reference it (fonts, photos) will 404 for
those specific files even though the page itself still loads. Copy the
`assets/` directory over manually from another machine or from a backup
before relying on those assets locally.

## Makefile targets

| Target            | What it does                                              |
|-------------------|------------------------------------------------------------|
| `make dev`        | Build the static search index, then run Flask on `http://localhost:5001` |
| `make port`       | Copy one already-rendered guide from the upstream ResearchGuides repo through the pipeline (no quarto run). Usage: `make port SLUG=<slug>` |
| `make port-render`| Render one guide upstream with quarto, then port it. Usage: `make port-render SLUG=<slug>` |
| `make port-all`   | Render + port every non-excluded upstream guide (the full pipeline) |
| `make build`      | Re-publish `research-guides/` → `temp/` + manifest (`tools/build.py`) |
| `make test`       | Run the pytest suite                                        |
| `make freeze`     | Freeze the site into `docs/` and build the Pagefind search index |

## Dev loop for research guides

Guide sources live in the sibling repo
(`../ResearchGuides/research-guides/<slug>/`). `tools/port_guides.py` renders
there, copies the output (never `.qmd` sources) into this repo's
`research-guides/<slug>/`, normalizes the main HTML to `<slug>.html`, and
runs `tools/build.py` to publish `temp/` and `guides_manifest.json`.

1. Edit the guide's `.qmd` in the ResearchGuides repo.
2. Run `make port-render SLUG=<slug>` (or render manually upstream and use
   `make port SLUG=<slug>` to skip the quarto step).
3. With `make dev` running, check the result at
   `http://localhost:5001/guides/<slug>/`.

The Research Guides search reads the generated Pagefind bundle from `docs/`.
`make dev` refreshes that bundle before starting Flask, so search behaves the
same way in the local preview as it does after deployment.

Guide selection is exclusion-based — see `guides.exclude`. Render failures
are collected into a summary table; the run continues past them. Note that
Stata chunks only render on a machine with a local Stata install.

## Testing

```bash
make test
```

Runs a pytest smoke suite (`tests/test_app.py`) that boots the app and checks
`/`, `/research-guides`, and a guide route all return 200.
