# -------------------------------------------------------------------------------
# Copyright (c) 2023-2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import json
import os
import pathlib
from enum import Enum
from typing import Any, List, Optional, Union

from cyclonedx.factory.license import LicenseFactory
from cyclonedx.model import ExternalReference, ExternalReferenceType, HashAlgorithm, HashType, Property, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.model.contact import OrganizationalEntity
from cyclonedx.model.definition import Definitions, Standard
from cyclonedx.model.tool import ToolRepository
from cyclonedx.output.json import JsonV1Dot6
from sortedcontainers import SortedSet

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
    def set_property(comp: Component, name: str, value: str) -> None:
        """Sets the property with the given name."""
        comp.properties.add(Property(name=name, value=value))

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
            CycloneDxSupport.set_property(comp, name, value)

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
    def set_ext_ref(comp: Component, type: ExternalReferenceType, comment: str, value: str,
                    hash_algo: str = "", hash: str = "") -> None:
        ext_ref = ExternalReference(
            type=type,
            url=XsUri(value),
            comment=comment)

        if hash_algo and hash:
            ext_ref.hashes.add(HashType(
                alg=HashAlgorithm.SHA_1,
                content=hash))

        comp.external_references.add(ext_ref)

    @staticmethod
    def update_or_set_ext_ref(comp: Component, type: ExternalReferenceType, comment: str, value: str) -> None:
        ext_ref = None
        for er in comp.external_references:
            if (er.type == type) and (er.comment == comment):
                ext_ref = er
                break

        if ext_ref:
            ext_ref.url = XsUri(value)
        else:
            CycloneDxSupport.set_ext_ref(comp, type, comment, value)

    @staticmethod
    def have_relative_ext_ref_path(ext_ref: ExternalReference, rel_to: str) -> str:
        if isinstance(ext_ref.url, str):
            bip = pathlib.PurePath(ext_ref.url)
        else:
            bip = pathlib.PurePath(ext_ref.url._uri)
        file = bip.as_posix()
        if os.path.isfile(file):
            ext_ref.url = XsUri("file://" + bip.relative_to(rel_to).as_posix())
        return bip.name

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
    def get_ext_ref_source_code_url(comp: Component) -> Any:
        for ext_ref in comp.external_references:
            if (ext_ref.type == ExternalReferenceType.DISTRIBUTION) \
                    and (ext_ref.comment is None):
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
    def get_capycli_tool(version: str = "") -> Component:
        """Get CaPyCLI as tool."""
        component = Component(
            name="CaPyCLI",
            supplier=OrganizationalEntity(name="Siemens AG"),
            type=ComponentType.APPLICATION
        )
        if version:
            component.version = version
        else:
            component.version = capycli.get_app_version()

        extref = ExternalReference(
            type=ExternalReferenceType.WEBSITE,
            url=XsUri("https://github.com/sw360/capycli"))
        component.external_references.add(extref)

        return component

    @staticmethod
    def add_tools(components: SortedSet) -> None:
        tc1 = SbomCreator.get_capycli_tool()
        components.add(tc1)

    @staticmethod
    def add_standard_bom_standard(sbom: Bom) -> None:
        """Add the Siemens Standard BOM definition."""
        std_comp = Standard(
            name="Standard BOM",
            version="3.0.0",
            bom_ref="standard-bom",
            description="The Standard for Software Bills of Materials in Siemens",
            owner="Siemens AG",
            external_references=[ExternalReference(
                type=ExternalReferenceType.WEBSITE,
                url=XsUri("https://sbom.siemens.io/")
            )]
        )

        if not sbom.definitions:
            sbom.definitions = Definitions(standards=[std_comp])
        else:
            sbom.definitions.standards.add(std_comp)

    @staticmethod
    def add_profile(sbom: Bom, profile: str) -> None:
        """Adds the given Siemens Standard BOM profile."""
        prop = Property(
            name=CycloneDxSupport.CDX_PROP_PROFILE,
            value=profile)
        sbom.metadata.properties.add(prop)

    @staticmethod
    def create(bom: Union[List[Component], SortedSet], **kwargs: Any) -> Bom:
        sbom = Bom()

        if "addlicense" in kwargs and kwargs["addlicense"]:
            license_factory = LicenseFactory()
            sbom.metadata.licenses.add(license_factory.make_with_id("CC0-1.0"))

        if "addprofile" in kwargs and kwargs["addprofile"]:
            SbomCreator.add_profile(sbom, "clearing")

        if not sbom.metadata.tools:
            sbom.metadata.tools = ToolRepository()

        if "addtools" in kwargs and kwargs["addtools"]:
            SbomCreator.add_tools(sbom.metadata.tools.components)
            SbomCreator.add_standard_bom_standard(sbom)

        if "name" in kwargs or "version" in kwargs or "description" in kwargs:
            _name = str(kwargs.get("name", ""))
            _version = str(kwargs.get("version", ""))
            _description = str(kwargs.get("description", ""))
            if _name and _version and _description:
                sbom.metadata.component = Component(name=_name, version=_version, description=_description)

        if bom:
            for c in bom:
                sbom.components.add(c)
                if sbom.metadata.component:
                    sbom.register_dependency(sbom.metadata.component, [c])
            sbom.components = SortedSet(bom)

        return sbom


