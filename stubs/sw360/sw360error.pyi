from _typeshed import Incomplete
from requests import Response as Response

class SW360Error(IOError):
    message: Incomplete
    response: Incomplete
    url: Incomplete
    details: Incomplete
    def __init__(self, response: Response | None = None, url: str = "", message: str = "") -> None: ...
