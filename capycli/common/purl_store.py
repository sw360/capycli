# -------------------------------------------------------------------------------
# Copyright (c) 2022-23 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from typing import Any, Dict, Optional

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
    def __init__(self, cache: Optional[Dict] = None):
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

    def add(self, purl: PackageURL, entry: Any) -> tuple[bool, Any]:
        # Prepare cache for purl
        pc = self.purl_cache
        for key in (purl.type, purl.namespace, purl.name):
            pc.setdefault(key, {})
            pc = pc[key]

        # Version already exists in the store
        if purl.version in pc:
            return False, pc[purl.version]

        pc[purl.version] = entry
        return True, entry

    def get_by_namespace(self, purl: PackageURL) -> Optional[Dict]:
        if (purl.type in self.purl_cache
                and purl.namespace in self.purl_cache[purl.type]):
            return self.purl_cache[purl.type][purl.namespace]

        return None

    def get_by_name(self, purl: PackageURL) -> Optional[Dict]:
        entries = self.get_by_namespace(purl)
        if entries and purl.name in entries:
            return entries[purl.name]

        return None

    def get_by_version(self, purl: PackageURL) -> Optional[Dict]:
        entries = self.get_by_name(purl)
        if entries and purl.version in entries:
            return entries[purl.version]

        return None

    def remove_duplicates(self, duplicates: list) -> None:
        for d in duplicates:
            if d[0] not in self.purl_cache:
                continue
            if d[1] not in self.purl_cache[d[0]]:
                continue
            if d[2] not in self.purl_cache[d[0]][d[1]]:
                continue
            if d[3] not in self.purl_cache[d[0]][d[1]][d[2]]:
                continue

            # Remove entry
            del (self.purl_cache[d[0]][d[1]][d[2]][d[3]])

            # Clean up empty entries
            if len(self.purl_cache[d[0]][d[1]][d[2]]) == 0:
                del (self.purl_cache[d[0]][d[1]][d[2]])
            if len(self.purl_cache[d[0]][d[1]]) == 0:
                del (self.purl_cache[d[0]][d[1]])
            if len(self.purl_cache[d[0]]) == 0:
                del (self.purl_cache[d[0]])
