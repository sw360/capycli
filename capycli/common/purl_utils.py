# -------------------------------------------------------------------------------
# Copyright (c) 2022-23 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import json
from typing import Any, Dict

import packageurl
from colorama import Fore, Style


class PurlUtils:
    """
    Package URL utilities
    """
    @staticmethod
    def get_purl_list_from_sw360_object(sw360_object: Dict) -> list:  # type: ignore
        """
        Parse SW360 object to get the list of package URL's
        :param sw360_object: sw360 object component/release
        :return: list of package URL's
        """
        sw360_purl = sw360_object.get("externalIds", {}).get("package-url", "")

        purls = []
        for purl_str in PurlUtils.parse_purls_from_external_id(sw360_purl):
            try:
                purl = packageurl.PackageURL.from_string(purl_str)
                purls.append(purl)
            except ValueError:

                print(Fore.LIGHTYELLOW_EX
                      + "-> Ignoring invalid purl entry in", sw360_object["_links"]["self"]["href"])
                print(purl_str)
                print(Style.RESET_ALL)

        return purls

    @staticmethod
    def parse_purls_from_external_id(purl_entries: Any) -> list:  # type: ignore
        """Parse package-url list as strings from SW360 external id"""
        if isinstance(purl_entries, list):
            return purl_entries

        if isinstance(purl_entries, str):
            if purl_entries.startswith("["):
                # arrghh, the JSON array has been returned as a single string
                new_purl = json.loads(purl_entries)
                return PurlUtils.parse_purls_from_external_id(new_purl)
            return purl_entries.split()

        return []

    @staticmethod
    def contains(purls: list, search_purl: packageurl.PackageURL,  # type: ignore
                 compare_qualifiers: bool = False) -> bool:
        """
        Search the given PackageURL in the provided list
        Important: The matching is only based on type, namespace, name and version.
        If `compare_qualifiers` is set, the qualifiers present in the search_purl are also checked.
        We do not consider other qualifiers and subpath.
        """
        for entry in purls:
            if (entry.type == search_purl.type
                    and entry.namespace == search_purl.namespace
                    and entry.name == search_purl.name
                    and entry.version == search_purl.version):
                if compare_qualifiers and isinstance(search_purl.qualifiers, dict):
                    for key, value in search_purl.qualifiers.items():
                        if key not in entry.qualifiers or entry.qualifiers[key] != value:
                            return False
                return True
        return False

    @staticmethod
    def convert_purls_to_external_id(purl_entries: list) -> str:  # type: ignore
        """Convert list of package-url to SW360 external id format"""
        if len(purl_entries) == 1:
            return purl_entries[0]
        else:
            return "[\"" + "\",\"".join(purl_entries) + "\"]"

    @staticmethod
    def component_purl_from_release_purl(component_purl: packageurl.PackageURL) -> str:
        purl = packageurl.PackageURL(type=component_purl.type, namespace=component_purl.namespace,
                                     name=component_purl.name, version=None,
                                     qualifiers=component_purl.qualifiers)
        return purl.to_string()
