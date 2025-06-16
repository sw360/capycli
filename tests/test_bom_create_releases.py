# -------------------------------------------------------------------------------
# Copyright (c) 2021-2025 Siemens
# All Rights Reserved.
# Author: gernot.hillier@siemens.com, thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

"""unit tests for bom/create_components.py in createreleases mode"""
from typing import Any, Dict, Tuple

import responses
from cyclonedx.model import ExternalReference, ExternalReferenceType, HashAlgorithm, HashType, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from packageurl import PackageURL

import capycli.bom.create_components
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.common.map_result import MapResult
from tests.test_base_vcr import SW360_BASE_URL, CapycliTestBase


def upload_matcher(filename: str, filetype: str = "SOURCE", comment: str = "") -> Any:
    # responses.matcher.multipart_matcher didn't work for me
    def match(request: Any) -> Tuple[bool, str]:
        result = True
        reason = ""

        if isinstance(request.body, bytes):
            request_body = request.body.decode("utf-8")
        print(request)
        if '"filename": "' + filename + '"' not in request_body:
            result = False
            reason = ("filename " + filename + " not found in: " + request_body)
        if '"attachmentType": "' + filetype + '"' not in request_body:
            result = False
            reason = ("attachmentType " + filetype + " not found in: " + request_body)
        if comment and '"createdComment": "' + comment + '"' not in request_body:
            result = False
            reason = ("createdComment " + comment + " not found in: " + request_body)

        return result, reason
    return match


