# -------------------------------------------------------------------------------
# Copyright (c) 2022-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import shutil

import responses

from capycli.main.result_codes import ResultCode
from capycli.project.show_licenses import ShowLicenses
from tests.test_base import AppArguments, TestBase


class TestShowLicenses(TestBase):
    def test_show_help(self) -> None:
        sut = ShowLicenses()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("licenses")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli project licenses" in out)

    @responses.activate
    def test_no_login(self) -> None:
        sut = ShowLicenses()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("licenses")
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
        sut = ShowLicenses()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("licenses")
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

        if os.path.exists(sut.TEMPFOLDER):
            shutil.rmtree(sut.TEMPFOLDER)

    @responses.activate
    def test_project_not_found(self) -> None:
        sut = ShowLicenses()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("licenses")
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

        if os.path.exists(sut.TEMPFOLDER):
            shutil.rmtree(sut.TEMPFOLDER)

    def get_wheel_for_test(self):
        """
        Provide release and attachment responses.
        """
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r001",
            json=self.get_release_wheel_for_test(),
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/attachments/r001a001",
            body="""
                {
                    "_embedded": {
                        "sw360:attachments": [
                            {
                                "filename": "CLIXML_angular-10.0.7.xml",
                                "sha1": "5f392efeb0934339fb6b0f3e021076db19fad164",
                                "attachmentType":
                                "COMPONENT_LICENSE_INFO_XML"
                            }
                        ]
                    }
                }""",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/attachments/r001a002",
            body="""
                {
                    "_embedded": {
                        "sw360:attachments": [
                            {
                                "filename": "CLIXML_angular-10.0.7.xml",
                                "sha1": "5f392efeb0934339fb6b0f3e021076db19fad164",
                                "attachmentType":
                                "COMPONENT_LICENSE_INFO_XML"
                            }
                        ]
                    }
                }""",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

    def get_cli_for_test(self):
        """
        Provide release and attachment responses.
        """
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/r002",
            json=self.get_release_cli_for_test(),
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/attachments/r002a001",
            body="""
                {
                    "filename": "clipython-1.3.0.zip",
                    "sha1": "5f392efeb0934339fb6b0f3e021076db19fad164",
                    "attachmentType":
                    "SOURCE"
                }""",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/attachments/r002a002",
            body="""
                {
                    "filename": "CLIXML_clipython-1.3.0.xml",
                    "sha1": "5f392efeb0934339fb6b0f3e021076db19fad164",
                    "attachmentType":
                    "COMPONENT_LICENSE_INFO_XML"
                }""",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

    def get_cli_file_gpl(self):
        """
        Return the XML contents of a CLI file with GPL-2.0 license.
        """
        return """<?xml version="1.0" encoding="utf-8" standalone="no"?>
<ComponentLicenseInformation
    component="charset_normalizer-3.1.0.zip" creator="thomas.graf@siemens.com"
    date="2023-03-14" baseDoc="" toolUsed="CliEditor" componentID="" includesAcknowledgements="false"
    componentSHA1="67878344e28168dd11b9d6f9c3dbd80a4c1e1b9e" Version="1.5">
  <GeneralInformation>
    <ReportId>168fafd4-c25b-11ed-8ced-6f5dd240728b</ReportId>
    <ReviewedBy />
    <ComponentName>charset-normalizer</ComponentName>
    <Community>NA</Community>
    <ComponentVersion>3.1.0</ComponentVersion>
    <ComponentHash>67878344E28168DD11B9D6F9C3DBD80A4C1E1B9E</ComponentHash>
    <ComponentReleaseDate>NA</ComponentReleaseDate>
    <LinkComponentManagement></LinkComponentManagement>
    <LinkScanTool />
    <ComponentId>
      <Type>package-url</Type>
      <Id>pkg:pypi/charset-normalizer@3.1.0</Id>
    </ComponentId>
  </GeneralInformation>
  <AssessmentSummary>
    <GeneralAssessment><![CDATA[N/A]]></GeneralAssessment>
    <CriticalFilesFound>None</CriticalFilesFound>
    <DependencyNotes>None</DependencyNotes>
    <ExportRestrictionsFound>None</ExportRestrictionsFound>
    <UsageRestrictionsFound>None</UsageRestrictionsFound>
    <AdditionalNotes><![CDATA[NA]]></AdditionalNotes>
  </AssessmentSummary>
  <License type="global" name="GNU General Public License, v2.0" spdxidentifier="GPL-2.0">
    <Content><![CDATA[Permission is hereby granted]]></Content>
    <Files><![CDATA[charset_normalizer/__init__.py]]></Files>
    <FileHash><![CDATA[7d1b9e407eaae7983be386ef9b9a21642ce140e9]]></FileHash>
    <Tags></Tags>
  </License>
  <Copyright>
    <Content><![CDATA[© 2012 XXX]]></Content>
    <Files><![CDATA[README.md]]></Files>
    <FileHash><![CDATA[4e033debe19d28cb1b17adfbf7c1b9f2383281fa]]></FileHash>
  </Copyright>
  <IrrelevantFiles>
    <Files><![CDATA[]]></Files>
  </IrrelevantFiles>
  <Tags></Tags>
  <Comment></Comment>
  <ExternalIds />
</ComponentLicenseInformation>
            """

    @responses.activate
    def test_project_licenses_no_cli_files(self) -> None:
        sut = ShowLicenses()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("licenses")
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
        self.get_wheel_for_test()

        # the second release
        self.get_cli_for_test()

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Project name: CaPyCLI, 1.9.0" in out)
        self.assertTrue("Project owner: thomas.graf@siemens.com" in out)
        self.assertTrue("Clearing state: IN_PROGRESS" in out)
        self.assertTrue("Scanning 2 releases." in out)
        self.assertTrue("cli-support, 1.3" in out)
        self.assertTrue("wheel, 0.38.4" in out)
        self.assertTrue("No CLI file found!" in out)

        if os.path.exists(sut.TEMPFOLDER):
            shutil.rmtree(sut.TEMPFOLDER)

    @responses.activate
    def test_project_licenses_error_in_release(self) -> None:
        sut = ShowLicenses()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("licenses")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True
        args.id = "p001"
        args.name

        self.add_login_response()

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
        self.get_wheel_for_test()

        # the second release
        release = self.get_release_cli_for_test()
        # delete required information => create invalid release
        del release["_embedded"]["sw360:attachments"][0]["_links"]
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
        self.assertTrue("Project name: CaPyCLI, 1.9.0" in out)
        self.assertTrue("Project owner: thomas.graf@siemens.com" in out)
        self.assertTrue("Clearing state: IN_PROGRESS" in out)
        self.assertTrue("Scanning 2 releases." in out)
        self.assertTrue("cli-support, 1.3" in out)
        self.assertTrue("wheel, 0.38.4" in out)
        self.assertTrue("No CLI file found!" in out)
        self.assertTrue("Error processing release" in out)

        if os.path.exists(sut.TEMPFOLDER):
            shutil.rmtree(sut.TEMPFOLDER)

    @responses.activate
    def test_project_licenses_invalid_cli_file(self) -> None:
        sut = ShowLicenses()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("licenses")
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
        self.get_wheel_for_test()

        # the second release
        self.get_cli_for_test()

        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/releases/r002/attachments/r002a002",
            body='xxxx',
            status=200,
            content_type="application/text",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Project name: CaPyCLI, 1.9.0" in out)
        self.assertTrue("Project owner: thomas.graf@siemens.com" in out)
        self.assertTrue("Clearing state: IN_PROGRESS" in out)
        self.assertTrue("Scanning 2 releases." in out)
        self.assertTrue("cli-support, 1.3" in out)
        self.assertTrue("wheel, 0.38.4" in out)
        self.assertTrue("ParseError" in out)

        if os.path.exists(sut.TEMPFOLDER):
            shutil.rmtree(sut.TEMPFOLDER)

    @responses.activate
    def test_project_licenses_by_id(self) -> None:
        sut = ShowLicenses()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("licenses")
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
        self.get_wheel_for_test()

        # the second release
        self.get_cli_for_test()

        cli_file = self.get_cli_file_gpl()
        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/releases/r002/attachments/r002a002",
            body=cli_file,
            status=200,
            content_type="application/text",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Project name: CaPyCLI, 1.9.0" in out)
        self.assertTrue("Project owner: thomas.graf@siemens.com" in out)
        self.assertTrue("Clearing state: IN_PROGRESS" in out)
        self.assertTrue("Scanning 2 releases." in out)
        self.assertTrue("cli-support, 1.3" in out)
        self.assertTrue("wheel, 0.38.4" in out)
        # self.assertTrue("[39mMIT" in out)
        self.assertTrue("[93mGNU General Public License, v2.0 (GPL-2.0)" in out)

        if os.path.exists(sut.TEMPFOLDER):
            shutil.rmtree(sut.TEMPFOLDER)


if __name__ == "__main__":
    APP = TestShowLicenses()
    APP.test_project_licenses_by_id()
