# -------------------------------------------------------------------------------
# Copyright (c) 2022-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import sys

import sw360

import capycli.common.script_base
from capycli.common.json_support import write_json_to_file
from capycli.common.print import print_green, print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class ShowExportControlStatus(capycli.common.script_base.ScriptBase):
    """Show project export control details."""

    def show_project_status(self, result: dict):
        if not result:
            return

        print_text("  Project name: " + result["Name"] + ", " + result["Version"])
        if "ProjectResponsible" in result:
            print("  Project responsible: " + result["ProjectResponsible"])
        print_text("  Project owner: " + result["ProjectOwner"])
        print_text("  Clearing state: " + result["ClearingState"])

        if len(result["Projects"]) > 0:
            print("\n  Linked projects: ")
            for project in result["Projects"]:
                print_text("    " + project["Name"] + ", " + project["Version"])
        else:
            print_text("\n    No linked projects")

        if len(result["Releases"]) > 0:
            print_text("\n  Components: ")
            releases = result["Releases"]
            releases.sort(key=lambda s: s["Name"].lower())
            for release in releases:
                eccstate = release.get("EccStatus", "Unknown")
                eccnstate = release.get("ECCN", "Unknown")
                alstate = release.get("AL", "Unknown")
                if eccstate.lower() == "approved":
                    if (eccnstate != "N") or (alstate != "N"):
                        print_yellow(
                            "  " + release["Name"] +
                            ", " + release["Version"] + ": " +
                            "ECC status=" + eccstate + ", " +
                            "ECCN=" + eccnstate + ", " +
                            "AL=" + alstate)
                    else:
                        print_green(
                            "  " + release["Name"] +
                            ", " + release["Version"] + ": " +
                            "ECC status=" + eccstate + ", " +
                            "ECCN=" + eccnstate + ", " +
                            "AL=" + alstate)
                else:
                    print_yellow(
                        "  " + release["Name"] +
                        ", " + release["Version"] + ": " +
                        "ECC status not approved or no ECC status at all")
        else:
            print_text("    No linked releases")

    def get_project_status(self, project_id: str):
        """Get the project status for the project with the specified id"""
        print_text("Retrieving project details...")
        result = {}

        try:
            self.project = self.client.get_project(project_id)
        except sw360.SW360Error as swex:
            print_red("  ERROR: unable to access project: " + repr(swex))
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        if not self.project:
            print_red("  ERROR: unable to read project data!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        result["Name"] = self.project["name"]
        result["Version"] = self.project["version"]
        result["ProjectOwner"] = self.project["projectOwner"]
        result["ProjectResponsible"] = self.project["projectResponsible"]
        result["SecurityResponsibles"] = self.project["securityResponsibles"]
        result["BusinessUnit"] = self.project["businessUnit"]
        result["Tag"] = self.project["tag"]
        if "clearingState" in self.project:
            result["ClearingState"] = self.project["clearingState"]
        else:
            result["ClearingState"] = "OPEN"
        result["ProjectLink"] = (
            self.sw360_url + "group/guest/projects/-/project/detail/" + project_id
        )

        result["Releases"] = []

        if "sw360:releases" in self.project["_embedded"]:
            releases = self.project["_embedded"]["sw360:releases"]
            releases.sort(key=lambda s: s["name"].lower())
            for release in releases:
                href = release["_links"]["self"]["href"]

                rel_item = {}
                rel_item["Name"] = release["name"]
                rel_item["Version"] = release["version"]
                rel_item["Id"] = self.client.get_id_from_href(href)
                rel_item["S360Id"] = rel_item["Id"]
                rel_item["Href"] = href
                rel_item["Url"] = (
                    self.sw360_url
                    + "group/guest/components/-/component/release/detailRelease/"
                    + self.client.get_id_from_href(href))

                try:
                    release_details = self.client.get_release_by_url(href)
                    # capycli.common.json_support.print_json(release_details)
                    eccinfo = release_details.get("eccInformation", {})
                    rel_item["EccStatus"] = eccinfo.get("eccStatus", "UNKNOWN")
                    rel_item["AL"] = eccinfo.get("al", "UNKNOWN")
                    rel_item["ECCN"] = eccinfo.get("eccn", "UNKNOWN")
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
            " - Show project export control details\n")

        if args.help:
            print("usage: CaPyCli project ecc [-h] -name NAME -version VERSION [-id PROJECT_ID] [-o OUTPUTFILE]")
            print("")
            print("optional arguments:")
            print("    -h, --help            show this help message and exit")
            print("    -n NAME, --name NAME  name of the project")
            print("    -v VERSION,           version of the project")
            print("    -id PROJECT_ID        SW360 id of the project, supersedes name and version parameters")
            print("    -o OUTPUTFILE         output file to write project details to")
            return

        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        name = args.name
        version = None
        pid = None
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
                print_text("\nWriting result to file " + args.outputfile)
                write_json_to_file(status, args.outputfile)
        else:
            print_yellow("  No matching project found")
