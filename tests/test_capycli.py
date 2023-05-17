# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

from cyclonedx.model.bom_ref import BomRef
from cyclonedx.model.component import Component

from capycli.common.capycli_bom_support import CaPyCliBom, SbomCreator, SbomWriter
from tests.test_base import TestBase


class TestCaPyCli(TestBase):
    INPUTFILE1 = "sbom.cyclonedx.simple.json"
    INPUTFILE2 = "capycli_extra.json"
    OUTPUTFILE = "sbom.json"

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

    def assert_components(self, cx_components: list[Component]) -> None:
        self.assertEqual(4, len(cx_components))

        self.assertEqual("colorama", cx_components[0].name)
        self.assertEqual("0.4.3", cx_components[0].version)
        self.assertEqual("pkg:pypi/colorama@0.4.3", cx_components[0].purl)
        self.assertEqual(BomRef("pkg:pypi/colorama@0.4.3"), cx_components[0].bom_ref)

        self.assertEqual("python", cx_components[1].name)
        self.assertEqual("3.8", cx_components[1].version)
        self.assertEqual("pkg:pypi/python@3.8", cx_components[1].purl)
        self.assertEqual(BomRef("pkg:pypi/python@3.8"), cx_components[1].bom_ref)

        self.assertEqual("tomli", cx_components[2].name)
        self.assertEqual("2.0.1", cx_components[2].version)
        self.assertEqual("pkg:pypi/tomli@2.0.1", cx_components[2].purl)
        self.assertEqual(BomRef("pkg:pypi/tomli@2.0.1"), cx_components[2].bom_ref)

        self.assertEqual("wheel", cx_components[3].name)
        self.assertEqual("0.34.2", cx_components[3].version)
        self.assertEqual("pkg:pypi/wheel@0.34.2", cx_components[3].purl)
        self.assertEqual(BomRef("pkg:pypi/wheel@0.34.2"), cx_components[3].bom_ref)

    def test_read(self) -> None:
        filename = os.path.join(os.path.dirname(__file__), "fixtures", TestCaPyCli.INPUTFILE1)
        sbom = CaPyCliBom.read_sbom(filename)
        self.assert_default_test_bom(sbom.components)

    def test_read_extra(self) -> None:
        filename = os.path.join(os.path.dirname(__file__), "fixtures", TestCaPyCli.INPUTFILE2)
        sbom = CaPyCliBom.read_sbom(filename)

        self.assertEqual("colorama", sbom.components[0].name)
        self.assertEqual("0.4.3", sbom.components[0].version)
        self.assertEqual("pkg:pypi/colorama@0.4.3", sbom.components[0].purl)
        self.assertEqual(BomRef("pkg:pypi/colorama@0.4.3"), sbom.components[0].bom_ref)

    def test_write_simple(self) -> None:
        filename = os.path.join(os.path.dirname(__file__), "fixtures", TestCaPyCli.INPUTFILE1)
        sbom = CaPyCliBom.read_sbom(filename)
        self.assert_components(sbom.components)

        filename_out = os.path.join(
            os.path.dirname(__file__), "fixtures", TestCaPyCli.OUTPUTFILE)
        CaPyCliBom.write_sbom(sbom, filename_out)

        sbom2 = CaPyCliBom.read_sbom(filename_out)
        self.assert_components(sbom2.components)

        TestCaPyCli.delete_file(filename_out)

    def test_write_simple_bom(self) -> None:
        # create BOM
        bom = []
        comp = Component(name="test1", version="99.9")
        bom.append(comp)

        creator = SbomCreator()
        sbom = creator.create(bom, addlicense=True, addprofile=True, addtools=True)
        filename_out = os.path.join(
            os.path.dirname(__file__), "fixtures", TestCaPyCli.OUTPUTFILE)
        SbomWriter.write_to_json(sbom, filename_out, pretty_print=False)

        sbom2 = CaPyCliBom.read_sbom(filename_out)
        self.assertEqual("test1", sbom2.components[0].name)
        self.assertEqual("99.9", sbom2.components[0].version)

        TestCaPyCli.delete_file(filename_out)

    def test_write_simple_bom2(self) -> None:
        # create BOM
        bom = []
        comp = Component(name="test1", version="99.9")
        bom.append(comp)

        filename_out = os.path.join(
            os.path.dirname(__file__), "fixtures", TestCaPyCli.OUTPUTFILE)
        CaPyCliBom.write_simple_sbom(bom, filename_out)

        sbom2 = CaPyCliBom.read_sbom(filename_out)
        self.assertEqual("test1", sbom2.components[0].name)
        self.assertEqual("99.9", sbom2.components[0].version)

        TestCaPyCli.delete_file(filename_out)
