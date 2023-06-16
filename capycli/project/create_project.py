# -------------------------------------------------------------------------------
# Copyright (c) 2019-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import os
import sys
from typing import List

import requests
import sw360
from cyclonedx.model.bom import Bom

import capycli.common.script_base
from capycli import get_logger
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class CreateProject(capycli.common.script_base.ScriptBase):
    """
    Create or update a project on SW360.
    """

    def __init__(self, onlyUpdateProject=False):
        self.onlyUpdateProject = onlyUpdateProject

    def bom_to_release_list(self, sbom: Bom) -> List[str]:
        """Creates a list with linked releases"""
        linkedReleases = []

        for cx_comp in sbom.components:
            rid = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SW360ID)
            if not rid:
                print_red(
                    + "No SW360 id given for " + cx_comp.name
                    + ", " + cx_comp.version)
                continue

            linkedReleases.append(rid)

        return linkedReleases

    def update_project(self, project_id: str, project: dict, sbom: Bom, project_info: dict) -> None:
        """Update an existing project with the given SBOM"""

        data = self.bom_to_release_list(sbom)

        ignore_update_elements = ["name", "version"]
        # remove elements from list because they are handled separately
        for element in ignore_update_elements:
            if project_info and element in project_info:
                project_info.pop(element)

        try:
            print_text("  " + str(len(data)) + " releases in SBOM")

            if project and "_embedded" in project and "sw360:releases" in project["_embedded"]:
                print_text(
                    "  " + str(len(project["_embedded"]["sw360:releases"])) +
                    " releases in project before update")

            result = self.client.update_project_releases(data, project_id, add=self.onlyUpdateProject)
            if not result:
                print_red("  Error updating project releases!")
            project = self.client.get_project(project_id)

            if len(data):
                if project and "_embedded" in project and "sw360:releases" in project["_embedded"]:
                    print_text(
                        "  " + str(len(project["_embedded"]["sw360:releases"])) +
                        " releases in project after update")
                    if len(project["_embedded"]["sw360:releases"]) != len(data):
                        print_yellow("  You might want to call `project prerequisites` to check difference")

            if project_info:
                result = self.client.update_project(project_info, project_id, add_subprojects=self.onlyUpdateProject)
                if not result:
                    print_red("  Error updating project!")

        except sw360.sw360_api.SW360Error as swex:
            if swex.response.status_code == requests.codes["unauthorized"]:
                print_red("  You are not authorized!")
                sys.exit(ResultCode.RESULT_AUTH_ERROR)
            if swex.response.status_code == requests.codes["forbidden"]:
                print_red("  You are not authorized - do you have a valid write token?")
                sys.exit(ResultCode.RESULT_AUTH_ERROR)

    def update_project_version(self, project_id: str, project: dict, new_version: str) -> None:
        """Update an existing project with the given SBOM and version"""

        """Update project metadata based on existing metadata. This will only change the version"""
        data = {}
        data["description"] = project.get("description", "")
        data["businessUnit"] = project.get("businessUnit", "")
        data["tag"] = project.get("tag", "")
        data["ownerGroup"] = project.get("ownerGroup", "")
        data["projectOwner"] = project.get("projectOwner", "")
        data["projectResponsible"] = project.get("projectResponsible", "")
        data["projectType"] = project.get("projectType", "")
        data["visibility"] = project.get("visibility", "")
        data["version"] = new_version
        data["moderators"] = []

        if project.get("_embedded").get("sw360:moderators"):
            moderators = project.get("_embedded").get("sw360:moderators")
            moderator_emails = []
            for moderator in moderators:
                moderator_email = moderator.get("email")
                moderator_emails.append(moderator_email)

            data["moderators"] = moderator_emails

        self.client.update_project(data, project_id)

    def bom_to_release_list_new(self, sbom: Bom) -> dict:
        """Creates a list with linked releases for a NEW project"""
        linkedReleases = {}

        for cx_comp in sbom.components:
            rid = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SW360ID)
            if not rid:
                print_red(
                    + "No SW360 id given for " + cx_comp.name
                    + ", " + cx_comp.version)
                continue

            linkedRelease = {}
            linkedRelease["mainlineState"] = "SPECIFIC"
            linkedRelease["releaseRelation"] = "DYNAMICALLY_LINKED"
            linkedRelease["setMainlineState"] = True
            linkedRelease["setReleaseRelation"] = True
            linkedReleases[rid] = linkedRelease

        return linkedReleases

    def upload_attachments(self, attachments):
        """Upload attachments to project"""
        print("  Upload attachments to project")

        project_attachments = self.client.get_attachment_infos_for_project(self.project_id)

        if not project_attachments:
            project_attachments = []

        for attachment in attachments:
            if 'file' not in attachment:
                print_yellow("  No file specified to upload")
            else:
                filename = os.path.basename(attachment['file'])
                upload = True
                for project_attachment in project_attachments:
                    if project_attachment['filename'] == filename:
                        print_yellow(
                            "  Attachment file " + filename +
                            " already exists! Please check manually")
                        upload = False
                        continue

                if not os.path.isfile(attachment['file']):
                    upload = False
                    print_text(attachment['file'] + " not found!")

                if not upload:
                    continue

                self.client.upload_project_attachment(self.project_id, attachment['file'], "OTHER")
                print_text("  Uploaded attachment " + attachment['file'])

    def create_project(self, name: str, version: str, sbom: Bom, project_info: dict) -> None:
        """Create a new project with the given SBOM"""

        data = project_info
        data["name"] = name
        data["version"] = version
        data["linkedReleases"] = self.bom_to_release_list_new(sbom)

        # Mandatory fields
        data["description"] = project_info.get("description", "")
        data["projectType"] = project_info.get("projectType", "")
        data["visibility"] = project_info.get("visibility", "")

        try:
            result = self.client.create_new_project(
                name,
                data["projectType"],
                data["visibility"],
                data["description"],
                version,
                project_details=data)
            # print("result", result)
            if not result:
                print_red("  Error creating project!")
            else:
                self.project_id = str(result['_links']['self']['href']).split('/')[-1]
                print("  Project created: " + self.project_id)

        except sw360.sw360_api.SW360Error as swex:
            if swex.response.status_code == requests.codes["unauthorized"]:
                print_red("  You are not authorized!")
                sys.exit(ResultCode.RESULT_AUTH_ERROR)
            elif swex.response.status_code == requests.codes["forbidden"]:
                print_red("  You are not authorized - do you have a valid write token?")
                sys.exit(ResultCode.RESULT_AUTH_ERROR)
            else:
                print_red(
                    str(swex.details.get("status", "")) + " " +
                    swex.details.get("error", "Error") + ": " +
                    swex.details.get("message", "(unknown)"))
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)
        except Exception as ex:
            print_red("  General error creating project " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

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
            " - Create or update a project on SW360\n")

        if args.help:
            print("usage: CaPyCli project create -i bom.json -o bom_created.json [-source <folder>]")
            print("")
            print("optional arguments:")
            print("    -i INPUTFILE,            bom file to read from  (JSON)")
            print("    -t SW360_TOKEN,          use this token for access to SW360")
            print("    -oa, --oauth2            this is an oauth2 token")
            print("    -url SW360_URL           use this URL for access to SW360")
            print("    -name NAME, --name NAME  name of the project")
            print("    -version VERSION,        version of the project")
            print("    -id PROJECT_ID           SW360 id of the project, supersedes name and version parameters")
            print("    -old-version             ")
            print("    -source projectinfo.json additional information about the project to be created")
            return

        if not args.inputfile:
            print_red("No input file (BOM) specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not args.id:
            if not args.name:
                print_red("Neither project name nor id specified!")
                sys.exit(ResultCode.RESULT_COMMAND_ERROR)
            if not args.version:
                print_red("Neiter project version nor id specified!")
                sys.exit(ResultCode.RESULT_COMMAND_ERROR)
            if not args.source:
                print_red("No project information file specified!")
                sys.exit(ResultCode.RESULT_COMMAND_ERROR)
            if not os.path.isfile(args.source):
                print_red("Project information file not found!")
                sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if not os.path.isfile(args.inputfile):
            print_red("Input file (BOM) not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        is_update_version = False

        if args.old_version and args.old_version != "":
            print_text("Project version will be updated with version: " + args.old_version)
            is_update_version = True

        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        print_text("Loading SBOM file", args.inputfile)
        try:
            sbom = CaPyCliBom.read_sbom(args.inputfile)
        except Exception as ex:
            print_red("Error reading input SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)

        if args.verbose:
            print_text(" ", self.get_comp_count_text(sbom), "read from SBOM")

        info = None
        if args.source:
            print("Reading project information", args.source)
            try:
                info = capycli.common.json_support.load_json_file(args.source)
            except Exception as ex:
                print_red("Error reading project information: " + repr(ex))
                sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if args.id:
            self.project_id = args.id
        elif args.name and args.version:
            if is_update_version:
                self.project_id = self.find_project(args.name, args.old_version)
            else:
                self.project_id = self.find_project(args.name, args.version)

        attachments = None
        if info and '_embedded' in info and 'sw360:attachments' in info['_embedded']:
            attachments = info['_embedded']['sw360:attachments']
            info.pop('_embedded')

        if self.project_id:
            print("Updating project...")
            try:
                project = self.client.get_project(self.project_id)
            except sw360.SW360Error as swex:
                print_red("  ERROR: unable to access project:" + repr(swex))
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

            self.update_project(self.project_id, project, sbom, info)
            if is_update_version:
                self.update_project_version(self.project_id, project, args.version)
        else:
            if self.onlyUpdateProject:
                print_yellow("Please provide project id!")
                sys.exit(ResultCode.RESULT_COMMAND_ERROR)
            print("Creating project ...")
            self.create_project(args.name, args.version, sbom, info)

        if attachments:
            self.upload_attachments(attachments)

        print("\nDone")
