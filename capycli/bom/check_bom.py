# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import os
import sys
from typing import Any, Dict, Optional

import requests
import sw360.sw360_api
from colorama import Fore, Style
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component

import capycli.common.script_base
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.common.print import print_green, print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class CheckBom(capycli.common.script_base.ScriptBase):
    """
    Check that all releases listed in the SBOM really exist
    """

    def _bom_has_items_without_id(self, bom: Bom) -> bool:
        """Determines whether there is at least one SBOM item
        without Sw360Id."""
        for item in bom.components:
            sw360id = CycloneDxSupport.get_property_value(item, CycloneDxSupport.CDX_PROP_SW360ID)
            if not sw360id:
                return True

        return False

    def _find_by_id(self, component: Component) -> Optional[Dict[str, Any]]:
        sw360id = CycloneDxSupport.get_property_value(component, CycloneDxSupport.CDX_PROP_SW360ID)
        version = component.version or ""
        for step in range(3):
            try:
                release_details = self.client.get_release(sw360id)
                return release_details
            except sw360.sw360_api.SW360Error as swex:
                if swex.response is None:
                    print_red("  Unknown error: " + swex.message)
                elif swex.response.status_code == requests.codes['not_found']:
                    print_yellow(
                        "  Not found " + component.name +
                        ", " + version + ", " + sw360id)
                    break

                # only report other errors if this is the third attempt
                if step >= 2:
                    print(Fore.LIGHTRED_EX + "  Error retrieving release data: ")
                    print(
                        "  " + component.name + ", " + version +
                        ", " + sw360id)
                    if swex.response:
                        print("  Status Code: " + str(swex.response.status_code))
                    if swex.message:
                        print("    Message: " + swex.message)
                    print(Style.RESET_ALL)

        return None

    def _find_by_name(self, component: Component) -> Optional[Dict[str, Any]]:
        version = component.version or ""
        for step in range(3):
            try:
                releases = self.client.get_releases_by_name(component.name)
                if not releases:
                    return None

                for r in releases:
                    if r.get("version", "") == version:
                        return r

                return None
            except sw360.sw360_api.SW360Error as swex:
                if swex.response is None:
                    print_red("  Unknown error: " + swex.message)
                elif swex.response.status_code == requests.codes['not_found']:
                    print_yellow(
                        "  Not found " + component.name +
                        ", " + version)
                    break

                # only report other errors if this is the third attempt
                if step >= 2:
                    print(Fore.LIGHTRED_EX + "  Error retrieving release data: ")
                    print(
                        "  " + component.name + ", " + version)
                    if swex.response:
                        print("  Status Code: " + str(swex.response.status_code))
                    if swex.message:
                        print("    Message: " + swex.message)
                    print(Style.RESET_ALL)

        return None

    def check_releases(self, bom: Bom) -> int:
        """Checks for each release in the list whether it can be found on the specified
        SW360 instance."""
        found_count = 0
        for component in bom.components:
            release_details = None
            sw360id = CycloneDxSupport.get_property_value(component, CycloneDxSupport.CDX_PROP_SW360ID)
            if sw360id:
                release_details = self._find_by_id(component)
            else:
                release_details = self._find_by_name(component)

            if release_details:
                sid = self.client.get_id_from_href(release_details["_links"]["self"]["href"])
                print_green(
                    "  Found " + release_details["name"] +
                    ", " + release_details["version"] + ", " + sid)
                found_count += 1
                continue

            if not sw360id:
                print_yellow(
                    "  " + component.name +
                    ", " + component.version +
                    " - No id available - skipping!")
                continue

        return found_count

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
            "\n" + capycli.APP_NAME + ", " + capycli.get_app_version() +
            " - Check that all releases in the SBOM exist on target SW360 instance.\n")

        if args.help:
            print("usage: CaPyCli bom check [-h] [-t SW360_TOKEN] [-oa] [-url SW360_URL] [-v] -i bomfile")
            print("")
            print("optional arguments:")
            print("    -h, --help            show this help message and exit")
            print("    -t SW360_TOKEN,       SW360_TOKEN")
            print("                          use this token for access to SW360")
            print("    -oa, --oauth2         this is an oauth2 token")
            print("    -url SW360_URL        use this URL for access to SW360")
            print("    -i INPUTFILE          SBOM file to read from")
            print("    -v                    be verbose")
            return

        if not args.inputfile:
            print_red("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        print("Loading SBOM file", args.inputfile)
        try:
            bom = CaPyCliBom.read_sbom(args.inputfile)
        except Exception as ex:
            print_red("Error loading SBOM: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)

        if args.verbose:
            print_text(" ", self.get_comp_count_text(bom), " read from SBOM")

        if self._bom_has_items_without_id(bom):
            print("There are SBOM items without Sw360 id - searching per name may take a little bit longer...")

        if args.sw360_token and args.oauth2:
            self.analyze_token(args.sw360_token)

        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        found = self.check_releases(bom)

        print()
        print(len(bom.components), "components checked,", found, "successfully found.")
