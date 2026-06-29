import base64
import json
import logging
import re
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, send_from_directory, url_for

from tools.extractor import extract

app = Flask(__name__)
logger = logging.getLogger(__name__)

TEMP_GUIDES_DIR = Path(__file__).parent / "temp"
CONSULTANTS_FILE = Path(__file__).parent / "data" / "consultants.json"
GUIDES_MANIFEST_FILE = Path(__file__).parent / "guides_manifest.json"

# Assets that must never load inside base.html:
#   • Full Bootstrap distribution — clobbers site nav/footer styles.
#     Hashed pattern covers Quarto >= 1.7 (bootstrap-<hash>.min.css).
#   • polyfill.io — domain was hijacked in 2024; the CDN is dead/malicious.
_STRIP_ASSET_PATTERNS = [
    re.compile(r"/bootstrap(?:-[0-9a-f]+)?\.min\.(css|js)$"),
    re.compile(r"polyfill\.min\.js"),   # matches polyfill.io AND cdnjs.cloudflare.com/polyfill
]

# Self-contained renders (embed-resources: true) inline Bootstrap as a
# data: URI stylesheet, which has no filename for the patterns above to
# match. Its `--bs-blue` custom property (URL-encoded or literal) is the
# marker; the quarto-hl data-CSS (syntax highlighting) must be kept.
_DATA_CSS_BOOTSTRAP_MARKERS = ("%2D%2Dbs%2Dblue", "--bs-blue")


def _filter_quarto_assets(assets):
    kept = []
    for a in assets:
        if any(p.search(a.src) for p in _STRIP_ASSET_PATTERNS):
            continue
        if a.src.startswith("data:text/css") and any(
            m in a.src for m in _DATA_CSS_BOOTSTRAP_MARKERS
        ):
            continue
        kept.append(a)
    return kept


