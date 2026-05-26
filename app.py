import json
import re
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, send_from_directory

from tools.extractor import extract

app = Flask(__name__)

TEMP_GUIDES_DIR = Path(__file__).parent / "temp"
CONSULTANTS_FILE = Path(__file__).parent / "data" / "consultants.json"

# Assets that must never load inside base.html:
#   • Full Bootstrap distribution — clobbers site nav/footer styles.
#     Hashed pattern covers Quarto >= 1.7 (bootstrap-<hash>.min.css).
#   • polyfill.io — domain was hijacked in 2024; the CDN is dead/malicious.
_STRIP_ASSET_PATTERNS = [
    re.compile(r"/bootstrap(?:-[0-9a-f]+)?\.min\.(css|js)$"),
    re.compile(r"polyfill\.min\.js"),   # matches polyfill.io AND cdnjs.cloudflare.com/polyfill
]


def _filter_quarto_assets(assets):
    return [
        a for a in assets
        if not any(p.search(a.src) for p in _STRIP_ASSET_PATTERNS)
    ]


def load_consultants():
    if not CONSULTANTS_FILE.is_file():
        return []
    with open(CONSULTANTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _consultant_map(consultants):
    """Return a dict keyed by lowercased name for O(1) lookup in templates."""
    return {c["name"].strip().lower(): c for c in consultants}


def list_available_guides():
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
            title = extract(html_file).title or entry.name
        except Exception:
            title = entry.name
        guides.append({"slug": entry.name, "title": title})
    return guides


@app.context_processor
def inject_now():
    return {"now": datetime.utcnow()}


ASSETS_DIR = Path(__file__).parent / "assets"


@app.route("/assets/yale-font/<filename>")
def serve_font(filename):
    return send_from_directory(ASSETS_DIR / "yale-font", filename)


@app.route("/assets/consultant-photos/<filename>")
def serve_consultant_photo(filename):
    return send_from_directory(ASSETS_DIR / "consultant-photos", filename)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/research-guides")
def research_guides():
    return render_template("research_guides.html", guides=list_available_guides())


@app.route("/guides/<slug>")
def guide_no_slash(slug):
    # Force trailing slash so the browser resolves relative asset paths
    # (e.g. "mixed-effects-models_files/...") against the guide directory.
    return redirect(f"/guides/{slug}/", code=301)


@app.route("/guides/<slug>/")
def guide_index(slug):
    guide_dir = TEMP_GUIDES_DIR / slug
    html_file = guide_dir / f"{slug}.html"
    if not html_file.is_file():
        abort(404)
    guide = extract(html_file)
    guide.stylesheets = _filter_quarto_assets(guide.stylesheets)
    guide.scripts = _filter_quarto_assets(guide.scripts)
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


@app.route("/about/team")
def team():
    consultants = load_consultants()
    current = [c for c in consultants if c.get("status") == "current"]
    former = [c for c in consultants if c.get("status") == "former"]
    return render_template("team.html", current=current, former=former)


@app.route("/consultants/<slug>")
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
                g = extract(html_file)
                authored_guides.append({"slug": guide_slug, "title": g.title, "date": g.date})
            except Exception:
                pass

    return render_template(
        "consultant.html",
        consultant=consultant,
        guides=authored_guides,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
