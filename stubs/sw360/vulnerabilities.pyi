from typing import Any

from .base import BaseMixin

class VulnerabilitiesMixin(BaseMixin):
    def get_all_vulnerabilities(self) -> dict[str, Any] | None: ...
    def get_vulnerability(self, vulnerability_id: str) -> dict[str, Any] | None: ...
