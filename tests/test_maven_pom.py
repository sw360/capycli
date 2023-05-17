# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

from capycli.dependencies.maven_pom import GetJavaMavenPomDependencies
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestGetJavaMavenPomDependencies(TestBase):
    INPUTFILE = "pom.xml"
    INPUTFILE_INVALID = "plaintext.txt"
    OUTPUTFILE = "output.json"

    def test_show_help(self) -> None:
        sut = GetJavaMavenPomDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("MavenPom")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("CaPyCli getdependencies mavenpom" in out)

    def test_no_input_file(self) -> None:
        try:
            sut = GetJavaMavenPomDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("MavenPom")

            self.add_login_response()

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_input_file_not_found(self) -> None:
        try:
            sut = GetJavaMavenPomDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("MavenPom")
            args.inputfile = "DOES_NOT_EXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_no_output_file(self) -> None:
        try:
            sut = GetJavaMavenPomDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("MavenPom")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_invalid_input_file(self) -> None:
        sut = GetJavaMavenPomDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("MavenPom")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_INVALID)
        args.outputfile = self.OUTPUTFILE

        try:
            self.capture_stdout(sut.run, args)
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, ex.code)

    def test_get_dependencies_from_maven_pom(self):
        sut = GetJavaMavenPomDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("MavenPom")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)
        args.outputfile = self.OUTPUTFILE
        args.verbose = True
        args.debug = True

        self.delete_file(self.OUTPUTFILE)
        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue(self.INPUTFILE in out)
        self.assertTrue("Writing new SBOM to" in out)
        self.assertTrue("Writing new SBOM to output.json" in out)
        self.assertTrue(self.OUTPUTFILE in out)

        self.assertTrue(os.path.isfile(self.OUTPUTFILE))

        self.delete_file(self.OUTPUTFILE)


if __name__ == '__main__':
    APP = TestGetJavaMavenPomDependencies()
    APP.test_invalid_input_file()
