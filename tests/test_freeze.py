from __future__ import annotations

from pathlib import Path

import pytest

from tools import freeze as freeze_mod


@pytest.fixture()
def frozen(tmp_path: Path, monkeypatch):
    """A stand-in docs/ tree plus the manifest that should describe it."""
    docs = tmp_path / "docs"
    docs.mkdir()

    def set_manifest(assets):
        monkeypatch.setattr(
            freeze_mod, "load_guides_manifest",
            lambda: [{"slug": "anova", "title": "Anova", "assets": assets}],
        )

    monkeypatch.setattr(freeze_mod, "DOCS_DIR", docs)
    return {"docs": docs, "set_manifest": set_manifest}


def write_frozen(docs: Path, slug: str, rel: str) -> None:
    path = docs / "guides" / slug / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("a,b\n1,2\n", encoding="utf-8")


def test_no_complaint_when_every_asset_was_frozen(frozen):
    frozen["set_manifest"](["assets/data/nunn.csv", "assets/scripts/sim.R"])
    write_frozen(frozen["docs"], "anova", "assets/data/nunn.csv")
    write_frozen(frozen["docs"], "anova", "assets/scripts/sim.R")

    assert freeze_mod.verify_frozen_assets() == []


def test_reports_assets_that_never_reached_the_site(frozen):
    frozen["set_manifest"](["assets/data/nunn.csv", "assets/scripts/sim.R"])
    write_frozen(frozen["docs"], "anova", "assets/data/nunn.csv")

    assert freeze_mod.verify_frozen_assets() == ["guides/anova/assets/scripts/sim.R"]


def test_guide_without_assets_is_fine(frozen):
    frozen["set_manifest"]([])
    assert freeze_mod.verify_frozen_assets() == []


def test_missing_manifest_is_not_an_error(frozen, monkeypatch):
    monkeypatch.setattr(freeze_mod, "load_guides_manifest", lambda: None)
    assert freeze_mod.verify_frozen_assets() == []
