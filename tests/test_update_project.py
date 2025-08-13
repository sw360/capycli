from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

from cyclonedx.model.bom import Bom
from pytest import fixture, raises
from sw360 import SW360Error

from capycli.main.result_codes import ResultCode
from capycli.project.create_project import CreateProject

IRRELEVANT_STR = "irrelevant"
IRRELEVANT_DICT = {"irrelevant": "data"}
IRRELEVANT_BOM = Bom()


class DummyComponent:
    """Dummy class to simulate a component in a BOM."""
    def __init__(self, name: str, version: str, props: dict[str, Any] = {}) -> None:
        self.name = name
        self.version = version
        self.properties = props or {}


class DummyBom:
    """Dummy class to simulate a Bill of Materials (BOM)."""
    def __init__(self, components: list[DummyComponent]) -> None:
        self.components = components


def make_project(additional_data: dict[str, Any] = {}, embedded_releases: dict[str, Any] = {}) -> dict[str, Any]:
    """Helper function to create a SW360-like Project dictionary with optional additional data
    and embedded releases."""

    result = {
        "additionalData": additional_data or {},
        "_embedded": {"sw360:releases": [{}]} if embedded_releases else {},
    }
    return result


def make_sbom() -> DummyBom:
    """Helper function to create a dummy SBOM with a single dummy component."""
    comp = DummyComponent("Dummy Component 1", "1.2.3", props={})
    return DummyBom([comp])


class DummyResp:
    status_code = 500
    text = "server error"


@fixture
def dummy_response() -> Callable[[int, str], Callable[[int, str], MagicMock]]:
    """Fixture to create a dummy response object."""
    def _dummy_response(status_code: int, text: str) -> Callable[[int, str], MagicMock]:
        result = MagicMock()
        result.status_code = status_code
        result.text = text
        return result
    return _dummy_response


@fixture
def sut() -> CreateProject:
    """Fixture to create an instance of CreateProject with a mocked client."""
    cp = CreateProject()
    cp.client = MagicMock()
    return cp


@fixture
def patched_print_text() -> Any:
    """Fixture to patch the print_text function."""
    return patch("capycli.project.create_project.print_text")


@fixture
def patched_print_red() -> Any:
    """Fixture to patch the print_red function."""
    return patch("capycli.project.create_project.print_red")


@fixture
def patched_print_yellow() -> Any:
    """Fixture to patch the print_yellow function."""
    return patch("capycli.project.create_project.print_yellow")


@fixture
def patched_get_app_signature() -> Callable[[Any], Any]:
    """Fixture to patch the get_app_signature function."""
    def _patch_get_app_signature(what_to_return: Any) -> Any:
        return patch("capycli.get_app_signature", return_value=what_to_return)
    return _patch_get_app_signature


@fixture
def patched_bom_to_release_list() -> Any:
    """Fixture to patch the bom_to_release_list method."""
    return patch("capycli.project.create_project.CreateProject.bom_to_release_list", return_value=MagicMock())


@fixture
def patched_merge_project_mainline_states() -> Any:
    """Fixture to patch the merge_project_mainline_states method."""
    return patch("capycli.project.create_project.CreateProject.merge_project_mainline_states", return_value=MagicMock())


@fixture
def dummy_project() -> dict[str, Any]:
    """Fixture to create a dummy project dictionary."""
    return make_project()


@fixture
def dummy_project_info() -> dict[str, Any]:
    """Fixture to create a dummy project info dictionary."""
    return {"foo": "bar"}


