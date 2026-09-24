"""J-STAGE から「ジャンル問わず面白そうな論文」を数件拾ってくる。

方針:
  * AI要約は一切しない。著者が書いた抄録をそのまま出す（読む練習なので）。
  * ランダムな日常語を種に J-STAGE WebAPI（記事検索）を叩き、候補を集める。
  * 各候補の記事ページから抄録を取り、ヒューリスティックで「読み物として面白そうか」を採点。
  * 上位を分野が被らないように選び、読みやすいHTMLにして開く。

J-STAGE WebAPI 利用規約: https://www.jstage.jst.go.jp/static/pages/WebAPI/-char/ja
  非営利・個人利用の範囲で、リクエストは少数・間隔を空けて行う設計にしています。
"""

from jstage_picker.cli import main

__all__ = ["main"]
