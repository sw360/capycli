# -------------------------------------------------------------------------------
# Copyright (c) 2026 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import sys
from typing import Any

import capycli.common.script_base
import sw360
from capycli.bom.component_check import ComponentCheck
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class ProjectComponentCheck(capycli.common.script_base.ScriptBase):
    """
    Check a project for special components.
    """
    def __init__(self) -> None:
        self.component_check = ComponentCheck()
        self.verbose = False

    def is_dev_dependency(self, name: str) -> bool:
        """Check whether the given component matches any known development dependency."""
        dd = self.component_check.component_check_list.get("dev_dependencies", [])
        for ecosystem in dd:
            for entry in dd.get(ecosystem, []):
                to_compare = entry.get("name", "")
                if entry.get("namespace", ""):
                    to_compare = entry.get("namespace", "") + "/" + to_compare
                if name.lower() == to_compare.lower():
                    return True

        return False

    def is_python_binary_component(self, name: str) -> bool:
        """Check whether the given component matches any known python component
        with additional binary dependencies."""
        pbc = self.component_check.component_check_list.get("python_binary_components", [])
        for entry in pbc:
            if name.lower() == entry.get("name", ""):
                return True

        return False

    def is_file_to_ignore(self, name: str) -> bool:
        """Check whether the given component is to be ignored."""
        for entry in self.component_check.files_to_ignore:
            if name.lower() == entry.get("name", ""):
                return True

        return False

    def check_bom_items(self, project_id: str) -> int:
        """Check the given project for special components."""
        print_text("\nRetrieving project details...")

        special_component_count = 0

        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        try:
            self.project = self.client.get_project(project_id)
        except sw360.SW360Error as swex:
            print_red("  ERROR: unable to access project: " + repr(swex))
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        if not self.project:
            print_red("  ERROR: unable to read project data!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        if "sw360:releases" in self.project["_embedded"]:
            releases = self.project["_embedded"]["sw360:releases"]
            releases.sort(key=lambda s: s["name"].lower())
            for release in releases:
                name = release.get("name", "")
                version = release.get("version", "")
                # print(name, version)
                if self.is_file_to_ignore(name):
                    continue

                if self.is_dev_dependency(name):
                    special_component_count += 1
                    print_yellow("  ", name, version, "seems to be a development dependency")

                if self.is_python_binary_component(name):
                    special_component_count += 1
                    print_yellow("  ", name, version,
                                 "is known as a Python component that has additional binary dependencies")

        return special_component_count

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
            "\n" + capycli.get_app_signature() +
            " - Check the project for special components\n")

        if args.help:
            print_text("usage: CaPyCli project componentcheck [-h] -t TOKEN -name NAME -version VERSION "
                       "[-v] [-id PROJECT_ID] [-rcl URL] [-lcl FILE]")
            print_text("")
            print_text("optional arguments:")
            print_text("    -h, --help            show this help message and exit")
            print_text("    -name NAME            name of the project")
            print_text("    -version VERSION      version of the project")
            print_text("    -id PROJECT_ID        SW360 id of the project, supersedes name and version parameters")
            print_text("    -t SW360_TOKEN        use this token for access to SW360")
            print_text("    -oa,                  this is an oauth2 token")
            print_text("    -url SW360_URL        use this URL for access to SW360")
            print_text("    -v                    be verbose")
            print_text("    -rcl                  read the component check list file from the URL specified")
            print_text("    -lcl                  read the component check list file from local")
            print_text("    --forceerror          force an error exit code in case of validation errors or warnings")
            return

        self.verbose = args.verbose
        self.component_check.verbose = args.verbose

        print_text("Reading component checklist...")
        try:
            self.component_check.read_component_check_list(args.remote_check_list, args.local_checklist_list)
        except Exception as ex:
            print_red("Error reading component checklist " + repr(ex))
            sys.exit(ResultCode.RESULT_GENERAL_ERROR)
        if len(self.component_check.component_check_list) > 0:
            print_text("  Got component checklist.")

        self.component_check.files_to_ignore = self.component_check.component_check_list.get("files_to_ignore", [])
        print_text(f"  {len(self.component_check.files_to_ignore)} components will be ignored.")

        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        name: str = args.name
        version: str = ""
        pid: str = ""
        if args.version:
            version = args.version

        if args.id:
            pid = args.id
        elif (args.name and args.version):
            # find_project() is part of script_base.py
            pid = self.find_project(name, version)
        else:
            print_red("Neither name and version nor project id specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        result = 0
        if pid:
            result = self.check_bom_items(pid)

            print_text("\nDone.")
        else:
            print_yellow("  No matching project found")

        if result > 0:
            if args.force_error:
                if args.verbose:
                    print_yellow("Special component(s) found, exiting with code != 0")
                sys.exit(ResultCode.RESULT_SPECIAL_COMPONENT_FOUND)
