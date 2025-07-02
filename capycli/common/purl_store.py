# -------------------------------------------------------------------------------
# Copyright (c) 2022-23 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from typing import Any, Dict, List, Optional

from packageurl import PackageURL


class PurlStore:
    """
    In memory store from package-url (purl) to object.
    Internal structure:
    cache = {
        <type e.g. maven>: {
            <namespace e.g. ch.qos.logback>: {
                <name e.g. logback-core>: {
                    <version e.g. 1.2.11>:
                        object-to-store,
                    None:
                        component-to-store
                }
            }
        }
    }
    """
    def __init__(self, cache: Optional[Dict] = None):  # type: ignore
        if cache:
            self.purl_cache = cache
        else:
            self.purl_cache = {}

    def __getitem__(self, key: str) -> Any:
        return self.purl_cache[key]

    def __contains__(self, key: str) -> bool:
        return key in self.purl_cache

    def __bool__(self, *args: Any, **kwargs: Any) -> bool:
        """ True if self else False """
        return bool(self.purl_cache)

    def add(self, purl: PackageURL, sw360_href: str) -> List[Dict[str, Any]]:
        # Prepare cache for purl
        pc = self.purl_cache
        for key in (purl.type, purl.namespace, purl.name):
            pc.setdefault(key, {})
            pc = pc[key]

        pc.setdefault(purl.version, [])
        pc[purl.version].append({
            "purl": purl,
            "href": sw360_href
        })
        return pc[purl.version]

    def get_by_namespace(self, purl: PackageURL) -> Optional[Dict]:  # type: ignore
        if (purl.type in self.purl_cache
                and purl.namespace in self.purl_cache[purl.type]):
            return self.purl_cache[purl.type][purl.namespace]

        return None

    def get_by_name(self, purl: PackageURL) -> Optional[Dict]:  # type: ignore
        entries = self.get_by_namespace(purl)
        if entries and purl.name in entries:
            return entries[purl.name]

        return None

    def get_by_version(self, purl: PackageURL) -> List[Dict[str, Any]]:
        """
        Retrieve entries by version from the cache.

        :param purl: The PackageURL object containing type, namespace, name, and version.
        :return: List of entries (dicts with "purl" and "href") matching the version.
        """
        entries = self.get_by_name(purl)
        if entries and purl.version in entries:
            return entries[purl.version]

        return []
