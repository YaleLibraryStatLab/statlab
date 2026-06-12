from __future__ import annotations

from pathlib import Path

import pytest

from tools import build as build_mod
from tools import port_guides as pg

GUIDE_HTML = """<!DOCTYPE html>
<html><head><title>{title}</title></head>
<body><div id="quarto-content">
<main class="content" id="quarto-document-content"><h1>{title}</h1></main>
</div></body></html>
"""


def make_upstream_guide(
    upstream: Path, slug: str, *, html_name: str | None = None, extra_html: str | None = None
) -> Path:
    guide_dir = upstream / slug
    guide_dir.mkdir(parents=True)
    (guide_dir / f"{slug}.qmd").write_text("---\ntitle: x\n---\n```{r}\n1\n```\n")
    (guide_dir / (html_name or f"{slug}.html")).write_text(
        GUIDE_HTML.format(title=slug.title()), encoding="utf-8"
    )
    if extra_html:
        (guide_dir / extra_html).write_text("<html></html>")
    files = guide_dir / f"{slug}_files" / "libs"
    files.mkdir(parents=True)
    (files / "quarto.js").write_text("// js")
    return guide_dir


@pytest.fixture()
def env(tmp_path: Path, monkeypatch):
    """Isolated upstream + dest trees; build_mod.build stubbed out."""
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    dest = tmp_path / "dest-guides"
    dest.mkdir()
    exclude = tmp_path / "guides.exclude"
    exclude.write_text("# none\n")

    monkeypatch.setattr(pg, "DEST_GUIDES", dest)
    monkeypatch.setattr(build_mod, "DEFAULT_EXCLUDE_FILE", exclude)

    calls = []
    monkeypatch.setattr(build_mod, "build", lambda *a, **k: calls.append(1) or 0)
    return {"upstream": upstream, "dest": dest, "exclude": exclude, "build_calls": calls}


def test_no_render_ports_guide_and_strips_sources(env):
    make_upstream_guide(env["upstream"], "anova")

    assert pg.port(env["upstream"], no_render=True) == 0

    ported = env["dest"] / "anova"
    assert (ported / "anova.html").is_file()
    assert (ported / "anova_files" / "libs" / "quarto.js").is_file()
    assert not (ported / "anova.qmd").exists()
    assert env["build_calls"], "tools/build.py was not invoked"


def test_main_html_is_normalized_to_slug(env):
    make_upstream_guide(env["upstream"], "diffindiff", html_name="differenceindifference.html")

    assert pg.port(env["upstream"], no_render=True) == 0

    ported = env["dest"] / "diffindiff"
    assert (ported / "diffindiff.html").is_file()
    assert (ported / "differenceindifference.html").is_file()  # original kept


def test_ambiguous_main_html_fails_that_guide(env, capsys):
    make_upstream_guide(env["upstream"], "odd", html_name="one.html", extra_html="two.html")
    make_upstream_guide(env["upstream"], "anova")

    assert pg.port(env["upstream"], no_render=True) == 1

    out = capsys.readouterr().out
    assert "ambiguous main HTML" in out
    assert not (env["dest"] / "odd").exists()  # no half-ported guide left behind
    assert (env["dest"] / "anova" / "anova.html").is_file()  # run continued


def test_exclusion_typo_fails_before_any_work(env, capsys):
    make_upstream_guide(env["upstream"], "anova")
    env["exclude"].write_text("anvoa\n")

    assert pg.port(env["upstream"], no_render=True) == 1
    assert "anvoa" in capsys.readouterr().err
    assert not any(env["dest"].iterdir())
    assert not env["build_calls"]


def test_only_with_excluded_slug_is_an_error(env, capsys):
    make_upstream_guide(env["upstream"], "anova")
    env["exclude"].write_text("anova\n")

    assert pg.port(env["upstream"], only=["anova"], no_render=True) == 1
    assert "excluded by guides.exclude" in capsys.readouterr().err


def test_excluded_guides_are_not_ported(env):
    make_upstream_guide(env["upstream"], "anova")
    make_upstream_guide(env["upstream"], "bootstrap")
    env["exclude"].write_text("bootstrap\n")

    assert pg.port(env["upstream"], no_render=True) == 0
    assert (env["dest"] / "anova").is_dir()
    assert not (env["dest"] / "bootstrap").exists()


def test_dry_run_writes_nothing(env, capsys):
    make_upstream_guide(env["upstream"], "anova")

    assert pg.port(env["upstream"], no_render=True, dry_run=True) == 0
    assert not any(env["dest"].iterdir())
    assert not env["build_calls"]
    assert "would copy: anova" in capsys.readouterr().out


def test_render_failure_is_summarized_not_fatal(env, monkeypatch, capsys):
    make_upstream_guide(env["upstream"], "anova")
    make_upstream_guide(env["upstream"], "bootstrap")

    def fake_render(guide_dir: Path):
        if guide_dir.name == "anova":
            return False, "quarto render anova.qmd failed:\nsome R error"
        return True, "rendered bootstrap.qmd"

    monkeypatch.setattr(pg, "render_guide", fake_render)
    monkeypatch.setattr(pg, "preflight", lambda **k: True)

    assert pg.port(env["upstream"]) == 1

    out = capsys.readouterr().out
    assert "FAILED (render)" in out
    assert not (env["dest"] / "anova").exists()
    assert (env["dest"] / "bootstrap" / "bootstrap.html").is_file()
    assert env["build_calls"], "build should still run for the guides that succeeded"
