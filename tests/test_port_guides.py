from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools import build as build_mod
from tools import consult as consult_mod
from tools import port_guides as pg

GUIDE_HTML = """<!DOCTYPE html>
<html><head><title>{title}</title></head>
<body><div id="quarto-content">
<main class="content" id="quarto-document-content"><h1>{title}</h1></main>
</div></body></html>
"""


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def init_upstream(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-q")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "user.name", "Test")
    git(path, "checkout", "-q", "-b", "main")
    return path


def write_guide(repo: Path, slug: str, *, html_name: str | None = None, extra_html: str | None = None) -> None:
    guide = repo / pg.UPSTREAM_SUBDIR / slug
    libs = guide / f"{slug}_files" / "libs"
    libs.mkdir(parents=True)
    (guide / f"{slug}.qmd").write_text("---\ntitle: x\n---\n", encoding="utf-8")
    (guide / (html_name or f"{slug}.html")).write_text(
        GUIDE_HTML.format(title=slug.title()), encoding="utf-8"
    )
    if extra_html:
        (guide / extra_html).write_text("<html></html>", encoding="utf-8")
    (libs / "quarto.js").write_text("// js", encoding="utf-8")


def commit_guides(repo: Path, *slugs: str, branch: str = "main", **kw) -> None:
    if branch != "main":
        git(repo, "checkout", "-q", "-b", branch)
    for slug in slugs:
        write_guide(repo, slug, **kw)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"add {', '.join(slugs)} on {branch}")
    if branch != "main":
        git(repo, "checkout", "-q", "main")


@pytest.fixture()
def env(tmp_path: Path, monkeypatch):
    upstream = init_upstream(tmp_path / "upstream")
    dest = tmp_path / "dest-guides"
    dest.mkdir()
    exclude = tmp_path / "guides.exclude"
    exclude.write_text("# none\n")

    monkeypatch.setattr(pg, "DEST_GUIDES", dest)
    monkeypatch.setattr(build_mod, "DEFAULT_EXCLUDE_FILE", exclude)

    calls = []
    monkeypatch.setattr(build_mod, "build", lambda *a, **k: calls.append(k) or 0)

    # Stub the recount so tests never read/rewrite the real data/consultants.json.
    consult_calls = []
    monkeypatch.setattr(consult_mod, "sync", lambda *a, **k: consult_calls.append((a, k)) or 0)
    return {
        "upstream": upstream, "dest": dest, "exclude": exclude,
        "build_calls": calls, "consult_calls": consult_calls,
    }


