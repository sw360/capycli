from typing import List


class Cassette:
    def load(cls, **kwargs: int):
        ...


class VCR:
    def use_cassette(self, path=None, **kwargs: int) -> Cassette:
        ...


def use_cassette(self, path: str = "", filter_headers: List[str] = [],
                 match_on: List[str] = [], record_mode: str = "none") -> Cassette:
    ...
