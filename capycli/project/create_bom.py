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
from cyclonedx.model import ExternalReferenceType, HashAlgorithm
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component

import capycli.common.script_base
from capycli import get_logger
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomCreator
from capycli.common.purl_utils import PurlUtils
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

    def get_clearing_state(self, proj, href) -> str:
        """Returns the clearing state of the given component/release"""
        rel = proj["linkedReleases"]
        for key in rel:
            if key["release"] == href:
                return key["mainlineState"]

        return None

    def create_project_bom(self, project) -> list:
        bom = []

        releases = project["_embedded"].get("sw360:releases", [])
        releases.sort(key=lambda s: s["name"].lower())
        for release in releases:
            print_text("   ", release["name"], release["version"])
            href = release["_links"]["self"]["href"]
            sw360_id = self.client.get_id_from_href(href)

            try:
                release_details = self.client.get_release_by_url(href)

                purl = self.get_external_id("package-url", release_details)
                if not purl:
                    # try another id name
                    purl = self.get_external_id("purl", release_details)

                purl = PurlUtils.parse_purls_from_external_id(purl)
                if len(purl) > 1:
                    print_yellow("      Multiple purls added for", release["name"], release["version"])
                    print_yellow("      You must remove all but one in your SBOM!")
                purl = " ".join(purl)

                if purl:
                    rel_item = Component(name=release["name"], version=release["version"], purl=purl, bom_ref=purl)
                else:
                    rel_item = Component(name=release["name"], version=release["version"])

                for key, property in (("clearingState", CycloneDxSupport.CDX_PROP_CLEARING_STATE),
                                      ("mainlineState", CycloneDxSupport.CDX_PROP_REL_STATE)):
                    if key in release_details and release_details[key]:
                        CycloneDxSupport.set_property(rel_item, property, release_details[key])

                if "languages" in release_details and release_details["languages"]:
                    languages = self.list_to_string(release_details["languages"])
                    CycloneDxSupport.set_property(rel_item, CycloneDxSupport.CDX_PROP_LANGUAGE, languages)

                for key, comment in (("sourceCodeDownloadurl", CaPyCliBom.SOURCE_URL_COMMENT),
                                     ("binaryDownloadurl", CaPyCliBom.BINARY_URL_COMMENT)):
                    if key in release_details and release_details[key]:
                        # add hash from attachment (see below) also here if same filename?
                        CycloneDxSupport.set_ext_ref(rel_item, ExternalReferenceType.DISTRIBUTION,
                                                     comment, release_details[key])

                if "repository" in release_details and "url" in release_details["repository"]:
                    CycloneDxSupport.set_ext_ref(rel_item, ExternalReferenceType.VCS, comment=None,
                                                 value=release_details["repository"]["url"])

                attachments = self.get_release_attachments(release_details)
                for attachment in attachments:
                    at_type = attachment["attachmentType"]
                    if at_type not in CaPyCliBom.FILE_COMMENTS:
                        continue
                    comment = CaPyCliBom.FILE_COMMENTS[at_type]
                    if at_type in ("SOURCE", "SOURCE_SELF", "BINARY", "BINARY_SELF"):
                        ext_ref_type = ExternalReferenceType.DISTRIBUTION
                    else:
                        ext_ref_type = ExternalReferenceType.OTHER
                        comment += (", sw360Id: "
                                    + self.client.get_id_from_href(attachment["_links"]["self"]["href"]))
                    CycloneDxSupport.set_ext_ref(rel_item, ext_ref_type,
                                                 comment, attachment["filename"],
                                                 HashAlgorithm.SHA_1, attachment.get("sha1"))

            except sw360.SW360Error as swex:
                print_red("    ERROR: unable to access project:" + repr(swex))
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

            state = self.get_clearing_state(project, href)
            if state:
                CycloneDxSupport.set_property(rel_item, CycloneDxSupport.CDX_PROP_PROJ_STATE, state)

            CycloneDxSupport.set_property(rel_item, CycloneDxSupport.CDX_PROP_SW360ID, sw360_id)

            CycloneDxSupport.set_property(
                rel_item,
                CycloneDxSupport.CDX_PROP_SW360_URL,
                self.release_web_url(sw360_id))

            bom.append(rel_item)

        # sub-projects are not handled at the moment

        return bom

    def create_project_cdx_bom(self, project_id) -> Bom:
        try:
            project = self.client.get_project(project_id)
        except sw360.sw360_api.SW360Error as swex:
            print_red("  ERROR: unable to access project:" + repr(swex))
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        print_text("  Project name: " + project["name"] + ", " + project["version"])

        cdx_components = self.create_project_bom(project)

        creator = SbomCreator()
        sbom = creator.create(cdx_components, addlicense=True, addprofile=True, addtools=True,
                              name=project.get("name"), version=project.get("version"),
                              description=project.get("description"), addprojectdependencies=True)

        return sbom

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
            bom = self.create_project_cdx_bom(pid)
            CaPyCliBom.write_sbom(bom, args.outputfile)
        else:
            print_yellow("  No matching project found")