def load_consultants():
    if not CONSULTANTS_FILE.is_file():
        return []
    with open(CONSULTANTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _consultant_map(consultants):
    """Return a dict keyed by lowercased name for O(1) lookup in templates."""
    return {c["name"].strip().lower(): c for c in consultants}


# extract() results keyed on (path, mtime) so repeated views don't re-parse
# the same guide HTML.
_extract_cache: dict[Path, tuple[float, object]] = {}


def cached_extract(html_file):
    mtime = html_file.stat().st_mtime
    cached = _extract_cache.get(html_file)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    guide = extract(html_file)
    _extract_cache[html_file] = (mtime, guide)
    return guide


def load_guides_manifest():
    """Read guides_manifest.json, or None if missing/unreadable."""
    if not GUIDES_MANIFEST_FILE.is_file():
        return None
    try:
        with open(GUIDES_MANIFEST_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not read %s: %s", GUIDES_MANIFEST_FILE.name, exc)
        return None


def _scan_temp_guides():
    """Scan temp/ for guide directories that contain <slug>/<slug>.html."""
    if not TEMP_GUIDES_DIR.is_dir():
        return []
    guides = []
    for entry in sorted(TEMP_GUIDES_DIR.iterdir()):
        if not entry.is_dir():
            continue
        html_file = entry / f"{entry.name}.html"
        if not html_file.is_file():
            continue
        try:
            guide = cached_extract(html_file)
            title, date = guide.title or entry.name, guide.date
        except Exception:
            title, date = entry.name, None
        guides.append({"slug": entry.name, "title": title, "date": date})
    return guides


def list_available_guides():
    """List published guides from guides_manifest.json, falling back to a
    directory scan of temp/ if the manifest is missing or unreadable."""
    manifest = load_guides_manifest()
    if manifest is None:
        logger.warning(
            "%s not found; falling back to scanning %s (run tools/build.py to "
            "generate the manifest)",
            GUIDES_MANIFEST_FILE.name, TEMP_GUIDES_DIR.name,
        )
        return _scan_temp_guides()
    return [
        {"slug": g["slug"], "title": g["title"], "date": g.get("date")}
        for g in manifest
    ]


@app.context_processor
def inject_now():
    return {"now": datetime.utcnow()}


@app.template_filter("friendly_date")
def friendly_date(value):
    """Render an ISO date string ('2026-06-01') as 'June 1, 2026'."""
    if not value:
        return ""
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%B %-d, %Y")
    except ValueError:
        return value


ASSETS_DIR = Path(__file__).parent / "assets"

# The Yale 2024 typeface is proprietary and must not be published. Its .otf
# files live in assets/yale-font/ (gitignored) and are present only in local
# dev; the public/CI build ships without them. Templates gate the @font-face
# on this flag so the font is referenced only when it is actually served —
# otherwise --font-serif falls back to the free EB Garamond / Georgia stack.
HAS_YALE_FONT = any((ASSETS_DIR / "yale-font").glob("*.otf"))


@app.context_processor
def inject_has_yale_font():
    return {"has_yale_font": HAS_YALE_FONT}


@app.route("/assets/yale-font/<filename>")
def serve_font(filename):
    return send_from_directory(ASSETS_DIR / "yale-font", filename)


@app.route("/assets/yale-logo/<filename>")
def serve_logo(filename):
    return send_from_directory(ASSETS_DIR / "yale-logo", filename)


@app.route("/assets/consultant-photos/<filename>")
def serve_consultant_photo(filename):
    return send_from_directory(ASSETS_DIR / "consultant-photos", filename)


@app.route("/assets/statlab-photos/<path:filename>")
def serve_statlab_photo(filename):
    return send_from_directory(ASSETS_DIR / "statlab-photos", filename)


def _first_guide_image(guide):
    """First usable figure in a guide — a local file path or a data: URI."""
    for img in guide.images:
        if img.is_local or img.src.startswith("data:image/"):
            return img
    return None


def _enrich_guides(guides):
    """Add authors, abstract, and thumbnail info to manifest guide entries
    by reading each guide's HTML (cached, so repeat views are cheap)."""
    enriched = []
    for g in guides:
        info = dict(g, authors=[], abstract=None, has_thumbnail=False)
        html_file = TEMP_GUIDES_DIR / g["slug"] / f"{g['slug']}.html"
        if html_file.is_file():
            try:
                extracted = cached_extract(html_file)
                info["authors"] = [a.name for a in extracted.authors]
                info["abstract"] = extracted.abstract
                info["has_thumbnail"] = _first_guide_image(extracted) is not None
            except Exception:
                logger.warning("Could not enrich guide %s", g["slug"], exc_info=True)
        enriched.append(info)
    return enriched


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/research-guides/")
def research_guides():
    return render_template(
        "research_guides.html", guides=_enrich_guides(list_available_guides())
    )


@app.route("/guides/<slug>/thumbnail")
def guide_thumbnail(slug):
    """Serve the guide's first figure as a card thumbnail. Self-contained
    renders inline figures as data: URIs, which we decode and serve as
    real image bytes so listing pages stay small."""
    html_file = TEMP_GUIDES_DIR / slug / f"{slug}.html"
    if not html_file.is_file():
        abort(404)
    img = _first_guide_image(cached_extract(html_file))
    if img is None:
        abort(404)
    if img.is_local:
        return redirect(url_for("guide_asset", slug=slug, filename=img.src))
    header, _, b64 = img.src.partition(",")
    mimetype = header.removeprefix("data:").split(";", 1)[0]
    try:
        data = base64.b64decode(b64)
    except ValueError:  # binascii.Error subclasses ValueError
        abort(404)
    resp = app.response_class(data, mimetype=mimetype)
    resp.cache_control.max_age = 86400
    return resp


@app.route("/guides/<slug>")
def guide_no_slash(slug):
    # Force trailing slash so the browser resolves relative asset paths
    # (e.g. "mixed-effects-models_files/...") against the guide directory.
    return redirect(url_for("guide_index", slug=slug), code=301)


@app.route("/guides/<slug>/")
def guide_index(slug):
    guide_dir = TEMP_GUIDES_DIR / slug
    html_file = guide_dir / f"{slug}.html"
    if not html_file.is_file():
        abort(404)
    cached = cached_extract(html_file)
    guide = replace(
        cached,
        stylesheets=_filter_quarto_assets(cached.stylesheets),
        scripts=_filter_quarto_assets(cached.scripts),
    )
    consultants = load_consultants()
    return render_template(
        "guide.html",
        guide=guide,
        slug=slug,
        consultant_map=_consultant_map(consultants),
    )


@app.route("/guides/<slug>/<path:filename>")
def guide_asset(slug, filename):
    guide_dir = TEMP_GUIDES_DIR / slug
    if not guide_dir.is_dir():
        abort(404)
    return send_from_directory(guide_dir, filename)


@app.route("/about/")
def about():
    return render_template("about.html")


@app.route("/consultations/")
def consultations():
    return render_template("consultations.html")


@app.route("/workshops/")
def workshops():
    return render_template("workshops.html")


@app.route("/about/team/")
def team():
    consultants = load_consultants()
    current = [c for c in consultants if c.get("status") == "current"]
    former = [c for c in consultants if c.get("status") == "former"]
    return render_template("team.html", current=current, former=former)


@app.route("/consultants/<slug>/")
def consultant_profile(slug):
    consultants = load_consultants()
    consultant = next((c for c in consultants if c["slug"] == slug), None)
    if consultant is None:
        abort(404)

    authored_guides = []
    for guide_slug in consultant.get("guides", []):
        html_file = TEMP_GUIDES_DIR / guide_slug / f"{guide_slug}.html"
        if html_file.is_file():
            try:
                g = cached_extract(html_file)
                authored_guides.append({
                    "slug": guide_slug,
                    "title": g.title,
                    "date": g.date,
                    "abstract": g.abstract,
                    "has_thumbnail": _first_guide_image(g) is not None,
                })
            except Exception:
                pass

    return render_template(
        "consultant.html",
        consultant=consultant,
        guides=authored_guides,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
