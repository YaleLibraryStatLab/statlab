from __future__ import annotations

from pathlib import Path

import pytest

from tools.extractor import extract

GUIDE_HTML = """<!DOCTYPE html>
<html><head>
<title>Standard Errors</title>
<meta name="dcterms.date" content="2026-01-15">
</head>
<body><div id="quarto-content">
<main class="content" id="quarto-document-content">
<h1 id="sec-intro">Standard Errors</h1>
<p><a href="assets/data/nunn.csv" download="nunn.csv">the Nunn data</a></p>
<p><a href="assets/scripts/simulate.R">simulation code</a></p>
<p><a href="#sec-intro">back to the top</a></p>
<p><a href="https://example.org/remote.csv">an off-site copy</a></p>
<p><a href="mailto:statlab@yale.edu">email us</a></p>
<p><a href="/assets/yale-logo/logo.svg">site chrome</a></p>
<p><a href="assets/data/with%20space.csv">quoted name</a></p>
</main></div></body></html>
"""


@pytest.fixture()
def guide(tmp_path: Path):
    html = tmp_path / "standard-errors.html"
    html.write_text(GUIDE_HTML, encoding="utf-8")
    return extract(html)


def test_links_capture_relative_targets(guide):
    local = [a.src for a in guide.links if a.is_local]
    assert "assets/data/nunn.csv" in local
    assert "assets/scripts/simulate.R" in local


def test_links_skip_in_page_anchors(guide):
    assert not any(a.src.startswith("#") for a in guide.links)


def test_links_mark_offsite_targets_non_local(guide):
    offsite = {a.src for a in guide.links if not a.is_local}
    assert offsite == {"https://example.org/remote.csv", "mailto:statlab@yale.edu"}


def test_links_preserve_the_download_attribute(guide):
    nunn = next(a for a in guide.links if a.src == "assets/data/nunn.csv")
    assert nunn.attrs["download"] == "nunn.csv"
    sim = next(a for a in guide.links if a.src == "assets/scripts/simulate.R")
    assert sim.attrs == {}


def test_links_keep_server_absolute_paths_for_the_caller_to_skip(guide):
    """build.find_missing_assets drops these; the extractor still reports them."""
    assert any(a.src == "/assets/yale-logo/logo.svg" for a in guide.links)


def test_links_are_all_kind_link(guide):
    assert {a.kind for a in guide.links} == {"link"}
