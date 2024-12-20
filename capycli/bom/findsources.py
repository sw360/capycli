# -------------------------------------------------------------------------------
# Copyright (c) 2023-2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, felix.hirschel@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import os
import re
import sys
import time
from typing import Any, Dict, List, Tuple

import requests
import semver
from bs4 import BeautifulSoup
from colorama import Fore, Style

# from packageurl import PackageURL
from cyclonedx.model import ExternalReferenceType, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from sw360 import SW360Error

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
        self.sw360_url: str = os.environ.get("SW360ServerUrl", "")

    def is_sourcefile_accessible(self, sourcefile_url: str) -> bool:
        """Check if the URL is accessible."""
        try:
            response = requests.head(sourcefile_url, allow_redirects=True)
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
    def github_request(url: str, username: str = "", token: str = "") -> Any:
        try:
            headers = {}
            if token:
                headers["Authorization"] = "token " + token
            if username:
                headers["Username"] = username
            response = requests.get(url, headers=headers)
            if not response.ok:
                if response.status_code == 429 or \
                        'rate limit exceeded' in response.reason or \
                        "API rate limit exceeded" in response.json().get("message"):
                    print(
                        Fore.LIGHTYELLOW_EX +
                        "      Github API rate limit exceeded - wait 60s and retry ... " +
                        Style.RESET_ALL)
                    time.sleep(60)
                    return FindSources.github_request(url, username, token)

            return response.json()

        except Exception as ex:
            print(
                Fore.LIGHTYELLOW_EX +
                "      Error accessing GitHub: " + repr(ex) +
                Style.RESET_ALL)

            return {}

    @staticmethod
    def get_repositories(name: str, language: str, username: str = "", token: str = "") -> Any:
        """Query for GitHub repositories"""
        query = name + " language:" + language.lower()
        search_url = "https://api.github.com/search/repositories?q=" + query
        return FindSources.github_request(search_url, username, token)

    @staticmethod
    def get_repo_name(github_url: str) -> str:
        """Extract the GitHub repo name from the specified URL."""
        git = "github.com/"
        url = github_url.replace(".git", "").replace("#readme", "")[github_url.find(git) + len(git):]
        split = url.split("/")

        if len(split) > 0:
            if len(split) > 1:
                repo_name = split[0] + "/" + split[1]
            else:
                repo_name = split[0]
        else:
            print(
                Fore.LIGHTYELLOW_EX +
                "      Error getting repo name from: " + github_url +
                Style.RESET_ALL)
            return ""

        return repo_name

    if not sys.version_info < (3, 10):
        get_github_info_type = List[Dict[str, Any]] | Dict[str, Any]
    else:
        get_github_info_type = Any

    @staticmethod
    def get_github_info(repository_url: str, username: str = "",
                        token: str = "") -> get_github_info_type:
        """
        Query tag infos from GitHub.

        In the good case a list of tags entries (= dictionaries) is returned.
        In the bad case a JSON error message is returned.
        """
        length_per_page = 100
        page = 1
        tags: List[Dict[str, Any]] = []
        tag_url = "https://api.github.com/repos/" + repository_url + "/tags"
        query = "?per_page=%s&page=%s" % (length_per_page, page)
        tmp = FindSources.github_request(tag_url + query, username, token)
        if not isinstance(tmp, list):
            return tags
        tags.extend(tmp)
        while len(tmp) == length_per_page:
            page += 1
            query = "?per_page=%s&page=%s" % (length_per_page, page)
            tmp = FindSources.github_request(tag_url + query, username, token)
            tags.extend(tmp)
        return tags

    def to_semver_string(self, version: str) -> str:
        """Bring all version information to a format we can compare."""
        result = self.version_regex.search(version)
        if result is None:
            return "0.0.0"
        ver = result.group(0).replace("_", ".").replace("+", "")
        if not ver[0].isdigit():
            return "0.0.0"
        # Remove leading zeros e.g. 01.10.01 -> 1.10.1
        ver = ".".join(str(int(i)) for i in ver.split(".") if i.isnumeric())

        if len(ver[ver.find("."):]) <= 3:
            return str(ver + ".0")
        return ver

    def find_github_url(self, component: Component, use_language: bool = True) -> str:
        """ Find github url for component"""
        if not component:
            return ""
        component_name = component.name
        language = ""
        for val in component.properties:
            if val.name == "siemens:primaryLanguage":
                language = val.value
        if not use_language:
            language = ""
        repositories = self.get_repositories(
            component_name, language,
            self.github_name, self.github_token)
        if not repositories or repositories.get("total_count", 0) == 0:
            return ""
        name_match = [r for r in repositories.get("items") if r.get("name", "") == component_name]
        if not len(name_match):
            name_match = [r for r in repositories.get("items") if component_name in r.get("name", "")]
        if len(name_match):
            for match in name_match:
                tag_info = self.github_request(match["tags_url"], self.github_name, self.github_token)
                source_url = self.get_matching_tag(tag_info, component.version or "", match["html_url"])
                if len(name_match) == 1:
                    return source_url
                elif source_url:
                    return source_url

        return ""

    def get_pkg_go_repo_url(self, name: str) -> str:
        repo_request_url = 'https://pkg.go.dev/' + name
        link_repo = repo_request_url
        try:
            pkg_go_page = requests.get(repo_request_url)
            if not pkg_go_page:
                return ""

            soup = BeautifulSoup(pkg_go_page.text, 'html.parser')
            link_repo = soup.find('div', class_='UnitMeta-repo').find('a').get("href")  # type: ignore
        except Exception as ex:
            print(
                Fore.LIGHTYELLOW_EX +
                "      Error trying to get repository url: " + repr(ex) +
                Style.RESET_ALL)

        return link_repo

    def find_golang_url(self, component: Component) -> str:
        """ Find github url for component"""
        if not component:
            return ""

        component_name = component.name or ""
        component_version = component.version or ""
        suffix = "+incompatible"
        if component_version.endswith(suffix):
            component_version = component_version[:-len(suffix)]
        repository_name = self.get_pkg_go_repo_url(component_name)
        if not len(repository_name):
            return ""

        source_url = ""
        if repository_name.__contains__("github.com"):
            version_split = component_version.split("-")
            if len(version_split) == 3:
                commit_ref = version_split[2]
                print(
                    Fore.LIGHTYELLOW_EX +
                    "      Warning: version " + component_version +
                    " does not exist, trying to use the commit ref :" + commit_ref
                    + Style.RESET_ALL)
                source_url = repository_name + "/archive/" + commit_ref + ".zip"
            else:
                if component_name.startswith("github.com/"):
                    component_name_without_repo_prefix = component_name[len("github.com/"):]
                else:
                    component_name_without_repo_prefix = component_name
                if component_name_without_repo_prefix.startswith("gopkg.in/"):
                    component_name_without_repo_prefix = component_name_without_repo_prefix[len("gopkg.in/"):]
                component_name_without_version = re.sub(r"/v[0-9]+$", '', component_name_without_repo_prefix)
                component_name_without_version = re.sub(r"\.v[0-9]+$", '', component_name_without_version)
                component_name_without_github_split = component_name_without_version.split("/")
                version_prefix = None
                if len(component_name_without_github_split) > 2:
                    version_prefix = "/".join(component_name_without_github_split[2:])

                if repository_name.startswith("https://github.com/"):
                    repository_name = repository_name[len("https://github.com/"):]
                tag_info = self.get_github_info(repository_name, self.github_name, self.github_token)
                tag_info_checked = self.check_for_github_error(tag_info)
                source_url = self.get_matching_tag(tag_info_checked, component_version,
                                                   repository_name, version_prefix or "")

        # component["RepositoryUrl"] = repository_name
        return source_url

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
        tag_info_checked = self.check_for_github_error(tag_info)
        return self.get_matching_tag(tag_info_checked, version, github_url)

    def check_for_github_error(self, tag_info: get_github_info_type) -> List[Dict[str, Any]]:
        if isinstance(tag_info, list):
            # assume valid answer
            return tag_info

        # check for 'rate limit exceeded' message
        if "message" in tag_info:
            if tag_info["message"].startswith("API rate limit exceeded"):
                print_red("GitHub API rate limit exceeded - aborting!")
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SERVICE)
            if tag_info["message"].startswith("Bad credentials"):
                print_red("Invalid GitHub credential provided - aborting!")
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SERVICE)

        return []

    def get_matching_tag(self, tag_info: List[Dict[str, Any]], version: str, github_url: str,
                         version_prefix: str = "") -> str:
        if not tag_info or (len(tag_info) == 0):
            print(
                Fore.LIGHTRED_EX +
                "      No tags info reply from GitHub! " + github_url +
                Style.RESET_ALL)
            return ""

        # search for a tag matching our given version information
        matching_tag = None

        for tag in tag_info:
            try:
                if version_prefix:
                    name = tag.get("name")
                    if name and name.rpartition("/")[0] != version_prefix:
                        continue

                version_diff = semver.VersionInfo.parse(
                    self.to_semver_string(tag.get("name", None))).compare(
                    self.to_semver_string(version))
            except Exception as e:
                print(
                    Fore.LIGHTYELLOW_EX +
                    "      Warning: semver.compare() threw " + e.__class__.__name__ +
                    " Exception :" + github_url + " " + version +
                    ", released version: " + tag.get("name", None)
                    + Style.RESET_ALL)
                version_diff = 0 if tag.get("name", None) == version else 2
            # If versions are equal, version_diff shall be 0.
            # 1 and -1 have different meanings that doesn't be checked below
            if version_diff == 0:
                matching_tag = tag
                break

        if not matching_tag:
            print_yellow("      No matching tag for version " + version + " found ")
            return ""

        # print("matching_tag", matching_tag)
        source_url = matching_tag.get("zipball_url", "")
        if source_url == "":
            return ""
        source_url = source_url.replace(
            "https://api.github.com/repos", "https://github.com").replace(
                "zipball/refs/tags", "archive/refs/tags")
        source_url = source_url + ".zip"

        return source_url

    def get_source_url_from_release(self, release_id: str) -> str:
        """ get source code url from release """
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        for x in range(5):
            try:
                # print(self.client)
                release_details = self.client.get_release(release_id)
                if release_details:
                    source_url = release_details.get("sourceCodeDownloadurl", "")
                    if self.verbose:
                        print("getting source url from get from sw360 for release_id " + release_id)
                    if source_url != "":
                        return source_url
                    break
            except SW360Error as ex:
                if x < 4 and ex.response and ex.response.status_code == requests.codes["bad_gateway"]:
                    time.sleep(5)
                else:
                    raise ex

        return ""

    def get_release_component_id(self, release_id: str) -> str:
        """ get the component id of a release """
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        release_details = self.client.get_release(release_id)
        if not release_details:
            return ""

        return str(release_details["_links"]["sw360:component"]["href"]).split('/')[-1]

    def find_source_url_from_component(self, component_id: str) -> str:
        """ find source code url from component releases """
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        component_details = self.client.get_component(component_id)
        if not component_details:
            return ""

        source_url = ""
        github = "github.com"
        if component_details.get("_embedded") and \
                component_details["_embedded"].get("sw360:releases"):
            for release in component_details["_embedded"].get("sw360:releases"):
                release_id = str(release["_links"]["self"]["href"]).split('/')[-1]
                source_url = self.get_source_url_from_release(release_id)
                if source_url and github in source_url:
                    break

        if source_url and self.verbose:
            print(f'{source_url} found over component_id {component_id}')

        if not source_url and "github.com" in component_details.get("homepage", ""):
            source_url = component_details.get("homepage") or ""
            if source_url and self.verbose:
                print(f'{source_url} found on github over component homepage')

        return source_url

    def find_source_url_on_release(self, component: Component) -> str:
        """find the url from sourceCodeDownloadurl from the Id or Sw360Id"""
        url = ""
        release_id = ""
        for val in component.properties:
            if val.name == "siemens:sw360Id":
                release_id = val.value
        if release_id:
            # get the existing source_url for any kind of release.
            url = self.get_source_url_from_release(release_id)

        return url

    def find_source_url_recursive_by_sw360(self, component: Component) -> str:
        """find the url via an other release of the parent component"""
        url = ""
        found_by_component = False
        version = component.version or ""
        release_id = ""
        component_id = ""
        for val in component.properties:
            if val.name == "capycli:componentId":
                component_id = val.value
            if val.name == "siemens:sw360Id":
                release_id = val.value
        if release_id:
            # get the existing source_url for any kind of release, not only related to Github.
            url = self.get_source_url_from_release(release_id)
            if not url or url == "":
                component_id = self.get_release_component_id(release_id)
                # when searching by component, only a github url will be considered.
                url = self.find_source_url_from_component(component_id)
                found_by_component = True
        elif component_id:
            url = self.find_source_url_from_component(component_id)
            found_by_component = True

        # 2nd try for component only when on github: find again the proper url for the current version.
        if url and found_by_component and "github.com" in url:
            url = self.get_github_source_url(url, version)

        return url

    @staticmethod
    def find_source_url_by_language(component: Component) -> str:
        capycli.dependencies.javascript.GetJavascriptDependencies().try_find_component_metadata(component, "")
        url = CycloneDxSupport.get_ext_ref_source_url(component)
        if isinstance(url, XsUri):
            return url._uri
        else:
            return url

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

            # skip source URL check for debian components as github url s are invalid for Debian.
            if str(component.purl).startswith("pkg:deb/debian/") or str(component.bom_ref).startswith("pkg:deb/debian"):
                print_red("No source code check for debian components!")
                continue

            language = ""
            for val in component.properties:
                if val.name == "siemens:primaryLanguage":
                    language = val.value
            # first check if not already set on the release.
            if self.use_sw360:
                if self.verbose:
                    print("    No Source code URL available",
                          "try to find from sw360 component or releases")
                try:
                    source_url = self.find_source_url_on_release(component)
                except SW360Error as swex:
                    if swex.response is None:
                        print_red("  Unknown error: " + swex.message)
                    elif swex.response.status_code == requests.codes['not_found']:
                        print(
                            Fore.LIGHTYELLOW_EX + "  Release not found " + component.name +
                            ", " + component.version + Style.RESET_ALL)
                    else:
                        print(Fore.LIGHTRED_EX + "  Error retrieving release data: ")
                        print("  " + component.name + ", " + component.version)
                        print("  Status Code: " + str(swex.response.status_code))
                        if swex.message:
                            print("    Message: " + swex.message)
                        print(Style.RESET_ALL)

            # then consider the package managers
            if not source_url and language.lower() == "javascript":
                if self.verbose:
                    print("    No Source code URL available - try to find with language:")
                source_url = self.find_source_url_by_language(component)
            if not source_url and (language.lower() == "golang" or language.lower() == "go"):
                if self.verbose:
                    print("    No Source code URL available - try to find on pkg.go.dev:")
                source_url = self.find_golang_url(component)

            # finally look on github
            repository_url = CycloneDxSupport.get_ext_ref_repository(component)
            if repository_url and not source_url:
                if self.verbose:
                    print_text("    Repository URL available:", repository_url)
                source_url = self.get_github_source_url(
                    str(repository_url),
                    component.version)
            binary_url = CycloneDxSupport.get_ext_ref_binary_url(component)
            if binary_url and not source_url:
                if self.verbose:
                    print_text("    Repository URL available:", repository_url)
                source_url = self.get_github_source_url(
                    str(binary_url),
                    component.version)
            website = CycloneDxSupport.get_ext_ref_website(component)
            if website and not source_url:
                if self.verbose:
                    print_text("    Project site URL available:", website)
                source_url = self.get_github_source_url(
                    str(website),
                    component.version)
            source_code_url = CycloneDxSupport.get_ext_ref_source_code_url(component)
            if source_code_url and not source_url:
                if self.verbose:
                    print_text("    Repository URL available:", source_code_url)
                source_url = self.get_github_source_url(
                    str(source_code_url),
                    component.version)

            # look via the component
            if not source_url and self.use_sw360:
                if self.verbose:
                    print("    No Source code URL available",
                          "try to find via the parent sw360 component")
                source_url = self.find_source_url_recursive_by_sw360(component)

            # deeper search on github
            if not source_url:
                if self.verbose:
                    print("    No Source code URL available - try to find on github:")
                source_url = self.find_github_url(component)
            if not source_url and not language == "":
                if self.verbose:
                    print("    No Source code URL available - try to find on github without language:")
                source_url = self.find_github_url(component, use_language=False)

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
            print("    -t SW360_TOKEN        (optional) use this token for access to SW360")
            print("    -oa, --oauth2         (optional) this is an oauth2 token")
            print("    -url SW360_URL        (optional) use this URL for access to SW360")
            print("    -name NAME            (optional) GitHub name for login")
            print("    -gt TOKEN             (optional) GitHub token for login")
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
        self.github_token = args.github_token
        if args.sw360_url:
            self.sw360_url = args.sw360_url

        if self.sw360_url:
            self.login(
                token=args.sw360_token, url=self.sw360_url, oauth2=args.oauth2)
            print("Using SW360 releases and components to detect GitHub url")
            self.use_sw360 = True
        else:
            self.use_sw360 = False
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
