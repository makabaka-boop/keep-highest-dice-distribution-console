"""Flask 服务：返回骰池总分的精确概率分布（约分分数）。"""

from fractions import Fraction

from flask import Flask, jsonify, request

import dice

app = Flask(__name__)


@app.after_request
def add_cors_headers(resp):
    # 同源部署时由 ui 容器反代，无需 CORS；这里放行方便本地联调
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


def _frac(fr: Fraction) -> dict:
    return {
        "num": str(fr.numerator),
        "den": str(fr.denominator),
        "decimal": float(fr),
    }


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/api/distribution")
def distribution():
    body = request.get_json(silent=True)
    if body is None:
        return jsonify(error="请求体必须是 JSON"), 400
    try:
        p = dice.validate_params(body)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    dist = dice.pool_distribution(p["n"], p["faces"], p["keep"], p["reroll"])
    exp = dice.expectation(dist)
    tail = dice.prob_at_least(dist, p["threshold"])
    total = sum(dist.values(), Fraction(0))

    return jsonify(
        params={
            "n": p["n"],
            "faces": p["faces"],
            "keep": p["keep"],
            "reroll": sorted(p["reroll"]),
            "threshold": p["threshold"],
        },
        distribution=[
            {"total": t, **_frac(prob)} for t, prob in sorted(dist.items())
        ],
        expectation=_frac(exp),
        at_least={"threshold": p["threshold"], **_frac(tail)},
        total_probability=f"{total.numerator}/{total.denominator}",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
