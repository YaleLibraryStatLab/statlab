"""Deterministic topic classification for published research guides.

The build pipeline imports :func:`classify_guide` so every port or direct
build writes topic IDs into ``guides_manifest.json``. This module also has a
CLI for previewing, checking, or repairing an existing manifest::

    python tools/guide_topics.py
    python tools/guide_topics.py --check
    python tools/guide_topics.py --write

Rules use specific statistical phrases rather than broad words such as
"regression". A guide that matches no rule is still publishable and is
reported for review. Exceptional cases belong in
``data/guide_topic_overrides.json`` rather than slug-specific Python code.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = ROOT / "guides_manifest.json"
DEFAULT_OVERRIDES = ROOT / "data" / "guide_topic_overrides.json"


@dataclass(frozen=True)
class Topic:
    id: str
    label: str
    terms: tuple[str, ...]


# Tuple order is public presentation order and therefore part of the output.
TOPICS: tuple[Topic, ...] = (
    Topic(
        "linear-generalized-models",
        "Linear & generalized models",
        (
            "ordinary least square", "ordinary least squares", "ols",
            "linear probability model", "binary response model",
            "limited dependent variable", "logistic regression",
            "probit regression", "generalized linear model",
            "generalized linear mixed effects model", "glmm",
            "maximum likelihood estimation", "odds ratio",
            "predicted probabilities", "marginal effects",
        ),
    ),
    Topic(
        "mixed-longitudinal-models",
        "Mixed & longitudinal models",
        (
            "mixed effects", "mixed effect", "hierarchical model",
            "multilevel model", "random effects", "variance components",
            "longitudinal data", "panel data", "clustered data", "glmm",
        ),
    ),
    Topic(
        "causal-inference",
        "Causal inference",
        (
            "instrumental variables", "causal inference",
            "regression discontinuity", "rdd", "confounding",
            "directed acyclic graph",
        ),
    ),
    Topic(
        "inference-model-building",
        "Inference & model building",
        (
            "standard errors", "heteroskedasticity", "robust inference",
            "cluster robust", "newey west", "hac", "conley", "bootstrap",
            "sandwich estimator", "covariate selection", "variable selection",
            "model selection", "overfitting", "aic", "bic",
            "cross validation", "t test", "anova",
            "maximum likelihood estimation", "odds ratio", "marginal effects",
        ),
    ),
    Topic(
        "time-to-event-models",
        "Time-to-event models",
        (
            "survival analysis", "time to event", "kaplan meier",
            "nelson aalen", "cox proportional hazards", "log rank",
            "censoring", "hazard ratio", "competing risks",
            "restricted mean survival time", "parametric survival model",
        ),
    ),
)

TOPIC_LABELS = {topic.id: topic.label for topic in TOPICS}
TOPIC_IDS = frozenset(TOPIC_LABELS)


class TopicConfigError(ValueError):
    """An override file is malformed or refers to unknown data."""


@dataclass(frozen=True)
class TopicOverride:
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()


def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).casefold()
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def _contains_phrase(haystack: str, phrase: str) -> bool:
    return f" {_normalise(phrase)} " in f" {haystack} "


def _matching_topics(text: str) -> list[str]:
    normalised = _normalise(text)
    return [
        topic.id
        for topic in TOPICS
        if any(_contains_phrase(normalised, term) for term in topic.terms)
    ]


def load_overrides(
    path: Path = DEFAULT_OVERRIDES,
    *,
    known_slugs: Iterable[str] | None = None,
) -> dict[str, TopicOverride]:
    """Load and validate per-guide includes/excludes from *path*."""
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TopicConfigError(f"could not read {path}: {exc}") from exc

    if not isinstance(raw, dict) or not isinstance(raw.get("guides", {}), dict):
        raise TopicConfigError(f"{path} must contain a 'guides' object")
    extra_keys = set(raw) - {"_comment", "guides"}
    if extra_keys:
        raise TopicConfigError(
            f"{path} has unknown top-level key(s): {', '.join(sorted(extra_keys))}"
        )

    guide_rules = raw.get("guides", {})
    if known_slugs is not None:
        unknown_slugs = set(guide_rules) - set(known_slugs)
        if unknown_slugs:
            raise TopicConfigError(
                "topic overrides refer to unknown guide slug(s): "
                + ", ".join(sorted(unknown_slugs))
            )

    overrides: dict[str, TopicOverride] = {}
    for slug, config in guide_rules.items():
        if not isinstance(config, dict) or set(config) - {"include", "exclude"}:
            raise TopicConfigError(
                f"override for {slug!r} may contain only 'include' and 'exclude'"
            )
        include = config.get("include", [])
        exclude = config.get("exclude", [])
        if not isinstance(include, list) or not all(isinstance(v, str) for v in include):
            raise TopicConfigError(f"override include for {slug!r} must be a list of topic IDs")
        if not isinstance(exclude, list) or not all(isinstance(v, str) for v in exclude):
            raise TopicConfigError(f"override exclude for {slug!r} must be a list of topic IDs")
        unknown_ids = (set(include) | set(exclude)) - TOPIC_IDS
        if unknown_ids:
            raise TopicConfigError(
                f"override for {slug!r} uses unknown topic ID(s): "
                + ", ".join(sorted(unknown_ids))
            )
        overlap = set(include) & set(exclude)
        if overlap:
            raise TopicConfigError(
                f"override for {slug!r} both includes and excludes: "
                + ", ".join(sorted(overlap))
            )
        overrides[slug] = TopicOverride(tuple(include), tuple(exclude))
    return overrides


def classify_guide(
    *,
    slug: str,
    title: str,
    keywords: Iterable[str],
    abstract: str | None = None,
    override: TopicOverride | None = None,
) -> list[str]:
    """Return ordered topic IDs for one guide."""
    primary = " ".join((slug, title, *keywords))
    matched = _matching_topics(primary)
    if not matched and abstract:
        abstract_text = BeautifulSoup(abstract, "html.parser").get_text(" ", strip=True)
        matched = _matching_topics(abstract_text)

    override = override or TopicOverride()
    selected = (set(matched) | set(override.include)) - set(override.exclude)
    return [topic.id for topic in TOPICS if topic.id in selected]


def classify_manifest(
    guides: list[dict],
    overrides: dict[str, TopicOverride],
) -> tuple[list[dict], list[str]]:
    """Return copied manifest entries with topics plus unclassified slugs."""
    enriched: list[dict] = []
    unclassified: list[str] = []
    for guide in guides:
        entry = dict(guide)
        topics = classify_guide(
            slug=entry["slug"],
            title=entry.get("title", ""),
            keywords=entry.get("keywords", []),
            abstract=entry.pop("_abstract", None),
            override=overrides.get(entry["slug"]),
        )
        entry["topics"] = topics
        if not topics:
            unclassified.append(entry["slug"])
        enriched.append(entry)
    return enriched, unclassified


def _read_manifest(path: Path) -> list[dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TopicConfigError(f"could not read {path}: {exc}") from exc
    if not isinstance(value, list) or not all(isinstance(g, dict) for g in value):
        raise TopicConfigError(f"{path} must contain a list of guide objects")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify research guides into browse topics.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="fail if stored topics are stale")
    mode.add_argument("--write", action="store_true", help="write classified topics to the manifest")
    args = parser.parse_args(argv)

    try:
        guides = _read_manifest(args.manifest)
        slugs = [guide.get("slug") for guide in guides]
        if any(not isinstance(slug, str) or not slug for slug in slugs):
            raise TopicConfigError("every manifest guide must have a non-empty string slug")
        overrides = load_overrides(args.overrides, known_slugs=slugs)
        classified, unclassified = classify_manifest(guides, overrides)
    except TopicConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for guide in classified:
        labels = [TOPIC_LABELS[topic_id] for topic_id in guide["topics"]]
        print(f"  {guide['slug']}: {', '.join(labels) if labels else 'REVIEW NEEDED'}")
    for slug in unclassified:
        print(f"warning: no topic matched guide {slug!r}", file=sys.stderr)

    if args.check:
        stale = [
            guide["slug"]
            for old, guide in zip(guides, classified)
            if old.get("topics", []) != guide["topics"]
        ]
        if stale:
            print("error: stale topic data for: " + ", ".join(stale), file=sys.stderr)
            return 1
        return 0

    output = json.dumps(classified, indent=2, ensure_ascii=False) + "\n"
    if args.write:
        args.manifest.write_text(output, encoding="utf-8")
        print(f"wrote {args.manifest}")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
