# -------------------------------------------------------------------------------
# Copyright (c) 2022-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
from typing import Any, Dict, List

import capycli.bom.filter_bom
import capycli.common.json_support
import capycli.common.script_base
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestBomFilter(TestBase):
    INPUTFILE_EMPTY = "sbom_no_components.json"
    INPUTFILE_INVALID = "plaintext.txt"
    INPUTFILE1 = "sbom_with_sw360.json"
    OUTPUTFILE = "output.json"
    FILTERFILE = "test_bom_filter.json"
    FILTERFILE_INCLUDE = "test_bom_filter_include.json"

    def test_show_help(self) -> None:
        sut = capycli.bom.filter_bom.FilterBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("Usage: CaPyCli bom filter [-h] [-v]" in out)

    def test_app_bom_no_input_file_specified(self):
        db = capycli.bom.filter_bom.FilterBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, sysex.code)

    def test_app_bom_input_file_not_found(self) -> None:
        db = capycli.bom.filter_bom.FilterBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        args.inputfile = "DOESNOTEXIST"
        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, sysex.code)

    def test_app_bom_no_filter_file_specified(self) -> None:
        db = capycli.bom.filter_bom.FilterBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_EMPTY)

        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, sysex.code)

    def test_app_bom_no_filter_not_found(self) -> None:
        db = capycli.bom.filter_bom.FilterBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_EMPTY)
        args.filterfile = "DOESNOTEXIST"

        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, sysex.code)

    def test_app_bom_no_output_file_specified(self) -> None:
        db = capycli.bom.filter_bom.FilterBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_EMPTY)
        args.filterfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_EMPTY)

        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, sysex.code)

    def test_app_bom_input_file_invalid(self) -> None:
        db = capycli.bom.filter_bom.FilterBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_INVALID)
        args.filterfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_INVALID)
        args.outputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.OUTPUTFILE)

        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, sysex.code)

    def test_add_single_item(self) -> None:
        sut = capycli.bom.filter_bom.FilterBom()

        inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_EMPTY)
        outputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.OUTPUTFILE)
        filterfile = os.path.join(os.path.dirname(__file__), "fixtures", self.FILTERFILE)

        # clean any existing test files
        self.delete_file(outputfile)
        self.delete_file(filterfile)

        # create filter file that adds a single component
        filter: Dict[str, Any] = {}
        filter_entries: List[Dict[str, Any]] = []
        filter_entry: Dict[str, Any] = {}
        component: Dict[str, Any] = {}
        component["Name"] = "newdummy"
        component["Version"] = "99.99"
        filter_entry["component"] = component
        filter_entry["Mode"] = "add"

        filter_entries.append(filter_entry)
        filter["Components"] = filter_entries

        capycli.common.json_support.write_json_to_file(filter, filterfile)

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        args.inputfile = inputfile
        args.outputfile = outputfile
        args.filterfile = filterfile

        sut.run(args)
        self.assertTrue(os.path.exists(outputfile), "Filter output file not created!")
        bom = CaPyCliBom.read_sbom(outputfile)
        self.assertEqual(1, len(bom.components))
        self.assertEqual(component["Name"], bom.components[0].name)
        self.assertEqual(component["Version"], bom.components[0].version)

        # clean test files
        self.delete_file(outputfile)
        self.delete_file(filterfile)

    def test_add_single_item_to_existing_bom(self) -> None:
        sut = capycli.bom.filter_bom.FilterBom()

        inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        outputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.OUTPUTFILE)
        filterfile = os.path.join(os.path.dirname(__file__), "fixtures", self.FILTERFILE)

        # clean any existing test files
        self.delete_file(outputfile)
        self.delete_file(filterfile)

        self.assertTrue(os.path.exists(inputfile), "Filter input file not found!")

        # create filter file that adds a single component
        filter: Dict[str, Any] = {}
        filter_entries: List[Dict[str, Any]] = []
        filter_entry: Dict[str, Any] = {}
        component: Dict[str, Any] = {}
        component["Name"] = "newdummy"
        component["Version"] = "99.99"
        filter_entry["component"] = component
        filter_entry["Mode"] = "add"

        filter_entries.append(filter_entry)
        filter["Components"] = filter_entries

        capycli.common.json_support.write_json_to_file(filter, filterfile)

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        args.inputfile = inputfile
        args.outputfile = outputfile
        args.filterfile = filterfile
        args.debug = True
        args.verbose = True

        sut.run(args)
        self.assertTrue(os.path.exists(outputfile), "Filter output file not created!")
        bom = CaPyCliBom.read_sbom(outputfile)
        self.assertEqual(5, len(bom.components))
        self.assertEqual(component["Name"], bom.components[1].name)
        self.assertEqual(component["Version"], bom.components[1].version)

        # clean test files
        self.delete_file(outputfile)
        self.delete_file(filterfile)

    def test_add_item_with_include(self) -> None:
        sut = capycli.bom.filter_bom.FilterBom()

        inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        outputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.OUTPUTFILE)
        filterfile = os.path.join(os.path.dirname(__file__), "fixtures", self.FILTERFILE)
        filterfile_include = os.path.join(os.path.dirname(__file__), "fixtures", self.FILTERFILE_INCLUDE)

        # clean any existing test files
        self.delete_file(outputfile)
        self.delete_file(filterfile)
        self.delete_file(filterfile_include)

        self.assertTrue(os.path.exists(inputfile), "Filter input file not found!")

        # create filter file to be included
        filter: Dict[str, Any] = {}
        filter_entries: List[Dict[str, Any]] = []
        filter_entry: Dict[str, Any] = {}
        component: Dict[str, Any] = {}
        component["Name"] = "xxx"
        component["Version"] = "99.99"
        filter_entry["component"] = component
        filter_entry["Mode"] = "INVALID"

        filter_entries.append(filter_entry)
        filter["Components"] = filter_entries

        capycli.common.json_support.write_json_to_file(filter, filterfile_include)

        # create filter file that adds a single component
        filter = {}
        filter_entries = []
        filter_entry = {}
        component = {}
        component["Name"] = "colora*"
        component["Version"] = "0.4.6"
        filter_entry["component"] = component
        filter_entry["Mode"] = "remove"
        includes = []
        includes.append(self.FILTERFILE_INCLUDE)
        includes.append("DOES_NOT_EXIST")

        filter_entries.append(filter_entry)
        filter["Components"] = filter_entries
        filter["Include"] = includes

        capycli.common.json_support.write_json_to_file(filter, filterfile)

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        args.inputfile = inputfile
        args.outputfile = outputfile
        args.filterfile = filterfile
        args.debug = True
        args.verbose = True

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue(self.INPUTFILE1 in out)
        self.assertTrue(self.FILTERFILE in out)
        self.assertTrue(self.FILTERFILE_INCLUDE in out)
        self.assertTrue("Invalid filter mode for xxx, 99.99: INVALID" in out)
        self.assertTrue("DOES_NOT_EXIST does not exist!" in out)
        self.assertTrue(self.OUTPUTFILE in out)

        self.assertTrue(os.path.exists(outputfile), "Filter output file not created!")
        bom = CaPyCliBom.read_sbom(outputfile)
        self.assertEqual(3, len(bom.components))

        # clean test files
        self.delete_file(outputfile)
        self.delete_file(filterfile)
        self.delete_file(filterfile_include)

    def test_remove_single_item_by_purl(self) -> None:
        sut = capycli.bom.filter_bom.FilterBom()

        inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        outputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.OUTPUTFILE)
        filterfile = os.path.join(os.path.dirname(__file__), "fixtures", self.FILTERFILE)

        # clean any existing test files
        self.delete_file(outputfile)
        self.delete_file(filterfile)

        self.assertTrue(os.path.exists(inputfile), "Filter input file not found!")

        # create filter file that adds a single component
        filter: Dict[str, Any] = {}
        filter_entries: List[Dict[str, Any]] = []
        filter_entry: Dict[str, Any] = {}
        component: Dict[str, Any] = {}
        component["RepositoryId"] = "pkg:pypi/tomli@2.0.1"
        filter_entry["component"] = component
        filter_entry["Mode"] = "remove"

        filter_entries.append(filter_entry)
        filter["Components"] = filter_entries

        capycli.common.json_support.write_json_to_file(filter, filterfile)

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        args.inputfile = inputfile
        args.outputfile = outputfile
        args.filterfile = filterfile

        sut.run(args)
        self.assertTrue(os.path.exists(outputfile), "Filter output file not created!")

        bom = CaPyCliBom.read_sbom(outputfile)
        self.assertEqual(3, len(bom.components))

        # clean test files
        self.delete_file(outputfile)
        self.delete_file(filterfile)

    def test_update_single_item(self) -> None:
        sut = capycli.bom.filter_bom.FilterBom()

        inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        outputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.OUTPUTFILE)
        filterfile = os.path.join(os.path.dirname(__file__), "fixtures", self.FILTERFILE)

        # clean any existing test files
        self.delete_file(outputfile)
        self.delete_file(filterfile)

        self.assertTrue(os.path.exists(inputfile), "Filter input file not found!")

        # create filter file that adds a single component
        filter: Dict[str, Any] = {}
        filter_entries: List[Dict[str, Any]] = []
        filter_entry: Dict[str, Any] = {}
        component: Dict[str, Any] = {}
        component["Name"] = "tomli"
        component["Version"] = "2.0.1"
        component["Language"] = "Go"
        component["SourceFileUrl"] = "https://somewhere/tomli.zip"
        component["SourceFile"] = "tomli.zip"
        component["BinaryFile"] = "tomli.whl"
        component["RepositoryType"] = "package-url"
        component["RepositoryId"] = "pkg:pypi/tomli@99.99.99"
        component["Sw360Id"] = "007"
        filter_entry["component"] = component
        filter_entry["Mode"] = "add"

        filter_entries.append(filter_entry)
        filter["Components"] = filter_entries

        capycli.common.json_support.write_json_to_file(filter, filterfile)

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        args.inputfile = inputfile
        args.outputfile = outputfile
        args.filterfile = filterfile
        args.verbose = True

        sut.run(args)
        self.assertTrue(os.path.exists(outputfile), "Filter output file not created!")

        bom = CaPyCliBom.read_sbom(outputfile)
        self.assertEqual(4, len(bom.components))
        self.assertEqual(component["Name"], bom.components[2].name)
        self.assertEqual(component["Version"], bom.components[2].version)
        self.assertEqual(component["RepositoryId"], bom.components[2].purl.to_string())
        self.assertEqual(component["SourceFileUrl"], str(CycloneDxSupport.get_ext_ref_source_url(bom.components[2])))
        self.assertEqual(component["SourceFile"], str(CycloneDxSupport.get_ext_ref_source_file(bom.components[2])))
        self.assertEqual(
            component["Language"],
            CycloneDxSupport.get_property_value(bom.components[2], CycloneDxSupport.CDX_PROP_LANGUAGE))
        self.assertEqual(
            component["Sw360Id"],
            CycloneDxSupport.get_property_value(bom.components[2], CycloneDxSupport.CDX_PROP_SW360ID))

        # clean test files
        self.delete_file(outputfile)
        self.delete_file(filterfile)


if __name__ == "__main__":
    lib = TestBomFilter()
    lib.test_remove_single_item_by_purl()
