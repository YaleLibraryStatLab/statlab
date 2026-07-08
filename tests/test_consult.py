from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.consult import _normalize_name, sync


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture()
def env(tmp_path: Path):
    manifest = tmp_path / "guides_manifest.json"
    consultants = tmp_path / "consultants.json"
    return {"manifest": manifest, "consultants": consultants}


def test_normalize_strips_credentials_and_case():
    assert _normalize_name("Atalay Demiray, MD, MSc") == "atalay demiray"
    assert _normalize_name("  Cole   Brookson ") == "cole brookson"


def test_credential_suffix_matches_bare_name(env):
    write_json(env["manifest"], [
        {"slug": "survival-analysis", "authors": ["Atalay Demiray, MD, MSc"]},
    ])
    write_json(env["consultants"], [
        {"name": "Atalay Demiray", "slug": "atalay-demiray", "guides": []},
    ])

    assert sync(env["manifest"], env["consultants"]) == 0
    assert read_json(env["consultants"])[0]["guides"] == ["survival-analysis"]


def test_overwrite_drops_stale_slug_and_accumulates(env):
    write_json(env["manifest"], [
        {"slug": "glmms", "authors": ["Cole Brookson"]},
        {"slug": "mixed-effects-models", "authors": ["Cole Brookson"]},
        {"slug": "panel-regression", "authors": ["Cole Brookson"]},
    ])
    write_json(env["consultants"], [
        {"name": "Cole Brookson", "slug": "cole-brookson", "guides": ["stale-guide"]},
    ])

    assert sync(env["manifest"], env["consultants"]) == 0
    # Manifest order preserved; stale hand-entered slug dropped.
    assert read_json(env["consultants"])[0]["guides"] == [
        "glmms", "mixed-effects-models", "panel-regression",
    ]


def test_no_authored_guides_clears_list(env):
    write_json(env["manifest"], [
        {"slug": "olsregression", "authors": ["Muji Chughtai"]},
    ])
    write_json(env["consultants"], [
        {"name": "Ted Ellsworth", "slug": "ted-ellsworth", "guides": ["old-guide"]},
        {"name": "Muji Chughtai", "slug": "muji-chughtai", "guides": []},
    ])

    assert sync(env["manifest"], env["consultants"]) == 0
    data = read_json(env["consultants"])
    assert data[0]["guides"] == []                       # cleared authoritatively
    assert data[1]["guides"] == ["olsregression"]


def test_unmatched_author_warns_but_succeeds(env, capsys):
    write_json(env["manifest"], [
        {"slug": "logit-probit", "authors": ["Jiye Kwon"]},
    ])
    write_json(env["consultants"], [
        {"name": "Cole Brookson", "slug": "cole-brookson", "guides": []},
    ])

    assert sync(env["manifest"], env["consultants"]) == 0
    err = capsys.readouterr().err
    assert "Jiye Kwon" in err and "logit-probit" in err
    assert read_json(env["consultants"])[0]["guides"] == []


def test_dry_run_writes_nothing(env):
    write_json(env["manifest"], [
        {"slug": "olsregression", "authors": ["Muji Chughtai"]},
    ])
    write_json(env["consultants"], [
        {"name": "Muji Chughtai", "slug": "muji-chughtai", "guides": []},
    ])

    assert sync(env["manifest"], env["consultants"], dry_run=True) == 0
    assert read_json(env["consultants"])[0]["guides"] == []   # unchanged on disk


def test_missing_manifest_is_a_warning_not_a_failure(env, capsys):
    write_json(env["consultants"], [
        {"name": "Muji Chughtai", "slug": "muji-chughtai", "guides": ["keep"]},
    ])

    assert sync(env["manifest"], env["consultants"]) == 0
    assert "not found" in capsys.readouterr().err
    assert read_json(env["consultants"])[0]["guides"] == ["keep"]  # untouched


def test_other_fields_and_order_preserved(env):
    write_json(env["manifest"], [
        {"slug": "olsregression", "authors": ["Muji Chughtai"]},
    ])
    write_json(env["consultants"], [
        {"name": "Muji Chughtai", "slug": "muji-chughtai", "guides": [], "role": "PhD"},
    ])

    assert sync(env["manifest"], env["consultants"]) == 0
    c = read_json(env["consultants"])[0]
    assert c["role"] == "PhD"
    assert list(c.keys()) == ["name", "slug", "guides", "role"]
