# -------------------------------------------------------------------------------
# Copyright (c) 2019-24 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import json
import logging
import os
import pathlib
import re
import sys
import urllib
from enum import Enum
from typing import Any, Dict, List, Optional

from cyclonedx.model import ExternalReference, ExternalReferenceType, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from packageurl import PackageURL
from sw360 import SW360

import capycli.common.file_support
import capycli.common.script_base
from capycli import get_logger
from capycli.bom.legacy import LegacySupport
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomCreator, SbomWriter
from capycli.common.comparable_version import ComparableVersion
from capycli.common.component_cache import ComponentCacheManagement
from capycli.common.map_result import MapResult
from capycli.common.print import print_green, print_red, print_text, print_yellow
from capycli.common.purl_service import PurlService
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class MapMode(str, Enum):
    # default, write everything to resulting SBOM
    ALL = "all"
    # resulting SBOM shows only components that were found
    FOUND = "found"
    # resulting SBOM shows only components that were not found
    NOT_FOUND = "notfound"


class MapBom(capycli.common.script_base.ScriptBase):
    """
    Map a given SBOM to data on SW360
    """
    def __init__(self) -> None:
        self.releases: List[Dict[str, Any]] = []
        self.old_releases = None
        self.verbosity = 1
        self.relaxed_debian_parsing = False
        self.mode = MapMode.ALL
        self.purl_service: Optional[PurlService] = None
        self.no_match_by_name_only = True

    def is_id_match(self, release: Dict[str, Any], component: Component) -> bool:
        """Determines whether this release is a match via identifier for the specified SBOM item"""
        if not component.purl:
            return False

        cmp = component.purl.to_string().lower()
        if "ExternalIds" in release:
            extid_list = release["ExternalIds"]
        else:
            extid_list = release["externalIds"]

        for external_id in extid_list:
            if cmp == extid_list[external_id].lower():
                return True

        return False

    def filter_exceptions(self, partsBomItem: List[str]) -> List[str]:
        """Filter some parts that appear too often in too many component names"""
        if ("cordova" in partsBomItem) and ("plugin" in partsBomItem):
            partsBomItem.remove("cordova")
            partsBomItem.remove("plugin")

        return partsBomItem

    def similar_name_match(self, component: Component, release: Dict[str, Any]) -> bool:
        """Determine whether there is a release with a similar name. Similar means
        a combination of name words..."""
        SIMILARITY_THRESHOLD = 2
        separators = {"-", "@", "_"}

        if not component.name:
            return False

        if ("Name" not in release) or not release["Name"]:
            return False

        bomitem_name = component.name
        for char in separators:
            bomitem_name = bomitem_name.replace(char, " ")
        parts_bom_item = re.split(r"\W+", bomitem_name)
        if len(parts_bom_item) < 2:
            # no enough parts
            return False

        release_name = release["Name"]
        for char in separators:
            release_name = release_name.replace(char, " ")
        parts_release = re.split(r"\W+", release_name)
        if len(parts_release) < 2:
            # no enough parts
            return False

        parts_bom_item = self.filter_exceptions(parts_bom_item)

        match_count = 0
        for pitem in parts_bom_item:
            for prel in parts_release:
                if pitem.lower() == prel.lower():
                    match_count = match_count + 1

            if match_count >= SIMILARITY_THRESHOLD:
                return True

        return False

    def add_match_if_better(self, map_result: MapResult, release: Dict[str, Any], proposed_match_code: str) -> bool:
        """adds `release` with `proposed_match_code` to `map_result` if it is as good or better than the existing ones.

        :return: True if the match was added, False if it was ignored
        :rtype: bool
        """
        best_match = MapResult.NO_MATCH
        for rel in map_result.releases:
            if rel["MapResult"] < best_match:
                best_match = rel["MapResult"]

        if proposed_match_code > best_match:
            if self.verbosity > 1:
                print("    IGNORE (" + proposed_match_code + ")")
            return False

        if proposed_match_code < best_match and map_result.releases:
            map_result.releases.clear()
            if self.verbosity > 1:
                print("    CLEAR (" + proposed_match_code + ")")

        map_result.result = proposed_match_code

        release["MapResult"] = proposed_match_code
        map_result.releases.append(release)
        if self.verbosity > 1:
            print("    ADDED (" + proposed_match_code + ") " + release["Sw360Id"])
        return True

    @staticmethod
    def is_good_match(match_code: str) -> bool:
        """
        Returns True of this is a good match, i.e.
        """

        # numeric: if match_item["MapResult"] <= MapResult.GOOD_MATCH_FOUND

        # Full match by identifier.
        if match_code == MapResult.FULL_MATCH_BY_ID:
            return True

        # Full match by source file hash.
        if match_code == MapResult.FULL_MATCH_BY_HASH:
            return True

        # Full match by name and version.
        if match_code == MapResult.FULL_MATCH_BY_NAME_AND_VERSION:
            return True

        # Match by source code filename.
        if match_code == MapResult.MATCH_BY_FILENAME:
            return True

        return False

    def map_bom_item(self, component: Component, check_similar: bool, result_required: bool) -> MapResult:
        """Maps a single SBOM item to the list of SW360 releases"""

        result = self.map_bom_commons(component)
        result_release_ids = [r.split("/")[-1] for r in result.release_hrefs]
        result_component_ids = [r.split("/")[-1] for r in result.component_hrefs]

        for release in self.releases:
            if ("Id" in release) and ("Sw360Id" not in release):
                release["Sw360Id"] = release["Id"]

            # first check: unique id
            if release["Sw360Id"] in result_release_ids or self.is_id_match(release, component):
                self.add_match_if_better(result, release, MapResult.FULL_MATCH_BY_ID)
                break

            # second check: name AND version
            if (component.name and release.get("Name")):
                if release["ComponentId"] in result_component_ids:
                    name_match = True
                else:
                    name_match = component.name.lower() == release["Name"].lower()
                version_exists = "Version" in release
                if (name_match
                    and version_exists and component.version
                        and (component.version.lower() == release["Version"].lower())):
                    self.add_match_if_better(result, release, MapResult.FULL_MATCH_BY_NAME_AND_VERSION)
                    break
            else:
                name_match = False

            # third check unique(?) file hashes
            cmp_hash = CycloneDxSupport.get_source_file_hash(component)
            if (("SourceFileHash" in release)
                    and cmp_hash
                    and release["SourceFileHash"]):
                if (cmp_hash.lower() == release["SourceFileHash"].lower()):
                    self.add_match_if_better(result, release, MapResult.FULL_MATCH_BY_HASH)
                    break

            cmp_hash = CycloneDxSupport.get_binary_file_hash(component)
            if (("BinaryFileHash" in release)
                and cmp_hash
                    and release["BinaryFileHash"]):
                if (cmp_hash.lower() == release["BinaryFileHash"].lower()):
                    self.add_match_if_better(result, release, MapResult.FULL_MATCH_BY_HASH)
                    break

            # fourth check: source filename
            cmp_src_file = str(CycloneDxSupport.get_ext_ref_source_file(component))
            if (("SourceFile" in release)
                and cmp_src_file
                    and release["SourceFile"]):
                if cmp_src_file.lower() == release["SourceFile"].lower():
                    self.add_match_if_better(result, release, MapResult.MATCH_BY_FILENAME)
                    break

            # fifth check: name and ANY version
            if name_match:
                if self.no_match_by_name_only:
                    nn = release.get("Name", "")
                    vv = release.get("Version", "")
                    print_yellow(f"Match by name only found for {nn}, {component.version} => {vv}, but ignored")
                    continue

                self.add_match_if_better(result, release, MapResult.MATCH_BY_NAME)
                continue

            if check_similar:
                # sixth check: look for similar names (experimental!)
                if self.similar_name_match(component, release):
                    if self.add_match_if_better(result, release, MapResult.SIMILAR_COMPONENT_FOUND):
                        if self.verbosity > 1:
                            print("--- added MapResult.SIMILAR_COMPONENT_FOUND: " + str(release))

        if result_required:
            # use only wants to have releases report that have a clearing result available
            for item in result.releases:
                if not self.has_release_clearing_result(self.client, item):
                    print_red(
                        "item removed " +
                        item["Name"] + ", " + item["Version"])
                    result.releases.remove(item)

        return result

    def cut_off_debian_extras(self, version: str) -> str:
        """Cut of certain extra debian version infos"""
        parts = version.split("-")
        new_version = parts[0]
        return new_version

    def map_bom_item_no_cache(self, component: Component) -> MapResult:
        """Maps a single SBOM item to SW360 via online checks (no cache!)"""

        def get_release_details(href: str) -> Optional[Dict[str, Any]]:
            """Get release data from SW360 for match result"""
            if not self.client:
                return None
            real_release = self.client.get_release_by_url(href)
            if not real_release:
                print_red("Error accessing release " + href)
                return None
            release = ComponentCacheManagement.convert_release_details(self.client, real_release)
            return release

        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        result = self.map_bom_commons(component)
        components = []

        # Handle matches of PURL cache
        if result.release_hrefs:
            for href in result.release_hrefs:
                release = get_release_details(href)
                if release:
                    self.add_match_if_better(result, release, MapResult.FULL_MATCH_BY_ID)
                # If we have release matches by PURL, we're done
                return result

        if result.component_hrefs:
            components += result.component_hrefs
        else:
            # if there's no purl match for components, search by name
            components2 = self.client.get_component_by_name(component.name)
            if not components2:
                return result
            components = [
                compref["_links"]["self"]["href"]
                for compref in components2.get("_embedded", {}).get("sw360:components", [])
                if compref["name"].lower() == component.name.lower()
            ]

        for compref in components:
            comp = self.client.get_component_by_url(compref)
            if not comp:
                continue
            rel_list = comp["_embedded"].get("sw360:releases", [])

            # Sorted alternatives in descending version order
            # Please note: the release list sometimes contain just the href but no version
            try:
                rel_list = sorted(rel_list,
                                  key=lambda x: "version" in x and ComparableVersion(
                                      x.get("version", "")), reverse=True)
            except ValueError:
                pass  # we can live with an unsorted list

            for relref in rel_list:
                href = relref["_links"]["self"]["href"]

                # generate proper release for result
                release = get_release_details(href)
                if not release:
                    continue

                # first check: unique id
                if self.is_id_match(release, component):
                    self.add_match_if_better(result, release, MapResult.FULL_MATCH_BY_ID)
                    break

                # second check: name AND version (we don't need to check the name
                # again as we checked it when compiling component list)
                version_exists = "Version" in release
                if (version_exists
                        and ((component.version or "").lower() == release.get("Version", "").lower())):
                    self.add_match_if_better(result, release, MapResult.FULL_MATCH_BY_NAME_AND_VERSION)
                    break

                # third check unique(?) file hashes
                cmp_hash = CycloneDxSupport.get_source_file_hash(component)
                if (("SourceFileHash" in release)
                        and cmp_hash
                        and release["SourceFileHash"]):
                    if (cmp_hash.lower() == release["SourceFileHash"].lower()):
                        self.add_match_if_better(result, release, MapResult.FULL_MATCH_BY_HASH)
                        break

                cmp_hash = CycloneDxSupport.get_binary_file_hash(component)
                if (("BinaryFileHash" in release)
                    and cmp_hash
                        and release["BinaryFileHash"]):
                    if (cmp_hash.lower() == release["BinaryFileHash"].lower()):
                        self.add_match_if_better(result, release, MapResult.FULL_MATCH_BY_HASH)
                        break

                # fifth check: name and ANY version
                if self.no_match_by_name_only:
                    nn = release.get("Name", "")
                    vv = release.get("Version", "")
                    print_yellow(f"Match by name only found for {nn}, {component.version} => {vv}, but ignored")
                    continue
                self.add_match_if_better(result, release, MapResult.MATCH_BY_NAME)
        return result

    def has_release_clearing_result(self, client: Optional[SW360], result_item: Dict[str, Any]) -> bool:
        """Checks whether this given result item has a clearing result"""
        if not client:
            return False

        print_text(
            "Checking clearing result for " + result_item["Name"] +
            ", " + result_item["Version"])
        release = client.get_release(result_item["Sw360Id"])
        if not release:
            return False

        cli = ComponentCacheManagement.get_attachment(release, "COMPONENT_LICENSE_INFO_XML")
        if cli:
            return True

        cr = ComponentCacheManagement.get_attachment(release, "CLEARING_REPORT")
        if cr:
            return True

        return False

    def map_bom_to_releases(
            self, sbom: Bom, check_similar: bool, result_required: bool, nocache: bool = False) -> List[MapResult]:
        """Maps the bill of material items to the list of SW360 releases"""

        # Initialize external id service now, before ruin the stdout for mapping
        # with information of the cache build
        #
        # quick guess of all purl types in bom, if we make a mistake here, PurlService will
        # retrieve missing types later
        purl_types = set()
        for component in sbom.components:
            if component.purl and component.purl.type:
                purl_types.add(component.purl.type)
        self.external_id_svc.build_purl_cache(purl_types, self.verbosity <= 1)

        mapresult: list[MapResult] = []
        for component in sbom.components:
            try:
                print_text("  " + component.name + ", " + component.version)
                if nocache:
                    res = self.map_bom_item_no_cache(component)
                else:
                    res = self.map_bom_item(component, check_similar, result_required)

                mapresult.append(res)
            except Exception as ex:
                print_text("    Error mapping SBOM item: " + repr(ex))

        return mapresult

    def search_source_hash_match(self, hashvalue: str) -> None:
        """Searches SW360 for a release with an attachment with
        the specified source file hash"""
        pass

    def search_binary_hash_match(self, hashvalue: str) -> None:
        """Searches SW360 for a release with an attachment with
        the specified binary file hash"""
        pass

    def create_overview(self, result: List[MapResult]) -> Dict[str, Any]:
        """Create JSON data with an mapping result overview"""
        data: Dict[str, Any] = {}
        dataitems: List[Dict[str, Any]] = []
        overall_result = "COMPLETE"
        count = 0
        for item in result:
            if not item:
                continue

            dataitem: Dict[str, Any] = {}
            if item.input_component:
                dataitem["BomItem"] = item.input_component.name + ", " + (item.input_component.version or "")
            dataitem["ResultCode"] = item.result
            dataitem["ResultText"] = item.map_code_to_string(item.result)
            dataitems.append(dataitem)
            count = count + 1
            if (item.result == MapResult.INVALID) or (
                not self.is_good_match(item.result)
            ):
                overall_result = "INCOMPLETE"

        data["OverallResult"] = overall_result
        data["Details"] = dataitems

        return data

    def write_overview(self, overview: Dict[str, Any], filename: str) -> None:
        """Writes a JSON file with an mapping result overview"""
        with open(filename, "w") as outfile:
            json.dump(overview, outfile, indent=2)

    def get_purl_from_match(self, match: Dict[str, Any]) -> str:
        """
        Return the package-url for the given SW360 entry.
        """
        purl = ""
        if "RepositoryId" in match and match["RepositoryId"]:
            return match["RepositoryId"]

        if "ExternalIds" in match:
            if "package-url" in match["ExternalIds"]:
                purl = match["ExternalIds"]["package-url"]
            elif "purl" in match["ExternalIds"]:
                purl = match["ExternalIds"]["purl"]

        return purl

    def update_bom_item(self, component: Optional[Component], match: Dict[str, Any]) -> Component:
        """Update the (current) SBOM item with values from the match"""

        # print(match.get("Name", "???"), match.get("Version", "???"), "purl =", match.get("RepositoryId", "XXX"))
        purl = self.get_purl_from_match(match)

        if not component:
            # create a new one
            if purl:
                component = Component(
                    name=match.get("Name", ""),
                    version=match.get("Version", ""),
                    purl=PackageURL.from_string(purl),
                    bom_ref=match.get("RepositoryId", ""))
            else:
                component = Component(
                    name=match.get("Name", ""),
                    version=match.get("Version", ""))
        else:
            # always overwrite the following properties
            name = match.get("Name", "")
            if name:
                component.name = name

            version = match.get("Version", "")
            if version:
                component.version = version

            value_match = match.get("RepositoryId", "")
            if not value_match.startswith("pkg:"):
                value_match = None

            if value_match:
                component.purl = PackageURL.from_string(value_match)

        # update if current is empty
        value_match = match.get("Language", "")
        if value_match:
            prop = CycloneDxSupport.get_property(component, CycloneDxSupport.CDX_PROP_LANGUAGE)
            if not prop:
                CycloneDxSupport.update_or_set_property(
                    component, CycloneDxSupport.CDX_PROP_LANGUAGE, value_match)
            elif not prop.value:
                prop.value = value_match

        value_match = match.get("ComponentId", "")
        if value_match:
            prop = CycloneDxSupport.get_property(component, CycloneDxSupport.CDX_PROP_COMPONENT_ID)
            if not prop:
                CycloneDxSupport.update_or_set_property(
                    component, CycloneDxSupport.CDX_PROP_COMPONENT_ID, value_match)
            elif not prop.value:
                prop.value = value_match

        value_match = match.get("SourceUrl", "")
        if value_match:
            ext_ref = CycloneDxSupport.get_ext_ref(
                component,
                ExternalReferenceType.DISTRIBUTION,
                CaPyCliBom.SOURCE_URL_COMMENT)
            if not ext_ref:
                CycloneDxSupport.update_or_set_ext_ref(
                    component,
                    ExternalReferenceType.DISTRIBUTION,
                    CaPyCliBom.SOURCE_URL_COMMENT,
                    value_match)
            elif str(ext_ref.url) == "":
                ext_ref.url = XsUri(value_match)

        value_match = match.get("SourceFile", "")
        if value_match:
            value_match = urllib.parse.quote(value_match)
            ext_ref_src_file = CycloneDxSupport.get_ext_ref(
                component,
                ExternalReferenceType.DISTRIBUTION,
                CaPyCliBom.SOURCE_FILE_COMMENT)
            if not ext_ref_src_file:
                CycloneDxSupport.update_or_set_ext_ref(
                    component,
                    ExternalReferenceType.DISTRIBUTION,
                    CaPyCliBom.SOURCE_FILE_COMMENT,
                    value_match)
            elif str(ext_ref_src_file.url) == "":
                ext_ref_src_file.url = XsUri(value_match)

        value_match = match.get("BinaryFile", "")
        if value_match:
            value_match = urllib.parse.quote(value_match)
            ext_ref_bin_file = CycloneDxSupport.get_ext_ref(
                component,
                ExternalReferenceType.DISTRIBUTION,
                CaPyCliBom.BINARY_FILE_COMMENT)
            if not ext_ref_bin_file:
                CycloneDxSupport.update_or_set_ext_ref(
                    component,
                    ExternalReferenceType.DISTRIBUTION,
                    CaPyCliBom.BINARY_FILE_COMMENT,
                    value_match)
            elif str(ext_ref_bin_file.url) == "":
                ext_ref_bin_file.url = XsUri(value_match)

        value_match = match.get("ProjectSite", "")
        if value_match:
            ext_ref = CycloneDxSupport.get_ext_ref(
                component, ExternalReferenceType.WEBSITE, "")
            if not ext_ref:
                ext_ref = ExternalReference(
                    type=ExternalReferenceType.WEBSITE,
                    url=XsUri(value_match))
                component.external_references.add(ext_ref)
            elif str(ext_ref.url) == "":
                ext_ref.url = XsUri(value_match)

        # no updates for
        #  * SourceFileHash
        #  * BinaryFileHash

        value_match = match.get("Sw360Id", "")
        if value_match:
            prop = CycloneDxSupport.get_property(component, CycloneDxSupport.CDX_PROP_SW360ID)
            if not prop:
                CycloneDxSupport.update_or_set_property(
                    component, CycloneDxSupport.CDX_PROP_SW360ID, value_match)
            elif not prop.value:
                prop.value = value_match

        return component

    def create_updated_bom(self, old_bom: Bom, result: List[MapResult]) -> Bom:
        """Create an updated SBOM with the mapping results"""
        newbom = old_bom

        # clear all existing components
        newbom.components.clear()
        newbom.dependencies.clear()

        for item in result:
            newitem = None
            if item.result == MapResult.INVALID:
                if (self.mode == MapMode.FOUND):
                    continue

                newitem = Component(name="???", version="???")
                CycloneDxSupport.update_or_set_property(newitem, CycloneDxSupport.CDX_PROP_MAPRESULT, item.result)
                newbom.components.add(newitem)
                if newbom.metadata.component:
                    newbom.register_dependency(newbom.metadata.component, [newitem])
            elif (item.result == MapResult.NO_MATCH
                  or not self.is_good_match(item.result)):
                # if we have no good match, add the component we're looking for as well

                if (self.mode == MapMode.FOUND):
                    continue

                newitem = item.input_component
                if newitem:
                    CycloneDxSupport.update_or_set_property(
                        newitem,
                        CycloneDxSupport.CDX_PROP_MAPRESULT,
                        MapResult.NO_MATCH)
                newbom.components.add(newitem)

            # Sorted alternatives in descending version order
            try:
                item.releases = sorted(item.releases, key=lambda x: ComparableVersion(x['Version']), reverse=True)
            except ValueError:
                pass  # we can live with an unsorted list

            for match_item in item.releases:
                if self.is_good_match(match_item["MapResult"]):
                    # For good matches, merge the input component with the match item
                    newitem = self.update_bom_item(item.input_component, match_item)
                else:
                    # newitem = match_item
                    newitem = self.update_bom_item(None, match_item)

                CycloneDxSupport.update_or_set_property(
                    newitem,
                    CycloneDxSupport.CDX_PROP_MAPRESULT,
                    match_item["MapResult"])

                if (self.mode == MapMode.NOT_FOUND) and (self.is_good_match(match_item["MapResult"])):
                    continue

                newbom.components.add(newitem)

        return newbom

    def write_mapping_result(self, result: List[MapResult], filename: str) -> None:
        """Create a JSON file with the mapping details"""
        data = []

        for item in result:
            single_result: Dict[str, Any] = {}
            if not item.input_component:
                continue

            for prop in item.input_component.properties:
                if prop.name == CycloneDxSupport.CDX_PROP_MAPRESULT:
                    item.input_component.properties.remove(prop)
                    break

            single_result["BomItem"] = LegacySupport.cdx_component_to_legacy(item.input_component)
            single_result["Result"] = item.result
            single_result["Matches"] = []
            for item_match in item.releases:
                single_result["Matches"].append(item_match)

            data.append(single_result)

        with open(filename, "w") as outfile:
            json.dump(data, outfile, indent=4)

    def refresh_component_cache(
            self, cachefile: str, use_existing_data: bool, token: str, oauth2: bool,
            sw360_url: str) -> List[Dict[str, Any]]:
        """Refreshes the component cache."""
        cache_mgr = ComponentCacheManagement()

        if use_existing_data:
            count = cache_mgr.read_existing_component_cache(cachefile)
            print(
                " " + str(count) +
                " releases read from existing cache file.")
        print(" Refreshing component cache...")
        print(" This may take 1-3 minutes...")
        rel_data = cache_mgr.refresh_component_cache(
            cachefile, True, token, oauth2=oauth2, url=sw360_url)
        return rel_data

    def map_bom_commons(self, component: Component) -> MapResult:
        """
        Common parts to map from a SBOM component to the SW360 component/release.
        :param bomitem: SBOM component
        :return: MapResult instance, (Optional) release url, (Optional) component url
        """
        if self.relaxed_debian_parsing and component.version:
            component.version = self.cut_off_debian_extras(component.version)

        result = MapResult(component)

        # search release and component by purl which is independent of the component cache.
        if component.purl:
            result.component_hrefs = self.external_id_svc.search_components_by_purl(component.purl)
            result.release_hrefs = self.external_id_svc.search_releases_by_purl(component.purl)

        return result

    @property
    def external_id_svc(self) -> PurlService:
        """
        Lazy external id service getter
        :return: Purl service
        """
        if not self.client:
            print_red("  No client!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        if not self.purl_service:
            # Initialize external id service
            self.purl_service = PurlService(self.client)
        return self.purl_service

    def setup_cache(self, args: Any) -> None:
        if not args.nocache:
            if args.cachefile:
                cachefile = args.cachefile
            else:
                cachefile = pathlib.Path().absolute()
                cachefile = os.path.join(cachefile, ComponentCacheManagement.CACHE_FILENAME)
            print_text("\nCachefile is ", cachefile)

            print_text("  Creating backups...")
            capycli.common.file_support.create_backup(cachefile)
            capycli.common.file_support.create_backup(ComponentCacheManagement.CACHE_ALL_RELEASES)

            if args.refresh_cache:
                print_text("  Running forced component cache refresh...")
                self.releases = self.refresh_component_cache(
                    cachefile, True, args.sw360_token, oauth2=args.oauth2, sw360_url=args.sw360_url)

            print_text("  Loading cache...")
            self.releases = ComponentCacheManagement.read_component_cache(cachefile)
            if self.releases:
                print_text("  " + str(len(self.releases)) + " cached releases read from cache file.")
            else:
                self.releases = self.refresh_component_cache(
                    cachefile, False, args.sw360_token, oauth2=args.oauth2, sw360_url=args.sw360_url)

        if not self.releases:
            if args.nocache:
                print_yellow("No cached releases available!")
            else:
                print_red("No cached releases available!")
                sys.exit(ResultCode.RESULT_NO_CACHED_RELEASES)

    def show_help(self) -> None:
        """Show help text."""
        print("usage: CaPyCLI bom map [-h] [-cf CACHEFILE] [-rc] [-sc] [--nocache]")
        print("                            [-ov CREATE_OVERVIEW] [-mr WRITE_MAPRESULT] [-rr]")
        print("                            [-url SW360_URL] [-t SW360_TOKEN] [-oa] [-v] ")
        print("                            -i bomfile [-o UPDATED_BOM]")
        print("")
        print("Map a given SBOM to data on SW360")
        print("")
        print("optional arguments:")
        print("    -h, --help            show this help message and exit")
        print("    -i INPUTFILE          input file to read from (JSON)")
        print("    -cf CACHEFILE, --cachefile CACHEFILE")
        print("                          cache file name to use")
        print("    -rc, --refresh_cache  refresh component cache")
        print("    -sc, --similar        look for components with similar name")
        print("    -ov CREATE_OVERVIEW, --overview CREATE_OVERVIEW")
        print("                          create an mapping overview JSON file")
        print("    -mr WRITE_MAPRESULT, --mapresult WRITE_MAPRESULT")
        print("                          create a JSON file with the mapping details")
        print("    -o UPDATED_BOM, --update UPDATED_BOM")
        print("                          create an updated SBOM")
        print("    -rr                   there must be a clearing result available")
        print("    -t SW360_TOKEN, --token SW360_TOKEN")
        print("                          use this token for access to SW360")
        print("    -url SW360_URL        use this URL for access to SW360")
        print("    -oa, --oauth2         this is an oauth2 token")
        print("    -v                    be verbose")
        print("    --nocache             do not use component cache")
        print("    -m MODE, --mode MODE  mapping mode")
        print("                          all = default, write everything to resulting SBOM")
        print("                          found = resulting SBOM shows only components that were found")
        print("                          notfound = resulting SBOM shows only components that were not found")
        print("    --dbx                 relaxed Debian version handling: *completely* ignore Debian revision,")
        print("                          so SBOM version 3.1 will match SW360 version 3.1-3.debian")
        print("    -all                  also report matches for name, but different version")

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
            " - Map a given SBOM to data on SW360\n")

        if args.help:
            self.show_help()
            return

        if not args.inputfile:
            print_red("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if args.verbose:
            self.verbosity = 2

        if args.dbx:
            print_text("Using relaxed debian version checks")
            self.relaxed_debian_parsing = True

        if args.mode:
            self.mode = args.mode

        if args.all:
            self.no_match_by_name_only = False

        print_text("Loading SBOM file", args.inputfile)
        try:
            sbom = CaPyCliBom.read_sbom(args.inputfile)
        except Exception as ex:
            print_red("Error reading input SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)
        if self.verbosity > 1:
            print_text(" ", self.get_comp_count_text(sbom), "read from SBOM")

        if args.sw360_token and args.oauth2:
            self.analyze_token(args.sw360_token)

        print_text("  Checking access to SW360...")
        if not self.login(token=args.sw360_token, url=args.sw360_url, oauth2=args.oauth2):
            print_red("ERROR: login failed!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        self.setup_cache(args)

        look_similar = ""
        if args.similar:
            look_similar = " including components with similar names"
        print_text()
        print_text("Do mapping" + look_similar + "...")
        result = self.map_bom_to_releases(
            sbom, args.similar, args.result_required, args.nocache)

        if result:
            print_text("\nMapping result:")
            count_full_match = 0
            count_match_name = 0
            count_similar = 0
            count_no_match = 0
            for mapresult in result:
                if self.is_good_match(mapresult.result):
                    print_green("  " + str(mapresult))
                elif mapresult.result == MapResult.NO_MATCH:
                    print_red("  " + str(mapresult))
                else:
                    print_yellow("  " + str(mapresult))

                if mapresult.result == mapresult.SIMILAR_COMPONENT_FOUND:
                    count_similar = count_similar + 1
                elif mapresult.result == mapresult.MATCH_BY_NAME:
                    count_match_name = count_match_name + 1
                elif (mapresult.result == mapresult.FULL_MATCH_BY_HASH) \
                    or (mapresult.result == mapresult.FULL_MATCH_BY_ID) \
                    or (mapresult.result == mapresult.FULL_MATCH_BY_NAME_AND_VERSION) \
                        or (mapresult.result == mapresult.MATCH_BY_FILENAME):
                    count_full_match = count_full_match + 1
                else:
                    count_no_match = count_no_match + 1

            # show result overview
            print_text("")
            print_text("Total releases    = " + str(len(result)))
            print_text("  Full matches    = " + str(count_full_match))
            print_text("  Name matches    = " + str(count_match_name))
            print_text("  Similar matches = " + str(count_similar))
            print_text("  No match        = " + str(count_no_match))
        print("")

        overview = self.create_overview(result)
        if args.create_overview:
            print_text(" Creating result overview " + args.create_overview)
            self.write_overview(overview, args.create_overview)

        if args.outputfile:
            print_text("Writing updated SBOM to " + args.outputfile)
            if self.mode == MapMode.FOUND:
                print_yellow(
                    "   Resulting SBOM contains only components were a full natch was found")
            if self.mode == MapMode.NOT_FOUND:
                print_yellow(
                    "   Resulting SBOM contains only components were no match was found")
            new_bom = self.create_updated_bom(sbom, result)
            try:
                # set Siemens Standard BOM version
                SbomCreator.add_standard_bom_standard(new_bom)
                SbomWriter.write_to_json(new_bom, args.outputfile, True)
            except Exception as ex:
                print_red("Error writing updated SBOM file: " + repr(ex))
                sys.exit(ResultCode.RESULT_ERROR_WRITING_BOM)
            if self.verbosity > 1:
                print_text(" ", self.get_comp_count_text(sbom), "written to SBOM file")

        if args.write_mapresult:
            print_text(" Creating mapping result file " + args.write_mapresult)
            self.write_mapping_result(result, args.write_mapresult)

        if overview["OverallResult"] != "COMPLETE":
            print_yellow("No unique mapping found - manual action needed!\n")
            if self.mode == MapMode.ALL:
                sys.exit(ResultCode.RESULT_NO_UNIQUE_MAPPING)
            else:
                sys.exit(ResultCode.RESULT_INCOMPLETE_MAPPING)

        print_text()
        print_text("done.")
