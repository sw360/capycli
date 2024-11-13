# -------------------------------------------------------------------------------
# Copyright (c) 2019-2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import os
import re
import sys
import tempfile
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import packageurl
import requests
from colorama import Fore, Style
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from sw360 import SW360Error

import capycli.common.json_support
import capycli.common.script_base
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomWriter
from capycli.common.print import print_green, print_red, print_text, print_yellow
from capycli.common.purl_utils import PurlUtils
from capycli.common.script_support import ScriptSupport
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class BomCreateComponents(capycli.common.script_base.ScriptBase):
    """
    Create new components and releases on SW360
    """

    command_help = [
        "usage: CaPyCLI bom {} -i bom.json -o bom_created.json [-source <folder>]",
        "",
        "optional arguments:",
        "    -h, --help            show this help message and exit",
        "    -i INPUTFILE,         input file to read from (JSON)",
        "    -o OUTPUTFILE,        output file to write to",
        "    -t SW360_TOKEN,       use this token for access to SW360",
        "    -oa, --oauth2         this is an oauth2 token",
        "    -url SW360_URL        use this URL for access to SW360",
        "    -o OUTPUT             write updated BOM to a JSON file",
        "    -source SOURCE        source folder or additional source file",
        "    --download            enable automatic download of missing sources",
        "    --dbx                 relaxed Debian version handling: when checking for existing releases,",
        "                          ignore prefixes like \"2:\" (epoch) and suffixes like \".debian\"",
    ]

    def __init__(self, onlyCreateReleases: bool = False) -> None:
        self.source_folder: str = ""
        self.download: bool = False
        self.relaxed_debian_parsing: bool = False
        self.onlyCreateReleases: bool = onlyCreateReleases

    def upload_source_file(self, release_id: str, sourcefile: str,
                           filetype: str = "SOURCE", comment: str = "") -> None:
        """Upload source code attachment

        @params:
            release_id - the id of the release (string)
            sourcefile - name/path of the file to get uploaded (string)
            filetype   - SW360 attachment type ("SOURCE" or "SOURCE_SELF")
            comment    - upload comment for SW360 attachment
        """
        print_text("    Uploading source file: " + sourcefile)
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        try:
            self.client.upload_release_attachment(
                release_id, sourcefile, upload_type=filetype, upload_comment=comment)
        except SW360Error as swex:
            errortext = "    Error uploading source file: " + self.get_error_message(swex)
            print(Fore.LIGHTRED_EX + errortext + Style.RESET_ALL)

    def upload_file_from_url(self, release_id: str, url: Optional[str], filename: str,
                             filetype: str = "SOURCE", comment: str = "",
                             attached_filenames: List[str] = []) -> None:
        """Download a file from a URL if it's not available locally
        and upload the file as attachment to SW360.

        @params:
            release_id - the id of the release (string)
            url        - url of the file to get uploaded (string)
            filename   - local file name
            filetype   - SW360 attachment type ("SOURCE" or "SOURCE_SELF")
            comment    - upload comment for SW360 attachment
        """
        if os.path.isfile(filename):
            self.upload_source_file(release_id, filename, filetype, comment)
            return

        if self.source_folder:
            fullpath = os.path.join(self.source_folder, filename)
            if os.path.isfile(fullpath):
                self.upload_source_file(release_id, fullpath, filetype, comment)
                return

        if not self.download:
            print_red("    File not found, perhaps you want --download?")
            return

        print_text("    Downloading file", filename)

        if self.source_folder:
            tmpfolder = None
        else:
            tmpfolder = tempfile.TemporaryDirectory()
            fullpath = os.path.join(tmpfolder.name, filename)

        try:
            if not url:
                print_red("    No url specified!")
                return

            response = requests.get(url, allow_redirects=True)
            if (response.status_code == requests.codes["ok"]):
                print_text("      Writing file", fullpath)
                try:
                    open(fullpath, "wb").write(response.content)
                    if response.headers.__contains__("content-disposition"):
                        header = response.headers.get("content-disposition")
                        if header and header.__contains__("filename="):
                            print_text("      Found header:", header)
                            newfilename = header.split("=")[-1]
                            newfilename = newfilename.strip('"')
                            head, tail = os.path.split(fullpath)
                            if newfilename != tail:
                                newpath = str(fullpath).replace(tail, newfilename)
                                print_text(
                                    "      Rename downloaded file from", fullpath, "to", newpath,
                                    "because content-disposition defines this files name")
                                os.rename(fullpath, newpath)
                                fullpath = newpath

                    head, tail = os.path.split(fullpath)
                    if tail in attached_filenames:
                        # for now, we can never get here as upload_file() will not call us if *any* source
                        # attachment exists - but this code might be useful in future if this semantics changes
                        print_text(
                            "      File with the name '", tail, "' is already attached to release. Skip the upload!")
                    else:
                        self.upload_source_file(release_id, fullpath, filetype, comment)
                except Exception as ex:
                    print_red("      Error writing downloaded file: " + repr(ex))
            else:
                print_red(
                    "    Error downloading file, http response = " +
                    str(response.status_code))
        except Exception as ex:
            print_red("      Error downloading file: " + repr(ex))

        # cleanup
        if tmpfolder:
            tmpfolder.cleanup()

    def prepare_release_data(self, cx_comp: Component) -> Dict[str, Any]:
        """Create release data structure as expected by SW360 REST API

        :param item: a single bill of materials item - a release
        :type item: dictionary
        :return: the release
        :rtype: release (dictionary)
        """
        data: Dict[str, Any] = {}
        data["name"] = cx_comp.name
        data["version"] = cx_comp.version or ""

        # mandatory properties
        src_url = str(CycloneDxSupport.get_ext_ref_source_url(cx_comp))
        if src_url:
            data["sourceCodeDownloadurl"] = src_url

        bin_url = str(CycloneDxSupport.get_ext_ref_binary_url(cx_comp))
        if bin_url:
            data["binaryDownloadurl"] = bin_url

        # recommended properties
        if cx_comp.purl:
            data["externalIds"] = {}
            # ensure that we have the only correct external-id name: package-url
            data["externalIds"]["package-url"] = cx_comp.purl.to_string()

        # use project site as fallback for source code download url
        website = CycloneDxSupport.get_ext_ref_website(cx_comp)
        repo = CycloneDxSupport.get_ext_ref_repository(cx_comp)
        if not src_url:
            if repo:
                print("    Using repository for source code download URL...")
                data["sourceCodeDownloadurl"] = str(repo)
            elif website:
                print("    Using website for source code download URL...")
                data["sourceCodeDownloadurl"] = str(website)

        language = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_LANGUAGE)
        if language:
            data["languages"] = []
            data["languages"].append(language)

        return data

    def prepare_component_data(self, cx_comp: Component) -> Dict[str, Any]:
        """Create component data structure as expected by SW360 REST API

        :param item: single bill of materials item - a release
        :type item: dictionary
        :return: the release structure
        :rtype: release (dictionary)
        """
        data: Dict[str, Any] = {}
        data["description"] = "n/a"
        if cx_comp.description:
            data["description"] = cx_comp.description
        data["componentType"] = "OSS"

        language = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_LANGUAGE)
        if language:
            languages: List[str] = []
            languages.append(language)
            data["languages"] = languages

        # optional properties
        categories: List[str] = []
        cat = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_CATEGORIES)
        if cat:
            categories.append(cat)
        else:
            # default = library
            categories.append("library")

        data["categories"] = categories

        data["homepage"] = "n/a"
        website = CycloneDxSupport.get_ext_ref_website(cx_comp)
        if website:
            data["homepage"] = str(website)

        if cx_comp.purl:
            purl = PurlUtils.component_purl_from_release_purl(cx_comp.purl)
            data["externalIds"] = {"package-url": purl}
        return data

    def create_release(self, cx_comp: Component, component_id: str) -> Optional[Dict[str, Any]]:
        """Create a new release on SW360

        :param item: a single bill of materials item - a release
        :type item: dictionary
        :param component_id: the id of the component
        :type component_id: string
        :return: the release
        :rtype: release (dictionary)
        """
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        data = self.prepare_release_data(cx_comp)
        # ensure that the release mainline state is properly set
        data["mainlineState"] = "OPEN"
        try:
            release_new = self.client.create_new_release(
                cx_comp.name, cx_comp.version or "",
                component_id, release_details=data)
        except SW360Error as swex:
            errortext = "    Error creating component: " + self.get_error_message(swex)
            print_red(errortext)
            sys.exit(ResultCode.RESULT_ERROR_CREATING_COMPONENT)
        return release_new

    def update_release(self, cx_comp: Component, release_data: Dict[str, Any]) -> None:
        """Update an existing release on SW360

        :param item: a single bill of materials item - a release
        :type item: dictionary
        :param release_data: SW360 release data
        :type release_data: release (dictionary)
        """
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        release_id = self.get_sw360_id(release_data)
        data = self.prepare_release_data(cx_comp)

        update_data = {}
        if "sourceCodeDownloadurl" in data and data["sourceCodeDownloadurl"]:
            if not release_data.get("sourceCodeDownloadurl", ""):
                update_data["sourceCodeDownloadurl"] = data["sourceCodeDownloadurl"]
            elif release_data["sourceCodeDownloadurl"] != data["sourceCodeDownloadurl"]:
                print_yellow(
                    "    WARNING: SW360 source URL", release_data["sourceCodeDownloadurl"],
                    "differs from BOM URL", data["sourceCodeDownloadurl"])

        if "binaryDownloadurl" in data and data["binaryDownloadurl"]:
            if not release_data.get("binaryDownloadurl", ""):
                update_data["binaryDownloadurl"] = data["binaryDownloadurl"]
            elif release_data["binaryDownloadurl"] != data["binaryDownloadurl"]:
                print_yellow(
                    "    WARNING: SW360 binary URL", release_data["binaryDownloadurl"],
                    "differs from BOM URL", data["binaryDownloadurl"])

        if len(data.get("externalIds", {})):
            for repository_type, repository_id in data["externalIds"].items():
                if repository_type not in release_data.get("externalIds", {}):
                    update_data.setdefault("externalIds", release_data.get("externalIds", {}))
                    update_data["externalIds"][repository_type] = repository_id
                elif release_data["externalIds"][repository_type] != data["externalIds"][repository_type]:
                    id_match = False
                    try:
                        bom_purl = packageurl.PackageURL.from_string(
                            data["externalIds"][repository_type])
                        sw360_purls = PurlUtils.get_purl_list_from_sw360_object(release_data)
                        id_match = PurlUtils.contains(sw360_purls, bom_purl)
                    except ValueError:
                        pass
                    if not id_match:
                        print_yellow(
                            "    WARNING: SW360 external id", repository_type,
                            release_data["externalIds"][repository_type],
                            "differs from BOM id", data["externalIds"][repository_type])

        if len(update_data):
            # Some releases return 400 code while updating - to not break the script catch this exception
            try:
                print_text("    Updating release data")
                self.client.update_release(update_data, release_id)
            except Exception as e:
                print_yellow(
                    "    WARNING: Updating SW360 releaseId: ", release_id,
                    "data: ", update_data, "failed! ", e)

        filetype = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SRC_FILE_TYPE)
        if not filetype:
            filetype = "SOURCE"
        file_comment = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SRC_FILE_COMMENT)
        if not file_comment:
            file_comment = "Attached by CaPyCli"
        self.upload_file(cx_comp, release_data, release_id, filetype, file_comment)

    def upload_file(
            self, cx_comp: Component, release_data: Dict[str, Any],
            release_id: str, filetype: str, comment: str) -> None:
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        url = None
        filename = None
        filehash = None
        if filetype in ["SOURCE", "SOURCE_SELF"]:
            url = str(CycloneDxSupport.get_ext_ref_source_url(cx_comp))
            filename = str(CycloneDxSupport.get_ext_ref_source_file(cx_comp))
            filehash = str(CycloneDxSupport.get_source_file_hash(cx_comp))

            if filename is not None and filename.endswith('.git'):
                print_red("    WARNING: resetting filename to prevent uploading .git file")
                filename = None

        if filetype in ["BINARY", "BINARY_SELF"]:
            url = str(CycloneDxSupport.get_ext_ref_binary_url(cx_comp))
            filename = str(CycloneDxSupport.get_ext_ref_binary_file(cx_comp))
            filehash = str(CycloneDxSupport.get_binary_file_hash(cx_comp))

        # Note that we retrieve the SHA1 has from the CycloneDX data.
        # But there is no guarantee that this *IS* really a SHA1 hash!

        if (filename is None or filename == "") and url:
            filename_parsed = urlparse(url)
            if filename_parsed:
                filename = os.path.basename(filename_parsed.path)

        if not filename:
            print_red("    Unable to identify filename from url!")
            return

        if filetype.endswith("_SELF"):
            filetype_pattern = filetype[:-5]
        else:
            filetype_pattern = filetype

        attached_filenames = []
        source_attachment_exists = False
        for attachment in release_data.get("_embedded", {}).get("sw360:attachments", []):
            if attachment["attachmentType"].startswith(filetype_pattern):
                at_info = self.client.get_attachment_by_url(attachment['_links']['self']['href'])
                if at_info and at_info.get("checkStatus", "") == "REJECTED":
                    continue
                source_attachment_exists = True
                attached_filenames.append(attachment["filename"])
                if attachment["filename"] != filename:
                    print_yellow(
                        "    WARNING: different source attachment - BOM:",
                        filename, "SW360:", attachment["filename"])
                    if attachment["filename"].endswith('.git'):
                        source_attachment_exists = False
                        print_yellow(
                            "    WARNING: existing attachment has .git extension."
                            + " Upload new archive attachment ", filename)
                elif filehash and attachment["sha1"] != filehash:
                    print_yellow(
                        "    WARNING: different hash for source attachment", filename,
                        "- BOM:", filehash, "SW360:", attachment["sha1"])
                else:
                    print_green("     Attachment", filename, "ok")

        if not source_attachment_exists:
            self.upload_file_from_url(release_id, url, filename, filetype, comment, attached_filenames)

    def search_for_release(self, component: Dict[str, Any], cx_comp: Component) -> Optional[Dict[str, Any]]:
        """Checks whether the given component already contains
        the requested release

        :param component: the component (dictionary)
        :type component: dictionary
        :param release: the release (dictionary)
        :type release: dictionary
        :return: the release or None
        :rtype: release (dictionary)
        """
        if "_embedded" not in component:
            return None

        if "sw360:releases" not in component["_embedded"]:
            return None

        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        for comprel in component["_embedded"]["sw360:releases"]:
            if comprel.get("version", None) == cx_comp.version:
                return self.client.get_release_by_url(comprel["_links"]["self"]["href"])

        if self.relaxed_debian_parsing:
            # if there's no exact match, try relaxed search
            for comprel in component["_embedded"]["sw360:releases"]:
                # "2:5.2.1-1.debian" -> "5.2.1-1"
                if not cx_comp.version:
                    continue
                bom_pattern = re.sub("^[0-9]+:", "", cx_comp.version)
                bom_pattern = re.sub(r"[\. \(]*[dD]ebian[ \)]*$", "", bom_pattern)
                sw360_pattern = re.sub("^[0-9]+:", "", comprel.get("version", ""))
                sw360_pattern = re.sub(r"[\. \(]*[dD]ebian[ \)]*$", "", sw360_pattern)

                if bom_pattern == sw360_pattern:
                    print(
                        Fore.LIGHTYELLOW_EX,
                        "    WARNING: SW360 version", comprel["version"],
                        "differs from BOM version", cx_comp.version,
                        Style.RESET_ALL)
                    return self.client.get_release_by_url(comprel["_links"]["self"]["href"])
        return None

    def get_component(self, cx_comp: Component) -> str:
        """
        Get component id for related BOM item
        - Default take ComponentId from BOM item
        - Alternative search component in SW360 by name
        :param item: BOM item
        :return: id or None
        """
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        component = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_COMPONENT_ID)
        if not component:
            if self.onlyCreateReleases:
                print_yellow("    No component id in bom, skipping due to createreleases mode!")

                return ""

            components = self.client.get_component_by_name(cx_comp.name)
            if components:
                if not component and components["_embedded"]["sw360:components"]:
                    for compref in components["_embedded"]["sw360:components"]:
                        if compref["name"].lower() != cx_comp.name.lower():
                            continue
                        else:
                            component = self.get_sw360_id(compref)
                            break

        return component

    def create_component(self, cx_comp: Component) -> Optional[Dict[str, Any]]:
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        data = self.prepare_component_data(cx_comp)
        try:
            component_new = self.client.create_new_component(
                cx_comp.name,
                data["description"],
                data["componentType"],
                data["homepage"],
                component_details=data)
            print_yellow("    Component created")
            return component_new
        except SW360Error as swex:
            errortext = "    Error creating component: " + self.get_error_message(swex)
            print_red(errortext)
            sys.exit(ResultCode.RESULT_ERROR_CREATING_COMPONENT)

    def update_component(self, cx_comp: Component, component_id: str, component_data: Dict[str, Any]) -> None:
        """Update an existing component on SW360

        :param item: a single bill of materials item - a component
        :type item: dictionary
        :param component_id: SW360 component id
        :type component_id: string
        :param component_data: SW360 component data
        :type component_data: component (dictionary)
        """
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        purl = ""
        if cx_comp.purl:
            purl = PurlUtils.component_purl_from_release_purl(cx_comp.purl)
            if component_data.get("externalIds", {}).get("package-url", None) is None:
                print_red("    Updating component purl")
                try:
                    self.client.update_component_external_id("package-url", purl, component_id)
                except Exception as e:
                    print_yellow("    WARNING: Updating component failed!", e)
            elif component_data["externalIds"]["package-url"] != purl:
                id_match = False
                try:
                    bom_purl = packageurl.PackageURL.from_string(purl)
                    sw360_purls = PurlUtils.get_purl_list_from_sw360_object(component_data)
                    id_match = PurlUtils.contains(sw360_purls, bom_purl)
                except ValueError:
                    pass
                if not id_match:
                    print_yellow(
                        "    WARNING: SW360 package-url",
                        component_data["externalIds"]["package-url"],
                        "differs from BOM id", purl)

    def get_sw360_id(self, sw360_object: Dict[str, Any]) -> str:
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        return self.client.get_id_from_href(sw360_object["_links"]["self"]["href"])

    def create_component_and_release(self, cx_comp: Component) -> None:
        """Create new releases and if necessary also new components

        :param item: a single bill of materials item - a release
        :type item: dictionary
        """
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        release = None

        # Get or create component related to the BOM item
        component_id = self.get_component(cx_comp)
        if component_id:
            print_text("    Component " + cx_comp.name + " exists.")

            # get full component info
            component = self.client.get_component(component_id)
            if component:
                self.update_component(cx_comp, component_id, component)
                release = self.search_for_release(component, cx_comp)
        else:
            if self.onlyCreateReleases:
                print_red("    Component doesn't exist!")
                return

            # create component
            component = self.create_component(cx_comp)
            if not component:
                print_red("Component creation failed!")
                return

            component_id = self.get_sw360_id(component)

        try:
            if release:
                item_name = ScriptSupport.get_full_name_from_component(cx_comp)
                print_red("      " + item_name + " already exists")
            else:
                if not component:
                    return

                release = self.create_release(
                    cx_comp, self.get_sw360_id(component))
                print_text("    Release created")

            if release:
                self.update_release(cx_comp, release)
        except SW360Error as swex:
            errortext = "    Error creating release: " + self.get_error_message(swex)
            print_red(errortext)
            sys.exit(ResultCode.RESULT_ERROR_CREATING_RELEASE)

        if release:
            CycloneDxSupport.update_or_set_property(
                cx_comp, CycloneDxSupport.CDX_PROP_SW360ID, self.get_sw360_id(release))
            cx_comp.version = release["version"]

    def create_items(self, sbom: Bom) -> None:
        """Create missing components and releases

        :param bom: the bill of materials
        :type bom: list of components
        """
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        ok = True

        for cx_comp in sbom.components:
            item_name = ScriptSupport.get_full_name_from_component(cx_comp)
            id = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SW360ID)
            if id:
                print_text("  " + item_name + " already exists")
                rel = self.client.get_release(id)
                if rel:
                    self.update_release(cx_comp, rel)
            else:
                print_text("  " + item_name)
                self.create_component_and_release(cx_comp)
                id = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SW360ID)
                if id:
                    print("    Release id = " + id)
                else:
                    ok = False

            # clear map result
            CycloneDxSupport.remove_property(cx_comp, CycloneDxSupport.CDX_PROP_MAPRESULT)

        if not ok:
            print_red("An error occurred during component/release creation!")
            sys.exit(ResultCode.RESULT_ERROR_CREATING_ITEM)

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
            " - Create new components and releases on SW360\n")

        if args.help:
            sub_command = "createreleases" if self.onlyCreateReleases else "createcomponents"
            for entry in self.command_help:
                print_text(entry.format(sub_command))
            return

        if not args.inputfile:
            print_red("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if args.source:
            self.source_folder = args.source

        self.download = args.download

        if args.dbx:
            print_text("Using relaxed debian version checks")
            self.relaxed_debian_parsing = True

        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        print_text("Loading SBOM file", args.inputfile)
        try:
            sbom = CaPyCliBom.read_sbom(args.inputfile)
        except Exception as ex:
            print_red("Error reading input SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)
        print_text(" ", self.get_comp_count_text(sbom), "read from SBOM")

        print("Creating items...")
        self.create_items(sbom)

        if args.outputfile:
            print_text("Writing updated SBOM to " + args.outputfile)
            try:
                SbomWriter.write_to_json(sbom, args.outputfile, True)
            except Exception as ex:
                print_red("Error writing updated SBOM file: " + repr(ex))
                sys.exit(ResultCode.RESULT_ERROR_WRITING_BOM)

            print_text(" ", self.get_comp_count_text(sbom), "written to SBOM file")

        print("\n")
