# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import json
from typing import NamedTuple

from cyclonedx.model import ExternalReference, ExternalReferenceType, HashAlgorithm, HashType, Property, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component

from capycli import LOG
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, ParserMode, SbomJsonParser

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
            ext_ref = ExternalReference(
                reference_type=ExternalReferenceType.DISTRIBUTION,
                comment=CaPyCliBom.SOURCE_FILE_COMMENT,
                url=XsUri(prop.value))
            prop2 = CycloneDxSupport.get_property(component, "source-file-hash")
            if prop2:
                ext_ref.hashes.add(HashType(
                    algorithm=HashAlgorithm.SHA_1,
                    hash_value=prop2.value))
            component.external_references.add(ext_ref)
            component.properties.remove(prop)

        prop = CycloneDxSupport.get_property(component, "source-file-url")
        if prop:
            ext_ref = ExternalReference(
                reference_type=ExternalReferenceType.DISTRIBUTION,
                comment=CaPyCliBom.SOURCE_URL_COMMENT,
                url=XsUri(prop.value))
            prop2 = CycloneDxSupport.get_property(component, "source-file-hash")
            if prop2:
                ext_ref.hashes.add(HashType(
                    algorithm=HashAlgorithm.SHA_1,
                    hash_value=prop2.value))
            component.external_references.add(ext_ref)
            component.properties.remove(prop)

        prop = CycloneDxSupport.get_property(component, "source-file-hash")
        if prop:
            component.properties.remove(prop)

        prop = CycloneDxSupport.get_property(component, "binary-file-url")
        if prop:
            ext_ref = ExternalReference(
                reference_type=ExternalReferenceType.DISTRIBUTION,
                comment=CaPyCliBom.BINARY_URL_COMMENT,
                url=XsUri(prop.value))
            prop2 = CycloneDxSupport.get_property(component, "binary-file-hash")
            if prop2:
                ext_ref.hashes.add(HashType(
                    algorithm=HashAlgorithm.SHA_1,
                    hash_value=prop2.value))
            component.external_references.add(ext_ref)
            component.properties.remove(prop)

        prop = CycloneDxSupport.get_property(component, "binary-file")
        if prop:
            ext_ref = ExternalReference(
                reference_type=ExternalReferenceType.DISTRIBUTION,
                comment=CaPyCliBom.BINARY_FILE_COMMENT,
                url=XsUri(prop.value))
            prop2 = CycloneDxSupport.get_property(component, "binary-file-hash")
            if prop2:
                ext_ref.hashes.add(HashType(
                    algorithm=HashAlgorithm.SHA_1,
                    hash_value=prop2.value))
            component.external_references.add(ext_ref)
            component.properties.remove(prop)

        prop = CycloneDxSupport.get_property(component, "binary-file-hash")
        if prop:
            component.properties.remove(prop)

        return component

    @classmethod
    def _convert_bom(cls, bom: Bom) -> Bom:
        for component in bom.components:
            component = cls._convert_component(component)

        return bom

    @classmethod
    def read_sbom(cls, inputfile: str) -> Bom:
        LOG.debug(f"Reading from file {inputfile}")
        with open(inputfile) as fin:
            content = json.load(fin)

            parser = SbomJsonParser(content, ParserMode.LEGACY_CX)
            bom = Bom.from_parser(parser=parser)
            LegacyCx._init_mapping()
            bom2 = LegacyCx._convert_bom(bom)

        return bom2
