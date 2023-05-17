# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

from capycli.bom.show_bom import ShowBom
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestShowBom(TestBase):
    INPUTFILE = "sbom.cyclonedx.simple.json"

    def test_show_help(self) -> None:
        sut = ShowBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("show")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: capycli bom show" in out)

    def test_no_file_specified(self) -> None:
        try:
            sut = ShowBom()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("show")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_file_not_found(self) -> None:
        try:
            sut = ShowBom()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("show")
            args.inputfile = "DOESNOTEXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_simple_bom(self) -> None:
        sut = ShowBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("show")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestShowBom.INPUTFILE)

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("colorama, 0.4.3" in out)
        self.assertTrue("python, 3.8" in out)
        self.assertTrue("tomli, 2.0.1" in out)
        self.assertTrue("wheel, 0.34.2" in out)
        self.assertTrue("4 items in bill of material" in out)
