# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import sys

# from enum import StrEnum  # not supported in Python 3.10.3
from enum import Enum
from typing import Any

from sortedcontainers import SortedSet

import capycli.common.json_support
import capycli.common.script_base
from capycli import get_logger
from capycli.common.capycli_bom_support import CaPyCliBom
from capycli.common.print import print_red, print_text
from capycli.main.exceptions import CaPyCliException
from capycli.main.result_codes import ResultCode

from .csv import CsvSupport
from .html import HtmlConversionSupport
from .legacy import LegacySupport
from .legacy_cx import LegacyCx
from .plaintext import PlainTextSupport

LOG = get_logger(__name__)


class BomFormat(str, Enum):
    # CaPyCLI flavor of Siemens Standard BOM/CycloneDX
    CAPYCLI = "capycli"
    # Siemens Standard BOM
    SBOM = "sbom"
    # plain text
    TEXT = "text"
    # CSV
    CSV = "csv"
    # CaPyCLI JSON
    LEGACY = "legacy"
    # CaPyCLI CycloneDX
    LEGACY_CX = "legacy-cx"
    # HTML
    HTML = "html"


class BomConvert(capycli.common.script_base.ScriptBase):
    def convert(self,
                inputfile: str,
                inputformat: str,
                outputfile: str,
                outputformat: str) -> None:
        """Main conversion method."""
        if not outputformat:
            # default is CaPyCLI
            outputformat = BomFormat.CAPYCLI

        cdx_components: SortedSet
        project = None
        sbom = None
        try:
            if inputformat == BomFormat.TEXT:
                cdx_components = SortedSet(PlainTextSupport.flatlist_to_cdx_components(inputfile))
                print_text(f"  {len(cdx_components)} components read from file {inputfile}")
            elif inputformat == BomFormat.CSV:
                cdx_components = SortedSet(CsvSupport.csv_to_cdx_components(inputfile))
                print_text(f"  {len(cdx_components)} components read from file {inputfile}")
            elif (inputformat == BomFormat.CAPYCLI) or (inputformat == BomFormat.SBOM):
                sbom = CaPyCliBom.read_sbom(inputfile)
                cdx_components = sbom.components
                project = sbom.metadata.component
                print_text(f"  {len(cdx_components)} components read from file {inputfile}")
            elif inputformat == BomFormat.LEGACY:
                cdx_components = SortedSet(LegacySupport.legacy_to_cdx_components(inputfile))
                print_text(f"  {len(cdx_components)} components read from file {inputfile}")
            elif inputformat == BomFormat.LEGACY_CX:
                sbom = LegacyCx.read_sbom(inputfile)
                cdx_components = sbom.components
                print_text(f"  {len(cdx_components)} components read from file {inputfile}")
            else:
                print_red("Unsupported input format!")
                sys.exit(ResultCode.RESULT_COMMAND_ERROR)
        except CaPyCliException as error:
            LOG.error(f"Error processing input file: {str(error)}")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        try:
            if outputformat == BomFormat.TEXT:
                PlainTextSupport.write_cdx_components_as_flatlist2(cdx_components, outputfile)
                print_text(f"  {len(cdx_components)} components written to file {outputfile}")
            elif outputformat == BomFormat.CSV:
                CsvSupport.write_cdx_components_as_csv(cdx_components, outputfile)
                print_text(f"  {len(cdx_components)} components written to file {outputfile}")
            elif outputformat == BomFormat.HTML:
                HtmlConversionSupport.write_cdx_components_as_html(cdx_components, outputfile, project)
                print_text(f"  {len(cdx_components)} components written to file {outputfile}")
            elif outputformat == BomFormat.CAPYCLI:
                if sbom:
                    CaPyCliBom.write_sbom(sbom, outputfile)
                    print_text(f"  {len(sbom.components)} components written to file {outputfile}")
                else:
                    CaPyCliBom.write_simple_sbom(cdx_components, outputfile)
                    print_text(f"  {len(cdx_components)} components written to file {outputfile}")
            elif outputformat == BomFormat.LEGACY:
                LegacySupport.write_cdx_components_as_legacy(cdx_components, outputfile)
                print_text(f"  {len(cdx_components)} components written to file {outputfile}")
            else:
                LOG.error("Unsupported output format!")
                sys.exit(ResultCode.RESULT_COMMAND_ERROR)
        except CaPyCliException as error:
            LOG.error(f"Error creating output file: {str(error)}")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

    def check_arguments(self, args: Any) -> None:
        """Check input arguments."""
        if not args.inputfile:
            LOG.error("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            LOG.error("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if not args.inputformat:
            LOG.error("No input format specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not args.outputfile:
            LOG.error("No output file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not args.outputformat:
            LOG.warning("No output format specified, defaulting to sbom")

    def display_help(self) -> None:
        """Display (local) help."""
        print("usage: CaPyCli bom convert [-h] [-i INPUTFILE] [-if {capycli,text,csv,legacy,legacy-cx}]")
        print("                           [-o OUTPUTFILE] [-of {capycli,text,csv,legacy,legacy-cx,html}]")
        print("")
        print("optional arguments:")
        print("    -h, --help            Show this help message and exit")
        print("    -i INPUTFILE          Input BOM filename (JSON)")
        print("    -o OUTPUTFILE         Output BOM filename")
        print("    -if INPUTFORMAT       Specify input file format: capycli|sbom|text|csv|legacy|legacy-cx")
        print("    -of OUTPUTFORMAT      Specify output file format: capycli|text|csv|legacy|html")

    def run(self, args):
        """Main method()"""
        print("\n" + capycli.APP_NAME + ", " + capycli.get_app_version() + " - Convert SBOM formats\n")

        if args.help:
            self.display_help()
            return

        self.check_arguments(args)
        if args.debug:
            global LOG
            LOG = get_logger(__name__)

        self.convert(args.inputfile, args.inputformat, args.outputfile, args.outputformat)
