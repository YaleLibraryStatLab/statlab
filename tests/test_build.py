from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import build as build_mod
from tools.build import (
    DEFAULT_EXCLUDE_FILE,
    build,
    load_exclusions,
)

GUIDE_HTML = """<!DOCTYPE html>
<html><head>
<title>{title}</title>
<meta name="generator" content="quarto-1.7.32">
<meta name="dcterms.date" content="2026-01-15">
<meta name="keywords" content="testing, pipelines">
<meta name="author" content="Jane Doe">
<script src="{slug}_files/libs/quarto.js"></script>
<link rel="stylesheet" href="{slug}_files/libs/style.css">
</head>
<body><div id="quarto-content">
<main class="content" id="quarto-document-content">
<h1>{title}</h1><p>Hello.</p>
<img src="images/plot.png">
</main></div></body></html>
"""


def make_guide(source: Path, slug: str, *, title: str | None = None, assets: bool = True) -> Path:
    guide_dir = source / slug
    libs = guide_dir / f"{slug}_files" / "libs"
    guide_dir.mkdir(parents=True)
    (guide_dir / f"{slug}.html").write_text(
        GUIDE_HTML.format(slug=slug, title=title or slug.title()), encoding="utf-8"
    )
    if assets:
        libs.mkdir(parents=True)
        (libs / "quarto.js").write_text("// js")
        (libs / "style.css").write_text("/* css */")
        (guide_dir / "images").mkdir()
        (guide_dir / "images" / "plot.png").write_bytes(b"\x89PNG")
    return guide_dir


@pytest.fixture()
def tree(tmp_path: Path) -> dict[str, Path]:
    source = tmp_path / "research-guides"
    source.mkdir()
    exclude = tmp_path / "guides.exclude"
    exclude.write_text("# none\n")
    # Isolated from data/guide_topic_overrides.json: load_overrides validates
    # override slugs against the manifest, so a real override for a real guide
    # would fail every synthetic tree here.
    overrides = tmp_path / "guide_topic_overrides.json"
    overrides.write_text('{"guides": {}}\n')
    return {
        "source": source,
        "dest": tmp_path / "temp",
        "exclude": exclude,
        "overrides": overrides,
        "manifest": tmp_path / "guides_manifest.json",
    }


def run_build(tree: dict[str, Path], **kwargs) -> int:
    kwargs.setdefault("topic_overrides_path", tree["overrides"])
    return build(
        source=tree["source"],
        dest=tree["dest"],
        exclude_file=tree["exclude"],
        manifest_path=tree["manifest"],
        **kwargs,
    )


def test_full_build_copies_guides_and_writes_manifest(tree):
    make_guide(tree["source"], "anova")
    make_guide(tree["source"], "bootstrap")
    tree["exclude"].write_text("bootstrap  # not ready\n")

    assert run_build(tree) == 0

    assert (tree["dest"] / "anova" / "anova.html").is_file()
    assert (tree["dest"] / "anova" / "anova_files" / "libs" / "quarto.js").is_file()
    assert not (tree["dest"] / "bootstrap").exists()

    manifest = json.loads(tree["manifest"].read_text())
    assert [g["slug"] for g in manifest] == ["anova"]
    entry = manifest[0]
    assert entry["title"] == "Anova"
    assert entry["date"] == "2026-01-15"
    assert entry["authors"] == ["Jane Doe"]
    assert entry["keywords"] == ["testing", "pipelines"]
    assert entry["topics"] == ["inference-model-building"]


def test_unmatched_exclusion_warns_but_builds(tree, capsys):
    make_guide(tree["source"], "anova")
    tree["exclude"].write_text("no-such-guide\n")

    assert run_build(tree) == 0
    err = capsys.readouterr().err
    assert "warning" in err and "no-such-guide" in err
    # The build itself proceeds normally.
    assert (tree["dest"] / "anova" / "anova.html").is_file()


def test_unmatched_exclusion_fails_when_strict(tree, capsys):
    make_guide(tree["source"], "anova")
    tree["exclude"].write_text("anova\nno-such-guide\n")

    assert run_build(tree, strict_exclusions=True) == 1
    assert "no-such-guide" in capsys.readouterr().err
    assert not tree["manifest"].exists()
    assert not tree["dest"].exists()


def test_dry_run_writes_nothing(tree, capsys):
    make_guide(tree["source"], "anova")

    assert run_build(tree, dry_run=True) == 0
    assert not tree["dest"].exists()
    assert not tree["manifest"].exists()
    out = capsys.readouterr().out
    assert "would publish: anova" in out
    assert '"slug": "anova"' in out


