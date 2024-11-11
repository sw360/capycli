# -------------------------------------------------------------------------------
# Copyright (c) 2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

from capycli.bom.bom_validate import BomValidate
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestBomValidate(TestBase):
    INPUTFILE1 = "sbom.cyclonedx.simple.json"
    INPUTFILE2 = "sbom_1_6_invalid.json"
    INPUT_BAD = "plaintext.txt"

    def test_show_help(self) -> None:
        sut = BomValidate()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("validate")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli bom validate" in out)

    def test_input_file_not_specified(self) -> None:
        try:
            sut = BomValidate()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("validate")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_sbom_not_found(self) -> None:
        try:
            sut = BomValidate()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("validate")
            args.inputfile = "DOESNOTEXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_validate_sbom_no_spec(self) -> None:
        sut = BomValidate()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("validate")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("No CycloneDX spec version specified, defaulting to 1.6" in out)
        self.assertTrue("JSON file successfully validated" in out)

    def test_validate_sbom_1_6_ok(self) -> None:
        sut = BomValidate()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("validate")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.version = "1.6"

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("JSON file successfully validated" in out)

    def test_validate_sbom_1_4_ok(self) -> None:
        sut = BomValidate()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("validate")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.version = "1.4"

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("JSON file successfully validated" in out)

    def test_validate_sbom_1_6_error(self) -> None:
        try:
            sut = BomValidate()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("validate")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE2)
            args.version = "1.6"

            self.capture_stdout(sut.run, args)
            self.assertTrue(True, "Exception not reported!")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_GENERAL_ERROR, ex.code)


if __name__ == '__main__':
    APP = TestBomValidate()
    APP.test_sbom_not_found()
