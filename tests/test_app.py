from __future__ import annotations

import pytest

from app import app


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_index(client):
    assert client.get("/").status_code == 200


def test_research_guides(client):
    assert client.get("/research-guides").status_code == 200


def test_guide_page(client):
    assert client.get("/guides/mixed-effects-models/").status_code == 200
