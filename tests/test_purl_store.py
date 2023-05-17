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

    def test_add_valid_purl_to_store(self):
        sut = PurlStore()

        purl = packageurl.PackageURL.from_string("pkg:maven/test/test")
        entry = {"name": "test", "version": "1"}
        successful, value = sut.add(purl, entry)
        self.assertTrue(successful)
        self.assertEqual(value, entry)
        self.assertEqual(sut.get_by_name(purl), {None: entry}, msg="Entry shall be {}".format({None: entry}))

    def test_add_duplicate_version_shall_fail(self):
        sut = PurlStore()

        purl = packageurl.PackageURL.from_string("pkg:maven/test/test@1")
        entry1 = {"name": "test", "version": "1", "first": True}
        # Add shall return True for successful and the newly added value
        successful, value = sut.add(purl, entry1)
        self.assertTrue(successful)
        self.assertEqual(value, entry1)
        entry2 = {"name": "test", "version": "1", "first": False}
        # Add shall return False for failed and the current entry in the store
        successful, value = sut.add(purl, entry2)
        self.assertFalse(successful)
        self.assertEqual(value, entry1)
        self.assertEqual(sut.get_by_version(purl), entry1)

    def test_remove_duplicates_shall_remove_unnecessary_entries(self):
        sut = PurlStore()

        purl: packageurl.PackageURL = packageurl.PackageURL.from_string("pkg:maven/test/test@1")
        duplicates: list[tuple[str, str, str, str]] = [(purl.type, purl.namespace, purl.name, purl.version)]
        sut.add(purl, {})

        sut.remove_duplicates(duplicates)
        self.assertFalse(bool(sut.purl_cache), msg="Shall be empty {}".format(sut.purl_cache))

    def test_remove_duplicates_shall_ignore_unknown_entries(self):
        sut = PurlStore()

        purl: packageurl.PackageURL = packageurl.PackageURL.from_string("pkg:maven/test/test@1")
        sut.add(purl, {"test": True})
        duplicates: list[tuple[str, str, str, str]] = [
            (purl.type, purl.namespace, purl.name, "unknown"),
            (purl.type, purl.namespace, "unknown", None),
            (purl.type, "unknown", None, None),
            ("unknown", None, None, None)
        ]
        sut.remove_duplicates(duplicates)
        self.assertTrue(bool(sut.purl_cache))
