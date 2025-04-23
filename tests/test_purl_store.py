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
from capycli.common.map_result import MapResultByIdQualifiers


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
        for p in (purl1, purl2):
            res = sut.get_by_version(p)
            if res is None:
                self.fail("Expected results to be not None for", p)
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

    def test_get_with_filter_qualifiers(self) -> None:
        sut = PurlStore()

        purl1 = packageurl.PackageURL.from_string("pkg:maven/test/test@1?classifier=sources")
        entry1 = "https://sw360.org/api/releases/123"
        sut.add(purl1, entry1)

        entry1_duplicate = "https://sw360.org/api/releases/124"
        sut.add(purl1, entry1_duplicate)

        purl2 = packageurl.PackageURL.from_string("pkg:maven/test/test@1?classifier=dist&type=zip")
        entry2 = "https://sw360.org/api/releases/456"
        sut.add(purl2, entry2)

        purl3 = packageurl.PackageURL.from_string("pkg:maven/test/test@1")
        entry3 = "https://sw360.org/api/releases/789"
        sut.add(purl3, entry3)

        # For known qualifiers, we should get the full match(es)
        entries = sut.get_by_version(purl1)
        result, entries = sut.filter_by_qualifiers(entries, purl1)
        self.assertEqual(len(entries), 2)
        hrefs = {entry["href"]: entry for entry in entries}
        self.assertIn(entry1, hrefs)
        self.assertEqual(hrefs[entry1]["purl"].qualifiers["classifier"], "sources")
        self.assertIn(entry1_duplicate, hrefs)
        self.assertEqual(hrefs[entry1_duplicate]["purl"].qualifiers["classifier"], "sources")
        assert result == MapResultByIdQualifiers.FULL_MATCH

        entries = sut.get_by_version(purl2)
        result, entries = sut.filter_by_qualifiers(entries, purl2)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["href"], entry2)
        self.assertEqual(entries[0]["purl"].qualifiers["classifier"], "dist")
        assert result == MapResultByIdQualifiers.FULL_MATCH

        # For the same version without qualifiers, we should get all entries
        entries = sut.get_by_version(purl3)
        result, entries = sut.filter_by_qualifiers(entries, purl3)
        self.assertEqual(len(entries), 4)
        hrefs = {entry["href"]: entry for entry in entries}
        self.assertIn(entry1, hrefs)
        self.assertEqual(hrefs[entry1]["purl"].qualifiers["classifier"], "sources")
        self.assertIn(entry2, hrefs)
        self.assertEqual(hrefs[entry2]["purl"].qualifiers["classifier"], "dist")
        self.assertIn(entry3, hrefs)
        self.assertEqual(hrefs[entry3]["purl"].qualifiers, {})
        self.assertIn(entry1_duplicate, hrefs)
        self.assertEqual(hrefs[entry1_duplicate]["purl"].qualifiers["classifier"], "sources")
        assert result == MapResultByIdQualifiers.NO_QUALIFIER_MAPPING

        # If all given qualifiers match, we should get the full match
        purl4 = packageurl.PackageURL.from_string("pkg:maven/test/test@1?classifier=dist")
        entries = sut.get_by_version(purl4)
        result, entries = sut.filter_by_qualifiers(entries, purl4)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["href"], entry2)
        self.assertEqual(entries[0]["purl"].qualifiers["classifier"], "dist")
        assert result == MapResultByIdQualifiers.FULL_MATCH

        # For the same version with an unknown qualifier, we should get all entries
        purl4 = packageurl.PackageURL.from_string("pkg:maven/test/test@1?classifier=x86")
        entries = sut.get_by_version(purl4)
        result, entries = sut.filter_by_qualifiers(entries, purl4)
        self.assertEqual(len(entries), 4)
        assert result == MapResultByIdQualifiers.IGNORED

        # Same if not all qualifiers match
        purl5 = packageurl.PackageURL.from_string("pkg:maven/test/test@1?classifier=dist&type=jar")
        entries = sut.get_by_version(purl5)
        result, entries = sut.filter_by_qualifiers(entries, purl5)
        self.assertEqual(len(entries), 4)
        assert result == MapResultByIdQualifiers.IGNORED
