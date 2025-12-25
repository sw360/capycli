# -------------------------------------------------------------------------------
# Copyright (c) 2023-2025 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import json
from typing import List, NamedTuple

from cyclonedx.model import ExternalReference, ExternalReferenceType, HashAlgorithm, HashType, Property, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component

from capycli import LOG
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport

# ------------------------------------------------------------
# Expected File Format
#
# A CycloneDX JSON file with a list of component objects.
# The components may have properties with the following names:
# * language
# * sw360-id
# * source-url ????????
# * source-file
# * source-file-url
# * source-file-hash
# * source-file-type
# * source-file-comment
# * binary-file
# * binary-file-url
# * binary-file-hash


class LegacyCx(CaPyCliBom):
    """
    Support for old CaPyCLI CycloneDX format.
    """
    class Mapping(NamedTuple):
        legacy: str
        capycli: str
    replacements = [Mapping]

    @classmethod
    def _init_mapping(cls) -> None:
        LegacyCx.replacements.append(
            LegacyCx.Mapping("sw360-id", CycloneDxSupport.CDX_PROP_SW360ID))  # type: ignore
        LegacyCx.replacements.append(
            LegacyCx.Mapping("source-file-type", CycloneDxSupport.CDX_PROP_SRC_FILE_TYPE))  # type: ignore
        LegacyCx.replacements.append(
            LegacyCx.Mapping("source-file-comment", CycloneDxSupport.CDX_PROP_SRC_FILE_COMMENT))  # type: ignore
        LegacyCx.replacements.append(
            LegacyCx.Mapping("language", CycloneDxSupport.CDX_PROP_LANGUAGE))  # type: ignore

    @classmethod
    def _convert_component(cls, component: Component) -> Component:
        for r in LegacyCx.replacements:
            prop = CycloneDxSupport.get_property(component, r.legacy)
            if prop:
                component.properties.add(Property(
                    name=r.capycli, value=prop.value))
                component.properties.remove(prop)

        # extra handling
        prop = CycloneDxSupport.get_property(component, "source-file")
        if prop:
            file_uri = prop.value
            if not file_uri.startswith("file://"):
                file_uri = "file:///" + file_uri
            ext_ref = ExternalReference(
                type=ExternalReferenceType.DISTRIBUTION,
                comment=CaPyCliBom.SOURCE_FILE_COMMENT,
                url=XsUri(file_uri))
            prop2 = CycloneDxSupport.get_property(component, "source-file-hash")
            if prop2:
                ext_ref.hashes.add(HashType(
                    alg=HashAlgorithm.SHA_1,
                    content=prop2.value))
            component.external_references.add(ext_ref)
            component.properties.remove(prop)

        prop = CycloneDxSupport.get_property(component, "source-file-url")
        if prop:
            file_uri = prop.value
            if not file_uri.startswith("file://"):
                file_uri = "file:///" + file_uri
            ext_ref = ExternalReference(
                type=ExternalReferenceType.DISTRIBUTION,
                comment=CaPyCliBom.SOURCE_URL_COMMENT,
                url=XsUri(file_uri))
            prop2 = CycloneDxSupport.get_property(component, "source-file-hash")
            if prop2:
                ext_ref.hashes.add(HashType(
                    alg=HashAlgorithm.SHA_1,
                    content=prop2.value))
            component.external_references.add(ext_ref)
            component.properties.remove(prop)

        prop = CycloneDxSupport.get_property(component, "source-file-hash")
        if prop:
            component.properties.remove(prop)

        prop = CycloneDxSupport.get_property(component, "binary-file-url")
        if prop:
            ext_ref = ExternalReference(
                type=ExternalReferenceType.DISTRIBUTION,
                comment=CaPyCliBom.BINARY_URL_COMMENT,
                url=XsUri(prop.value))
            prop2 = CycloneDxSupport.get_property(component, "binary-file-hash")
            if prop2:
                ext_ref.hashes.add(HashType(
                    alg=HashAlgorithm.SHA_1,
                    content=prop2.value))
            component.external_references.add(ext_ref)
            component.properties.remove(prop)

        prop = CycloneDxSupport.get_property(component, "binary-file")
        if prop:
            file_uri = prop.value
            if not file_uri.startswith("file://"):
                file_uri = "file:///" + file_uri
            ext_ref = ExternalReference(
                type=ExternalReferenceType.DISTRIBUTION,
                comment=CaPyCliBom.BINARY_FILE_COMMENT,
                url=XsUri(file_uri))
            prop2 = CycloneDxSupport.get_property(component, "binary-file-hash")
            if prop2:
                ext_ref.hashes.add(HashType(
                    alg=HashAlgorithm.SHA_1,
                    content=prop2.value))
            component.external_references.add(ext_ref)
            component.properties.remove(prop)

        prop = CycloneDxSupport.get_property(component, "binary-file-hash")
        if prop:
            component.properties.remove(prop)

        return component

    @classmethod
    def _convert_bom(cls, bom: Bom) -> Bom:
        new_components: List[Component] = []
        for component in bom.components:
            new_component = cls._convert_component(component)
            new_components.append(new_component)

        bom.components.clear()
        bom.dependencies.clear()
        for component in new_components:
            bom.components.add(component)
            if bom.metadata.component:
                bom.register_dependency(bom.metadata.component, [component])

        return bom

    @classmethod
    def read_sbom(cls, inputfile: str) -> Bom:
        LOG.debug(f"Reading from file {inputfile}")
        with open(inputfile) as fin:
            string_content = fin.read()

        # the only difference between Legacy CX and real CycloneDX is,
        # that properties have a "key" field instead of a "name" filed.
        # => we just replace those and then we can process it like
        # normal CycloneDX data.
        fixed = string_content.replace('"key"', '"name"')

        content = json.loads(fixed)
        bom: Bom = Bom.from_json(content)  # type: ignore
        LegacyCx._init_mapping()
        LegacyCx._convert_bom(bom)

        return bom
