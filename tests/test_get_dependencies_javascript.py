# -------------------------------------------------------------------------------
# Copyright (c) 2022-2025 Siemens
# All Rights Reserved.
# Author: gernot.hillier@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
from typing import Any, Dict

from cyclonedx.model import XsUri
from cyclonedx.model.component import Component

import capycli.common.script_base
import capycli.dependencies.javascript
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomCreator
from capycli.common.json_support import write_json_to_file
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestGetDependenciesJavascript(TestBase):
    INPUTFILE1 = "package-lock.json"
    INPUTFILE2 = "package-lock-3.json"
    OUTPUTFILE1 = "output.json"
    OUTPUTFILE2 = "output-3.json"

    def create_package_lock_1(self, filename: str) -> None:
        pl: Dict[str, Any] = {}
        pl["name"] = "APP"
        pl["version"] = "0.0.1"
        pl["lockfileVersion"] = 1
        pl["requires"] = True

        dependencies = {}

        dep1: Dict[str, Any] = {}
        dep1["version"] = "1.0.0"
        dep1["resolved"] = "artifactory/api/npm/npm-all/@agm/core/-/core-1.0.0.tgz"
        dep1["integrity"] = "sha1-sqd9GPv/4EzVyQzy6tQaVmP4mGI="
        dep1["requires"] = {}
        dep1["dev"] = "true"
        dependencies["@agm/core"] = dep1

        dep2: Dict[str, Any] = {}
        dep2["version"] = "0.10.3"
        dep2["resolved"] = "artifactory/api/npm/npm-all/zone.js/-/zone.js-0.10.3.tgz"
        dep2["integrity"] = "sha1-Pl5NoDxgfJ3NkuN901aHoUoUDBY="
        dependencies["zone.js"] = dep2

        pl["dependencies"] = dependencies

        write_json_to_file(pl, filename)

    def create_package_lock_3(self, filename: str) -> None:
        pl: Dict[str, Any] = {}
        pl["name"] = "APP"
        pl["version"] = "0.0.3"
        pl["lockfileVersion"] = 3
        pl["requires"] = True

        packages: Dict[str, Any] = {}

        dep1: Dict[str, Any] = {}
        dep1["version"] = "3.0.0"
        dep1["resolved"] = "artifactory/api/npm/npm-all/@angular/router/-/router-3.0.0.tgz"
        dep1["integrity"] = "sha1-sqd9GUfj/&hfTGwhfiwmGI="
        dep1["requires"] = {}
        dep1["dev"] = "true"
        packages["@angular/router"] = dep1

        dep2: Dict[str, Any] = {}
        dep2["version"] = "7.8.0"
        dep2["resolved"] = "artifactory/api/npm/npm-all/rxjs/-/rxjs-7.8.0.tgz"
        dep2["integrity"] = "sha1-Pl5NoDxgfJ3NkuN901aHoUoUDBY="
        dep2["requires"] = {}
        packages["rxjs"] = dep2

        pl["packages"] = packages

        write_json_to_file(pl, filename)

    def test_show_help(self) -> None:
        sut = capycli.dependencies.javascript.GetJavascriptDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("javascript")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("CaPyCli getdependencies javascript" in out)

    def test_no_input_file_specified(self) -> None:
        try:
            sut = capycli.dependencies.javascript.GetJavascriptDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("javascript")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_file_not_found(self) -> None:
        try:
            sut = capycli.dependencies.javascript.GetJavascriptDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("javascript")
            args.inputfile = "DOESNOTEXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_no_output_file_specified(self) -> None:
        try:
            sut = capycli.dependencies.javascript.GetJavascriptDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("javascript")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_convert_package_lock(self) -> None:
        self.create_package_lock_1("test_package_lock_1.json")
        sut = capycli.dependencies.javascript.GetJavascriptDependencies()
        sbom = sut.convert_package_lock("test_package_lock_1.json")
        self.assertEqual(1, len(sbom.components))

        self.delete_file("test_package_lock_1.json")

    def test_convert_package_lock_3(self) -> None:
        self.create_package_lock_3("test_package_lock_3.json")
        sut = capycli.dependencies.javascript.GetJavascriptDependencies()
        sbom = sut.convert_package_lock("test_package_lock_3.json")
        print(type(sbom))
        print(sbom.components)
        self.assertEqual(1, len(sbom.components))

        self.delete_file("test_package_lock_3.json")

    def test_try_find_metadata_simple(self) -> None:
        self.create_package_lock_1("test_package_lock_1.json")
        sut = capycli.dependencies.javascript.GetJavascriptDependencies()
        sbom = sut.convert_package_lock("test_package_lock_1.json")

        self.assertEqual(1, len(sbom.components))
        self.assertEqual("zone.js", sbom.components[0].name)
        self.assertEqual(None, sbom.components[0].description)
        val = CycloneDxSupport.get_ext_ref_source_url(sbom.components[0])
        self.assertEqual("", val)

        enhanced = sut.try_find_metadata(
            sbom,
            "https://registry.npmjs.org/")
        # print_json(enhanced)

        self.assertEqual(1, len(enhanced.components))
        self.assertEqual("zone.js", enhanced.components[0].name)
        self.assertEqual("Zones for JavaScript", enhanced.components[0].description)
        val = str(CycloneDxSupport.get_ext_ref_source_url(sbom.components[0]))
        self.assertEqual("github.com/angular/angular.git", val)

        self.delete_file("test_package_lock_1.json")

    def test_try_find_metadata_simple_3(self) -> None:
        self.create_package_lock_3("test_package_lock_3.json")
        sut = capycli.dependencies.javascript.GetJavascriptDependencies()
        sbom = sut.convert_package_lock("test_package_lock_3.json")

        self.assertEqual(1, len(sbom.components))
        self.assertEqual("rxjs", sbom.components[0].name)
        self.assertEqual(None, sbom.components[0].description)
        val = CycloneDxSupport.get_ext_ref_source_url(sbom.components[0])
        self.assertEqual("", val)

        enhanced = sut.try_find_metadata(
            sbom,
            "https://registry.npmjs.org/")
        # print_json(enhanced)

        self.assertEqual(1, len(enhanced.components))
        self.assertEqual("rxjs", enhanced.components[0].name)
        self.assertEqual("Reactive Extensions for modern JavaScript", enhanced.components[0].description)
        val = str(CycloneDxSupport.get_ext_ref_source_url(sbom.components[0]))
        self.assertEqual("https://github.com/reactivex/rxjs/archive/refs/tags/7.8.0.zip", val)

        self.delete_file("test_package_lock_3.json")

    def test_issue_100(self) -> None:
        bom = SbomCreator.create([], addlicense=True, addprofile=True, addtools=True)
        bom.components.add(Component(
            name="@types/fetch-jsonp",
            version="1.1.0"))

        sut = capycli.dependencies.javascript.GetJavascriptDependencies()
        enhanced = sut.try_find_metadata(
            bom,
            "https://registry.npmjs.org/")
        self.assertEqual(1, len(enhanced.components))

    def test_get_metadata_source_archive_url(self) -> None:
        sut = capycli.dependencies.javascript.GetJavascriptDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("javascript")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE1
        args.debug = True
        args.search_meta_data = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE1 in out)
        self.assertTrue("Writing new SBOM to output.json" in out)
        self.assertTrue("6 components written to file output.json" in out)

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE1)
        self.assertIsNotNone(sbom)
        self.assertEqual(6, len(sbom.components))

        self.assertEqual("tslib", sbom.components[4].name)
        self.assertEqual("2.3.1", sbom.components[4].version)
        val = str(CycloneDxSupport.get_ext_ref_source_url(sbom.components[4]))
        self.assertEqual("https://github.com/Microsoft/tslib/archive/refs/tags/2.3.1.zip", val)

        self.delete_file(self.OUTPUTFILE1)

    def test_get_metadata_source_archive_url_lockfile3(self) -> None:
        sut = capycli.dependencies.javascript.GetJavascriptDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("javascript")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE2)
        args.outputfile = self.OUTPUTFILE2
        args.debug = True
        args.search_meta_data = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE2 in out)
        self.assertTrue("Writing new SBOM to output-3.json" in out)
        self.assertTrue("3 components written to file output-3.json" in out)

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE2)
        self.assertIsNotNone(sbom)
        self.assertEqual(3, len(sbom.components))

        self.assertEqual("rxjs", sbom.components[2].name)
        self.assertEqual("7.8.1", sbom.components[2].version)
        val = CycloneDxSupport.get_ext_ref_source_url(sbom.components[1])
        print(val)
        self.assertEqual(XsUri("https://github.com/angular/angular/archive/refs/tags/15.2.9.zip"), val)

        self.delete_file(self.OUTPUTFILE2)

    def test_real_package_lock(self) -> None:
        sut = capycli.dependencies.javascript.GetJavascriptDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("javascript")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE1
        args.debug = True
        args.search_meta_data = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE1 in out)
        self.assertTrue("Writing new SBOM to output.json" in out)
        self.assertTrue("6 components written to file output.json" in out)

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE1)
        self.assertIsNotNone(sbom)
        self.assertEqual(6, len(sbom.components))
        self.assertEqual("@angular/common", sbom.components[0].name)
        self.assertEqual("13.1.1", sbom.components[0].version)
        self.assertEqual("@angular/core", sbom.components[1].name)
        self.assertEqual("13.1.1", sbom.components[1].version)
        self.assertEqual("@angular/forms", sbom.components[2].name)
        self.assertEqual("13.1.1", sbom.components[2].version)

        self.assertEqual("zone.js", sbom.components[5].name)
        self.assertEqual("0.11.4", sbom.components[5].version)

        self.delete_file(self.OUTPUTFILE1)

    def test_real_package_lock_3(self) -> None:
        sut = capycli.dependencies.javascript.GetJavascriptDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("javascript")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE2)
        args.outputfile = self.OUTPUTFILE2
        args.debug = True
        args.search_meta_data = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE2 in out)
        self.assertTrue("Writing new SBOM to output-3.json" in out)
        self.assertTrue("3 components written to file output-3.json" in out)

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE2)
        self.assertIsNotNone(sbom)
        self.assertEqual(3, len(sbom.components))
        self.assertEqual("@angular/animations", sbom.components[0].name)
        self.assertEqual("15.2.9", sbom.components[0].version)
        self.assertEqual("@angular/compiler", sbom.components[1].name)
        self.assertEqual("15.2.9", sbom.components[1].version)
        self.assertEqual("rxjs", sbom.components[2].name)
        self.assertEqual("7.8.1", sbom.components[2].version)

        self.delete_file(self.OUTPUTFILE2)


if __name__ == "__main__":
    APP = TestGetDependenciesJavascript()
    APP.test_get_metadata_source_archive_url_lockfile3()
