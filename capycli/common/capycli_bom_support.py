# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import json
import os
import tempfile
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Optional

from cyclonedx.model import (
    AttachedText,
    ExternalReference,
    ExternalReferenceType,
    HashAlgorithm,
    HashType,
    License,
    LicenseChoice,
    Property,
    Tool,
    XsUri,
)
from cyclonedx.model.bom import Bom, BomMetaData
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.output.json import JsonV1Dot4
from cyclonedx.parser import BaseParser
from dateutil import parser as dateparser
from sortedcontainers import SortedSet  # type: ignore

import capycli.common.script_base
from capycli import LOG
from capycli.common import json_support
from capycli.main.exceptions import CaPyCliException

# -------------------------------------
# Expected File Format
#
# -------------------------------------


class ParserMode(Enum):
    # Siemens Standard BOM
    SBOM = 1
    # Legacy-cx format
    LEGACY_CX = 2


class SbomJsonParser(BaseParser):
    """Parser to read a CycloneDX SBOM from a JSON file."""
    def __init__(self, json_content: dict[str, Any], mode: ParserMode = ParserMode.SBOM):
        super().__init__()
        LOG.debug("Processing CycloneDX data...")
        self.parser_mode = mode
        self.metadata = self.read_metadata(json_content.get("metadata"))
        serial_number = json_content.get("serialNumber", None)
        self.serial_number = uuid.UUID(serial_number) \
            if self.is_valid_serial_number(serial_number) \
            else None
        components = json_content.get("components", None)
        if components:
            for component_entry in components:
                component = self.read_component(component_entry)
                if component:
                    self._components.append(component)
        self.external_references = self.read_external_references(
            json_content.get("externalReferences", None))

        LOG.debug("...done.")

    def get_project(self) -> Component:
        """BasesParser not not (always) return a value for
        self.metadata.component. Therefore we have an extra function."""
        return self.metadata.component  # type: ignore

    def link_dependencies_to_project(self, bom: Bom) -> None:
        if not self.metadata.component:
            return

        for component in self._components:
            bom.metadata.component.dependencies.add(component.bom_ref)

    def get_tools(self) -> list[Tool]:
        """Get the list of tools read by the parser."""
        return self.metadata.tools

    def get_metadata_licenses(self) -> SortedSet:
        """Get the metadata licenses read by the parser."""
        return self.metadata.licenses

    def get_metadata_properties(self) -> SortedSet:
        """Get the list of metadata properties read by the parser."""
        return self.metadata.properties

    def is_valid_serial_number(self, serial_number: str) -> bool:
        if not serial_number:
            return False

        return not (serial_number is None or "urn:uuid:None" == serial_number)

    def read_tools(self, param: Iterable[dict[str, Any]]) -> Optional[Iterable[Tool]]:
        if not param:
            return None

        LOG.debug("CycloneDX: reading tools")
        tools = []
        for tool in param:
            tools.append(Tool(
                vendor=tool.get("vendor"),
                name=tool.get("name"),
                version=tool.get("version"),
                external_references=self.read_external_references(
                    tool.get("externalReferences", None))
            ))
        return tools

    def read_timestamp(self, param: str) -> Optional[datetime]:
        if not param:
            return None

        try:
            timestamp = dateparser.isoparse(param)
            return timestamp
        except ValueError:
            return None

    def read_url(self, param: str) -> Optional[XsUri]:
        if not param:
            return None

        return XsUri(uri=param)

    def read_license(self, param: dict[str, Any]) -> Optional[License]:
        if not param:
            return None

        text = param.get("text", None)
        license_text = AttachedText(content=text) if text else None
        return License(
            spdx_license_id=param.get("id", None),
            license_name=param.get("name", None),
            license_text=license_text,
            license_url=self.read_url(param.get("url", None)),
        )

    def read_licenses(self, param: Iterable[dict[str, Any]]) -> Optional[Iterable[LicenseChoice]]:
        if not param:
            return None

        licenses = []
        for entry in param:
            lic = self.read_license(entry.get("license", None))
            if lic:
                licenses.append(LicenseChoice(license_=lic))
                continue
            exp = entry.get("expression", None)
            if exp:
                licenses.append(LicenseChoice(license_expression=exp))
        return licenses

    def read_metadata(self, param: Optional[Any]) -> Optional[BomMetaData]:
        if param is None:
            return None

        LOG.debug("CycloneDX: reading metadata")
        licenses = self.read_licenses(param.get("licenses", None))
        metadata = BomMetaData(
            component=self.read_component(param.get("component", None)),
            properties=self.read_properties(param.get("properties", None)),
            licenses=licenses
        )
        if param.get("timestamp", None) is not None:
            timestamp = self.read_timestamp(param.get("timestamp"))
            if timestamp:
                metadata.timestamp = timestamp
        metadata.tools = self.read_tools(param.get("tools", None))
        return metadata

    def read_hash_algorithm(self, param: Any) -> HashAlgorithm:
        return HashAlgorithm(param)

    def read_hashes(self, hashes: Iterable[dict[str, Any]]) -> Optional[Iterable[HashType]]:
        if not hashes:
            return None

        hash_types = []
        for entry in hashes:
            if entry["alg"]:
                hash_types.append(HashType(
                    algorithm=self.read_hash_algorithm(entry["alg"]),
                    hash_value=entry["content"]))
        return hash_types

    def read_properties(self, values: Iterable[dict[str, Any]]) -> Optional[Iterable[Property]]:
        if not values:
            return None

        LOG.debug("CycloneDX: reading properties")
        properties = []
        for entry in values:
            if self.parser_mode == ParserMode.LEGACY_CX:
                # legacy-cx
                properties.append(Property(name=entry["key"], value=entry["value"]))
            else:
                properties.append(Property(name=entry["name"], value=entry["value"]))

        return properties

    def read_external_reference_type(self, value: Any) -> ExternalReferenceType:
        return ExternalReferenceType(value)

    def read_external_references(self, values: Iterable[dict[str, Any]]) -> Optional[Iterable[ExternalReference]]:
        if not values:
            return None

        ex_refs = []
        for entry in values:
            if entry.get("type"):
                ex_refs.append(ExternalReference(
                    reference_type=self.read_external_reference_type(entry.get("type")),
                    url=entry.get("url", None),
                    comment=entry.get("comment"),
                    hashes=self.read_hashes(entry.get("hashes", []))
                ))
        return ex_refs

    def read_component(self, entry: dict[str, Any]) -> Optional[Component]:
        if not entry:
            return None

        name = entry.get("name", None)
        version = entry.get("version")
        LOG.debug(f"CycloneDX: reading component {name}, {version}")
        return Component(
            name=name,
            version=version,
            group=entry.get("group"),
            author=entry.get("author"),
            description=entry.get("description"),
            copyright_=entry.get("copyright"),
            purl=entry.get("purl"),
            bom_ref=entry.get("bom-ref"),
            component_type=self.read_component_type(entry.get("type", None)),
            hashes=self.read_hashes(entry.get("hashes", None)),
            properties=self.read_properties(entry.get("properties", None)),
            external_references=self.read_external_references(entry.get("externalReferences", None)),
            licenses=self.read_licenses(entry.get("licenses", None))
        )

    def read_component_type(self, type_str: str) -> ComponentType:
        return ComponentType(type_str)


