# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

from capycli.common.capycli_bom_support import CaPyCliBom
from capycli.dependencies.nuget import GetNuGetDependencies
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestGetDependenciesNuget(TestBase):
    INPUTFILE1 = "Nuget1.csproj"
    INPUTFILE2 = "Nuget.sln"
    OUTPUTFILE1 = "output.json"

    def test_show_help(self) -> None:
        sut = GetNuGetDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("python")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("Usage: capycli getdependencies nuget" in out)

    def test_no_input_file_specified(self) -> None:
        try:
            sut = GetNuGetDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("python")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_file_not_found(self) -> None:
        try:
            sut = GetNuGetDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("python")
            args.inputfile = "DOESNOTEXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_no_output_file_specified(self) -> None:
        try:
            sut = GetNuGetDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("python")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_csproj(self) -> None:
        sut = GetNuGetDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("python")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE1
        args.verbose = True
        args.debug = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE1 in out)
        self.assertTrue("Writing new SBOM to output.json" in out)
        self.assertTrue("3 components items written to file" in out)

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE1)
        self.assertIsNotNone(sbom)
        self.assertEqual(3, len(sbom.components))
        self.assertEqual("DocumentFormat.OpenXml", sbom.components[0].name)
        self.assertEqual("2.12.3", sbom.components[0].version)
        self.assertEqual("Tethys.Logging", sbom.components[1].name)
        self.assertEqual("1.6.0", sbom.components[1].version)
        self.assertEqual("Tethys.Logging.Controls.NET5", sbom.components[2].name)
        self.assertEqual("1.6.0", sbom.components[2].version)

        self.delete_file(self.OUTPUTFILE1)

    def test_sln(self) -> None:
        sut = GetNuGetDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("python")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE2)
        args.outputfile = self.OUTPUTFILE1
        args.verbose = True
        args.debug = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE2 in out)
        self.assertTrue("Writing new SBOM to output.json" in out)
        self.assertTrue("5 components items written to file" in out)

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE1)
        self.assertIsNotNone(sbom)
        self.assertEqual(5, len(sbom.components))
        self.assertEqual("DatabaseProvider", sbom.components[0].name)
        self.assertEqual("1.8.1", sbom.components[0].version)
        self.assertEqual("DocumentFormat.OpenXml", sbom.components[1].name)
        self.assertEqual("2.12.3", sbom.components[1].version)
        self.assertEqual("Serilog.AspNetCore", sbom.components[2].name)
        self.assertEqual("6.1.0", sbom.components[2].version)
        self.assertEqual("Tethys.Logging", sbom.components[3].name)
        self.assertEqual("1.6.0", sbom.components[3].version)
        self.assertEqual("Tethys.Logging.Controls.NET5", sbom.components[4].name)
        self.assertEqual("1.6.0", sbom.components[4].version)

        self.delete_file(self.OUTPUTFILE1)
