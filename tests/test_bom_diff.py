# -------------------------------------------------------------------------------
# Copyright (c) 2021-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, manuel.schaffer@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

import capycli.bom.diff_bom
import capycli.common.json_support
import capycli.common.script_base
from capycli.common.capycli_bom_support import CaPyCliBom
from capycli.common.json_support import load_json_file
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestBomDiff(TestBase):
    INPUTFILE1 = "sbom_for_download.json"
    INPUTFILE2 = "sbom_no_components.json"
    INPUTFILE3 = "sbom_for_download_diff.json"
    INPUTFILE4 = "sbom_for_diff1.json"
    INPUTFILE5 = "sbom_for_diff2.json"
    INPUTFILE_INVALID = "plaintext.txt"
    OUTPUTFILE = "output.json"
    OUTPUTFILE_MR = "output_mr.json"

    def test_show_help(self) -> None:
        sut = capycli.bom.diff_bom.DiffBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("diff")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli bom diff [-h]" in out)

    def test_app_bom_no_files_specified(self) -> None:
        db = capycli.bom.diff_bom.DiffBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("diff")
        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, sysex.code)

    def test_app_bom_only_one_file_specified(self) -> None:
        db = capycli.bom.diff_bom.DiffBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("diff")
        args.command.append("tests/bom_diff_1.json")
        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, sysex.code)

    def test_app_bom_first_file_not_found(self) -> None:
        db = capycli.bom.diff_bom.DiffBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("diff")
        args.command.append("tests/__not_available__.json")
        args.command.append("tests/bom_diff_1.json")
        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, sysex.code)

    def test_app_bom_second_file_not_found(self) -> None:
        db = capycli.bom.diff_bom.DiffBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("diff")
        args.command.append("tests/bom_diff_1.json")
        args.command.append("tests/__not_available__.json")
        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, sysex.code)

    def test_app_bom_cyclonedx_invalid_file1(self) -> None:
        db = capycli.bom.diff_bom.DiffBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("diff")
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_INVALID))
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1))

        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, sysex.code)

    def test_app_bom_cyclonedx_invalid_file2(self) -> None:
        db = capycli.bom.diff_bom.DiffBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("diff")
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1))
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_INVALID))

        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, sysex.code)

    def test_bom_identical(self) -> None:
        db = capycli.bom.diff_bom.DiffBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("diff")
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1))
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1))

        out = self.capture_stdout(db.run, args)
        self.assertTrue(self.INPUTFILE1 in out)
        self.assertTrue("Release exists in both SBOMs: certifi, 2022.12.7" in out)
        self.assertIsNotNone(db.equal_bom)
        self.assertIsNotNone(db.diff_bom)
        if db.diff_bom:
            self.assertEqual(1, len(db.equal_bom.components))
            self.assertEqual(0, len(db.diff_bom.components))

            self.assertEqual("certifi", db.equal_bom.components[0].name)
            self.assertEqual("2022.12.7", db.equal_bom.components[0].version)

    def test_bom_diff1(self) -> None:
        db = capycli.bom.diff_bom.DiffBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("diff")
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1))
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE2))

        out = self.capture_stdout(db.run, args)
        self.assertTrue(self.INPUTFILE1 in out)
        self.assertTrue("Release has been removed:     certifi, 2022.12.7" in out)
        self.assertIsNotNone(db.equal_bom)
        self.assertIsNotNone(db.diff_bom)
        if db.diff_bom:
            self.assertEqual(0, len(db.equal_bom.components))
            self.assertEqual(1, len(db.diff_bom.components))

            self.assertEqual("certifi", db.diff_bom.components[0].name)
            self.assertEqual("2022.12.7", db.diff_bom.components[0].version)

    def test_bom_diff2(self) -> None:
        db = capycli.bom.diff_bom.DiffBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("diff")
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1))
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE3))

        out = self.capture_stdout(db.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue(self.INPUTFILE1 in out)
        self.assertTrue("Release has been removed:     certifi, 2022.12.7" in out)
        self.assertTrue("New release:                  certifi, 2022.12.999" in out)
        self.assertIsNotNone(db.equal_bom)
        self.assertIsNotNone(db.diff_bom)
        if db.diff_bom:
            self.assertEqual(0, len(db.equal_bom.components))
            self.assertEqual(2, len(db.diff_bom.components))

            self.assertEqual("certifi", db.diff_bom.components[0].name)
            self.assertEqual("2022.12.7", db.diff_bom.components[0].version)
            self.assertEqual("certifi", db.diff_bom.components[1].name)
            self.assertEqual("2022.12.999", db.diff_bom.components[1].version)

    def test_app_bom_different_with_fileoutput(self) -> None:
        db = capycli.bom.diff_bom.DiffBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("diff")
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE4))
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE5))
        args.outputfile = self.OUTPUTFILE
        args.verbose = True
        args.all = True
        args.debug = True

        out = self.capture_stdout(db.run, args)
        self.assertTrue(self.INPUTFILE4 in out)
        self.assertTrue(self.INPUTFILE5 in out)
        self.assertTrue("Release exists in both SBOMs: Autofac, 6.2.0" in out)
        self.assertTrue("Release has been removed:     Tethys.Framework, 4.5.0" in out)
        self.assertTrue("Major update:                 AbrarJahin.DiffMatchPatch, 0.1.0 -> 9.1.0" in out)
        self.assertTrue("New release:                  Dummy, 9.9.9" in out)
        self.assertTrue("Minor update:                 certifi, 2022.12.7 -> 2022.12.99" in out)

        # check result JSON file
        self.assertTrue(os.path.isfile(self.OUTPUTFILE))
        result = load_json_file(self.OUTPUTFILE)

        self.assertEqual(5, len(result))
        self.assertEqual("Autofac", result[0]["Name"])
        self.assertEqual("6.2.0", result[0]["Version"])
        self.assertEqual("IDENTICAL", result[0]["Result"])

        self.assertEqual("Tethys.Framework", result[1]["Name"])
        self.assertEqual("4.5.0", result[1]["Version"])
        self.assertEqual("OBSOLETE", result[1]["Result"])

        self.assertEqual("AbrarJahin.DiffMatchPatch", result[2]["Name"])
        self.assertEqual("9.1.0", result[2]["Version"])
        self.assertEqual("MAJOR_UPDATE", result[2]["Result"])
        self.assertEqual("0.1.0", result[2]["VersionOld"])

        self.assertEqual("Dummy", result[3]["Name"])
        self.assertEqual("9.9.9", result[3]["Version"])
        self.assertEqual("NEW", result[3]["Result"])

        self.assertEqual("certifi", result[4]["Name"])
        self.assertEqual("2022.12.99", result[4]["Version"])
        self.assertEqual("MINOR_UPDATE", result[4]["Result"])
        self.assertEqual("2022.12.7", result[4]["VersionOld"])

        self.delete_file(self.OUTPUTFILE)

    def test_app_bom_different_with_fileoutput2(self) -> None:
        db = capycli.bom.diff_bom.DiffBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("diff")
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE4))
        args.command.append(os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE5))
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.OUTPUTFILE_MR

        out = self.capture_stdout(db.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue(self.INPUTFILE4 in out)
        self.assertTrue(self.INPUTFILE5 in out)
        self.assertTrue("Release has been removed:     AbrarJahin.DiffMatchPatch, 0.1.0" in out)
        self.assertTrue("Release exists in both SBOMs: Autofac, 6.2.0" in out)
        self.assertTrue("Release has been removed:     Tethys.Framework, 4.5.0" in out)
        self.assertTrue("Release has been removed:     certifi, 2022.12.7" in out)
        self.assertTrue("New release:                  AbrarJahin.DiffMatchPatch, 9.1.0" in out)
        self.assertTrue("New release:                  Dummy, 9.9.9" in out)
        self.assertTrue("New release:                  certifi, 2022.12.99" in out)

        # check diff result file
        self.assertTrue(os.path.isfile(self.OUTPUTFILE))
        bom = CaPyCliBom.read_sbom(self.OUTPUTFILE)
        self.assertEqual(6, len(bom.components))
        self.assertEqual("AbrarJahin.DiffMatchPatch", bom.components[0].name)
        self.assertEqual("0.1.0", bom.components[0].version)
        self.assertEqual("AbrarJahin.DiffMatchPatch", bom.components[1].name)
        self.assertEqual("9.1.0", bom.components[1].version)
        self.assertEqual("Dummy", bom.components[2].name)
        self.assertEqual("9.9.9", bom.components[2].version)
        self.assertEqual("Tethys.Framework", bom.components[3].name)
        self.assertEqual("4.5.0", bom.components[3].version)
        self.assertEqual("certifi", bom.components[4].name)
        self.assertEqual("2022.12.7", bom.components[4].version)
        self.assertEqual("certifi", bom.components[5].name)
        self.assertEqual("2022.12.99", bom.components[5].version)

        self.assertTrue(os.path.isfile(self.OUTPUTFILE_MR))
        bom = CaPyCliBom.read_sbom(self.OUTPUTFILE_MR)
        self.assertEqual(1, len(bom.components))
        self.assertEqual("Autofac", bom.components[0].name)
        self.assertEqual("6.2.0", bom.components[0].version)

        self.delete_file(args.outputfile)
        self.delete_file(args.write_mapresult)
