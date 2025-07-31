import pytest
from capycli.main.result_codes import ResultCode
from capycli.project.create_project import CreateProject

IRRELEVANT = "irrelevant"


class TestUpdateProject():

    def test_update_project_no_client(self):
        """Test that update_project raises SystemExit with RESULT_ERROR_ACCESSING_SW360
        when the client is not set."""
        sut = CreateProject()
        sut.client = None
        with pytest.raises(SystemExit) as e:
            sut.update_project(IRRELEVANT, IRRELEVANT, IRRELEVANT, IRRELEVANT)
        assert e.value.code == ResultCode.RESULT_ERROR_ACCESSING_SW360
