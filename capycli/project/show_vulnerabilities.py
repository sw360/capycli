# -------------------------------------------------------------------------------
# Copyright (c) 2020-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import sys
from typing import Any, Dict, Optional

import requests
from colorama import Fore, Style

import capycli.common.json_support
import capycli.common.script_base
from capycli.common.print import print_green, print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode
from sw360 import SW360Error

LOG = capycli.get_logger(__name__)


class ShowSecurityVulnerability(capycli.common.script_base.ScriptBase):
    """Show security vulnerabilities of a project."""

    def __init__(self) -> None:
        """Initialize."""
        self.verbose: bool = False
        self.format: str = "text"

    def list_projects(self, name: str, version: str) -> None:
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        try:
            print_text("  Searching for projects by name (and version)")
            projects = self.client.get_projects_by_name(name)

            if not projects:
                print_yellow("  No matching project found!")
                sys.exit(ResultCode.RESULT_PROJECT_NOT_FOUND)

            for project in projects:
                if version:
                    proj_version = project.get("version", "")
                    if proj_version == version:
                        self.display_project(project)
                else:
                    self.display_project(project)

        except Exception as ex:
            print_red("Error searching for project: \n" + repr(ex))

    def show_project_by_id(self, project_id: str) -> Dict[str, Any]:
        """
        Show information about a single project by project id.
        """
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        try:
            project = self.client.get_project(project_id)
            if not project:
                print_yellow("No project with given id found!")
                sys.exit(ResultCode.RESULT_PROJECT_NOT_FOUND)

            return self.display_project(project)
        except SW360Error as swex:
            if swex.response is None:
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

            if swex.response.status_code == requests.codes['not_found']:
                print_yellow("Project not found!")
                sys.exit(ResultCode.RESULT_PROJECT_NOT_FOUND)
            else:
                print_red("Error searching for project: \n")
                print_red("  Status Code: " + str(swex.response.status_code))
                if swex.message:
                    print_red("    Message: " + swex.message)
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

    def display_project(self, project: Optional[Dict[str, Any]], pid: str = "") -> Dict[str, Any]:
        """
        Show information about a single project.
        """
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        report: Dict[str, Any] = {}
        href = None
        if pid:
            project = self.client.get_project(pid)
        else:
            if project:
                href = project["_links"]["self"]["href"]
                project = self.client.get_project_by_url(href)

        if not project:
            print_red("  No client!")
            return {}

        if not href:
            href = project["_links"]["self"]["href"]

        report["Name"] = project["name"]
        report["Version"] = project.get("version", "")
        report["Id"] = self.client.get_id_from_href(href)
        report["Sw360Id"] = report["Id"]
        report["Vulnerabilities"] = []

        print_text("Project information:")
        print_text("  Name:", project["name"])
        print_text("  Version:", project.get("version", ""))
        if self.verbose:
            print_text("  Id:", self.client.get_id_from_href(href))

        vuls = self.client.get_project_vulnerabilities(self.client.get_id_from_href(href))
        if not vuls:
            print_red("Got no vulnerabilities!")
            return {}

        # capycli.common.json_support.write_json_to_file(vuls, "vuls.json")
        if "_embedded" not in vuls:
            return report

        # 2022-07-01: SW360 changed "sw360:vulnerabilityDToes" to "sw360:vulnerabilityDTOes" - arrgghhh
        if "sw360:vulnerabilityDTOes" not in vuls["_embedded"]:
            return report

        report["Vulnerabilities"] = vuls["_embedded"]["sw360:vulnerabilityDTOes"]

        print_text("\nVulnerabilities: ")
        if len(report["Vulnerabilities"]) == 0:
            print_green("  No security vulnerabilities known or feature not enabled\n")

        for vu in report["Vulnerabilities"]:
            relevance = vu.get("projectRelevance", "???")
            prio = vu.get("priority", "???")
            color = Style.RESET_ALL
            if relevance == "RESOLVED":
                color = Fore.LIGHTGREEN_EX
            elif relevance == "IN_ANALYSIS":
                color = Fore.LIGHTYELLOW_EX
            elif ((prio == "1 - critical") or (prio == "2 - major")):
                color = Fore.LIGHTRED_EX

            print_text(color, " Priority:         ", prio)
            print_text("  Project Relevance:", relevance)
            print_text("  Project Comment:  ", vu.get("comment", "???"))
            print_text("  Project Action:   ", vu.get("projectAction", "???"))
            print_text("  Component:        ", vu.get("intReleaseName", "???"))
            print(Style.RESET_ALL)

        return report

    def check_report_for_critical_findings(self, report: Dict[str, Any], prio_text: str) -> bool:
        """
        Checks the report data for critical findings, i.e. a vulnerability
        with priority less than or equal to prio and greater than 0.
        1 - critical
        2 - major
        3 - minor
        """

        try:
            prio = int(prio_text)
        except ValueError:
            prio = 0

        if prio < 0:
            prio = 0

        if prio > 5:
            prio = 5

        if prio == 0:
            # no check requested
            return False

        for v in report.get("Vulnerabilities", []):
            vprio_text = v.get("priority", "0")
            if len(vprio_text) < 1:
                continue

            vprio = int(vprio_text[0])
            if vprio > prio:
                continue

            if v.get("projectRelevance", "???") == "NOT_CHECKED":
                return True

        return False

    def show_command_help(self) -> None:
        print("\nusage: CaPyCli project vulnerabilities [options]")
        print("Options:")
        print("""
  -id ID           SW360 id of the project
  -t SW360_TOKEN   use this token for access to SW360
  -oa,             this is an oauth2 token
  -url SW360_URL   use this URL for access to SW360
  -name            name of the project, component or release
  -version         version of the project, component or release
  -v               be verbose
  -format FMT      output format, one of [text, json], default is text
  -fe PRIO         minimum vulnerability priority to force exit code != 0
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
            " - Show security vulnerabilities of a project")

        if args.help:
            self.show_command_help()
            return

        if args.verbose:
            self.verbose = args.verbose

        self.format = args.format
        if args.verbose:
            print("Output format is", self.format)

        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        report = None
        if args.id:
            report = self.show_project_by_id(args.id)
            if args.outputfile and report:
                capycli.common.json_support.write_json_to_file(report, args.outputfile)
        else:
            if args.name:
                self.list_projects(args.name, args.version)
            else:
                print_red("Neither name nor external id specified!")
                sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        # do we have to set an exit code?
        if args.force_exit and report:
            critical = self.check_report_for_critical_findings(report, args.force_exit)
            if critical:
                print_yellow("Unhandled security vulnerability found, exiting with code != 0")
                sys.exit(ResultCode.RESULT_UNHANDLED_SECURITY_VULNERABILITY_FOUND)
