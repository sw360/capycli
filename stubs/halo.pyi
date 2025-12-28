# https://github.com/manrajgrover/halo/

from typing import Any, Optional

class Halo(object):
    def __init__(self, text: str = ..., spinner: Any = ...) -> None:
        ...

    def clear(self) -> "Halo":
        ...

    def start(self) -> "Halo":
        ...

    def stop(self) -> "Halo":
        ...

    def succeed(self, text: Optional[str] = ...) -> "Halo":
        ...

    @property
    def text(self) -> str:
        ...

    @text.setter
    def text(self, value: str) -> None:
        ...
