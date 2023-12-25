from typing import Any

from .base import BaseMixin

class ComponentsMixin(BaseMixin):
    def get_all_components(
        self, fields: str = "", page: int = -1, page_size: int = -1, all_details: bool = False, sort: str = ""
    ) -> Any: ...
    def get_components_by_type(self, component_type: str) -> list[dict[str, Any]]: ...
    def get_component(self, component_id: str) -> dict[str, Any] | None: ...
    def get_component_by_url(self, component_url: str) -> dict[str, Any] | None: ...
    def get_component_by_name(self, component_name: str) -> dict[str, Any] | None: ...
    def get_components_by_external_id(self, ext_id_name: str, ext_id_value: str = "") -> list[dict[str, Any]]: ...
    def create_new_component(
        self, name: str, description: str, component_type: str, homepage: str, component_details: dict[str, Any] = {}
    ) -> dict[str, Any] | None: ...
    def update_component(self, component: dict[str, Any], component_id: str) -> dict[str, Any] | None: ...
    def update_component_external_id(
        self, ext_id_name: str, ext_id_value: str, component_id: str, update_mode: str = "none"
    ) -> dict[str, Any] | None: ...
    def delete_component(self, component_id: str) -> dict[str, Any] | None: ...
    def get_users_of_component(self, component_id: str) -> dict[str, Any] | None: ...