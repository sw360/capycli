# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

from cyclonedx.model import XsUri
from cyclonedx.model.bom_ref import BomRef
from sortedcontainers import SortedSet

from capycli.bom.legacy_cx import LegacyCx
from capycli.common.capycli_bom_support import CycloneDxSupport
from tests.test_base import TestBase


class TestLegacyCx(TestBase):
    INPUTFILE1 = "legacy-cx.json"
    OUTPUTFILE = "sbom.json"

    def assert_components(self, cx_components: SortedSet) -> None:
        self.assertEqual(4, len(cx_components))

        self.assertEqual("colorama", cx_components[0].name)
        self.assertEqual("0.4.3", cx_components[0].version)
        self.assertEqual("pkg:pypi/colorama@0.4.3", cx_components[0].purl.to_string())
        self.assertEqual(BomRef("pkg:pypi/colorama@0.4.3"), cx_components[0].bom_ref)

        # we MUST NOT find this property
        prop = CycloneDxSupport.get_property(cx_components[0], "sw360-id")
        self.assertTrue(prop is None, "Property must not exist!")
        prop = CycloneDxSupport.get_property(cx_components[0], CycloneDxSupport.CDX_PROP_SW360ID)
        self.assertTrue(prop is not None, "Property must exist!")
        self.assertEqual("44ce6d4c8b1b84baa450f29e53001702",
                         CycloneDxSupport.get_property_value(cx_components[0], CycloneDxSupport.CDX_PROP_SW360ID))
        self.assertEqual("SOURCE", CycloneDxSupport.get_property_value(
            cx_components[0], CycloneDxSupport.CDX_PROP_SRC_FILE_TYPE))
        self.assertEqual("James Bond", CycloneDxSupport.get_property_value(
            cx_components[0], CycloneDxSupport.CDX_PROP_SRC_FILE_COMMENT))
        self.assertEqual(XsUri("colorama-0.4.3.tar.gz"), CycloneDxSupport.get_ext_ref_source_file(
            cx_components[0]))

        self.assertEqual("python", cx_components[1].name)
        self.assertEqual("3.8", cx_components[1].version)
        self.assertEqual("pkg:pypi/python@3.8", cx_components[1].purl.to_string())
        self.assertEqual(BomRef("pkg:pypi/python@3.8"), cx_components[1].bom_ref)

        self.assertEqual("tomli", cx_components[2].name)
        self.assertEqual("2.0.1", cx_components[2].version)
        self.assertEqual("pkg:pypi/tomli@2.0.1", cx_components[2].purl.to_string())
        self.assertEqual(BomRef("pkg:pypi/tomli@2.0.1"), cx_components[2].bom_ref)

        self.assertEqual("wheel", cx_components[3].name)
        self.assertEqual("0.34.2", cx_components[3].version)
        self.assertEqual("pkg:pypi/wheel@0.34.2", cx_components[3].purl.to_string())
        self.assertEqual(BomRef("pkg:pypi/wheel@0.34.2"), cx_components[3].bom_ref)

    def test_read(self) -> None:
        filename = os.path.join(os.path.dirname(__file__), "fixtures", TestLegacyCx.INPUTFILE1)
        sbom = LegacyCx.read_sbom(filename)
        self.assert_components(sbom.components)


if __name__ == '__main__':
    APP = TestLegacyCx()
    APP.test_read()
