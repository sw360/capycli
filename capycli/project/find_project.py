# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import sys
import traceback

import requests

import capycli.common.script_base
import sw360
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class FindProject(capycli.common.script_base.ScriptBase):
    """Find projects by name on SW360"""

    def list_projects(self, name, version):
        try:
            print_text("  Searching for projects by name")
            projects = self.client.get_projects_by_name(name)

            if not projects:
                print_yellow("  No matching project found!")
                sys.exit(ResultCode.RESULT_PROJECT_NOT_FOUND)

            for project in projects:
                self.display_project(project)

        except Exception as ex:
            print_red(
                "Error searching for project: \n" +
                repr(ex) + "\n" +
                str(traceback.format_exc()))

    def display_project(self, project, pid=-1):
        if not project:
            project = self.client.get_project(pid)

        href = project["_links"]["self"]["href"]
        if "version" not in project:
            print_text(
                "    " + project["name"] + " => ID = " +
                self.client.get_id_from_href(href))
        else:
            print_text(
                "    " + project["name"] + ", " + project["version"] +
                " => ID = " + self.client.get_id_from_href(href))

    def check_project_id(self, project_id):
        try:
            project = self.client.get_project(project_id)
            if not project:
                print_yellow("No project with given id found!")
                return

            print_text(
                "Project found, name = " + project["name"] +
                ", version = " + project["version"])
        except sw360.SW360Error as swex:
            if swex.response.status_code == requests.codes['not_found']:
                print_yellow(f"Project with id {project_id} not found!")
            else:
                print_red("Error retrieving project data.")
                print_red("  Status Code: " + str(swex.response.status_code))
                if swex.message:
                    print_red("    Message: " + swex.message)
        except Exception as ex:
            print_yellow("Error searching for project: " + repr(ex))

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
            " - Find a project by name\n")

        if args.help:
            print("usage: CaPyCli project find [-h] -t TOKEN -name NAME -version VERSION [-id PROJECT_ID]")
            print("")
            print("optional arguments:")
            print("    -h, --help            show this help message and exit")
            print("    -name NAME            name of the project")
            print("    -version VERSION      version of the project")
            print("    -id PROJECT_ID        SW360 id of the project, supersedes name and version parameters")
            return

        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        name = args.name
        version = None
        if args.version:
            version = args.version

        if args.id:
            self.check_project_id(args.id)
        else:
            if name:
                if version:
                    # find_project() is part of script_base.py
                    pid = self.find_project(name, version)
                    if pid:
                        self.display_project(None, pid)
                    else:
                        print_yellow("\nNo matching project found!")
                else:
                    self.list_projects(name, version)
            else:
                print_red("Neither name nor external id specified!")
                sys.exit(ResultCode.RESULT_COMMAND_ERROR)
