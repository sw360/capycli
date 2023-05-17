# -------------------------------------------------------------------------------
# Copyright (c) 2022-23 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------
import json

import packageurl
from colorama import Fore, Style


class PurlUtils:
    """
    Package URL utilities
    """
    @staticmethod
    def get_purl_list_from_sw360_object(sw360_object: dict) -> list:
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
    def parse_purls_from_external_id(purl_entries: any) -> list:
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
    def contains(purls: list, search_purl: packageurl.PackageURL) -> bool:
        """
        Search the given PackageURL in the provided list
        Important: The matching is only based on type, namespace, name and version.
        We do not consider qualifiers and subpath.
        """
        for entry in purls:
            if (entry.type == search_purl.type
                    and entry.namespace == search_purl.namespace
                    and entry.name == search_purl.name
                    and entry.version == search_purl.version):
                return True
        return False

    @staticmethod
    def convert_purls_to_external_id(purl_entries: list) -> str:
        """Convert list of package-url to SW360 external id format"""
        if len(purl_entries) == 1:
            return purl_entries[0]
        else:
            return "[\"" + "\",\"".join(purl_entries) + "\"]"

    @staticmethod
    def component_purl_from_release_purl(component_purl):
        purl = packageurl.PackageURL.from_string(component_purl)
        purl = packageurl.PackageURL(type=purl.type, namespace=purl.namespace,
                                     name=purl.name, version=None,
                                     qualifiers=purl.qualifiers)
        return purl.to_string()