class CycloneDxSupport():
    # have constants for all important properties
    CDX_PROP_SW360ID = "siemens:sw360Id"
    CDX_PROP_LANGUAGE = "siemens:primaryLanguage"
    CDX_PROP_SRC_FILE_TYPE = "capycli:sourceFileType"
    CDX_PROP_SRC_FILE_COMMENT = "capycli:sourceFileComment"
    CDX_PROP_COMPONENT_ID = "capycli:componentId"
    CDX_PROP_FILENAME = "siemens:filename"
    CDX_PROP_MAPRESULT = "capycli:mapResult"
    CDX_PROP_SW360_HREF = "capycli:sw360Href"
    CDX_PROP_SW360_URL = "capycli:sw360Url"
    CDX_PROP_REL_STATE = "capycli:releaseMainlineState"
    CDX_PROP_CLEARING_STATE = "capycli:clearingState"
    CDX_PROP_CATEGORIES = "capycli:categories"
    CDX_PROP_PROJ_STATE = "capycli:projectClearingState"
    CDX_PROP_PROFILE = "siemens:profile"

    @staticmethod
    def get_property(comp: Component, name: str) -> Any:
        """Returns the property with the given name."""
        for prop in comp.properties:
            if prop.name == name:
                return prop

        return None

    @staticmethod
    def update_or_set_property(comp: Component, name: str, value: str) -> None:
        """Returns the property with the given name."""
        prop = None
        for p in comp.properties:
            if p.name == name:
                prop = p
                break

        if prop:
            prop.value = value
        else:
            comp.properties.add(Property(name=name, value=value))

    @staticmethod
    def remove_property(comp: Component, name: str) -> None:
        """Removes the property with the given name."""
        for p in comp.properties:
            if p.name == name:
                comp.properties.remove(p)
                break

    @staticmethod
    def get_property_value(comp: Component, name: str) -> Any:
        """Returns the value of the property with the given name."""
        for prop in comp.properties:
            if prop.name == name:
                return prop.value

        return ""

    @staticmethod
    def get_ext_ref(comp: Component, type: ExternalReferenceType, comment: str) -> Optional[ExternalReference]:
        for ext_ref in comp.external_references:
            if (ext_ref.type == type) and (ext_ref.comment == comment):
                return ext_ref

        return None

    @staticmethod
    def update_or_set_ext_ref(comp: Component, type: ExternalReferenceType, comment: str, value: str) -> None:
        ext_ref = None
        for er in comp.external_references:
            if (er.type == type) and (er.comment == comment):
                ext_ref = er
                break

        if ext_ref:
            ext_ref.url = value
        else:
            ext_ref = ExternalReference(
                reference_type=type,
                url=value,
                comment=comment)
            comp.external_references.add(ext_ref)

    @staticmethod
    def get_ext_ref_by_comment(comp: Component, comment: str) -> Any:
        for ext_ref in comp.external_references:
            if ext_ref.comment == comment:
                return ext_ref.url

        return ""

    @staticmethod
    def get_ext_ref_website(comp: Component) -> Any:
        for ext_ref in comp.external_references:
            if ext_ref.type == ExternalReferenceType.WEBSITE:
                return ext_ref.url

        return ""

    @staticmethod
    def get_ext_ref_repository(comp: Component) -> Any:
        for ext_ref in comp.external_references:
            if ext_ref.type == ExternalReferenceType.VCS:
                return ext_ref.url

        return ""

    @staticmethod
    def get_ext_ref_source_url(comp: Component) -> Any:
        for ext_ref in comp.external_references:
            if (ext_ref.type == ExternalReferenceType.DISTRIBUTION) \
                    and (ext_ref.comment == CaPyCliBom.SOURCE_URL_COMMENT):
                return ext_ref.url

        return ""

    @staticmethod
    def get_ext_ref_source_file(comp: Component) -> Any:
        for ext_ref in comp.external_references:
            if (ext_ref.type == ExternalReferenceType.DISTRIBUTION) \
                    and (ext_ref.comment == CaPyCliBom.SOURCE_FILE_COMMENT):
                return ext_ref.url

        return ""

    @staticmethod
    def get_ext_ref_binary_url(comp: Component) -> Any:
        for ext_ref in comp.external_references:
            if (ext_ref.type == ExternalReferenceType.DISTRIBUTION) \
                    and (ext_ref.comment == CaPyCliBom.BINARY_URL_COMMENT):
                return ext_ref.url

        return ""

    @staticmethod
    def get_ext_ref_binary_file(comp: Component) -> Any:
        for ext_ref in comp.external_references:
            if (ext_ref.type == ExternalReferenceType.DISTRIBUTION) \
                    and (ext_ref.comment == CaPyCliBom.BINARY_FILE_COMMENT):
                return ext_ref.url

        return ""

    @staticmethod
    def get_source_file_hash(comp: Component) -> Any:
        for ext_ref in comp.external_references:
            if (ext_ref.type == ExternalReferenceType.DISTRIBUTION) \
                    and (ext_ref.comment == CaPyCliBom.SOURCE_FILE_COMMENT):
                for hash in ext_ref.hashes:
                    if hash.alg == HashAlgorithm.SHA_1:
                        return hash.content

        return ""

    @staticmethod
    def get_binary_file_hash(comp: Component) -> Any:
        for ext_ref in comp.external_references:
            if (ext_ref.type == ExternalReferenceType.DISTRIBUTION) \
                    and (ext_ref.comment == CaPyCliBom.BINARY_FILE_COMMENT):
                for hash in ext_ref.hashes:
                    if hash.alg == HashAlgorithm.SHA_1:
                        return hash.content

        return ""


