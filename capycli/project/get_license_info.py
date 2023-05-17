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
import sys

import sw360

import capycli.common.script_base
from capycli.common.json_support import load_json_file
from capycli.common.print import print_red, print_text, print_yellow
from capycli.common.script_support import ScriptSupport
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class GetLicenseInfo(capycli.common.script_base.ScriptBase):
    """
    Get license info on all project components.
    """
    def get_cli_files_for_release(self, release: dict, folder: str, no_overwrite: bool) -> list:
        """Find all CLI file attachments for the given release, download them and return
        a list with the file information."""
        files = []
        if "_embedded" not in release:
            return files

        if "sw360:attachments" not in release["_embedded"]:
            return files

        attachment_infos = release["_embedded"]["sw360:attachments"]
        for key in attachment_infos:
            att_href = key["_links"]["self"]["href"]
            attachment = self.client.get_attachment_by_url(att_href)
            if not attachment["attachmentType"] == "COMPONENT_LICENSE_INFO_XML":
                continue

            release_id = self.client.get_id_from_href(release["_links"]["self"]["href"])
            attachment_id = self.client.get_id_from_href(att_href)

            fileinfo = {}
            filename = os.path.join(folder, attachment.get("filename", ""))
            fileinfo["filename"] = filename
            fileinfo["createdBy"] = attachment.get("createdBy", "")
            fileinfo["createdOn"] = attachment.get("createdOn", "")
            fileinfo["checkedBy"] = attachment.get("checkedBy", "")
            fileinfo["checkedTeam"] = attachment.get("checkedTeam", "")
            fileinfo["checkStatus"] = attachment.get("checkStatus", "")
            files.append(fileinfo)

            if no_overwrite and os.path.isfile(filename):
                continue

            self.client.download_release_attachment(filename, release_id, attachment_id)

        return files

    def get_project_info(
            self,
            project_id: str,
            destination: str,
            no_overwrite: bool,
            use_all_files: bool,
            config_file: str) -> dict:
        """Downloads all CLI files and generates a configuration file for
        Readme_OSS generation"""
        rdm_info = {}

        try:
            self.project = self.client.get_project(project_id)
        except sw360.sw360_api.SW360Error as swex:
            print_red("  ERROR: unable to access project: " + repr(swex))
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        rdm_info["ProjectName"] = ScriptSupport.get_full_name_from_dict(
            self.project, "name", "version")
        rdm_info["Format"] = 2  # = HTML
        rdm_info["OutputFileName"] = "Readme_OSS.html"
        complist = []

        if config_file:
            try:
                existing_config = load_json_file(config_file)
            except Exception as ex:
                print_yellow("  WARNING: unable to read existing config file: " + repr(ex))
                print_yellow("  Existing config data wilrr be ignored!")

            if existing_config:
                props = [
                    "ProjectName", "OutputFileName", "CompanyName", "CompanyAddress1",
                    "CompanyAddress2", "CompanyAddress3", "CompanyAddress4"]
                for prop in props:
                    if prop in existing_config:
                        rdm_info[prop] = existing_config[prop]

        if "sw360:releases" in self.project["_embedded"]:
            print_text("\n  Components: ")

            releases = self.project["_embedded"]["sw360:releases"]

            target_folder = destination
            if not os.path.exists(target_folder):
                os.mkdir(target_folder)

            for key in releases:
                href = key["_links"]["self"]["href"]
                release = self.client.get_release_by_url(href)

                component_name = release["name"]
                if "version" in release:
                    component_name = (
                        component_name + " " + release["version"]
                    )

                print_text("    " + component_name)

                count = 0
                warning_shown = False
                cli_files = self.get_cli_files_for_release(release, target_folder, no_overwrite)
                for cli_file in cli_files:
                    comp = {}
                    comp["ComponentName"] = component_name
                    comp["CliFile"] = cli_file["filename"]
                    comp["CreatedBy"] = cli_file["createdBy"]
                    comp["CreatedOn"] = cli_file["createdOn"]
                    comp["CheckedBy"] = cli_file["checkedBy"]
                    comp["CheckedTeam"] = cli_file["checkedTeam"]
                    comp["CheckStatus"] = cli_file["checkStatus"]

                    count += 1
                    if count > 1:
                        if not use_all_files:
                            continue

                        if not warning_shown:
                            print_yellow("        Multiple CLI files exist for the same component"
                                         + " - manual review needed!")
                            warning_shown = True

                    complist.append(comp)

            complist.sort(key=lambda s: s["ComponentName"].lower())

            rdm_info["Components"] = complist

        return rdm_info

    def show_command_help(self) -> None:
        print("\nUsage: CaPyCli project GetLicenseInfo [options]")
        print("Options:")
        print("""
  -id ID                         SW360 id of the project
  -t SW360_TOKEN                 use this token for access to SW360
  -oa,                           this is an oauth2 token
  -url SW360_URL                 use this URL for access to SW360
  -name                          name of the project, component or release
  -version                       version of the project, component or release
  -i INPUTFILE,                  existing configuration file to read from (optional)")
  -o OUTPUTFILE                  output file to write to
  -dest DESTINATION              destination folder
  -ncli, --no-overwrite-cli      do not overwrite existing CLI files
  -nconf, --no-overwrite-config  do not overwrite an existing configuration file
  -all                           add all available CLI files of a component
        """)

        print()

    @classmethod
    def write_result(cls, result: dict, filename: str, no_overwrite: bool) -> None:
        """Write the Readme_OSS configuration to a JSON file"""
        if no_overwrite and os.path.isfile(filename):
            print_text("  Existing file '" + filename + "' will not be overwritten.")
            return

        with open(filename, "w") as outfile:
            json.dump(result, outfile, indent=2)

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
            " - Get license info on all project components\n")

        if args.help:
            self.show_command_help()
            return

        if not args.destination:
            print_red("No destination folder specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not args.outputfile:
            print_red("No project file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if args.inputfile:
            if not os.path.isfile(args.inputfile):
                print_red("Input file not found!")
                sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        if (args.name and args.version):
            # find_project() is part of script_base.py
            self.project_id = self.find_project(args.name, args.version)
            if not self.project_id:
                print_yellow("  No matching project found")
                sys.exit(ResultCode.RESULT_PROJECT_NOT_FOUND)

        if args.id:
            self.project_id = args.id

        if not self.project_id:
            print_red("Neither name and version nor project id specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if args.ncli:
            print_text("\n  Existing CLI files will not get overwritten.")

        rdm_info = self.get_project_info(self.project_id, args.destination, args.ncli, args.all, args.inputfile)

        print("")

        print_text("  Writing Readme_OSS config file " + args.outputfile)
        self.write_result(rdm_info, args.outputfile, args.nconf)

        print_text("\ndone.")
