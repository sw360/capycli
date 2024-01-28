# -------------------------------------------------------------------------------
# (c) 2022-23 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com
#
# SPDX-FileCopyrightText: (c) 2022-2023 Siemens
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------
import unittest

from packageurl import PackageURL

from capycli.common.purl_utils import PurlUtils


class TestPurlUtils(unittest.TestCase):
    def test_get_purls_from_external_id_invalid_entries(self) -> None:

        # no purl
        data = None
        actual = PurlUtils.parse_purls_from_external_id(data)
        self.assertListEqual(actual, [])

        # purl is a number
        data = 123
        actual = PurlUtils.parse_purls_from_external_id(data)
        self.assertListEqual(actual, [])

    def test_get_purls_from_external_id_single_string(self) -> None:

        # single valid purl
        data = "pkg:github/macchrome/winchrome@v80.0.3987.149-r989-Win64"
        actual = PurlUtils.parse_purls_from_external_id(data)
        self.assertIsNotNone(actual)
        self.assertTrue(isinstance(actual, list))
        self.assertEqual(len(actual), 1)
        self.assertEqual(actual[0], "pkg:github/macchrome/winchrome@v80.0.3987.149-r989-Win64")

    def test_get_purls_from_external_id_strings(self) -> None:

        # valid purls separated by blank
        purl1 = "pkg:github/chrome/chrome@v80"
        purl2 = "pkg:github/chrome/chrome@v99"
        data = purl1 + " " + purl2
        actual = PurlUtils.parse_purls_from_external_id(data)
        self.assertIsNotNone(actual)
        self.assertTrue(isinstance(actual, list))
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual[0], purl1)
        self.assertEqual(actual[1], purl2)

    def test_get_purls_from_external_id_list(self) -> None:

        # two valid purls as list
        purl1 = "pkg:github/chrome/chrome@v80"
        purl2 = "pkg:github/chrome/chrome@v99"
        actual = PurlUtils.parse_purls_from_external_id([purl1, purl2])
        self.assertIsNotNone(actual)
        self.assertTrue(isinstance(actual, list))
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual[0], purl1)
        self.assertEqual(actual[1], purl2)

    def test_get_purls_from_external_id_list_as_string(self) -> None:

        # two valid purls as list
        purl1 = "pkg:github/chrome/chrome@v80"
        purl2 = "pkg:github/chrome/chrome@v99"
        datalist = '["' + purl1 + '", "' + purl2 + '"]'
        actual = PurlUtils.parse_purls_from_external_id(datalist)
        self.assertIsNotNone(actual)
        self.assertTrue(isinstance(actual, list))
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual[0], purl1)
        self.assertEqual(actual[1], purl2)

    def test_get_purls_from_external_id_list_with_invalid_entries(self) -> None:

        # two valid purls as list
        purl1 = "pkg:github/chrome/chrome"
        purl_invalid = "invaldi:github/chrome/chromium"
        purl2 = "pkg:github/chrome/chromium"

        sw360_object = {
            "externalIds": {
                "package-url": PurlUtils.convert_purls_to_external_id([purl1, purl_invalid, purl2])
            },
            "_links": {
                "self": {
                    "href": "123",
                }
            }
        }
        actual = PurlUtils.get_purl_list_from_sw360_object(sw360_object)
        self.assertIsNotNone(actual)
        self.assertTrue(isinstance(actual, list))
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual[0], PackageURL.from_string(purl1))
        self.assertEqual(actual[1], PackageURL.from_string(purl2))

    def test_contains(self) -> None:
        input_purl = PackageURL.from_string("pkg:maven/org.springframework.boot/spring-boot-actuator@2.7.1?type=jar")
        search_purl = PackageURL.from_string("pkg:maven/org.springframework.boot/spring-boot-actuator@2.7.1")
        self.assertTrue(PurlUtils.contains([input_purl], search_purl))
