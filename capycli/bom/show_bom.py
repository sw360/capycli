# -------------------------------------------------------------------------------
# Copyright (c) 2019-2024 Siemens
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

from cyclonedx.factory.license import DisjunctiveLicense, LicenseExpression  # type: ignore
from cyclonedx.model import XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component

import capycli.common.script_base
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class ShowBom(capycli.common.script_base.ScriptBase):
    def __init__(self) -> None:
        self.has_error: bool = False
        self.verbose: bool = False

    def get_license(self, bomitem: Component) -> str:
        """
        Get the license information of a component as string.
        Only for CycloneDX 1.6 and later.
        """
        if not bomitem.licenses:
            return ""

        for license in bomitem.licenses:
            # CycloneDX 1.6
            if isinstance(license, DisjunctiveLicense):
                if license.id:  # supersedes name
                    return license.id
                if license.name:
                    return license.name

            if isinstance(license, LicenseExpression) and license.value:
                return license.value

            if license.id:
                return license.id

        return ""

    def display_bom(self, bom: Bom) -> None:
        """Print SBOM contents to stdout"""
        if not bom:
            print_yellow("  Empty SBOM!")
            return

        for bomitem in bom.components:
            print_text("  " + bomitem.name + ", " + bomitem.version)

            if self.verbose:
                if bomitem.purl:
                    print_text("    package-url: " + bomitem.purl.to_string())
                else:
                    print_yellow("    No package-url given!")
                    self.has_error = True

                sw360id = CycloneDxSupport.get_property_value(bomitem, CycloneDxSupport.CDX_PROP_SW360ID)
                if sw360id:
                    print_text("    SW360 id:" + sw360id)

                download_url: XsUri
                download_url = CycloneDxSupport.get_ext_ref_source_url(bomitem)
                if download_url:
                    print_text("    download URL: " + download_url.uri)
                else:
                    print_yellow("    No download URL given!")
                    self.has_error = True

                license = self.get_license(bomitem)
                if license:
                    print_text("    license: " + license)
                else:
                    print_yellow("    No license given!")

        print_text("\n" + str(len(bom.components)) + " items in bill of material\n")

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)

        print_text("\n" + capycli.get_app_signature() + " - Print SBOM contents to stdout\n")

        if args.help:
            print("usage: capycli bom show [-h] -i bomfile")
            print("")
            print("optional arguments:")
            print("-h, --help            show this help message and exit")
            print("-i INPUTFILE          input file to read from (JSON)")
            print("-v                    be verbose (show more details about purl, download URL, and license)")
            print("--forceerror          force an error exit code in case of prerequisite errors or warnings")
            return

        if not args.inputfile:
            LOG.error("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            LOG.error("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if args.verbose:
            self.verbose = True

        try:
            bom = CaPyCliBom.read_sbom(args.inputfile)
        except Exception as ex:
            print_red("Error reading SBOM: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)

        self.display_bom(bom)

        if args.force_error and self.has_error:
            sys.exit(ResultCode.RESULT_PREREQUISITE_ERROR)