class CapycliTestBomCreate(CapycliTestBase):
    @responses.activate
    def setUp(self) -> None:
        self.app = capycli.bom.create_components.BomCreateComponents(onlyCreateReleases=True)
        responses.add(responses.GET, SW360_BASE_URL, json={"status": "ok"})
        self.app.login("sometoken", "https://my.server.com")

    @responses.activate
    def test_create_items_existing_release_with_id(self) -> None:
        """Release exists and was identified in "bom map"
        """
        responses.add(responses.GET, SW360_BASE_URL + 'releases/06a6e5', json={
            "name": "activemodel",
            "version": "5.2.1",
            "_links": {"self": {
                "href": SW360_BASE_URL + "releases/06a6e5"}}})

        cx_comp = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_property(cx_comp, CycloneDxSupport.CDX_PROP_SW360ID, "06a6e5")

        items = Bom()
        items.components.add(cx_comp)
        self.app.create_items(items)
        # no assertion needed, we verify that nothing is created in SW360
        # any SW360 write access would trigger an exception

        cx_comp = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_property(cx_comp, CycloneDxSupport.CDX_PROP_SW360ID, "06a6e5")
        CycloneDxSupport.update_or_set_ext_ref(
            cx_comp, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, "new_url")

        items = Bom()
        items.components.add(cx_comp)

        responses.add(
            responses.PATCH, SW360_BASE_URL + 'releases/06a6e5',
            match=[responses.matchers.json_params_matcher({
                "sourceCodeDownloadurl": "new_url"})],
            # server answer with created release data
            json={
                "sourceCodeDownloadurl": "new_url",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e5"}}})
        self.app.create_items(items)
        assert responses.calls[-1].request.method == responses.PATCH
        assert responses.calls[-1].request.url == SW360_BASE_URL + 'releases/06a6e5'

    @responses.activate
    def test_create_comp_release_no_component(self) -> None:
        """Component doesn't exist. As we test onlyCreateReleases case here,
        we shall not do anything.
        """
        responses.add(responses.GET, SW360_BASE_URL + 'components?name=somecomp', json={
            "_embedded": {"sw360:components": []}})

        cx_comp = Component(
            name="somecomp",
            version="5.2.4.3"
        )
        CycloneDxSupport.update_or_set_property(cx_comp, CycloneDxSupport.CDX_PROP_MAPRESULT, MapResult.NO_MATCH)
        self.app.create_component_and_release(cx_comp)

        # no assertion needed, we verify that nothing is created in SW360
        # any SW360 write access would trigger an exception

    @responses.activate
    def test_create_comp_release_no_component_id(self) -> None:
        """No ComponentId in bom. require-id mode is default for , do nothing.
        """
        cx_comp = Component(
            name="somecomp",
            version="5.2.4.3"
        )
        CycloneDxSupport.update_or_set_property(cx_comp, CycloneDxSupport.CDX_PROP_MAPRESULT, MapResult.NO_MATCH)
        self.app.create_component_and_release(cx_comp)
        # no assertion needed, we verify that nothing is created in SW360
        # any SW360 access would trigger an exception

    @responses.activate
    def test_create_comp_release_existing_release_without_id(self) -> None:
        """Release exists, but was not identified during "bom map"
        """
        responses.add(responses.GET, SW360_BASE_URL + 'components/06a6e5', json={
            "name": "activemodel",
            "_embedded": {"sw360:releases": [{
                "name": "activemodel",
                "version": "5.2.1",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e6"}}}]}})
        responses.add(responses.GET, SW360_BASE_URL + 'releases/06a6e6', json={
            "name": "activemodel",
            "version": "5.2.1",
            "_links": {"self": {
                "href": SW360_BASE_URL + "releases/06a6e6"}}})

        item = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_COMPONENT_ID, "06a6e5")
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_MAPRESULT, MapResult.NO_MATCH)

        self.app.create_component_and_release(item)
        assert len(responses.calls) >= 1
        id = CycloneDxSupport.get_property_value(item, CycloneDxSupport.CDX_PROP_SW360ID)
        assert id == "06a6e6"

    @responses.activate
    def test_create_comp_release_existing_debian_release_default(self) -> None:
        """existing Debian release (not identified during "bom map"), default mode
        """
        responses.add(responses.GET, SW360_BASE_URL + 'components/06a6e5', json={
            "name": "activemodel",
            "_links": {"self": {
                    "href": SW360_BASE_URL + "components/06a6e5"}},
            "_embedded": {"sw360:releases": [{
                "name": "activemodel",
                "version": "5.2.1-1",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e6"}}}]}})
        responses.add(
            responses.POST,
            SW360_BASE_URL + 'releases',
            # verify data we send in POST
            match=[responses.matchers.json_params_matcher({
                "name": "activemodel",
                "componentId": "06a6e5",
                "version": "5.2.1-1.debian",
                "mainlineState": "OPEN",
                "additionalData": {"createdWith": capycli.get_app_signature()}})],
            # server answer with created release data
            json={"version": "5.2.1-1.debian",
                  "_links": {"self": {
                      "href": SW360_BASE_URL + "releases/06a6e7"}}})

        item = Component(
            name="activemodel",
            version="5.2.1-1.debian"
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_COMPONENT_ID, "06a6e5")
        self.app.create_component_and_release(item)
        id = CycloneDxSupport.get_property_value(item, CycloneDxSupport.CDX_PROP_SW360ID)
        assert id == "06a6e7"

    @responses.activate
    def test_create_comp_release_existing_debian_release_relaxed(self) -> None:
        """existing Debian release (not identified during "bom map"), relaxed mode
        """
        self.app.relaxed_debian_parsing = True
        responses.add(responses.GET, SW360_BASE_URL + 'components/06a6e5', json={
            "name": "activemodel",
            "_links": {"self": {
                    "href": SW360_BASE_URL + "components/06a6e5"}},
            "_embedded": {"sw360:releases": [{
                "name": "activemodel",
                "version": "2:5.2.1-1",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e6"}}}]}})
        responses.add(responses.GET, SW360_BASE_URL + 'releases/06a6e6', json={
            "name": "activemodel",
            "version": "2:5.2.1-1",
            "_links": {"self": {
                "href": SW360_BASE_URL + "releases/06a6e6"}}})

        item = Component(
            name="activemodel",
            version="5.2.1-1.debian"
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_COMPONENT_ID, "06a6e5")
        self.app.create_component_and_release(item)
        assert CycloneDxSupport.get_property_value(item, CycloneDxSupport.CDX_PROP_SW360ID) == "06a6e6"
        assert item.version == "2:5.2.1-1"

        item = Component(
            name="activemodel",
            version="2:5.2.1-1 (Debian)"
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_COMPONENT_ID, "06a6e5")
        self.app.create_component_and_release(item)
        assert CycloneDxSupport.get_property_value(item, CycloneDxSupport.CDX_PROP_SW360ID) == "06a6e6"
        assert item.version == "2:5.2.1-1"

    @responses.activate
    def test_create_comp_release_existing_debian_release_relaxed_epoch(self) -> None:
        """existing Debian release w/o epoch, relaxed mode
        """
        self.app.relaxed_debian_parsing = True
        responses.add(responses.GET, SW360_BASE_URL + 'components/06a6e5', json={
            "name": "activemodel",
            "_links": {"self": {
                    "href": SW360_BASE_URL + "components/06a6e5"}},
            "_embedded": {"sw360:releases": [{
                "name": "activemodel",
                "version": "5.2.1-1",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e6"}}}]}})
        responses.add(responses.GET, SW360_BASE_URL + 'releases/06a6e6', json={
            "name": "activemodel",
            "version": "5.2.1-1",
            "_links": {"self": {
                "href": SW360_BASE_URL + "releases/06a6e6"}}})

        item = Component(
            name="activemodel",
            version="2:5.2.1-1 (Debian)"
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_COMPONENT_ID, "06a6e5")
        self.app.create_component_and_release(item)
        assert CycloneDxSupport.get_property_value(item, CycloneDxSupport.CDX_PROP_SW360ID) == "06a6e6"
        assert item.version == "5.2.1-1"

    @responses.activate
    def test_create_comp_release_existing_debian_release_relaxed_no_match(self) -> None:
        """Existing Debian release has a different patch level
        """
        self.app.relaxed_debian_parsing = True
        responses.add(responses.GET, SW360_BASE_URL + 'components/06a6e5', json={
            "name": "activemodel",
            "_links": {"self": {
                    "href": SW360_BASE_URL + "components/06a6e5"}},
            "_embedded": {"sw360:releases": [{
                "name": "activemodel",
                "version": "2:5.2.1-1+deb10u3",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e6"}}}]}})
        responses.add(
            responses.POST,
            SW360_BASE_URL + 'releases',
            # verify data we send in POST
            match=[responses.matchers.json_params_matcher({
                "name": "activemodel",
                "componentId": "06a6e5",
                "version": "5.2.1-1.debian",
                "mainlineState": "OPEN",
                "additionalData": {"createdWith": capycli.get_app_signature()}})],
            # server answer with created release data
            json={"version": "5.2.1-1.debian",
                  "_links": {"self": {
                      "href": SW360_BASE_URL + "releases/06a6e7"}}})

        item = Component(
            name="activemodel",
            version="5.2.1-1.debian"
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_COMPONENT_ID, "06a6e5")
        self.app.create_component_and_release(item)
        assert CycloneDxSupport.get_property_value(item, CycloneDxSupport.CDX_PROP_SW360ID) == "06a6e7"
        assert item.version == "5.2.1-1.debian"

    @responses.activate
    def test_create_comp_release_existing_debian_release_relaxed_exactmatch(self) -> None:
        """Even in relaxed mode, we should prefer exact matches
        """
        self.app.relaxed_debian_parsing = True
        responses.add(responses.GET, SW360_BASE_URL + 'components/06a6e5', json={
            "name": "activemodel",
            "_links": {"self": {
                    "href": SW360_BASE_URL + "components/06a6e5"}},
            "_embedded": {"sw360:releases": [{
                "name": "activemodel",
                "version": "2:5.2.1-1 (split source)",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e6"}}}, {
                "name": "activemodel",
                "version": "5.2.1-1.debian",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6a5"}}}]}})
        responses.add(responses.GET, SW360_BASE_URL + 'releases/06a6a5', json={
            "name": "activemodel",
            "version": "5.2.1-1.debian",
            "_links": {"self": {
                "href": SW360_BASE_URL + "releases/06a6a5"}}})

        item = Component(
            name="activemodel",
            version="5.2.1-1.debian"
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_COMPONENT_ID, "06a6e5")
        self.app.create_component_and_release(item)
        assert CycloneDxSupport.get_property_value(item, CycloneDxSupport.CDX_PROP_SW360ID) == "06a6a5"

    @responses.activate
    def test_create_comp_release_component_id(self) -> None:
        """Release doesn't exist and we have a componentId match. So create it.
        """
        # no search for component name must occur
        responses.add(responses.GET, SW360_BASE_URL + 'components/06a6e5', json={
            "name": "activemodel",
            "_links": {"self": {
                    "href": SW360_BASE_URL + "components/06a6e5"}},
            "_embedded": {"sw360:releases": [{
                "name": "activemodel",
                "version": "5.2.1",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e6"}}}]}})
        responses.add(
            responses.POST,
            SW360_BASE_URL + 'releases',
            # verify data we send in POST
            match=[responses.matchers.json_params_matcher({
                "name": "activemodel",
                "componentId": "06a6e5",
                "version": "5.2.4.3",
                "mainlineState": "OPEN",
                "additionalData": {"createdWith": capycli.get_app_signature()}})],
            # server answer with created release data
            json={"version": "5.2.4.3",
                  "_links": {"self": {
                      "href": SW360_BASE_URL + "releases/06a6e7"}}})

        item = Component(
            name="activemodel",
            version="5.2.4.3"
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_COMPONENT_ID, "06a6e5")
        self.app.create_component_and_release(item)
        assert CycloneDxSupport.get_property_value(item, CycloneDxSupport.CDX_PROP_SW360ID) == "06a6e7"

    @responses.activate
    def test_create_comp_release_component_id_update(self) -> None:
        """We have a componentId match. Update package-url if needed.
        """
        # component has package-url, release exists
        component_data: Dict[str, Any] = {
            "name": "activemodel",
            "externalIds": {"package-url": "pkg:deb/debian/activemodel?arch=source"},
            "_links": {"self": {
                    "href": SW360_BASE_URL + "components/06a6e5"}},
            "_embedded": {"sw360:releases": [{
                "name": "activemodel",
                "version": "5.2.1",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e6"}}}]}}
        responses.add(responses.GET, SW360_BASE_URL + 'components/06a6e5', json=component_data)
        responses.add(responses.GET, SW360_BASE_URL + 'releases/06a6e6', json={
            "name": "activemodel",
            "version": "5.2.1",
            "externalIds": {"package-url": "pkg:deb/debian/activemodel@5.2.1?arch=source"},
            "_links": {"self": {
                "href": SW360_BASE_URL + "releases/06a6e6"}}})

        item = Component(
            name="activemodel",
            version="5.2.1",
            purl=PackageURL.from_string("pkg:deb/debian/activemodel@5.2.1?arch=source")
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_COMPONENT_ID, "06a6e5")
        self.app.create_component_and_release(item)
        assert len(responses.calls) == 2

        # component lacks package-url, release exists
        del component_data["externalIds"]["package-url"]
        responses.replace(responses.GET, SW360_BASE_URL + 'components/06a6e5', json=component_data)

        responses.add(
            responses.PATCH, SW360_BASE_URL + 'components/06a6e5',
            match=[responses.matchers.json_params_matcher({
                "externalIds": {"package-url": "pkg:deb/debian/activemodel?arch=source"}})],
            json={
                "_links": {"self": {
                    "href": SW360_BASE_URL + "components/06a6e7"}}})

        item = Component(
            name="activemodel",
            version="5.2.1",
            purl=PackageURL.from_string("pkg:deb/debian/activemodel@5.2.1?arch=source")
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_COMPONENT_ID, "06a6e5")
        self.app.create_component_and_release(item)
        assert responses.calls[-2].request.url == SW360_BASE_URL + 'components/06a6e5'
        assert responses.calls[-2].request.method == responses.PATCH

        # component lacks externalIds, release exists
        del component_data["externalIds"]
        responses.replace(responses.GET, SW360_BASE_URL + 'components/06a6e5', json=component_data)

        self.app.create_component_and_release(item)
        assert responses.calls[-2].request.url == SW360_BASE_URL + 'components/06a6e5'
        assert responses.calls[-2].request.method == responses.PATCH

    @responses.activate
    def test_update_component_other_purl(self) -> None:
        """Existing component has different purl, so issue warning.
        """
        component_data: Dict[str, Any] = {
            "name": "activemodel",
            "externalIds": {"package-url": "pkg:deb/ubuntu/activemodel?arch=source"},
            "_links": {"self": {
                    "href": SW360_BASE_URL + "components/06a6e5"}},
            "_embedded": {"sw360:releases": [{
                "name": "activemodel",
                "version": "5.2.1",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e6"}}}]}}
        item = Component(
            name="activemodel",
            version="5.2.1",
            purl=PackageURL.from_string("pkg:deb/debian/activemodel@5.2.1?arch=source")
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_COMPONENT_ID, "06a6e5")
        self.app.update_component(item, "123", component_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "differs from BOM id" in captured.out

        component_data["externalIds"]["package-url"] = ('['
                                                        '"pkg:deb/ubuntu/activemodel?arch=source",'
                                                        '"pkg:deb/debian/activemodel?arch=source"]')
        self.app.update_component(item, "123", component_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "differs from BOM id" not in captured.out
        assert "WARNING" not in captured.out

    @responses.activate
    def test_create_release_SourceUrl(self) -> None:
        """Create release from BOM SourceFileUrl, no download
        """
        responses.add(
            responses.POST,
            SW360_BASE_URL + 'releases',
            # verify data we send in POST
            match=[responses.matchers.json_params_matcher({
                "name": "activemodel",
                "componentId": "06a6e5",
                "sourceCodeDownloadurl": "https://rubygems.org/gems/activemodel-5.2.1.gem",
                "version": "5.2.1",
                "mainlineState": "OPEN",
                "additionalData": {"createdWith": capycli.get_app_signature()}})],
            # server answer with created release data
            json={"_links": {"self": {
                "href": SW360_BASE_URL + "releases/06a6e7"}}})
        item = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, "https://rubygems.org/gems/activemodel-5.2.1.gem")
        release = self.app.create_release(item, "06a6e5")
        assert release is not None
        if release:
            assert release["_links"]["self"]["href"].endswith("06a6e7")

        # no automatic download/upload as default for self.app.download is False
        item = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, "https://rubygems.org/gems/activemodel-5.2.1.gem")
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_COMPONENT_ID, "06a6e5")
        release = self.app.create_release(item, component_id="06a6e5")
        assert release is not None
        if release:
            assert release["_links"]["self"]["href"].endswith("06a6e7")

        captured = self.capsys.readouterr()  # type: ignore
        assert "Error" not in captured.out
        assert captured.err == ""

    @responses.activate
    def test_create_release_emptySourceFile(self) -> None:
        """Create release from BOM with empty SourceFileUrl or SourceFile
        """
        responses.add(
            responses.POST,
            SW360_BASE_URL + 'releases',
            # verify data we send in POST
            match=[responses.matchers.json_params_matcher({
                "name": "activemodel",
                "componentId": "06a6e5",
                # "sourceCodeDownloadurl": "",
                "mainlineState": "OPEN",
                "version": "5.2.1",
                "additionalData": {"createdWith": capycli.get_app_signature()}})],
            # server answer with created release data
            json={"_links": {"self": {
                "href": SW360_BASE_URL + "releases/06a6e7"}}})
        item = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, "")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_FILE_COMMENT, "")
        release = self.app.create_release(item, component_id="06a6e5")
        assert release is not None
        if release:
            assert release["_links"]["self"]["href"].endswith("06a6e7")

        captured = self.capsys.readouterr()  # type: ignore
        print(captured.out)
        assert "Error" not in captured.out
        assert captured.err == ""

        item = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, "")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_FILE_COMMENT, "notexist.txt")
        release = self.app.create_release(item, component_id="06a6e5")
        assert release is not None
        if release:
            self.app.update_release(item, release)
            assert release["_links"]["self"]["href"].endswith("06a6e7")

        captured = self.capsys.readouterr()  # type: ignore
        # assert "File not found" in captured.out
        assert captured.err == ""

    @responses.activate
    def test_upload_file_download(self) -> None:
        """Upload file including download
        """
        responses.add(
            responses.GET, 'https://rubygems.org/gems/activemodel-5.2.1.gem',
            body="content")
        responses.add(
            responses.POST, SW360_BASE_URL + 'releases/06a6e7/attachments',
            match=[upload_matcher("activemodel-5.2.1.gem")])

        # guess filename from SourceFileUrl
        self.app.download = True
        item = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, "https://rubygems.org/gems/activemodel-5.2.1.gem")
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_SRC_FILE_COMMENT, "testcomment")
        self.app.upload_file(item, {}, "06a6e7", "SOURCE", "testcomment")

        # use specified filename for upload
        responses.replace(
            responses.POST, SW360_BASE_URL + 'releases/06a6e7/attachments',
            match=[upload_matcher("anothername.zip", "SOURCE", "testcomment")])
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_FILE_COMMENT, "anothername.zip")
        self.app.upload_file(item, {}, "06a6e7", "SOURCE", "testcomment")

        assert len(responses.calls) == 4
        captured = self.capsys.readouterr()  # type: ignore
        assert "Error" not in captured.out
        assert captured.err == ""

    @responses.activate
    def test_upload_file_download_rename(self) -> None:
        """Upload file including download with server specifying different file name
        """
        responses.add(
            responses.GET, 'https://github.com/babel/babel/archive/refs/tags/v7.16.0.zip',
            headers={"content-disposition": 'attachment; filename=babel-7.16.0.zip'},
            body="content")
        responses.add(
            responses.POST, SW360_BASE_URL + 'releases/06a6e7/attachments',
            match=[upload_matcher("babel-7.16.0.zip")])

        self.app.download = True
        # item = {"Name": "babel", "Version": "7.16.0",
        #        "SourceFileUrl": "https://github.com/babel/babel/archive/refs/tags/v7.16.0.zip"}
        item2 = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_ext_ref(
            item2, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, "https://github.com/babel/babel/archive/refs/tags/v7.16.0.zip")
        self.app.upload_file(item2, {}, "06a6e7", "SOURCE", "")
        captured = self.capsys.readouterr()  # type: ignore
        assert len(responses.calls) == 2
        assert "Error" not in captured.out
        assert captured.err == ""

    @responses.activate
    def test_upload_file_local(self) -> None:
        """Upload local file
        """
        my_url = "https://code.siemens.com/sw360/clearingautomation/Readme.md"
        responses.add(
            responses.POST, SW360_BASE_URL + 'releases/06a6e7/attachments',
            match=[upload_matcher("Readme.md", filetype="SOURCE_SELF")])

        # local filename + url
        item = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_SRC_FILE_TYPE, "SOURCE_SELF")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_FILE_COMMENT, "Readme.md")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, my_url)
        self.app.upload_file(item, {}, "06a6e7", "SOURCE_SELF", "")

        # local filename guessed from remote url
        item = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_SRC_FILE_TYPE, "SOURCE_SELF")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, my_url)
        self.app.upload_file(item, {}, "06a6e7", "SOURCE_SELF", "")

        assert len(responses.calls) == 2
        captured = self.capsys.readouterr()  # type: ignore
        assert "Error" not in captured.out
        assert captured.err == ""

    @responses.activate
    def test_upload_file_prevent_git_source_upload(self) -> None:
        """Prevent uploading SOURCE, SOURCE_SELF file with .git file type
        """
        responses.add(
            responses.GET, 'https://github.com/babel/babel.git',
            body="content")

        self.app.download = True
        item = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, "https://github.com/babel/babel.git")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_FILE_COMMENT, "babel.git")

        self.app.upload_file(item, {}, "06a6e7", "SOURCE", "")
        captured = self.capsys.readouterr()  # type: ignore
        assert len(responses.calls) == 0
        assert "WARNING: resetting filename to prevent uploading .git file" in captured.out
        assert captured.err == ""

    @responses.activate
    def test_upload_file_allow_git_binary_upload(self) -> None:
        """Allow uploading BINARY file with .git file type
        """
        responses.add(
            responses.GET, 'https://github.com/babel/babel.git',
            body="content")
        responses.add(
            responses.POST, SW360_BASE_URL + 'releases/06a6e7/attachments',
            match=[upload_matcher("babel.git", "BINARY")])

        self.app.download = True
        item = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.BINARY_URL_COMMENT, "https://github.com/babel/babel.git")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.BINARY_FILE_COMMENT, "babel.git")

        self.app.upload_file(item, {}, "06a6e7", "BINARY", "")
        captured = self.capsys.readouterr()  # type: ignore
        assert len(responses.calls) == 2
        assert "WARNING: resetting filename to prevent uploading .git file" not in captured.out
        assert captured.err == ""

    @responses.activate
    def test_upload_binary_file_local(self) -> None:
        """Upload local file
        """
        my_url = "https://code.siemens.com/sw360/clearingautomation/Readme.md"
        responses.add(
            responses.POST, SW360_BASE_URL + 'releases/06a6e7/attachments',
            match=[upload_matcher("Readme.md", filetype="BINARY_SELF")])

        # local filename + url
        item = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_SRC_FILE_TYPE, "BINARY_SELF")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.BINARY_FILE_COMMENT, "Readme.md")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.BINARY_URL_COMMENT, my_url)
        self.app.upload_file(item, {}, "06a6e7", "BINARY_SELF", "")

        # local filename guessed from remote url
        item = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_SRC_FILE_TYPE, "BINARY_SELF")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.BINARY_URL_COMMENT, my_url)
        self.app.upload_file(item, {}, "06a6e7", "BINARY_SELF", "")

        assert len(responses.calls) == 2
        captured = self.capsys.readouterr()  # type: ignore
        assert "Error" not in captured.out
        assert captured.err == ""

    @responses.activate
    def test_upload_file_source_dir(self) -> None:
        """Upload local file from source_dir
        """
        my_url = "https://code.siemens.com/sw360/clearingautomation/__main__.py"
        responses.add(
            responses.POST, SW360_BASE_URL + 'releases/06a6e7/attachments',
            match=[upload_matcher("__main__.py")])

        self.app.source_folder = "capycli"

        # local filename + url
        item = Component(
            name="Capycli main",
            version="0.1.2"
        )
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_FILE_COMMENT, "__main__.py")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, my_url)
        self.app.upload_file(item, {}, "06a6e7", "SOURCE", "")

        # local filename guessed from remote url
        item = Component(
            name="activemodel",
            version="5.2.1"
        )
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, my_url)
        self.app.upload_file(item, {}, "06a6e7", "SOURCE", "")

        assert len(responses.calls) == 2
        captured = self.capsys.readouterr()  # type: ignore
        assert "Error" not in captured.out
        assert captured.err == ""

    @responses.activate
    def test_update_release_SourceUrl(self) -> None:
        """Update SourceUrl in existing release
        """
        # no existing URL, no new URL
        release_data: Dict[str, Any] = {
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}
        }

        item2 = Component(name="")
        self.app.update_release(item2, release_data)

        # existing URL, no new URL
        release_data = {
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}},
            "sourceCodeDownloadurl": "old_url"
        }
        item2 = Component(name="")
        self.app.update_release(item2, release_data)

        # existing URL equals to new URL
        item2 = Component(name="")
        CycloneDxSupport.update_or_set_ext_ref(
            item2, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, "old_url")
        self.app.update_release(item2, release_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "differs from BOM URL" not in captured.out

        # existing URL differs from new URL
        item2 = Component(name="")
        CycloneDxSupport.update_or_set_ext_ref(
            item2, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, "https://some.new/file.tar.gz")
        self.app.update_release(item2, release_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "differs from BOM URL" in captured.out
        assert len(responses.calls) == 0  # assure data in SW360 is not changed

        # no existing URL, set new URL
        responses.add(
            responses.PATCH, SW360_BASE_URL + 'releases/06a6e7',
            match=[responses.matchers.json_params_matcher({
                "sourceCodeDownloadurl": "new_url"})],
            # server answer with created release data
            json={
                "sourceCodeDownloadurl": "new_url",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e7"}}})
        release_data = {
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}
        }
        item2 = Component(name="")
        CycloneDxSupport.update_or_set_ext_ref(
            item2, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, "new_url")
        self.app.update_release(item2, release_data)
        assert len(responses.calls) == 1

        # existing URL empty, set new URL
        release_data = {
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}},
            "sourceCodeDownloadurl": ""
        }
        self.app.update_release(item2, release_data)
        assert len(responses.calls) == 2

    @responses.activate
    def test_update_release_BinaryUrl(self) -> None:
        """Update SourceUrl in existing release
        """
        # no existing URL, no new URL
        release_data: Dict[str, Any] = {
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}
        }

        item2 = Component(name="")
        self.app.update_release(item2, release_data)

        # existing URL, no new URL
        release_data = {
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}},
            "binaryDownloadurl": "old_url"
        }
        item2 = Component(name="")
        self.app.update_release(item2, release_data)

        # existing URL equals to new URL
        item2 = Component(name="")
        CycloneDxSupport.update_or_set_ext_ref(
            item2, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.BINARY_URL_COMMENT, "old_url")
        self.app.update_release(item2, release_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "differs from BOM URL" not in captured.out

        # existing URL differs from new URL
        item2 = Component(name="")
        CycloneDxSupport.update_or_set_ext_ref(
            item2, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.BINARY_URL_COMMENT, "new_url")
        self.app.update_release(item2, release_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "differs from BOM URL" in captured.out

        # no existing URL, set new URL
        responses.add(
            responses.PATCH, SW360_BASE_URL + 'releases/06a6e7',
            match=[responses.matchers.json_params_matcher({
                "binaryDownloadurl": "new_url"})],
            # server answer with created release data
            json={
                "binaryDownloadurl": "new_url",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e7"}}})
        release_data = {
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}
        }
        item2 = Component(name="")
        CycloneDxSupport.update_or_set_ext_ref(
            item2, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.BINARY_URL_COMMENT, "new_url")
        self.app.update_release(item2, release_data)
        assert len(responses.calls) == 1

        # existing URL empty, set new URL
        release_data = {
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}},
            "binaryDownloadurl": ""
        }
        self.app.update_release(item2, release_data)
        assert len(responses.calls) == 2

    @responses.activate
    def test_update_release_externalId(self) -> None:
        """Update externalId in existing release
        """
        # existing externalId, no new Id -> do nothing, "%7E" = "~"
        release_data: Dict[str, Any] = {
            "externalIds": {"package-url": "pkg:deb/debian/bash@1.0%7E1"},
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}
        }
        item = Component(name="")
        self.app.update_release(item, release_data)

        # existing Id same as new Id
        item = Component(
            name="",
            purl=PackageURL.from_string("pkg:deb/debian/bash@1.0%7E1")
        )
        self.app.update_release(item, release_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "differs from BOM id" not in captured.out

        item.purl = PackageURL.from_string("pkg:deb/debian/bash@1.0~1")
        self.app.update_release(item, release_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "differs from BOM id" not in captured.out

        # existing Id differs from new Id -> only warn
        item.purl = PackageURL.from_string("pkg:deb/debian/bash@2.0")
        self.app.update_release(item, release_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "differs from BOM id" in captured.out
        assert item.purl.to_string() == "pkg:deb/debian/bash@2.0"

        # existing Id invalid
        release_data["externalIds"]["package-url"] = "pkg:something"  # invalid purl
        self.app.update_release(item, release_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "differs from BOM id" in captured.out
        assert item.purl.to_string() == "pkg:deb/debian/bash@2.0"

        # add new Id, no existing ID
        release_data = {
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}
        }
        responses.add(
            responses.PATCH, SW360_BASE_URL + 'releases/06a6e7',
            match=[responses.matchers.json_params_matcher({
                "externalIds": {
                    "package-url": "pkg:deb/debian/bash@2.0"}})],
            # server answer with created release data
            json={
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e7"}}})
        self.app.update_release(item, release_data)
        assert len(responses.calls) == 1

        release_data = {
            "externalIds": {},
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}
        }
        self.app.update_release(item, release_data)
        assert len(responses.calls) == 2

        # add new Id to existing IDs -> assure we keep existing ones
        release_data = {
            "externalIds": {"some_id": "42"},
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}
        }
        responses.replace(
            responses.PATCH, SW360_BASE_URL + 'releases/06a6e7',
            match=[responses.matchers.json_params_matcher({
                "externalIds": {
                    "some_id": "42",
                    "package-url": "pkg:deb/debian/bash@2.0"}})],
            # server answer with created release data
            json={
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e7"}}})
        self.app.update_release(item, release_data)
        assert len(responses.calls) == 3

    @responses.activate
    def test_update_release_attachment(self) -> None:
        """Upload to existing release
        """
        responses.add(responses.GET, SW360_BASE_URL + "attachments/0123",
                      json={})

        # existing source, no new source -> do nothing
        release_data = {
            '_embedded': {'sw360:attachments': [{
                'filename': 'adduser-3.118.zip',
                'attachmentType': 'SOURCE'}]},
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}}
        item = Component(name="")
        self.app.update_release(item, release_data)

        # existing source same as new source
        release_data = {
            '_embedded': {'sw360:attachments': [{
                'filename': 'some.txt',
                'attachmentType': 'DOCUMENT'}, {
                '_links': {'self': {'href': SW360_BASE_URL + 'attachments/0123'}},
                'filename': 'adduser-3.118.zip',
                'attachmentType': 'SOURCE_SELF'}]},
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}}
        item = Component(name="")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_FILE_COMMENT, "adduser-3.118.zip")
        self.app.update_release(item, release_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "different source attachment" not in captured.out
        assert len(responses.calls) == 1

        # existing source with different hash -> do nothing
        release_data = {
            '_embedded': {'sw360:attachments': [{
                '_links': {'self': {'href': SW360_BASE_URL + 'attachments/0123'}},
                'filename': 'adduser-3.118.zip',
                'sha1': '123',
                'attachmentType': 'SOURCE'}]},
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}}
        item = Component(name="")
        extref = ExternalReference(
            type=ExternalReferenceType.DISTRIBUTION,
            comment=CaPyCliBom.SOURCE_FILE_COMMENT,
            url=XsUri("adduser-3.118.zip"))
        extref.hashes.add(HashType(
            alg=HashAlgorithm.SHA_1,
            content="456"))
        item.external_references.add(extref)
        self.app.update_release(item, release_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "different hash for source attachment" in captured.out
        assert len(responses.calls) == 2

        # existing source, different source -> do nothing
        item = Component(name="")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_FILE_COMMENT, "Readme.md")
        self.app.update_release(item, release_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "different source attachment" in captured.out
        assert len(responses.calls) == 3

        # no attachment existing -> upload
        release_data = {
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}}
        item = Component(name="")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_FILE_COMMENT, "Readme.md")
        responses.add(
            responses.POST, SW360_BASE_URL + 'releases/06a6e7/attachments',
            match=[upload_matcher("Readme.md")])
        self.app.update_release(item, release_data)
        assert len(responses.calls) == 4

        # only other attachments existing -> upload
        release_data = {
            '_embedded': {'sw360:attachments': [{
                'filename': 'some.txt',
                'attachmentType': 'DOCUMENT'}]},
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}}
        self.app.update_release(item, release_data)
        assert len(responses.calls) == 5

    @responses.activate
    def test_update_release_attachment_rejected(self) -> None:
        """Upload to existing release with rejected attachment
        """
        responses.add(responses.GET, SW360_BASE_URL + "attachments/0124",
                      json={'checkStatus': 'REJECTED'})
        release_data = {
            '_embedded': {'sw360:attachments': [{
                '_links': {'self': {'href': SW360_BASE_URL + 'attachments/0124'}},
                'filename': 'invalid.zip',
                'attachmentType': 'SOURCE'}]},
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}}

        responses.add(
            responses.POST, SW360_BASE_URL + 'releases/06a6e7/attachments',
            match=[upload_matcher("Readme.md")])

        item = Component(name="")
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_FILE_COMMENT, "Readme.md")
        self.app.update_release(item, release_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "different source attachment" not in captured.out
        assert len(responses.calls) == 2

    @responses.activate
    def test_update_release_attachment_rename(self) -> None:
        """Upload to existing release with content-disposition rename
        """
        # attachment with target file name after rename exists -> don't upload
        # (test for commit 2e403af032)
        responses.add(responses.GET, SW360_BASE_URL + "attachments/0123",
                      json={})
        responses.add(
            responses.GET, 'https://github.com/babel/babel/archive/refs/tags/v7.16.0.zip',
            headers={"content-disposition": 'attachment; filename=babel-7.16.0.zip'},
            body="content")
        release_data = {
            "sourceCodeDownloadurl": "https://github.com/babel/babel/archive/refs/tags/v7.16.0.zip",
            '_embedded': {'sw360:attachments': [{
                '_links': {'self': {'href': SW360_BASE_URL + 'attachments/0123'}},
                'filename': 'babel-7.16.0.zip',
                'attachmentType': 'SOURCE'}]},
            "_links": {"self": {"href": SW360_BASE_URL + "releases/06a6e7"}}}
        self.app.download = True
        item = Component(
            name="babel",
            version="7.16.0"
        )
        CycloneDxSupport.update_or_set_ext_ref(
            item, ExternalReferenceType.DISTRIBUTION,
            CaPyCliBom.SOURCE_URL_COMMENT, "https://github.com/babel/babel/archive/refs/tags/v7.16.0.zip")
        self.app.update_release(item, release_data)
        captured = self.capsys.readouterr()  # type: ignore
        assert "different source attachment" in captured.out

        # currently, upload_file() will do nothing if *any* source attachment exists,
        # so there should be 0 calls. If this semantics changes and content-disposition
        # handling avoids duplicated uploads, we will see 1 call, so accept 0 or 1 here.
        assert len(responses.calls) <= 1
        assert "Error" not in captured.out
        assert captured.err == ""


if __name__ == '__main__':
    APP = CapycliTestBomCreate()
    APP.setUp()
    APP.test_upload_file_allow_git_binary_upload()
