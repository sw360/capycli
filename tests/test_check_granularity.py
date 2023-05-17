# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

from capycli.bom.check_granularity import CheckGranularity
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestCheckGranularity(TestBase):
    INPUTFILE1 = "sbom_for_granularity.json"
    INPUT_INVALID = "plaintext.txt"
    OUTPUTFILE1 = "output.json"

    def test_show_help(self) -> None:
        sut = CheckGranularity()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("granularity")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli bom granularity" in out)

    def test_no_input_file_specified(self) -> None:
        try:
            sut = CheckGranularity()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("granularity")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_file_not_found(self) -> None:
        try:
            sut = CheckGranularity()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("granularity")
            args.inputfile = "DOESNOTEXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_error_reading_bom(self) -> None:
        try:
            sut = CheckGranularity()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("granularity")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUT_INVALID)

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, ex.code)

    def test_real_bom1(self) -> None:
        sut = CheckGranularity()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("granularity")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE1 in out)
        self.assertTrue("Reading granularity data from granularity_list.csv" in out)
        self.assertTrue("@angular/animations, 15.2.6 should get replaced by Angular" in out)
        self.assertTrue("@angular/router, 15.2.6 should get replaced by Angular" in out)
        self.assertTrue("1 items can be reduced by granularity check" in out)
        self.assertTrue("To get updated SBOM file - use the '-o <filename>' parameter" in out)

    def test_real_bom2(self) -> None:
        sut = CheckGranularity()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("granularity")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE1
        args.debug = True
        args.search_meta_data = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE1 in out)
        self.assertTrue("Reading granularity data from granularity_list.csv" in out)
        self.assertTrue("@angular/animations, 15.2.6 should get replaced by Angular" in out)
        self.assertTrue("@angular/router, 15.2.6 should get replaced by Angular" in out)
        self.assertTrue("1 items can be reduced by granularity check" in out)

        # self.assertTrue("https://registry.npmjs.org:443" in out)
        # self.assertTrue("GET /Angular/15.2.6" in out)
        self.assertTrue("No info found for component Angular, 15.2.6" in out)
        self.assertTrue("Writing new SBOM to output.json" in out)
        self.assertTrue("2 components written to file output.json" in out)

        self.assertTrue(os.path.isfile(self.OUTPUTFILE1))
        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE1)
        self.assertIsNotNone(sbom)
        self.assertEqual(2, len(sbom.components))

        self.assertEqual("Angular", sbom.components[0].name)
        self.assertEqual("15.2.6", sbom.components[0].version)
        val = CycloneDxSupport.get_ext_ref_source_url(sbom.components[0])
        self.assertEqual("https://github.com/angular/angular", val)

        self.assertEqual("certifi", sbom.components[1].name)
        self.assertEqual("2022.12.7", sbom.components[1].version)

        self.delete_file(self.OUTPUTFILE1)
