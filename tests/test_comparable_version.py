# -------------------------------------------------------------------------------
# Copyright (c) 2022-23 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------
import unittest

from capycli.common.comparable_version import ComparableVersion


class ComparableVersionTestBase(unittest.TestCase):

    def test_equal_versions(self):
        equal_versions = [("5.3.18", "5.03.18"), ("2.13.2.2", "v2.13.2.2")]
        for v1, v2 in equal_versions:
            with self.subTest():
                self.assertEqual(ComparableVersion(v1), ComparableVersion(v2), "The version should be identical")

    def test_greater_versions(self):
        greater_versions = [("1.0.1", "1.0"), ("5.3.18", "5.3.1"), ("v2.14", "v2.13.2.2"), ("0.5.10.2-5", "0.5.10.2-4")]
        for v1, v2 in greater_versions:
            with self.subTest():
                self.assertGreater(ComparableVersion(v1), ComparableVersion(v2), "The version should be greater")

    def test_handle_special_versions(self):
        special = ["20180813", "1", "12", "30.1.1-jre", "1.0-1", "1.2_conflict", "0.5.10.2-5", "5.3.28+dfsg1-0.5",
                   "10.3+deb10u4", "0~20171227-0.2.", "6.3.0.RELEASE", "6.3.0.CR2", "6.3.0.FINAL", "6.3.0.xyz",
                   "6.3.0.99.88.77"]
        for v in special:
            with self.subTest():
                self.assertIsNotNone(ComparableVersion(v))

    def test_get_major_part(self):
        special = [("1", 1), ("12", 12), ("30.1.1-jre", 30), ("1.0-1", 1), ("0.5.10.2-5", 0)]
        for v in special:
            with self.subTest(msg="major version shall be {} -> {}".format(v[0], v[1])):
                cv: ComparableVersion = ComparableVersion(v[0])
                self.assertIsNotNone(cv)
                self.assertEqual(cv.major, v[1])

    def test_incompatible_versions(self):
        """See issue #132"""
        higher_version = ComparableVersion("1.1.1d-0+deb10u3.debian")
        lower_version = ComparableVersion("1.1.1.d-dev")
        self.assertGreater(higher_version, lower_version, "The version should be greater")
        self.assertEqual(ComparableVersion("bullshit"), ComparableVersion("bullshit"), "The version should be equal")

    def test_fill_version(self):
        """See issue #132"""
        version1 = ComparableVersion("3.28.0")
        version2 = ComparableVersion("3.28")
        self.assertEqual(version1, version2, "The version should be equal")
        self.assertEqual(version2, version1, "The version should be equal")
