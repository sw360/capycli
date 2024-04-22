# -------------------------------------------------------------------------------
# Copyright (c) 2019-24 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import os
import shutil
import sys
import traceback
from typing import Any, Dict, List

from cli_support import CliFile
from colorama import Fore, Style

import capycli.common.script_base
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class ShowLicenses(capycli.common.script_base.ScriptBase):
    TEMPFOLDER = ".\\_cli_temp_"

    """Show licenses of all cleared compponents."""
    def __init__(self) -> None:
        self.nodelete: bool = False
        self.global_license_list: List[str] = []

    @classmethod
    def ensure_dir(cls, folder_path: str) -> None:
        """Ensures that the given path exists"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if not os.path.exists(folder_path):
            print_red("  Unable to create temp folder!")

    @classmethod
    def print_license_list(cls, license_list: List[str]) -> None:
        """Displays the licenses color-coded"""
        for lic in license_list:
            color = Fore.RESET
            check = lic.upper()
            if "GPL" in check:
                color = Fore.LIGHTYELLOW_EX

            if "EPL" in check:
                color = Fore.LIGHTYELLOW_EX

            if "MPL" in check:
                color = Fore.LIGHTYELLOW_EX

            if "CDDL" in check:
                color = Fore.LIGHTYELLOW_EX

            if "CPL" in check:
                color = Fore.LIGHTYELLOW_EX

            print(color + lic + " ", end="", flush=True)

        print(Style.RESET_ALL)

    def process_release(self, release: Dict[str, Any], tempfolder: str) -> None:
        """Processes a single release"""
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        if "_embedded" not in release:
            print_red("    No license information available!")
            return

        if "sw360:attachments" not in release["_embedded"]:
            print_red("    No license information available!")
            return

        cli_filename = ""
        attachment_infos = release["_embedded"]["sw360:attachments"]
        for key in attachment_infos:
            att_href = key["_links"]["self"]["href"]
            attachment = self.client.get_attachment_by_url(att_href)
            if not attachment:
                continue
            if attachment.get("attachmentType", "") != "COMPONENT_LICENSE_INFO_XML":
                continue

            filename = key["filename"]
            filename = os.path.join(tempfolder, filename)
            release_id = self.client.get_id_from_href(release["_links"]["self"]["href"])
            attachment_id = self.client.get_id_from_href(att_href)
            self.client.download_release_attachment(filename, release_id, attachment_id)
            if os.path.isfile(filename):
                cli_filename = filename
                break
            else:
                print_red("    Error downloading CLI file!")

        if not cli_filename:
            print_yellow("    No CLI file found!")
            return

        clifile = CliFile()

        try:
            clifile.read_from_file(cli_filename)
        except OSError as ex:
            print_red("    Error reading CLI file: " + cli_filename)
            print_red("    Error '{0}' occured. Arguments {1}.".format(ex.errno, ex.args))

        license_list = []
        for lic in clifile.licenses:
            license_list.append(lic.name + " (" + lic.spdx_identifier + ")")
            if lic.name not in self.global_license_list:
                self.global_license_list.append(lic.name)

        self.print_license_list(license_list)

    def show_licenses(self, id: str) -> None:
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        tempfolder = self.TEMPFOLDER
        self.ensure_dir(tempfolder)

        try:
            project = self.client.get_project(id)
        except Exception as ex:
            print_red(
                "Error searching for project: \n" +
                repr(ex) + "\n" +
                str(traceback.format_exc()))
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        if not project:
            print_red("Unable to read project!")
            return

        print_text("  Project name: " + project["name"] + ", " + project["version"])
        print_text("  Project owner: " + project.get("projectOwner", "???"))
        print_text("  Clearing state: " + project.get("clearingState", "???"))
        if self.nodelete:
            print_text("  Temp folder", tempfolder, "will not get deleted.")

        self.global_license_list = []
        if "sw360:releases" in project["_embedded"]:
            print_text("\nComponents: ")
            releases = project["_embedded"]["sw360:releases"]
            print_text("  Scanning", len(releases), "releases.")
            for key in sorted(releases, key=lambda item: item["name"]):
                href = key["_links"]["self"]["href"]
                print_text("\n  " + key["name"] + ", " + key["version"])
                release = self.client.get_release_by_url(href)
                if not release:
                    print_red("Error processing release")
                else:
                    try:
                        self.process_release(release, tempfolder)
                    except Exception as ex:
                        print_red("Error processing release: \n" + repr(ex))

            print_text("\nLicense summary:")
            self.print_license_list(self.global_license_list)
        else:
            print_text("\n  No linked releases")

        if not self.nodelete:
            shutil.rmtree(tempfolder)

    def show_command_help(self) -> None:
        print("\nusage: CaPyCli project licenses [options]")
        print("Options:")
        print("""
  -id ID           SW360 id of the project
  -t SW360_TOKEN   use this token for access to SW360
  -oa,             this is an oauth2 token
  -url SW360_URL   use this URL for access to SW360
  -name            name of the project, component or release
  -version         version of the project, component or release
        """)

        print()

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
            "\n" + capycli.APP_NAME + ", " + capycli.get_app_version() +
            " - Show licenses of all cleared components.")

        if args.help:
            self.show_command_help()
            return

        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        name: str = args.name
        version: str = ""
        if args.version:
            version = args.version

        if args.id:
            self.show_licenses(args.id)
        elif (args.name and args.version):
            # find_project() is part of script_base.py
            pid = self.find_project(name, version)
            if pid:
                self.show_licenses(pid)
            else:
                print_yellow("  No matching project found")
        else:
            print_red("Neither name and version nor project id specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)
