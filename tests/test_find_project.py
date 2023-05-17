# -------------------------------------------------------------------------------
# Copyright (c) 2022-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import responses

from capycli.main.result_codes import ResultCode
from capycli.project.find_project import FindProject
from tests.test_base import AppArguments, TestBase


class TestFindProject(TestBase):
    def test_show_help(self) -> None:
        sut = FindProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("find")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli project find" in out)

    # @responses.activate
    def test_no_login(self) -> None:
        sut = FindProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("find")
        args.sw360_url = "https://my.server.com"
        args.debug = True
        args.verbose = True

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_AUTH_ERROR, ex.code)

    @responses.activate
    def test_no_project_identification(self) -> None:
        sut = FindProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("find")
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
        sut = FindProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("find")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True
        args.id = "007007"

        self.add_login_response()

        # purl cache: components
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/007007",
            body="""{}""",
            status=404,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Project with id 007007 not found!" in out)

    @responses.activate
    def test_project_find_by_id(self) -> None:
        sut = FindProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("find")
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

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Project found, name = CaPyCLI, version = 1.9.0" in out)

    @responses.activate
    def test_project_find_by_name_and_version(self):
        sut = FindProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("find")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True
        args.name = "CaPyCLI"
        args.version = "1.9.0"

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

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Searching for project..." in out)
        self.assertTrue("CaPyCLI, 1.9.0 => ID = p001" in out)

    @responses.activate
    def test_project_find_by_name(self):
        sut = FindProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("find")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True
        args.name = "CaPyCLI"

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
                        "projectType" : "PRODUCT",
                        "visibility" : "EVERYONE",
                        "_links" : {
                            "self" : {
                            "href" : "https://sw360.org/resource/api/projects/p001"
                            }
                        }
                    },
                    {
                        "name" : "CaPyCLI",
                        "version" : "1.2.0",
                        "projectType" : "PRODUCT",
                        "visibility" : "EVERYONE",
                        "_links" : {
                            "self" : {
                            "href" : "https://sw360.org/resource/api/projects/p002"
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

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("Searching for projects by name" in out)
        self.assertTrue("CaPyCLI, 1.9.0 => ID = p001" in out)
        self.assertTrue("CaPyCLI, 1.2.0 => ID = p002" in out)

    @responses.activate
    def test_project_find_by_name_no_data(self):
        sut = FindProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("find")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True
        args.name = "CaPyCLI"

        self.add_login_response()

        # projects by name
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects?name=CaPyCLI",
            body="""
            {
                "_embedded" : {
                    "sw360:projects" : []
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

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_PROJECT_NOT_FOUND, ex.code)


if __name__ == "__main__":
    APP = TestFindProject()
    APP.test_no_login()
