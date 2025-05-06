# -------------------------------------------------------------------------------
# Copyright (c) 2022-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
from typing import Any, Dict
from unittest.mock import MagicMock

import responses

from capycli.main.result_codes import ResultCode
from capycli.project.show_project import ShowProject
from tests.test_base import AppArguments, TestBase


class TestShowProject(TestBase):
    OUTPUTFILE = "output.json"

    def setUp(self) -> None:
        self.client_mock = MagicMock()
        self.sut = ShowProject()
        self.sut.client = self.client_mock

    def test_show_help(self) -> None:
        sut = ShowProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("show")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli project show" in out)

    @responses.activate
    def test_no_login(self) -> None:
        sut = ShowProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("show")
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
        sut = ShowProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("show")
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
        sut = ShowProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("show")
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
    def test_project_show_by_id(self) -> None:
        sut = ShowProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("show")
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
        self.assertTrue("cli-support, 1.3 = MAINLINE, APPROVED" in out)
        self.assertTrue("wheel, 0.38.4 = SPECIFIC, APPROVED" in out)

    @responses.activate
    def test_project_show_by_name(self) -> None:
        sut = ShowProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("show")
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

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Retrieving project details..." in out)

        self.assertTrue("Project name: CaPyCLI, 1.9.0" in out)
        self.assertTrue("Project responsible: thomas.graf@siemens.com" in out)
        self.assertTrue("Project owner: thomas.graf@siemens.com" in out)
        self.assertTrue("Clearing state: IN_PROGRESS" in out)
        self.assertTrue("No linked projects" in out)
        self.assertTrue("cli-support, 1.3 = OPEN, OPEN; No source provided" in out)
        self.assertTrue("wheel, 0.38.4 = SPECIFIC, APPROVED" in out)

    @responses.activate
    def test_project_show_with_subproject(self) -> None:
        sut = ShowProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("show")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True
        args.id = "p001"
        args.outputfile = self.OUTPUTFILE
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

        self.delete_file(self.OUTPUTFILE)
        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Retrieving project details..." in out)

        self.assertTrue("Project name: CaPyCLI, 1.9.0" in out)
        self.assertTrue("Project responsible: thomas.graf@siemens.com" in out)
        self.assertTrue("Project owner: thomas.graf@siemens.com" in out)
        self.assertTrue("Clearing state: IN_PROGRESS" in out)
        self.assertTrue("Linked projects:" in out)
        self.assertTrue("sub-project-dummy, 2.0.1" in out)
        self.assertTrue("cli-support, 1.3 = MAINLINE, APPROVED" in out)
        self.assertTrue("wheel, 0.38.4 = SPECIFIC, APPROVED" in out)

        self.assertTrue(os.path.isfile(self.OUTPUTFILE), "no output file generated")
        self.delete_file(self.OUTPUTFILE)

    def test_project_show_with_defaults(self) -> None:
        """
        Ensure project show will use the default values if the response
        miss some parts of the required data.
        See issue #133
        """
        self.client_mock.get_project.return_value = {
            'description': '',
            'createdOn': '2016-10-10',
            'state': 'ACTIVE',
            'enableSvm': False,
            'considerReleasesFromExternalList': False,
            'enableVulnerabilitiesDisplay': False,
            'projectType': 'PRODUCT',
            'visibility': 'EVERYONE',
            'linkedProjects': [],
            'linkedReleases': [],
            '_links': {
                'self':
                    {
                        'href': 'https://sw360.siemens.com/resource/api/projects/my_dummy_id'
                    }
            },
            '_embedded': {
                'sw360:projects': [],
                'createdBy': {},
                'sw360:moderators': [],
                'sw360:releases': [],
                'sw360:attachments': []
            }
        }

        actual = self.sut.get_project_status("dummy_id")
        self.assertIsNotNone(actual)
        self.assertEqual(actual.get("ClearingState", ""), 'OPEN')
        self.assertEqual(actual.get("Name", None), "")
        self.assertEqual(actual.get("Version", None), "")
        self.assertEqual(actual.get("ProjectOwner", None), "")
        self.assertEqual(actual.get("ProjectResponsible", None), "")
        self.assertEqual(actual.get("SecurityResponsibles", None), [])
        self.assertEqual(actual.get("BusinessUnit", None), "")
        self.assertEqual(actual.get("Tag", None), "")
        self.assertIsNotNone(actual.get("Releases", None))
        self.assertIsNotNone(actual.get("Projects", None))


if __name__ == "__main__":
    APP = TestShowProject()
    APP.setUp()
    APP.test_project_show_with_defaults()
