# -------------------------------------------------------------------------------
# Copyright (c) 2020-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import hashlib
import logging
import os
import pathlib
import re
import sys
from typing import Any, Optional, Tuple
from urllib.parse import urlparse

import requests
from cyclonedx.model import ExternalReference, ExternalReferenceType, HashAlgorithm, HashType, XsUri
from cyclonedx.model.bom import Bom

import capycli.common.json_support
import capycli.common.script_base
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomWriter
from capycli.common.print import print_red, print_text, print_yellow
from capycli.common.script_support import ScriptSupport
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class BomDownloadSources(capycli.common.script_base.ScriptBase):
    """
    Download source files from the URL specified in the SBOM.
    """

    def get_filename_from_cd(self, cd: str) -> str:
        """
        Get filename from content-disposition.
        """
        if not cd:
            return ""
        fname = re.findall('filename=(.+)', cd)
        if len(fname) == 0:
            return ""
        return fname[0].rstrip('"').lstrip('"')

    def download_source_file(self, url: str, source_folder: str) -> Optional[Tuple[str, str]]:
        """Download a file from a URL.

        @params:
            url           - Required : url of the file to get uploaded (string)
            source_folder - Required : folder to store the source files (string)
        """
        print_text("    URL = " + url)

        try:
            response = requests.get(url, allow_redirects=True)
            filename = self.get_filename_from_cd(response.headers.get("content-disposition", ""))
            if not filename:
                filename_ps = urlparse(url)
                if filename_ps:
                    filename = os.path.basename(filename_ps.path)

            elif not filename:
                print_red("    Unable to identify filename from url!")
                return None

            print_text("    Downloading file " + filename)
            path = os.path.join(source_folder, filename)
            if (response.status_code == requests.codes["ok"]):
                open(path, "wb").write(response.content)
                sha1 = hashlib.sha1(response.content).hexdigest()
                return (path, sha1)
            else:
                print_red(
                    "    Error downloading file, http response = " +
                    str(response.status_code))
        except Exception as ex:
            print_red("      Error downloading file: " + repr(ex))

        return None

    def download_sources(self, sbom: Bom, source_folder: str) -> None:
        """Download source files for all items of the SBOM.

        @params:
            bom           - Required : the bill of materials (BOM) (list)
            source_folder - Required : folder to store the source files (string)
        """

        for component in sbom.components:
            item_name = ScriptSupport.get_full_name_from_component(component)
            print_text("  " + item_name)

            source_url = CycloneDxSupport.get_ext_ref_source_url(component)
            if source_url:
                result = self.download_source_file(source_url._uri, source_folder)
            else:
                result = None
                print_red("    No URL specified!")

            if result is not None:
                (path, sha1) = result
                # update SBOM
                # For Siemens CycloneDX SBOM the file location needs to be relative
                # to the location of the SBOM file.
                # Here, we only stored the absolute path, the matching relative path
                # in another method.
                new = False
                ext_ref = CycloneDxSupport.get_ext_ref(
                    component, ExternalReferenceType.DISTRIBUTION, CaPyCliBom.SOURCE_FILE_COMMENT)
                if not ext_ref:
                    ext_ref = ExternalReference(
                        type=ExternalReferenceType.DISTRIBUTION,
                        comment=CaPyCliBom.SOURCE_FILE_COMMENT,
                        url=XsUri(path))
                    new = True
                else:
                    ext_ref.url = XsUri(path)
                ext_ref.hashes.add(HashType(
                    alg=HashAlgorithm.SHA_1,
                    content=sha1))
                if new:
                    component.external_references.add(ext_ref)

    def update_local_path(self, sbom: Bom, bomfile: str) -> None:
        bompath = pathlib.Path(bomfile).parent
        for component in sbom.components:
            ext_ref = CycloneDxSupport.get_ext_ref(
                component, ExternalReferenceType.DISTRIBUTION, CaPyCliBom.SOURCE_FILE_COMMENT)
            if ext_ref:
                try:
                    name = CycloneDxSupport.have_relative_ext_ref_path(ext_ref, bompath.as_posix())
                    CycloneDxSupport.update_or_set_property(
                        component,
                        CycloneDxSupport.CDX_PROP_FILENAME,
                        name)
                except ValueError:
                    if type(ext_ref.url) is XsUri:
                        print_yellow("  SBOM file is not relative to source file " + ext_ref.url._uri)
                    else:
                        print_yellow("  SBOM file is not relative to source file " + str(ext_ref.url))

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
            " - Download source files from the URL specified in the SBOM\n")

        if args.help:
            print("usage: capycli bom downloadsources -i bom.json [-source <folder>]")
            print("")
            print("optional arguments:")
            print("    -h, --help            show this help message and exit")
            print("    -i INPUTFILE,         input SBOM file to read from (JSON)")
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
            print_text(" " + str(len(bom.components)) + "components written to SBOM file")

        source_folder = "./"
        if args.source:
            source_folder = args.source
        if (not source_folder) or (not os.path.isdir(source_folder)):
            print_red("Target source code folder does not exist!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        print_text("Downloading source files to folder " + source_folder + " ...")

        self.download_sources(bom, source_folder)

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
