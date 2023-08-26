# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

import responses
from cyclonedx.model import ExternalReferenceType

from capycli.common.capycli_bom_support import CaPyCliBom
from capycli.main.result_codes import ResultCode
from capycli.project.create_bom import CreateBom
from tests.test_base import AppArguments, TestBase


class TestCreateBom(TestBase):
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
        self.assertTrue("usage: CaPyCli project createbom" in out)

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

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_AUTH_ERROR, ex.code)

    @responses.activate
    def test_no_output_file(self) -> None:
        sut = CreateBom()

        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createbom")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True

        self.add_login_response()

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    @responses.activate
    def test_no_project_identification(self) -> None:
        sut = CreateBom()

        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createbom")
        args.debug = True
        args.verbose = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL

        self.add_login_response()

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    @responses.activate
    def test_project_not_found(self) -> None:
        sut = CreateBom()

        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createbom")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
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

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_ACCESSING_SW360, ex.code)

    @responses.activate
    def test_create_bom_multiple_purls(self):
        sut = CreateBom()

        self.add_login_response()
        sut.login(token=TestBase.MYTOKEN, url=TestBase.MYURL)

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

        out = self.capture_stdout(sut.create_project_bom, self.get_project_for_test())
        self.assertIn("Multiple purls added", out)

        # TODO self.capture_stdout doesn't allow us to get return value,
        # so re-run test. See also https://github.com/sw360/capycli/issues/39
        cdx_components = sut.create_project_bom(self.get_project_for_test())
        self.assertEqual(cdx_components[0].purl, "pkg:deb/debian/cli-support@1.3-1 pkg:pypi/cli-support@1.3")

    @responses.activate
    def test_project_by_id(self):
        sut = CreateBom()

        self.add_login_response()
        sut.login(token=TestBase.MYTOKEN, url=TestBase.MYURL)

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
        self.assertEqual(cx_comp.purl, release["externalIds"]["package-url"])

        ext_refs_src_url = [e for e in cx_comp.external_references if e.comment == CaPyCliBom.SOURCE_URL_COMMENT]
        self.assertEqual(len(ext_refs_src_url), 1)
        self.assertEqual(ext_refs_src_url[0].url, release["sourceCodeDownloadurl"])
        self.assertEqual(ext_refs_src_url[0].type, ExternalReferenceType.DISTRIBUTION)

        ext_refs_src_file = [e for e in cx_comp.external_references if e.comment == CaPyCliBom.SOURCE_FILE_COMMENT]
        self.assertEqual(len(ext_refs_src_file), 2)
        self.assertEqual(ext_refs_src_file[0].url, release["_embedded"]["sw360:attachments"][0]["filename"])
        self.assertEqual(ext_refs_src_file[0].type, ExternalReferenceType.DISTRIBUTION)
        self.assertEqual(ext_refs_src_file[0].hashes[0].alg, "SHA-1")
        self.assertEqual(ext_refs_src_file[0].hashes[0].content, release["_embedded"]["sw360:attachments"][0]["sha1"])

        ext_refs_vcs = [e for e in cx_comp.external_references if e.type == ExternalReferenceType.VCS]
        self.assertEqual(len(ext_refs_vcs), 1)
        self.assertEqual(ext_refs_vcs[0].url, release["repository"]["url"])

        self.assertEqual(cdx_bom.metadata.component.name, project["name"])
        self.assertEqual(cdx_bom.metadata.component.version, project["version"])
        self.assertEqual(cdx_bom.metadata.component.description, project["description"])

    @responses.activate
    def test_project_show_by_name(self):
        sut = CreateBom()

        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createbom")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
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

        self.assertTrue("Searching for project..." in out)
        self.assertTrue("Project name: CaPyCLI, 1.9.0" in out)
        self.assertTrue("cli-support 1.3" in out)
        self.assertTrue("wheel 0.38.4" in out)

        self.assertTrue(os.path.isfile(self.OUTPUTFILE))
        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE)
        self.assertIsNotNone(sbom)
        self.assertEqual(2, len(sbom.components))

        self.delete_file(self.OUTPUTFILE)


if __name__ == "__main__":
    APP = TestCreateBom()
    APP.test_project_show_by_name()
