# https://github.com/madpah/requirements-parser

from typing import Iterator, List, TextIO, Union


class Requirement:
    line: str
    editable: bool
    local_file: bool
    specifier: bool
    vcs: str = ""
    name: str = ""
    subdirectory: str = ""
    uri: str = ""
    path: str = ""
    revision: str = ""
    hash_name: str = ""
    hash: str = ""
    extras: List[str] = []
    specs: List[str] = []
    ...


def parse(reqstr: Union[str, TextIO]) -> Iterator[Requirement]:
    ...
