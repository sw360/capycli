# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from typing import Any, Dict, List

from cyclonedx.model import ExternalReference, ExternalReferenceType, HashAlgorithm, HashType, Property, XsUri
from cyclonedx.model.bom_ref import BomRef
from cyclonedx.model.component import Component
from packageurl import PackageURL
from sortedcontainers import SortedSet

from capycli import LOG
from capycli.common import json_support
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport

# -------------------------------------
# Expected File Format
#
# A JSON file with a list of JSON objects.
# Each object can have the following properties
# * Name
# * Version
# * Description
# * ProjectSite
# * Sw360Id (or Id)
# * Href
# * Url
# * SourceFileUrl
# * SourceUrl
# * SourceFile
# * SourceFileType
# * SourceFileComment
# * BinaryFile
# * BinaryFileUrl
# * RepositoryUrl
# * Language
# * RepositoryType
# * RepositoryId
# * SourceFileHash (always assumed to be SHA-1)
# * BinaryFileHash (always assumed to be SHA-1)
# * ProjectClearingState
# * ClearingState
# * ReleaseMainlineState
# -------------------------------------


class LegacySupport():
    @staticmethod
    def get_purl_from_name(item: Dict[str, Any]) -> PackageURL:
        """Builds/guesses a package-url from name, version
        and provided language information."""
        lang = "generic"
        if "Language" in item:
            if item["Language"].lower() == "python":
                lang = "pypi"
            elif item["Language"].lower() == "c#":
                lang = "nuget"
            elif item["Language"].lower() == "java":
                lang = "maven"
            if item["Language"].lower() == "javascript":
                lang = "npm"

        purl = PackageURL(type=lang, name=item.get("Name", ""), version=item.get("Version", ""))
        return purl

    @staticmethod
    def get_purl_from_legacy(item: Dict[str, Any]) -> PackageURL:
        if "RepositoryType" in item:
            if (item["RepositoryType"] == "package-url") or (item["RepositoryType"] == "purl"):
                id = item.get("RepositoryId", "")
                if id:
                    return PackageURL.from_string(id)

        return LegacySupport.get_purl_from_name(item)

    @staticmethod
    def legacy_component_to_cdx(item: Dict[str, Any]) -> Component:
        """Convert a single CaPyCLI legacy component to a CycloneDX component."""
        purl = LegacySupport.get_purl_from_legacy(item)
        if purl:
            cxcomp = Component(
                name=item.get("Name", "").strip(),
                version=item.get("Version", "").strip(),
                purl=purl,
                bom_ref=BomRef(purl.to_string()),
                description=item.get("Description", "").strip())

        website = item.get("ProjectSite", "")
        if not website:
            website = item.get("Homepage", "")
        if website:
            ext_ref = ExternalReference(
                type=ExternalReferenceType.WEBSITE,
                url=XsUri(website))
            cxcomp.external_references.add(ext_ref)

        projectClearingState = item.get("ProjectClearingState", "")
        if projectClearingState:
            prop = Property(
                name=CycloneDxSupport.CDX_PROP_PROJ_STATE,
                value=projectClearingState)
            cxcomp.properties.add(prop)

        if "Sw360Id" in item:
            sw360_id = item.get("Sw360Id", "")
        else:
            sw360_id = item.get("Id", "")
        if sw360_id:
            prop = Property(
                name=CycloneDxSupport.CDX_PROP_SW360ID,
                value=sw360_id)
            cxcomp.properties.add(prop)

        sw360_href = item.get("Href", "")
        if sw360_href:
            prop = Property(
                name=CycloneDxSupport.CDX_PROP_SW360_HREF,
                value=sw360_href)
            cxcomp.properties.add(prop)

        sw360_url = item.get("Url", "")
        if projectClearingState:
            prop = Property(
                name=CycloneDxSupport.CDX_PROP_SW360_URL,
                value=sw360_url)
            cxcomp.properties.add(prop)

        clearingState = item.get("ClearingState", "")
        if clearingState:
            prop = Property(
                name=CycloneDxSupport.CDX_PROP_CLEARING_STATE,
                value=clearingState)
            cxcomp.properties.add(prop)

        releaseMainlineState = item.get("ReleaseMainlineState", "")
        if releaseMainlineState:
            prop = Property(
                name=CycloneDxSupport.CDX_PROP_REL_STATE,
                value=releaseMainlineState)
            cxcomp.properties.add(prop)

        sourceFileUrl = item.get("SourceFileUrl", "")
        if sourceFileUrl:
            ext_ref = ExternalReference(
                type=ExternalReferenceType.DISTRIBUTION,
                comment=CaPyCliBom.SOURCE_FILE_COMMENT,
                url=XsUri(sourceFileUrl))
            hash = item.get("SourceFileHash", "")
            if hash:
                ext_ref.hashes.add(HashType(
                    alg=HashAlgorithm.SHA_1,
                    content=hash))
            cxcomp.external_references.add(ext_ref)
        else:
            sourceUrl = item.get("SourceUrl", "")
            if sourceUrl:
                ext_ref = ExternalReference(
                    type=ExternalReferenceType.DISTRIBUTION,
                    comment=CaPyCliBom.SOURCE_URL_COMMENT,
                    url=XsUri(sourceUrl))
                hash = item.get("SourceFileHash", "")
                if hash:
                    ext_ref.hashes.add(HashType(
                        alg=HashAlgorithm.SHA_1,
                        content=hash))
                cxcomp.external_references.add(ext_ref)

        sourceFile = item.get("SourceFile", "")
        if sourceFile:
            ext_ref = ExternalReference(
                type=ExternalReferenceType.DISTRIBUTION,
                comment="source archive (local copy)",
                url=XsUri(sourceFile))
            hash = item.get("SourceFileHash", "")
            if hash:
                ext_ref.hashes.add(HashType(
                    alg=HashAlgorithm.SHA_1,
                    content=hash))
            cxcomp.external_references.add(ext_ref)

        # no way to map SourceFileHash, because we do not know the type of hash

        sourceFileType = item.get("SourceFileType", "")
        if sourceFileType:
            prop = Property(
                name=CycloneDxSupport.CDX_PROP_SRC_FILE_TYPE,
                value=sourceFileType)
            cxcomp.properties.add(prop)

        sourceFileComment = item.get("SourceFileComment", "")
        if sourceFileComment:
            prop = Property(
                name=CycloneDxSupport.CDX_PROP_SRC_FILE_COMMENT,
                value=sourceFileComment)
            cxcomp.properties.add(prop)

        binaryFile = item.get("BinaryFile", "")
        if binaryFile:
            ext_ref = ExternalReference(
                type=ExternalReferenceType.DISTRIBUTION,
                comment=CaPyCliBom.BINARY_FILE_COMMENT,
                url=XsUri(binaryFile))
            hash = item.get("BinaryFileHash", "")
            if hash:
                ext_ref.hashes.add(HashType(
                    alg=HashAlgorithm.SHA_1,
                    content=hash))
            cxcomp.external_references.add(ext_ref)

        # no way to map BinaryFileHash, because we do not know the type of hash

        binaryFileUrl = item.get("BinaryFileUrl", "")
        if binaryFileUrl:
            ext_ref = ExternalReference(
                type=ExternalReferenceType.DISTRIBUTION,
                comment=CaPyCliBom.BINARY_URL_COMMENT,
                url=XsUri(binaryFileUrl))
            hash = item.get("BinaryFileHash", "")
            if hash:
                ext_ref.hashes.add(HashType(
                    alg=HashAlgorithm.SHA_1,
                    content=hash))
            cxcomp.external_references.add(ext_ref)

        repositoryUrl = item.get("RepositoryUrl", "")
        if repositoryUrl:
            ext_ref = ExternalReference(
                type=ExternalReferenceType.VCS,
                url=XsUri(repositoryUrl))
            cxcomp.external_references.add(ext_ref)

        language = item.get("Language", "")
        if language:
            prop = Property(
                name=CycloneDxSupport.CDX_PROP_LANGUAGE,
                value=language)
            cxcomp.properties.add(prop)

        return cxcomp

    @classmethod
    def legacy_to_cdx_components(cls, inputfile: str) -> List[Component]:
        """Convert a CaPyCLI legacy  list of components to a list
        of CycloneDX components."""
        LOG.debug(f"Reading from file {inputfile}")
        bom = []
        legacy_bom = json_support.load_json_file(inputfile)
        for item in legacy_bom:
            cxcomp = LegacySupport.legacy_component_to_cdx(item)
            LOG.debug(f"  Reading from legacy: name={cxcomp.name}, version={cxcomp.version}")

            bom.append(cxcomp)

        return bom

    @classmethod
    def cdx_component_to_legacy(cls, cx_comp: Component) -> Dict[str, Any]:
        lcomp: Dict[str, Any] = {}
        lcomp["Name"] = cx_comp.name
        lcomp["Version"] = cx_comp.version or ""
        lcomp["Description"] = cx_comp.description or ""
        lcomp["Language"] = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_LANGUAGE)
        lcomp["SourceUrl"] = str(CycloneDxSupport.get_ext_ref_source_url(cx_comp))
        lcomp["RepositoryUrl"] = str(CycloneDxSupport.get_ext_ref_repository(cx_comp))
        lcomp["SourceFile"] = str(CycloneDxSupport.get_ext_ref_source_file(cx_comp))
        lcomp["SourceFileHash"] = CycloneDxSupport.get_source_file_hash(cx_comp)
        lcomp["BinaryFile"] = str(CycloneDxSupport.get_ext_ref_binary_file(cx_comp))
        lcomp["BinaryFileHash"] = CycloneDxSupport.get_binary_file_hash(cx_comp)
        lcomp["BinaryFileUrl"] = str(CycloneDxSupport.get_ext_ref_binary_url(cx_comp))
        lcomp["Homepage"] = str(CycloneDxSupport.get_ext_ref_website(cx_comp))
        lcomp["ProjectSite"] = str(CycloneDxSupport.get_ext_ref_website(cx_comp))  # same!
        if cx_comp.purl:
            lcomp["RepositoryType"] = "package-url"
            lcomp["RepositoryId"] = cx_comp.purl.to_string() or ""
        lcomp["Sw360Id"] = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SW360ID)

        lcomp["SourceFileType"] = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SRC_FILE_TYPE)
        lcomp["SourceFileComment"] = CycloneDxSupport.get_property_value(
            cx_comp, CycloneDxSupport.CDX_PROP_SRC_FILE_COMMENT)

        lcomp["Href"] = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SW360_HREF)
        lcomp["Url"] = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_SW360_URL)
        lcomp["ClearingState"] = CycloneDxSupport.get_property_value(
            cx_comp, CycloneDxSupport.CDX_PROP_CLEARING_STATE)
        lcomp["ReleaseMainlineState"] = CycloneDxSupport.get_property_value(
            cx_comp, CycloneDxSupport.CDX_PROP_REL_STATE)
        lcomp["ProjectClearingState"] = CycloneDxSupport.get_property_value(
            cx_comp, CycloneDxSupport.CDX_PROP_PROJ_STATE)
        lcomp["ComponentId"] = CycloneDxSupport.get_property_value(cx_comp, CycloneDxSupport.CDX_PROP_COMPONENT_ID)

        return lcomp

    @classmethod
    def write_cdx_components_as_legacy(cls, bom: SortedSet, outputfile: str) -> None:
        LOG.debug(f"Writing to file {outputfile}")

        legacy_bom = []
        for cx_comp in bom:
            lcomp = cls.cdx_component_to_legacy(cx_comp)
            legacy_bom.append(lcomp)

        json_support.write_json_to_file(legacy_bom, outputfile)

        LOG.debug("done")
