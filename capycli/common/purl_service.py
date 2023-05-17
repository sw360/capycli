# -------------------------------------------------------------------------------
# Copyright (c) 2022-2023 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# ----------

import packageurl
from sw360 import SW360

from capycli.common.print import print_green, print_text, print_yellow
from capycli.common.purl_store import PurlStore
from capycli.common.purl_utils import PurlUtils


class PurlService:
    def __init__(self, client: SW360, cache: dict = None) -> None:
        self.client = client
        self.purl_cache = PurlStore(cache)

    def build_purl_cache(self, purl_types=tuple(), no_warnings: bool = True) -> None:
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
        if len(all_ids) == 0:
            all_ids = self.client.get_releases_by_external_id("package-url")
        else:
            all_ids = all_ids + self.client.get_releases_by_external_id("package-url")
        print_text(" Found", len(all_ids), "total purls")

        duplicates = []
        for entry in all_ids:
            for purl_string in PurlUtils.parse_purls_from_external_id(entry["externalIds"]["package-url"]):
                try:
                    purl = packageurl.PackageURL.from_string(purl_string)
                    if purl_types and purl.type not in purl_types:
                        continue
                    successful, value = self.purl_cache.add(purl, entry["_links"]["self"]["href"])
                    if not successful and value != entry["_links"]["self"]["href"]:
                        if not no_warnings:
                            print_yellow("-> Multiple entries for purl:", purl)
                            print_yellow(
                                self.client.url +
                                "group/guest/components/-/component/release/detailRelease/" +
                                self.client.get_id_from_href(value))
                            print_yellow(
                                self.client.url +
                                "group/guest/components/-/component/release/detailRelease/" +
                                self.client.get_id_from_href(entry["_links"]["self"]["href"]))
                        duplicates.append(
                            (purl.type, purl.namespace, purl.name, purl.version))
                except ValueError:
                    if not no_warnings:
                        print_yellow("-> Ignoring invalid purl entry in", entry["_links"]["self"]["href"])
                        print_yellow(purl_string)

        self.purl_cache.remove_duplicates(duplicates)

    def search_release_by_external_id(self, ext_id_name: str, ext_id_value: str):
        """Get SW360 release by external id

        For now, this only supports searching for package urls.

        :param ext_id_name: type of external id ("package-url", "npm-id", etc.)
        :type ext_id_name: string
        :param ext_id_value: external id
        :type ext_id_value: string
        """
        if ext_id_name != "package-url":
            return None

        if not ext_id_value:
            return None

        purl = packageurl.PackageURL.from_string(ext_id_value)
        self.build_purl_cache((purl.type,))

        return self.purl_cache.get_by_version(purl)

    def search_component_by_external_id(self, ext_id_name: str, ext_id_value: str):
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
            return None

        if not ext_id_value:
            return None

        purl = packageurl.PackageURL.from_string(ext_id_value)
        self.build_purl_cache((purl.type,))

        purl_entries = self.purl_cache.get_by_name(purl)
        if purl_entries:
            if None in purl_entries:
                # component entry
                comp = purl_entries[None]
                print_green("    Found component", comp.split("/")[-1], "via purl")
                return comp
            else:
                # release entries
                component_candidates = {}
                for version, purl_entry in purl_entries.items():
                    release = self.client.get_release_by_url(purl_entry)
                    c1 = release["_links"].get("sw360:component", None)
                    if not c1:
                        continue

                    if "href" not in c1:
                        continue

                    component = release["_links"]["sw360:component"]["href"]
                    component_candidates[component] = version
                if len(component_candidates) > 1:
                    print_yellow("    Releases purls point to different components:", component_candidates)
                    return None
                elif len(component_candidates) == 1:
                    component = list(component_candidates.keys())[0]
                    print_green(
                        "    Found component", component.split("/")[-1],
                        "via purl for release",
                        component_candidates[component])
                    return list(component_candidates.keys())[0]
        # no match in purl cache
        return None

    def search_component_and_release(self, ext_id_value: str):
        """
        Get SW360 component and release at once by external id
        :param ext_id_value: external id
        :return: tuple of SW360 release and component URL
        """
        component = release = None
        release = self.search_release_by_external_id("package-url", ext_id_value)
        component = self.search_component_by_external_id("package-url", ext_id_value)
        return component, release
