from typing import Any, List

class Cassette:
    def load(cls, **kwargs: int) -> Any:
        ...


class VCR:
    def use_cassette(self, path: str = "", **kwargs: int) -> Cassette:
        ...


def use_cassette(path: str = "", filter_headers: List[str] = [],
                 match_on: List[str] = [], record_mode: str = "none") -> Cassette:
    ...