def write_assets(repo: Path, slug: str) -> None:
    """Give a guide an assets/ tree whose names collide with the copy filters."""
    assets = repo / pg.UPSTREAM_SUBDIR / slug / "assets"
    (assets / "src").mkdir(parents=True)
    (assets / "scripts").mkdir(parents=True)
    (assets / "data").mkdir(parents=True)
    (assets / "src" / "generate_data.R").write_text("# R", encoding="utf-8")
    (assets / "scripts" / "refresh.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (assets / "data" / "nunn.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (assets / "notes.qmd").write_text("---\ntitle: x\n---\n", encoding="utf-8")


def make_orphan(dest: Path, slug: str) -> Path:
    d = dest / slug
    d.mkdir(parents=True)
    (d / f"{slug}.html").write_text("<html>old</html>")
    return d


def test_mirrors_main_guides_and_strips_sources(env):
    commit_guides(env["upstream"], "anova", "bootstrap")

    assert pg.port(env["upstream"]) == 0

    for slug in ("anova", "bootstrap"):
        ported = env["dest"] / slug
        assert (ported / f"{slug}.html").is_file()
        assert (ported / f"{slug}_files" / "libs" / "quarto.js").is_file()
        assert not (ported / f"{slug}.qmd").exists()   # source stripped
    assert env["build_calls"] == [{"clean": True}]      # build run with --clean
    assert len(env["consult_calls"]) == 1               # recount run after build


def test_excluded_guide_is_not_ported(env):
    commit_guides(env["upstream"], "anova", "bootstrap")
    env["exclude"].write_text("bootstrap\n")

    assert pg.port(env["upstream"]) == 0
    assert (env["dest"] / "anova").is_dir()
    assert not (env["dest"] / "bootstrap").exists()


def test_orphan_not_on_main_is_removed(env):
    commit_guides(env["upstream"], "anova")
    make_orphan(env["dest"], "stale-guide")

    assert pg.port(env["upstream"]) == 0
    assert (env["dest"] / "anova").is_dir()
    assert not (env["dest"] / "stale-guide").exists()   # mirror pruned it


def test_main_html_normalized_to_slug(env):
    commit_guides(env["upstream"], "diffindiff", html_name="differenceindifference.html")

    assert pg.port(env["upstream"]) == 0
    ported = env["dest"] / "diffindiff"
    assert (ported / "diffindiff.html").is_file()
    assert (ported / "differenceindifference.html").is_file()   # original kept


def test_ambiguous_html_fails_that_guide_only(env, capsys):
    commit_guides(env["upstream"], "anova")
    commit_guides(env["upstream"], "odd")  # second commit
    # give "odd" two html files and no odd.html
    (env["upstream"] / pg.UPSTREAM_SUBDIR / "odd" / "odd.html").unlink()
    (env["upstream"] / pg.UPSTREAM_SUBDIR / "odd" / "a.html").write_text("<html></html>")
    (env["upstream"] / pg.UPSTREAM_SUBDIR / "odd" / "b.html").write_text("<html></html>")
    git(env["upstream"], "add", "-A")
    git(env["upstream"], "commit", "-q", "-m", "ambiguous odd")

    assert pg.port(env["upstream"]) == 1
    out = capsys.readouterr().out
    assert "ambiguous main HTML" in out
    assert not (env["dest"] / "odd").exists()            # no half-ported guide
    assert (env["dest"] / "anova" / "anova.html").is_file()  # run continued
    assert env["build_calls"], "build still runs for the guides that succeeded"


def test_exclusion_typo_fails_before_any_work(env, capsys):
    commit_guides(env["upstream"], "anova")
    env["exclude"].write_text("anvoa\n")   # not on main

    assert pg.port(env["upstream"]) == 1
    assert "anvoa" in capsys.readouterr().err
    assert not any(env["dest"].iterdir())
    assert not env["build_calls"]


def test_dry_run_changes_nothing(env, capsys):
    commit_guides(env["upstream"], "anova")
    make_orphan(env["dest"], "stale-guide")

    assert pg.port(env["upstream"], dry_run=True) == 0
    assert not (env["dest"] / "anova").exists()          # nothing ported
    assert (env["dest"] / "stale-guide").exists()        # nothing removed
    assert not env["build_calls"]
    assert not env["consult_calls"]                      # dry run recounts nothing
    out = capsys.readouterr().out
    assert "would port: anova" in out
    assert "would remove (not on main): stale-guide" in out


def test_only_ports_one_and_does_not_prune(env):
    commit_guides(env["upstream"], "anova", "bootstrap")
    make_orphan(env["dest"], "keep-me")   # orphan that --only must NOT touch

    assert pg.port(env["upstream"], only=["anova"]) == 0
    assert (env["dest"] / "anova" / "anova.html").is_file()
    assert not (env["dest"] / "bootstrap").exists()      # other main guide not pulled
    assert (env["dest"] / "keep-me").exists()            # orphan left in place


def test_only_unknown_slug_errors(env, capsys):
    commit_guides(env["upstream"], "anova")
    assert pg.port(env["upstream"], only=["nope"]) == 1
    assert "not on main" in capsys.readouterr().err


def test_ref_reads_a_different_branch(env):
    commit_guides(env["upstream"], "anova")                 # main
    commit_guides(env["upstream"], "feature-guide", branch="feature")

    # plain ref mirror: pulls the feature branch's guides
    assert pg.port(env["upstream"], ref="feature") == 0
    assert (env["dest"] / "feature-guide").is_dir()

    # --only --ref pulls one guide from the branch without pruning anova
    assert pg.port(env["upstream"], only=["anova"], ref="main") == 0
    assert (env["dest"] / "anova").is_dir()
    assert (env["dest"] / "feature-guide").is_dir()         # not pruned by --only


def test_missing_ref_errors(env, capsys):
    commit_guides(env["upstream"], "anova")
    assert pg.port(env["upstream"], ref="nonexistent") == 1
    assert "not found" in capsys.readouterr().err
    assert not env["build_calls"]


# ---------------------------------------------------------------------------
# assets/ is the publish contract: everything committed there ships verbatim,
# even names the source/cache filters drop everywhere else.
# ---------------------------------------------------------------------------

def test_assets_tree_survives_the_copy_filters(env):
    commit_guides(env["upstream"], "anova")
    write_assets(env["upstream"], "anova")
    git(env["upstream"], "add", "-A")
    git(env["upstream"], "commit", "-q", "-m", "add assets")

    assert pg.port(env["upstream"]) == 0

    assets = env["dest"] / "anova" / "assets"
    assert (assets / "src" / "generate_data.R").is_file()   # 'src' is filtered elsewhere
    assert (assets / "scripts" / "refresh.sh").is_file()    # '*.sh' is filtered elsewhere
    assert (assets / "data" / "nunn.csv").is_file()
    assert (assets / "notes.qmd").is_file()                 # '*.qmd' is filtered elsewhere


def test_filters_still_apply_outside_assets(env):
    commit_guides(env["upstream"], "anova")
    guide = env["upstream"] / pg.UPSTREAM_SUBDIR / "anova"
    (guide / "src").mkdir()
    (guide / "src" / "helper.R").write_text("# R", encoding="utf-8")
    (guide / "notes-to-self.md").write_text("private", encoding="utf-8")
    write_assets(env["upstream"], "anova")
    git(env["upstream"], "add", "-A")
    git(env["upstream"], "commit", "-q", "-m", "add sources")

    assert pg.port(env["upstream"]) == 0

    ported = env["dest"] / "anova"
    assert not (ported / "src").exists()
    assert not (ported / "notes-to-self.md").exists()
    assert not (ported / "anova.qmd").exists()
    assert (ported / "assets" / "src" / "generate_data.R").is_file()


def test_underscore_prefixed_dirs_are_not_guides(env):
    """_translation-project and friends are upstream infrastructure, not guides."""
    commit_guides(env["upstream"], "anova")
    infra = env["upstream"] / pg.UPSTREAM_SUBDIR / "_translation-project"
    infra.mkdir(parents=True)
    (infra / "CONVENTIONS.md").write_text("# conventions", encoding="utf-8")
    git(env["upstream"], "add", "-A")
    git(env["upstream"], "commit", "-q", "-m", "add infra dir")

    assert pg.catalog(env["upstream"], "main") == ["anova"]
    # It has no rendered HTML, so selecting it would fail the whole port.
    assert pg.port(env["upstream"]) == 0
    assert not (env["dest"] / "_translation-project").exists()
