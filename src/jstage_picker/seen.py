"""既読 DOI の記録。本文やメタデータは保存しない。"""

from pathlib import Path

from jstage_picker.models import Paper


class SeenStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> set[str]:
        return set(self.path.read_text().split()) if self.path.exists() else set()

    def add(self, papers: list[Paper]) -> None:
        with self.path.open("a") as f:
            f.writelines(p.doi + "\n" for p in papers if p.doi)
