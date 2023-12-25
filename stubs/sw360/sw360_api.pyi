from _typeshed import Incomplete
from typing import Any

from .attachments import AttachmentsMixin
from .clearing import ClearingMixin
from .components import ComponentsMixin
from .license import LicenseMixin
from .project import ProjectMixin
from .releases import ReleasesMixin
from .vendor import VendorMixin
from .vulnerabilities import VulnerabilitiesMixin

class SW360(
    AttachmentsMixin, ClearingMixin, ComponentsMixin, LicenseMixin, ProjectMixin, ReleasesMixin, VendorMixin, VulnerabilitiesMixin
):
    url: Incomplete
    session: Incomplete
    api_headers: Incomplete
    force_no_session: bool
    def __init__(self, url: str, token: str, oauth2: bool = False) -> None: ...
    def login_api(self, token: str = "") -> bool: ...
    def close_api(self) -> None: ...
    def api_get_raw(self, url: str = "") -> str: ...
    def get_health_status(self) -> dict[str, Any] | None: ...
