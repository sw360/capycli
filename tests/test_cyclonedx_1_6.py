# -------------------------------------------------------------------------------
# Copyright (c) 2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import json
import os
from typing import List

from cyclonedx.model import ExternalReference, ExternalReferenceType, HashAlgorithm, HashType, Property, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.bom_ref import BomRef
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.model.definition import Standard
from packageurl import PackageURL

from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomCreator
from tests.test_base import TestBasePytest


class TestCycloneDx_1_6(TestBasePytest):
    OUTPUTFILE = "output.json"
    INPUTFILE1 = "sbom.siemens.cdx_1.6.json"
    INPUTFILE2 = "sbom.siemens.cdx_1_4.json"

    def test_read_cdx_1_6_sbom(self) -> None:
        inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestCycloneDx_1_6.INPUTFILE1)
        sbom: Bom = CaPyCliBom.read_sbom(inputfile)

        assert sbom is not None
        assert sbom.version == 1
        assert sbom.components is not None
        assert len(sbom.components) == 66

        assert sbom.definitions is not None
        assert sbom.definitions.standards is not None
        assert len(sbom.definitions.standards) == 1
        std: Standard = sbom.definitions.standards[0]
        assert std.name == "Standard BOM"
        assert std.bom_ref.value == "standard-bom"
        assert std.description == "The Standard for Software Bills of Materials in Siemens"
        assert std.owner == "Siemens AG"
        assert std.version == "3.0.0"
        assert len(std.external_references) == 1
        extref: ExternalReference = std.external_references[0]
        assert extref.type == ExternalReferenceType.WEBSITE
        assert extref.url.uri == "https://sbom.siemens.io/"

        assert sbom.metadata is not None
        assert sbom.metadata.licenses is not None
        assert len(sbom.metadata.licenses) == 1
        lic = sbom.metadata.licenses[0]
        assert lic.id == "CC0-1.0"

        assert sbom.metadata.properties is not None
        assert len(sbom.metadata.properties) == 1
        prop: Property = sbom.metadata.properties[0]
        assert prop.name == "siemens:profile"
        assert prop.value == "clearing"

        assert sbom.metadata.timestamp is not None

        assert sbom.metadata.tools is not None
        assert sbom.metadata.tools.components is not None
        assert len(sbom.metadata.tools.components) == 1
        tc1: Component = sbom.metadata.tools.components[0]
        assert tc1.name == "CaPyCLI"
        assert tc1.type == ComponentType.APPLICATION
        assert tc1.version == "2.5.1"
        assert tc1.external_references is not None
        assert len(tc1.external_references) == 1
        extref = tc1.external_references[0]
        assert extref.type == ExternalReferenceType.WEBSITE
        assert extref.url.uri == "https://github.com/sw360/capycli"
        assert tc1.supplier is not None
        assert tc1.supplier.name == "Siemens AG"

    def test_read_cdx_1_4_sbom(self) -> None:
        inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestCycloneDx_1_6.INPUTFILE2)
        sbom: Bom = CaPyCliBom.read_sbom(inputfile)

        assert sbom is not None
        assert sbom.version == 1
        assert sbom.components is not None
        assert len(sbom.components) == 4

        assert sbom.definitions is None

        assert sbom.metadata is not None
        assert sbom.metadata.timestamp is not None

        assert sbom.metadata.tools is not None
        assert sbom.metadata.tools.components is not None
        assert len(sbom.metadata.tools.components) == 0

        assert sbom.metadata.tools.tools is not None
        assert len(sbom.metadata.tools.tools) == 2
        tc1: Component = sbom.metadata.tools.tools[0]
        assert tc1.name == "SBomFromSW360.Net"
        assert tc1.version == "0.6.0.0"
        assert tc1.external_references is not None
        assert len(tc1.external_references) == 1
        extref = tc1.external_references[0]
        assert extref.type == ExternalReferenceType.WEBSITE
        assert extref.url.uri == "https://code.siemens.com/sbom/tools/sbomfromsw360.net"
        assert tc1.vendor == "Siemens AG"  # type: ignore

        std: Component = sbom.metadata.tools.tools[1]
        assert std.name == "standard-bom"
        assert std.version == "2.0.0"
        assert len(std.external_references) == 1
        extref: ExternalReference = std.external_references[0]
        assert extref.type == ExternalReferenceType.WEBSITE
        assert extref.url.uri == "https://code.siemens.com/scpautomation/standard-bom"

        c1: Component = sbom.components[0]
        assert c1.name == "colorama"
        assert c1.licenses[0].name == "BSD-2-Clause"
        assert len(c1.properties) == 4
        prop: Property = c1.properties[1]
        assert prop.name == "capycli:projectClearingState"
        assert prop.value == "PHASEOUT"

    def test_write_cdx_1_6_sbom(self) -> None:
        purl = PackageURL(type="pypi", name="certifi", version="2024.8.30")
        br = BomRef(purl.to_string())
        component = Component(
            name="certifi",
            version="2024.8.30",
            purl=purl,
            type=ComponentType.LIBRARY,
            description="Python package for providing Mozilla's CA Bundle.",
            properties=[Property(name="siemens:primaryLanguage", value="Python")],
            external_references=[
                 ExternalReference(
                     type=ExternalReferenceType.DISTRIBUTION,
                     url=XsUri("https://pypi.org/project/certifi/2024.8.30"),
                     comment="binary (download location)",
                     hashes=[HashType(
                         alg=HashAlgorithm.SHA_256,
                         content="bec941d2aa8195e248a60b31ff9f0558284cf01a52591ceda73ea9afffd69fd9")]
                 )
            ],
            bom_ref=br)
        CycloneDxSupport.set_property(component, CycloneDxSupport.CDX_PROP_SW360ID, "0815")
        CycloneDxSupport.set_property(component, CycloneDxSupport.CDX_PROP_SW360_URL, "https:/sw360/xyz")
        components: List[Component] = []
        components.append(component)

        creator = SbomCreator()
        sbom = creator.create(components, addlicense=True, addprofile=True, addtools=True,
                              name="unit-test", version="9.8.7", description="test case")
        self.delete_file(self.OUTPUTFILE)
        CaPyCliBom.write_sbom(sbom, self.OUTPUTFILE)

        assert os.path.isfile(self.OUTPUTFILE)
        # load as plain JSON file
        with open(self.OUTPUTFILE, encoding="utf-8") as fin:
            data = json.load(fin)

        assert data is not None
        assert "components" in data
        assert "definitions" in data
        assert "metadata" in data
        assert "serialNumber" in data
        assert "bomFormat" in data
        assert "specVersion" in data

        assert data["specVersion"] == "1.6"
        assert data["bomFormat"] == "CycloneDX"

        assert "component" in data["metadata"]
        assert "licenses" in data["metadata"]
        assert "properties" in data["metadata"]
        assert "tools" in data["metadata"]

        assert "components" in data["metadata"]["tools"]
        assert "CaPyCLI" in data["metadata"]["tools"]["components"][0]["name"]

        assert "standards" in data["definitions"]
        assert "Standard BOM" in data["definitions"]["standards"][0]["name"]
        assert "3.0.0" in data["definitions"]["standards"][0]["version"]

        self.delete_file(self.OUTPUTFILE)


if __name__ == "__main__":
    APP = TestCycloneDx_1_6()
    APP.test_read_cdx_1_4_sbom()
