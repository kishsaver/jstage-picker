"""コマンドライン入口: 検索 → 採点 → 選定 → HTML 出力。

使い方:
  jstage-picker                 # 5件
  jstage-picker -n 3            # 3件
  jstage-picker --seed 醤油 苔   # 種語を指定
  jstage-picker --llm           # 選定だけ Claude に任せる（要 ANTHROPIC_API_KEY）
"""

import argparse
import random
import sys
import webbrowser
from datetime import date
from pathlib import Path

from jstage_picker import jstage, scoring
from jstage_picker.config import POOL_SIZE, SEARCH_COUNT, SEEN_FILE
from jstage_picker.http_client import PoliteClient
from jstage_picker.llm import llm_pick
from jstage_picker.models import Paper
from jstage_picker.render import render_html
from jstage_picker.seeds import SEEDS
from jstage_picker.seen import SeenStore


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="J-STAGEから面白そうな論文を拾う")
    ap.add_argument("-n", type=int, default=5, help="選ぶ件数")
    ap.add_argument("--seeds", type=int, default=8, help="使う種語の数（=API検索回数）")
    ap.add_argument("--seed", nargs="*", help="種語を指定")
    ap.add_argument(
        "--per-seed", type=int, default=4, help="種語ごとに抄録を見に行く件数"
    )
    ap.add_argument("--since", type=int, default=1990, help="この年以降の論文から")
    ap.add_argument("--llm", action="store_true", help="最終選定をClaudeに任せる")
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("-o", default="jstage_picks.html")
    ap.add_argument("--no-open", action="store_true")
    return ap.parse_args(argv)


def random_year_range(since: int, this_year: int) -> tuple[int, int]:
    """検索対象の年範囲をランダムに決める（毎回違う時代に当たるように）。"""
    start = random.randint(since, this_year - 3)
    end = min(this_year, start + random.randint(3, 15))
    return start, end


def search_seed(
    client: PoliteClient, seed: str, since: int, seen: set[str]
) -> list[Paper]:
    """種語で検索し、候補になりうる論文をシャッフルして返す。"""
    year_from, year_to = random_year_range(since, date.today().year)
    try:
        xml_text = client.get(jstage.search_url(seed, year_from, year_to, SEARCH_COUNT))
    except Exception as ex:  # noqa: BLE001
        print(f"  検索失敗: {seed} ({ex})", file=sys.stderr)
        return []
    found = [
        p for p in jstage.parse_search(xml_text, seed) if scoring.is_candidate(p, seen)
    ]
    random.shuffle(found)
    print(f"「{seed}」{year_from}-{year_to}: {len(found)}件ヒット", file=sys.stderr)
    return found


def enrich(client: PoliteClient, p: Paper) -> bool:
    """記事ページから抄録などを取って採点する。抄録が取れたら True。"""
    try:
        p.apply(jstage.parse_article(client.get(p.url)))
    except Exception:  # noqa: BLE001
        return False
    p.score = scoring.score(p)
    return bool(p.abstract)


def collect_candidates(
    client: PoliteClient, seeds: list[str], per_seed: int, since: int, seen: set[str]
) -> list[Paper]:
    candidates = []
    for seed in seeds:
        for p in search_seed(client, seed, since, seen)[:per_seed]:
            if enrich(client, p):
                candidates.append(p)
    return candidates


def print_summary(picks: list[Paper], out: Path) -> None:
    print(f"\n{len(picks)}件を書き出しました: {out}", file=sys.stderr)
    for p in picks:
        print(f"・{p.title}（{p.journal}, {p.year}）\n  {p.url}")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    seen_store = SeenStore(SEEN_FILE)
    seeds = args.seed or random.sample(SEEDS, args.seeds)

    candidates = collect_candidates(
        PoliteClient(), seeds, args.per_seed, args.since, seen_store.load()
    )
    if not candidates:
        sys.exit(
            "候補が見つかりませんでした。--seeds を増やすか時間をおいて再実行してください。"
        )

    pool = scoring.top_by_score(candidates, POOL_SIZE)
    picks = (
        llm_pick(pool, args.n, args.model)
        if args.llm
        else scoring.pick_diverse(pool, args.n)
    )

    out = Path(args.o).resolve()
    out.write_text(render_html(picks), encoding="utf-8")
    seen_store.add(picks)
    print_summary(picks, out)
    if not args.no_open:
        webbrowser.open(out.as_uri())
