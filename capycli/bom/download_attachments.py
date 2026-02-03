# -------------------------------------------------------------------------------
# Copyright (c) 2020-2023 Siemens
# All Rights Reserved.
# Author: gernot.hillier@siemens.com, thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import os
import sys
from typing import Any, Tuple

import sw360.sw360_api
from cyclonedx.model.bom import Bom

import capycli.common.json_support
import capycli.common.script_base
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomWriter
from capycli.common.print import print_red, print_text, print_yellow
from capycli.common.script_support import ScriptSupport
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class BomDownloadAttachments(capycli.common.script_base.ScriptBase):
    """
    Download SW360 attachments as specified in the SBOM.
    """

    def download_attachments(self, sbom: Bom, source_folder: str, bompath: str = None,
                             attachment_types: Tuple[str] = ("COMPONENT_LICENSE_INFO_XML", "CLEARING_REPORT")) -> Bom:

        for component in sbom.components:
            item_name = ScriptSupport.get_full_name_from_component(component)
            print_text("  " + item_name)

            for ext_ref in component.external_references:
                if not ext_ref.comment:
                    continue
                found = False
                for at_type in attachment_types:
                    if ext_ref.comment.startswith(CaPyCliBom.FILE_COMMENTS[at_type]):
                        found = True
                if not found:
                    continue

                attachment_id = ext_ref.comment.split(", sw360Id: ")
                if len(attachment_id) != 2:
                    print_red("    No sw360Id for attachment!")
                    continue
                attachment_id = attachment_id[1]

                release_id = CycloneDxSupport.get_property_value(component, CycloneDxSupport.CDX_PROP_SW360ID)
                if not release_id:
                    print_red("    No sw360Id for release!")
                    continue
                print("   ", ext_ref.url, release_id, attachment_id)
                filename = os.path.join(source_folder, ext_ref.url)

                print_text("    Downloading file " + filename)
                try:
                    at_info = self.client.get_attachment(attachment_id)
                    at_info = {k: v for k, v in at_info.items()
                               if k.startswith("check")
                               or k.startswith("created")}
                    print(at_info)

                    self.client.download_release_attachment(filename, release_id, attachment_id)
                    ext_ref.url = filename
                    try:
                        if bompath:
                            CycloneDxSupport.have_relative_ext_ref_path(ext_ref, bompath)
                    except ValueError:
                        print_yellow("    SBOM file is not relative to source file " + ext_ref.url)

                except sw360.sw360_api.SW360Error as swex:
                    print_red("    Error getting", swex.url, swex.response)
        return sbom

    def run(self, args: Any) -> None:
        """Main method

        @params:
            args - command line arguments
        """
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)
        else:
            # suppress (debug) log output from requests and urllib
            logging.getLogger("requests").setLevel(logging.WARNING)
            logging.getLogger("urllib3").setLevel(logging.WARNING)
            logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

        print_text(
            "\n" + capycli.APP_NAME + ", " + capycli.get_app_version() +
            " - Download SW360 attachments as specified in the SBOM\n")

        if args.help:
            print("usage: capycli bom downloadattachments -i bom.json [-source <folder>]")
            print("")
            print("optional arguments:")
            print("    -h, --help            show this help message and exit")
            print("    -i INPUTFILE,         input SBOM to read from, e.g. created by \"project CreateBom\"")
            print("    -source SOURCE        source folder or additional source file")
            print("    -o OUTPUTFILE         output file to write to")
            print("    -v                    be verbose")
            return

        if not args.inputfile:
            print_red("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        print_text("Loading SBOM file " + args.inputfile)
        try:
            bom = CaPyCliBom.read_sbom(args.inputfile)
        except Exception as ex:
            print_red("Error reading input SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)

        if args.verbose:
            print_text(" " + str(len(bom.components)) + "components read from SBOM file")

        source_folder = "./"
        if args.source:
            source_folder = args.source
        if (not source_folder) or (not os.path.isdir(source_folder)):
            print_red("Target source code folder does not exist!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if args.sw360_token and args.oauth2:
            self.analyze_token(args.sw360_token)

        print_text("  Checking access to SW360...")
        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        print_text("Downloading source files to folder " + source_folder + " ...")

        self.download_attachments(bom, source_folder, os.path.dirname(args.outputfile))

        if args.outputfile:
            print_text("Updating path information")
            self.update_local_path(bom, args.outputfile)

            print_text("Writing updated SBOM to " + args.outputfile)
            try:
                SbomWriter.write_to_json(bom, args.outputfile, True)
            except Exception as ex:
                print_red("Error writing updated SBOM file: " + repr(ex))
                sys.exit(ResultCode.RESULT_ERROR_WRITING_BOM)

            if args.verbose:
                print_text(" " + str(len(bom.components)) + " components written to SBOM file")

        print("\n")
