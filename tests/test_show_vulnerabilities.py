# -------------------------------------------------------------------------------
# Copyright (c) 2022-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
from typing import Any, Dict

import responses

from capycli.main.result_codes import ResultCode
from capycli.project.show_vulnerabilities import ShowSecurityVulnerability
from tests.test_base import AppArguments, TestBase


class TestShowSecurityVulnerability(TestBase):
    OUTPUTFILE = "output.json"

    def test_show_help(self) -> None:
        sut = ShowSecurityVulnerability()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("vulnerabilities")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli project vulnerabilities" in out)

    @responses.activate
    def test_no_login(self) -> None:
        sut = ShowSecurityVulnerability()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("vulnerabilities")
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
        sut = ShowSecurityVulnerability()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("vulnerabilities")
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
        sut = ShowSecurityVulnerability()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("vulnerabilities")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True
        args.id = "34ef5c5452014c52aa9ce4bc180624d8"

        self.add_login_response()

        # project
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
            self.assertEqual(ResultCode.RESULT_PROJECT_NOT_FOUND, ex.code)

    def get_vulnerabilities_for_test(self) -> Dict[str, Any]:
        """
        Get vulnerability response for tesing.
        """
        vul = {
            "_embedded": {
                "sw360:vulnerabilityDTOes": [
                    {
                        "priority": "2 - major",
                        "projectRelevance": "NOT_CHECKED",
                        "comment": "",
                        "projectAction": "",
                        "intReleaseId": "a14fb081b6dae6aecd31f2086e2f2cf0",
                        "intReleaseName": "PyJWT 1.7.1",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/vulnerabilities/91040"
                            }
                        }
                    }
                ]
            }
        }
        return vul

    @responses.activate
    def test_project_show_by_id(self) -> None:
        sut = ShowSecurityVulnerability()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("vulnerabilities")
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

        # vulnerabilities
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/p001/vulnerabilities",
            json=self.get_vulnerabilities_for_test(),
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Project information:" in out)

        self.assertTrue("Name: CaPyCLI" in out)
        self.assertTrue("Version: 1.9.0" in out)
        self.assertTrue("Id: p001" in out)

        self.assertTrue("Priority:          2 - major" in out)
        self.assertTrue("Project Relevance: NOT_CHECKED" in out)
        self.assertTrue("Project Comment:" in out)
        self.assertTrue("Project Action:" in out)
        self.assertTrue("Component:         PyJWT 1.7.1" in out)

    @responses.activate
    def test_project_show_by_id_and_force_exit_code(self) -> None:
        sut = ShowSecurityVulnerability()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("vulnerabilities")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True
        args.id = "p001"
        args.force_exit = "2"
        args.outputfile = self.OUTPUTFILE

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

        # vulnerabilities
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/p001/vulnerabilities",
            json=self.get_vulnerabilities_for_test(),
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            self.delete_file(self.OUTPUTFILE)
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_UNHANDLED_SECURITY_VULNERABILITY_FOUND, ex.code)

        self.assertTrue(os.path.isfile(self.OUTPUTFILE), "no output file generated")
        self.delete_file(self.OUTPUTFILE)

    @responses.activate
    def test_project_show_by_name(self) -> None:
        sut = ShowSecurityVulnerability()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("vulnerabilities")
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
                        "href" : "https://my.server.com/resource/api/projects/p001"
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

        # vulnerabilities
        vuls = self.get_vulnerabilities_for_test()
        v = {
            "priority": "3 - minor",
            "projectRelevance": "IN_ANALYSIS",
            "comment": "",
            "projectAction": "",
            "intReleaseId": "a14fb081b6dae6aecd31f2086e2f2cf2",
            "intReleaseName": "xxx 1.7.1",
            "_links": {
                "self": {
                    "href": "https://my.server.com/resource/api/vulnerabilities/91042"
                }
            }
        }
        vuls["_embedded"]["sw360:vulnerabilityDTOes"].append(v)

        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/p001/vulnerabilities",
            json=vuls,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Project information:" in out)

        self.assertTrue("Name: CaPyCLI" in out)
        self.assertTrue("Version: 1.9.0" in out)
        self.assertTrue("Id: p001" in out)

        self.assertTrue("Priority:          2 - major" in out)
        self.assertTrue("Project Relevance: NOT_CHECKED" in out)
        self.assertTrue("Project Comment:" in out)
        self.assertTrue("Project Action:" in out)
        self.assertTrue("Component:         PyJWT 1.7.1" in out)

        self.assertTrue("Priority:          3 - minor" in out)
        self.assertTrue("Project Relevance: IN_ANALYSIS" in out)

    def test_check_report(self) -> None:
        sut = ShowSecurityVulnerability()

        report: Dict[str, Any] = {}
        report["Vulnerabilities"] = []
        report["Vulnerabilities"].append({"priority": "0"})

        ret = sut.check_report_for_critical_findings(report, "0")
        self.assertFalse(ret)

        ret = sut.check_report_for_critical_findings(report, "6")
        self.assertFalse(ret)

        report: Dict[str, Any] = {}
        report["Vulnerabilities"] = []
        report["Vulnerabilities"].append({"priority": "0"})
        v: Dict[str, Any] = {}
        v["priority"] = "1"
        v["projectRelevance"] = "NOT_CHECKED"
        report["Vulnerabilities"].append(v)
        ret = sut.check_report_for_critical_findings(report, "2")
        self.assertTrue(ret)


if __name__ == "__main__":
    APP = TestShowSecurityVulnerability()
    APP.test_project_not_found()
