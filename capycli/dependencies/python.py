# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import json
import logging
import os
import subprocess
import sys
from io import TextIOWrapper
from typing import Any, Dict, List

import chardet
import requests
import requirements
from cyclonedx.model import ExternalReference, ExternalReferenceType, License, LicenseChoice, Property
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from packageurl import PackageURL

import capycli.common.json_support
import capycli.common.script_base
from capycli import get_logger
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomCreator, SbomWriter
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class GetPythonDependencies(capycli.common.script_base.ScriptBase):
    """
    Determine Python components/dependencies for a given project
    """

    def __init__(self):
        self.verbose = False

    # NOT USED AT THE MOMENT
    def create_local_package_list(self) -> dict:
        """
        Create a list of all packages in the local environment.

        :return a list of the local Python packages
        :rtype list of package item dictionaries, as returned by pip
        """
        args = ["pip3", "list", "--format", "json"]
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False)
        raw_data = proc.communicate()[0]
        package_list = json.loads(raw_data)
        return package_list

    def requirements_to_package_list(self, input_file: str) -> List[Dict[str, str]]:
        """
        Converts the requirements file to a package list.

        :param input_file: the requirements file.
        :type input_file: string
        :return a list of the local Python packages
        :rtype list of package item dictionaries, as retuned by pip
        """
        rawdata = open(input_file, 'rb').read()
        result = chardet.detect(rawdata)
        with open(input_file, 'r', encoding=result['encoding']) as fin:
            package_list = self.read_requirements_bom(fin)
            return package_list

    def read_requirements_bom(self, requirements_file: TextIOWrapper) -> List[Dict[str, str]]:
        """
        Read SBOM data from file handle.

        :param requirements_file: the requirements file.
        :type requirements_file: string.
        :return a list of the local Python packages.
        :rtype list of package item dictionaries, as retuned by pip.
        """
        package_list = []
        for req in requirements.parse(requirements_file):
            name = req.name
            if req.local_file:
                print_yellow(
                    "WARNING: Local file " + req.path +
                    " does not have versions. Skipping.")
                continue

            if not req.specs:
                print_yellow(
                    "WARNING: " + name +
                    " does not have a version specified. Skipping.")
                continue

            if len(req.specs[0]) >= 2:
                version = req.specs[0][1]
                if req.specs[0][0] != "==":
                    print_yellow(
                        "WARNING: " + name +
                        " is not pinned to a specific version. Using: " + version)

                package = {}
                package["name"] = name
                package["version"] = version
                package_list.append(package)

        return package_list

    def get_package_meta_info(self, name: str, version: str, package_source: str = "") -> dict or None:
        """
        Retrieves meta data of the given package from PyPi.

        :param name: the name of the component.
        :param version: the version of the component.
        :type name: string.
        :type version: string.
        :return: the PyPi meta data.
        :rtype: JSON dictionary or None.
        """
        if package_source:
            ship_api_url = package_source + name + "/" + version + "/json"
        else:
            ship_api_url = "https://pypi.org/pypi/" + name + "/" + version + "/json"

        if self.verbose:
            LOG.debug("  Retrieving meta data for " + name + ", " + version)

        try:
            response = requests.get(ship_api_url)
            if not response.ok:
                print_yellow(
                    "  WARNING: no meta data available for package " +
                    name + ", " + version)
                return None

            json = response.json()
            return json
        except Exception as ex:
            print_red(
                "  ERROR: unable to retrieve meta data for package " +
                name + ", " + version + ": " + str(ex))

        return None

    def generate_purl(self, name: str, version: str) -> str:
        """
        Generate the package URL for the PyPi component identified by
        the given name and version.
        For details see https://github.com/package-url/purl-spec

        :param name: the name of the component.
        :param version: the version of the component.
        :type name: string.
        :type version: string.
        :return a package URL
        :rtype string
        """
        return PackageURL("pypi", '', name, version, '', '').to_string()

    def add_meta_data_to_bomitem(self, cxcomp: Component, package_source: str = ""):
        """
        Try to lookup meta data for the given item.

        :param bomitem: a single bill of material item (a single component)
        :type bomitem: dictionary
        """
        meta = self.get_package_meta_info(cxcomp.name, cxcomp.version, package_source)
        if not meta:
            LOG.debug(f"No meta data found for {cxcomp.name}, {cxcomp.version}")
            return

        if "info" in meta:
            homepage = meta["info"].get("home_page", "")
            if homepage:
                ext_ref = ExternalReference(
                    reference_type=ExternalReferenceType.WEBSITE,
                    url=homepage)
                LOG.debug("  got website/homepage")
                cxcomp.external_references.add(ext_ref)

            data = meta["info"].get("license", "")
            if data:
                license = License(license_name=data)
                license_choice = LicenseChoice(license_=license)
                cxcomp.licenses.add(license_choice)
                LOG.debug("  got license")

            data = meta["info"].get("summary", "")
            if data:
                cxcomp.description = data
                LOG.debug("  got description")

            data = meta["info"].get("package_url", "")
            if data:
                ext_ref = ExternalReference(
                    reference_type=ExternalReferenceType.DISTRIBUTION,
                    comment="PyPi URL",
                    url=data)
                cxcomp.external_references.add(ext_ref)
                LOG.debug("  got package url")

            if "urls" in meta:
                # there can be multiple etries, for wheel, source, etc.
                for item in meta["urls"]:
                    if "packagetype" in item:
                        if item["packagetype"] == "bdist_wheel":
                            ext_ref = ExternalReference(
                                reference_type=ExternalReferenceType.DISTRIBUTION,
                                comment=CaPyCliBom.BINARY_FILE_COMMENT,
                                url=item["filename"])
                            cxcomp.external_references.add(ext_ref)
                            LOG.debug("  got binary file")

                            ext_ref = ExternalReference(
                                reference_type=ExternalReferenceType.DISTRIBUTION,
                                comment=CaPyCliBom.BINARY_URL_COMMENT,
                                url=item["url"])
                            cxcomp.external_references.add(ext_ref)
                            LOG.debug("  got binary file url")

                        if item["packagetype"] == "sdist":
                            ext_ref = ExternalReference(
                                reference_type=ExternalReferenceType.DISTRIBUTION,
                                comment=CaPyCliBom.SOURCE_FILE_COMMENT,
                                url=item["filename"])
                            cxcomp.external_references.add(ext_ref)
                            LOG.debug("  got source file")

                            ext_ref = ExternalReference(
                                reference_type=ExternalReferenceType.DISTRIBUTION,
                                comment=CaPyCliBom.SOURCE_URL_COMMENT,
                                url=item["url"])
                            cxcomp.external_references.add(ext_ref)
                            LOG.debug("  got source file url")

    def convert_package_list(self, package_list: list, search_meta_data: bool, package_source: str = "") -> Bom:
        """
        Convert package list to SBOM.

        :param package_list: list of packages to convert
        :type package_list: list of package item dictionaries, as retuned by pip.
        :return the bill or material
        :rtype list of bom item dictionaries
        """
        creator = SbomCreator()
        sbom = creator.create(None, addlicense=True, addprofile=True, addtools=True)
        for package in package_list:
            purl = self.generate_purl(package["name"], package["version"])
            cxcomp = Component(
                name=package.get("name", "").strip(),
                version=package.get("version", "").strip(),
                purl=purl,
                bom_ref=purl,
                description=package.get("Description", "").strip())

            prop = Property(
                name=CycloneDxSupport.CDX_PROP_LANGUAGE,
                value="Python")
            cxcomp.properties.add(prop)

            if search_meta_data:
                self.add_meta_data_to_bomitem(cxcomp, package_source)

            sbom.components.add(cxcomp)

        return sbom

    def print_package_list(self, package_list: list) -> None:
        """
        Print the package list.

        :param package_list: list of packages to convert
        :type package_list: list of package item dictionaries, as retuned by pip.
        """

        print_text("\nPackages:")
        for package in package_list:
            print_text("  " + package["name"] + ", " + package["version"])

        print()

    def check_meta_data(self, sbom: Bom) -> bool:
        """
        Check whether all required meta-data is available.

        Args:
            sbom (Bom): the SBOM

        Returns:
            bool: True if all required meta-data is available; otherwise False.
        """

        if self.verbose:
            print_text("\nChecking meta-data:")

        result = True
        for cxcomp in sbom.components:
            if self.verbose:
                print_text(f"  {cxcomp.name}, {cxcomp.version}")

            if not cxcomp.purl:
                result = False
                if self.verbose:
                    print_yellow("    package-url missing")

            homepage = CycloneDxSupport.get_ext_ref_website(cxcomp)
            if not homepage:
                result = False
                if self.verbose:
                    print_yellow("    Homepage missing")

            src_url = CycloneDxSupport.get_ext_ref_source_url(cxcomp)
            if not src_url:
                result = False
                if self.verbose:
                    print_yellow("    Source code URL missing")

        return result

    def run(self, args):
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)
        else:
            # suppress (debug) log output from requests and urllib
            logging.getLogger("requests").setLevel(logging.WARNING)
            logging.getLogger("urllib3").setLevel(logging.WARNING)
            logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

        print_text(
            "        \n" + capycli.APP_NAME + ", " + capycli.get_app_version() +
            " - Determine Python components/dependencies\n")

        if args.help:
            print("usage: capycli getdependencies python [-i INPUTFILE] [-o OUTFILE] [-ol] [-v] [-ds]")
            print("")
            print("Determine Python project dependencies")
            print("")
            print("optional arguments:")
            print("    -h, --help            show this help message and exit")
            print("    -i INPUTFILE, --inputfile INPUTFILE")
            print("                            input file (requirements.txt)")
            print("    -o OUTFILE, --outfile OUTFILE")
            print("                            output file (BOM)")
            print("    -v, --verbose         verbose output")
            print("    --search-meta-data    search for package meta data")
            return

        if not args.inputfile:
            print_red("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if not args.outputfile:
            print_red("No output SBOM file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        self.verbose = args.verbose

        print_text("Reading input file " + args.inputfile)
        package_list = self.requirements_to_package_list(args.inputfile)

        if self.verbose:
            self.print_package_list(package_list)

        print_text("Formatting package list...")
        sbom = self.convert_package_list(package_list, args.search_meta_data, args.package_source)
        self.check_meta_data(sbom)

        if self.verbose:
            print()

        print_text("Writing new SBOM to " + args.outputfile)
        SbomWriter.write_to_json(sbom, args.outputfile, True)
        print_text(" " + self.get_comp_count_text(sbom) + " items written to file.")

        print()
