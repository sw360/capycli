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


class TestCheckBom(TestBase):
    INPUTFILE = "sbom_with_sw360.json"
    INPUTFILE2 = "sbom_with_sw360_two_ids_missing.json"

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
        args.command.append("check")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestCheckBom.INPUTFILE)

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("colorama, 0.4.6" in out)
        self.assertTrue("python, 3.8" in out)
        self.assertTrue("tomli, 2.0.1" in out)
        self.assertTrue("wheel, 0.38.4" in out)

    def test_simple_bom_verbose(self) -> None:
        sut = ShowBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("check")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.verbose = True
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestCheckBom.INPUTFILE)

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("colorama, 0.4.6" in out)
        self.assertTrue("package-url:pkg:pypi/colorama@0.4.6" in out)
        self.assertTrue("SW360 id:9a2373710bd44769a2560dd31280901d" in out)
        self.assertTrue("python, 3.8" in out)
        self.assertTrue("package-url:pkg:pypi/python@3.8" in out)
        self.assertTrue("SW360 id:05c30bf89a512463260b57e84d99b38f" in out)
        self.assertTrue("tomli, 2.0.1" in out)
        self.assertTrue("package-url:pkg:pypi/tomli@2.0.1" in out)
        self.assertTrue("SW360 id:fa0d21eb17574ba9ae17e5c9b432558e" in out)
        self.assertTrue("wheel, 0.38.4" in out)
        self.assertTrue("package-url:pkg:pypi/wheel@0.38.4" in out)
        self.assertTrue("SW360 id:e0995819173d4ac8b1a4da3548935976" in out)
