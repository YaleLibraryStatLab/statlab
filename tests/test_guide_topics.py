from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.guide_topics import (
    TopicConfigError,
    TopicOverride,
    classify_guide,
    classify_manifest,
    load_overrides,
    main,
)


def test_classifies_primary_metadata_in_presentation_order():
    assert classify_guide(
        slug="new-glmm-guide",
        title="A GLMM Guide",
        keywords=["causal inference", "multilevel models", "generalized linear models"],
    ) == [
        "linear-generalized-models",
        "mixed-longitudinal-models",
        "causal-inference",
    ]


def test_abstract_is_only_a_fallback():
    assert classify_guide(
        slug="iv-guide",
        title="Instrumental Variables",
        keywords=[],
        abstract="This includes an aside about survival analysis.",
    ) == ["causal-inference"]
    assert classify_guide(
        slug="event-guide",
        title="Event Timing",
        keywords=[],
        abstract="An introduction to <strong>Kaplan-Meier</strong> estimation.",
    ) == ["time-to-event-models"]


def test_override_can_include_and_exclude():
    assert classify_guide(
        slug="mixed-guide",
        title="Mixed-Effects Models",
        keywords=[],
        override=TopicOverride(
            include=("inference-model-building",),
            exclude=("mixed-longitudinal-models",),
        ),
    ) == ["inference-model-building"]


def test_unclassified_guide_is_retained_for_all_guides():
    guides, unclassified = classify_manifest(
        [{"slug": "mystery", "title": "A New Method", "keywords": []}],
        {},
    )
    assert guides[0]["topics"] == []
    assert unclassified == ["mystery"]


def write_overrides(path: Path, guides: dict) -> None:
    path.write_text(json.dumps({"guides": guides}), encoding="utf-8")


def test_override_rejects_unknown_topic(tmp_path):
    path = tmp_path / "overrides.json"
    write_overrides(path, {"known": {"include": ["made-up-topic"]}})
    with pytest.raises(TopicConfigError, match="unknown topic"):
        load_overrides(path, known_slugs={"known"})


def test_override_rejects_unknown_guide(tmp_path):
    path = tmp_path / "overrides.json"
    write_overrides(path, {"typo-slug": {"include": ["causal-inference"]}})
    with pytest.raises(TopicConfigError, match="unknown guide slug"):
        load_overrides(path, known_slugs={"known"})


def test_cli_check_detects_stale_topics(tmp_path, capsys):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([
        {"slug": "iv", "title": "Instrumental Variables", "keywords": [], "topics": []}
    ]))
    overrides = tmp_path / "overrides.json"
    write_overrides(overrides, {})

    assert main([
        "--manifest", str(manifest),
        "--overrides", str(overrides),
        "--check",
    ]) == 1
    assert "stale topic data" in capsys.readouterr().err


def test_current_guides_have_expected_topics():
    root = Path(__file__).resolve().parent.parent
    manifest = json.loads((root / "guides_manifest.json").read_text(encoding="utf-8"))
    overrides = load_overrides(
        root / "data" / "guide_topic_overrides.json",
        known_slugs={guide["slug"] for guide in manifest},
    )
    classified, unclassified = classify_manifest(manifest, overrides)
    assert unclassified == []
    assert {guide["slug"]: guide["topics"] for guide in classified} == {
        "glmms": ["linear-generalized-models", "mixed-longitudinal-models"],
        "instrumental-variables": ["causal-inference"],
        "logit-probit": ["linear-generalized-models", "inference-model-building"],
        "mixed-effects-models": ["mixed-longitudinal-models"],
        "olsregression": ["linear-generalized-models", "inference-model-building"],
        "panel-regression": ["mixed-longitudinal-models"],
        "rdd": ["causal-inference"],
        "standard-errors": ["inference-model-building"],
        "survival-analysis": ["time-to-event-models"],
        "variable-selection": ["causal-inference", "inference-model-building"],
    }
