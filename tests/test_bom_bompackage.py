# -------------------------------------------------------------------------------
# Copyright (c) 2025 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import tempfile
import zipfile

import responses
from cyclonedx.model import ExternalReferenceType

from capycli.bom.bom_package import BomPackage
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestBomPackage(TestBase):
    INPUTFILE = "sbom_for_download.json"
    INPUTERROR = "plaintext.txt"
    OUTPUTFILE = "test_bom_package.zip"

    def test_show_help(self) -> None:
        sut = BomPackage()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("bompackage")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: capycli bom bompackage" in out)

    def test_no_inputfile_specified(self) -> None:
        try:
            sut = BomPackage()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("bompackage")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_no_outputfile_specified(self) -> None:
        try:
            sut = BomPackage()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("bompackage")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomPackage.INPUTERROR)

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_file_not_found(self) -> None:
        try:
            sut = BomPackage()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("bompackage")
            args.inputfile = "DOESNOTEXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_error_loading_file(self) -> None:
        try:
            sut = BomPackage()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("bompackage")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomPackage.INPUTERROR)
            args.outputfile = TestBomPackage.OUTPUTFILE

            sut.run(args)
            self.assertTrue(False, "Failed to report invalid file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, ex.code)

    @responses.activate
    def test_simple_bom_package(self) -> None:
        sut = BomPackage()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("bompackage")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomPackage.INPUTFILE)
        args.outputfile = TestBomPackage.OUTPUTFILE

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
                out = self.capture_stdout(sut.run, args)
                # json_support.write_json_to_file(out, "STDOUT.TXT")
                self.assertTrue("Loading SBOM file" in out)
                self.assertTrue("sbom_for_download.json" in out)  # path may vary
                self.assertTrue("Downloading files to folder" in out)
                self.assertTrue("Downloading file certifi-2022.12.7.tar.gz" in out)
                self.assertTrue("Creating BOM package test_bom_package.zip" in out)

                self.assertTrue(os.path.isfile(args.outputfile))
                archive = zipfile.ZipFile(args.outputfile, 'r')
                namelist = archive.namelist()
                self.assertIn("sbom.cdx.json", namelist)
                self.assertIn("sources/1b27be1573e99442dc3ca77b36caf76fc77a456a/", namelist)
                self.assertIn("sources/1b27be1573e99442dc3ca77b36caf76fc77a456a/certifi-2022.12.7.tar.gz", namelist)
                archive.extract("sbom.cdx.json", tmpdirname)
                out_bom = CaPyCliBom.read_sbom(os.path.join(tmpdirname, "sbom.cdx.json"))

                ext_ref = CycloneDxSupport.get_ext_ref(
                    out_bom.components[0], ExternalReferenceType.DISTRIBUTION, CaPyCliBom.SOURCE_FILE_COMMENT)
                self.assertIsNotNone(ext_ref)
                if ext_ref:  # only for mypy
                    check_val = ext_ref.url._uri
                    if check_val.startswith("file:///"):
                        check_val = check_val[8:]
                    self.assertEqual(
                        check_val,
                        "sources/1b27be1573e99442dc3ca77b36caf76fc77a456a/certifi-2022.12.7.tar.gz")

                archive.close()
                self.delete_file(args.outputfile)
                return
            except Exception as e:  # noqa
                # catch all exception to let Python cleanup the temp folder
                print(e)

        self.assertTrue(False, "Error: we must never arrive here")

    @responses.activate
    def test_simple_bom_error_download(self) -> None:
        sut = BomPackage()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("bompackage")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestBomPackage.INPUTFILE)
        args.outputfile = TestBomPackage.OUTPUTFILE

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
            self.assertTrue("Downloading files to folder" in out)
            self.assertTrue("Downloading file certifi-2022.12.7.tar.gz" in out)

            self.assertTrue(os.path.isfile(args.outputfile))
            archive = zipfile.ZipFile(args.outputfile, 'r')
            namelist = archive.namelist()
            self.assertIn("sbom.cdx.json", namelist)
            self.assertNotIn("sources/1b27be1573e99442dc3ca77b36caf76fc77a456a/", namelist)
            self.assertNotIn("sources/1b27be1573e99442dc3ca77b36caf76fc77a456a/certifi-2022.12.7.tar.gz", namelist)
            if os.path.isfile(os.path.join(args.outputfile)):
                self.delete_file(args.outputfile)
            return
        except:  # noqa
            # catch all exception to let Python cleanup the temp folder
            pass

        self.assertTrue(False, "Error: we must never arrive here")


if __name__ == "__main__":
    lib = TestBomPackage()
    lib.test_simple_bom_error_download()
