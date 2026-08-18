from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

import app as app_module
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


# ---------------------------------------------------------------------------
# Data & materials — the per-guide download set recorded by tools/build.py
# ---------------------------------------------------------------------------

def _with_manifest(monkeypatch, assets):
    monkeypatch.setattr(
        app_module, "load_guides_manifest",
        lambda: [{"slug": "demo", "title": "Demo", "assets": assets}],
    )


def test_guide_downloads_groups_by_assets_subdirectory(monkeypatch):
    _with_manifest(monkeypatch, [
        "assets/data/nunn.csv",
        "assets/data/nunn.Rda",
        "assets/scripts/simulate.R",
        "assets/README.txt",
    ])

    groups = {g["label"]: [f["name"] for f in g["files"]]
              for g in app_module.guide_downloads("demo")}
    assert groups == {
        "Data": ["nunn.csv", "nunn.Rda"],
        "Scripts": ["simulate.R"],
        "Files": ["README.txt"],
    }


def test_guide_downloads_omits_inline_figures(monkeypatch):
    """assets/images/ is rendered in the body already — not a download."""
    _with_manifest(monkeypatch, ["assets/images/fig.png", "assets/data/d.csv"])
    labels = [g["label"] for g in app_module.guide_downloads("demo")]
    assert labels == ["Data"]


def test_guide_downloads_empty_for_unknown_guide(monkeypatch):
    _with_manifest(monkeypatch, ["assets/data/d.csv"])
    assert app_module.guide_downloads("not-a-guide") == []


def test_downloads_section_renders_with_prefixed_urls(client, monkeypatch):
    monkeypatch.setattr(
        app_module, "guide_downloads",
        lambda slug: [{"label": "Data",
                       "files": [{"path": "assets/data/nunn.csv", "name": "nunn.csv"}]}],
    )
    soup = BeautifulSoup(client.get("/guides/mixed-effects-models/").data, "html.parser")

    section = soup.select_one("section.guide-downloads")
    assert section is not None
    assert section.has_attr("data-pagefind-ignore")   # keep filenames out of search
    link = section.select_one("a[download]")
    assert link["download"] == "nunn.csv"
    assert link["href"].endswith("/guides/mixed-effects-models/assets/data/nunn.csv")


def test_no_downloads_section_when_guide_has_no_assets(client, monkeypatch):
    monkeypatch.setattr(app_module, "guide_downloads", lambda slug: [])
    soup = BeautifulSoup(client.get("/guides/mixed-effects-models/").data, "html.parser")
    assert soup.select_one("section.guide-downloads") is None


def test_guide_asset_serves_nested_paths(client):
    """The route that makes /guides/<slug>/assets/... resolvable."""
    rel = "assets/data/washb-index.csv"
    on_disk = app_module.TEMP_GUIDES_DIR / "logit-probit" / rel
    response = client.get(f"/guides/logit-probit/{rel}")
    assert response.status_code == 200
    assert response.data == on_disk.read_bytes()


# ---------------------------------------------------------------------------
# Consultations FAQ — authored in assets/statlab-faqs.md, rendered at build
# ---------------------------------------------------------------------------

FAQ_MD = """\
Intro prose before any question is not itself a question.

### Does it cost anything?

No. It is **free**.

Second paragraph.

### Can you help with code?

Yes, with caveats.
"""


def test_parse_faqs_splits_on_level_three_headings():
    faqs = app_module.parse_faqs(FAQ_MD)
    assert [f["question"] for f in faqs] == [
        "Does it cost anything?",
        "Can you help with code?",
    ]


def test_parse_faqs_renders_markdown_in_answers():
    first = app_module.parse_faqs(FAQ_MD)[0]
    assert "<strong>free</strong>" in first["answer_html"]
    assert first["answer_html"].count("<p>") == 2   # both paragraphs survive


def test_parse_faqs_builds_stable_anchors():
    assert app_module.parse_faqs(FAQ_MD)[0]["anchor"] == "faq-does-it-cost-anything"


def test_parse_faqs_ignores_text_before_the_first_question():
    assert all("Intro prose" not in f["answer_html"] for f in app_module.parse_faqs(FAQ_MD))


def test_parse_faqs_empty_for_markdown_without_questions():
    assert app_module.parse_faqs("Just prose, no headings.\n") == []


def test_load_faqs_survives_a_missing_source_file(monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "FAQS_FILE", tmp_path / "nope.md")
    monkeypatch.setattr(app_module, "_faq_cache", {})
    assert app_module.load_faqs() == []


def test_consultations_page_renders_every_faq(client):
    soup = BeautifulSoup(client.get("/consultations/").data, "html.parser")
    questions = soup.select(".faq-list__q")
    answers = soup.select(".faq-list__a")
    assert len(questions) == len(app_module.load_faqs()) > 0
    assert len(answers) == len(questions)
    # each question is anchorable, and the anchor matches its heading id
    for dt in questions:
        assert dt.get("id")
        assert dt.select_one("a")["href"] == f"#{dt['id']}"


def test_consultations_faq_section_absent_when_there_are_no_faqs(client, monkeypatch):
    monkeypatch.setattr(app_module, "load_faqs", lambda: [])
    soup = BeautifulSoup(client.get("/consultations/").data, "html.parser")
    assert soup.select_one(".faq-list") is None


# ---------------------------------------------------------------------------
# Feedback / resource-request form — one MS Form, two named intents
# ---------------------------------------------------------------------------

FEEDBACK_PAGES = ["/workshops/", "/research-guides/"]


def _external_link_is_safe(a):
    """target=_blank without rel=noopener leaks window.opener to the new tab."""
    rel = a.get("rel") or []
    return a.get("target") == "_blank" and "noopener" in rel and "noreferrer" in rel