class SbomCreator():
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_standard_bom_tool() -> Tool:
        """Get Standard BOM version as tool."""
        tool = Tool()
        tool.vendor = "Siemens AG"
        tool.name = "standard-bom"
        tool.version = "2.0.0"

        extref = ExternalReference(
            reference_type=ExternalReferenceType.WEBSITE,
            url=XsUri("https://code.siemens.com/scpautomation/standard-bom"))
        tool.external_references.add(extref)

        return tool

    @staticmethod
    def get_capycli_tool(version: str = "") -> Tool:
        """Get CaPyCLI as tool."""
        tool = Tool()
        tool.vendor = "Siemens AG"
        tool.name = "CaPyCLI"
        if version:
            tool.version = version
        else:
            tool.version = capycli.get_app_version()

        extref = ExternalReference(
            reference_type=ExternalReferenceType.WEBSITE,
            url=XsUri("https://code.siemens.com/sw360/clearingautomation"))
        tool.external_references.add(extref)

        return tool

    @staticmethod
    def add_tools(tools: SortedSet) -> None:
        t1 = SbomCreator.get_standard_bom_tool()
        tools.add(t1)

        t2 = SbomCreator.get_capycli_tool()
        tools.add(t2)

    @staticmethod
    def add_profile(sbom: Bom, profile: str) -> None:
        """Adds the given Siemes Standard BOM profile."""
        prop = Property(
            name=CycloneDxSupport.CDX_PROP_PROFILE,
            value=profile)
        sbom.metadata.properties.add(prop)

    @staticmethod
    def create(bom: list[Component], **kwargs: bool) -> Bom:
        sbom = Bom()

        if not sbom.metadata.properties:
            sbom.metadata.properties = SortedSet()

        if not sbom.metadata.licenses:
            sbom.metadata.licenses = SortedSet()

        if "addlicense" in kwargs and kwargs["addlicense"]:
            license = License(spdx_license_id="CC0-1.0")
            license_choice = LicenseChoice(
                license_=license
            )
            sbom.metadata.licenses.add(license_choice)

        if "addprofile" in kwargs and kwargs["addprofile"]:
            SbomCreator.add_profile(sbom, "capycli")

        if not sbom.metadata.tools:
            sbom.metadata.tools = []

        if "addtools" in kwargs and kwargs["addtools"]:
            SbomCreator.add_tools(sbom.metadata.tools)

        if bom:
            sbom.components = bom

        return sbom


