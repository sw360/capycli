# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import shutil

import responses

from capycli.common.json_support import load_json_file
from capycli.main.result_codes import ResultCode
from capycli.project.get_license_info import GetLicenseInfo
from tests.test_base import AppArguments, TestBase


class TestGetLicenseInfo(TestBase):
    INPUTFILE = "sbom_for_check_prerequisites.json"
    INPUTFILE_TEXT = "plaintext.txt"
    OUTPUTFILE = "output.json"
    CONFIG_FILE = "readme_oss_config.json"

    def test_show_help(self) -> None:
        sut = GetLicenseInfo()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("getlicenseinfo")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("Usage: CaPyCli project GetLicenseInfo" in out)

    def test_no_destination(self) -> None:
        try:
            sut = GetLicenseInfo()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("getlicenseinfo")

            self.add_login_response()

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    # @responses.activate
    def test_no_login(self) -> None:
        sut = GetLicenseInfo()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("getlicenseinfo")
        args.destination = ".//cli_files"
        args.outputfile = self.OUTPUTFILE
        args.sw360_url = "https://my.server.com"

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_AUTH_ERROR, ex.code)

    def test_config_file_not_found(self) -> None:
        try:
            sut = GetLicenseInfo()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("getlicenseinfo")
            args.destination = ".//cli_files"
            args.outputfile = self.OUTPUTFILE
            args.sw360_url = "https://my.server.com"
            args.inputfile = "DOESNOTEXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    @responses.activate
    def test_project_not_found_by_name(self):
        sut = GetLicenseInfo()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("getlicenseinfo")
        args.destination = ".//cli_files"
        args.outputfile = self.OUTPUTFILE
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.verbose = True
        args.debug = True
        args.ncli = True

        self.add_login_response()

        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects?name=CaPyCLI",
            json={
                "_embedded": {
                    "sw360:projects": []
                }
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_PROJECT_NOT_FOUND, ex.code)

    @responses.activate
    def test_error_getting_project(self):
        sut = GetLicenseInfo()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("getlicenseinfo")
        args.destination = ".//cli_files"
        args.outputfile = self.OUTPUTFILE
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.verbose = True
        args.debug = True
        args.ncli = True

        self.add_login_response()

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
            status=500,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_ACCESSING_SW360, ex.code)

        # cleanup
        if os.path.isdir(".//cli_files"):
            shutil.rmtree(".//cli_files")

    @responses.activate
    def test_get_license_info_no_components(self):
        sut = GetLicenseInfo()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("getlicenseinfo")
        args.destination = ".//cli_files"
        args.outputfile = self.OUTPUTFILE
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.verbose = True
        args.debug = True
        args.ncli = True

        self.add_login_response()

        # search for project by name
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
        self.assertTrue("Existing CLI files will not get overwritten." in out)
        self.assertTrue("Components:" in out)
        self.assertTrue(self.OUTPUTFILE in out)

        # cleanup
        self.delete_file(self.OUTPUTFILE)
        if os.path.isdir(".//cli_files"):
            shutil.rmtree(".//cli_files")

    @responses.activate
    def test_get_license_info_no_cli_files(self):
        sut = GetLicenseInfo()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("getlicenseinfo")
        args.destination = ".//cli_files"
        args.outputfile = self.OUTPUTFILE
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.verbose = True
        args.debug = True
        args.ncli = True

        self.add_login_response()

        # search for project by name
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
                    "sw360:releases": [
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
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # get release
        release = self.get_release_cli_for_test()
        del release["_embedded"]
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
        self.assertTrue("Searching for project..." in out)
        self.assertTrue("Existing CLI files will not get overwritten." in out)
        self.assertTrue("Components:" in out)
        self.assertTrue("cli-support 1.3" in out)
        self.assertTrue(self.OUTPUTFILE in out)

        # cleanup
        self.delete_file(self.OUTPUTFILE)
        if os.path.isdir(".//cli_files"):
            shutil.rmtree(".//cli_files")

    @responses.activate
    def test_get_license_info(self):
        sut = GetLicenseInfo()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("getlicenseinfo")
        args.destination = ".//cli_files"
        args.outputfile = self.OUTPUTFILE
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.verbose = True
        args.debug = True
        args.ncli = True

        self.add_login_response()

        # search for project by name
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
                    "sw360:releases": [
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
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # get release
        release = self.get_release_cli_for_test()
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r002",
            json=release,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # attachment info 1
        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/attachments/r002a001",
            body="""
                {
                    "filename": "CLIXML_clipython-1.3.0.xml",
                    "sha1": "dd4c38387c6811dba67d837af7742d84e61e20de",
                    "attachmentType": "COMPONENT_LICENSE_INFO_XML",
                    "_links": {
                        "self": {
                            "href": "https://my.server.com/resource/api/attachments/r002a001"
                        }
                    }
                }""",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # get attachment 1
        cli_file = self.get_cli_file_mit()
        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/releases/r002/attachments/r002a001",
            body=cli_file,
            status=200,
            content_type="application/text",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # attachment info 2
        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/attachments/r002a002",
            body="""
                {
                    "filename": "clipython-1.3.0.zip",
                    "sha1": "0fc54fe4bb73989ce669ad26a8976e7753d31acb",
                    "attachmentType": "SOURCE",
                    "_links": {
                        "self": {
                            "href": "https://my.server.com/resource/api/attachments/r002a001"
                        }
                    }
                }""",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        self.delete_file(self.OUTPUTFILE)
        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Searching for project..." in out)
        self.assertTrue("Existing CLI files will not get overwritten." in out)
        self.assertTrue("Components:" in out)
        self.assertTrue("cli-support 1.3" in out)
        self.assertTrue(self.OUTPUTFILE in out)

        self.assertTrue(os.path.isfile(self.OUTPUTFILE))
        data = load_json_file(self.OUTPUTFILE)
        self.assertIsNotNone(data)
        self.assertEqual("CaPyCLI, TEST", data.get("ProjectName", ""))
        self.assertEqual("Readme_OSS.html", data.get("OutputFileName", ""))
        self.assertEqual(1, len(data["Components"]))
        cli_info = data["Components"][0]
        self.assertIsNotNone(cli_info)
        cli = cli_info.get("CliFile", "")
        self.assertTrue(os.path.isfile(cli))

        # check that properties that cannot get retrieved automatically do not exist
        self.assertFalse("CompanyName" in data)
        self.assertFalse("CompanyAddress1" in data)
        self.assertFalse("CompanyAddress2" in data)
        self.assertFalse("CompanyAddress3" in data)
        self.assertFalse("CompanyAddress4" in data)

        # cleanup
        self.delete_file(cli)
        self.delete_file(self.OUTPUTFILE)
        if os.path.isdir(".//cli_files"):
            shutil.rmtree(".//cli_files")

    @responses.activate
    def test_get_license_info_existing_config(self):
        sut = GetLicenseInfo()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("getlicenseinfo")
        args.destination = ".//cli_files"
        args.outputfile = self.OUTPUTFILE
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.verbose = True
        args.debug = True
        args.ncli = True
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.CONFIG_FILE)

        self.add_login_response()

        # search for project by name
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
                    "sw360:releases": [
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
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # get release
        release = self.get_release_cli_for_test()
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r002",
            json=release,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # attachment info 1
        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/attachments/r002a001",
            body="""
                {
                    "filename": "CLIXML_clipython-1.3.0.xml",
                    "sha1": "dd4c38387c6811dba67d837af7742d84e61e20de",
                    "attachmentType": "COMPONENT_LICENSE_INFO_XML",
                    "_links": {
                        "self": {
                            "href": "https://my.server.com/resource/api/attachments/r002a001"
                        }
                    }
                }""",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # get attachment 1
        cli_file = self.get_cli_file_mit()
        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/releases/r002/attachments/r002a001",
            body=cli_file,
            status=200,
            content_type="application/text",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # attachment info 2
        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/attachments/r002a002",
            body="""
                {
                    "filename": "clipython-1.3.0.zip",
                    "sha1": "0fc54fe4bb73989ce669ad26a8976e7753d31acb",
                    "attachmentType": "SOURCE",
                    "_links": {
                        "self": {
                            "href": "https://my.server.com/resource/api/attachments/r002a001"
                        }
                    }
                }""",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        self.delete_file(self.OUTPUTFILE)
        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Searching for project..." in out)
        self.assertTrue("Existing CLI files will not get overwritten." in out)
        self.assertTrue("Components:" in out)
        self.assertTrue("cli-support 1.3" in out)
        self.assertTrue(self.OUTPUTFILE in out)

        self.assertTrue(os.path.isfile(self.OUTPUTFILE))
        data = load_json_file(self.OUTPUTFILE)
        self.assertIsNotNone(data)
        self.assertEqual("CaPyCLI, 1.9.0", data.get("ProjectName", ""))  # taken from existing config
        self.assertEqual("Readme_OSS.html", data.get("OutputFileName", ""))
        self.assertEqual(1, len(data["Components"]))
        cli_info = data["Components"][0]
        self.assertIsNotNone(cli_info)
        cli = cli_info.get("CliFile", "")
        self.assertTrue(os.path.isfile(cli))

        # check that properties have been taken over from the existing config
        self.assertEqual("Some Company", data.get("CompanyName", ""))
        self.assertEqual("Some Company, Ltd.", data.get("CompanyAddress1", ""))
        self.assertEqual("Any Street 999", data.get("CompanyAddress2", ""))
        self.assertEqual("My City", data.get("CompanyAddress3", ""))
        self.assertEqual("This Country", data.get("CompanyAddress4", ""))

        # cleanup
        self.delete_file(cli)
        self.delete_file(self.OUTPUTFILE)
        if os.path.isdir(".//cli_files"):
            shutil.rmtree(".//cli_files")


if __name__ == '__main__':
    APP = TestGetLicenseInfo()
    APP.test_get_license_info_existing_config()
