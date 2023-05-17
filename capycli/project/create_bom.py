# -------------------------------------------------------------------------------
# Copyright (c) 2021-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import sys

import sw360

import capycli.common.script_base
from capycli import get_logger
from capycli.bom.legacy import LegacySupport
from capycli.common.capycli_bom_support import CaPyCliBom
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class CreateBom(capycli.common.script_base.ScriptBase):
    """Create a SBOM for a project on SW360."""

    def get_external_id(self, name: str, release_details: dict):
        """Returns the external id with the given name or None."""
        if "externalIds" not in release_details:
            return None

        return release_details["externalIds"].get(name, "")

    def get_attachment(self, att_type: str, release_details: dict) -> dict:
        """Returns the first attachment with the given type or None."""
        if "_embedded" not in release_details:
            return None

        if "sw360:attachments" not in release_details["_embedded"]:
            return None

        attachments = release_details["_embedded"]["sw360:attachments"]
        for attachment in attachments:
            if attachment["attachmentType"] == att_type:
                return attachment

        return None

    def get_clearing_state(self, proj, href) -> str:
        """Returns the clearing state of the given component/release"""
        rel = proj["linkedReleases"]
        for key in rel:
            if key["release"] == href:
                return key["mainlineState"]

        return None

    def create_project_bom(self, project_id) -> list:
        try:
            project = self.client.get_project(project_id)
        except sw360.sw360_api.SW360Error as swex:
            print_red("  ERROR: unable to access project:" + repr(swex))
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        print_text("  Project name: " + project["name"] + ", " + project["version"])

        bom = []

        releases = project["_embedded"].get("sw360:releases", [])
        releases.sort(key=lambda s: s["name"].lower())
        for release in releases:
            print_text("   ", release["name"], release["version"])
            href = release["_links"]["self"]["href"]
            state = self.get_clearing_state(project, href)

            rel_item = {}
            rel_item["Name"] = release["name"]
            rel_item["Version"] = release["version"]
            rel_item["ProjectClearingState"] = state
            rel_item["Id"] = self.client.get_id_from_href(href)
            rel_item["Sw360Id"] = rel_item["Id"]
            rel_item["Url"] = (
                self.sw360_url
                + "group/guest/components/-/component/release/detailRelease/"
                + self.client.get_id_from_href(href))

            try:
                release_details = self.client.get_release_by_url(href)
                # capycli.common.json_support.print_json(release_details)
                rel_item["ClearingState"] = release_details["clearingState"]
                rel_item["ReleaseMainlineState"] = release_details.get("mainlineState", "")

                rel_item["Language"] = self.list_to_string(release_details.get("languages", ""))
                rel_item["SourceCodeDownloadUrl"] = release_details.get("sourceCodeDownloadurl", "")
                rel_item["BinaryDownloadUrl"] = release_details.get("binaryDownloadurl", "")
                rel_item["Purl"] = self.get_external_id("purl", release_details)
                if not rel_item["Purl"]:
                    # try another id name
                    rel_item["Purl"] = self.get_external_id("package-url", release_details)

                if "repository" in release_details:
                    rel_item["Repository"] = release_details["repository"].get("url", "")

                source_attachment = self.get_attachment("SOURCE", release_details)
                if source_attachment:
                    rel_item["SourceCodeFile"] = source_attachment.get("filename", "")
                    rel_item["SourceCodeFileSha1"] = source_attachment.get("sha1", "")

                binary_attachment = self.get_attachment("BINARY", release_details)
                if binary_attachment:
                    rel_item["BinaryFile"] = binary_attachment.get("filename", "")
                    rel_item["BinarySha1"] = binary_attachment.get("sha1", "")

            except sw360.SW360Error as swex:
                print_red("    ERROR: unable to access project:" + repr(swex))
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

            bom.append(rel_item)

        # sub-projects are not handled at the moment

        return bom

    def show_command_help(self):
        print("\nusage: CaPyCli project createbom [options]")
        print("Options:")
        print("""
  -id ID           SW360 id of the project
  -t SW360_TOKEN   use this token for access to SW360
  -oa,             this is an oauth2 token
  -url SW360_URL   use this URL for access to SW360
  -name            name of the project, component or release
  -version         version of the project, component or release
  -o OUTPUTFILE    output file to write to
        """)

        print()

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
            " - Create a SBOM for a project on SW360\n")

        if args.help:
            self.show_command_help()
            return

        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        name = args.name
        version = None
        if args.version:
            version = args.version

        if not args.outputfile:
            print_red("No SBOM filename specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if args.id:
            pid = args.id
        elif (args.name and args.version):
            # find_project() is part of script_base.py
            pid = self.find_project(name, version)
        else:
            print_red("Neither name and version nor project id specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if pid:
            bom = self.create_project_bom(pid)

            cdx_components = []
            for item in bom:
                cx_comp = LegacySupport.legacy_component_to_cdx(item)
                cdx_components.append(cx_comp)

            CaPyCliBom.write_simple_sbom(cdx_components, args.outputfile)
        else:
            print_yellow("  No matching project found")
