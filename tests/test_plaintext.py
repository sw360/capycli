# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import io
import os

from cyclonedx.model.component import Component

from capycli.bom.legacy import LegacySupport
from capycli.bom.plaintext import PlainTextSupport
from tests.test_base import TestBase


class TestPlainText(TestBase):
    INPUTFILE1 = "plaintext.txt"
    OUTPUTFILE = "test_temp.txt"

    def assert_default_test_bom(self, cx_components: list[Component]) -> None:
        self.assertEqual(4, len(cx_components))

        self.assertEqual("colorama", cx_components[0].name)
        self.assertEqual("0.4.3", cx_components[0].version)

        self.assertEqual("python", cx_components[1].name)
        self.assertEqual("3.8", cx_components[1].version)

        self.assertEqual("tomli", cx_components[2].name)
        self.assertEqual("2.0.1", cx_components[2].version)

        self.assertEqual("wheel", cx_components[3].name)
        self.assertEqual("0.34.2", cx_components[3].version)

    def test_read(self) -> None:
        filename = os.path.join(os.path.dirname(__file__), "fixtures", TestPlainText.INPUTFILE1)
        cx_components = PlainTextSupport.flatlist_to_cdx_components(filename)
        self.assert_default_test_bom(cx_components)

    def test_write_plaintext(self) -> None:
        filename = os.path.join(os.path.dirname(__file__), "fixtures", TestPlainText.INPUTFILE1)
        cx_components = PlainTextSupport.flatlist_to_cdx_components(filename)
        self.assert_default_test_bom(cx_components)

        filename_out = os.path.join(
            os.path.dirname(__file__), "fixtures", TestPlainText.OUTPUTFILE)
        PlainTextSupport.write_cdx_components_as_flatlist(cx_components, filename_out)

        self.assertListEqual(
            list(io.open(filename)),
            list(io.open(filename_out)))

        TestPlainText.delete_file(filename_out)

    def test_write_legacy(self) -> None:
        filename = os.path.join(os.path.dirname(__file__), "fixtures", TestPlainText.INPUTFILE1)
        cx_components = PlainTextSupport.flatlist_to_cdx_components(filename)
        self.assert_default_test_bom(cx_components)

        filename_out = os.path.join(
            os.path.dirname(__file__), "fixtures", TestPlainText.OUTPUTFILE)
        LegacySupport.write_cdx_components_as_legacy(cx_components, filename_out)

        cx_components2 = LegacySupport.legacy_to_cdx_components(filename_out)
        self.assert_default_test_bom(cx_components2)

        TestPlainText.delete_file(filename_out)
