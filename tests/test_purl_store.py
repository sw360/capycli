# -------------------------------------------------------------------------------
# Copyright (c) 2022-23 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import packageurl

from capycli.common.purl_store import PurlStore
from tests.test_base import TestBase


class TestPurlStore(TestBase):

    def test_add_valid_purl_to_store(self) -> None:
        sut = PurlStore()

        purl = packageurl.PackageURL.from_string("pkg:maven/test/test")
        entry = "https://sw360.org/api/component/123"
        cache_entries = sut.add(purl, entry)
        self.assertEqual(cache_entries[0]["href"], entry)
        self.assertEqual(cache_entries[0]["purl"], purl)
        self.assertEqual(sut.get_by_name(purl), {None: [{"purl": purl, "href": entry}]})

    def test_add_duplicate_component(self) -> None:
        sut = PurlStore()

        purl = packageurl.PackageURL.from_string("pkg:maven/test/test")
        entry1 = "https://sw360.org/api/component/123"
        sut.add(purl, entry1)
        entry2 = "https://sw360.org/api/component/456"
        sut.add(purl, entry2)
        results = sut.get_by_name(purl)
        if results is None:
            self.fail("Expected results to be not None")
        else:
            self.assertEqual(len(results[None]), 2)
            self.assertEqual(results[None][0]["href"], entry1)
            self.assertEqual(results[None][0]["purl"], purl)
            self.assertEqual(results[None][1]["href"], entry2)
            self.assertEqual(results[None][1]["purl"], purl)

    def test_add_duplicate_version(self) -> None:
        sut = PurlStore()

        purl1 = packageurl.PackageURL.from_string("pkg:maven/test/test@1?classifier=sources")
        entry1 = "https://sw360.org/api/releases/123"
        cache_entries = sut.add(purl1, entry1)
        self.assertEqual(cache_entries[0]["href"], entry1)

        purl2 = packageurl.PackageURL.from_string("pkg:maven/test/test@1?classifier=dist")
        entry2 = "https://sw360.org/api/releases/456"
        cache_entries = sut.add(purl2, entry2)
        self.assertEqual(cache_entries[0]["href"], entry1)
        self.assertEqual(cache_entries[0]["purl"].qualifiers["classifier"], "sources")
        self.assertEqual(cache_entries[1]["href"], entry2)
        self.assertEqual(cache_entries[1]["purl"].qualifiers["classifier"], "dist")
        res = sut.get_by_version(purl1)
        if res is None:
            self.fail("Expected results to be not None")
        else:
            self.assertEqual(len(res), 2)

    def test_add_duplicate_qualifiers(self) -> None:
        sut = PurlStore()

        purl = packageurl.PackageURL.from_string("pkg:maven/test/test@1?classifier=sources")
        entry1 = "https://sw360.org/api/releases/123"
        cache_entries = sut.add(purl, entry1)
        entry2 = "https://sw360.org/api/releases/456"
        cache_entries = sut.add(purl, entry2)
        self.assertEqual(cache_entries[0]["href"], entry1)
        self.assertEqual(cache_entries[0]["purl"].qualifiers["classifier"], "sources")
        self.assertEqual(cache_entries[1]["href"], entry2)
        self.assertEqual(cache_entries[1]["purl"].qualifiers["classifier"], "sources")
        res = sut.get_by_version(purl)
        if res is None:
            self.fail("Expected results to be not None")
        else:
            self.assertEqual(len(res), 2)
