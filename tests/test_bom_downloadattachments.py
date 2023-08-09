# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import tempfile

import responses

from capycli.common.capycli_bom_support import CaPyCliBom
from capycli.common.json_support import load_json_file
from capycli.bom.download_attachments import BomDownloadAttachments
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestBomDownloadAttachments(TestBase):
    INPUTFILE = "sbom_for_download.json"
    CONTROLFILE = "sbom_for_download-control.json"
    INPUTERROR = "plaintext.txt"
    OUTPUTFILE = "output.json"

    @responses.activate
    def setUp(self) -> None:
        self.app = BomDownloadAttachments()
        self.add_login_response()
        self.app.login("sometoken", "https://my.server.com")

        # return super().setUp()

    def test_show_help(self) -> None:
        sut = BomDownloadAttachments()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("downloadattachments")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: capycli bom downloadattachments" in out)

    def test_no_inputfile_specified(self) -> None:
        try:
            sut = BomDownloadAttachments()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("downloadattachments")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_file_not_found(self) -> None:
        try:
            sut = BomDownloadAttachments()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("downloadattachments")
            args.inputfile = "DOESNOTEXIST"
            args.controlfile = os.path.join(os.path.dirname(__file__),
                                            "fixtures", TestBomDownloadAttachments.CONTROLFILE)

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_error_loading_file(self) -> None:
        try:
            sut = BomDownloadAttachments()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("downloadattachments")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadAttachments.INPUTERROR)
            args.controlfile = os.path.join(os.path.dirname(__file__),
                                            "fixtures", TestBomDownloadAttachments.CONTROLFILE)

            sut.run(args)
            self.assertTrue(False, "Failed to report invalid file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, ex.code)

    @responses.activate
    def test_source_folder_does_not_exist(self) -> None:
        try:
            sut = BomDownloadAttachments()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("downloadattachments")

            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadAttachments.INPUTFILE)
            args.controlfile = os.path.join(os.path.dirname(__file__),
                                            "fixtures", TestBomDownloadAttachments.CONTROLFILE)
            args.source = "XXX"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing folder")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    @responses.activate
    def test_simple_bom(self) -> None:
        bom = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadAttachments.INPUTFILE)
        controlfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadAttachments.CONTROLFILE)

        bom = CaPyCliBom.read_sbom(bom)
        controlfile = load_json_file(controlfile)

        # get attachment - CLI
        cli_file = self.get_cli_file_mit()
        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/releases/ae8c7ed/attachments/794446",
            body=cli_file,
            status=200,
            content_type="application/text",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )
        # get attachment - report
        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/releases/ae8c7ed/attachments/63b368",
            body="some_report_content",
            status=200,
            content_type="application/text",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        with tempfile.TemporaryDirectory() as tmpdirname:
            try:
                bom = self.app.download_attachments(bom, controlfile["Components"], tmpdirname)
                resultfile = os.path.join(tmpdirname, "CLIXML_certifi-2022.12.7.xml")
                self.assertEqual(str(bom.components[0].external_references[5].url), resultfile)
                self.assertTrue(os.path.isfile(resultfile), "CLI file missing")

                resultfile = os.path.join(tmpdirname, "certifi-2022.12.7_clearing_report.docx")
                self.assertEqual(str(bom.components[0].external_references[6].url), resultfile)
                self.assertTrue(os.path.isfile(resultfile), "report file missing")
                return
            except Exception as e:  # noqa
                # catch all exception to let Python cleanup the temp folder
                print(e)

        self.assertTrue(False, "Error: we must never arrive here")

    @responses.activate
    def test_simple_bom_relpath(self) -> None:
        bom = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadAttachments.INPUTFILE)
        bom = CaPyCliBom.read_sbom(bom)

        controlfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadAttachments.CONTROLFILE)
        controlfile = load_json_file(controlfile)

        # get attachment - CLI
        cli_file = self.get_cli_file_mit()
        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/releases/ae8c7ed/attachments/794446",
            body=cli_file,
            status=200,
            content_type="application/text",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        with tempfile.TemporaryDirectory() as tmpdirname:
            try:
                bom = self.app.download_attachments(bom, controlfile["Components"],
                                                    tmpdirname, tmpdirname, ("COMPONENT_LICENSE_INFO_XML",))
                resultfile = os.path.join(tmpdirname, "CLIXML_certifi-2022.12.7.xml")
                self.assertEqual(str(bom.components[0].external_references[5].url),
                                 "file://CLIXML_certifi-2022.12.7.xml")
                self.assertTrue(os.path.isfile(resultfile), "CLI file missing")

                return
            except Exception as e:  # noqa
                # catch all exception to let Python cleanup the temp folder
                print(e)

        self.assertTrue(False, "Error: we must never arrive here")

    @responses.activate
    def test_simple_bom_download_errors(self) -> None:
        # create argparse command line argument object
        bom = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadAttachments.INPUTFILE)
        bom = CaPyCliBom.read_sbom(bom)

        controlfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadAttachments.CONTROLFILE)
        controlfile = load_json_file(controlfile)

        # get attachment - CLI, error
        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/releases/ae8c7ed/attachments/794446",
            status=500,
            content_type="application/text",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )
        # get attachment - CLI, error
        responses.add(
            method=responses.GET,
            url=self.MYURL + "resource/api/releases/ae8c7ed/attachments/63b368",
            status=403,
            content_type="application/text",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        with tempfile.TemporaryDirectory() as tmpdirname:
            try:
                bom = self.app.download_attachments(bom, controlfile["Components"], tmpdirname)
                resultfile = os.path.join(tmpdirname, "CLIXML_certifi-2022.12.7.xml")
                self.assertFalse(os.path.isfile(resultfile), "CLI created despite HTTP 500")

                resultfile = os.path.join(tmpdirname, "certifi-2022.12.7_clearing_report.docx")
                self.assertFalse(os.path.isfile(resultfile), "report created despite HTTP 404")
                return
            except Exception as e:  # noqa
                # catch all exception to let Python cleanup the temp folder
                print(e)

        self.assertTrue(False, "Error: we must never arrive here")

    @responses.activate
    def test_simple_bom_no_release_id(self) -> None:
        bom = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadAttachments.INPUTFILE)
        bom = CaPyCliBom.read_sbom(bom)
        bom.components[0].properties = []
        with tempfile.TemporaryDirectory() as tmpdirname:
            try:
                err = self.capture_stdout(self.app.download_attachments, bom, [], tmpdirname)
                self.assertIn("No sw360Id for release", err)

                return
            except Exception as e:  # noqa
                # catch all exception to let Python cleanup the temp folder
                print(e)

        self.assertTrue(False, "Error: we must never arrive here")

    @responses.activate
    def test_simple_bom_no_ctrl_file_entry(self) -> None:
        bom = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadAttachments.INPUTFILE)
        bom = CaPyCliBom.read_sbom(bom)

        with tempfile.TemporaryDirectory() as tmpdirname:
            try:
                err = self.capture_stdout(self.app.download_attachments, bom, [], tmpdirname)
                assert "Found 0 entries for attachment CLIXML_certifi-2022.12.7.xml" in err

                return
            except Exception as e:  # noqa
                # catch all exception to let Python cleanup the temp folder
                print(e)

        self.assertTrue(False, "Error: we must never arrive here")
