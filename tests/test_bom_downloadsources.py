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

from capycli.bom.download_sources import BomDownloadSources
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestBomDownloadsources(TestBase):
    INPUTFILE = "sbom_for_download.json"
    INPUTERROR = "plaintext.txt"
    OUTPUTFILE = "output.json"

    def test_show_help(self) -> None:
        sut = BomDownloadSources()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("downloadsources")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: capycli bom downloadsources" in out)

    def test_no_inputfile_specified(self) -> None:
        try:
            sut = BomDownloadSources()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("downloadsources")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_file_not_found(self) -> None:
        try:
            sut = BomDownloadSources()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("downloadsources")
            args.inputfile = "DOESNOTEXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_error_loading_file(self) -> None:
        try:
            sut = BomDownloadSources()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("downloadsources")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadsources.INPUTERROR)

            sut.run(args)
            self.assertTrue(False, "Failed to report invalid file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, ex.code)

    def test_source_folder_does_not_exist(self) -> None:
        try:
            sut = BomDownloadSources()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("downloadsources")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadsources.INPUTFILE)
            args.source = "XXX"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing folder")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    @responses.activate
    def test_simple_bom(self) -> None:
        sut = BomDownloadSources()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("downloadsources")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadsources.INPUTFILE)
        args.outputfile = TestBomDownloadsources.OUTPUTFILE

        with tempfile.TemporaryDirectory() as tmpdirname:
            args.source = tmpdirname

            # for login
            responses.add(
                responses.GET,
                url="https://files.pythonhosted.org/packages/37/f7/2b1b/certifi-2022.12.7.tar.gz",
                body="""
                SOME DUMMY DATA
                """,
                status=200,
                content_type="application/json",
            )

            try:
                out = self.capture_stdout(sut.run, args)
                # capycli.common.json_support.write_json_to_file(out, "STDOUT.TXT")
                self.assertTrue("Loading SBOM file" in out)
                self.assertTrue("sbom_for_download.json" in out)  # path may vary
                self.assertTrue("Downloading source files to folder" in out)
                self.assertTrue("Downloading file certifi-2022.12.7.tar.gz" in out)

                resultfile = os.path.join(tmpdirname, "certifi-2022.12.7.tar.gz")
                self.assertTrue(os.path.isfile(resultfile))

                self.delete_file(args.outputfile)
                return
            except:  # noqa
                # catch all exception to let Python cleanup the temp folder
                pass

        self.assertTrue(False, "Error: we must never arrive here")

    @responses.activate
    def test_simple_bom_error_download(self) -> None:
        sut = BomDownloadSources()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("downloadsources")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadsources.INPUTFILE)
        args.outputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadsources.OUTPUTFILE)

        with tempfile.TemporaryDirectory() as tmpdirname:
            args.source = tmpdirname

            # for login
            responses.add(
                responses.GET,
                url="https://files.pythonhosted.org/packages/37/f7/2b1b/certifi-2022.12.7.tar.gz",
                body="""
                SOME DUMMY DATA
                """,
                status=500,
                content_type="application/json",
            )

            try:
                out = self.capture_stdout(sut.run, args)
                # capycli.common.json_support.write_json_to_file(out, "STDOUT.TXT")
                self.assertTrue("Loading SBOM file" in out)
                self.assertTrue("sbom_for_download.json" in out)  # path may vary
                self.assertTrue("Downloading source files to folder" in out)
                self.assertTrue("Downloading file certifi-2022.12.7.tar.gz" in out)

                resultfile = os.path.join(tmpdirname, "certifi-2022.12.7.tar.gz")
                self.assertFalse(os.path.isfile(resultfile))
                self.delete_file(args.outputfile)
                return
            except:  # noqa
                # catch all exception to let Python cleanup the temp folder
                pass

        self.assertTrue(False, "Error: we must never arrive here")
