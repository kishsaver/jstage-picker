"""アプリ全体で共有する定数。"""

from pathlib import Path

USER_AGENT = "jstage-pick/1.0 (personal, non-commercial reading tool)"
REQUEST_INTERVAL = 1.5  # 秒。J-STAGE に負荷をかけないための間隔
REQUEST_TIMEOUT = 20  # 秒

SEARCH_API = "https://api.jstage.jst.go.jp/searchapi/do"
SEARCH_COUNT = 100  # 1回の検索で取得する件数

SEEN_FILE = (
    Path.home() / ".jstage_pick_seen.txt"
)  # 既読のDOIだけ記録（本文やメタデータは保存しない）

POOL_SIZE = 25  # 最終選定にかける上位候補数
