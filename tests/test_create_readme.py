# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

from capycli.main.result_codes import ResultCode
from capycli.project.create_readme import CreateReadmeOss
from tests.test_base import AppArguments, TestBase


class TestCreateReadmeOss(TestBase):
    CONFIG_FILE = "readme_oss_config.json"
    CONFIG_FILE_INVALID = "plaintext.txt"
    OUTPUTFILE = "output.json"

    def test_show_help(self) -> None:
        sut = CreateReadmeOss()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createreadme")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli project createreadme" in out)

    def test_no_input_file(self) -> None:
        try:
            sut = CreateReadmeOss()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("createreadme")

            self.add_login_response()

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_no_output_file(self) -> None:
        try:
            sut = CreateReadmeOss()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("createreadme")
            args.inputfile = "DOES_NOT_EXIST"

            self.add_login_response()

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_input_file_not_found(self) -> None:
        try:
            sut = CreateReadmeOss()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("createreadme")
            args.inputfile = "DOES_NOT_EXIST"
            args.outputfile = self.OUTPUTFILE

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_error_reading_input_file(self) -> None:
        try:
            sut = CreateReadmeOss()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("createreadme")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.CONFIG_FILE_INVALID)
            args.outputfile = self.OUTPUTFILE

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_create_readme(self) -> None:
        sut = CreateReadmeOss()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createreadme")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.CONFIG_FILE)
        args.outputfile = self.OUTPUTFILE
        args.verbose = True
        args.debug = True

        self.delete_file(self.OUTPUTFILE)
        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Reading config file" in out)
        self.assertTrue(args.inputfile in out)
        self.assertTrue("Reading CLI files..." in out)
        self.assertTrue("Reading cli-support 1.3" in out)
        self.assertTrue("Creating Readme_OSS..." in out)
        self.assertTrue("Writing cli-support" in out)

        self.assertTrue(os.path.isfile(self.OUTPUTFILE))
        # self.delete_file(self.OUTPUTFILE)
