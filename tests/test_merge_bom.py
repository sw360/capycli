# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

from capycli.bom.merge_bom import MergeBom
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestMergeBom(TestBase):
    INPUTFILE1 = "sbom_for_download.json"
    INPUTFILE2 = "sbom_for_download_diff.json"
    INPUT_BAD = "plaintext.txt"
    OUTPUTFILE = "output.json"

    def test_show_help(self) -> None:
        sut = MergeBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("merge")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli bom merge" in out)

    def test_input_file_specified(self) -> None:
        try:
            sut = MergeBom()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("merge")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_no_second_bom(self) -> None:
        try:
            sut = MergeBom()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("merge")
            args.command.append("DOESNOTEXIST")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_first_bom_not_found(self) -> None:
        try:
            sut = MergeBom()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("merge")
            args.command.append("DOESNOTEXIST")
            args.command.append("DOESNOTEXIST")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_second_bom_not_found(self) -> None:
        try:
            sut = MergeBom()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("merge")
            args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1))
            args.command.append("DOESNOTEXIST")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_first_bom_error(self) -> None:
        try:
            sut = MergeBom()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("merge")
            args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUT_BAD))
            args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE2))

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, ex.code)

    def test_second_bom_error(self) -> None:
        try:
            sut = MergeBom()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("merge")
            args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1))
            args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUT_BAD))

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, ex.code)

    def test_merge_same_bom(self) -> None:
        sut = MergeBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("merge")
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1))
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1))
        outputfile = self.OUTPUTFILE
        args.command.append(outputfile)

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "dump.txt")
        self.assertTrue(outputfile in out)
        self.assertTrue("Loading first SBOM file" in out)
        self.assertTrue("sbom_for_download.json" in out)
        self.assertTrue("Loading second SBOM file" in out)
        self.assertTrue("Writing combined SBOM with 1 component to" in out)

        bom = CaPyCliBom.read_sbom(outputfile)
        self.assertEqual(1, len(bom.components))

        self.delete_file(outputfile)

    def test_merge_bom1(self) -> None:
        sut = MergeBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("merge")
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1))
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE2))
        outputfile = self.OUTPUTFILE
        args.command.append(outputfile)

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "dump.txt")
        self.assertTrue(outputfile in out)
        self.assertTrue("Loading first SBOM file" in out)
        self.assertTrue("sbom_for_download.json" in out)
        self.assertTrue("Loading second SBOM file" in out)
        self.assertTrue("Writing combined SBOM with 2 components to" in out)

        bom = CaPyCliBom.read_sbom(outputfile)

        self.assertEqual(2, len(bom.metadata.tools))
        self.assertEqual("Siemens AG", bom.metadata.tools[0].vendor)
        self.assertEqual("CaPyCLI", bom.metadata.tools[0].name)
        self.assertEqual("Siemens AG", bom.metadata.tools[1].vendor)
        self.assertEqual("standard-bom", bom.metadata.tools[1].name)

        self.assertEqual(1, len(bom.metadata.licenses))

        self.assertEqual(1, len(bom.metadata.properties))
        self.assertEqual(CycloneDxSupport.CDX_PROP_PROFILE, bom.metadata.properties[0].name)
        self.assertEqual("capycli", bom.metadata.properties[0].value)

        self.assertEqual(2, len(bom.components))
        self.assertEqual("certifi", bom.components[0].name)
        self.assertEqual("2022.12.7", bom.components[0].version)
        self.assertEqual("pkg:pypi/certifi@2022.12.7", bom.components[0].purl)
        self.assertEqual(6, len(bom.components[0].external_references))
        self.assertEqual(1, len(bom.components[0].properties))

        self.assertEqual(2, len(bom.components))
        self.assertEqual("certifi", bom.components[1].name)
        self.assertEqual("2022.12.999", bom.components[1].version)
        self.assertEqual("pkg:pypi/certifi@2022.12.999", bom.components[1].purl)
        self.assertEqual(6, len(bom.components[1].external_references))
        self.assertEqual(1, len(bom.components[1].properties))

        self.delete_file(outputfile)