@pytest.mark.parametrize("path", ["/", "/consultations/", *FEEDBACK_PAGES])
def test_contact_dropdown_names_both_intents(client, path):
    soup = BeautifulSoup(client.get(path).data, "html.parser")
    links = [a for a in soup.select(".dropdown-menu a")
             if a["href"] == app_module.FEEDBACK_FORM_URL]
    labels = [a.get_text(" ", strip=True) for a in links]
    assert len(links) == 2, "both 'feedback' and 'request' entry points present"
    assert any("Share feedback" in text for text in labels)
    assert any("Request a resource" in text for text in labels)
    assert all(_external_link_is_safe(a) for a in links)


@pytest.mark.parametrize("path", FEEDBACK_PAGES)
def test_feedback_widget_renders_on_resource_pages(client, path):
    soup = BeautifulSoup(client.get(path).data, "html.parser")
    callout = soup.select_one(".feedback-callout")
    assert callout is not None
    cta = callout.select_one("a")
    assert cta["href"] == app_module.FEEDBACK_FORM_URL
    assert _external_link_is_safe(cta)


@pytest.mark.parametrize("path", FEEDBACK_PAGES)
def test_feedback_widget_is_a_labelled_landmark(client, path):
    soup = BeautifulSoup(client.get(path).data, "html.parser")
    callout = soup.select_one(".feedback-callout")
    target = callout["aria-labelledby"]
    assert soup.select_one(f"#{target}") is not None
    ids = [tag["id"] for tag in soup.select("[id]")]
    assert len(ids) == len(set(ids)), "widget ids must not collide with the page"


@pytest.mark.parametrize("path", FEEDBACK_PAGES)
def test_new_tab_links_announce_themselves(client, path):
    """Sighted users see the arrow; screen readers need it said out loud."""
    soup = BeautifulSoup(client.get(path).data, "html.parser")
    cta = soup.select_one(".feedback-callout a")
    hidden = cta.select_one(".visually-hidden")
    assert hidden is not None and "new tab" in hidden.get_text(strip=True)


def test_feedback_widget_stays_off_unrelated_pages(client):
    for path in ("/", "/about/", "/consultations/"):
        soup = BeautifulSoup(client.get(path).data, "html.parser")
        assert soup.select_one(".feedback-callout") is None, path


def test_form_url_is_defined_once(client):
    """The three entry points must all read the same constant, not copies."""
    soup = BeautifulSoup(client.get("/research-guides/").data, "html.parser")
    hrefs = {a["href"] for a in soup.select("a[href]")
             if "forms.cloud.microsoft" in a["href"]}
    assert hrefs == {app_module.FEEDBACK_FORM_URL}


def test_workshops_cta_names_the_dominant_intent(client):
    """Workshops routes requests to the form; email keeps open-ended questions."""
    soup = BeautifulSoup(client.get("/workshops/").data, "html.parser")

    cta = soup.select_one(".feedback-callout a")
    assert "Request a workshop" in cta.get_text(" ", strip=True)

    # The blurb must still tell the feedback half of the audience they belong.
    blurb = soup.select_one(".feedback-callout__body").get_text(" ", strip=True)
    assert "feedback" in blurb.lower()

    # The notice's email button no longer solicits topic requests.
    notice = soup.select_one(".workshops-notice").get_text(" ", strip=True)
    assert "like us to teach" not in notice
    assert soup.select_one(".workshops-notice a[href^='mailto:']") is not None


def test_consultations_does_not_duplicate_the_faq_in_hand_written_prose(client):
    """The .md is the single source for explanatory copy on this page.

    Guards the consolidation: eligibility and services were previously stated
    both in the template and in the FAQ, which drifted (the template listed
    postdocs; the Markdown did not).
    """
    soup = BeautifulSoup(client.get("/consultations/").data, "html.parser")
    headings = [h.get_text(strip=True) for h in soup.select(".consult-section > h2")]
    assert headings == ["How to Book", "Frequently Asked Questions"]

    # Eligibility/cost copy belongs to the FAQ only. Repeats *within* the FAQ
    # are fine — each answer is anchor-linkable and has to stand alone.
    faq_block = soup.select_one(".faq-list")
    assert "free of charge" in faq_block.get_text(" ", strip=True).lower()
    faq_block.decompose()
    remaining = soup.select_one(".consult-body").get_text(" ", strip=True).lower()
    assert "free of charge" not in remaining
    assert "all disciplines" not in remaining


def test_eligibility_answer_keeps_the_facts_the_template_used_to_carry(client):
    soup = BeautifulSoup(client.get("/consultations/").data, "html.parser")
    faq = soup.select_one(".faq-list").get_text(" ", strip=True).lower()
    for fact in ("postdoc", "disciplines", "humanities", "public health"):
        assert fact in faq, f"{fact} was lost when the template section was removed"


def test_faq_referral_links_are_real_links(client):
    """Bracketed placeholders render as literal text, not links — catch regressions."""
    soup = BeautifulSoup(client.get("/consultations/").data, "html.parser")
    faq = soup.select_one(".faq-list")
    hrefs = {a["href"] for a in faq.select("a[href^='http']")}
    assert hrefs == {
        "https://www.library.yale.edu/help-and-research-support/subject-specialist",
        "https://guides.library.yale.edu/GIS",
        "https://researchdata.yale.edu/research-data-management",
        "https://library.yale.edu/digital-humanities-laboratory",
    }


def test_faq_markdown_lists_survive_rendering(client):
    soup = BeautifulSoup(client.get("/consultations/").data, "html.parser")
    assert len(soup.select(".faq-list__a li")) >= 4
