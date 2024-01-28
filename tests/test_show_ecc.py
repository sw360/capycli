# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
from typing import Any, Dict

import responses

from capycli.main.result_codes import ResultCode
from capycli.project.show_ecc import ShowExportControlStatus
from tests.test_base import AppArguments, TestBase


class TestShowExportControlStatus(TestBase):
    OUTPUTFILE = "output.json"

    def test_show_help(self) -> None:
        sut = ShowExportControlStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("ecc")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli project ecc" in out)

    @responses.activate
    def test_no_login(self) -> None:
        sut = ShowExportControlStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("ecc")
        args.sw360_url = "https://myserver.com"
        args.debug = True
        args.verbose = True

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_AUTH_ERROR, ex.code)

    @responses.activate
    def test_no_project_identification(self) -> None:
        sut = ShowExportControlStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("ecc")
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
        sut = ShowExportControlStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("ecc")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True
        args.id = "34ef5c5452014c52aa9ce4bc180624d8"

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
    def test_project_ecc_by_id(self) -> None:
        sut = ShowExportControlStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("ecc")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True
        args.id = "p001"

        self.add_login_response()

        # the project
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/p001",
            json=self.get_project_for_test(),
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
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r002",
            json=self.get_release_cli_for_test(),
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Retrieving project details..." in out)

        self.assertTrue("Project name: CaPyCLI, 1.9.0" in out)
        self.assertTrue("Project responsible: thomas.graf@siemens.com" in out)
        self.assertTrue("Project owner: thomas.graf@siemens.com" in out)
        self.assertTrue("Clearing state: IN_PROGRESS" in out)
        self.assertTrue("No linked projects" in out)
        self.assertTrue("cli-support, 1.3: ECC status=APPROVED, ECCN=N, AL=N" in out)
        self.assertTrue("wheel, 0.38.4: ECC status=APPROVED, ECCN=N, AL=N" in out)

    @responses.activate
    def test_project_ecc_by_name(self) -> None:
        sut = ShowExportControlStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("ecc")
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
        release = self.get_release_wheel_for_test()
        del release["eccInformation"]
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r001",
            json=release,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the second release, force state as open without source code
        release = self.get_release_cli_for_test()
        release["eccInformation"]["al"] = ""
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
        self.assertTrue("Retrieving project details..." in out)

        self.assertTrue("Project name: CaPyCLI, 1.9.0" in out)
        self.assertTrue("Project responsible: thomas.graf@siemens.com" in out)
        self.assertTrue("Project owner: thomas.graf@siemens.com" in out)
        self.assertTrue("Clearing state: IN_PROGRESS" in out)
        self.assertTrue("No linked projects" in out)
        self.assertTrue("cli-support, 1.3: ECC status=APPROVED, ECCN=N, AL=" in out)
        self.assertTrue("wheel, 0.38.4: ECC status not approved or no ECC status at all" in out)

        self.assertTrue(os.path.isfile(self.OUTPUTFILE), "no output file generated")
        self.delete_file(self.OUTPUTFILE)

    @responses.activate
    def test_project_show_ecc_with_subproject(self) -> None:
        sut = ShowExportControlStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("ecc")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True
        args.id = "p001"
        args.cyclonedx = True

        self.add_login_response()

        # the project, with sub-project
        project = self.get_project_for_test()
        subproject: Dict[str, Any] = {}
        subproject["name"] = "sub-project-dummy"
        subproject["version"] = "2.0.1"
        subproject["securityResponsibles"] = []
        subproject["projectType"] = "PRODUCT"
        subproject["visibility"] = "EVERYONE"
        subproject["_links"] = {}
        subproject["_links"]["self"] = {}
        subproject["_links"]["self"]["href"] = self.MYURL + "resource/api/projects/p002"
        project["_embedded"]["sw360:projects"] = []
        project["_embedded"]["sw360:projects"].append(subproject)
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
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r002",
            json=self.get_release_cli_for_test(),
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Retrieving project details..." in out)

        self.assertTrue("Project name: CaPyCLI, 1.9.0" in out)
        self.assertTrue("Project responsible: thomas.graf@siemens.com" in out)
        self.assertTrue("Project owner: thomas.graf@siemens.com" in out)
        self.assertTrue("Clearing state: IN_PROGRESS" in out)
        self.assertTrue("Linked projects:" in out)
        self.assertTrue("sub-project-dummy, 2.0.1" in out)
        self.assertTrue("cli-support, 1.3: ECC status=APPROVED, ECCN=N, AL=N" in out)


if __name__ == "__main__":
    APP = TestShowExportControlStatus()
    APP.setUp()
    APP.test_project_ecc_by_id()
