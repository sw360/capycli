# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

import responses

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
