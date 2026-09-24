"""「読み物として面白そうか」のヒューリスティック採点と選定。"""

import random
import re

from jstage_picker.models import Paper

JUNK_MATERIAL = re.compile(
    r"(大会|講演|予稿|発表|要旨|抄録集|学術講演|シンポジウム|年次|Proceedings|Abstract)",
    re.I,
)
CURIOUS = re.compile(
    r"(なぜ|謎|起源|由来|誕生|変遷|再考|試論|意外|とは何か|について|をめぐる|の歴史|の民俗|の文化|？|\?)"
)
KANA = re.compile(r"[぀-ヿ]")
DENSE_CHARS = re.compile(r"[A-Za-z0-9%±=<>μ]")

NO_ABSTRACT_SCORE = -99.0
JITTER = 1.2  # 毎回少し揺らす幅


def is_candidate(p: Paper, seen: set[str]) -> bool:
    """日本語タイトルで、未読で、予稿集でないもの。"""
    return (
        bool(KANA.search(p.title))
        and p.doi not in seen
        and not JUNK_MATERIAL.search(p.journal)
    )


def score(p: Paper, rng: random.Random = random) -> float:
    a = p.abstract
    if not a:
        return NO_ABSTRACT_SCORE
    n = len(a)
    s = 0.0
    s += (
        2 if 200 <= n <= 900 else (0.5 if n > 900 else -2)
    )  # 短すぎる抄録は読み応えがない
    s += 1.5 if p.free else -1  # 本文まで読めるもの優先
    s += 1.5 if CURIOUS.search(p.title) else 0
    s -= 3 if JUNK_MATERIAL.search(p.journal) else 0  # 学会の予稿集は薄いことが多い
    # 専門用語の濃さ：英字・数字・記号の割合が高いほど減点
    s -= len(DENSE_CHARS.findall(a)) / n * 12
    # 「本研究では〜を明らかにした」だけの定型抄録は少し減点
    if a.count("明らかにした") + a.count("示唆された") >= 2:
        s -= 0.5
    s += rng.uniform(0, JITTER)
    return s


def top_by_score(papers: list[Paper], limit: int) -> list[Paper]:
    return sorted(papers, key=lambda p: p.score, reverse=True)[:limit]


def pick_diverse(papers: list[Paper], n: int) -> list[Paper]:
    """スコア上位から、雑誌も種語も被らないように n 件選ぶ。"""
    chosen: list[Paper] = []
    journals: set[str] = set()
    seeds: set[str] = set()
    for p in top_by_score(papers, len(papers)):
        if p.journal in journals or p.seed in seeds:
            continue
        chosen.append(p)
        journals.add(p.journal)
        seeds.add(p.seed)
        if len(chosen) == n:
            break
    return chosen
