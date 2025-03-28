# -------------------------------------------------------------------------------
# Copyright (c) 2023-2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import tempfile

import responses
from cyclonedx.model import ExternalReferenceType
from cyclonedx.model.component import Component

from capycli.bom.download_sources import BomDownloadSources
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
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
                out_bom = CaPyCliBom.read_sbom(args.outputfile)
                # capycli.common.json_support.write_json_to_file(out, "STDOUT.TXT")
                self.assertTrue("Loading SBOM file" in out)
                self.assertTrue("sbom_for_download.json" in out)  # path may vary
                self.assertIn("SBOM file is not relative to", out)
                self.assertTrue("Downloading source files to folder" in out)
                self.assertTrue("Downloading file certifi-2022.12.7.tar.gz" in out)

                resultfile = os.path.join(tmpdirname, "certifi-2022.12.7.tar.gz")
                self.assertTrue(os.path.isfile(resultfile))

                ext_ref = CycloneDxSupport.get_ext_ref(
                    out_bom.components[0], ExternalReferenceType.DISTRIBUTION, CaPyCliBom.SOURCE_FILE_COMMENT)
                self.assertIsNotNone(ext_ref)
                if ext_ref:  # only for mypy
                    self.assertEqual(ext_ref.url._uri, resultfile)
                    # if ext_ref.url is XsUri:
                    #    self.assertEqual(ext_ref.url._uri, resultfile)
                    # else:
                    #    self.assertEqual(ext_ref.url, resultfile)

                self.delete_file(args.outputfile)
                return
            except Exception as e:  # noqa
                # catch all exception to let Python cleanup the temp folder
                print(e)

        self.assertTrue(False, "Error: we must never arrive here")

    @responses.activate
    def test_simple_bom_relative_path(self) -> None:
        sut = BomDownloadSources()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("downloadsources")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomDownloadsources.INPUTFILE)

        with tempfile.TemporaryDirectory() as tmpdirname:
            args.source = tmpdirname
            args.outputfile = os.path.join(tmpdirname, TestBomDownloadsources.OUTPUTFILE)

            # fake file content
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
                sut.run(args)
                out_bom = CaPyCliBom.read_sbom(args.outputfile)

                ext_ref = CycloneDxSupport.get_ext_ref(
                    out_bom.components[0], ExternalReferenceType.DISTRIBUTION, CaPyCliBom.SOURCE_FILE_COMMENT)
                self.assertIsNotNone(ext_ref)
                if ext_ref:  # only for mypy
                    self.assertEqual(ext_ref.url._uri, "file://certifi-2022.12.7.tar.gz")

                self.delete_file(args.outputfile)
                return
            except Exception as e:  # noqa
                # catch all exception to let Python cleanup the temp folder
                print(e)

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

    @responses.activate
    def test_simple_bom_no_url(self) -> None:
        sut = BomDownloadSources()

        with tempfile.TemporaryDirectory() as tmpdirname:
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
                bom = CaPyCliBom.read_sbom(
                    os.path.join(
                        os.path.dirname(__file__),
                        "fixtures", TestBomDownloadsources.INPUTFILE))
                bom.components.add(Component(name="foo", version="1.2.3"))
                sut.download_sources(bom, tmpdirname)
                resultfile = os.path.join(tmpdirname, "certifi-2022.12.7.tar.gz")
                self.assertTrue(os.path.isfile(resultfile))

                ext_ref = CycloneDxSupport.get_ext_ref(
                    bom.components[0], ExternalReferenceType.DISTRIBUTION, CaPyCliBom.SOURCE_FILE_COMMENT)
                self.assertIsNotNone(ext_ref)
                if ext_ref:  # only for mypy
                    self.assertEqual(str(ext_ref.url), resultfile)

                self.assertEqual(len(bom.components[1].external_references), 0)
                return
            except Exception as e:  # noqa
                # catch all exception to let Python cleanup the temp folder
                print(e)

        self.assertTrue(False, "Error: we must never arrive here")


if __name__ == "__main__":
    lib = TestBomDownloadsources()
    lib.test_simple_bom()
