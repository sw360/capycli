from typing import Any

from .base import BaseMixin

class ClearingMixin(BaseMixin):
    def get_clearing_request(self, request_id: str) -> dict[str, Any] | None: ...
    def get_clearing_request_for_project(self, project_id: str) -> dict[str, Any] | None: ...
