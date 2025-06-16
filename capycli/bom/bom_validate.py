# -------------------------------------------------------------------------------
# Copyright (c) 2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import sys
from typing import Any

import capycli.common.json_support
import capycli.common.script_base
from capycli import get_logger
from capycli.bom.show_bom import ShowBom
from capycli.common.capycli_bom_support import CaPyCliBom
from capycli.common.print import print_green, print_text
from capycli.main.exceptions import CaPyCliException
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class BomValidate(capycli.common.script_base.ScriptBase):
    def __init__(self) -> None:
        self.has_error: bool = False
        self.verbose: bool = False

    def validate(self, inputfile: str, spec_version: str) -> bool:
        """Main validation method."""
        try:
            if not spec_version:
                print_text("No CycloneDX spec version specified, defaulting to 1.6")
                spec_version = "1.6"
            return CaPyCliBom.validate_sbom(inputfile, spec_version, False)
        except CaPyCliException as error:
            LOG.error(f"Error processing input file: {str(error)}")
            sys.exit(ResultCode.RESULT_GENERAL_ERROR)

    def check_arguments(self, args: Any) -> None:
        """Check input arguments."""
        if not args.inputfile:
            LOG.error("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            LOG.error("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

    def display_help(self) -> None:
        """Display (local) help."""
        print("usage: CaPyCli bom validate [-h] -i INPUTFILE [-version SpecVersion]")
        print("")
        print("optional arguments:")
        print("    -h, --help            Show this help message and exit")
        print("    -i INPUTFILE          Input BOM filename (JSON)")
        print("    -version SpecVersion  CycloneDX spec version to validate against: allowed are 1.4, 1.5, and 1.6")
        print("    -v                    be verbose (show more details about purl, download URL, and license)")
        print("    --forceerror          force an error exit code in case of validation errors or warnings")

    def run(self, args: Any) -> None:
        """Main method()"""
        print("\n" + capycli.get_app_signature() + " - Validate a CaPyCLI/CycloneDX SBOM\n")

        if args.help:
            self.display_help()
            return

        self.check_arguments(args)
        if args.debug:
            global LOG
            LOG = get_logger(__name__)

        if args.verbose:
            self.verbose = True

        self.has_error = not self.validate(args.inputfile, args.version)
        if not self.has_error:
            print_green("JSON file successfully validated against CycloneDX.")

        if self.verbose:
            try:
                bom = CaPyCliBom.read_sbom(args.inputfile)
            except Exception as ex:
                LOG.error("Error reading SBOM: " + repr(ex))
                sys.exit(ResultCode.RESULT_ERROR_READING_BOM)

            show_bom = ShowBom()
            show_bom.verbose = self.verbose
            print_text("Siemens Standard BOM checks")
            show_bom.display_bom(bom)
            if show_bom.has_error:
                self.has_error = True

        if args.force_error and self.has_error:
            sys.exit(ResultCode.RESULT_PREREQUISITE_ERROR)
