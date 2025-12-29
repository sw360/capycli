# -------------------------------------------------------------------------------
# Copyright (c) 2025 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import os
import pathlib
import posixpath
import shutil
import sys
import tempfile
from typing import Any

from cyclonedx.model import ExternalReference, ExternalReferenceType, HashAlgorithm, HashType, XsUri
from cyclonedx.model.bom import Bom

import capycli.common.script_base
from capycli.bom.download_sources import BomDownloadSources
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomWriter
from capycli.common.print import print_red, print_text, print_yellow
from capycli.common.script_support import ScriptSupport
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class BomPackage(capycli.common.script_base.ScriptBase):
    """
    Create a single zip archive that contains the SBOM and all source and binary files.
    The archive shoukd have the following structure:

    sbom.cdx.json
    +--- binaries
    |    +--- 77100a62c2e6f04b53977b9f541044d7d722693d
    |    |    `--- some-binary.jar
    |    +--- 8031352b2bb0a49e67818bf04c027aa92e645d5c
    |    |    `--- another-binary.jar
    |    `--- (... more ...)
    `--- sources
        +--- 6bb10559db88828dac3627de26974035a5dd4ddb
        |    `--- some-sources.jar
        +--- 4d44e4edc4a7fb39f09b95b09f560a15976fa1ba
        |    `--- another-sources.jar
        `--- (... more ...)
    """
    def download_files(self, sbom: Bom, target_folder: str) -> None:
        """Download source and binary files for all items of the SBOM.

        @params:
            bom           - Required : the bill of materials (BOM) (list)
            target_folder - Required : folder to store the source files (string)
        """

        for component in sbom.components:
            item_name = ScriptSupport.get_full_name_from_component(component)
            print_text("  " + item_name)

            # download source file
            source_url = CycloneDxSupport.get_ext_ref_source_url(component)
            if source_url:
                result = BomDownloadSources.download_source_file(source_url._uri, target_folder)
            else:
                result = None
                print_red("    No source URL specified!")

            if result is not None:
                (path, sha1) = result
                # move file to appropriate location
                filename = pathlib.Path(path).name
                targetsha = os.path.join(target_folder, "sources", sha1)
                os.makedirs(targetsha, exist_ok=True)
                target = os.path.join(targetsha, filename)
                shutil.move(path, target)

                # update SBOM
                new = False
                ext_ref = CycloneDxSupport.get_ext_ref(
                    component, ExternalReferenceType.DISTRIBUTION, CaPyCliBom.SOURCE_FILE_COMMENT)
                file_uri = posixpath.join("sources", sha1, filename)
                if not file_uri.startswith("file://"):
                    file_uri = "file:///" + file_uri
                if not ext_ref:
                    ext_ref = ExternalReference(
                        type=ExternalReferenceType.DISTRIBUTION,
                        comment=CaPyCliBom.SOURCE_FILE_COMMENT,
                        url=XsUri(file_uri))
                    new = True
                else:
                    ext_ref.url = XsUri(file_uri)
                ext_ref.hashes.add(HashType(
                    alg=HashAlgorithm.SHA_1,
                    content=sha1))
                if new:
                    component.external_references.add(ext_ref)

            # download binary file
            binary_url = CycloneDxSupport.get_ext_ref_binary_url(component)
            if binary_url:
                result = BomDownloadSources.download_source_file(binary_url._uri, target_folder, is_binary=True)
            else:
                result = None
                print_yellow("    No binary URL specified!")

            if result is not None:
                (path, sha1) = result
                # move file to appropriate location
                filename = pathlib.Path(path).name
                targetsha = os.path.join(target_folder, "binaries", sha1)
                os.makedirs(targetsha, exist_ok=True)
                target = os.path.join(targetsha, filename)
                shutil.move(path, target)

                # update SBOM
                new = False
                ext_ref = CycloneDxSupport.get_ext_ref(
                    component, ExternalReferenceType.DISTRIBUTION, CaPyCliBom.BINARY_FILE_COMMENT)
                file_uri = posixpath.join("binaries", sha1, filename)
                if not file_uri.startswith("file://"):
                    file_uri = "file:///" + file_uri
                if not ext_ref:
                    ext_ref = ExternalReference(
                        type=ExternalReferenceType.DISTRIBUTION,
                        comment=CaPyCliBom.BINARY_FILE_COMMENT,
                        url=XsUri(file_uri))
                    new = True
                else:
                    ext_ref.url = XsUri(file_uri)
                ext_ref.hashes.add(HashType(
                    alg=HashAlgorithm.SHA_1,
                    content=sha1))
                if new:
                    component.external_references.add(ext_ref)

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
            "\n" + capycli.get_app_signature() +
            " - create a single zip archive that contains the SBOM and all source and binary files\n")

        if args.help:
            print("usage: capycli bom bompackage -i bom.json")
            print("")
            print("optional arguments:")
            print("    -h, --help            show this help message and exit")
            print("    -i INPUTFILE,         input SBOM file to read from (JSON)")
            print("    -o OUTPUT ARCHIVE,    path of the output zip archive")
            print("    -v                    be verbose")
            return

        if not args.inputfile:
            print_red("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if not args.outputfile:
            print_red("No output file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        print_text("Loading SBOM file " + args.inputfile)
        try:
            bom = CaPyCliBom.read_sbom(args.inputfile)
        except Exception as ex:
            print_red("Error reading input SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)

        if args.verbose:
            print_text(" " + str(len(bom.components)) + "components read from SBOM file")

        temp_dir = tempfile.TemporaryDirectory(prefix="capycli_bom_pkg_")
        target_folder = temp_dir.name

        pp = pathlib.Path(args.outputfile)
        if pp.suffix.lower() != ".zip":
            print_yellow("Warning: bom package file should have .zip extension")
            args.bom_package = args.outputfile + ".zip"

        print_text("\nDownloading files to folder " + target_folder + " ...")

        self.download_files(bom, target_folder)

        print_text("\nCreating BOM package " + args.outputfile)
        try:
            # add SBOM to temp folder
            sbom_file = os.path.join(target_folder, "sbom.cdx.json")
            SbomWriter.write_to_json(bom, sbom_file, True)
            shutil.make_archive(
                base_name=args.outputfile.rstrip(".zip"),
                format="zip",
                root_dir=target_folder)
            temp_dir.cleanup()
        except Exception as ex:
            print_red("Error creating BOM package: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_WRITING_BOM)

        print("\n")
