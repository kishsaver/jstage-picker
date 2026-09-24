"""J-STAGE WebAPI（記事検索）と記事ページのパース。"""

import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from jstage_picker.config import SEARCH_API
from jstage_picker.models import ArticleInfo, Paper

NS = {
    "a": "http://www.w3.org/2005/Atom",
    "prism": "http://prismstandard.org/namespaces/basic/2.0/",
}


# ---------------------------------------------------------------- 検索API
def search_url(seed: str, year_from: int, year_to: int, count: int) -> str:
    query = {
        "service": 3,
        "article": seed,
        "pubyearfrom": year_from,
        "pubyearto": year_to,
        "count": count,
    }
    return SEARCH_API + "?" + urllib.parse.urlencode(query)


def _text(el: ET.Element, path: str) -> str:
    x = el.find(path, NS)
    return x.text.strip() if x is not None and x.text else ""


def _ja_or_en(el: ET.Element, path: str) -> str:
    return _text(el, f"{path}/a:ja") or _text(el, f"{path}/a:en")


def _authors(entry: ET.Element) -> list[str]:
    for lang in ("ja", "en"):
        names = [
            n.text.strip()
            for n in entry.findall(f"a:author/a:{lang}/a:n", NS)
            if n.text
        ]
        if names:
            return names
    return []


def parse_search(xml_text: str, seed: str) -> list[Paper]:
    root = ET.fromstring(xml_text)
    papers = []
    for entry in root.findall("a:entry", NS):
        title = _ja_or_en(entry, "a:article_title")
        url = _ja_or_en(entry, "a:article_link")
        if not title or not url:
            continue
        papers.append(
            Paper(
                title=title,
                url=url,
                journal=_ja_or_en(entry, "a:material_title"),
                year=_text(entry, "a:pubyear"),
                authors=_authors(entry),
                doi=_text(entry, "prism:doi"),
                seed=seed,
            )
        )
    return papers


# ---------------------------------------------------------------- 記事ページ
class _MetaParser(HTMLParser):
    """<meta name|property=... content=...> を集める。"""

    def __init__(self):
        super().__init__()
        self.meta: dict[str, list[str]] = {}

    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        a = dict(attrs)
        key = (a.get("name") or a.get("property") or "").lower()
        if key and a.get("content") is not None:
            self.meta.setdefault(key, []).append(a["content"])


def _first(meta: dict[str, list[str]], key: str) -> str:
    return (meta.get(key) or [""])[0]


def _extract_abstract(meta: dict[str, list[str]]) -> str:
    for key in ("abstract", "citation_abstract", "og:description"):
        value = _first(meta, key).strip()
        if value and value != "J-STAGE":  # og:description の既定値は除外
            return html.unescape(value)
    return ""


def _extract_keywords(meta: dict[str, list[str]]) -> list[str]:
    keywords = []
    for raw in meta.get("citation_keywords", []) + meta.get("keywords", []):
        keywords += [s.strip() for s in re.split(r"[,、;；]", raw) if s.strip()]
    return list(dict.fromkeys(keywords))  # 順序を保って重複除去


def _is_free(meta: dict[str, list[str]]) -> bool:
    return (
        "フリー" in _first(meta, "access_control")
        or "citation_fulltext_world_readable" in meta
    )


def parse_article(page: str) -> ArticleInfo:
    parser = _MetaParser()
    parser.feed(page)
    meta = parser.meta
    return ArticleInfo(
        abstract=_extract_abstract(meta),
        free=_is_free(meta),
        keywords=_extract_keywords(meta),
    )
