# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
from typing import Any

import pytest
import responses
from cyclonedx.model import ExternalReferenceType

from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.main.result_codes import ResultCode
from capycli.project.create_bom import CreateBom
from tests.test_base import AppArguments, TestBasePytest


class TestCreateBom(TestBasePytest):
    OUTPUTFILE = "output.json"

    def test_show_help(self) -> None:
        sut = CreateBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createbom")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        assert "usage: CaPyCli project createbom" in out

    @responses.activate
    def test_no_login(self) -> None:
        sut = CreateBom()

        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createbom")
        args.sw360_url = "https://my.server.com"
        args.debug = True
        args.verbose = True

        with pytest.raises(SystemExit) as ex:
            sut.run(args)
        assert ResultCode.RESULT_AUTH_ERROR == ex.value.code

    @responses.activate
    def test_no_output_file(self) -> None:
        sut = CreateBom()

        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createbom")
        args.sw360_token = TestBasePytest.MYTOKEN
        args.sw360_url = TestBasePytest.MYURL
        args.debug = True
        args.verbose = True

        self.add_login_response()

        with pytest.raises(SystemExit) as ex:
            sut.run(args)
        assert ResultCode.RESULT_COMMAND_ERROR == ex.value.code

    @responses.activate
    def test_no_project_identification(self) -> None:
        sut = CreateBom()

        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createbom")
        args.debug = True
        args.verbose = True
        args.sw360_token = TestBasePytest.MYTOKEN
        args.sw360_url = TestBasePytest.MYURL

        self.add_login_response()

        with pytest.raises(SystemExit) as ex:
            sut.run(args)
        assert ResultCode.RESULT_COMMAND_ERROR == ex.value.code

    @responses.activate
    def test_project_not_found(self) -> None:
        sut = CreateBom()

        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createbom")
        args.sw360_token = TestBasePytest.MYTOKEN
        args.sw360_url = TestBasePytest.MYURL
        args.debug = True
        args.verbose = True
        args.id = "34ef5c5452014c52aa9ce4bc180624d8"
        args.outputfile = self.OUTPUTFILE

        self.add_login_response()

        # purl cache: components
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/34ef5c5452014c52aa9ce4bc180624d8",
            body="""{}""",
            status=404,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        with pytest.raises(SystemExit) as ex:
            sut.run(args)
        assert ResultCode.RESULT_ERROR_ACCESSING_SW360 == ex.value.code

    @responses.activate
    def test_create_bom_multiple_purls(self, capsys: Any) -> None:
        sut = CreateBom()

        self.add_login_response()
        sut.login(token=TestBasePytest.MYTOKEN, url=TestBasePytest.MYURL)

        # the first release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r001",
            json=self.get_release_wheel_for_test(),
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the second release
        release = self.get_release_cli_for_test()
        # use a specific purl
        release["externalIds"]["package-url"] = "[\"pkg:deb/debian/cli-support@1.3-1\",\"pkg:pypi/cli-support@1.3\"]"
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r002",
            json=release,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        cdx_components = sut.create_project_bom(self.get_project_for_test())
        captured = capsys.readouterr()

        assert "Stored them in property purl_list" in captured.out
        assert cdx_components[0].purl is None
        purl_raw = CycloneDxSupport.get_property(cdx_components[0], "purl_list").value
        assert purl_raw == "pkg:deb/debian/cli-support@1.3-1 pkg:pypi/cli-support@1.3"

    @responses.activate
    def test_project_by_id(self) -> None:
        sut = CreateBom()

        self.add_login_response()
        sut.login(token=TestBasePytest.MYTOKEN, url=TestBasePytest.MYURL)

        # the project
        project = self.get_project_for_test()
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/p001",
            json=project,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the first release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r001",
            json=self.get_release_wheel_for_test(),
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the second release
        release = self.get_release_cli_for_test()
        # use a specific purl
        release["externalIds"]["package-url"] = "pkg:deb/debian/cli-support@1.3-1"
        # add a SOURCE_SELF attachment
        release["_embedded"]["sw360:attachments"].append({
            "filename": "clipython-repacked-for-fun.zip",
            "sha1": "face4b90d134e2a2bcf9464c50ea086f849a9b82",
            "attachmentType": "SOURCE_SELF",
            "_links": {
                "self": {
                    "href": "https://my.server.com/resource/api/attachments/r002a002"
                }
            }
        })
        release["_embedded"]["sw360:attachments"].append({
            "filename": "clipython-1.3.0.docx",
            "sha1": "f0d8f2ddd017bdeaecbaec72ff76a6c0a045ec66",
            "attachmentType": "CLEARING_REPORT",
            "_links": {
                "self": {
                    "href": "https://my.server.com/resource/api/attachments/r002a003"
                }
            }
        })

        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r002",
            json=release,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        cdx_bom = sut.create_project_cdx_bom("p001")
        cx_comp = cdx_bom.components[0]
        assert cx_comp.purl.to_string() == release["externalIds"]["package-url"]

        ext_refs = [e for e in cx_comp.external_references if e.comment == CaPyCliBom.SOURCE_URL_COMMENT]
        assert len(ext_refs) == 1
        assert str(ext_refs[0].url) == release["sourceCodeDownloadurl"]
        assert ext_refs[0].type == ExternalReferenceType.DISTRIBUTION

        ext_refs = [e for e in cx_comp.external_references if e.comment == CaPyCliBom.SOURCE_FILE_COMMENT]
        assert len(ext_refs) == 2
        assert str(ext_refs[0].url) == release["_embedded"]["sw360:attachments"][0]["filename"]
        assert ext_refs[0].type == ExternalReferenceType.DISTRIBUTION
        assert ext_refs[0].hashes[0].alg == "SHA-1"
        assert ext_refs[0].hashes[0].content == release["_embedded"]["sw360:attachments"][0]["sha1"]

        ext_refs = [e for e in cx_comp.external_references
                    if e.comment and e.comment.startswith(CaPyCliBom.CLI_FILE_COMMENT)]
        assert len(ext_refs) == 1
        assert str(ext_refs[0].url) == release["_embedded"]["sw360:attachments"][1]["filename"]
        assert ext_refs[0].type == ExternalReferenceType.OTHER
        assert ext_refs[0].comment, CaPyCliBom.CLI_FILE_COMMENT + " == sw360Id: r002a002"
        assert ext_refs[0].hashes[0].alg == "SHA-1"
        assert ext_refs[0].hashes[0].content == release["_embedded"]["sw360:attachments"][1]["sha1"]

        ext_refs = [e for e in cx_comp.external_references
                    if e.comment and e.comment.startswith(CaPyCliBom.CRT_FILE_COMMENT)]
        assert len(ext_refs) == 1
        assert str(ext_refs[0].url) == release["_embedded"]["sw360:attachments"][3]["filename"]
        assert ext_refs[0].comment, CaPyCliBom.CRT_FILE_COMMENT + " == sw360Id: r002a003"
        assert ext_refs[0].type == ExternalReferenceType.OTHER
        assert ext_refs[0].hashes[0].alg == "SHA-1"
        assert ext_refs[0].hashes[0].content == release["_embedded"]["sw360:attachments"][3]["sha1"]

        ext_refs = [e for e in cx_comp.external_references if e.type == ExternalReferenceType.VCS]
        assert len(ext_refs) == 1
        assert str(ext_refs[0].url) == release["repository"]["url"]

        prj_ml_state = CycloneDxSupport.get_property(cx_comp, CycloneDxSupport.CDX_PROP_PROJ_STATE)
        assert prj_ml_state.value == "MAINLINE"
        releaseRelation = CycloneDxSupport.get_property(cx_comp, CycloneDxSupport.CDX_PROP_PROJ_RELATION)
        assert releaseRelation.value == "DYNAMICALLY_LINKED"

        prj_ml_state = CycloneDxSupport.get_property(cdx_bom.components[1], CycloneDxSupport.CDX_PROP_PROJ_STATE)
        assert prj_ml_state.value == "SPECIFIC"
        releaseRelation = CycloneDxSupport.get_property(cdx_bom.components[1], CycloneDxSupport.CDX_PROP_PROJ_RELATION)
        assert releaseRelation.value == "UNKNOWN"

        assert cdx_bom.metadata.component is not None
        if cdx_bom.metadata.component:
            assert cdx_bom.metadata.component.name == project["name"]
            assert cdx_bom.metadata.component.version == project["version"]
            assert cdx_bom.metadata.component.description == project["description"]

    @responses.activate
    def test_project_show_by_name(self) -> None:
        sut = CreateBom()

        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createbom")
        args.sw360_token = TestBasePytest.MYTOKEN
        args.sw360_url = TestBasePytest.MYURL
        args.debug = True
        args.verbose = True
        args.name = "CaPyCLI"
        args.version = "1.9.0"
        args.outputfile = self.OUTPUTFILE

        self.add_login_response()

        # projects by name
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects?name=CaPyCLI",
            body="""
            {
                "_embedded" : {
                    "sw360:projects" : [ {
                    "name" : "CaPyCLI",
                    "version" : "1.9.0",
                    "securityResponsibles" : [ ],
                    "considerReleasesFromExternalList" : false,
                    "projectType" : "PRODUCT",
                    "visibility" : "EVERYONE",
                    "_links" : {
                        "self" : {
                        "href" : "https://sw360.org/resource/api/projects/p001"
                        }
                    }
                    } ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the project
        project = self.get_project_for_test()
        project["linkedReleases"][1]["mainlineState"] = "OPEN"
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/p001",
            json=project,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the first release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r001",
            json=self.get_release_wheel_for_test(),
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the second release, force state as open without source code
        release = self.get_release_cli_for_test()
        release["clearingState"] = "OPEN"
        release["mainlineState"] = "OPEN"
        release["_embedded"]["sw360:attachments"][0]["attachmentType"] = "XXX"
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r002",
            json=release,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        self.delete_file(self.OUTPUTFILE)
        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")

        assert "Searching for project..." in out
        assert "Project name: CaPyCLI, 1.9.0" in out
        assert "cli-support 1.3" in out
        assert "wheel 0.38.4" in out

        assert os.path.isfile(self.OUTPUTFILE)
        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE)
        assert sbom is not None
        assert 2 == len(sbom.components)

        self.delete_file(self.OUTPUTFILE)


if __name__ == "__main__":
    APP = TestCreateBom()
    APP.test_project_show_by_name()
