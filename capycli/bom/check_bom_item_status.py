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
from sw360 import SW360Error

import capycli.common.script_base
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.common.print import print_red, print_text
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class CheckBomItemStatus(capycli.common.script_base.ScriptBase):
    """Print SBOM item status to stdout"""

    def _bom_has_items_without_id(self, bom: Bom) -> bool:
        """Determines whether there is at least one SBOM item
        without Sw360Id."""
        for item in bom.components:
            sw360id = CycloneDxSupport.get_property_value(item, CycloneDxSupport.CDX_PROP_SW360ID)
            if not sw360id:
                return True

        return False

    def _find_by_id(self, component: Component) -> Optional[Dict[str, Any]]:
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        sw360id = CycloneDxSupport.get_property_value(component, CycloneDxSupport.CDX_PROP_SW360ID)
        version = component.version or ""
        try:
            release_details = self.client.get_release(sw360id)
            return release_details
        except SW360Error as swex:
            if swex.response is None:
                print_red("  Unknown error: " + swex.message)
            elif swex.response.status_code == requests.codes['not_found']:
                print(
                    Fore.LIGHTYELLOW_EX + "  Not found " + component.name +
                    ", " + version + ", " + sw360id + Style.RESET_ALL)
            else:
                print(Fore.LIGHTRED_EX + "  Error retrieving release data: ")
                print(
                    "  " + component.name + ", " + version +
                    ", " + sw360id)
                print("  Status Code: " + str(swex.response.status_code))
                if swex.message:
                    print("    Message: " + swex.message)
                print(Style.RESET_ALL)

        return None

    def _find_by_name(self, component: Component) -> Optional[Dict[str, Any]]:
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        version = component.version or ""
        try:
            releases = self.client.get_releases_by_name(component.name)
            if not releases:
                return None

            for r in releases:
                if r.get("version", "") == version:
                    return self.client.get_release_by_url(r["_links"]["self"]["href"])

            return None
        except SW360Error as swex:
            if swex.response is None:
                print_red("  Unknown error: " + swex.message)
            elif swex.response.status_code == requests.codes['not_found']:
                print(
                    Fore.LIGHTYELLOW_EX + "  Not found " + component.name +
                    ", " + version + ", " +
                    Style.RESET_ALL)
            else:
                print(Fore.LIGHTRED_EX + "  Error retrieving release data: ")
                print("  " + str(component.name) + ", " + str(version))
                print("  Status Code: " + str(swex.response.status_code))
                if swex.message:
                    print("    Message: " + swex.message)
                print(Style.RESET_ALL)

            return None

    def show_bom_item_status(self, bom: Bom, all: bool = False) -> None:
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        for component in bom.components:
            release = None
            id = CycloneDxSupport.get_property_value(component, CycloneDxSupport.CDX_PROP_SW360ID)
            if id:
                release = self._find_by_id(component)
            else:
                release = self._find_by_name(component)

            if release:
                if not all:
                    cs = release.get("clearingState", "(unknown clearing state)")
                    color = Fore.WHITE
                    if cs == "APPROVED":
                        color = Fore.LIGHTGREEN_EX

                    print(
                        color +
                        "  " + component.name + ", " + component.version +
                        " => " + cs + ", " +
                        release.get("mainlineState", "(unknown mainline state)") +
                        Style.RESET_ALL)
                    continue

                comp_sw360 = self.client.get_component(
                    self.client.get_id_from_href(
                        release["_links"]["sw360:component"]["href"]
                    )
                )
                if not comp_sw360:
                    print_red("Error accessing component")
                    continue

                rel_list = comp_sw360["_embedded"]["sw360:releases"]
                print("  " + component.name + ", " + component.version + " => ", end="", flush=True)
                print("releases for component found = " + str(len(rel_list)))
                for orel in rel_list:
                    href = orel["_links"]["self"]["href"]
                    rel = self.client.get_release_by_url(href)
                    if not rel:
                        print_red("Error accessing release " + href)
                        continue
                    cs = rel.get("clearingState", "(unkown clearing state)")
                    if cs == "APPROVED":
                        print(Fore.LIGHTGREEN_EX, end="", flush=True)
                    print(
                        "    " + orel["version"] + ", " + cs + ", " +
                        rel.get("mainlineState", "(unknown mainline state)"))
                    print(Style.RESET_ALL, end="", flush=True)

                print("")
                continue

            if not id:
                print_red(
                    "  " + component.name + ", " + component.version +
                    " => --- no id ---")
                continue

    def run(self, args: Any) -> None:
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
            "\n" + capycli.APP_NAME + ", " + capycli.get_app_version()
            + " - check the status of the items on SW360\n")

        if args.help:
            print("usage: capycli bom CheckItemStatus [-h] [-all] -i bomfile")
            print("")
            print("optional arguments:")
            print("-h, --help            show this help message and exit")
            print("-i INPUTFILE          input file to read from")
            print("-all                  show status of all versions of the component")
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
            print_red("Error reading SBOM: " + repr(ex))
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

        self.show_bom_item_status(bom, args.all)

        print()
