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
    return {
        "source": source,
        "dest": tmp_path / "temp",
        "exclude": exclude,
        "manifest": tmp_path / "guides_manifest.json",
    }


def run_build(tree: dict[str, Path], **kwargs) -> int:
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
