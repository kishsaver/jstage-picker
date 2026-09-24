"""J-STAGE へ行儀よくアクセスするための HTTP クライアント。"""

import time
import urllib.request

from jstage_picker.config import REQUEST_INTERVAL, REQUEST_TIMEOUT, USER_AGENT


class PoliteClient:
    """リクエストごとに一定間隔を空ける（成功・失敗を問わず）。"""

    def __init__(
        self, interval: float = REQUEST_INTERVAL, timeout: int = REQUEST_TIMEOUT
    ):
        self.interval = interval
        self.timeout = timeout
        self._last = 0.0

    def get(self, url: str) -> str:
        self._wait()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                charset = r.headers.get_content_charset() or "utf-8"
                return r.read().decode(charset, errors="replace")
        finally:
            self._last = time.monotonic()

    def _wait(self) -> None:
        remaining = self._last + self.interval - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)
