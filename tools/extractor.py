r"""
extractor.py

Pull structured data out of a Quarto-compiled HTML file for ingestion into
the Flask app.  The three things this module cares about are:

  1. main_content  – the cleaned <main> body as an HTML string
  2. metadata      – title, authors, date, abstract, keywords, quarto version
  3. assets        – every local and CDN asset referenced in <head>

Quarto edge-cases handled
--------------------------
* Multiple <meta name="author"> tags (multi-author guides)
* Keywords meta tag wraps the content in a <p> tag — we strip it
* quarto-code-tools dropdown (Show/Hide all code, View Source) is removed
  because View Source tries to fetch the .qmd file, which won't exist in Flask
* code-copy buttons (.code-copy-button) are preserved — they need clipboard.js
* Mermaid diagram blocks (pre.mermaid) are kept intact; mermaid.js must be
  loaded separately in the Flask template
* Bootstrap CSS filenames include a content-hash in newer Quarto builds
  (e.g. bootstrap-81267100e462c21b3d6c0d5bf76a3417.min.css) — captured as-is
* Local asset paths are expressed relative to the HTML file; callers can
  rewrite them with rewrite_asset_paths()
* quarto-xref links (#fig-*, #sec-*, #tbl-*) are internal anchors — they
  work as long as the content is embedded in full
* Inline math uses <span class="math inline|display">\(...\)</span> — MathJax
  or KaTeX must be loaded in the Flask template
* Callout boxes (callout-note, callout-important, callout-caution, etc.) are
  kept verbatim; they rely only on Bootstrap + a small slice of Quarto CSS
* Panel tabsets (.panel-tabset) need Bootstrap JS + quarto.js to function
* Collapsible code blocks (details.code-fold) are native HTML — no JS needed
* Emoji spans (<span class="emoji" data-emoji="...">) render the emoji as
  text content already; no extra handling required
* Citation spans (.citation) and the bibliography section (.csl-bib-body) are
  kept; they are pure HTML with no special runtime dependencies
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Author:
    name: str
    url: Optional[str] = None
    affiliation: Optional[str] = None


@dataclass
class Asset:
    kind: str          # "script" | "stylesheet" | "image"
    src: str           # original src/href value from the HTML
    is_local: bool     # False  → CDN / absolute URL
    attrs: dict = field(default_factory=dict)   # any extra HTML attrs


@dataclass
class ExtractedGuide:
    # --- metadata ---
    title: str
    authors: list[Author]
    date: Optional[str]          # raw ISO string from dcterms.date
    abstract: Optional[str]      # inner HTML of the abstract block
    keywords: list[str]
    quarto_version: Optional[str]

    # --- content ---
    main_html: str               # cleaned inner HTML of <main>

    # --- assets ---
    scripts: list[Asset]
    stylesheets: list[Asset]
    images: list[Asset]          # images referenced in <head> (rare) + <main>

    # Defaulted fields must come last in a dataclass.
    toc_html: Optional[str] = None   # inner HTML of nav#TOC when toc: true


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_local(url: str) -> bool:
    parsed = urlparse(url)
    return not parsed.scheme and not parsed.netloc


def _strip_html_tags(raw: str) -> str:
    return BeautifulSoup(raw, "html.parser").get_text(separator=" ").strip()


def _clean_keywords(raw_html: str) -> list[str]:
    """
    Quarto wraps keywords in <p><code>...</code></p> markup.
    Strip all tags, then split on commas.
    """
    text = _strip_html_tags(raw_html)
    return [k.strip() for k in text.split(",") if k.strip()]


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

def _extract_metadata(soup: BeautifulSoup) -> dict:
    meta: dict = {
        "title": None,
        "authors": [],
        "date": None,
        "abstract": None,
        "keywords": [],
        "quarto_version": None,
    }

    # title
    title_tag = soup.find("title")
    if title_tag:
        meta["title"] = title_tag.get_text(strip=True)

    # quarto version
    gen = soup.find("meta", attrs={"name": "generator"})
    if gen and gen.get("content", "").startswith("quarto"):
        meta["quarto_version"] = gen["content"].replace("quarto-", "").strip()

    # date
    date_meta = soup.find("meta", attrs={"name": "dcterms.date"})
    if date_meta:
        meta["date"] = date_meta.get("content")

    # keywords
    kw_meta = soup.find("meta", attrs={"name": "keywords"})
    if kw_meta:
        meta["keywords"] = _clean_keywords(kw_meta.get("content", ""))

    # authors + affiliations — pull from the rendered title block, not just
    # <meta>, because the title block carries URLs and affiliation text that
    # the meta tags don't expose.
    author_block = soup.find("div", class_="quarto-title-meta-author")
    if author_block:
        name_divs = author_block.find_all("div", class_="quarto-title-meta-contents")
        # Quarto interleaves author name divs and affiliation divs:
        # [name, affil, name, affil, ...]
        names, affils = [], []
        for div in name_divs:
            if div.find("p", class_="author"):
                a_tag = div.find("a")
                p_tag = div.find("p", class_="author")
                url = a_tag["href"] if a_tag and a_tag.get("href") else None
                name = p_tag.get_text(strip=True) if p_tag else div.get_text(strip=True)
                names.append((name, url))
            elif div.find("p", class_="affiliation"):
                affils.append(div.get_text(strip=True))

        for i, (name, url) in enumerate(names):
            affil = affils[i] if i < len(affils) else None
            meta["authors"].append(Author(name=name, url=url, affiliation=affil))

    # Fall back to <meta name="author"> if the title block parse yielded nothing
    if not meta["authors"]:
        for m in soup.find_all("meta", attrs={"name": "author"}):
            meta["authors"].append(Author(name=m["content"]))

    # abstract — rendered as div.abstract > div.block-title + <p>
    abstract_div = soup.find("div", class_="abstract")
    if abstract_div:
        # Remove the "Abstract" label before capturing inner HTML
        label = abstract_div.find("div", class_="block-title")
        if label:
            label.decompose()
        meta["abstract"] = abstract_div.decode_contents().strip()

    return meta


# ---------------------------------------------------------------------------
# Asset extraction
# ---------------------------------------------------------------------------

def _extract_assets(soup: BeautifulSoup) -> tuple[list[Asset], list[Asset], list[Asset]]:
    scripts: list[Asset] = []
    stylesheets: list[Asset] = []
    images: list[Asset] = []

    head = soup.find("head")
    if not head:
        return scripts, stylesheets, images

    for tag in head.find_all("script"):
        src = tag.get("src")
        if not src:
            continue
        extra = {k: v for k, v in tag.attrs.items() if k not in ("src",)}
        scripts.append(Asset(kind="script", src=src, is_local=_is_local(src), attrs=extra))

    for tag in head.find_all("link", rel=lambda r: r and "stylesheet" in r):
        href = tag.get("href", "")
        extra = {k: v for k, v in tag.attrs.items() if k not in ("href", "rel")}
        stylesheets.append(Asset(kind="stylesheet", src=href, is_local=_is_local(href), attrs=extra))

    return scripts, stylesheets, images


# ---------------------------------------------------------------------------
# Main-content extraction
# ---------------------------------------------------------------------------

_QUARTO_CHROME_SELECTORS = [
    # "Code" dropdown (show/hide all code, view source) — not functional in Flask
    {"class": "code-tools-button"},
    # quarto-html JS injects a "Copy to Clipboard" tooltip — button is kept but
    # the dropdown menu wrapper we strip above is enough
]


def _remove_quarto_chrome(main: Tag) -> None:
    """Strip interactive Quarto UI elements that don't work in a Flask embed."""
    for selector in _QUARTO_CHROME_SELECTORS:
        for el in main.find_all(True, attrs=selector):
            el.decompose()

    # A body-located TOC (toc-location: body) would duplicate the one the
    # template renders from .toc_html; it is captured separately in extract().
    for nav in main.find_all("nav", id="TOC"):
        nav.decompose()

    # The title block's h1 is wrapped in a div.quarto-title-block alongside
    # the now-removed dropdown button; unwrap it so the h1 stands alone.
    for wrapper in main.find_all("div", class_="quarto-title-block"):
        h1 = wrapper.find("h1")
        if h1:
            wrapper.replace_with(h1)


