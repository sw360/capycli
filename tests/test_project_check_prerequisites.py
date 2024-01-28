# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

import responses

from capycli.main.result_codes import ResultCode
from capycli.project.check_prerequisites import CheckPrerequisites
from tests.test_base import AppArguments, TestBase


class TestCheckPrerequisites(TestBase):
    INPUTFILE = "sbom_for_check_prerequisites.json"
    INPUTFILE_INVALID = "plaintext.txt"

    def test_show_help(self) -> None:
        sut = CheckPrerequisites()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("prerequisites")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("Usage: CaPyCli project prerequisites" in out)

    @responses.activate
    def test_no_login(self) -> None:
        sut = CheckPrerequisites()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("prerequisites")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_AUTH_ERROR, ex.code)

    @responses.activate
    def test_bom_file_not_found(self) -> None:
        try:
            sut = CheckPrerequisites()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("prerequisites")
            args.sw360_token = TestBase.MYTOKEN
            args.sw360_url = TestBase.MYURL
            args.name = "CaPyCLI"
            args.version = "TEST"
            args.inputfile = "DOES_NOT_EXIST"

            self.add_login_response()

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    @responses.activate
    def test_bom_file_invalid(self) -> None:
        try:
            sut = CheckPrerequisites()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("prerequisites")
            args.sw360_token = TestBase.MYTOKEN
            args.sw360_url = TestBase.MYURL
            args.name = "CaPyCLI"
            args.version = "TEST"
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_INVALID)

            self.add_login_response()

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, ex.code)

    @responses.activate
    def test_no_id_no_name(self) -> None:
        try:
            sut = CheckPrerequisites()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("prerequisites")
            args.sw360_token = TestBase.MYTOKEN
            args.sw360_url = TestBase.MYURL

            self.add_login_response()

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    @responses.activate
    def test_check_project_not_found(self) -> None:
        sut = CheckPrerequisites()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("prerequisites")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.verbose = True
        args.debug = True

        self.add_login_response()

        # find project => do not report the project we are looking for
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects?name=CaPyCLI",
            json={
                "_embedded": {
                    "sw360:projects": [{
                        "name": "CaPyCLI",
                        "version": "1.9.0",
                        "securityResponsibles": [],
                        "considerReleasesFromExternalList": False,
                        "projectType": "PRODUCT",
                        "visibility": "EVERYONE",
                        "_links": {
                            "self": {
                                "href": TestBase.MYURL + "resource/api/projects/376576"
                            }
                        }
                    }]
                }
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Searching for project..." in out)
        self.assertTrue("No matching project found" in out)

    def add_find_project_response(self) -> None:
        """
        Add response for find project by name.
        """
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects?name=CaPyCLI",
            json={
                "_embedded": {
                    "sw360:projects": [{
                        "name": "CaPyCLI",
                        "version": "TEST",
                        "securityResponsibles": [],
                        "considerReleasesFromExternalList": False,
                        "projectType": "PRODUCT",
                        "visibility": "EVERYONE",
                        "_links": {
                            "self": {
                                "href": TestBase.MYURL + "resource/api/projects/007"
                            }
                        }
                    }]
                }
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

    @responses.activate
    def test_check_project_no_releases(self) -> None:
        sut = CheckPrerequisites()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("prerequisites")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.verbose = True
        args.debug = True

        self.add_login_response()

        # find project by name
        self.add_find_project_response()

        # get project by id
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/007",
            json={
                "name": "CaPyCLI",
                "version": "TEST",
                "securityResponsibles": [],
                "considerReleasesFromExternalList": False,
                "projectType": "PRODUCT",
                "visibility": "EVERYONE",
                "_links": {
                    "self": {
                        "href": TestBase.MYURL + "resource/api/projects/376576"
                    }
                },
                "_embedded": {
                    "sw360:releases": []
                }
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Searching for project..." in out)
        self.assertTrue("Project name: CaPyCLI, TEST" in out)
        self.assertTrue("Clearing state: UNKNOWN" in out)
        self.assertTrue("No project owner specified!" in out)
        self.assertTrue("No project responsible specified!" in out)
        self.assertTrue("No security responsibles specified!" in out)
        self.assertTrue("No tag specified!" in out)

        self.assertTrue("No linked projects" in out)
        self.assertTrue("No SBOM specified, skipping release comparison!" in out)

    @responses.activate
    def test_check_project_error_reading_project(self) -> None:
        sut = CheckPrerequisites()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("prerequisites")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.verbose = True
        args.debug = True

        self.add_login_response()

        # find project by name
        self.add_find_project_response()

        # get project by id
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/007",
            json={
            },
            status=500,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_ACCESSING_SW360, ex.code)

    def test_get_component_management_id(self) -> None:
        release = {
            "name": "wheel",
            "version": "0.38.4",
            "releaseDate": "",
            "componentType": "OSS",
            "externalIds": {
                "package-url": "pkg:pypi/wheel@0.38.4"
            }
        }

        sut = CheckPrerequisites()
        val = sut.get_component_management_id(release)
        self.assertEqual({"package-url": "pkg:pypi/wheel@0.38.4"}, val)

        release2 = {
            "name": "wheel",
            "version": "0.38.4",
            "releaseDate": "",
            "componentType": "OSS",
            "externalIds": {
                "com.siemens.mainl.component.id": "1234",
                "com.siemens.mainl.component.request": "56",
                "com.siemens.em.component.id": "78",
                "com.siemens.svm.component.id": "90"
            }
        }

        val = sut.get_component_management_id(release2)
        self.assertEqual({}, val)

    @responses.activate
    def test_check_project_check_fail(self) -> None:
        sut = CheckPrerequisites()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("prerequisites")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.verbose = True
        args.debug = True

        self.add_login_response()

        # find project by name
        self.add_find_project_response()

        # get project by id
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/007",
            json={
                "name": "CaPyCLI",
                "version": "TEST",
                "securityResponsibles": [],
                "considerReleasesFromExternalList": False,
                "projectType": "PRODUCT",
                "visibility": "EVERYONE",
                "_links": {
                    "self": {
                        "href": TestBase.MYURL + "resource/api/projects/376576"
                    }
                },
                "linkedReleases": [
                    {
                        "createdBy": "thomas.graf@siemens.com",
                        "release": "https://my.server.com/resource/api/releases/r001",
                        "mainlineState": "SPECIFIC",
                        "comment": "Automatically updated by SCC",
                        "createdOn": "2023-03-14",
                        "relation": "UNKNOWN"
                    }
                ],
                "_embedded": {
                    "sw360:releases": [{
                        "name": "wheel",
                        "version": "0.38.4",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/releases/r001"
                            }
                        }
                    }]
                }
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the first release - all checks fail
        release = self.get_release_wheel_for_test()
        # remove most data
        del release["sourceCodeDownloadurl"]
        del release["languages"]
        del release["_embedded"]
        del release["externalIds"]
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r001",
            json=release,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("No project owner specified!" in out)
        self.assertTrue("No project responsible specified!" in out)
        self.assertTrue("No security responsibles specified!" in out)
        self.assertTrue("No tag specified!" in out)

        self.assertTrue("No linked projects" in out)

        self.assertTrue("wheel, 0.38.4: SPECIFIC" in out)
        self.assertTrue("No download URL specified!" in out)
        self.assertTrue("No programming language specified!" in out)
        self.assertTrue("0 source file(s) available" in out)
        self.assertTrue("No component management id (package-url, etc.) specified!" in out)

        self.assertTrue("No SBOM specified, skipping release comparison!" in out)

    @responses.activate
    def test_check_project_check_passed(self) -> None:
        sut = CheckPrerequisites()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("prerequisites")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)
        args.verbose = True
        args.debug = True

        self.add_login_response()

        # find project by name
        self.add_find_project_response()

        # get project by id
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/007",
            json={
                "name": "CaPyCLI",
                "version": "TEST",
                "considerReleasesFromExternalList": False,
                "projectType": "PRODUCT",
                "visibility": "EVERYONE",
                "projectResponsible": "thomas.graf@siemens.com",
                "securityResponsibles": [
                    "thomas.graf@siemens.com"
                ],
                "projectOwner": "thomas.graf@siemens.com",
                "tag": "Demo",
                "_links": {
                    "self": {
                        "href": TestBase.MYURL + "resource/api/projects/376576"
                    }
                },
                "linkedReleases": [
                    {
                        "createdBy": "thomas.graf@siemens.com",
                        "release": "https://my.server.com/resource/api/releases/r001",
                        "mainlineState": "SPECIFIC",
                        "comment": "Automatically updated by SCC",
                        "createdOn": "2023-03-14",
                        "relation": "UNKNOWN"
                    }
                ],
                "linkedProjects": [{
                    "project": "https://my.server.com/resource/api/projects/f0c2",
                    "enableSvm": "true",
                    "relation": "REFERRED"
                }],
                "_embedded": {
                    "sw360:releases": [{
                        "name": "cli-support",
                        "version": "1.3.0",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/releases/r002"
                            }
                        }
                    }],
                    "sw360:projects": [{
                        "name": "dummyproject",
                        "version": "99.88",
                        "project": "https://my.server.com/resource/api/projects/f0c2",
                        "enableSvm": "true",
                        "relation": "REFERRED"
                    }]
                }
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the release - all checks pass
        release = self.get_release_cli_for_test()
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r002",
            json=release,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # attachment info
        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/attachments/r002a001",
            body="""
                {
                    "filename": "clipython-1.3.0.zip",
                    "sha1": "5f392efeb0934339fb6b0f3e021076db19fad164",
                    "attachmentType": "SOURCE",
                    "checkStatus" : "ACCEPTED",
                    "checkedBy" : "thomas.graf@siemens.com"
                }""",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Project owner: thomas.graf@siemens.com" in out)
        self.assertTrue("Project responsible: thomas.graf@siemens.com" in out)
        self.assertTrue("Security responsible(s): thomas.graf@siemens.com" in out)
        self.assertTrue("Tag: Demo" in out)

        self.assertTrue("Linked projects:" in out)
        self.assertTrue("dummyproject, 99.88" in out)

        self.assertTrue("cli-support, 1.3.0" in out)
        self.assertTrue("Download URL: https://github.com/sw360/clipython" in out)
        self.assertTrue("Programming language: Python" in out)
        self.assertTrue("SHA1 for source clipython-1.3.0.zip does not match!" in out)
        self.assertTrue("clipython-1.3.0.zip ACCEPTED by thomas.graf@siemens.com" in out)
        self.assertTrue("1 source file(s) available." in out)
        self.assertTrue("component management id: {'package-url': 'pkg:pypi/cli-support@1.3'}" in out)

        self.assertTrue("SBOM release check:" in out)
        self.assertTrue("SBOM Item not in SW360 project: xx-support 3.0" in out)


if __name__ == '__main__':
    APP = TestCheckPrerequisites()
    APP.test_check_project_check_fail()