def test_parse_failure_skips_guide_without_crashing(tree, capsys):
    make_guide(tree["source"], "anova")
    broken = tree["source"] / "broken"
    broken.mkdir()
    (broken / "broken.html").write_text("<html><body>no main element</body></html>")

    assert run_build(tree) == 0
    assert "skipped broken" in capsys.readouterr().err
    assert not (tree["dest"] / "broken").exists()
    manifest = json.loads(tree["manifest"].read_text())
    assert [g["slug"] for g in manifest] == ["anova"]


def test_missing_assets_reported_but_guide_still_published(tree, capsys):
    make_guide(tree["source"], "anova", assets=False)

    assert run_build(tree) == 0
    err = capsys.readouterr().err
    assert "anova_files/libs/quarto.js" in err
    assert "images/plot.png" in err
    assert (tree["dest"] / "anova" / "anova.html").is_file()


def test_dir_without_slug_html_is_skipped_with_warning(tree, capsys):
    odd = tree["source"] / "diffindiff"
    odd.mkdir()
    (odd / "differenceindifference.html").write_text("<html></html>")

    assert run_build(tree) == 0
    assert "no diffindiff.html" in capsys.readouterr().err


def test_legacy_guides_dir_is_ignored(tree):
    make_guide(tree["source"], "anova")
    legacy = tree["source"] / "guides"
    legacy.mkdir()
    (legacy / "index.html").write_text("<html></html>")

    assert run_build(tree) == 0
    manifest = json.loads(tree["manifest"].read_text())
    assert [g["slug"] for g in manifest] == ["anova"]


def test_clean_removes_excluded_and_vanished_guides(tree):
    make_guide(tree["source"], "anova")
    stale = tree["dest"] / "vanished"
    stale.mkdir(parents=True)
    (stale / "vanished.html").write_text("<html></html>")

    assert run_build(tree, clean=True) == 0
    assert not stale.exists()
    assert (tree["dest"] / "anova" / "anova.html").is_file()


def test_clean_keeps_guides_that_failed_this_run(tree):
    broken = tree["source"] / "broken"
    broken.mkdir()
    (broken / "broken.html").write_text("<html><body>no main</body></html>")
    previous = tree["dest"] / "broken"
    previous.mkdir(parents=True)
    (previous / "broken.html").write_text("<html>old good copy</html>")

    assert run_build(tree, clean=True) == 0
    assert previous.exists()


def test_dest_equal_to_source_is_rejected(tree):
    make_guide(tree["source"], "anova")
    tree["dest"] = tree["source"]
    assert run_build(tree) == 1
    assert (tree["source"] / "anova" / "anova.html").is_file()


def test_cli_dry_run_exits_zero(tree, capsys):
    make_guide(tree["source"], "anova")
    rc = build_mod.main([
        "--source", str(tree["source"]),
        "--dest", str(tree["dest"]),
        "--exclude-file", str(tree["exclude"]),
        "--topic-overrides", str(tree["overrides"]),
        "--dry-run",
    ])
    assert rc == 0
    assert "would publish: anova" in capsys.readouterr().out


def test_invalid_topic_override_fails_before_publishing(tree, tmp_path, capsys):
    make_guide(tree["source"], "anova")
    overrides = tmp_path / "topic-overrides.json"
    overrides.write_text(json.dumps({
        "guides": {"typo-slug": {"include": ["causal-inference"]}}
    }))

    assert run_build(tree, topic_overrides_path=overrides) == 1
    assert "unknown guide slug" in capsys.readouterr().err
    assert not tree["dest"].exists()
    assert not tree["manifest"].exists()


def test_repo_exclusion_file_matches_main_catalog():
    """Every guides.exclude entry must be a real guide on the upstream main branch.

    Selection now comes from main (read via git), so main — not local
    research-guides/ — is the authoritative catalog for the exclusion list.
    """
    from tools.port_guides import (
        DEFAULT_REF,
        DEFAULT_UPSTREAM,
        catalog,
        is_git_repo,
        ref_exists,
    )

    if not is_git_repo(DEFAULT_UPSTREAM) or not ref_exists(DEFAULT_UPSTREAM, DEFAULT_REF):
        pytest.skip("upstream ResearchGuides repo / main ref not present on this machine")
    cat = set(catalog(DEFAULT_UPSTREAM, DEFAULT_REF))
    excluded = load_exclusions(DEFAULT_EXCLUDE_FILE)
    assert sorted(excluded - cat) == []


# ---------------------------------------------------------------------------
# assets/ — the per-guide download set: inventoried into the manifest, and
# dead links to it are reported rather than shipped as 404s.
# ---------------------------------------------------------------------------

