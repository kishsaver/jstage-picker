"""選ばれた論文を読みやすい HTML にする。"""

import re
from datetime import date
from html import escape
from string import Template

from jstage_picker.models import Paper

MAX_AUTHORS = 4
MAX_KEYWORDS = 6

CSS = """
:root{--bg:#f7f4ee;--fg:#222;--sub:#6b665c;--line:#ddd6c8;--acc:#7a3b1d}
@media (prefers-color-scheme:dark){:root{--bg:#1b1a17;--fg:#e8e4da;--sub:#a39d90;--line:#3a3731;--acc:#e0a07a}}
body{background:var(--bg);color:var(--fg);margin:0;font-family:"Hiragino Mincho ProN","Yu Mincho","Noto Serif JP",serif;line-height:2;}
main{max-width:40em;margin:0 auto;padding:3em 16px 5em}
header h1{font-size:1.1em;letter-spacing:.2em;color:var(--sub);font-weight:normal}
article{border-top:1px solid var(--line);padding:2.5em 0}
h2{font-size:1.35em;line-height:1.6;margin:.3em 0}
h2 a{color:var(--fg);text-decoration:none} h2 a:hover{color:var(--acc)}
.meta,.auth,.kw,.seed{font-family:system-ui,sans-serif;font-size:.8em;color:var(--sub)}
.free{color:var(--acc)}
.abs{font-size:1.05em;margin:1.2em 0;text-align:justify} .abs p{margin:0 0 1em;text-indent:1em}
footer{font-family:system-ui,sans-serif;font-size:.75em;color:var(--sub);border-top:1px solid var(--line);padding-top:1.5em}
footer a{color:var(--sub)}
"""

PAGE = Template("""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>今日の論文 $iso_date</title>
<style>$css</style></head><body><main>
<header><h1>今日の論文　$dotted_date</h1></header>
$cards
<footer>抄録は各著者によるもので、要約・加工はしていません。<br>
Powered by <a href="https://www.jstage.jst.go.jp/browse/-char/ja">J-STAGE</a></footer>
</main></body></html>""")

CARD = Template("""
<article>
  <div class="meta">$meta</div>
  <h2><a href="$url" target="_blank" rel="noopener">$title</a></h2>
  <div class="auth">$authors</div>
  <div class="abs">$abstract</div>
  $keywords
  <div class="seed">種語「$seed」から</div>
</article>""")


def _meta_line(p: Paper) -> str:
    free = '　<span class="free">無料で本文まで読める</span>' if p.free else ""
    return f"{escape(p.journal)}　{escape(p.year)}{free}"


def _authors_line(p: Paper) -> str:
    more = " ほか" if len(p.authors) > MAX_AUTHORS else ""
    return escape("、".join(p.authors[:MAX_AUTHORS])) + more


def _abstract_paragraphs(p: Paper) -> str:
    return "".join(
        f"<p>{escape(s)}</p>" for s in re.split(r"\n+", p.abstract) if s.strip()
    )


def _keywords_line(p: Paper) -> str:
    kw = " / ".join(escape(k) for k in p.keywords[:MAX_KEYWORDS])
    return f'<div class="kw">キーワード：{kw}</div>' if kw else ""


def render_card(p: Paper) -> str:
    return CARD.substitute(
        meta=_meta_line(p),
        url=escape(p.url),
        title=escape(p.title),
        authors=_authors_line(p),
        abstract=_abstract_paragraphs(p),
        keywords=_keywords_line(p),
        seed=escape(p.seed),
    )


def render_html(picks: list[Paper], today: date | None = None) -> str:
    today = today or date.today()
    return PAGE.substitute(
        iso_date=today.isoformat(),
        dotted_date=f"{today:%Y.%m.%d}",
        css=CSS,
        cards="".join(render_card(p) for p in picks),
    )