class SbomWriter():
    @classmethod
    def _remove_tool_python_lib(cls, sbom: Bom) -> None:
        for tool in sbom.metadata.tools:
            if tool.name == "cyclonedx-python-lib":
                sbom.metadata.tools.remove(tool)
                break

    @classmethod
    def remove_empty_properties(cls, component: Component) -> None:
        """
        Remove all empty properties in the given component.
        """
        to_be_deleted = []
        if not component:
            return

        for prop in component.properties:
            if not prop.value:
                to_be_deleted.append(prop)

        for prop in to_be_deleted:
            component.properties.remove(prop)

    @classmethod
    def remove_empty_properties_in_sbom(cls, sbom: Bom) -> None:
        """
        The CycloneDX writer does not correctly write empty properties,
        it writes only the property name, but no value. The resulting
        file is invalid.
        Mitigation: remove all empty properties.
        """
        if sbom.metadata.component:
            cls.remove_empty_properties(sbom.metadata.component)

        if sbom.components:
            for component in sbom.components:
                cls.remove_empty_properties(component)

    @classmethod
    def write_to_json(cls, sbom: Bom, outputfile: str, pretty_print: bool = False) -> None:
        SbomWriter._remove_tool_python_lib(sbom)
        if len(sbom.metadata.tools) == 0:
            sbom.metadata.tools.add(SbomCreator.get_capycli_tool())

        writer = JsonV1Dot4(sbom)
        cls.remove_empty_properties_in_sbom(sbom)

        if pretty_print:
            f = tempfile.NamedTemporaryFile(delete=False)
            output_file = Path(f.name)
            output_file.parent.mkdir(exist_ok=True, parents=True)
            writer.output_to_file(filename=f.name, allow_overwrite=True)
            jsondata = json_support.load_json_file(f.name)
            json_support.write_json_to_file(jsondata, outputfile)
            f.close()
            os.remove(f.name)
        else:
            writer.output_to_file(filename=outputfile, allow_overwrite=True)


