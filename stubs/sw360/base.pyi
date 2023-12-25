from _typeshed import Incomplete
from typing import Any

class BaseMixin:
    url: Incomplete
    session: Incomplete
    api_headers: Incomplete
    force_no_session: bool
    def __init__(self, url: str, token: str, oauth2: bool = False) -> None: ...
    def api_get(self, url: str = "") -> dict[str, Any] | None: ...
    @classmethod
    def get_id_from_href(cls, href: str) -> str: ...
