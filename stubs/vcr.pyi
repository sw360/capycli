class Cassette:
    def load(cls, **kwargs: int):
        ...


class VCR:
    def use_cassette(self, path=None, **kwargs: int) -> Cassette:
        ...
