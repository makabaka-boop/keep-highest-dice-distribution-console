"""桌面骰池的精确概率引擎。

规则（每颗骰子独立，共 n 颗）：
1. 每颗骰先掷一次（1..faces 均匀）。
2. 若首掷命中重掷面集合 reroll，则恰好重掷一次，以第二次结果为准
   （第二次即使再次命中重掷面也不再重掷）。
3. 最终面等于最大面 faces 时，追加掷一颗附加骰并相加；
   附加骰不再重掷，也不再触发追加。
4. 全部骰子结算后，从 n 个总点数中保留最高的 keep 颗求和。

所有概率用 fractions.Fraction 精确表示，构造时自动约分，
因此分布中每个总分的概率都是最简分数，且全部概率之和恒为 1。
"""

from __future__ import annotations

from fractions import Fraction
from math import factorial
from typing import Dict, FrozenSet

MIN_DICE = 1
MAX_DICE = 6
MIN_FACES = 2
MAX_FACES = 8


def validate_params(raw) -> dict:
    """校验并规范化请求参数，非法输入抛出 ValueError。"""
    if not isinstance(raw, dict):
        raise ValueError("请求体必须是 JSON 对象")

    def _int(name: str, lo: int, hi: int) -> int:
        v = raw.get(name)
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(f"{name} 必须是整数")
        if not lo <= v <= hi:
            raise ValueError(f"{name} 必须在 {lo}~{hi} 之间")
        return v

    n = _int("n", MIN_DICE, MAX_DICE)
    faces = _int("faces", MIN_FACES, MAX_FACES)
    keep = _int("keep", 1, n)

    reroll_raw = raw.get("reroll", [])
    if not isinstance(reroll_raw, list):
        raise ValueError("reroll 必须是整数数组")
    reroll = set()
    for v in reroll_raw:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError("reroll 元素必须是整数")
        if not 1 <= v <= faces:
            raise ValueError(f"重掷面必须在 1~{faces} 之间")
        reroll.add(v)

    threshold = raw.get("threshold", 0)
    if isinstance(threshold, bool) or not isinstance(threshold, int):
        raise ValueError("threshold 必须是整数")

    return {
        "n": n,
        "faces": faces,
        "keep": keep,
        "reroll": frozenset(reroll),
        "threshold": threshold,
    }


def single_die_distribution(faces: int, reroll: FrozenSet[int]) -> Dict[int, Fraction]:
    """单颗骰子最终总点数的精确分布。

    最终面为 v 的概率 = 首掷即 v 且 v 不重掷 + 首掷命中重掷集合后再掷出 v。
    最终面为最大面时，总分 = faces + 附加骰（1..faces 均匀）。
    """
    r = len(reroll)
    dist: Dict[int, Fraction] = {}
    for v in range(1, faces + 1):
        p = Fraction(r, faces * faces)
        if v not in reroll:
            p += Fraction(1, faces)
        if v == faces:
            for bonus in range(1, faces + 1):
                dist[v + bonus] = dist.get(v + bonus, Fraction(0)) + p / faces
        else:
            dist[v] = dist.get(v, Fraction(0)) + p
    return dist


def pool_distribution(
    n: int, faces: int, keep: int, reroll: FrozenSet[int]
) -> Dict[int, Fraction]:
    """n 颗独立骰取最高 keep 颗求和的精确分布。

    按多重集枚举：每颗骰的取值种类很少（<= 2*faces-1 种），
    枚举所有计数向量 (c_1..c_m)（和为 n），其概率为多项式系数乘积，
    对每种多重集直接算出最高 keep 颗之和。
    """
    single = single_die_distribution(faces, reroll)
    values = sorted(single)
    probs = [single[v] for v in values]
    m = len(values)
    counts = [0] * m
    n_fact = factorial(n)
    result: Dict[int, Fraction] = {}

    def visit(pos: int, remaining: int) -> None:
        if pos == m - 1:
            counts[pos] = remaining
            coeff = n_fact
            prob = Fraction(1)
            for c, p in zip(counts, probs):
                coeff //= factorial(c)  # 逐次整除仍为整数（多项式系数性质）
                prob *= p ** c
            prob *= coeff
            total = 0
            left = keep
            for i in range(m - 1, -1, -1):
                if counts[i] == 0:
                    continue
                take = min(left, counts[i])
                total += take * values[i]
                left -= take
                if left == 0:
                    break
            result[total] = result.get(total, Fraction(0)) + prob
            return
        for c in range(remaining + 1):
            counts[pos] = c
            visit(pos + 1, remaining - c)

    visit(0, n)
    return result


def expectation(dist: Dict[int, Fraction]) -> Fraction:
    """分布的期望（精确分数）。"""
    return sum((Fraction(t) * p for t, p in dist.items()), Fraction(0))


def prob_at_least(dist: Dict[int, Fraction], threshold: int) -> Fraction:
    """P(总分 >= threshold)，精确分数。"""
    return sum((p for t, p in dist.items() if t >= threshold), Fraction(0))
