# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
from typing import List

from capycli.bom.bom_convert import BomConvert
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestBomConvert(TestBase):
    INPUTFILE = "sbom_for_check_prerequisites.json"
    INPUTFILE_TEXT = "plaintext.txt"
    INPUTFILE_LEGACY = "legacy.json"
    OUTPUTFILE = "output.json"

    def test_show_help(self) -> None:
        sut = BomConvert()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("convert")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli bom convert" in out)

    def test_no_input_file(self) -> None:
        try:
            sut = BomConvert()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("convert")

            self.add_login_response()

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_input_file_not_found(self) -> None:
        try:
            sut = BomConvert()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("convert")
            args.inputfile = "DOES_NOT_EXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_no_input_format(self) -> None:
        try:
            sut = BomConvert()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("convert")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_no_output_file(self) -> None:
        try:
            sut = BomConvert()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("convert")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)
            args.inputformat = "text"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_no_output_format(self) -> None:
        sut = BomConvert()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("convert")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)
        args.inputformat = "text"
        args.outputfile = self.OUTPUTFILE

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("No output format specified, defaulting to sbom" in out)

    def test_invalid_input_file(self) -> None:
        sut = BomConvert()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("convert")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_TEXT)
        args.inputformat = "SBOM"
        args.outputfile = self.OUTPUTFILE

        try:
            self.capture_stdout(sut.run, args)
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    @staticmethod
    def compare_text_files(filename1: str, filename2: str, show_result: bool = False) -> List[str]:
        differences = []

        # reading files
        with open(filename1, "r", encoding="utf-8") as f1:
            f1_data = f1.readlines()

        with open(filename2, "r", encoding="utf-8") as f2:
            f2_data = f2.readlines()

        if len(f1_data) != len(f2_data):
            text = f"Number of lines does not match: {len(f1_data)} <-> {len(f2_data)}"
            if show_result:
                print(text)
            differences.append(text)

        i = 0
        for line1 in f1_data:
            line2 = f2_data[i]
            if line1 == line2:
                if show_result:
                    print("Line ", i, ": IDENTICAL")
            else:
                differences.append(f"Line {i} is different: {line1} <-> {line2}")
                if show_result:
                    print("Line ", i, ":")
                    print("\tFile 1:", line1, end='')
                    print("\tFile 2:", line2, end='')
            i += 1

        return differences

    def test_convert_plain_to_plain(self) -> None:
        sut = BomConvert()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("convert")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_TEXT)
        args.outputfile = self.OUTPUTFILE
        args.inputformat = "text"
        args.outputformat = "text"
        args.verbose = True
        args.debug = True

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue(self.INPUTFILE_TEXT in out)
        self.assertTrue("4 components read from" in out)
        self.assertTrue("4 components written to" in out)
        self.assertTrue(self.OUTPUTFILE in out)

        result = self.compare_text_files(args.inputfile, args.outputfile)
        self.assertTrue(len(result) == 0)

    def test_convert_legacy_to_legacy(self) -> None:
        sut = BomConvert()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("convert")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_LEGACY)
        args.outputfile = self.OUTPUTFILE
        args.inputformat = "legacy"
        args.outputformat = "legacy"
        args.verbose = True
        args.debug = True

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue(self.INPUTFILE_LEGACY in out)
        self.assertTrue("4 components read from" in out)
        self.assertTrue("4 components written to" in out)
        self.assertTrue(self.OUTPUTFILE in out)


if __name__ == '__main__':
    APP = TestBomConvert()
    APP.test_convert_legacy_to_legacy()
