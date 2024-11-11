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
from capycli.common.capycli_bom_support import CaPyCliBom
from capycli.main.exceptions import CaPyCliException
from capycli.main.result_codes import ResultCode
from capycli.common.print import print_text

LOG = get_logger(__name__)


class BomValidate(capycli.common.script_base.ScriptBase):
    def validate(self, inputfile: str, spec_version: str) -> None:
        """Main validation method."""
        try:
            if not spec_version:
                print_text("No CycloneDX spec version specified, defaulting to 1.6")
                spec_version = "1.6"
            CaPyCliBom.validate_sbom(inputfile, spec_version)
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

    def run(self, args: Any) -> None:
        """Main method()"""
        print("\n" + capycli.APP_NAME + ", " + capycli.get_app_version() + " - Validate a CaPyCLI/CycloneDX SBOM\n")

        if args.help:
            self.display_help()
            return

        self.check_arguments(args)
        if args.debug:
            global LOG
            LOG = get_logger(__name__)

        self.validate(args.inputfile, args.version)
