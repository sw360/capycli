# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from enum import Enum
from typing import Any, List, Optional

from cyclonedx.model.component import Component

from capycli.common.capycli_bom_support import CycloneDxSupport


class MapResultByIdQualifiers(Enum):
    FULL_MATCH = "qualifiers-full-match"
    IGNORED = "qualifiers-ignored"
    UNKNOWN = "qualifiers-unknown-match"
    NO_QUALIFIER_MAPPING = ""


class MapResult:
    """Result of mapping a SBOM item to the list of releases"""

    # Match result codes: must be in the order best match to last match!!

    # Invalid result
    INVALID = "0-invalid"

    # Full match by identifier.
    FULL_MATCH_BY_ID = "1-full-match-by-id"

    # Full match by source file hash.
    FULL_MATCH_BY_HASH = "2-full-match-by-hash"

    # Full match by name and version.
    FULL_MATCH_BY_NAME_AND_VERSION = "3-full-match-by-name-and-version"

    # Match by source code filename.
    MATCH_BY_FILENAME = "4-good-match-by-filename"

    # Highest result code for a good match
    GOOD_MATCH_FOUND = MATCH_BY_FILENAME

    # Component found, no version match.
    MATCH_BY_NAME = "5-candidate-match-by-name"

    # Similar component found, no version check.
    SIMILAR_COMPONENT_FOUND = "6-candidate-match-similar-component"

    # Component was not found
    NO_MATCH = "9-no-match"

    def __init__(self, component: Optional[Component] = None) -> None:
        self.input_component: Optional[Component] = component
        self.result: str = MapResult.NO_MATCH
        self._component_hrefs: List[str] = []
        self._release_hrefs: List[str] = []
        self._release_hrefs_results: List[str] = []
        self.releases: List[Any] = []

    @property
    def release_hrefs_results(self) -> list[str]:
        return self._release_hrefs_results

    @release_hrefs_results.setter
    def release_hrefs_results(self, value: list[str]) -> None:
        self._release_hrefs_results = value
        if not self.input_component or not value:
            return
        CycloneDxSupport.update_or_set_property(
            self.input_component, CycloneDxSupport.CDX_PROP_MAPRESULT_BY_ID,
            " ".join(value))

    @property
    def component_hrefs(self) -> List[str]:
        return self._component_hrefs

    @component_hrefs.setter
    def component_hrefs(self, value: List[str]) -> None:
        self._component_hrefs = value
        if not self.input_component:
            return
        if len(value) == 1:
            CycloneDxSupport.update_or_set_property(self.input_component, CycloneDxSupport.CDX_PROP_COMPONENT_ID,
                                                    value[0].split("/")[-1])
        else:
            CycloneDxSupport.remove_property(self.input_component,
                                             CycloneDxSupport.CDX_PROP_COMPONENT_ID)

    @property
    def release_hrefs(self) -> List[str]:
        return self._release_hrefs

    @release_hrefs.setter
    def release_hrefs(self, value: List[str]) -> None:
        self._release_hrefs = value
        if not self.input_component:
            return
        if len(value) == 1:
            CycloneDxSupport.update_or_set_property(self.input_component, CycloneDxSupport.CDX_PROP_SW360ID,
                                                    value[0].split("/")[-1])
        else:
            CycloneDxSupport.remove_property(self.input_component, CycloneDxSupport.CDX_PROP_SW360ID)

    @classmethod
    def map_code_to_string(cls, map_code: str) -> str:
        """"Converts a map code to a string"""
        if map_code == MapResult.NO_MATCH:
            return "No match"
        if map_code == MapResult.FULL_MATCH_BY_ID:
            return "Full match by id"
        if map_code == MapResult.FULL_MATCH_BY_HASH:
            return "Full match by hash"
        if map_code == MapResult.FULL_MATCH_BY_NAME_AND_VERSION:
            return "Full match by name and version"
        if map_code == MapResult.MATCH_BY_FILENAME:
            return "Match by filename"
        if map_code == MapResult.MATCH_BY_NAME:
            return "Match by name"
        if map_code == MapResult.SIMILAR_COMPONENT_FOUND:
            return "Similar component found"

        return ""

    def __str__(self) -> str:
        rel = ""
        if self.releases:
            more = ""
            if len(self.releases) > 1:
                more = " (and " + str(len(self.releases)) + " others)"

            rel = (
                "=> "
                + self.releases[0].get("Name", self.releases[0].get("name", ""))
                + ", "
                + self.releases[0].get("Version", self.releases[0].get("version", ""))
                + ", "
                + self.releases[0].get("Id", self.releases[0].get("id", ""))
                + more
            )

        if not self.input_component:
            return (
                self.map_code_to_string(self.result)
                + ", (no component), "
                + rel
            )
        else:
            return (
                self.map_code_to_string(self.result)
                + ", "
                + str(self.input_component.name)
                + ", "
                + str(self.input_component.version or "")
                + " "
                + str(rel)
            )
