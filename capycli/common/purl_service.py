# -------------------------------------------------------------------------------
# Copyright (c) 2022-2023 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com, thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from typing import Any, Dict, List, Optional, Tuple

import packageurl
from sw360 import SW360

from capycli.common.print import print_green, print_text, print_yellow
from capycli.common.purl_store import PurlStore
from capycli.common.purl_utils import PurlUtils


class PurlService:
    def __init__(self, client: SW360, cache: Optional[Dict] = None) -> None:  # type: ignore
        self.client: SW360 = client
        self.purl_cache: PurlStore = PurlStore(cache)

    def build_purl_cache(self, purl_types: Any = tuple(), no_warnings: bool = True) -> None:
        """
        Retrieve all package-url external ids for components and releases
        and cache them in self.purl_cache as a chain of dictionaries. As the
        package url encoding isn't unique, we need to decode them.

        As an example, self.purl_cache["deb"]["debian"]["bash"]["4.4"] will
        contain the release id of bash 4.4 and self.purl_cache["deb"]["debian"]
        ["bash"][None] contains the component id of "bash".

        To save a bit of time and especially reduce number of warnings, you can
        specify `purl_types` to only include certain purls into cache
        (e.g. ("deb", "npm"))
        """
        if self.purl_cache:
            missing = False
            for pt in purl_types:
                if pt not in self.purl_cache:
                    missing = True
            if not missing:
                return

        print_text("Retrieving package-url ids, filter:", purl_types)
        all_ids = self.client.get_components_by_external_id("package-url")
        if all_ids and len(all_ids) == 0:
            all_ids = self.client.get_releases_by_external_id("package-url")
        else:
            all_rids = self.client.get_releases_by_external_id("package-url")
            if all_rids:
                all_ids = all_ids + all_rids
        print_text(" Found", len(all_ids), "total purls")

        for entry in all_ids:
            for purl_string in PurlUtils.parse_purls_from_external_id(entry["externalIds"]["package-url"]):
                try:
                    purl = packageurl.PackageURL.from_string(purl_string)
                    if purl_types and purl.type not in purl_types:
                        continue
                    if not no_warnings:
                        for e in self.purl_cache.get_by_version(purl):
                            if e["purl"] == purl:
                                print_yellow("-> Multiple entries for purl:", purl)
                                print_yellow(
                                    self.client.url +
                                    "group/guest/components/-/component/release/detailRelease/" +
                                    self.client.get_id_from_href(e["href"]))
                                print_yellow(
                                    self.client.url +
                                    "group/guest/components/-/component/release/detailRelease/" +
                                    self.client.get_id_from_href(entry["_links"]["self"]["href"]))

                    self.purl_cache.add(purl, entry["_links"]["self"]["href"])
                except ValueError:
                    if not no_warnings:
                        print_yellow("-> Ignoring invalid purl entry in", entry["_links"]["self"]["href"])
                        print_yellow(purl_string)

    def search_releases_by_external_id(self, ext_id_name: str, ext_id_value: str) -> List[Dict[str, Any]]:
        """Get SW360 release by external id

        For now, this only supports searching for package urls.

        :param ext_id_name: type of external id ("package-url", "npm-id", etc.)
        :type ext_id_name: string
        :param ext_id_value: external id
        :type ext_id_value: string
        :return: list of dictionaries with `href` and `purl` keys
        """
        if ext_id_name != "package-url":
            return []

        if not ext_id_value:
            return []

        purl = packageurl.PackageURL.from_string(ext_id_value)
        self.build_purl_cache((purl.type,))

        return self.purl_cache.get_by_version(purl)

    def search_release_by_external_id(self, ext_id_name: str, ext_id_value: str) -> Optional[str]:
        """Get exactly one SW360 release by external id

        :param ext_id_name: type of external id ("package-url", "npm-id", etc.)
        :type ext_id_name: str
        :param ext_id_value: external id
        :type ext_id_value: str
        :return: href of the release or None if not found
        """
        result = self.search_releases_by_external_id(ext_id_name, ext_id_value)
        unique_hrefs = {r["href"] for r in result}

        if len(unique_hrefs) == 1:
            return result[0]["href"]
        elif len(unique_hrefs) > 1:
            print_yellow("    No unique release match for", ext_id_value)
            for r in result:
                print_yellow("      Candidate", self.client.get_id_from_href(r["href"]),
                             "has purl", r["purl"])
            return None

        return None

    def search_components_by_external_id(self, ext_id_name: str, ext_id_value: str) -> List[Dict[str, Any]]:
        """
        Get SW360 component by external id

        For now, this only supports searching for package urls.

        First, search for the component purl. If there is no match, search for
        all release purls for this component and verify they all point to the
        same component.

        :param ext_id_name: type of external id ("package-url", "npm-id", etc.)
        :type ext_id_name: string
        :param ext_id_value: external id
        :type ext_id_value: string
        """

        if ext_id_name != "package-url":
            return []

        if not ext_id_value:
            return []

        purl = packageurl.PackageURL.from_string(ext_id_value)
        self.build_purl_cache((purl.type,))

        purl_entries = self.purl_cache.get_by_name(purl)
        if purl_entries:
            if None in purl_entries:
                # component entries
                return purl_entries[None]
            else:
                # release entries
                component_candidates = []
                for version, purl_list in purl_entries.items():
                    for purl_entry in purl_list:
                        release = self.client.get_release_by_url(purl_entry["href"])
                        if not release:
                            continue

                        c1 = release["_links"].get("sw360:component", None)
                        if not c1 or "href" not in c1:
                            continue

                        component_candidates.append({
                            "href": c1["href"],
                            "purl": purl_entry["purl"],
                            "release_href": purl_entry["href"]
                        })
                return component_candidates
        return []

    def search_component_by_external_id(self, ext_id_name: str, ext_id_value: str) -> Optional[str]:
        """Get exactly one SW360 component by external id
        :param ext_id_name: type of external id ("package-url", "npm-id", etc.)
        :type ext_id_name: str
        :param ext_id_value: external id
        :type ext_id_value: str
        :return: href of the component or empty string if not found
        """
        component_candidates = self.search_components_by_external_id(ext_id_name, ext_id_value)
        unique_hrefs = {c["href"] for c in component_candidates}

        if len(unique_hrefs) > 1:
            print_yellow("    No unique component match for", ext_id_value + ":")
            for c in component_candidates:
                if "release_href" in c:
                    print_yellow("      Release", self.client.get_id_from_href(c["release_href"]),
                                 "with purl", c["purl"],
                                 "points to component", self.client.get_id_from_href(c["href"]))
                else:
                    print_yellow("      Candidate", self.client.get_id_from_href(c["href"]),
                                 "has purl", c["purl"])
        elif len(unique_hrefs) == 1:
            c = component_candidates[0]
            if "release_href" in component_candidates[0]:
                print_green("    Found component", self.client.get_id_from_href(c["href"]), "via purl", c["purl"],
                            "for release", self.client.get_id_from_href(c["release_href"]))
            else:
                print_green("   Found component", self.client.get_id_from_href(c["href"]), "via purl", c["purl"])

            return component_candidates[0]["href"]

        # no match in purl cache
        return None

    def search_component_and_release(self, ext_id_value: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get SW360 component and release at once by external id
        :param ext_id_value: external id
        :return: tuple of SW360 release and component URL
        """
        component = release = None
        release = self.search_release_by_external_id("package-url", ext_id_value)
        component = self.search_component_by_external_id("package-url", ext_id_value)
        return component, release
