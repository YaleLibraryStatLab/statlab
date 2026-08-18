import base64
import json
import logging
import re
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, send_from_directory, url_for

import markdown

from tools.build import inventory_assets
from tools.extractor import extract
from tools.guide_topics import TOPICS, TOPIC_LABELS

app = Flask(__name__)
logger = logging.getLogger(__name__)

TEMP_GUIDES_DIR = Path(__file__).parent / "temp"
CONSULTANTS_FILE = Path(__file__).parent / "data" / "consultants.json"
GUIDES_MANIFEST_FILE = Path(__file__).parent / "guides_manifest.json"
# Authored as Markdown so the FAQ can be edited without touching a template;
# rendered into the consultations page at build time. See load_faqs().
FAQS_FILE = Path(__file__).parent / "assets" / "statlab-faqs.md"

# One Microsoft Form serves both "feedback on an existing resource" and
# "request a resource we don't have". Defined once here and injected into every
# template (see inject_globals) so the three entry points can't drift apart.
FEEDBACK_FORM_URL = (
    "https://forms.cloud.microsoft/Pages/ResponsePage.aspx"
    "?id=u76M3Tkh-E20EU4-h6vrXKPaMvtoJdpPpwgdkcrKi_tUOTFPWTUzRzM2UTEzNDlKRU1CUkZKWDY2US4u"
)
PAGEFIND_DIR = Path(__file__).parent / "docs" / "pagefind"

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


# Each FAQ entry starts at a level-3 heading; everything up to the next one is
# that question's answer.
_FAQ_HEADING_RE = re.compile(r"^###\s+(.*?)\s*$", re.MULTILINE)

# (path, mtime) -> parsed FAQ list, so editing the .md is picked up on reload
# without re-parsing on every request.
_faq_cache: dict[Path, tuple[float, list]] = {}


def _faq_anchor(question: str) -> str:
    """Stable URL fragment for a question, e.g. 'faq-does-a-consultation-cost'."""
    slug = re.sub(r"[^a-z0-9]+", "-", question.lower()).strip("-")
    return f"faq-{slug}" if slug else "faq"


def parse_faqs(text: str) -> list[dict]:
    """Split FAQ Markdown into {question, answer_html, anchor} entries.

    Text before the first '###' is ignored, so the file can carry a comment or
    title without it becoming a question.
    """
    matches = list(_FAQ_HEADING_RE.finditer(text))
    faqs = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        question = match.group(1).strip()
        body = text[match.end():end].strip()
        if not question:
            continue
        faqs.append({
            "question": question,
            "answer_html": markdown.markdown(body) if body else "",
            "anchor": _faq_anchor(question),
        })
    return faqs


def load_faqs():
    """Parsed FAQ entries, or [] when the source file is absent or unreadable."""
    if not FAQS_FILE.is_file():
        logger.warning("%s not found; the consultations FAQ will be empty", FAQS_FILE.name)
        return []
    try:
        mtime = FAQS_FILE.stat().st_mtime
        cached = _faq_cache.get(FAQS_FILE)
        if cached is not None and cached[0] == mtime:
            return cached[1]
        faqs = parse_faqs(FAQS_FILE.read_text(encoding="utf-8"))
    except OSError as exc:
        logger.warning("Could not read %s: %s", FAQS_FILE.name, exc)
        return []
    _faq_cache[FAQS_FILE] = (mtime, faqs)
    return faqs


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
        {
            "slug": g["slug"],
            "title": g["title"],
            "date": g.get("date"),
            "topics": g.get("topics", []),
        }
        for g in manifest
    ]


# assets/images/ holds inline figures already rendered in the body, so it is
# not offered as a download. Anything else under assets/ is reader-facing.
_ASSET_GROUPS_SKIPPED = {"images"}
_ASSET_GROUP_LABELS = {"data": "Data", "scripts": "Scripts", "src": "Scripts"}


def guide_downloads(slug):
    """Downloadable files for a guide, grouped by their assets/ subdirectory.

    Reads what the build recorded in the manifest so the page and the frozen
    site agree; falls back to a live scan when the manifest is missing, which
    matches the fallback in list_available_guides().
    """
    manifest = load_guides_manifest()
    if manifest is None:
        paths = inventory_assets(TEMP_GUIDES_DIR / slug)
    else:
        entry = next((g for g in manifest if g["slug"] == slug), None)
        paths = entry.get("assets", []) if entry else []

    groups = {}
    for path in paths:
        parts = path.split("/")
        # parts[0] is always the assets dir; a bare assets/<file> has no group.
        group = parts[1] if len(parts) > 2 else ""
        if group in _ASSET_GROUPS_SKIPPED:
            continue
        label = _ASSET_GROUP_LABELS.get(group, group.replace("-", " ").title() or "Files")
        groups.setdefault(label, []).append({"path": path, "name": parts[-1]})

    return [{"label": label, "files": files} for label, files in sorted(groups.items())]


@app.context_processor
def inject_now():
    return {"now": datetime.utcnow(), "feedback_form_url": FEEDBACK_FORM_URL}


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


@app.route("/assets/eb-garamond/<filename>")
def serve_eb_garamond(filename):
    # EB Garamond (OFL, free) — the public serif webfont; see base.html.
    return send_from_directory(ASSETS_DIR / "eb-garamond", filename)


@app.route("/assets/yale-logo/<filename>")
def serve_logo(filename):
    return send_from_directory(ASSETS_DIR / "yale-logo", filename)


@app.route("/assets/consultant-photos/<filename>")
def serve_consultant_photo(filename):
    return send_from_directory(ASSETS_DIR / "consultant-photos", filename)


@app.route("/assets/statlab-photos/<path:filename>")
def serve_statlab_photo(filename):
    return send_from_directory(ASSETS_DIR / "statlab-photos", filename)


@app.route("/pagefind/<path:filename>")
def serve_pagefind(filename):
    """Serve the generated static-search bundle in local Flask previews.

    Production serves the same files directly from GitHub Pages. ``make dev``
    runs the freeze first so this directory is fresh before Flask starts.
    """
    return send_from_directory(PAGEFIND_DIR, filename)


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
    guides = _enrich_guides(list_available_guides())
    used_topics = {topic_id for guide in guides for topic_id in guide.get("topics", [])}
    return render_template(
        "research_guides.html",
        guides=guides,
        topic_options=[topic for topic in TOPICS if topic.id in used_topics],
        topic_labels=TOPIC_LABELS,
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
        downloads=guide_downloads(slug),
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
    return render_template("consultations.html", faqs=load_faqs())


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
