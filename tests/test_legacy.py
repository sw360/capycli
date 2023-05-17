# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

from cyclonedx.model.component import Component

from capycli.bom.legacy import LegacySupport
from capycli.common.capycli_bom_support import CycloneDxSupport
from tests.test_base import TestBase


class TestLegacy(TestBase):
    INPUTFILE1 = "legacy.json"
    INPUTFILE2 = "legacy_extra.json"
    OUTPUTFILE = "test_temp.json"

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
        filename = os.path.join(os.path.dirname(__file__), "fixtures", TestLegacy.INPUTFILE1)
        cx_components = LegacySupport.legacy_to_cdx_components(filename)
        self.assert_default_test_bom(cx_components)

    def test_read_extra(self) -> None:
        filename = os.path.join(os.path.dirname(__file__), "fixtures", TestLegacy.INPUTFILE2)
        cx_components = LegacySupport.legacy_to_cdx_components(filename)

        self.assertEqual("colorama", cx_components[0].name)
        self.assertEqual("0.4.3", cx_components[0].version)
        self.assertEqual("41ce6d4c8b1b84baa450f29e53001702",
                         CycloneDxSupport.get_property_value(cx_components[0], CycloneDxSupport.CDX_PROP_SW360ID))
        self.assertEqual("SRC", CycloneDxSupport.get_property_value(
            cx_components[0], CycloneDxSupport.CDX_PROP_SRC_FILE_TYPE))
        self.assertEqual("Gernot", CycloneDxSupport.get_property_value(
            cx_components[0], CycloneDxSupport.CDX_PROP_SRC_FILE_COMMENT))
        self.assertEqual("d2b15d49c42f482987963e55a6c550d3", CycloneDxSupport.get_property_value(
            cx_components[0], CycloneDxSupport.CDX_PROP_SW360_HREF))
        self.assertEqual("https://sw360.siemens.com/group/guest/projects/-/" +
                         "project/detail/d2b15d49c42f482987963e55a6c550d3",
                         CycloneDxSupport.get_property_value(cx_components[0], CycloneDxSupport.CDX_PROP_SW360_URL))
        self.assertEqual("OPEN", CycloneDxSupport.get_property_value(
            cx_components[0], CycloneDxSupport.CDX_PROP_CLEARING_STATE))
        self.assertEqual("DENIED", CycloneDxSupport.get_property_value(
            cx_components[0], CycloneDxSupport.CDX_PROP_REL_STATE))
        self.assertEqual("PHASEOUT", CycloneDxSupport.get_property_value(
            cx_components[0], CycloneDxSupport.CDX_PROP_PROJ_STATE))

        self.assertEqual("python", cx_components[1].name)
        self.assertEqual("3.8", cx_components[1].version)

    def test_write_legacy(self) -> None:
        filename = os.path.join(os.path.dirname(__file__), "fixtures", TestLegacy.INPUTFILE1)
        cx_components = LegacySupport.legacy_to_cdx_components(filename)
        self.assert_default_test_bom(cx_components)

        filename_out = os.path.join(
            os.path.dirname(__file__), "fixtures", TestLegacy.OUTPUTFILE)
        LegacySupport.write_cdx_components_as_legacy(cx_components, filename_out)

        cx_components2 = LegacySupport.legacy_to_cdx_components(filename_out)
        self.assert_default_test_bom(cx_components2)

        TestLegacy.delete_file(filename_out)
