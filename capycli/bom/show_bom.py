# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

"""
Display the contents of a SBOM.
"""

import os
import sys
from typing import Any

from cyclonedx.model.bom import Bom

import capycli.common.script_base
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class ShowBom(capycli.common.script_base.ScriptBase):
    """Print SBOM contents to stdout"""
    def display_bom(self, bom: Bom, verbose: bool) -> None:
        if not bom:
            print_yellow("  Empty SBOM!")
            return

        for bomitem in bom.components:
            print_text("  " + bomitem.name + ", " + bomitem.version)

            if verbose:
                if bomitem.purl:
                    print_text("    package-url:" + bomitem.purl.to_string())

                sw360id = CycloneDxSupport.get_property_value(bomitem, CycloneDxSupport.CDX_PROP_SW360ID)
                if sw360id:
                    print_text("    SW360 id:" + sw360id)

                download_url = CycloneDxSupport.get_ext_ref_source_file(bomitem)
                if not download_url:
                    download_url = CycloneDxSupport.get_ext_ref_source_url(bomitem)
                if not download_url:
                    print_yellow("    No download URL given!")

        print_text("\n" + str(len(bom.components)) + " items in bill of material\n")

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)

        print_text("\n" + capycli.APP_NAME + ", " + capycli.get_app_version() + " - Print SBOM contents to stdout\n")

        if args.help:
            print("usage: capycli bom show [-h] -i bomfile")
            print("")
            print("optional arguments:")
            print("-h, --help            show this help message and exit")
            print("-i INPUTFILE          input file to read from (JSON)")
            print("-v                    be verbose")
            return

        if not args.inputfile:
            LOG.error("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            LOG.error("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        try:
            bom = CaPyCliBom.read_sbom(args.inputfile)
        except Exception as ex:
            print_red("Error reading SBOM: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)

        self.display_bom(bom, args.verbose)
