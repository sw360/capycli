# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import io
import os
from typing import List

from cyclonedx.model.component import Component
from sortedcontainers import SortedSet

from capycli.bom.csv import CsvSupport
from tests.test_base import TestBase


class TestCsv(TestBase):
    INPUTFILE1 = "components.csv"
    OUTPUTFILE = "test_temp.csv"

    def assert_default_test_bom(self, cx_components: List[Component]) -> None:
        self.assertEqual(4, len(cx_components))

        self.assertEqual("colorama", cx_components[0].name)
        self.assertEqual("0.4.3", cx_components[0].version)
        self.assertEqual("another description", cx_components[0].description)

        self.assertEqual("python", cx_components[1].name)
        self.assertEqual("3.8", cx_components[1].version)
        self.assertEqual("some description", cx_components[1].description)

        self.assertEqual("tomli", cx_components[2].name)
        self.assertEqual("2.0.1", cx_components[2].version)
        self.assertEqual("", cx_components[2].description)

        self.assertEqual("wheel", cx_components[3].name)
        self.assertEqual("0.34.2", cx_components[3].version)
        self.assertEqual("", cx_components[3].description)

    def test_read(self) -> None:
        filename = os.path.join(os.path.dirname(__file__), "fixtures", TestCsv.INPUTFILE1)
        cx_components = CsvSupport.csv_to_cdx_components(filename)
        self.assert_default_test_bom(cx_components)

    def test_write(self) -> None:
        filename = os.path.join(os.path.dirname(__file__), "fixtures", TestCsv.INPUTFILE1)
        cx_components = CsvSupport.csv_to_cdx_components(filename)
        self.assert_default_test_bom(cx_components)

        filename_out = os.path.join(
            os.path.dirname(__file__), "fixtures", TestCsv.OUTPUTFILE)
        CsvSupport.write_cdx_components_as_csv(SortedSet(cx_components), filename_out)

        self.assertListEqual(
            list(io.open(filename)),
            list(io.open(filename_out)))

        TestCsv.delete_file(filename_out)
