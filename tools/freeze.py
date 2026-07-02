"""
freeze.py — build a static copy of the StatLab Flask site into docs/.

Frozen-Flask drives the app through its test client and writes one file per
URL. The site deploys to GitHub Pages as a *project* site, served from the
``/statlab/`` path prefix, so every internal link must carry that prefix.

We get the prefix for free by:

  * routing every internal URL in the templates through ``url_for()`` (so the
    prefix is injected by Flask, never hard-coded), and
  * setting ``FREEZER_BASE_URL`` so Frozen-Flask runs ``url_for`` under
    ``SCRIPT_NAME='/statlab'`` and writes ``/statlab/...`` links into the
    output (``FREEZER_RELATIVE_URLS`` stays off, per the deploy plan).

The scheme/host of ``FREEZER_BASE_URL`` never appear in the output — no
``url_for`` uses ``_external=True`` — so only its path (``/statlab``) matters.

Run:  python tools/freeze.py        (or: make freeze)

Acceptance / local preview — simulate the Pages prefix with a symlink, since
``http.server`` can't mount under a subpath on its own::

    mkdir -p /tmp/pages && ln -sfn "$PWD/docs" /tmp/pages/statlab
    python -m http.server --directory /tmp/pages 8000
    # open http://localhost:8000/statlab/
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    # `python tools/freeze.py` puts tools/ (not the repo root) on sys.path;
    # add the root so `import app` resolves the same way it does for pytest.
    sys.path.insert(0, str(ROOT))

from flask_frozen import Freezer, MissingURLGeneratorWarning

from app import (
    ASSETS_DIR,
    TEMP_GUIDES_DIR,
    _first_guide_image,
    app,
    cached_extract,
    list_available_guides,
    load_consultants,
)

# GitHub Pages project site: https://<owner>.github.io/<repo>/. Only the path
# prefix is baked into the (root-relative) links Frozen-Flask emits. The repo
# is "statlab", so the prefix is "/statlab"; CI overrides it from the repo name
# (STATLAB_URL_PREFIX) so a rename can't silently break every link. An empty
# value targets a root deployment (a <user>.github.io user/org page).
_prefix = os.environ.get("STATLAB_URL_PREFIX", "statlab").strip("/")
URL_PREFIX = f"/{_prefix}" if _prefix else ""
DOCS_DIR = ROOT / "docs"
NOJEKYLL = ROOT / ".nojekyll"

app.config.update(
    FREEZER_DESTINATION=str(DOCS_DIR),
    FREEZER_BASE_URL=f"http://localhost{URL_PREFIX}/",
    FREEZER_RELATIVE_URLS=False,
    # Keep our post-freeze .nojekyll across runs (Frozen-Flask prunes files it
    # didn't generate).
    FREEZER_DESTINATION_IGNORE=[".nojekyll"],
    # guide_thumbnail 302-redirects a local-image thumbnail to the real asset;
    # 'follow' (the default, spelled out here) saves the followed image bytes
    # at the /thumbnail URL. Data-URI thumbnails return 200 bytes directly.
    FREEZER_REDIRECT_POLICY="follow",
    # /guides/<slug>/thumbnail files have no extension by design, so their
    # guessed type (octet-stream) never matches the real image Content-Type.
    # <img> sniffs content regardless, so silence that known, benign mismatch.
    FREEZER_IGNORE_MIMETYPE_WARNINGS=True,
)

freezer = Freezer(app)


def _dir_files(base: Path):
    """POSIX-relative paths for every non-hidden file under ``base`` (recursive)."""
    if not base.is_dir():
        return
    for path in sorted(base.rglob("*")):
        if path.is_file() and not path.name.startswith("."):
            yield path.relative_to(base).as_posix()


# ---- Parameterised routes -------------------------------------------------
# No-argument routes (/, /about, /consultations, /workshops, /about/team,
# /research-guides) are discovered automatically by Frozen-Flask, so only the
# routes that take URL arguments need explicit generators below.


@freezer.register_generator
def guide_index():
    for guide in list_available_guides():
        yield {"slug": guide["slug"]}


@freezer.register_generator
def guide_asset():
    # Every file in each guide directory — figures, _files/ bundles, the raw
    # <slug>.html, data, etc. — so nothing a guide references can 404.
    for guide in list_available_guides():
        for rel in _dir_files(TEMP_GUIDES_DIR / guide["slug"]):
            yield {"slug": guide["slug"], "filename": rel}


@freezer.register_generator
def guide_thumbnail():
    # Only guides whose first figure is usable have a thumbnail; the others
    # render an inline SVG placeholder and the route would 404.
    for guide in list_available_guides():
        html_file = TEMP_GUIDES_DIR / guide["slug"] / f"{guide['slug']}.html"
        if not html_file.is_file():
            continue
        try:
            if _first_guide_image(cached_extract(html_file)) is not None:
                yield {"slug": guide["slug"]}
        except Exception:
            pass


@freezer.register_generator
def consultant_profile():
    for consultant in load_consultants():
        yield {"slug": consultant["slug"]}


# ---- Asset routes ---------------------------------------------------------


@freezer.register_generator
def serve_font():
    for name in _dir_files(ASSETS_DIR / "yale-font"):
        yield {"filename": name}


@freezer.register_generator
def serve_eb_garamond():
    for name in _dir_files(ASSETS_DIR / "eb-garamond"):
        yield {"filename": name}


@freezer.register_generator
def serve_logo():
    for name in _dir_files(ASSETS_DIR / "yale-logo"):
        yield {"filename": name}


@freezer.register_generator
def serve_consultant_photo():
    for name in _dir_files(ASSETS_DIR / "consultant-photos"):
        yield {"filename": name}


@freezer.register_generator
def serve_statlab_photo():
    for name in _dir_files(ASSETS_DIR / "statlab-photos"):
        yield {"filename": name}


def freeze() -> Path:
    # guide_no_slash is a 301 -> /guides/<slug>/ redirect and is deliberately
    # NOT frozen: following it would write a *file* named <slug> that collides
    # with the <slug>/ guide directory, and a static host (GitHub Pages,
    # http.server) already 301s /guides/<slug> -> /guides/<slug>/ for
    # directories. Silence Frozen-Flask's "forgot a generator?" nag for it.
    warnings.filterwarnings("ignore", category=MissingURLGeneratorWarning)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    urls = freezer.freeze()  # set of generated URL paths

    # .nojekyll stops GitHub Pages from running Jekyll, which would otherwise
    # drop the Quarto <slug>_files/ directories (a leading '_' = ignored).
    if NOJEKYLL.is_file():
        shutil.copyfile(NOJEKYLL, DOCS_DIR / ".nojekyll")
    else:
        (DOCS_DIR / ".nojekyll").touch()

    # Pagefind runs after the static HTML exists. It sees data-pagefind-body
    # only on guide articles, so raw Quarto files and site chrome stay out of
    # the index while headings become direct section-level results.
    try:
        subprocess.run(
            [sys.executable, "-m", "pagefind", "--site", str(DOCS_DIR)],
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            "Pagefind indexing failed; install requirements-dev.txt and retry"
        ) from exc

    print(f"froze {len(urls)} URLs -> {DOCS_DIR.relative_to(ROOT)}/")
    return DOCS_DIR


if __name__ == "__main__":
    freeze()
