# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, felix.hirschel@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import os
import re
import sys
from typing import Any, Tuple

import requests
from cyclonedx.model import ExternalReferenceType
from cyclonedx.model.bom import Bom

import capycli.common.script_base
from capycli import get_logger
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomWriter
from capycli.common.print import print_green, print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class FindSources(capycli.common.script_base.ScriptBase):
    """Go through the list of SBOM items and try to determine the source code."""

    def __init__(self) -> None:
        self.verbose: bool = False
        self.version_regex = re.compile(r"[\d+\.|_]+[\d+]")
        self.github_project_name_regex = re.compile(r"^[a-zA-Z0-9-]+(/[a-zA-Z0-9-]+)*$")
        self.github_name: str = ""
        self.github_token: str = ""

    def is_sourcefile_accessible(self, sourcefile_url: str) -> bool:
        """Check if the URL is accessible."""
        try:
            response = requests.head(sourcefile_url)
            if not response.ok:
                return False

            if self.verbose:
                disposition = response.headers.get("content-disposition", "")
                if disposition:
                    term = "filename="
                    filename = disposition[disposition.find(term) + len(term):]
                    print_text("      Final filename will be ", filename)

            if response.status_code == 302:  # Found
                return self.is_sourcefile_accessible(response.headers["Location"])

            if response.status_code == 200:  # OK
                return True
        except Exception:
            # any exception
            return False

        return False

    @staticmethod
    def get_repo_name(github_url: str) -> str:
        """Extract the GitHub repo name from the specified URL."""
        git = "github.com/"
        url = github_url.replace(".git", "").replace("#readme", "")[github_url.find(git) + len(git):]
        split = url.split("/")
        repo_name = split[0] + "/" + split[1]
        return repo_name

    @staticmethod
    def get_github_info(repository_url: str, username: str = "", token: str = "") -> Any:
        """Query tag infos from GitHub."""
        try:
            headers = {}
            if username and token:
                headers = {
                    "Username": username,
                    "Authorization": "token " + token
                }

            tag_url = "https://api.github.com/repos/" + repository_url + "/tags?per_page=100"
            tags = requests.get(tag_url, headers=headers).json()
            return tags
        except Exception as ex:
            print_yellow("      Error acccessing GitHub: " + repr(ex))
            return None

    def to_semver_string(self, version: str) -> str:
        """Bring all version information to a format we can compare."""
        result = self.version_regex.search(version)
        if result is None:
            return "0.0.0"
        ver = result.group(0).replace("_", ".")
        if not ver[0].isdigit():
            return "0.0.0"
        # Remove leading zeros e.g. 01.10.01 -> 1.10.1
        ver = ".".join(str(int(i)) for i in ver.split("."))

        if len(ver[ver.find("."):]) <= 3:
            return str(ver + ".0")
        return ver

    def get_github_source_url(self, github_url: str, version: str) -> str:
        """Find a source file URL from repository URL and version information."""
        github_url = github_url.lower()
        if "github.com" not in github_url:
            # check if non GitHub URL matches github project name format
            if self.github_project_name_regex.match(github_url):
                github_url = "github.com/" + github_url
            else:
                print_red("      This is no GitHub URL!")
                return ""

        repo_name = self.get_repo_name(github_url)

        if self.verbose:
            print_text("      repo_name:", repo_name)

        tag_info = self.get_github_info(repo_name, self.github_name, self.github_token)
        if not tag_info or (len(tag_info) == 0):
            print_red("      No reply from GitHub URL!")
            return ""

        # check for 'rate limit exceeded' message
        if "message" in tag_info:
            if tag_info["message"].startswith("API rate limit exceeded"):
                print_red("GitHub API rate limit exceeded - aborting!")
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SERVICE)
            if tag_info["message"].startswith("Bad credentials"):
                print_red("Invalid GitHub credential provided - aborting!")
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SERVICE)

        # search for a tag matching our given version information
        matching_tag = None

        normalized_version = self.to_semver_string(version)
        for tag in tag_info:
            if isinstance(tag, str):
                # this should be dictionary, if it is a string then
                # something went wrong!
                continue

            version_match = self.to_semver_string(tag.get("name", None)) == normalized_version
            if version_match:
                matching_tag = tag
                break

        if not matching_tag:
            print_yellow("      No matching tag for version " + version + " found ")
            return ""

        # print("matching_tag", matching_tag)
        source_url = matching_tag.get("zipball_url", "")
        source_url = source_url.replace(
            "https://api.github.com/repos", "https://github.com").replace(
                "zipball/refs/tags", "archive/refs/tags")
        source_url = source_url + ".zip"

        return source_url

    def find_sources(self, bom: Bom) -> Tuple[int, int]:
        """Go through the list of SBOM items and try to determine the source code."""

        print_text("\nLooping through SBOM:")
        found_count = 0
        exist_count = 0
        for component in bom.components:
            print_text(" ", component.name, component.version)

            source_file_url = CycloneDxSupport.get_ext_ref_source_url(component)
            if source_file_url:
                exist_count += 1
                print_green("    Source file URL already exists:", source_file_url)
                continue

            source_url = None
            repository_url = CycloneDxSupport.get_ext_ref_repository(component)
            website = CycloneDxSupport.get_ext_ref_website(component)
            source_code_url = CycloneDxSupport.get_ext_ref_source_code_url(component)
            if repository_url:
                if self.verbose:
                    print_text("    Repository URL available:", repository_url)
                source_url = self.get_github_source_url(
                    str(repository_url),
                    component.version)
            if website and not source_url:
                if self.verbose:
                    print_text("    Project site URL available:", website)
                source_url = self.get_github_source_url(
                    str(website),
                    component.version)
            if source_code_url and not source_url:
                if self.verbose:
                    print_text("    Repository URL available:", source_code_url)
                source_url = self.get_github_source_url(
                    str(source_code_url),
                    component.version)

            if source_url:
                if self.is_sourcefile_accessible(source_url):
                    found_count += 1
                    CycloneDxSupport.update_or_set_ext_ref(
                        component,
                        ExternalReferenceType.DISTRIBUTION,
                        CaPyCliBom.SOURCE_URL_COMMENT,
                        source_url)
                    print_green("      Found source code: " + source_url)
                else:
                    print_green("      Found source code URL found, but not accessible!")
            else:
                print_red("      No source code URL found!")
                continue

        return (found_count, exist_count)

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
            " - Go through the list of SBOM items and try to determine the source code.\n")

        if args.help:
            print("usage: CaPyCli bom findsources [-h] [-v] [-o OUTPUTFILE] -i bomfile")
            print("")
            print("optional arguments:")
            print("    -h, --help            show this help message and exit")
            print("    -i INPUTFILE          SBOM file to read from (JSON)")
            print("    -o OUTPUTFILE         output file to write to")
            print("    -name NAME            (optional) GitHub name for login")
            print("    -t TOKEN              (optional) GitHub token for login")
            print("    -v                    be verbose")
            return

        if not args.inputfile:
            print_red("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        self.verbose = args.verbose
        self.github_name = args.name
        self.github_token = args.sw360_token
        if self.verbose:
            if self.github_name and self.github_token:
                print_text("Using provided GitHub credentials")
            else:
                print_text("Using anonymous GitHub access")

        print_text("Loading SBOM file", args.inputfile)
        try:
            sbom = CaPyCliBom.read_sbom(args.inputfile)
        except Exception as ex:
            print_red("Error reading input SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)
        if self.verbose:
            print_text(" ", self.get_comp_count_text(sbom), "read from SBOM")

        found_count, exist_count = self.find_sources(sbom)
        print_text("\nOf", self.get_comp_count_text(sbom))
        print_text("  ", exist_count, "source files were already available")
        print_text("  ", found_count, "source file URLs were found.")
        print()
        missing = len(sbom.components) - exist_count - found_count
        if missing == 0:
            print_green("=> All source file URLs are known.")
        else:
            print_yellow(str(missing) + " source file URLs are missing!")

        if args.outputfile:
            print_text("Writing new SBOM to " + args.outputfile)
            try:
                SbomWriter.write_to_json(sbom, args.outputfile, True)
            except Exception as ex:
                print_red("Error writing updated SBOM file: " + repr(ex))
                sys.exit(ResultCode.RESULT_ERROR_WRITING_BOM)
            if self.verbose:
                print_text(" ", self.get_comp_count_text(sbom), "written to SBOM file")