DOWNLOAD_HTML = """<!DOCTYPE html>
<html><head><title>{title}</title>
<meta name="dcterms.date" content="2026-01-15">
</head>
<body><div id="quarto-content">
<main class="content" id="quarto-document-content">
<h1>{title}</h1>
<p><a href="{href}" download="d.csv">the data</a></p>
<p><a href="#sec-intro">jump</a>
   <a href="https://example.org/x.csv">remote</a>
   <a href="mailto:statlab@yale.edu">mail</a></p>
</main></div></body></html>
"""


def make_download_guide(source: Path, slug: str, *, href: str, on_disk: str | None) -> Path:
    guide_dir = source / slug
    guide_dir.mkdir(parents=True)
    (guide_dir / f"{slug}.html").write_text(
        DOWNLOAD_HTML.format(title=slug.title(), href=href), encoding="utf-8"
    )
    if on_disk:
        target = guide_dir / on_disk
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("a,b\n1,2\n", encoding="utf-8")
    return guide_dir


def test_inventory_assets_lists_files_relative_to_the_guide(tmp_path):
    guide = tmp_path / "anova"
    (guide / "assets" / "data").mkdir(parents=True)
    (guide / "assets" / "scripts").mkdir(parents=True)
    (guide / "assets" / "data" / "b.csv").write_text("x")
    (guide / "assets" / "data" / "a.csv").write_text("x")
    (guide / "assets" / "scripts" / "sim.R").write_text("x")
    (guide / "assets" / ".DS_Store").write_text("x")
    (guide / "anova.html").write_text("<html></html>")   # outside assets/

    assert build_mod.inventory_assets(guide) == [
        "assets/data/a.csv",
        "assets/data/b.csv",
        "assets/scripts/sim.R",
    ]


def test_inventory_assets_empty_without_an_assets_dir(tmp_path):
    guide = tmp_path / "anova"
    guide.mkdir()
    assert build_mod.inventory_assets(guide) == []


def test_assets_are_recorded_in_the_manifest(tree):
    make_download_guide(
        tree["source"], "anova",
        href="assets/data/d.csv", on_disk="assets/data/d.csv",
    )

    assert run_build(tree) == 0
    manifest = json.loads(tree["manifest"].read_text())
    assert manifest[0]["assets"] == ["assets/data/d.csv"]
    # and the file really crossed into the publish dir
    assert (tree["dest"] / "anova" / "assets" / "data" / "d.csv").is_file()


def test_guide_without_assets_gets_an_empty_list(tree):
    make_guide(tree["source"], "anova")
    assert run_build(tree) == 0
    assert json.loads(tree["manifest"].read_text())[0]["assets"] == []


def test_dead_download_link_warns_but_still_publishes(tree, capsys):
    """The live case: a guide rendered before its data moved into assets/."""
    make_download_guide(
        tree["source"], "anova",
        href="anova_files/data/d.csv", on_disk="assets/data/d.csv",
    )

    assert run_build(tree) == 0
    err = capsys.readouterr().err
    assert "anova_files/data/d.csv" in err
    assert "missing file" in err
    assert (tree["dest"] / "anova" / "anova.html").is_file()   # published anyway


def test_offsite_and_in_page_links_are_not_flagged(tree, capsys):
    make_download_guide(
        tree["source"], "anova",
        href="assets/data/d.csv", on_disk="assets/data/d.csv",
    )

    assert run_build(tree) == 0
    err = capsys.readouterr().err
    assert "missing file" not in err
    assert "example.org" not in err and "mailto" not in err


def test_partition_splits_absent_files_from_unresolved_links():
    files, unresolved = build_mod.partition_missing([
        "assets/data/nunn.csv",
        "@sec-methods",
        "images/plot.png",
        "TODO-link-ols-guide",
        "LINK TO OTHER GUIDE",
    ])
    assert files == ["assets/data/nunn.csv", "images/plot.png"]
    assert unresolved == ["@sec-methods", "TODO-link-ols-guide", "LINK TO OTHER GUIDE"]


def test_unresolved_xref_reported_separately_from_missing_data(tree, capsys):
    """A guide's half-written cross-references must not bury a missing dataset."""
    make_download_guide(
        tree["source"], "anova",
        href="assets/data/gone.csv", on_disk=None,
    )
    guide_html = tree["source"] / "anova" / "anova.html"
    guide_html.write_text(
        guide_html.read_text().replace(
            '<a href="#sec-intro">jump</a>', '<a href="@sec-methods">jump</a>'
        ),
        encoding="utf-8",
    )

    assert run_build(tree) == 0
    err = capsys.readouterr().err
    missing_block, unresolved_block = err.split("unresolved link(s)")
    assert "assets/data/gone.csv" in missing_block
    assert "@sec-methods" in unresolved_block
    assert "@sec-methods" not in missing_block
