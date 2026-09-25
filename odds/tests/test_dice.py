"""对拍测试：小面数下枚举所有掷骰路径，与生产算法（dice.py）逐一比对。

brute_* 函数是独立实现：不做任何分布合并技巧，直接枚举
每颗骰的 首掷 × 重掷 × 附加骰 路径，以及 n 颗骰的全部结果元组。
"""

from fractions import Fraction
from itertools import combinations, product

import pytest

from dice import (
    expectation,
    pool_distribution,
    prob_at_least,
    single_die_distribution,
    validate_params,
)


def brute_single_die(faces, reroll):
    """逐路径枚举单骰：首掷 -> (命中集合则恰好重掷一次) -> (最大面则追加一颗)。"""
    dist = {}

    def add(total, w):
        dist[total] = dist.get(total, Fraction(0)) + w

    for first in range(1, faces + 1):
        w_first = Fraction(1, faces)
        if first in reroll:
            finals = [(second, w_first / faces) for second in range(1, faces + 1)]
        else:
            finals = [(first, w_first)]
        for final, w in finals:
            if final == faces:
                for bonus in range(1, faces + 1):
                    add(final + bonus, w / faces)
            else:
                add(final, w)
    return dist


def brute_pool(n, faces, keep, reroll):
    """枚举 n 颗骰的所有结果元组，取最高 keep 颗求和。"""
    single = brute_single_die(faces, reroll)
    totals = sorted(single)
    dist = {}
    for combo in product(range(len(totals)), repeat=n):
        w = Fraction(1)
        values = []
        for idx in combo:
            w *= single[totals[idx]]
            values.append(totals[idx])
        values.sort(reverse=True)
        s = sum(values[:keep])
        dist[s] = dist.get(s, Fraction(0)) + w
    return dist


def all_reroll_subsets(faces):
    vals = list(range(1, faces + 1))
    return [
        frozenset(combo)
        for r in range(len(vals) + 1)
        for combo in combinations(vals, r)
    ]


@pytest.mark.parametrize("faces", range(2, 9))
def test_single_die_matches_bruteforce(faces):
    for reroll in all_reroll_subsets(faces):
        got = single_die_distribution(faces, reroll)
        assert got == brute_single_die(faces, reroll), (
            f"faces={faces} reroll={sorted(reroll)}"
        )
        assert sum(got.values()) == 1


@pytest.mark.parametrize("faces", [2, 3, 4])
@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_pool_matches_bruteforce(faces, n):
    for reroll in all_reroll_subsets(faces):
        for keep in range(1, n + 1):
            got = pool_distribution(n, faces, keep, reroll)
            want = brute_pool(n, faces, keep, reroll)
            assert got == want, (
                f"faces={faces} n={n} keep={keep} reroll={sorted(reroll)}"
            )
            assert sum(got.values()) == 1


def test_expectation_and_tail_match_bruteforce():
    for faces, n, keep, reroll in [
        (4, 3, 2, frozenset({1})),
        (3, 4, 2, frozenset({1, 3})),
        (2, 4, 4, frozenset()),
        (4, 2, 1, frozenset({1, 2, 3, 4})),
    ]:
        dist = pool_distribution(n, faces, keep, reroll)
        brute = brute_pool(n, faces, keep, reroll)
        assert expectation(dist) == sum(
            Fraction(t) * p for t, p in brute.items()
        )
        hi = max(brute)
        for threshold in range(0, hi + 2):
            assert prob_at_least(dist, threshold) == sum(
                p for t, p in brute.items() if t >= threshold
            )


def test_fractions_are_reduced_and_sum_to_one():
    dist = pool_distribution(3, 6, 2, frozenset({1, 2}))
    assert sum(dist.values()) == 1
    for p in dist.values():
        assert isinstance(p, Fraction)
        assert p.denominator > 0
        # Fraction 构造即约分：重构造后分子分母不变即为最简
        assert Fraction(p.numerator, p.denominator) == p


def test_no_reroll_no_bonus_edge():
    # 重掷集合为空时退化为普通骰：单骰分布 = 均匀 1..faces-1 加最大面追加
    dist = single_die_distribution(4, frozenset())
    assert dist[1] == dist[2] == dist[3] == Fraction(1, 4)
    assert 4 not in dist  # 最终面为 4 必触发追加，总分不可能恰为 4
    for t in range(5, 9):
        assert dist[t] == Fraction(1, 16)


@pytest.mark.parametrize(
    "raw",
    [
        {"n": 0, "faces": 6, "keep": 1},
        {"n": 7, "faces": 6, "keep": 1},
        {"n": 2, "faces": 1, "keep": 1},
        {"n": 2, "faces": 9, "keep": 1},
        {"n": 2, "faces": 6, "keep": 3},
        {"n": 2, "faces": 6, "keep": 0},
        {"n": 2, "faces": 6, "keep": 1, "reroll": [0]},
        {"n": 2, "faces": 6, "keep": 1, "reroll": [7]},
        {"n": 2, "faces": 6, "keep": 1, "reroll": "1"},
        {"n": 2, "faces": 6, "keep": 1, "reroll": [1.5]},
        {"n": 2.0, "faces": 6, "keep": 1},
        {"n": True, "faces": 6, "keep": 1},
        {"n": 2, "faces": 6, "keep": 1, "threshold": "5"},
        "not-a-dict",
    ],
)
def test_validate_params_rejects_bad_input(raw):
    with pytest.raises(ValueError):
        validate_params(raw)


def test_validate_params_normalizes():
    p = validate_params(
        {"n": 3, "faces": 6, "keep": 2, "reroll": [6, 1, 1], "threshold": 9}
    )
    assert p["reroll"] == frozenset({1, 6})
    assert p["threshold"] == 9
