# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import sys
from typing import Any, Dict, Optional

from colorama import Fore

import capycli.common.json_support
import capycli.common.script_base
import sw360
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class ShowProject(capycli.common.script_base.ScriptBase):
    """Show project details."""
    def get_clearing_state(self, proj: Optional[Dict[str, Any]], href: str) -> str:
        """Returns the clearing state of the given component/release"""
        if not proj:
            return ""

        rel = proj["linkedReleases"]
        for key in rel:
            if key["release"] == href:
                return key["mainlineState"]

        return ""

    def show_project_status(self, result: Dict[str, Any]) -> None:
        if not result:
            return

        print_text("  Project name: " + result["Name"] + ", " + result["Version"])
        if "ProjectResponsible" in result:
            print_text("  Project responsible: " + result["ProjectResponsible"])
        print_text("  Project owner: " + result["ProjectOwner"])
        print_text("  Clearing state: " + result["ClearingState"])

        if len(result["Projects"]) > 0:
            print_text("\n  Linked projects: ")
            for project in result["Projects"]:
                print_text("    " + project["Name"] + ", " + project["Version"])
        else:
            print_text("\n    No linked projects")

        if len(result["Releases"]) > 0:
            print_text("\n  Components: ")
            releases = result["Releases"]
            releases.sort(key=lambda s: s["Name"].lower())
            for release in releases:
                state = self.get_clearing_state(self.project, release["Href"])
                prereq = ""
                if state == "OPEN":
                    print(Fore.LIGHTYELLOW_EX, end="", flush=True)
                    if release["SourceAvailable"] == "False":
                        print(Fore.LIGHTRED_EX, end="", flush=True)
                        prereq = "; No source provided"
                else:
                    prereq = ""

                print(
                    "    " + release["Name"] +
                    ", " + release["Version"] + " = " +
                    release.get("ProjectClearingState", "Unknown") + ", " +
                    release.get("ClearingState", "Unknown") +
                    prereq + Fore.RESET)
        else:
            print_text("    No linked releases")

    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get the project status for the project with the specified id"""
        print_text("Retrieving project details...")
        result = {}

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

        result["Name"] = self.project.get("name", "")
        result["Version"] = self.project.get("version", "")
        result["ProjectOwner"] = self.project.get("projectOwner", "")
        result["ProjectResponsible"] = self.project.get("projectResponsible", "")
        result["SecurityResponsibles"] = self.project.get("securityResponsibles", [])
        result["BusinessUnit"] = self.project.get("businessUnit", "")
        result["Tag"] = self.project.get("tag", "")
        result["enableSvm"] = self.project.get("enableSvm", None)
        result["EnableVulnerabilitiesDisplay"] = self.project.get("enableVulnerabilitiesDisplay", None)
        result["ClearingState"] = self.project.get("clearingState", "OPEN")
        if self.sw360_url:
            result["ProjectLink"] = (
                self.sw360_url + "group/guest/projects/-/project/detail/" + project_id
            )

        result["Releases"] = []

        if "sw360:releases" in self.project["_embedded"]:
            releases = self.project["_embedded"]["sw360:releases"]
            releases.sort(key=lambda s: s["name"].lower())
            for release in releases:
                href = release["_links"]["self"]["href"]
                state = self.get_clearing_state(self.project, href)

                rel_item = {}
                rel_item["Name"] = release["name"]
                rel_item["Version"] = release["version"]
                rel_item["ProjectClearingState"] = state
                rel_item["Id"] = self.client.get_id_from_href(href)
                rel_item["Sw360Id"] = rel_item["Id"]
                rel_item["Href"] = href
                rel_item["Url"] = (
                    self.sw360_url
                    + "group/guest/components/-/component/release/detailRelease/"
                    + self.client.get_id_from_href(href))

                try:
                    release_details = self.client.get_release_by_url(href)
                    if not release_details:
                        print_red("  ERROR: unable to access project:")
                        sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

                    # capycli.common.json_support.print_json(release_details)
                    rel_item["ClearingState"] = release_details["clearingState"]
                    rel_item["ReleaseMainlineState"] = release_details.get("mainlineState", "")
                    rel_item["SourceAvailable"] = "False"
                    if "externalIds" in release_details:
                        rel_item["ExternalIds"] = release_details["externalIds"]
                    if "_embedded" in release_details:
                        if "sw360:attachments" in release_details["_embedded"]:
                            att = release_details["_embedded"]["sw360:attachments"]
                            for key in att:
                                if key.get("attachmentType", "") == "SOURCE":
                                    rel_item["SourceAvailable"] = "True"
                except sw360.SW360Error as swex:
                    print_red("  ERROR: unable to access project:" + repr(swex))
                    sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

                result["Releases"].append(rel_item)

        result["Projects"] = []
        if "sw360:projects" in self.project["_embedded"]:
            projects = self.project["_embedded"]["sw360:projects"]
            projects.sort(key=lambda s: s["name"].lower())
            for project in projects:
                proj_item = {}
                proj_item["Name"] = project["name"]
                proj_item["Version"] = project["version"]
                proj_item["Href"] = project["_links"]["self"]["href"]
                result["Projects"].append(proj_item)

        return result

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
            " - Show project details\n")

        if args.help:
            print("usage: CaPyCli project show [-h] -t TOKEN -name NAME -version VERSION"
                  "[-id PROJECT_ID] [-o OUTPUTFILE]")
            print("")
            print("optional arguments:")
            print("    -h, --help            show this help message and exit")
            print("    -name NAME            name of the project")
            print("    -version VERSION      version of the project")
            print("    -id PROJECT_ID        SW360 id of the project, supersedes name and version parameters")
            print("    -t SW360_TOKEN        use this token for access to SW360")
            print("    -oa,                  this is an oauth2 token")
            print("    -url SW360_URL        use this URL for access to SW360")
            print("    -o OUTPUTFILE         output file to write project details to")
            return

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

        if pid:
            status = self.get_project_status(pid)
            self.show_project_status(status)
            if args.outputfile:
                capycli.common.json_support.write_json_to_file(status, args.outputfile)
        else:
            print_yellow("  No matching project found")
