# -------------------------------------------------------------------------------
# Copyright (c) 2019-2025 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import os
import sys
from typing import Any, Dict, List, Optional

import requests
from cyclonedx.model.bom import Bom
from sw360 import SW360Error

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

    def __init__(self, onlyUpdateProject: bool = False) -> None:
        self.onlyUpdateProject = onlyUpdateProject
        self.project_mainline_state: str = ""

    def bom_to_release_list(self, sbom: Bom) -> Dict[str, Any]:
        """Creates a list with linked releases from the SBOM."""
        linkedReleases: Dict[str, Any] = {}

        for cx_comp in sbom.components:
            rid = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SW360ID)
            if not rid:
                print_red(
                    "No SW360 id given for " + str(cx_comp.name)
                    + ", " + str(cx_comp.version))
                continue

            linkedReleases[rid] = {}

            mainlineState = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_PROJ_STATE)
            if mainlineState:
                linkedReleases[rid]["mainlineState"] = mainlineState
            relation = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_PROJ_RELATION)
            if relation:
                # No typo. In project structure, it's "relation", while release update API uses "releaseRelation".
                linkedReleases[rid]["releaseRelation"] = relation

        return linkedReleases

    def merge_project_mainline_states(self, data: Dict[str, Any], project: Optional[Dict[str, Any]]) -> None:
        if not project:
            return

        if "linkedReleases" not in project:
            return

        for release in project["linkedReleases"]:  # NOT ["sw360:releases"]
            pms_release = release.get("release", "")
            if not pms_release:
                continue
            pms_release = pms_release.split("/")[-1]
            if pms_release not in data:
                continue
            pms_state = release.get("mainlineState", "OPEN")
            pms_relation = release.get("relation", "UNKNOWN")

            if "mainlineState" not in data[pms_release]:
                data[pms_release]["mainlineState"] = pms_state
            if "releaseRelation" not in data[pms_release]:
                data[pms_release]["releaseRelation"] = pms_relation

    def update_project(self, project_id: str, project: Optional[Dict[str, Any]],
                       sbom: Bom, project_info: Dict[str, Any]) -> None:
        """Update an existing project with the given SBOM"""
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        data = self.bom_to_release_list(sbom)
        self.merge_project_mainline_states(data, project)

        ignore_update_elements = ["name", "version"]
        # remove elements from list because they are handled separately
        for element in ignore_update_elements:
            if project_info and element in project_info:
                project_info.pop(element)

        # add information that this project was created by CaPyCli
        project_info["additionalData"] = {}
        project_info["additionalData"]["createdWith"] = "CaPyCli: " + capycli.get_app_version()

        try:
            print_text("  " + str(len(data)) + " releases in SBOM")

            update_mode = self.onlyUpdateProject
            if project and "_embedded" in project and "sw360:releases" in project["_embedded"]:
                print_text(
                    "  " + str(len(project["_embedded"]["sw360:releases"])) +
                    " releases in project before update")
            else:
                # Workaround for SW360 API bug: add releases will hang forever for empty projects
                update_mode = False

            # note: type in sw360python, 1.4.0 is wrong - we are using the correct one!
            result = self.client.update_project_releases(data, project_id, add=update_mode)  # type: ignore
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
                result2 = self.client.update_project(project_info, project_id, add_subprojects=self.onlyUpdateProject)
                if not result2:
                    print_red("  Error updating project!")

        except SW360Error as swex:
            if swex.response is None:
                print_red("  Unknown error: " + swex.message)
                sys.exit(ResultCode.RESULT_AUTH_ERROR)
            if swex.response.status_code == requests.codes["unauthorized"]:
                print_red("  You are not authorized!")
                sys.exit(ResultCode.RESULT_AUTH_ERROR)
            if swex.response.status_code == requests.codes["forbidden"]:
                print_red("  You are not authorized - do you have a valid write token?")
                sys.exit(ResultCode.RESULT_AUTH_ERROR)
            if swex.response:
                print_red("  " + str(swex.response.status_code) + ": " + swex.response.text)
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)
            if swex.details:
                print_red("  " + swex.details.get("error", "") + ": " + swex.details.get("message", ""))
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

            print_red("  Unknown error updating project: " + repr(swex))
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

    def update_project_version(self, project_id: str, project: Dict[str, Any], new_version: str) -> None:
        """Update an existing project with the given SBOM and version"""
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        """Update project metadata based on existing metadata. This will only change the version"""
        data: Dict[str, Any] = {}
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

        if project.get("_embedded", {}).get("sw360:moderators"):
            moderators = project.get("_embedded", {}).get("sw360:moderators")
            moderator_emails = []
            for moderator in moderators:
                moderator_email = moderator.get("email")
                moderator_emails.append(moderator_email)

            data["moderators"] = moderator_emails

        self.client.update_project(data, project_id)

    def bom_to_release_list_new(self, sbom: Bom) -> Dict[str, Any]:
        """Creates a list with linked releases for a NEW project"""
        linkedReleases: Dict[str, Any] = {}

        target_state = "SPECIFIC"
        if self.project_mainline_state:
            target_state = self.project_mainline_state

        print_text(f"  New project releases will have state {target_state}")
        for cx_comp in sbom.components:
            rid = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SW360ID)
            if not rid:
                print_red(
                    "No SW360 id given for " + cx_comp.name
                    + ", " + cx_comp.version)
                continue

            linkedRelease: Dict[str, Any] = {}
            linkedRelease["mainlineState"] = target_state
            linkedRelease["releaseRelation"] = "DYNAMICALLY_LINKED"
            linkedRelease["setMainlineState"] = True
            linkedRelease["setReleaseRelation"] = True
            linkedReleases[rid] = linkedRelease

        return linkedReleases

    def upload_attachments(self, attachments: List[Dict[str, Any]]) -> None:
        """Upload attachments to project"""
        print("  Upload attachments to project")
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

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
                    if project_attachment.get('filename', '') == filename:
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

    def create_project(self, name: str, version: str, sbom: Bom, project_info: Dict[str, Any]) -> None:
        """Create a new project with the given SBOM"""
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        data = project_info
        data["name"] = name
        data["version"] = version
        data["linkedReleases"] = self.bom_to_release_list_new(sbom)

        # Mandatory fields
        data["description"] = project_info.get("description", "")
        data["projectType"] = project_info.get("projectType", "")
        data["visibility"] = project_info.get("visibility", "")

        # add information that this project was created by CaPyCli
        data["additionalData"] = {}
        data["additionalData"]["createdWith"] = "CaPyCli: " + capycli.get_app_version()

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

        except SW360Error as swex:
            if swex.response is None:
                print_red("  Unknown error: " + swex.message)
                sys.exit(ResultCode.RESULT_AUTH_ERROR)
            if swex.response.status_code == requests.codes["unauthorized"]:
                print_red("  You are not authorized!")
                sys.exit(ResultCode.RESULT_AUTH_ERROR)
            elif swex.response.status_code == requests.codes["forbidden"]:
                print_red("  You are not authorized - do you have a valid write token?")
                sys.exit(ResultCode.RESULT_AUTH_ERROR)
            elif swex.details:
                print_red(
                    str(swex.details.get("status", "")) + " " +
                    swex.details.get("error", "Error") + ": " +
                    swex.details.get("message", "(unknown)"))
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)
        except Exception as ex:
            print_red("  General error creating project " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

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
            " - Create or update a project on SW360\n")

        if args.help:
            print("usage: CaPyCli project create -i bom.json -o bom_created.json [-source <folder>]")
            print("")
            print("optional arguments:")
            print("    -i INPUTFILE,             bom file to read from  (JSON)")
            print("    -t SW360_TOKEN,           use this token for access to SW360")
            print("    -oa, --oauth2             this is an oauth2 token")
            print("    -url SW360_URL            use this URL for access to SW360")
            print("    -name NAME                name of the project")
            print("    -version VERSION,         version of the project")
            print("    -id PROJECT_ID            SW360 id of the project, supersedes name and version parameters")
            print("    -old-version              previous version")
            print("    -source projectinfo.json  additional information about the project to be created")
            print("    -pms                      project mainline state for releases in a newly created project")
            print("    --copy_from PROJECT_ID    copy the project with the given id and the update it")
            return

        if not args.inputfile:
            print_red("No input file (BOM) specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if args.copy_from:
            if args.id:
                print_red("--copy_from cannot get combined with -id!")
                sys.exit(ResultCode.RESULT_COMMAND_ERROR)
            if not args.version:
                print_red("No version for the new project specified!")
                sys.exit(ResultCode.RESULT_COMMAND_ERROR)
        elif not args.id:
            if not args.name:
                print_red("Neither project name nor id specified!")
                sys.exit(ResultCode.RESULT_COMMAND_ERROR)
            if not args.version:
                print_red("Neither project version nor id specified!")
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
        project = None

        if args.old_version and args.old_version != "":
            print_text("Project version will be updated with version: " + args.old_version)
            is_update_version = True

        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        print_text("Loading SBOM file", args.inputfile)
        try:
            sbom = CaPyCliBom.read_sbom(args.inputfile)
        except Exception as ex:
            print_red("Error reading input SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)

        if args.verbose:
            print_text(" ", self.get_comp_count_text(sbom), "read from SBOM")

        info: Dict[str, Any] = {}
        if args.source:
            print("Reading project information", args.source)
            try:
                info = capycli.common.json_support.load_json_file(args.source)
            except Exception as ex:
                print_red("Error reading project information: " + repr(ex))
                sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if args.copy_from:
            print(f"Creating a copy of project {args.copy_from}...")
            try:
                project = self.client.duplicate_project(args.copy_from, args.version)
                if project:
                    args.id = self.client.get_id_from_href(project["_links"]["self"]["href"])
            except SW360Error as swex:
                print_red("  ERROR: unable to copy existing project:" + repr(swex))
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

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

        self.project_mainline_state = args.project_mainline_state

        if self.project_id:
            print("Updating project...")
            try:
                if project is None:
                    project = self.client.get_project(self.project_id)
            except SW360Error as swex:
                print_red("  ERROR: unable to access project:" + repr(swex))
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

            self.update_project(self.project_id, project, sbom, info)
            if is_update_version and project:
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