class SbomWriter():
    @classmethod
    def _remove_tool_python_lib(cls, sbom: Bom) -> None:
        if isinstance(sbom.metadata.tools, ToolRepository):
            for component in sbom.metadata.tools.components:
                if component.name == "cyclonedx-python-lib":
                    sbom.metadata.tools.components.remove(component)
                    break
            for service in sbom.metadata.tools.services:
                if service.name == "cyclonedx-python-lib":
                    sbom.metadata.tools.services.remove(service)
                    break
            for tool in sbom.metadata.tools.tools:
                if tool.name == "cyclonedx-python-lib":
                    sbom.metadata.tools.tools.remove(tool)
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
        if not sbom.metadata:
            return

        if sbom.metadata.component:
            cls.remove_empty_properties(sbom.metadata.component)

        if sbom.components:
            for component in sbom.components:
                cls.remove_empty_properties(component)

    @classmethod
    def write_to_json(cls, sbom: Bom, outputfile: str, pretty_print: bool = False) -> None:
        SbomWriter._remove_tool_python_lib(sbom)
        if len(sbom.metadata.tools) == 0:
            sbom.metadata.tools.components.add(SbomCreator.get_capycli_tool())

        writer = JsonV1Dot6(sbom)
        cls.remove_empty_properties_in_sbom(sbom)

        if pretty_print:
            jsondata = writer.output_as_string().encode('utf-8')
            json_support.write_json_to_file(json.loads(jsondata), outputfile)
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
                json_data = json.load(fin)
            except Exception as exp:
                raise CaPyCliException("Error reading raw JSON file: " + str(exp))

            # my_json_validator = JsonStrictValidator(SchemaVersion.V1_6)
            # try:
            #     validation_errors = my_json_validator.validate_str(json_string)
            #     if validation_errors:
            #         raise CaPyCliException("JSON validation error: " + repr(validation_errors))
            #
            #     print_green("JSON file successfully validated")
            # except MissingOptionalDependencyException as error:
            #     print_yellow('JSON-validation was skipped due to', error)
            bom = Bom.from_json(  # type: ignore[attr-defined]
                json_data)
            return bom

    @classmethod
    def write_sbom(cls, sbom: Bom, outputfile: str) -> None:
        LOG.debug(f"Writing to file {outputfile}")
        try:
            # always add/update profile
            SbomCreator.add_profile(sbom, "clearing")
            SbomWriter.write_to_json(sbom, outputfile, pretty_print=True)
        except Exception as exp:
            raise CaPyCliException("Error writing CaPyCLI file: " + str(exp))
        LOG.debug("done")

    @classmethod
    def write_simple_sbom(cls, bom: SortedSet, outputfile: str) -> None:
        LOG.debug(f"Writing to file {outputfile}")
        try:
            creator = SbomCreator()
            sbom = creator.create(bom, addlicense=True, addprofile=True, addtools=True)
            SbomWriter.write_to_json(sbom, outputfile, pretty_print=True)
        except Exception as exp:
            raise CaPyCliException("Error writing CaPyCLI file: " + str(exp))
        LOG.debug("done")