def _ensure_heading_ids(main: Tag) -> None:
    """Give rendered headings stable, unique deep-link targets.

    Quarto commonly puts the anchor on a surrounding ``section`` while the
    heading itself has only ``data-anchor-id``. Search results need an ID on
    the heading to link to the exact answer. Existing IDs and section anchors
    are left untouched so TOC and cross-reference links keep working.
    """
    used = {tag["id"] for tag in main.find_all(id=True)}
    for heading in main.find_all(re.compile(r"^h[1-6]$")):
        if heading.get("id"):
            continue
        section = heading.find_parent("section", id=True)
        source = (
            heading.get("data-anchor-id")
            or (section.get("id") if section else None)
            or heading.get_text(" ", strip=True)
            or "section"
        )
        base = re.sub(r"[^a-z0-9]+", "-", source.casefold()).strip("-") or "section"
        candidate = base if base not in used else f"{base}-heading"
        suffix = 2
        while candidate in used:
            candidate = f"{base}-heading-{suffix}"
            suffix += 1
        heading["id"] = candidate
        used.add(candidate)


def _extract_main(soup: BeautifulSoup) -> str:
    main = soup.find("main", id="quarto-document-content")
    if main is None:
        main = soup.find("main")
    if main is None:
        raise ValueError("Could not find <main> content in this Quarto HTML file.")

    _remove_quarto_chrome(main)
    _ensure_heading_ids(main)
    return main.decode_contents()


