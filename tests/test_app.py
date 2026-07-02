from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from app import app, list_available_guides


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_index(client):
    assert client.get("/").status_code == 200


def test_research_guides(client):
    assert client.get("/research-guides/").status_code == 200


def test_research_guides_has_accessible_topic_filters(client):
    response = client.get("/research-guides/")
    soup = BeautifulSoup(response.data, "html.parser")

    filters = soup.select_one("[data-guide-filters]")
    assert filters is not None and filters.has_attr("hidden")
    buttons = filters.select("button[data-topic]")
    assert buttons[0].get_text(strip=True) == "All topics"
    assert buttons[0]["aria-pressed"] == "true"
    assert {button["data-topic"] for button in buttons[1:]} == {
        "linear-generalized-models",
        "mixed-longitudinal-models",
        "causal-inference",
        "inference-model-building",
        "time-to-event-models",
    }
    assert soup.select_one("#guide-filter-status[role='status'][aria-live='polite']")

    cards = soup.select("#guide-list .guide-card[data-topics]")
    assert len(cards) == len(list_available_guides())
    assert all(card.select(".guide-card__topics li") for card in cards)
    assert all(not card.has_attr("hidden") for card in cards)


def test_research_guides_has_progressive_search_ui(client):
    response = client.get("/research-guides/")
    soup = BeautifulSoup(response.data, "html.parser")

    search = soup.select_one("[data-guide-search][role='search']")
    assert search is not None and search.has_attr("hidden")
    assert search.select_one("pagefind-searchbox[show-sub-results]")
    config = search.select_one("pagefind-config")
    assert config["bundle-path"] == "/pagefind/"
    assert config["base-url"] == "/"
    assert soup.select_one(
        "link[href='/pagefind/pagefind-component-ui.css']"
    )
    ids = [tag["id"] for tag in soup.select("[id]")]
    assert len(ids) == len(set(ids))


def test_pagefind_assets_are_served_in_local_preview(client, tmp_path, monkeypatch):
    search_dir = tmp_path / "pagefind"
    search_dir.mkdir()
    (search_dir / "pagefind.js").write_text("export const ready = true;", encoding="utf-8")
    monkeypatch.setattr("app.PAGEFIND_DIR", search_dir)

    response = client.get("/pagefind/pagefind.js")
    assert response.status_code == 200
    assert b"ready = true" in response.data


def test_manifest_topics_reach_guide_listing():
    guides = {guide["slug"]: guide for guide in list_available_guides()}
    assert guides["glmms"]["topics"] == [
        "linear-generalized-models",
        "mixed-longitudinal-models",
    ]


def test_guide_page(client):
    response = client.get("/guides/mixed-effects-models/")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    article = soup.select_one("article.guide-article[data-pagefind-body]")
    assert article is not None
    assert article.select_one("h1[data-pagefind-meta='title']")
    heading_ids = [heading.get("id") for heading in article.select(".guide-content h1, .guide-content h2, .guide-content h3, .guide-content h4, .guide-content h5, .guide-content h6")]
    assert heading_ids and all(heading_ids)
    assert len(heading_ids) == len(set(heading_ids))
    all_ids = [tag["id"] for tag in soup.select("[id]")]
    assert len(all_ids) == len(set(all_ids))
