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

from colorama import Fore
from cyclonedx.model.bom import Bom

import capycli.common.script_base
from capycli import get_logger
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.common.print import print_green, print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class CheckPrerequisites(capycli.common.script_base.ScriptBase):
    """Checks whether all prerequisites for a successful software clearing are fulfilled."""

    def get_clearing_state(self, project: Dict[str, Any], href: str) -> str:
        """Returns the clearing state of the given component/release"""
        rel = project.get("linkedReleases", [])
        for key in rel:
            if key["release"] == href:
                return key.get("mainlineState", "")

        return ""

    def get_source_code(self, release: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return list of attachment infos for all source code attachments"""
        if "_embedded" not in release:
            return []

        if "sw360:attachments" not in release["_embedded"]:
            return []

        att = [
            entry
            for entry in release["_embedded"]["sw360:attachments"]
            if entry.get("attachmentType", "") in ("SOURCE", "SOURCE_SELF")
        ]
        return att

    def get_component_management_id(self, release: Dict[str, Any]) -> Dict[Any, Any]:
        """Retries the first component management id"""
        if "externalIds" not in release:
            return {}

        id_dict = dict(release.get("externalIds", {}))

        # remove all known ids
        if "com.siemens.mainl.component.id" in id_dict:
            del id_dict["com.siemens.mainl.component.id"]

        if "com.siemens.mainl.component.request" in id_dict:
            del id_dict["com.siemens.mainl.component.request"]

        if "com.siemens.em.component.id" in id_dict:
            del id_dict["com.siemens.em.component.id"]

        if "com.siemens.svm.component.id" in id_dict:
            del id_dict["com.siemens.svm.component.id"]

        return id_dict

    def check_checkStatus(self, source_info: Dict[str, Any]) -> None:
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        attachment = self.client.get_attachment_by_url(
            source_info["_links"]["self"]["href"]
        )
        if attachment and attachment["checkStatus"] == "ACCEPTED":
            print_green(
                "        " +
                attachment["filename"] +
                " ACCEPTED by " +
                attachment["checkedBy"])
        pass

    def any_sw360id_in_bom(self, sbom: Bom) -> bool:
        """Checks whether there are Sw360ids in the SBOM.
        If there are no such properties at all, there is no need to
         search for them."""
        for cx_comp in sbom.components:
            if CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SW360ID):
                return True

        return False

    def check_project_prerequisites(self, id: str, sbom: Optional[Bom]) -> bool:
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        try:
            project = self.client.get_project(id)
        except Exception as ex:
            print_red("Error retrieving project details: \n" + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        if not project:
            print_red("Error retrieving project details")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        count_errors = 0
        count_warnings = 0
        print_text("  Project name: " + project["name"] + ", " + project["version"])
        print_text("  Clearing state: " + project.get("clearingState", "UNKNOWN"))

        if not project.get("projectOwner", None):
            print_yellow("  No project owner specified!")
            count_warnings += 1
        else:
            print_green("  Project owner: " + project.get("projectOwner", "UNKNOWN"))

        if not project.get("projectResponsible", None):
            print_yellow("  No project responsible specified!")
            count_warnings += 1
        else:
            print_green(
                "  Project responsible: "
                + project["projectResponsible"])

        if len(project.get("securityResponsibles", [])) < 1:
            print_yellow("  No security responsibles specified!")
            count_warnings += 1
        else:
            print_green(
                "  Security responsible(s): "
                + self.list_to_string(project["securityResponsibles"]))

        if not project.get("tag", None):
            print_yellow("  No tag specified!")
            count_warnings += 1
        else:
            print_green("  Tag: " + project.get("tag", "UNKNOWN"))

        if "sw360:projects" in project["_embedded"]:
            linked_projects = project["_embedded"]["sw360:projects"]
            if linked_projects:
                print_text("\n  Linked projects: ")
                for key in linked_projects:
                    print_text("    " + key["name"] + ", " + key["version"])
        else:
            print_text("\n    No linked projects")

        releases: Dict[str, Any] = {}
        if "sw360:releases" in project["_embedded"]:
            print_text("\n  Components: ")
            releases = project["_embedded"]["sw360:releases"]
            for key in releases:
                href = key["_links"]["self"]["href"]
                release = self.client.get_release_by_url(href)
                if not release:
                    print_red("Error accessign release " + href)
                    count_errors += 1
                    continue

                state = self.get_clearing_state(project, href)

                print_text("    " + key["name"] + ", " + key["version"] + ": " + state)

                if not release.get("sourceCodeDownloadurl", ""):
                    print_yellow("      No download URL specified!")
                    count_warnings += 1
                else:
                    print_green(
                        "      Download URL: " +
                        release["sourceCodeDownloadurl"])

                if len(release.get("languages", [])) < 1:
                    print_yellow("      No programming language specified!")
                    count_warnings += 1
                else:
                    print_green(
                        "      Programming language: " +
                        release["languages"][0])

                bom_sha1 = None
                if sbom and self.any_sw360id_in_bom(sbom):
                    release_id = self.client.get_id_from_href(href)
                    bom_item = [cx_comp for cx_comp in sbom.components
                                if CycloneDxSupport.get_property_value(
                                    cx_comp, CycloneDxSupport.CDX_PROP_SW360ID) == release_id]
                    if len(bom_item) == 0:
                        print_red("      Item not in specified SBOM!")
                        count_errors += 1
                    else:
                        assert len(bom_item) == 1
                        bom_sha1 = CycloneDxSupport.get_source_file_hash(bom_item[0])

                source = self.get_source_code(release)
                for source_info in source:
                    source_name = source_info.get("filename", "")
                    if "-SOURCES.JAR" in source_name.upper():
                        print_yellow(
                            "      Source " +
                            source_name +
                            " seems to be from Maven!")
                        count_warnings += 1
                    if bom_sha1:
                        if bom_sha1 != source_info.get("sha1", ""):
                            print_red(
                                "      SHA1 for source " +
                                source_name +
                                " does not match!")
                            count_errors += 1
                            self.check_checkStatus(source_info)
                        else:
                            print_green(
                                "      SHA1 for source" +
                                source_name +
                                " matches!")

                if len(source) != 1:
                    if state == "OPEN":
                        print(Fore.LIGHTRED_EX, end="")
                        count_errors += 1
                    else:
                        print(Fore.LIGHTYELLOW_EX, end="")
                        count_warnings += 1
                else:
                    print(Fore.LIGHTGREEN_EX, end="")
                print("     ", len(source), "source file(s) available." + Fore.RESET)

                ids = self.get_component_management_id(release)
                if (not ids) or (not ids):
                    print_yellow(
                        "      No component management id (package-url, etc.) specified!")
                    count_warnings += 1
                else:
                    print_green("      component management id: " + str(ids))

                print()

            if sbom:
                print()
                print_text("    SBOM release check:")
                for cx_comp in sbom.components:
                    # note that a SBOM does not need to contain Sw360Id properties
                    sw360id = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SW360ID)
                    if not sw360id:
                        continue

                    found = [rel for rel in releases
                             if sw360id in rel["_links"]["self"]["href"]]
                    if len(found) == 0:
                        print_red(
                            "      SBOM Item not in SW360 project: "
                            + cx_comp.name + " " + cx_comp.version)
                        count_errors += 1
                print_text("      Check finished.")
            else:
                print_yellow("      No SBOM specified, skipping release comparison!")

        else:
            print_text("    No linked releases")

        print_text("\nSummary:")
        if releases:
            print_text("  Total components: " + str(len(releases)))
        else:
            print_text("  Total components: 0 (no releases)")
        if count_warnings > 0:
            print_yellow("  Warnings: " + str(count_warnings))
        if count_errors > 0:
            print_red("  Errors: " + str(count_errors))

        return count_errors > 0

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
            " - Checks whether all prerequisites for a successful software " +
            "clearing are fulfilled\n")

        if args.help:
            print("Usage: CaPyCli project prerequisites [-i INPUTFILE] -id ID [-name NAME] [-v VERSION] [-url URL]")
            print("")
            print("Checks whether all prerequisites for a successful software clearing are fulfilled")
            print("")
            print("Options:")
            print("    -h, --help              show this help message and exit")
            print("    -n NAME, --name NAME    name of the project")
            print("    -v VERSION,             version of the project")
            print("    -id PROJECT_ID          SW360 id of the project, supersedes name and version parameters")
            print("    -i INPUTFILE            SBOM input file to read from (JSON)")
            print("    -t SW360_TOKEN,         use this token for access to SW360")
            print("    -oa, --oauth2           this is an oauth2 token")
            print("    -url SW360_URL          use this URL for access to SW360")
            print("    --forceerror            force an error exit code in case of prerequisite errors")
            return

        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        sbom = None
        if args.inputfile:
            if not os.path.isfile(args.inputfile):
                print_red("Input file (BOM) not found!")
                sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

            print_text("Loading SBOM file", args.inputfile)
            try:
                sbom = CaPyCliBom.read_sbom(args.inputfile)
            except Exception as ex:
                print_red("Error reading input SBOM file: " + repr(ex))
                sys.exit(ResultCode.RESULT_ERROR_READING_BOM)

            if args.verbose:
                print_text(" ", self.get_comp_count_text(sbom), "read from SBOM")

        name: str = args.name
        version: str = ""
        if args.version:
            version = args.version

        if args.id:
            self.check_project_prerequisites(args.id, sbom)
        elif (args.name and args.version):
            # find_project() is part of script_base.py
            pid = self.find_project(name, version)
            if pid:
                if (self.check_project_prerequisites(pid, sbom) and args.force_error):
                    sys.exit(ResultCode.RESULT_PREREQUISITE_ERROR)
            else:
                print_yellow("  No matching project found")
        else:
            print_red("Neither name and version nor project id specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)
