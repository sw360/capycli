# -------------------------------------------------------------------------------
# Copyright (c) 2025 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

import pytest
import responses

# from capycli.common import json_support
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.dependencies.rust import GetRustDependencies
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestGetDependenciesRust(TestBase):
    OUTPUTFILE = "output.json"
    INPUT_PACKAGE = "rust_package"
    INPUT_WORKSPACE = "rust_workspace/cyclonedx-rust-cargo"
    INPUT_METADATA = "rust_metadata"

    def test_show_help(self) -> None:
        sut = GetRustDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("rust")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: capycli getdependencies rust" in out)

    def test_no_input_file_specified(self) -> None:
        try:
            sut = GetRustDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("rust")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_folder_not_found(self) -> None:
        try:
            sut = GetRustDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("rust")
            args.inputfile = "DOESNOTEXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_no_output_file_specified(self) -> None:
        try:
            sut = GetRustDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("rust")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUT_PACKAGE)

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_simple_bom(self) -> None:
        sut = GetRustDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("rust")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUT_PACKAGE)
        args.outputfile = self.OUTPUTFILE
        args.verbose = True
        args.debug = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("Analyzing project file:" in out)
        self.assertTrue("Found package:" in out)
        self.assertTrue("Found package: betterapp, version: 0.1.0" in out)
        self.assertTrue("Analyzing lock file..." in out)
        self.assertTrue("anstream, 0.6.21" in out)
        self.assertTrue("clap, 4.5.53" in out)
        self.assertTrue("Ignoring package: betterapp, 0.1.0" in out)
        self.assertTrue("Ignoring local dependency: siemens_lib, 0.1.0" in out)

        self.delete_file(self.OUTPUTFILE)

    @responses.activate
    @pytest.mark.skip
    def test_get_metadata(self) -> None:
        sut = GetRustDependencies()
        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("rust")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUT_METADATA)
        args.outputfile = self.OUTPUTFILE
        args.verbose = True
        args.debug = True
        args.search_meta_data = True

        # for get meta-data
        responses.add(
            responses.GET,
            url="https://crates.io/api/v1/crates/clap/4.5.53",
            body="""
            {
                "version": {
                    "id": 1761942,
                    "crate": "clap",
                    "num": "4.5.53",
                    "dl_path": "/api/v1/crates/windows-sys/0.61.2/download",
                    "license": "MIT OR Apache-2.0",
                    "links": {},
                    "crate_size": 2517186,
                    "published_by": {
                        "id": 64539,
                        "login": "kennykerr",
                        "name": "Kenny Kerr",
                        "avatar": "https://avatars.githubusercontent.com/u/9845234?v=4",
                        "url": "https://github.com/kennykerr"
                    },
                    "audit_actions": [],
                    "checksum": "ae137229bcbd6cdf0f7b80a31df61766145077ddf49416a728b02cb3921ff3fc",
                    "rust_version": "1.71",
                    "has_lib": "True",
                    "description": "A simple to use, efficient, and full-featured Command Line Argument Parser",
                    "homepage": "None",
                    "documentation": "None",
                    "repository": "https://github.com/clap-rs/clap"
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for is_sourcefile_accessible()
        responses.add(
            responses.HEAD,
            url="https://github.com/clap-rs/clap/archive/tags/4.5.53.zip",
            body="""
            """,
            status=200,
            content_type="application/json"
        )

        out = self.capture_stdout(sut.run, args)
        # json_support.write_json_to_file(out, "STDOUT.TXT")
        self.assertTrue("Analyzing project file:" in out)
        self.assertTrue("Found package:" in out)
        self.assertTrue("Found package: betterapp, version: 0.1.0" in out)
        self.assertTrue("Analyzing lock file..." in out)
        self.assertTrue("Ignoring package: betterapp, 0.1.0" in out)
        self.assertTrue("Ignoring local dependency: siemens_lib, 0.1.0" in out)
        self.assertTrue("Retrieving package meta data" in out)
        self.assertTrue("Checking meta-data:" in out)
        self.assertTrue("clap, 4.5.53" in out)
        self.assertTrue("Writing new SBOM to output.json" in out)
        self.assertTrue("1 component items written to file" in out)

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE)
        self.assertIsNotNone(sbom)
        self.assertEqual(1, len(sbom.components))
        self.assertEqual("clap", sbom.components[0].name)
        self.assertEqual("4.5.53", sbom.components[0].version)
        self.assertEqual("A simple to use, efficient, and full-featured Command Line Argument Parser",
                         sbom.components[0].description)
        self.assertEqual(
            "https://github.com/clap-rs/clap",
            str(CycloneDxSupport.get_ext_ref_website(sbom.components[0])))
        self.assertEqual(
            "https://github.com/clap-rs/clap",
            str(CycloneDxSupport.get_ext_ref_repository(sbom.components[0])))

        self.assertEqual(1, len(sbom.components[0].licenses))
        lic = sbom.components[0].licenses[0]
        self.assertEqual("MIT OR Apache-2.0", lic.value)

        self.assertEqual(
            "https://github.com/clap-rs/clap/archive/tags/4.5.53.zip",
            str(CycloneDxSupport.get_ext_ref_source_url(sbom.components[0])))

        self.delete_file(self.OUTPUTFILE)


if __name__ == "__main__":
    APP = TestGetDependenciesRust()
    APP.test_get_metadata()
