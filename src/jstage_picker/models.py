from dataclasses import dataclass, field


@dataclass
class ArticleInfo:
    """記事ページから取れる追加情報。"""

    abstract: str = ""
    free: bool = False
    keywords: list[str] = field(default_factory=list)


@dataclass
class Paper:
    title: str
    url: str
    journal: str
    year: str
    authors: list[str]
    doi: str
    seed: str
    abstract: str = ""
    free: bool = False
    keywords: list[str] = field(default_factory=list)
    score: float = 0.0

    def apply(self, info: ArticleInfo) -> None:
        self.abstract = info.abstract
        self.free = info.free
        self.keywords = info.keywords
