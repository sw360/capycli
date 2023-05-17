# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

from capycli.main.result_codes import ResultCode
from capycli.mapping.mapping_to_xlsx import MappingToExcelXlsx
from tests.test_base import AppArguments, TestBase


class TestBomMappingToXlsx(TestBase):
    INPUTFILE_INVALID = "plaintext.txt"
    INPUTFILE1 = "mapping_result.json"
    OUTPUTFILE = "output.xlsx"

    def test_show_help(self) -> None:
        sut = MappingToExcelXlsx()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("mapping")
        args.command.append("toxlsx")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli mapping toxlsx" in out)

    def test_app_bom_no_input_file_specified(self):
        db = MappingToExcelXlsx()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("mapping")
        args.command.append("toxlsx")
        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, sysex.code)

    def test_app_bom_input_file_not_found(self):
        db = MappingToExcelXlsx()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("mapping")
        args.command.append("toxlsx")
        args.inputfile = "DOESNOTEXIST"
        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, sysex.code)

    def test_app_bom_no_output_file_specified(self):
        db = MappingToExcelXlsx()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("mapping")
        args.command.append("toxlsx")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)

        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, sysex.code)

    def test_app_bom_input_file_invalid(self):
        db = MappingToExcelXlsx()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("mapping")
        args.command.append("toxlsx")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_INVALID)
        args.outputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.OUTPUTFILE)

        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, sysex.code)

    def test_create_mapping_html(self):
        sut = MappingToExcelXlsx()

        outputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.OUTPUTFILE)

        # clean any existing test files
        self.delete_file(outputfile)

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("mapping")
        args.command.append("toxlsx")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = outputfile
        args.debug = True

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "dump.txt")
        self.assertTrue("Loading mapping result" in out)
        self.assertTrue(self.INPUTFILE1 in out)
        self.assertTrue("Creating Excel sheet" in out)
        self.assertTrue(outputfile in out)

        self.assertTrue(os.path.exists(outputfile), "Xlsx output file not created!")

        # clean test files
        self.delete_file(outputfile)