def _extract_images_from_main(main_html: str) -> list[Asset]:
    """Collect <img> srcs from the extracted content."""
    soup = BeautifulSoup(main_html, "html.parser")
    images = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src:
            images.append(Asset(kind="image", src=src, is_local=_is_local(src)))
    return images


# ---------------------------------------------------------------------------
# Asset path rewriting
# ---------------------------------------------------------------------------

def rewrite_asset_paths(
    assets: list[Asset],
    *,
    url_prefix: str,
    source_dir: Path,
) -> list[Asset]:
    """
    Rewrite local asset src values so they point to a Flask static-file URL.

    Parameters
    ----------
    assets:
        List of Asset objects returned by extract().
    url_prefix:
        The Flask URL prefix where the guide's assets will be served, e.g.
        "/static/guides/mixed-effects-models".
    source_dir:
        Absolute path to the directory containing the original HTML file.
        Used to resolve relative paths before rewriting.

    Returns a new list; the originals are not mutated.
    """
    rewritten = []
    for asset in assets:
        if not asset.is_local:
            rewritten.append(asset)
            continue
        # Normalise: strip leading ./
        clean = asset.src.lstrip("./")
        new_src = f"{url_prefix.rstrip('/')}/{clean}"
        rewritten.append(Asset(
            kind=asset.kind,
            src=new_src,
            is_local=False,   # now a server-absolute URL
            attrs=asset.attrs,
        ))
    return rewritten


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract(html_path: str | Path) -> ExtractedGuide:
    """
    Parse a Quarto-compiled HTML file and return an ExtractedGuide.

    Parameters
    ----------
    html_path:
        Path to the .html file produced by `quarto render`.

    Returns
    -------
    ExtractedGuide
        Structured data ready for use in a Flask template or further processing.
    """
    html_path = Path(html_path)
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    raw = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")

    meta = _extract_metadata(soup)
    scripts, stylesheets, _ = _extract_assets(soup)

    # Capture the TOC (rendered when the guide sets toc: true) before main
    # extraction — Quarto places it in a sidebar outside <main>, or inside
    # it with toc-location: body, where _remove_quarto_chrome drops it.
    toc = soup.find("nav", id="TOC")
    toc_html = toc.decode_contents().strip() if toc else None

    main_html = _extract_main(soup)
    images = _extract_images_from_main(main_html)

    return ExtractedGuide(
        title=meta["title"] or "",
        authors=meta["authors"],
        date=meta["date"],
        abstract=meta["abstract"],
        keywords=meta["keywords"],
        quarto_version=meta["quarto_version"],
        main_html=main_html,
        scripts=scripts,
        stylesheets=stylesheets,
        images=images,
        toc_html=toc_html,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extractor.py <path-to-quarto.html> [--json]")
        sys.exit(1)

    path = sys.argv[1]
    as_json = "--json" in sys.argv

    guide = extract(path)

    if as_json:
        out = {
            "title": guide.title,
            "quarto_version": guide.quarto_version,
            "date": guide.date,
            "authors": [
                {"name": a.name, "url": a.url, "affiliation": a.affiliation}
                for a in guide.authors
            ],
            "keywords": guide.keywords,
            "abstract": guide.abstract,
            "scripts": [{"src": s.src, "is_local": s.is_local} for s in guide.scripts],
            "stylesheets": [{"src": s.src, "is_local": s.is_local} for s in guide.stylesheets],
            "images": [{"src": i.src, "is_local": i.is_local} for i in guide.images],
            "main_html_chars": len(guide.main_html),
        }
        print(json.dumps(out, indent=2))
    else:
        print(f"Title         : {guide.title}")
        print(f"Quarto version: {guide.quarto_version}")
        print(f"Date          : {guide.date}")
        print(f"Authors       : {[a.name for a in guide.authors]}")
        print(f"Keywords      : {guide.keywords}")
        print(f"Abstract      : {(guide.abstract or '')[:120]}...")
        print(f"Scripts       : {len(guide.scripts)}")
        print(f"Stylesheets   : {len(guide.stylesheets)}")
        print(f"Images        : {len(guide.images)}")
        print(f"Main HTML     : {len(guide.main_html):,} chars")
