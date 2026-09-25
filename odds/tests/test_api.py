"""Flask API 测试：响应结构、约分分数、概率合计为 1、期望与尾部概率自洽。"""

from fractions import Fraction

import pytest

from app import app


@pytest.fixture
def client():
    return app.test_client()


def _frac(row):
    return Fraction(int(row["num"]), int(row["den"]))


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_distribution_response(client):
    body = {"n": 3, "faces": 6, "keep": 2, "reroll": [1], "threshold": 12}
    resp = client.post("/api/distribution", json=body)
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["params"] == {**body, "reroll": [1]}
    assert data["total_probability"] == "1/1"
    assert data["at_least"]["threshold"] == 12

    dist = data["distribution"]
    assert [row["total"] for row in dist] == sorted(row["total"] for row in dist)

    # 概率合计恰为 1，且每个分数都是最简
    total = sum((_frac(row) for row in dist), Fraction(0))
    assert total == 1
    for row in dist:
        f = _frac(row)
        assert (f.numerator, f.denominator) == (int(row["num"]), int(row["den"]))
        assert abs(row["decimal"] - float(f)) < 1e-15

    # 期望、尾部概率与分布自洽
    exp = sum((_frac(row) * row["total"] for row in dist), Fraction(0))
    assert _frac(data["expectation"]) == exp
    tail = sum(
        (_frac(row) for row in dist if row["total"] >= 12), Fraction(0)
    )
    assert _frac(data["at_least"]) == tail


def test_distribution_defaults(client):
    resp = client.post("/api/distribution", json={"n": 1, "faces": 2, "keep": 1})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["params"]["reroll"] == []
    assert data["params"]["threshold"] == 0
    # 阈值 0 时尾部概率必为 1
    assert _frac(data["at_least"]) == 1


@pytest.mark.parametrize(
    "body",
    [
        {"n": 0, "faces": 6, "keep": 1},
        {"n": 2, "faces": 6, "keep": 5},
        {"n": 2, "faces": 6, "keep": 1, "reroll": [9]},
        {"n": "2", "faces": 6, "keep": 1},
        {},
    ],
)
def test_distribution_bad_request(client, body):
    resp = client.post("/api/distribution", json=body)
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_distribution_non_json(client):
    resp = client.post("/api/distribution", data="x", content_type="text/plain")
    assert resp.status_code == 400
