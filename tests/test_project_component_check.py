# -------------------------------------------------------------------------------
# Copyright (c) 2026 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from typing import Any, Dict
from unittest.mock import MagicMock

import responses

from capycli.main.result_codes import ResultCode
from capycli.project.project_component_check import ProjectComponentCheck
from tests.test_base import AppArguments, TestBase


class TestProjectComponentCheck(TestBase):
    def setUp(self) -> None:
        self.client_mock = MagicMock()
        self.sut = ProjectComponentCheck()
        self.sut.client = self.client_mock

    def test_show_help(self) -> None:
        sut = ProjectComponentCheck()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("componentcheck")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli project componentcheck" in out)

    @responses.activate
    def test_no_login(self) -> None:
        sut = ProjectComponentCheck()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("componentcheck")
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
        sut = ProjectComponentCheck()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("componentcheck")
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
        sut = ProjectComponentCheck()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("componentcheck")
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

    @staticmethod
    def get_project_for_test() -> Dict[str, Any]:
        """
        Return a SW360 project for unit testing.
        """
        project = {
            "name": "CaPyCLI",
            "description": "Software clearing for CaPyCLI, the clearing automation scripts for Python",
            "version": "1.9.0",
            "externalIds": {
                "com.siemens.code.project.id": "69287"
            },
            "additionalData": {},
            "createdOn": "2023-03-14",
            "businessUnit": "SI",
            "state": "ACTIVE",
            "tag": "Demo",
            "clearingState": "IN_PROGRESS",
            "projectResponsible": "thomas.graf@siemens.com",
            "roles": {},
            "securityResponsibles": [
                "thomas.graf@siemens.com"
            ],
            "projectOwner": "thomas.graf@siemens.com",
            "ownerAccountingUnit": "",
            "ownerGroup": "",
            "ownerCountry": "",
            "preevaluationDeadline": "",
            "systemTestStart": "",
            "systemTestEnd": "",
            "deliveryStart": "",
            "phaseOutSince": "",
            "enableSvm": True,
            "considerReleasesFromExternalList": False,
            "licenseInfoHeaderText": "dummy",
            "enableVulnerabilitiesDisplay": True,
            "clearingSummary": "",
            "specialRisksOSS": "",
            "generalRisks3rdParty": "",
            "specialRisks3rdParty": "",
            "deliveryChannels": "",
            "remarksAdditionalRequirements": "",
            "projectType": "INNER_SOURCE",
            "visibility": "EVERYONE",
            "linkedProjects": [],
            "linkedReleases": [
                {
                    "createdBy": "thomas.graf@siemens.com",
                    "release": "https://my.server.com/resource/api/releases/r001",
                    "mainlineState": "SPECIFIC",
                    "comment": "Automatically updated by SCC",
                    "createdOn": "2023-03-14",
                    "relation": "UNKNOWN"
                },
                {
                    "createdBy": "thomas.graf@siemens.com",
                    "release": "https://my.server.com/resource/api/releases/r002",
                    "mainlineState": "MAINLINE",
                    "comment": "Automatically updated by SCC",
                    "createdOn": "2023-03-14",
                    "relation": "DYNAMICALLY_LINKED"
                }
            ],
            "_links": {
                "self": {
                    "href": "https://my.server.com/resource/api/projects/p001"
                }
            },
            "_embedded": {
                "createdBy": {
                    "email": "thomas.graf@siemens.com",
                    "deactivated": False,
                    "fullName": "Thomas Graf",
                    "_links": {
                        "self": {
                            "href": "https://my.server.com/resource/api/users/byid/thomas.graf%2540siemens.com"
                        }
                    }
                },
                "sw360:releases": [
                    {
                        "name": "wheelxxx",
                        "version": "0.38.4",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/releases/r001"
                            }
                        }
                    },
                    {
                        "name": "cli-support",
                        "version": "1.3",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/releases/r002"
                            }
                        }
                    }
                ]
            }
        }

        return project

    @responses.activate
    def test_project_show_by_id(self) -> None:
        sut = ProjectComponentCheck()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("componentcheck")
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

        # the release
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
        self.assertTrue("Reading component checklist" in out)
        self.assertTrue("Got component checklist." in out)
        self.assertTrue("0 components will be ignored." in out)

        self.assertTrue("Retrieving project details..." in out)


if __name__ == "__main__":
    APP = TestProjectComponentCheck()
    APP.setUp()
    APP.test_project_show_by_id()
