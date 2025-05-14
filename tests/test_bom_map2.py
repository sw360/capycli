# -------------------------------------------------------------------------------
# Copyright (c) 2021-2023 Siemens
# All Rights Reserved.
# Author: gernot.hillier@siemens.com, thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
from typing import Any, Dict

import responses
from cyclonedx.model import ExternalReferenceType, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from packageurl import PackageURL

from capycli.bom.map_bom import MapBom, MapMode
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.common.json_support import load_json_file
from capycli.common.map_result import MapResult
from capycli.common.purl_service import PurlService
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase
from tests.test_base_vcr import SW360_BASE_URL, CapycliTestBase


class CapycliTestBomMap(CapycliTestBase):
    INPUTFILE_INVALID = "plaintext.txt"
    INPUTFILE1 = "sbom_for_mapping1.json"
    INPUTFILE2 = "sbom_for_mapping2.json"
    OUTPUTFILE = "output.json"
    OVERVIEW_FILE = "mappingoverview.json"
    MAPPING_FILE = "mapresult.json"
    MYTOKEN = "MYTOKEN"
    MYURL = "https://my.server.com/"
    ERROR_MSG_NO_LOGIN = "Unable to login"
    CACHE_FILE = "dummy_cache.json"

    @responses.activate
    def setUp(self) -> None:
        self.app = MapBom()
        responses.add(responses.GET, SW360_BASE_URL, json={"status": "ok"})
        self.app.login("sometoken", "https://my.server.com")

    # ---------------------- map_bom_item purl cases ----------------------

    @responses.activate
    def test_map_bom_item_purl_component(self) -> None:
        """test bom mapping: we have a component purl match, but different names
        """
        if not self.app.client:
            return

        self.app.purl_service = PurlService(self.app.client, cache={'deb': {'debian': {'sed': {
            None: [{
                "purl": PackageURL("deb", "debian", "sed"),
                "href": SW360_BASE_URL + "components/a035"}]}}}})
        # different name in release cache
        self.app.releases = [{"Id": "1234", "ComponentId": "a035",
                              "Name": "Unix Stream EDitor", "Version": "1.0",
                              "ExternalIds": {}}]
        bomitem = Component(
            name="sed",
            version="1.0",
            purl=PackageURL.from_string("pkg:deb/debian/sed@1.0?type=source"))

        # component found by PURL, version match by string comparison
        res = self.app.map_bom_item(bomitem, check_similar=False, result_required=False)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert res.component_hrefs[0] == SW360_BASE_URL + "components/a035"
        assert res.releases[0]["Sw360Id"] == "1234"
        assert res.releases[0]["ComponentId"] == "a035"

        bomitem = Component(
            name="sed",
            version="1.1",
            purl=PackageURL.from_string("pkg:deb/debian/sed@1.1?type=source"))

        # component found by PURL, but version does not match
        res = self.app.map_bom_item(bomitem, check_similar=False, result_required=False)
        assert res.result == MapResult.NO_MATCH
        assert res.component_hrefs[0] == SW360_BASE_URL + "components/a035"
        assert res.input_component is not None
        assert (
            CycloneDxSupport.get_property(res.input_component, CycloneDxSupport.CDX_PROP_COMPONENT_ID).value
            == "a035")
        assert len(res.releases) == 0

        # enable name matching
        self.app.no_match_by_name_only = False
        res = self.app.map_bom_item(bomitem, check_similar=False, result_required=False)
        assert res.result == MapResult.MATCH_BY_NAME
        assert res.component_hrefs[0] == SW360_BASE_URL + "components/a035"
        assert res.input_component is not None
        assert (
            CycloneDxSupport.get_property(res.input_component, CycloneDxSupport.CDX_PROP_COMPONENT_ID).value
            == "a035")
        assert res.releases[0]["ComponentId"] == "a035"
        assert len(res.releases) == 1

    @responses.activate
    def test_map_bom_item_purl_component_release_conflict(self) -> None:
        """test bom mapping (nocache): we have two releases for other versions
        with PURLs pointing to different components, no direct purl match for release
        """
        if not self.app.client:
            return

        self.app.purl_service = PurlService(self.app.client, cache={'maven': {
            'com.fasterxml.jackson.core': {'jackson-core': {
                "2.18.0": [{
                    "purl": PackageURL("maven", "com.fasterxml.jackson.core", "jackson-core", version="2.18.0"),
                    "href": SW360_BASE_URL + "releases/1234"}],
                "2.5.0": [{
                    "purl": PackageURL("maven", "com.fasterxml.jackson.core", "jackson-core", version="2.5.0"),
                    "href": SW360_BASE_URL + "releases/1235"}]}}}})

        self.app.releases = [{"Id": "1234", "ComponentId": "a035",
                              "Name": "Jackson Core", "Version": "2.18.0",
                              "ExternalIds": {
                                  "package-url": "pkg:maven/com.fasterxml.jackson.core/jackson-core@2.18.0"}},
                             {"Id": "1235", "ComponentId": "a034",
                              "Name": "com.fasterxml.jackson.core:jackson-core", "Version": "2.5.0",
                              "ExternalIds": {
                                  "package-url": "pkg:maven/com.fasterxml.jackson.core/jackson-core@2.5.0"}},
                             {"Id": "1236", "ComponentId": "a034",
                              "Name": "com.fasterxml.jackson.core:jackson-core", "Version": "2.17.0",
                              "ExternalIds": []}]

        # PURL search of components via releases needs to get component ids from releases
        release_data1 = {"name": "Jackson Core", "version": "2.18.0", "_links": {
                         "self": {"href": SW360_BASE_URL + 'releases/1234'},
                         "sw360:component": {"href": SW360_BASE_URL + "components/a035"}}}
        release_data2 = {"name": "com.fasterxml.jackson.core:jackson-core", "version": "2.5.0", "_links": {
                         "self": {"href": SW360_BASE_URL + 'releases/1235'},
                         "sw360:component": {"href": SW360_BASE_URL + "components/a034"}}}
        responses.add(responses.GET, SW360_BASE_URL + 'releases/1234', json=release_data1)
        responses.add(responses.GET, SW360_BASE_URL + 'releases/1235', json=release_data2)

        bomitem = Component(
            name="jackson-core",
            version="2.17.0",
            purl=PackageURL.from_string("pkg:maven/com.fasterxml.jackson.core/jackson-core@2.17.0"))

        # component found by PURL, version match by string comparison
        res = self.app.map_bom_item(bomitem, check_similar=False, result_required=False)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert res.releases[0]["Sw360Id"] == "1236"
        assert res.releases[0]["ComponentId"] == "a034"
        assert len(res.releases) == 1
        assert res.input_component is not None
        assert (
            CycloneDxSupport.get_property(res.input_component, CycloneDxSupport.CDX_PROP_COMPONENT_ID)
            is None)

    @responses.activate
    def test_map_bom_item_purl_release(self) -> None:
        """test bom mapping: we have a release purl match
        """
        if not self.app.client:
            return

        self.app.purl_service = PurlService(self.app.client, cache={'deb': {'debian': {'sed': {
            None: [{
                "purl": PackageURL("deb", "debian", "sed"),
                "href": SW360_BASE_URL + "components/a035"}],
            "1.0~1": [{
                "purl": PackageURL("deb", "debian", "sed", version="1.0~1"),
                "href": SW360_BASE_URL + "releases/1234"}]}}}})
        self.app.releases = [{"Id": "1234", "ComponentId": "a035",
                              "Name": "Unix Stream EDitor", "Version": "1.0+1",
                              "ExternalIds": {
                                  "package-url": "pkg:deb/debian/sed@1.0~1?type=source"}}
                             ]
        # in a purl, "~" may be encoded as %7E
        bomitem = Component(
            name="sed",
            version="1.0~1",
            purl=PackageURL.from_string("pkg:deb/debian/sed@1.0%7E1?type=source"))

        res = self.app.map_bom_item(bomitem, check_similar=False, result_required=False)
        assert res.result == MapResult.FULL_MATCH_BY_ID
        assert res.component_hrefs[0] == SW360_BASE_URL + "components/a035"
        assert res.input_component is not None
        assert (
            CycloneDxSupport.get_property(res.input_component, CycloneDxSupport.CDX_PROP_COMPONENT_ID).value
            == "a035")
        assert res.releases[0]["Sw360Id"] == "1234"
        assert res.releases[0]["ComponentId"] == "a035"

    @responses.activate
    def test_map_bom_item_purl_release_conflict(self) -> None:
        """test bom mapping (nocache): we have two releases in different components
        with same PURL and same version
        """
        if not self.app.client:
            return

        self.app.purl_service = PurlService(self.app.client, cache={'maven': {
            'com.fasterxml.jackson.core': {'jackson-core': {
                None: [{
                    "purl": PackageURL("maven", "com.fasterxml.jackson.core", "jackson-core"),
                    "href": SW360_BASE_URL + "components/a035"}],
                "2.18.0": [
                    {"purl": PackageURL("maven", "com.fasterxml.jackson.core", "jackson-core", version="2.18.0"),
                     "href": SW360_BASE_URL + "releases/1234"},
                    {"purl": PackageURL("maven", "com.fasterxml.jackson.core", "jackson-core", version="2.18.0"),
                     "href": SW360_BASE_URL + "releases/1236"}]}}}})

        self.app.releases = [{"Id": "1234", "ComponentId": "a035",
                              "Name": "Jackson Core", "Version": "2.18.0",
                              "ExternalIds": {
                                  "package-url": "pkg:maven/com.fasterxml.jackson.core/jackson-core@2.18.0"}},
                             {"Id": "1236", "ComponentId": "a034",
                              "Name": "com.fasterxml.jackson.core:jackson-core", "Version": "2.18.0",
                              "ExternalIds": {
                                  "package-url": "pkg:maven/com.fasterxml.jackson.core/jackson-core@2.18.0"}}]

        bomitem = Component(
            name="jackson-core",
            version="2.18.0",
            purl=PackageURL.from_string("pkg:maven/com.fasterxml.jackson.core/jackson-core@2.18.0"))

        # component found by PURL, version match by string comparison
        res = self.app.map_bom_item(bomitem, check_similar=False, result_required=False)
        assert res.result == MapResult.FULL_MATCH_BY_ID
        if res.releases[0]["Sw360Id"] == "1234":
            assert res.releases[0]["ComponentId"] == "a035"
        elif res.releases[0]["Sw360Id"] == "1236":
            assert res.releases[0]["ComponentId"] == "a034"
        else:
            assert False, "Unexpected release id"
        assert len(res.releases) == 1

    @responses.activate
    def test_map_bom_item_mixed_match(self) -> None:
        bomitem = Component(
            name="mail",
            version="1.4")

        self.app.releases = [{"Id": "1111", "ComponentId": "b001",
                              "Name": "mail", "Version": "1.4",
                              "ExternalIds": {}},
                             {"Id": "1112", "ComponentId": "b002",
                              "Name": "Mail", "Version": "1.0",
                              "ExternalIds": {}}]

        self.app.no_match_by_name_only = True
        res = self.app.map_bom_item(bomitem, False, False)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert len(res.releases) == 1

        # CaPyCli parameter --all set
        self.app.no_match_by_name_only = False
        res = self.app.map_bom_item(bomitem, False, False)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert len(res.releases) == 1

        self.app.releases = [{"Id": "1111", "ComponentId": "b001",
                              "Name": "mail", "Version": "1.0",
                              "ExternalIds": {}},
                             {"Id": "1112", "ComponentId": "b002",
                              "Name": "Mail", "Version": "1.4",
                              "ExternalIds": {}}]

        self.app.no_match_by_name_only = True
        res = self.app.map_bom_item(bomitem, False, False)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert len(res.releases) == 1

        # CaPyCli parameter --all set
        self.app.no_match_by_name_only = False
        res = self.app.map_bom_item(bomitem, False, False)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert len(res.releases) == 1

        bomitem.version = "1.2"

        self.app.no_match_by_name_only = True
        res = self.app.map_bom_item(bomitem, False, False)
        assert res.result == MapResult.NO_MATCH
        assert len(res.releases) == 0

        # CaPyCli parameter --all set
        self.app.no_match_by_name_only = False
        res = self.app.map_bom_item(bomitem, False, False)
        assert res.result == MapResult.MATCH_BY_NAME
        assert len(res.releases) == 2

    @responses.activate
    def test_map_bom_item_mixed_match_similar(self) -> None:
        """test mixed match with name match and similar name match"""
        bomitem = Component(
            name="mail-filter",
            version="1.4")

        # first components with similar names, then the (better) name match
        self.app.releases = [{"Id": "1111", "ComponentId": "b001",
                              "Name": "mail_Filter", "Version": "1.1",
                              "ExternalIds": {}},
                             {"Id": "1112", "ComponentId": "b002",
                              "Name": "Mail filter", "Version": "1.0",
                              "ExternalIds": {}},
                             {"Id": "1113", "ComponentId": "b003",
                              "Name": "Mail-Filter", "Version": "1.2",
                              "ExternalIds": {}}]

        self.app.no_match_by_name_only = True  # default
        res = self.app.map_bom_item(bomitem, check_similar=True, result_required=False)
        assert res.result == MapResult.SIMILAR_COMPONENT_FOUND
        assert len(res.releases) == 2

        self.app.no_match_by_name_only = False  # CaPyCli parameter --all set
        res = self.app.map_bom_item(bomitem, check_similar=True, result_required=False)
        assert res.result == MapResult.MATCH_BY_NAME
        assert len(res.releases) == 1

        # reverse order, now better match comes first
        self.app.releases = self.app.releases[::-1]

        self.app.no_match_by_name_only = False  # CaPyCli parameter --all set
        res = self.app.map_bom_item(bomitem, check_similar=True, result_required=False)
        assert res.result == MapResult.MATCH_BY_NAME
        assert len(res.releases) == 1

    # ---------------------- map_bom_item_no_cache ----------------------

    @responses.activate
    def test_map_bom_item_nocache_full_match_name_version(self) -> None:
        bomitem = Component(
            name="awk",
            version="1.0")

        component_matches = {"_embedded": {"sw360:components": [{
            "name": "Awk",
            "_links": {"self": {"href": SW360_BASE_URL + 'components/a034'}}}]}}
        component_data = {"_embedded": {"sw360:releases": [{
            "_links": {"self": {"href": SW360_BASE_URL + 'releases/1235'}}}]}}
        release_data = {"name": "awk",
                        "version": "1.0",
                        "_links": {
                            "self": {"href": SW360_BASE_URL + 'releases/1235'},
                            "sw360:component": {"href": SW360_BASE_URL + "components/a034"}}}
        responses.add(responses.GET,
                      SW360_BASE_URL + 'components/a034',
                      json=component_data)
        responses.add(responses.GET,
                      SW360_BASE_URL + 'components?name=awk',
                      json=component_matches)
        responses.add(responses.GET,
                      SW360_BASE_URL + 'releases/1235',
                      json=release_data)

        res = self.app.map_bom_item_no_cache(bomitem)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert res.releases[0]["Sw360Id"] == "1235"

    @responses.activate
    def test_map_bom_item_nocache_mixed_match(self) -> None:
        bomitem = Component(
            name="mail",
            version="1.4")
        component_matches = {"_embedded": {"sw360:components": [
            {"name": "mail",
             "_links": {"self": {"href": SW360_BASE_URL + 'components/b001'}}},
            {"name": "Mail",
             "_links": {"self": {"href": SW360_BASE_URL + 'components/b002'}}}]}}
        component_data1 = {"_embedded": {"sw360:releases": [{
            "_links": {"self": {"href": SW360_BASE_URL + 'releases/1111'}}}]}}
        component_data2 = {"_embedded": {"sw360:releases": [{
            "_links": {"self": {"href": SW360_BASE_URL + 'releases/1112'}}}]}}
        release_data1 = {"name": "mail", "version": "1.4", "_links": {
            "self": {"href": SW360_BASE_URL + 'releases/1111'},
            "sw360:component": {"href": SW360_BASE_URL + "components/b001"}}}
        release_data2 = {"name": "Mail", "version": "1.0", "_links": {
            "self": {"href": SW360_BASE_URL + 'releases/1112'},
            "sw360:component": {"href": SW360_BASE_URL + "components/b002"}}}
        responses.add(responses.GET, SW360_BASE_URL + 'components?name=mail',
                      json=component_matches)
        responses.add(responses.GET, SW360_BASE_URL + 'components/b001',
                      json=component_data1)
        responses.add(responses.GET, SW360_BASE_URL + 'components/b002',
                      json=component_data2)
        responses.add(responses.GET, SW360_BASE_URL + 'releases/1111',
                      json=release_data1)
        responses.add(responses.GET, SW360_BASE_URL + 'releases/1112',
                      json=release_data2)

        self.app.no_match_by_name_only = True  # default
        res = self.app.map_bom_item_no_cache(bomitem)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert len(res.releases) == 1

        self.app.no_match_by_name_only = False  # CaPyCli parameter --all set
        res = self.app.map_bom_item_no_cache(bomitem)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert len(res.releases) == 1

        component_matches = {"_embedded": {"sw360:components": [
            {"name": "Mail",
             "_links": {"self": {"href": SW360_BASE_URL + 'components/b002'}}},
            {"name": "mail",
             "_links": {"self": {"href": SW360_BASE_URL + 'components/b001'}}}]}}
        responses.replace(responses.GET, SW360_BASE_URL + 'components?name=mail',
                          json=component_matches)
        res = self.app.map_bom_item_no_cache(bomitem)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert len(res.releases) == 1

    @responses.activate
    def test_map_bom_item_nocache_invalid_version(self) -> None:
        bomitem = Component(
            name="mail",
            version="1.4")
        component_matches = {"_embedded": {"sw360:components": [
            {"name": "mail",
             "_links": {"self": {"href": SW360_BASE_URL + 'components/b001'}}}]}}
        component_data1 = {"_embedded": {"sw360:releases": [
            {"version": "1.4",
             "_links": {"self": {"href": SW360_BASE_URL + 'releases/1111'}}},
            {"version": "1.0._ME-2",
             "_links": {"self": {"href": SW360_BASE_URL + 'releases/1112'}}}]}}
        release_data1 = {"name": "mail", "version": "1.4", "_links": {
            "self": {"href": SW360_BASE_URL + 'releases/1111'},
            "sw360:component": {"href": SW360_BASE_URL + "components/b001"}}}
        release_data2 = {"name": "Mail", "version": "1.0._ME-2", "_links": {
            "self": {"href": SW360_BASE_URL + 'releases/1112'},
            "sw360:component": {"href": SW360_BASE_URL + "components/b002"}}}
        responses.add(responses.GET, SW360_BASE_URL + 'components?name=mail',
                      json=component_matches)
        responses.add(responses.GET, SW360_BASE_URL + 'components/b001',
                      json=component_data1)
        responses.add(responses.GET, SW360_BASE_URL + 'releases/1111',
                      json=release_data1)
        responses.add(responses.GET, SW360_BASE_URL + 'releases/1112',
                      json=release_data2)

        res = self.app.map_bom_item_no_cache(bomitem)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert len(res.releases) == 1

    # ----------------- map_bom_item_no_cache purl cases --------------------

    @responses.activate
    def test_map_bom_item_nocache_purl_component(self) -> None:
        """test bom mapping (nocache): we have a component purl match
        """
        if not self.app.client:
            return

        self.app.purl_service = PurlService(self.app.client, cache={'deb': {'debian': {'sed': {
            None: [{
                "purl": PackageURL("deb", "debian", "sed"),
                "href": SW360_BASE_URL + "components/a035"}]}}}})
        bomitem = Component(
            name="sed",
            version="1.0",
            purl=PackageURL.from_string("pkg:deb/debian/sed@1.0?type=source"))
        component_data = {"_embedded": {"sw360:releases": [{
            "_links": {"self": {"href": SW360_BASE_URL + 'releases/1234'}}}]}}
        release_data = {"name": "Unix Stream EDitor",
                        "version": "1.0", "_links": {
                            "self": {"href": SW360_BASE_URL + 'releases/1234'},
                            "sw360:component": {"href": SW360_BASE_URL + "components/a035"}}}

        responses.add(responses.GET,
                      SW360_BASE_URL + 'components/a035',
                      json=component_data)
        responses.add(responses.GET,
                      SW360_BASE_URL + 'releases/1234',
                      json=release_data)

        # component found by PURL, version match by string comparison
        res = self.app.map_bom_item_no_cache(bomitem)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert res.component_hrefs[0] == SW360_BASE_URL + "components/a035"
        assert res.releases[0]["Sw360Id"] == "1234"
        assert res.releases[0]["ComponentId"] == "a035"

        # component found by PURL, but version does not match
        bomitem = Component(
            name="sed",
            version="1.1",
            purl=PackageURL.from_string("pkg:deb/debian/sed@1.1?type=source"))
        res = self.app.map_bom_item_no_cache(bomitem)
        assert res.result == MapResult.NO_MATCH
        assert res.component_hrefs[0] == SW360_BASE_URL + "components/a035"
        assert res.input_component is not None
        assert (
            CycloneDxSupport.get_property(res.input_component, CycloneDxSupport.CDX_PROP_COMPONENT_ID).value
            == "a035")
        assert len(res.releases) == 0

        # enable name matching, so all versions shall be listed
        self.app.no_match_by_name_only = False
        res = self.app.map_bom_item_no_cache(bomitem)
        assert res.result == MapResult.MATCH_BY_NAME
        assert res.component_hrefs[0] == SW360_BASE_URL + "components/a035"
        assert res.input_component is not None
        assert (
            CycloneDxSupport.get_property(res.input_component, CycloneDxSupport.CDX_PROP_COMPONENT_ID).value
            == "a035")
        assert res.releases[0]["ComponentId"] == "a035"
        assert len(res.releases) == 1

    @responses.activate
    def test_map_bom_item_nocache_purl_nocomponent(self) -> None:
        """test bom mapping: we have no component purl match, so search by name
        """
        if not self.app.client:
            return

        self.app.purl_service = PurlService(self.app.client, cache={'deb': {'debian': {'sed': {
            None: SW360_BASE_URL + "components/a035"}}}})
        bomitem = Component(
            name="awk",
            version="1.0",
            purl=PackageURL.from_string("pkg:deb/debian/awk@1.0?type=source"))

        component_matches = {"_embedded": {"sw360:components": [{
            "name": "Awk",
            "_links": {"self": {"href": SW360_BASE_URL + 'components/a034'}}}]}}
        component_data = {"_embedded": {"sw360:releases": [{
            "_links": {"self": {"href": SW360_BASE_URL + 'releases/1235'}}}]}}
        release_data = {"name": "awk",
                        "version": "1.0", "_links": {
                            "self": {"href": SW360_BASE_URL + 'releases/1235'},
                            "sw360:component": {"href": SW360_BASE_URL + "components/a034"}}}
        responses.add(responses.GET,
                      SW360_BASE_URL + 'components/a034',
                      json=component_data)
        responses.add(responses.GET,
                      SW360_BASE_URL + 'components?name=awk',
                      json=component_matches)
        responses.add(responses.GET,
                      SW360_BASE_URL + 'releases/1235',
                      json=release_data)

        res = self.app.map_bom_item_no_cache(bomitem)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert res.component_hrefs == []
        assert res.input_component is not None
        assert CycloneDxSupport.get_property(res.input_component, CycloneDxSupport.CDX_PROP_COMPONENT_ID) is None
        assert res.releases[0]["Sw360Id"] == "1235"
        assert res.releases[0]["ComponentId"] == "a034"

    @responses.activate
    def test_map_bom_item_nocache_purl_component_release_conflict(self) -> None:
        """test bom mapping (nocache): we have two releases for other versions
        with PURLs pointing to different components, no direct purl match for release
        """
        if not self.app.client:
            return
        self.app.purl_service = PurlService(self.app.client, cache={'maven': {
            'com.fasterxml.jackson.core': {'jackson-core': {
                "2.18.0": [{
                    "purl": PackageURL("maven", "com.fasterxml.jackson.core", "jackson-core", version="2.18.0"),
                    "href": SW360_BASE_URL + "releases/1234"}],
                "2.5.0": [{
                    "purl": PackageURL("maven", "com.fasterxml.jackson.core", "jackson-core", version="2.5.0"),
                    "href": SW360_BASE_URL + "releases/1235"}]}}}})
        bomitem = Component(
            name="jackson-core",
            version="2.17.0",
            purl=PackageURL.from_string("pkg:maven/com.fasterxml.jackson.core/jackson-core@2.17.0"))

        component_data1 = {"_embedded": {"sw360:releases": [{
            "_links": {"self": {"href": SW360_BASE_URL + 'releases/1234'}}}]}}
        component_data2 = {"_embedded": {"sw360:releases": [
            {"_links": {"self": {"href": SW360_BASE_URL + 'releases/1235'}}},
            {"_links": {"self": {"href": SW360_BASE_URL + 'releases/1236'}}}]}}
        release_data1 = {"name": "Jackson Core", "version": "2.18.0", "_links": {
                         "self": {"href": SW360_BASE_URL + 'releases/1234'},
                         "sw360:component": {"href": SW360_BASE_URL + "components/a035"}}}
        release_data2 = {"name": "com.fasterxml.jackson.core:jackson-core", "version": "2.5.0", "_links": {
                         "self": {"href": SW360_BASE_URL + 'releases/1235'},
                         "sw360:component": {"href": SW360_BASE_URL + "components/a034"}}}
        release_data3 = {"name": "com.fasterxml.jackson.core:jackson-core", "version": "2.17.0", "_links": {
                         "self": {"href": SW360_BASE_URL + 'releases/1236'},
                         "sw360:component": {"href": SW360_BASE_URL + "components/a034"}}}
        responses.add(responses.GET, SW360_BASE_URL + 'components/a035', json=component_data1)
        responses.add(responses.GET, SW360_BASE_URL + 'components/a034', json=component_data2)
        responses.add(responses.GET, SW360_BASE_URL + 'releases/1234', json=release_data1)
        responses.add(responses.GET, SW360_BASE_URL + 'releases/1235', json=release_data2)
        responses.add(responses.GET, SW360_BASE_URL + 'releases/1236', json=release_data3)

        res = self.app.map_bom_item_no_cache(bomitem)
        assert res.result == MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        assert res.releases[0]["Sw360Id"] == "1236"
        assert res.releases[0]["ComponentId"] == "a034"
        assert len(res.releases) == 1
        assert res.input_component is not None
        assert (
            CycloneDxSupport.get_property(res.input_component, CycloneDxSupport.CDX_PROP_COMPONENT_ID)
            is None)

    @responses.activate
    def test_map_bom_item_nocache_purl_release(self) -> None:
        """test bom mapping: we have a release purl match, but names differ
        """
        if not self.app.client:
            return

        self.app.purl_service = PurlService(self.app.client, cache={'deb': {'debian': {'sed': {
            None: [{
                "purl": PackageURL("deb", "debian", "sed"),
                "href": SW360_BASE_URL + "components/a035"}],
            "1.0~1": [{
                "purl": PackageURL("deb", "debian", "sed", version="1.0~1"),
                "href": SW360_BASE_URL + "releases/1234"}]}}}})
        bomitem = Component(
            name="sed",
            version="1.0+1",
            purl=PackageURL.from_string("pkg:deb/debian/sed@1.0%7E1?type=source"))

        release_data = {"name": "Unix Stream EDitor",
                        "version": "1.0", "_links": {
                            "self": {"href": SW360_BASE_URL + 'releases/1234'},
                            "sw360:component": {"href": SW360_BASE_URL + "components/a035"}}}
        responses.add(responses.GET,
                      SW360_BASE_URL + 'releases/1234',
                      json=release_data)

        res = self.app.map_bom_item_no_cache(bomitem)
        assert res.result == MapResult.FULL_MATCH_BY_ID
        assert res.component_hrefs[0] == SW360_BASE_URL + "components/a035"
        assert res.release_hrefs[0] == SW360_BASE_URL + "releases/1234"
        assert res.input_component is not None
        assert (
            CycloneDxSupport.get_property(res.input_component, CycloneDxSupport.CDX_PROP_COMPONENT_ID).value
            == "a035")
        assert (
            CycloneDxSupport.get_property(res.input_component, CycloneDxSupport.CDX_PROP_SW360ID).value
            == "1234")
        assert len(res.releases) == 1
        assert res.releases[0]["Sw360Id"] == "1234"
        assert res.releases[0]["ComponentId"] == "a035"

    # ----------------- create_updated_bom --------------------

    @responses.activate
    def test_create_updated_bom_component_id(self) -> None:
        res = MapResult()
        res.input_component = Component(name="sed", version="1.1")
        res.result = MapResult.MATCH_BY_NAME
        res.component_hrefs = [SW360_BASE_URL + "components/a035"]
        res.releases = [{'Name': 'sed', 'Version': '1.0',
                         'Id': '1234', 'MapResult': MapResult.MATCH_BY_NAME}]
        oldbom = Bom()
        newbom = self.app.create_updated_bom(oldbom, [res])
        assert 2 == len(newbom.components)

        # note that the result CycloneDX SBOM has ordered components
        # first entry is the name match
        assert "sed" == newbom.components[0].name
        assert "1.0" == newbom.components[0].version
        prop = CycloneDxSupport.get_property_value(newbom.components[0], CycloneDxSupport.CDX_PROP_MAPRESULT)
        assert prop == MapResult.MATCH_BY_NAME
        prop = CycloneDxSupport.get_property_value(newbom.components[0], CycloneDxSupport.CDX_PROP_COMPONENT_ID)
        assert prop == ""

        # second entry is the input_component we were looking for
        assert "sed" == newbom.components[1].name
        assert "1.1" == newbom.components[1].version
        prop = CycloneDxSupport.get_property_value(newbom.components[1], CycloneDxSupport.CDX_PROP_MAPRESULT)
        assert prop == MapResult.NO_MATCH
        prop = CycloneDxSupport.get_property_value(newbom.components[1], CycloneDxSupport.CDX_PROP_COMPONENT_ID)
        assert prop == "a035"

        # we have component PURL conflict, two components with same PURL
        res.component_hrefs = [SW360_BASE_URL + "components/a035", SW360_BASE_URL + "components/1234"]
        oldbom = Bom()
        newbom = self.app.create_updated_bom(oldbom, [res])
        assert 2 == len(newbom.components)
        prop = CycloneDxSupport.get_property_value(newbom.components[1], CycloneDxSupport.CDX_PROP_COMPONENT_ID)
        assert prop == ""

        res.result = MapResult.NO_MATCH
        res.component_hrefs = [SW360_BASE_URL + "components/a035"]
        res.releases = []
        newbom = self.app.create_updated_bom(oldbom, [res])
        prop = CycloneDxSupport.get_property_value(newbom.components[0], CycloneDxSupport.CDX_PROP_MAPRESULT)
        assert prop == MapResult.NO_MATCH
        prop = CycloneDxSupport.get_property_value(newbom.components[0], CycloneDxSupport.CDX_PROP_COMPONENT_ID)
        assert prop == "a035"

    @responses.activate
    def test_create_updated_bom_mixed_match(self) -> None:
        res = MapResult()
        res.input_component = Component(name="mail", version="1.4")
        res.result = MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        res.releases = [
            {'Name': 'mail', 'Version': '1.4',
             'Id': '1111', 'MapResult': MapResult.FULL_MATCH_BY_NAME_AND_VERSION},
            {'Name': 'Mail', 'Version': '1.0',
             'Id': '1112', 'MapResult': MapResult.MATCH_BY_NAME}]
        oldbom = Bom()
        newbom = self.app.create_updated_bom(oldbom, [res])

        # note that the result CycloneDX SBOM has ordered components
        assert newbom.components[0].name == "Mail"
        assert newbom.components[0].version == "1.0"
        prop = CycloneDxSupport.get_property_value(newbom.components[0], CycloneDxSupport.CDX_PROP_MAPRESULT)
        assert prop == MapResult.MATCH_BY_NAME

        assert newbom.components[1].name == "mail"
        assert newbom.components[1].version == "1.4"
        prop = CycloneDxSupport.get_property_value(newbom.components[1], CycloneDxSupport.CDX_PROP_MAPRESULT)
        assert prop == MapResult.FULL_MATCH_BY_NAME_AND_VERSION

    # ----------------- basic tests --------------------

    def test_show_help(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.help = True

        out = TestBase.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCLI bom map [-h]" in out)

    def test_app_bom_no_input_file_specified(self) -> None:
        db = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, sysex.code)

    def test_app_bom_input_file_not_found(self) -> None:
        db = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        args.inputfile = "DOESNOTEXIST"
        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, sysex.code)

    def test_app_bom_input_file_invalid(self) -> None:
        db = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_INVALID)
        args.outputfile = self.OUTPUTFILE
        args.dbx = True
        args.debug = True
        args.verbose = True

        try:
            db.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, sysex.code)

    @responses.activate
    def test_no_login(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.sw360_url = "https://my.server.com"
        args.dbx = True
        args.debug = True
        args.verbose = True
        args.nocache = True

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_AUTH_ERROR, ex.code)

    @responses.activate
    def test_mapping_single_match_by_id(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.dbx = True
        args.debug = True
        args.verbose = True
        args.nocache = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL

        # for login
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'ok'}",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # purl cache: components
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/components/searchByExternalIds?package-url=",
            body="""
            {
                "_embedded": {
                    "sw360:components": [
                        {
                            "type": "component",
                            "name": "colorama",
                            "componentType": "OSS",
                            "visibility": "EVERYONE",
                            "externalIds": {
                                "package-url": "pkg:pypi/colorama"
                            },
                            "setBusinessUnit": false,
                            "setVisbility": true,
                            "_links": {
                                "self": {
                                    "href": "https://my.server.com/resource/api/components/678dstzd8"
                                }
                            }
                        }
                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # purl cache: releases
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/searchByExternalIds?package-url=",
            body="""
            {
                "_embedded": {
                    "sw360:releases": [
                        {
                            "type": "release",
                            "name": "colorama",
                            "version": "0.4.3",
                            "componentId" : "678dstzd8",
                            "externalIds" : {
                                "package-url" : "pkg:pypi/colorama@0.4.3"
                            },
                            "_links": {
                                "self": {
                                    "href": "https://my.server.com/resource/api/releases/3765276512"
                                }
                            }
                        }
                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.3",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "externalIds" : {
                    "package-url" : "pkg:pypi/colorama@0.4.3"
                },
                "_links": {
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    },
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    }
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = TestBase.capture_stdout(sut.run, args)
        # TestBase.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Using relaxed debian version checks" in out)
        self.assertTrue("1 component read from SBOM" in out)
        self.assertTrue("Retrieving package-url ids, filter: {'pypi'}" in out)
        self.assertTrue("Found 2 total purls" in out)
        self.assertTrue("Found component 678dstzd8 via purl" in out)
        self.assertTrue("ADDED (1-full-match-by-id) 3765276512" in out)
        self.assertTrue("Full matches    = 1" in out)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("COMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual("1-full-match-by-id", data["Details"][0]["ResultCode"])
        self.assertEqual("Full match by id", data["Details"][0]["ResultText"])

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)

    @responses.activate
    def test_mapping_multiple_match_by_id(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.debug = True
        args.verbose = True
        args.nocache = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL

        # for login
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'ok'}",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # purl cache: components
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/components/searchByExternalIds?package-url=",
            body="""
            {
                "_embedded": {
                    "sw360:components": [
                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # purl cache: releases
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/searchByExternalIds?package-url=",
            body="""
            {
                "_embedded": {
                    "sw360:releases": [
                        {
                            "type": "release",
                            "name": "colorama",
                            "version": "0.4.3",
                            "componentId" : "678dstzd8",
                            "externalIds" : {
                                "package-url" : "pkg:pypi/colorama@0.4.3"
                            },
                            "_links": {
                                "self": {
                                    "href": "https://my.server.com/resource/api/releases/3765276512"
                                }
                            }
                        },
                        {
                            "type": "release",
                            "name": "python-colorama",
                            "version": "0.4.3",
                            "componentId" : "12345678",
                            "externalIds" : {
                                "package-url" : "pkg:pypi/colorama@0.4.3"
                            },
                            "_links": {
                                "self": {
                                    "href": "https://my.server.com/resource/api/releases/1234"
                                }
                            }
                        }

                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.3",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "externalIds" : {
                    "package-url" : "pkg:pypi/colorama@0.4.3"
                },
                "_links": {
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    },
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    }
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/1234",
            body="""
            {
                "name": "python-colorama",
                "version": "0.4.3",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "12345678",
                "externalIds" : {
                    "package-url" : "pkg:pypi/colorama@0.4.3"
                },
                "_links": {
                    "self": {
                        "href": "https://my.server.com/api/releases/1234"
                    },
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/12345678"
                    }
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = TestBase.capture_stdout(sut.run, args)
        assert "1 component read from SBOM" in out
        assert "Retrieving package-url ids, filter: {'pypi'}" in out
        assert ("ADDED (1-full-match-by-id) 3765276512" in out
                or "ADDED (1-full-match-by-id) 1234" in out)
        assert "Release 3765276512 with purl pkg:pypi/colorama@0.4.3 points to component 678dstzd8" in out
        assert "Release 1234 with purl pkg:pypi/colorama@0.4.3 points to component 12345678" in out
        assert "Candidate 3765276512 has purl pkg:pypi/colorama@0.4.3" in out
        assert "Candidate 1234 has purl pkg:pypi/colorama@0.4.3" in out

        # check result BOM
        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE)
        assert sbom is not None
        assert len(sbom.components) == 1
        assert sbom.components[0].version == "0.4.3"
        prop = CycloneDxSupport.get_property_value(sbom.components[0], CycloneDxSupport.CDX_PROP_MAPRESULT)
        assert prop == MapResult.FULL_MATCH_BY_ID
        prop = CycloneDxSupport.get_property_value(sbom.components[0], CycloneDxSupport.CDX_PROP_COMPONENT_ID)
        if prop == "678dstzd8":
            prop = CycloneDxSupport.get_property_value(sbom.components[0], CycloneDxSupport.CDX_PROP_SW360ID)
            assert prop == "3765276512"
        elif prop == "12345678":
            prop = CycloneDxSupport.get_property_value(sbom.components[0], CycloneDxSupport.CDX_PROP_SW360ID)
            assert prop == "1234"
        else:
            assert False, "Unexpected component id: " + prop

        TestBase.delete_file(self.OUTPUTFILE)

    def provide_cache_responses(self) -> None:
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases?allDetails=true",
            body="""
            {
                "_embedded": {
                    "sw360:releases": [
                        {
                            "name": "colorama",
                            "version": "0.4.3",
                            "releaseDate" : "2016-12-07",
                            "componentId" : "678dstzd8",
                            "componentType" : "OSS",
                            "externalIds" : {
                                "package-url" : "pkg:pypi/colorama@0.4.3"
                            },
                            "createdOn" : "2016-12-18",
                            "mainlineState" : "SPECIFIC",
                            "clearingState" : "APPROVED",
                            "cpeId": "007",
                            "_links": {
                                "sw360:component" : {
                                    "href" : "https://sw360.org/api/components/17653524"
                                },
                                "self": {
                                    "href": "https://my.server.com/resource/api/releases/3765276512"
                                }
                            },
                            "_embedded" : {
                                "sw360:attachments" : [ [ {
                                    "filename" : "spring-core-4.3.4.RELEASE.jar",
                                    "sha1" : "da373e491d3863477568896089ee9457bc316783",
                                    "attachmentType" : "BINARY",
                                    "createdBy" : "admin@sw360.org",
                                    "createdTeam" : "Clearing Team 1",
                                    "createdComment" : "please check asap",
                                    "createdOn" : "2016-12-18",
                                    "checkedTeam" : "Clearing Team 2",
                                    "checkedComment" : "everything looks good",
                                    "checkedOn" : "2016-12-18",
                                    "checkStatus" : "ACCEPTED"
                                    }, {
                                    "filename" : "spring-core-4.3.4.zip",
                                    "sha1" : "da373e491d3863477568896089ee9457bc316799",
                                    "attachmentType" : "SOURCE",
                                    "createdBy" : "admin@sw360.org",
                                    "createdTeam" : "Clearing Team 1",
                                    "createdComment" : "please check asap",
                                    "createdOn" : "2016-12-18",
                                    "checkedTeam" : "Clearing Team 2",
                                    "checkedComment" : "everything looks good",
                                    "checkedOn" : "2016-12-18",
                                    "checkStatus" : "ACCEPTED"
                                    } ] ]
                            }
                        }
                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

    @responses.activate
    def test_mapping_use_cache(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.dbx = True
        args.debug = True
        args.verbose = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.cachefile = self.CACHE_FILE
        args.refresh_cache = True

        # for login
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'ok'}",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # component cache
        self.provide_cache_responses()

        # purl cache: components
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/components/searchByExternalIds?package-url=",
            body="""
            {
                "_embedded": {
                    "sw360:components": [
                        {
                            "type": "component",
                            "name": "colorama",
                            "componentType": "OSS",
                            "visibility": "EVERYONE",
                            "externalIds": {
                                "package-url": "pkg:pypi/colorama"
                            },
                            "setBusinessUnit": false,
                            "setVisbility": true,
                            "_links": {
                                "self": {
                                    "href": "https://my.server.com/resource/api/components/678dstzd8"
                                }
                            }
                        }
                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # purl cache: releases
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/searchByExternalIds?package-url=",
            body="""
            {
                "_embedded": {
                    "sw360:releases": [
                        {
                            "type": "release",
                            "name": "colorama",
                            "version": "0.4.3",
                            "componentId" : "678dstzd8",
                            "externalIds" : {
                                "package-url" : "pkg:pypi/colorama@0.4.3"
                            },
                            "_links": {
                                "self": {
                                    "href": "https://my.server.com/resource/api/releases/3765276512"
                                }
                            }
                        }
                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.3",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "externalIds" : {
                    "package-url" : "pkg:pypi/colorama@0.4.3"
                },
                "_links": {
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    }
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = TestBase.capture_stdout(sut.run, args)
        # TestBase.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Using relaxed debian version checks" in out)
        self.assertTrue("1 component read from SBOM" in out)
        self.assertTrue("Retrieving package-url ids, filter: {'pypi'}" in out)
        self.assertTrue("Found 2 total purls" in out)
        self.assertTrue("Found component 678dstzd8 via purl" in out)
        self.assertTrue("ADDED (1-full-match-by-id) 3765276512" in out)
        self.assertTrue("Full matches    = 1" in out)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("COMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual("1-full-match-by-id", data["Details"][0]["ResultCode"])
        self.assertEqual("Full match by id", data["Details"][0]["ResultText"])

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)
        TestBase.delete_file(self.CACHE_FILE)

    @responses.activate
    def test_mapping_no_releases(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.cachefile = self.CACHE_FILE
        args.refresh_cache = True

        # for login
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'ok'}",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # component cache
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases?allDetails=true",
            body="""
            {
                "_embedded": {
                    "sw360:releases": []
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # purl cache: components
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/components/searchByExternalIds?package-url=",
            body="""
            {
                "_embedded": {
                    "sw360:components": []
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # purl cache: releases
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/searchByExternalIds?package-url=",
            body="""
            {
                "_embedded": {
                    "sw360:releases": []
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            sut.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_NO_CACHED_RELEASES, sysex.code)

        TestBase.delete_file(self.CACHE_FILE)

    @responses.activate
    def test_mapping_no_releases_no_cache(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.nocache = True

        # for login
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'ok'}",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # component cache: empty
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases?allDetails=true",
            body="""
            {
                "_embedded": {
                    "sw360:releases": []
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # purl cache: components: empty
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/components/searchByExternalIds?package-url=",
            body="""
            {
                "_embedded": {
                    "sw360:components": []
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # purl cache: releases: empty
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/searchByExternalIds?package-url=",
            body="""
            {
                "_embedded": {
                    "sw360:releases": []
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # component(s) by name
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/components?name=colorama",
            body="""
            {
                "_embedded": {
                    "sw360:components": [
                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            sut.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_NO_UNIQUE_MAPPING, sysex.code)

    def add_login_response(self) -> None:
        """
        Add response for SW360 login.
        """
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'ok'}",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

    def add_empty_purl_cache_response(self) -> None:
        """
        Add responses for empty purl cache.
        """
        # purl cache: components
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/components/searchByExternalIds?package-url=",
            body="""
            {
                "_embedded": {
                    "sw360:components": [ ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # purl cache: releases
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/searchByExternalIds?package-url=",
            body="""
            {
                "_embedded": {
                    "sw360:releases": [ ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

    def add_component_per_name_colorama_response(self) -> None:
        # component(s) by name
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/components?name=colorama",
            body="""
            {
                "_embedded": {
                    "sw360:components": [
                        {
                            "type": "component",
                            "name": "colorama",
                            "componentType": "OSS",
                            "visibility": "EVERYONE",
                            "externalIds": {
                                "package-url": "pkg:pypi/colorama"
                            },
                            "setBusinessUnit": false,
                            "setVisbility": true,
                            "_links": {
                                "self": {
                                    "href": "https://my.server.com/resource/api/components/678dstzd8"
                                }
                            }
                        }
                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

    def add_component_colorama_response(self) -> None:
        # the component
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/components/678dstzd8",
            body="""
            {
                "name": "colorama",
                "componentType": "OSS",
                "visibility": "EVERYONE",
                "externalIds": {
                    "package-url": "pkg:pypi/colorama"
                },
                "setBusinessUnit": false,
                "setVisbility": true,
                "_links": {
                    "self": {
                        "href": "https://my.server.com/resource/api/components/678dstzd8"
                    }
                },
                "_embedded" : {
                    "sw360:releases" : [{
                        "name" : "colorama",
                        "version" : "0.4.3",
                        "_links" : {
                            "self" : {
                            "href" : "https://my.server.com/resource/api/releases/3765276512"
                            }
                        }
                    }]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

    @responses.activate
    def test_mapping_name_and_version(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.nocache = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL

        # for login
        self.add_login_response()

        # purl cache
        self.add_empty_purl_cache_response()

        self.add_component_per_name_colorama_response()

        self.add_component_colorama_response()

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.3",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "_links": {
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    },
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    }
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = TestBase.capture_stdout(sut.run, args)
        # TestBase.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("1 component read from SBOM" in out)
        self.assertTrue("Retrieving package-url ids, filter: {'pypi'}" in out)
        self.assertTrue("Found 0 total purls" in out)
        self.assertTrue("ADDED (3-full-match-by-name-and-version) 3765276512" in out)
        self.assertTrue("Full matches    = 1" in out)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("COMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual("3-full-match-by-name-and-version", data["Details"][0]["ResultCode"])
        self.assertEqual("Full match by name and version", data["Details"][0]["ResultText"])

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)

    @responses.activate
    def test_mapping_source_hash(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.nocache = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL

        # for login
        self.add_login_response()

        # purl cache
        self.add_empty_purl_cache_response()

        self.add_component_per_name_colorama_response()

        self.add_component_colorama_response()

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.33",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "_links": {
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    },
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    }
                },
                "_embedded" : {
                    "sw360:attachments" : [ [ {
                        "filename" : "spring-core-4.3.4.RELEASE.jar",
                        "sha1" : "e5d6a5f36e831d4258424848ff635dc931f6d77e",
                        "attachmentType" : "SOURCE",
                        "_links" : {
                            "self" : {
                            "href" : "https://sw360.org/api/attachments/1231231254"
                            }
                        }
                    }] ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = TestBase.capture_stdout(sut.run, args)
        # TestBase.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("1 component read from SBOM" in out)
        self.assertTrue("Retrieving package-url ids, filter: {'pypi'}" in out)
        self.assertTrue("Found 0 total purls" in out)
        self.assertTrue("ADDED (2-full-match-by-hash) 3765276512" in out)
        self.assertTrue("Full matches    = 1" in out)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("COMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual("2-full-match-by-hash", data["Details"][0]["ResultCode"])
        self.assertEqual("Full match by hash", data["Details"][0]["ResultText"])

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)

    @responses.activate
    def test_mapping_binary_hash(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.nocache = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL

        # for login
        self.add_login_response()

        # purl cache
        self.add_empty_purl_cache_response()

        self.add_component_per_name_colorama_response()

        self.add_component_colorama_response()

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.33",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "_links": {
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    },
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    }
                },
                "_embedded" : {
                    "sw360:attachments" : [ [ {
                        "filename" : "spring-core-4.3.4.RELEASE.jar",
                        "sha1" : "e5d6a5f36e831d4258424848ff635dc931f6d799",
                        "attachmentType" : "BINARY",
                        "_links" : {
                            "self" : {
                            "href" : "https://sw360.org/api/attachments/1231231254"
                            }
                        }
                    }] ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = TestBase.capture_stdout(sut.run, args)
        # TestBase.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("1 component read from SBOM" in out)
        self.assertTrue("Retrieving package-url ids, filter: {'pypi'}" in out)
        self.assertTrue("Found 0 total purls" in out)
        self.assertTrue("ADDED (2-full-match-by-hash) 3765276512" in out)
        self.assertTrue("Full matches    = 1" in out)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("COMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual("2-full-match-by-hash", data["Details"][0]["ResultCode"])
        self.assertEqual("Full match by hash", data["Details"][0]["ResultText"])

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)

    @responses.activate
    def test_mapping_name_only_found(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.nocache = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.mode = MapMode.FOUND
        args.all = True

        # for login
        self.add_login_response()

        # purl cache
        self.add_empty_purl_cache_response()

        self.add_component_per_name_colorama_response()

        self.add_component_colorama_response()

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.33",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "_links": {
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    },
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    }
                },
                "_embedded" : {
                    "sw360:attachments" : []
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            TestBase.capture_stdout(sut.run, args)
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_INCOMPLETE_MAPPING, sysex.code)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("INCOMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual("5-candidate-match-by-name", data["Details"][0]["ResultCode"])
        self.assertEqual("Match by name", data["Details"][0]["ResultText"])

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE)
        self.assertEqual(0, len(sbom.components))

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)

    @responses.activate
    def test_mapping_name_only_not_found(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.nocache = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.mode = MapMode.NOT_FOUND
        args.all = True

        # for login
        self.add_login_response()

        # purl cache
        self.add_empty_purl_cache_response()

        self.add_component_per_name_colorama_response()

        self.add_component_colorama_response()

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.33",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "_links": {
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    },
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    }
                },
                "_embedded" : {
                    "sw360:attachments" : []
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            TestBase.capture_stdout(sut.run, args)
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_INCOMPLETE_MAPPING, sysex.code)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("INCOMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual("5-candidate-match-by-name", data["Details"][0]["ResultCode"])
        self.assertEqual("Match by name", data["Details"][0]["ResultText"])

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE)
        self.assertEqual(2, len(sbom.components))

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)

    @responses.activate
    def test_mapping_require_result_not_found(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.nocache = False
        args.cachefile = self.CACHE_FILE
        args.refresh_cache = True
        args.result_required = True

        # for login
        self.add_login_response()

        # purl cache
        self.add_empty_purl_cache_response()

        self.add_component_per_name_colorama_response()

        self.add_component_colorama_response()

        self.provide_cache_responses()

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.3",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "_links": {
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    },
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    }
                },
                "_embedded" : {
                    "sw360:attachments" : []
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        TestBase.capture_stdout(sut.run, args)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("COMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual("1-full-match-by-id", data["Details"][0]["ResultCode"])
        self.assertEqual("Full match by id", data["Details"][0]["ResultText"])

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE)

        # no result components, because the is no clearing result
        self.assertEqual(0, len(sbom.components))

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)
        TestBase.delete_file(self.CACHE_FILE)

    @responses.activate
    def test_mapping_require_result_found(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.nocache = False
        args.cachefile = self.CACHE_FILE
        args.refresh_cache = True
        args.result_required = True

        # for login
        self.add_login_response()

        # purl cache
        self.add_empty_purl_cache_response()

        self.add_component_per_name_colorama_response()

        self.add_component_colorama_response()

        self.provide_cache_responses()

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.3",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "_links": {
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    },
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    }
                },
                "_embedded" : {
                    "sw360:attachments" : [ [ {
                        "filename" : "some_cli.xml",
                        "sha1" : "da373e491d3863477568896089ee9457bc316783",
                        "attachmentType" : "COMPONENT_LICENSE_INFO_XML",
                        "createdBy" : "admin@sw360.org",
                        "createdTeam" : "Clearing Team 1",
                        "createdComment" : "please check asap",
                        "createdOn" : "2016-12-18",
                        "checkedTeam" : "Clearing Team 2",
                        "checkedComment" : "everything looks good",
                        "checkedOn" : "2016-12-18",
                        "checkStatus" : "ACCEPTED"
                        } ] ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        TestBase.capture_stdout(sut.run, args)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("COMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual("1-full-match-by-id", data["Details"][0]["ResultCode"])
        self.assertEqual("Full match by id", data["Details"][0]["ResultText"])

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE)
        self.assertEqual(1, len(sbom.components))

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)
        TestBase.delete_file(self.CACHE_FILE)

    @responses.activate
    def test_mapping_cache_name_and_version(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.nocache = False
        args.cachefile = self.CACHE_FILE
        args.refresh_cache = True
        args.result_required = True

        # for login
        self.add_login_response()

        # purl cache
        self.add_empty_purl_cache_response()

        self.add_component_per_name_colorama_response()

        self.add_component_colorama_response()

        # component cache
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases?allDetails=true",
            body="""
            {
                "_embedded": {
                    "sw360:releases": [
                        {
                            "name": "colorama",
                            "version": "0.4.3",
                            "releaseDate" : "2016-12-07",
                            "componentId" : "678dstzd8",
                            "componentType" : "OSS",
                            "createdOn" : "2016-12-18",
                            "mainlineState" : "SPECIFIC",
                            "clearingState" : "APPROVED",
                            "cpeId": "007",
                            "_links": {
                                "sw360:component" : {
                                    "href" : "https://sw360.org/api/components/17653524"
                                },
                                "self": {
                                    "href": "https://my.server.com/resource/api/releases/3765276512"
                                }
                            },
                            "_embedded" : {
                                "sw360:attachments" : [ [ {
                                    "filename" : "spring-core-4.3.4.RELEASE.jar",
                                    "sha1" : "da373e491d3863477568896089ee9457bc316783",
                                    "attachmentType" : "BINARY",
                                    "createdBy" : "admin@sw360.org",
                                    "createdTeam" : "Clearing Team 1",
                                    "createdComment" : "please check asap",
                                    "createdOn" : "2016-12-18",
                                    "checkedTeam" : "Clearing Team 2",
                                    "checkedComment" : "everything looks good",
                                    "checkedOn" : "2016-12-18",
                                    "checkStatus" : "ACCEPTED"
                                    }, {
                                    "filename" : "spring-core-4.3.4.zip",
                                    "sha1" : "da373e491d3863477568896089ee9457bc316799",
                                    "attachmentType" : "SOURCE",
                                    "createdBy" : "admin@sw360.org",
                                    "createdTeam" : "Clearing Team 1",
                                    "createdComment" : "please check asap",
                                    "createdOn" : "2016-12-18",
                                    "checkedTeam" : "Clearing Team 2",
                                    "checkedComment" : "everything looks good",
                                    "checkedOn" : "2016-12-18",
                                    "checkStatus" : "ACCEPTED"
                                    } ] ]
                            }
                        }
                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.3",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "_links": {
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    },
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    }
                },
                "_embedded" : {
                    "sw360:attachments" : [ [ {
                        "filename" : "some_cli.xml",
                        "sha1" : "da373e491d3863477568896089ee9457bc316783",
                        "attachmentType" : "COMPONENT_LICENSE_INFO_XML",
                        "createdBy" : "admin@sw360.org",
                        "createdTeam" : "Clearing Team 1",
                        "createdComment" : "please check asap",
                        "createdOn" : "2016-12-18",
                        "checkedTeam" : "Clearing Team 2",
                        "checkedComment" : "everything looks good",
                        "checkedOn" : "2016-12-18",
                        "checkStatus" : "ACCEPTED"
                        } ] ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = TestBase.capture_stdout(sut.run, args)
        # TestBase.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("1 component read from SBOM" in out)
        self.assertTrue("Retrieving package-url ids, filter: {'pypi'}" in out)
        self.assertTrue("Found 0 total purls" in out)
        self.assertTrue("ADDED (3-full-match-by-name-and-version) 3765276512" in out)
        self.assertTrue("Full matches    = 1" in out)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("COMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual("3-full-match-by-name-and-version", data["Details"][0]["ResultCode"])
        self.assertEqual("Full match by name and version", data["Details"][0]["ResultText"])

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE)
        self.assertEqual(1, len(sbom.components))

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)
        TestBase.delete_file(self.CACHE_FILE)

    @responses.activate
    def test_mapping_cache_source_hash(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.nocache = False
        args.cachefile = self.CACHE_FILE
        args.refresh_cache = True
        args.result_required = True

        # for login
        self.add_login_response()

        # purl cache
        self.add_empty_purl_cache_response()

        self.add_component_per_name_colorama_response()

        self.add_component_colorama_response()

        # component cache
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases?allDetails=true",
            body="""
            {
                "_embedded": {
                    "sw360:releases": [
                        {
                            "name": "colorama",
                            "version": "0.4.33",
                            "releaseDate" : "2016-12-07",
                            "componentId" : "678dstzd8",
                            "componentType" : "OSS",
                            "createdOn" : "2016-12-18",
                            "mainlineState" : "SPECIFIC",
                            "clearingState" : "APPROVED",
                            "cpeId": "007",
                            "_links": {
                                "sw360:component" : {
                                    "href" : "https://sw360.org/api/components/17653524"
                                },
                                "self": {
                                    "href": "https://my.server.com/resource/api/releases/3765276512"
                                }
                            },
                            "_embedded" : {
                                "sw360:attachments" : [ [ {
                                    "filename" : "spring-core-4.3.4.zip",
                                    "sha1" : "e5d6a5f36e831d4258424848ff635dc931f6d77e",
                                    "attachmentType" : "SOURCE",
                                    "createdBy" : "admin@sw360.org",
                                    "createdTeam" : "Clearing Team 1",
                                    "createdComment" : "please check asap",
                                    "createdOn" : "2016-12-18",
                                    "checkedTeam" : "Clearing Team 2",
                                    "checkedComment" : "everything looks good",
                                    "checkedOn" : "2016-12-18",
                                    "checkStatus" : "ACCEPTED"
                                    } ] ]
                            }
                        }
                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.3",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "_links": {
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    },
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    }
                },
                "_embedded" : {
                    "sw360:attachments" : [ [ {
                        "filename" : "some_cli.xml",
                        "sha1" : "da373e491d3863477568896089ee9457bc316783",
                        "attachmentType" : "COMPONENT_LICENSE_INFO_XML",
                        "createdBy" : "admin@sw360.org",
                        "createdTeam" : "Clearing Team 1",
                        "createdComment" : "please check asap",
                        "createdOn" : "2016-12-18",
                        "checkedTeam" : "Clearing Team 2",
                        "checkedComment" : "everything looks good",
                        "checkedOn" : "2016-12-18",
                        "checkStatus" : "ACCEPTED"
                        } ] ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = TestBase.capture_stdout(sut.run, args)
        # TestBase.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("1 component read from SBOM" in out)
        self.assertTrue("Retrieving package-url ids, filter: {'pypi'}" in out)
        self.assertTrue("Found 0 total purls" in out)
        self.assertTrue("ADDED (2-full-match-by-hash) 3765276512" in out)
        self.assertTrue("Full matches    = 1" in out)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("COMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual(MapResult.FULL_MATCH_BY_HASH, data["Details"][0]["ResultCode"])
        self.assertEqual("Full match by hash", data["Details"][0]["ResultText"])

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE)
        self.assertEqual(1, len(sbom.components))

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)
        TestBase.delete_file(self.CACHE_FILE)

    @responses.activate
    def test_mapping_cache_binary_hash(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.nocache = False
        args.cachefile = self.CACHE_FILE
        args.refresh_cache = True
        args.result_required = True

        # for login
        self.add_login_response()

        # purl cache
        self.add_empty_purl_cache_response()

        self.add_component_per_name_colorama_response()

        self.add_component_colorama_response()

        # component cache
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases?allDetails=true",
            body="""
            {
                "_embedded": {
                    "sw360:releases": [
                        {
                            "name": "colorama",
                            "version": "0.4.33",
                            "releaseDate" : "2016-12-07",
                            "componentId" : "678dstzd8",
                            "componentType" : "OSS",
                            "createdOn" : "2016-12-18",
                            "mainlineState" : "SPECIFIC",
                            "clearingState" : "APPROVED",
                            "cpeId": "007",
                            "_links": {
                                "sw360:component" : {
                                    "href" : "https://sw360.org/api/components/17653524"
                                },
                                "self": {
                                    "href": "https://my.server.com/resource/api/releases/3765276512"
                                }
                            },
                            "_embedded" : {
                                "sw360:attachments" : [ [ {
                                    "filename" : "spring-core-4.3.4.RELEASE.jar",
                                    "sha1" : "e5d6a5f36e831d4258424848ff635dc931f6d799",
                                    "attachmentType" : "BINARY",
                                    "createdBy" : "admin@sw360.org",
                                    "createdTeam" : "Clearing Team 1",
                                    "createdComment" : "please check asap",
                                    "createdOn" : "2016-12-18",
                                    "checkedTeam" : "Clearing Team 2",
                                    "checkedComment" : "everything looks good",
                                    "checkedOn" : "2016-12-18",
                                    "checkStatus" : "ACCEPTED"
                                    } ] ]
                            }
                        }
                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.3",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "_links": {
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    },
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    }
                },
                "_embedded" : {
                    "sw360:attachments" : [ [ {
                        "filename" : "some_cli.xml",
                        "sha1" : "da373e491d3863477568896089ee9457bc316783",
                        "attachmentType" : "COMPONENT_LICENSE_INFO_XML",
                        "createdBy" : "admin@sw360.org",
                        "createdTeam" : "Clearing Team 1",
                        "createdComment" : "please check asap",
                        "createdOn" : "2016-12-18",
                        "checkedTeam" : "Clearing Team 2",
                        "checkedComment" : "everything looks good",
                        "checkedOn" : "2016-12-18",
                        "checkStatus" : "ACCEPTED"
                        } ] ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = TestBase.capture_stdout(sut.run, args)
        # TestBase.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("1 component read from SBOM" in out)
        self.assertTrue("Retrieving package-url ids, filter: {'pypi'}" in out)
        self.assertTrue("Found 0 total purls" in out)
        self.assertTrue("ADDED (2-full-match-by-hash) 3765276512" in out)
        self.assertTrue("Full matches    = 1" in out)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("COMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual(MapResult.FULL_MATCH_BY_HASH, data["Details"][0]["ResultCode"])
        self.assertEqual("Full match by hash", data["Details"][0]["ResultText"])

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE)
        self.assertEqual(1, len(sbom.components))

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)
        TestBase.delete_file(self.CACHE_FILE)

    @responses.activate
    def test_mapping_cache_source_file(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.nocache = False
        args.cachefile = self.CACHE_FILE
        args.refresh_cache = True
        args.result_required = True

        # for login
        self.add_login_response()

        # purl cache
        self.add_empty_purl_cache_response()

        self.add_component_per_name_colorama_response()

        self.add_component_colorama_response()

        # component cache
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases?allDetails=true",
            body="""
            {
                "_embedded": {
                    "sw360:releases": [
                        {
                            "name": "colorama",
                            "version": "0.4.33",
                            "releaseDate" : "2016-12-07",
                            "componentId" : "678dstzd8",
                            "componentType" : "OSS",
                            "createdOn" : "2016-12-18",
                            "mainlineState" : "SPECIFIC",
                            "clearingState" : "APPROVED",
                            "cpeId": "007",
                            "_links": {
                                "sw360:component" : {
                                    "href" : "https://sw360.org/api/components/17653524"
                                },
                                "self": {
                                    "href": "https://my.server.com/resource/api/releases/3765276512"
                                }
                            },
                            "_embedded" : {
                                "sw360:attachments" : [ [ {
                                    "filename" : "file:colorama-0.4.3.tar.gz",
                                    "sha1" : "da373e491d3863477568896089ee9457bc316783",
                                    "attachmentType" : "SOURCE",
                                    "createdBy" : "admin@sw360.org",
                                    "createdTeam" : "Clearing Team 1",
                                    "createdComment" : "please check asap",
                                    "createdOn" : "2016-12-18",
                                    "checkedTeam" : "Clearing Team 2",
                                    "checkedComment" : "everything looks good",
                                    "checkedOn" : "2016-12-18",
                                    "checkStatus" : "ACCEPTED"
                                    } ] ]
                            }
                        }
                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "colorama",
                "version": "0.4.3",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "_links": {
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    },
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    }
                },
                "_embedded" : {
                    "sw360:attachments" : [ [ {
                        "filename" : "some_cli.xml",
                        "sha1" : "da373e491d3863477568896089ee9457bc316783",
                        "attachmentType" : "COMPONENT_LICENSE_INFO_XML",
                        "createdBy" : "admin@sw360.org",
                        "createdTeam" : "Clearing Team 1",
                        "createdComment" : "please check asap",
                        "createdOn" : "2016-12-18",
                        "checkedTeam" : "Clearing Team 2",
                        "checkedComment" : "everything looks good",
                        "checkedOn" : "2016-12-18",
                        "checkStatus" : "ACCEPTED"
                        } ] ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = TestBase.capture_stdout(sut.run, args)
        # TestBase.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("1 component read from SBOM" in out)
        self.assertTrue("Retrieving package-url ids, filter: {'pypi'}" in out)
        self.assertTrue("Found 0 total purls" in out)
        self.assertTrue("ADDED (4-good-match-by-filename) 3765276512" in out)
        self.assertTrue("Full matches    = 1" in out)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("COMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual(MapResult.MATCH_BY_FILENAME, data["Details"][0]["ResultCode"])
        self.assertEqual("Match by filename", data["Details"][0]["ResultText"])

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE)
        self.assertEqual(1, len(sbom.components))

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)
        TestBase.delete_file(self.CACHE_FILE)

    @responses.activate
    def test_mapping_cache_similar(self) -> None:
        sut = MapBom()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE2)
        args.outputfile = self.OUTPUTFILE
        args.write_mapresult = self.MAPPING_FILE
        args.create_overview = self.OVERVIEW_FILE
        args.verbose = True
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.nocache = False
        args.cachefile = self.CACHE_FILE
        args.refresh_cache = True
        args.result_required = True
        args.similar = True

        # for login
        self.add_login_response()

        # purl cache
        self.add_empty_purl_cache_response()

        self.add_component_per_name_colorama_response()

        self.add_component_colorama_response()

        # component cache
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases?allDetails=true",
            body="""
            {
                "_embedded": {
                    "sw360:releases": [
                        {
                            "name": "python-colorama",
                            "version": "0.4.33",
                            "releaseDate" : "2016-12-07",
                            "componentId" : "678dstzd8",
                            "componentType" : "OSS",
                            "createdOn" : "2016-12-18",
                            "mainlineState" : "SPECIFIC",
                            "clearingState" : "APPROVED",
                            "cpeId": "007",
                            "_links": {
                                "sw360:component" : {
                                    "href" : "https://sw360.org/api/components/17653524"
                                },
                                "self": {
                                    "href": "https://my.server.com/resource/api/releases/3765276512"
                                }
                            },
                            "_embedded" : {
                                "sw360:attachments" : [ ]
                            }
                        }
                    ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # the release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/3765276512",
            body="""
            {
                "name": "python-colorama",
                "version": "0.4.3",
                "releaseDate" : "2016-12-07",
                "componentType" : "OSS",
                "componentId" : "678dstzd8",
                "_links": {
                    "sw360:component" : {
                        "href" : "https://my.server.com/resource/api/components/678dstzd8"
                    },
                    "self": {
                        "href": "https://my.server.com/api/releases/3765276512"
                    }
                },
                "_embedded" : {
                    "sw360:attachments" : [ [ {
                        "filename" : "some_cli.xml",
                        "sha1" : "da373e491d3863477568896089ee9457bc316783",
                        "attachmentType" : "COMPONENT_LICENSE_INFO_XML",
                        "createdBy" : "admin@sw360.org",
                        "createdTeam" : "Clearing Team 1",
                        "createdComment" : "please check asap",
                        "createdOn" : "2016-12-18",
                        "checkedTeam" : "Clearing Team 2",
                        "checkedComment" : "everything looks good",
                        "checkedOn" : "2016-12-18",
                        "checkStatus" : "ACCEPTED"
                        } ] ]
                }
            }
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            sut.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_NO_UNIQUE_MAPPING, sysex.code)

        # check result files
        data = load_json_file(self.OVERVIEW_FILE)
        self.assertIsNotNone(data)
        self.assertEqual("INCOMPLETE", data.get("OverallResult", ""))
        self.assertEqual(1, len(data["Details"]))
        self.assertEqual("colorama python, 0.4.3", data["Details"][0]["BomItem"])
        self.assertEqual(MapResult.SIMILAR_COMPONENT_FOUND, data["Details"][0]["ResultCode"])
        self.assertEqual("Similar component found", data["Details"][0]["ResultText"])

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE)
        self.assertEqual(2, len(sbom.components))

        TestBase.delete_file(self.OUTPUTFILE)
        TestBase.delete_file(self.MAPPING_FILE)
        TestBase.delete_file(self.OVERVIEW_FILE)
        TestBase.delete_file(self.CACHE_FILE)

    def test_update_bom_item(self) -> None:
        sut = MapBom()

        match: Dict[str, Any] = {}
        updated = sut.update_bom_item(None, match)
        self.assertIsNotNone(updated)
        self.assertEqual("", updated.name)
        self.assertEqual("", updated.version)

        # simple
        comp = Component(name="a", version="1")
        match: Dict[str, Any] = {}
        updated = sut.update_bom_item(comp, match)
        self.assertEqual("a", updated.name)
        self.assertEqual("1", updated.version)

        # update all - no existing
        match: Dict[str, Any] = {}
        match["Name"] = "b"
        match["Version"] = "2"
        match["Language"] = "C#"
        match["ComponentId"] = "123"
        match["SourceUrl"] = "http://123"
        match["SourceFile"] = "123%1.zip"
        match["BinaryFile"] = "123%.dll"
        match["ProjectSite"] = "http://somewhere"
        match["Sw360Id"] = "007"
        match["ComponentId"] = "0815"
        updated = sut.update_bom_item(comp, match)
        self.assertEqual("b", updated.name)
        self.assertEqual("2", updated.version)
        self.assertEqual("C#", CycloneDxSupport.get_property_value(updated, CycloneDxSupport.CDX_PROP_LANGUAGE))
        for ext_ref in updated.external_references:
            self.assertIsInstance(ext_ref.url, XsUri)
        self.assertEqual("http://123", str(CycloneDxSupport.get_ext_ref_source_url(updated)))
        self.assertEqual("123%251.zip", str(CycloneDxSupport.get_ext_ref_source_file(updated)))
        self.assertEqual("123%25.dll", str(CycloneDxSupport.get_ext_ref_binary_file(updated)))
        self.assertEqual("http://somewhere", str(CycloneDxSupport.get_ext_ref_website(updated)))
        self.assertEqual("007", CycloneDxSupport.get_property_value(updated, CycloneDxSupport.CDX_PROP_SW360ID))

        # update all - all existing => no updates
        comp = Component(name="a", version="1")
        CycloneDxSupport.update_or_set_property(comp, CycloneDxSupport.CDX_PROP_LANGUAGE, "Java")
        CycloneDxSupport.update_or_set_property(comp, CycloneDxSupport.CDX_PROP_SW360ID, "888")
        CycloneDxSupport.update_or_set_ext_ref(
            comp, ExternalReferenceType.DISTRIBUTION, CaPyCliBom.SOURCE_URL_COMMENT, "http://456")
        CycloneDxSupport.update_or_set_ext_ref(
            comp, ExternalReferenceType.DISTRIBUTION, CaPyCliBom.SOURCE_FILE_COMMENT, "456.zip")
        CycloneDxSupport.update_or_set_ext_ref(
            comp, ExternalReferenceType.DISTRIBUTION, CaPyCliBom.BINARY_FILE_COMMENT, "456.dll")
        CycloneDxSupport.update_or_set_ext_ref(
            comp, ExternalReferenceType.WEBSITE, "", "http://somewhereelse")

        updated = sut.update_bom_item(comp, match)
        self.assertEqual("b", updated.name)
        self.assertEqual("2", updated.version)
        self.assertEqual("Java", CycloneDxSupport.get_property_value(updated, CycloneDxSupport.CDX_PROP_LANGUAGE))
        self.assertEqual("http://456", str(CycloneDxSupport.get_ext_ref_source_url(comp)))
        for ext_ref in updated.external_references:
            self.assertIsInstance(ext_ref.url, XsUri)
        self.assertEqual("456.zip", str(CycloneDxSupport.get_ext_ref_source_file(updated)))
        self.assertEqual("456.dll", str(CycloneDxSupport.get_ext_ref_binary_file(updated)))
        self.assertEqual("http://somewhereelse", str(CycloneDxSupport.get_ext_ref_website(updated)))
        self.assertEqual("888", CycloneDxSupport.get_property_value(updated, CycloneDxSupport.CDX_PROP_SW360ID))

        # update all - all existing, but empty => updates
        comp = Component(name="a", version="1")
        CycloneDxSupport.update_or_set_property(comp, CycloneDxSupport.CDX_PROP_LANGUAGE, "")
        CycloneDxSupport.update_or_set_property(comp, CycloneDxSupport.CDX_PROP_SW360ID, "")
        CycloneDxSupport.update_or_set_ext_ref(
            comp, ExternalReferenceType.DISTRIBUTION, CaPyCliBom.SOURCE_URL_COMMENT, "")
        CycloneDxSupport.update_or_set_ext_ref(
            comp, ExternalReferenceType.DISTRIBUTION, CaPyCliBom.SOURCE_FILE_COMMENT, "")
        CycloneDxSupport.update_or_set_ext_ref(
            comp, ExternalReferenceType.DISTRIBUTION, CaPyCliBom.BINARY_FILE_COMMENT, "")
        CycloneDxSupport.update_or_set_ext_ref(
            comp, ExternalReferenceType.WEBSITE, "", "")
        CycloneDxSupport.update_or_set_property(comp, CycloneDxSupport.CDX_PROP_COMPONENT_ID, "")

        updated = sut.update_bom_item(comp, match)
        self.assertEqual("b", updated.name)
        self.assertEqual("2", updated.version)
        self.assertEqual("C#", CycloneDxSupport.get_property_value(updated, CycloneDxSupport.CDX_PROP_LANGUAGE))
        for ext_ref in updated.external_references:
            self.assertIsInstance(ext_ref.url, XsUri)
        self.assertEqual("http://123", str(CycloneDxSupport.get_ext_ref_source_url(updated)))
        self.assertEqual("123%251.zip", str(CycloneDxSupport.get_ext_ref_source_file(updated)))
        self.assertEqual("123%25.dll", str(CycloneDxSupport.get_ext_ref_binary_file(updated)))
        self.assertEqual("http://somewhere", str(CycloneDxSupport.get_ext_ref_website(updated)))
        self.assertEqual("007", CycloneDxSupport.get_property_value(updated, CycloneDxSupport.CDX_PROP_SW360ID))
        self.assertEqual("0815", CycloneDxSupport.get_property_value(updated, CycloneDxSupport.CDX_PROP_COMPONENT_ID))

        # extra: update package-url
        comp = Component(name="a", version="1.0")
        match = {}
        match["Name"] = "b"
        match["Version"] = "2.0"
        match["RepositoryId"] = "pkg:pypi/a@2.0"
        updated = sut.update_bom_item(comp, match)
        self.assertIsNotNone(updated)
        if updated:
            self.assertEqual("b", updated.name)
            self.assertEqual("2.0", updated.version)
            if updated.purl:
                self.assertEqual("pkg:pypi/a@2.0", updated.purl.to_string())

        # extra: update package-url
        comp = Component(name="a", version="1.0", purl=PackageURL.from_string("pkg:pypi/a@1.0"))
        match = {}
        match["Name"] = "b"
        match["Version"] = "2.0"
        match["RepositoryId"] = "pkg:pypi/a@2.0"
        updated = sut.update_bom_item(comp, match)
        self.assertIsNotNone(updated)
        if updated:
            self.assertEqual("b", updated.name)
            self.assertEqual("2.0", updated.version)
            if updated.purl:
                self.assertEqual("pkg:pypi/a@2.0", updated.purl.to_string())

    def test_add_match_if_better(self) -> None:
        sut = MapBom()

        release = {}

        # empty release list
        result = MapResult()
        release["MapResult"] = MapResult.NO_MATCH
        val = sut.add_match_if_better(result, release, MapResult.MATCH_BY_FILENAME)
        assert len(result.releases) == 1
        self.assertTrue(val)

        result = MapResult()
        release["MapResult"] = MapResult.NO_MATCH
        result.releases = [release]
        val = sut.add_match_if_better(result, release, MapResult.SIMILAR_COMPONENT_FOUND)
        self.assertTrue(val)

        result = MapResult()
        release["MapResult"] = MapResult.SIMILAR_COMPONENT_FOUND
        result.releases = [release]
        val = sut.add_match_if_better(result, release, MapResult.SIMILAR_COMPONENT_FOUND)
        self.assertTrue(val)
        assert len(result.releases) == 2

        val = sut.add_match_if_better(result, release, MapResult.MATCH_BY_NAME)
        self.assertTrue(val)

        result.releases = []
        release = {}
        release["MapResult"] = MapResult.MATCH_BY_NAME
        result.releases.append(release)
        release = {}
        release["MapResult"] = MapResult.MATCH_BY_FILENAME
        result.releases.append(release)
        release = {}
        release["MapResult"] = MapResult.FULL_MATCH_BY_NAME_AND_VERSION
        result.releases.append(release)
        release = {}
        release["MapResult"] = MapResult.FULL_MATCH_BY_HASH
        result.releases.append(release)

        val = sut.add_match_if_better(result, release, MapResult.FULL_MATCH_BY_HASH)
        self.assertTrue(val)

        val = sut.add_match_if_better(result, release, MapResult.FULL_MATCH_BY_ID)
        self.assertTrue(val)

        release = {}
        release["MapResult"] = MapResult.FULL_MATCH_BY_ID
        result.releases.append(release)

        val = sut.add_match_if_better(result, release, MapResult.FULL_MATCH_BY_HASH)
        self.assertFalse(val)

    def test_is_good_match(self) -> None:
        """
        Tests for
        * 'if match_item["MapResult"] <= MapResult.GOOD_MATCH_FOUND'
        * 'item.result > MapResult.GOOD_MATCH_FOUND'
        """
        sut = MapBom()
        self.assertFalse(sut.is_good_match(MapResult.INVALID))
        self.assertFalse(sut.is_good_match(MapResult.MATCH_BY_NAME))
        self.assertFalse(sut.is_good_match(MapResult.NO_MATCH))

        self.assertTrue(sut.is_good_match(MapResult.FULL_MATCH_BY_ID))
        self.assertTrue(sut.is_good_match(MapResult.FULL_MATCH_BY_HASH))
        self.assertTrue(sut.is_good_match(MapResult.FULL_MATCH_BY_NAME_AND_VERSION))
        self.assertTrue(sut.is_good_match(MapResult.MATCH_BY_FILENAME))


if __name__ == "__main__":
    APP = CapycliTestBomMap()
    APP.setUp()
    APP.test_mapping_require_result_not_found()