class CaPyCliBom():
    """
    CaPyCLI / Siemens Standard BOM support.
    """

    # external reference comments for CaPyCLI/Siemens Standard BOM
    SOURCE_URL_COMMENT = "source archive (download location)"
    SOURCE_FILE_COMMENT = "source archive (local copy)"
    BINARY_URL_COMMENT = "binary (download location)"
    BINARY_FILE_COMMENT = "relativePath"

    @classmethod
    def read_sbom(cls, inputfile: str) -> Bom:
        LOG.debug(f"Reading from file {inputfile}")
        with open(inputfile) as fin:
            try:
                content = json.load(fin)
            except Exception as exp:
                raise CaPyCliException("Invalid JSON file: " + str(exp))

            try:
                parser = SbomJsonParser(content)
                bom = Bom.from_parser(parser=parser)

                # it seems that some of the information available in the JSON file has been
                # correctly **read** by our parser, but `Bom.from_parser` does not handle
                # it correctly. Therefore:
                if not bom.metadata.component:
                    bom.metadata.component = parser.get_project()
                    parser.link_dependencies_to_project(bom)
                bom.metadata.tools = parser.get_tools()
                bom.metadata.licenses = parser.get_metadata_licenses()
                bom.metadata.properties = parser.get_metadata_properties()
            except Exception as exp:
                raise CaPyCliException("Invalid CaPyCLI file: " + str(exp))

        return bom

    @classmethod
    def write_sbom(cls, sbom: Bom, outputfile: str) -> None:
        LOG.debug(f"Writing to file {outputfile}")
        try:
            # always add/update profile
            SbomCreator.add_profile(sbom, "capycli")
            SbomWriter.write_to_json(sbom, outputfile, pretty_print=True)
        except Exception as exp:
            raise CaPyCliException("Error writing CaPyCLI file: " + str(exp))
        LOG.debug("done")

    @classmethod
    def write_simple_sbom(cls, bom: list[Component], outputfile: str) -> None:
        LOG.debug(f"Writing to file {outputfile}")
        try:
            creator = SbomCreator()
            sbom = creator.create(bom, addlicense=True, addprofile=True, addtools=True)
            SbomWriter.write_to_json(sbom, outputfile, pretty_print=True)
        except Exception as exp:
            raise CaPyCliException("Error writing CaPyCLI file: " + str(exp))
        LOG.debug("done")