class TestUpdateProject():
    """Test suite for the CreateProject.update_project method."""

    def test_update_project_no_client(self) -> None:
        """Test that update_project raises SystemExit with RESULT_ERROR_ACCESSING_SW360
        when the client is not set."""
        sut = CreateProject()
        sut.client = None
        with raises(SystemExit) as e:
            sut.update_project(IRRELEVANT_STR, IRRELEVANT_DICT, IRRELEVANT_BOM, IRRELEVANT_DICT)
        assert e.value.code == ResultCode.RESULT_ERROR_ACCESSING_SW360

    def test_update_project_additionalData_createdWith_added(self, sut: CreateProject,
                                                             patched_print_text: Any,
                                                             patched_print_yellow: Any,
                                                             patched_print_red: Any,
                                                             patched_get_app_signature: Any,
                                                             patched_bom_to_release_list: Any,
                                                             dummy_project: dict[str, Any],
                                                             dummy_project_info: dict[str, Any]) -> None:
        """Test that 'createdWith' is added to additionalData with
        the expected CaPyCLI value. The project exists."""

        with (patched_print_text,
              patched_print_red,
              patched_print_yellow,
              patched_get_app_signature("v1.2.3"),
              patched_bom_to_release_list):
            sut.update_project(IRRELEVANT_STR, dummy_project, IRRELEVANT_BOM, dummy_project_info)

        assert dummy_project_info["foo"] == "bar"
        assert dummy_project_info["additionalData"]["createdWith"] == "v1.2.3"

    def test_update_project_additionalData_createdWith_added_no_project(
            self, sut: CreateProject,
            patched_print_text: Any,
            patched_print_yellow: Any,
            patched_print_red: Any,
            patched_get_app_signature: Any,
            patched_bom_to_release_list: Any) -> None:
        """Test that 'createdWith' is added to additionalData with
        the expected CaPyCLI value. The project does not exist."""
        dummy_project_info: dict[str, Any] = {"foo": "bar", "additionalData": {"dummyKey": "dummyValue"}}

        with (patched_print_text,
              patched_print_red,
              patched_print_yellow,
              patched_get_app_signature("v1.2.3"),
              patched_bom_to_release_list):
            sut.update_project(IRRELEVANT_STR, None, IRRELEVANT_BOM, dummy_project_info)

        assert dummy_project_info["foo"] == "bar"
        assert "dummyKey" not in dummy_project_info["additionalData"]
        assert dummy_project_info["additionalData"]["createdWith"] == "v1.2.3"

    def test_update_project_update_project_releases_error(self,
                                                          patched_print_text: Any,
                                                          patched_print_yellow: Any,
                                                          patched_print_red: Any,
                                                          patched_get_app_signature: Any,
                                                          patched_bom_to_release_list: Any,
                                                          dummy_project: dict[str, Any],
                                                          dummy_project_info: dict[str, Any]) -> None:
        """Test that an error in updating project releases generates the expected error message."""
        sut = CreateProject()
        sut.client = MagicMock()
        sut.client.update_project_releases.return_value = False

        with (patched_print_text,
              patched_print_red as ppr,
              patched_print_yellow,
              patched_get_app_signature(IRRELEVANT_STR),
              patched_bom_to_release_list):
            sut.update_project(IRRELEVANT_STR, dummy_project, IRRELEVANT_BOM, dummy_project_info)
            ppr.assert_any_call("  Error updating project releases!")

    def test_update_project_update_project_error(self,
                                                 patched_print_text: Any,
                                                 patched_print_yellow: Any,
                                                 patched_print_red: Any,
                                                 patched_get_app_signature: Any,
                                                 patched_bom_to_release_list: Any,
                                                 dummy_project: dict[str, Any],
                                                 dummy_project_info: dict[str, Any]) -> None:
        """Test that an error in updating the project generates the expected error message."""
        sut = CreateProject()
        sut.client = MagicMock()
        sut.client.update_project.return_value = False

        with (patched_print_text,
              patched_print_red as ppr,
              patched_print_yellow,
              patched_get_app_signature(IRRELEVANT_STR),
              patched_bom_to_release_list):
            sut.update_project(IRRELEVANT_STR, dummy_project, IRRELEVANT_BOM, dummy_project_info)
            ppr.assert_any_call("  Error updating project!")

    def test_update_project_sw360error_no_response(self,
                                                   patched_print_text: Any,
                                                   patched_print_yellow: Any,
                                                   patched_print_red: Any,
                                                   patched_get_app_signature: Any,
                                                   patched_bom_to_release_list: Any,
                                                   dummy_project: dict[str, Any],
                                                   dummy_project_info: dict[str, Any]) -> None:
        """Test that a SW360Error with no response generates the expected error message."""
        sut = CreateProject()
        sut.client = MagicMock()
        sut.client.update_project_releases.side_effect = SW360Error(message="Dummy Unknown Error message")

        with (patched_print_text,
              patched_print_red as ppr,
              patched_print_yellow,
              patched_get_app_signature(IRRELEVANT_STR),
              patched_bom_to_release_list,
              raises(SystemExit) as e):
            sut.update_project(IRRELEVANT_STR, dummy_project, IRRELEVANT_BOM, dummy_project_info)

        assert e.value.code == ResultCode.RESULT_AUTH_ERROR
        ppr.assert_any_call("  Unknown error: Dummy Unknown Error message")

    def test_update_project_sw360error_unauthorized(self,
                                                    patched_print_text: Any,
                                                    patched_print_yellow: Any,
                                                    patched_print_red: Any,
                                                    patched_get_app_signature: Any,
                                                    patched_bom_to_release_list: Any,
                                                    dummy_project: dict[str, Any],
                                                    dummy_project_info: dict[str, Any],
                                                    dummy_response: Any) -> None:
        """Test that a SW360Error with status code 401 generates the expected error message."""
        sut = CreateProject()
        sut.client = MagicMock()
        sut.client.update_project_releases.side_effect = SW360Error(response=dummy_response(401, "unauthorized"))
        with (patched_print_text,
              patched_print_red as ppr,
              patched_print_yellow,
              patched_get_app_signature(IRRELEVANT_STR),
              patched_bom_to_release_list,
              raises(SystemExit) as e):
            sut.update_project(IRRELEVANT_STR, dummy_project, IRRELEVANT_BOM, dummy_project_info)
        assert e.value.code == ResultCode.RESULT_AUTH_ERROR
        ppr.assert_any_call("  You are not authorized!")

    def test_update_project_sw360error_forbidden(self,
                                                 patched_print_text: Any,
                                                 patched_print_yellow: Any,
                                                 patched_print_red: Any,
                                                 patched_get_app_signature: Any,
                                                 patched_bom_to_release_list: Any,
                                                 dummy_project: dict[str, Any],
                                                 dummy_project_info: dict[str, Any],
                                                 dummy_response: Any) -> None:
        """Test that a SW360Error with status code 403 generates the expected error message."""
        sut = CreateProject()
        sut.client = MagicMock()
        sut.client.update_project_releases.side_effect = SW360Error(response=dummy_response(403, "forbidden"))

        with (patched_print_text,
              patched_print_red as ppr,
              patched_print_yellow,
              patched_get_app_signature(IRRELEVANT_STR),
              patched_bom_to_release_list,
              raises(SystemExit) as e):
            sut.update_project(IRRELEVANT_STR, dummy_project, IRRELEVANT_BOM, dummy_project_info)
        assert e.value.code == ResultCode.RESULT_AUTH_ERROR
        ppr.assert_any_call("  You are not authorized - do you have a valid write token?")

    def test_update_project_sw360error_other_status(self,
                                                    patched_print_text: Any,
                                                    patched_print_yellow: Any,
                                                    patched_print_red: Any,
                                                    patched_get_app_signature: Any,
                                                    patched_bom_to_release_list: Any,
                                                    dummy_project: dict[str, Any],
                                                    dummy_project_info: dict[str, Any],
                                                    dummy_response: Any) -> None:
        """Test that a SW360Error with a status code other than 401 or 403 generates the expected error message."""
        sut = CreateProject()
        sut.client = MagicMock()
        sut.client.update_project_releases.side_effect = SW360Error(response=dummy_response(500, "server error"))

        with (patched_print_text,
              patched_print_red as ppr,
              patched_print_yellow,
              patched_get_app_signature(IRRELEVANT_STR),
              patched_bom_to_release_list,
              raises(SystemExit) as e):
            sut.update_project(IRRELEVANT_STR, dummy_project, IRRELEVANT_BOM, dummy_project_info)
        assert e.value.code == ResultCode.RESULT_ERROR_ACCESSING_SW360
        ppr.assert_any_call("  500: server error")
