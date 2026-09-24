"""任意: 最終選定だけ Claude に任せる。失敗時はヒューリスティックにフォールバック。"""

import json
import os
import re
import sys
import urllib.request

from jstage_picker.models import Paper
from jstage_picker.scoring import pick_diverse

MESSAGES_API = "https://api.anthropic.com/v1/messages"
ABSTRACT_PREVIEW = 600  # プロンプトに入れる抄録の最大文字数


def _build_prompt(papers: list[Paper], n: int) -> str:
    listing = "\n\n".join(
        f"[{i}] {p.title}（{p.journal}）\n{p.abstract[:ABSTRACT_PREVIEW]}"
        for i, p in enumerate(papers)
    )
    return (
        f"以下は学術論文の候補です。専門外の好奇心旺盛な一般読者が、抄録を読んで『へえ』と思い本文も読みたくなるものを"
        f"{n}件選んでください。分野はなるべくばらけさせること。予稿や定型的な報告は避けること。\n"
        f"出力はJSON配列の番号のみ（例: [3, 7, 12]）。説明は不要。\n\n{listing}"
    )


def _call_claude(prompt: str, model: str, api_key: str) -> str:
    body = json.dumps(
        {
            "model": model,
            "max_tokens": 100,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    req = urllib.request.Request(
        MESSAGES_API,
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["content"][0]["text"]


def _parse_indices(text: str) -> list[int]:
    match = re.search(r"\[.*?\]", text, re.S)
    if not match:
        raise ValueError(f"番号の配列が見つかりません: {text!r}")
    return [int(i) for i in json.loads(match.group(0))]


def llm_pick(papers: list[Paper], n: int, model: str) -> list[Paper]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "ANTHROPIC_API_KEY が無いのでヒューリスティック選定にします",
            file=sys.stderr,
        )
        return pick_diverse(papers, n)
    try:
        indices = _parse_indices(_call_claude(_build_prompt(papers, n), model, api_key))
    except Exception as ex:  # noqa: BLE001
        print(
            f"LLM選定に失敗（{ex}）。ヒューリスティックに切り替えます", file=sys.stderr
        )
        return pick_diverse(papers, n)
    picked = [papers[i] for i in indices if 0 <= i < len(papers)][:n]
    return picked or pick_diverse(papers, n)
