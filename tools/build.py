"""
build.py  –  future orchestration for the full guide pipeline.

Planned responsibilities
------------------------
1. Walk research-guides/ and find every compiled .html file
2. Run extractor.extract() on each
3. Rewrite local asset paths to Flask static URLs
4. Write a manifest.json consumed by the Flask route registry
5. Copy (or symlink) guide asset directories into Flask's static tree

Not yet implemented — scaffold only.
"""

from __future__ import annotations

import json
from pathlib import Path

# Project root is one directory above this file
ROOT = Path(__file__).parent.parent
GUIDES_DIR = ROOT / "research-guides"
STATIC_GUIDES = ROOT / "app" / "static" / "guides"   # future static target
MANIFEST_PATH = ROOT / "app" / "guides_manifest.json"


def discover_guides(guides_dir: Path = GUIDES_DIR) -> list[Path]:
    """Return paths to all top-level Quarto HTML files under guides_dir."""
    html_files = []
    for html in guides_dir.rglob("*.html"):
        # Skip the listing index and archive copies
        if html.name == "index.html":
            continue
        if "archive" in html.parts:
            continue
        html_files.append(html)
    return sorted(html_files)


def build(dry_run: bool = False) -> None:
    from extractor import extract, rewrite_asset_paths  # noqa: F401 – future use

    guides = discover_guides()
    manifest = []

    for html_path in guides:
        guide = extract(html_path)
        slug = html_path.parent.name

        # TODO: copy html_path.parent / "*_files" tree to STATIC_GUIDES / slug
        # TODO: rewrite_asset_paths(guide.scripts + guide.stylesheets + guide.images,
        #           url_prefix=f"/static/guides/{slug}",
        #           source_dir=html_path.parent)

        manifest.append({
            "slug": slug,
            "title": guide.title,
            "date": guide.date,
            "authors": [a.name for a in guide.authors],
            "keywords": guide.keywords,
            "html_path": str(html_path.relative_to(ROOT)),
        })
        print(f"  processed: {slug}")

    if not dry_run:
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
        print(f"\nManifest written to {MANIFEST_PATH}")
    else:
        print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    build(dry_run=dry)
