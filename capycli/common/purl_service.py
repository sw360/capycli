# -------------------------------------------------------------------------------
# Copyright (c) 2022-2023 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com, thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from typing import Any, Dict, List, Optional

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
                        already_in_cache = self.purl_cache.get_by_version(purl)
                        _, already_in_cache = PurlStore.filter_by_qualifiers(
                            already_in_cache, purl)
                        for e in already_in_cache:
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

    def search_releases_by_purl(self, purl: packageurl.PackageURL, qualifier_match: bool = False) -> Dict[str, Any]:
        """Get SW360 releases by Package URL using the purl cache

        :return: tuple of release hrefs and list of notes about mapping
        """
        self.build_purl_cache((purl.type,))

        result = self.purl_cache.get_by_version(purl)
        if qualifier_match:
            qualifier_result, result = PurlStore.filter_by_qualifiers(result, purl)
        else:
            qualifier_result = None
        unique_hrefs = {r["href"] for r in result}

        if len(unique_hrefs) > 1:
            print_yellow("    No unique release match for", purl.to_string())
            for r in result:
                print_yellow("      Candidate", self.client.get_id_from_href(r["href"]),
                             "has purl", r["purl"])

        search_result = {
            "hrefs": list(unique_hrefs),
            # can be extended with more details in the future
            "results": [qualifier_result.value] if (qualifier_result and qualifier_result.value) else []
        }
        return search_result

    def search_components_by_purl(self, purl: packageurl.PackageURL) -> List[str]:
        """
        Get SW360 components by Package URL using the purl cache.

        First, search for the component purl. If there is no match, search for
        all release purls for this component and verify they all point to the
        same component.

        :return: list of component urls
        """

        self.build_purl_cache((purl.type,))

        purl_entries = self.purl_cache.get_by_name(purl)
        if purl_entries:
            if None in purl_entries:
                # component entries
                result = purl_entries[None]
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
                result = component_candidates
        else:
            return []

        unique_hrefs = {c["href"] for c in result}

        if len(unique_hrefs) > 1:
            print_yellow("    No unique component match for", purl.to_string() + ":")
            for c in result:
                if "release_href" in c:
                    print_yellow("      Release", self.client.get_id_from_href(c["release_href"]),
                                 "with purl", c["purl"],
                                 "points to component", self.client.get_id_from_href(c["href"]))
                else:
                    print_yellow("      Candidate", self.client.get_id_from_href(c["href"]),
                                 "has purl", c["purl"])
        elif len(unique_hrefs) == 1:
            c = result[0]
            if "release_href" in result[0]:
                print_green("    Found component", self.client.get_id_from_href(c["href"]), "via purl", c["purl"],
                            "for release", self.client.get_id_from_href(c["release_href"]))
            else:
                print_green("   Found component", self.client.get_id_from_href(c["href"]), "via purl", c["purl"])

        return list(unique_hrefs)
