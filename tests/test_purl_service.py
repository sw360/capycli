# -------------------------------------------------------------------------------
# Copyright (c) 2022-2023 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com, thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from typing import Any, Dict, List

import responses
import unittest
from packageurl import PackageURL

from capycli.bom.map_bom import MapBom
from capycli.common.purl_service import PurlService
from tests.test_base import SW360_BASE_URL

sw360_purl_releases: List[Dict[str, Any]] = [
    {
        # in a purl, "~"" may be encoded as %7E and "+" must be "%2B"
        "externalIds": {
            "package-url": "pkg:deb/debian/sed@4.4%2B1%7E2?type=source"},
        "_links": {"self": {
            "href": SW360_BASE_URL + "releases/0623"}}},
    {
        "externalIds": {
            "package-url": "pkg:gem/mini_portile2@2.4.0"},
        "_links": {"self": {
            "href": SW360_BASE_URL + "releases/06a6"}}},
]

sw360_purl_components: List[Dict[str, Any]] = [
    {
        "externalIds": {
            "package-url": "pkg:deb/debian/sed?type=source"},
        "_links": {"self": {
            "href": SW360_BASE_URL + "components/a035"}}},
    {
        "externalIds": {
            "package-url": "pkg:gem/mini_portile2"},
        "_links": {"self": {
            "href": SW360_BASE_URL + "components/04a6"}}},
]


class TestPurlService(unittest.TestCase):

    @responses.activate
    def setUp(self) -> None:
        self.app: MapBom = MapBom()
        responses.add(responses.GET, SW360_BASE_URL, json={"status": "ok"})
        self.app.login("sometoken", "https://my.server.com")

    def purl_build_cache(self) -> PurlService:
        responses.add(
            responses.GET,
            SW360_BASE_URL + "releases/searchByExternalIds?package-url=",
            json={"_embedded": {"sw360:releases": sw360_purl_releases}})
        responses.add(
            responses.GET,
            SW360_BASE_URL + "components/searchByExternalIds?package-url=",
            json={"_embedded": {"sw360:components": sw360_purl_components}})

        assert self.app.client is not None
        if self.app.client:
            purl_service = PurlService(self.app.client)
            purl_service.build_purl_cache()
            assert purl_service.purl_cache["deb"]["debian"]["sed"][None][0]["href"] == sw360_purl_components[0]["_links"]["self"]["href"] # noqa
            assert purl_service.purl_cache["gem"][None]["mini_portile2"][None][0]["href"] == sw360_purl_components[1]["_links"]["self"]["href"] # noqa
            assert purl_service.purl_cache["deb"]["debian"]["sed"]["4.4+1~2"][0]["href"] == sw360_purl_releases[0]["_links"]["self"]["href"] # noqa
            assert purl_service.purl_cache["gem"][None]["mini_portile2"]["2.4.0"][0]["href"] == sw360_purl_releases[1]["_links"]["self"]["href"] # noqa

        return purl_service

    @responses.activate
    def test_purl_build_cache(self) -> None:
        self.purl_build_cache()

    @responses.activate
    def test_purl_build_cache__for_multi_purl_component(self) -> None:
        responses.add(
            responses.GET,
            SW360_BASE_URL + "releases/searchByExternalIds?package-url=",
            json={"_embedded": {"sw360:releases": []}})

        purl_list = "[\"pkg:maven/org.springframework/spring-tx\",\"pkg:maven/org.springframework/spring-jcl\"]"
        responses.add(
            responses.GET,
            SW360_BASE_URL + "components/searchByExternalIds?package-url=",
            # only first entry for components so we need to search via release
            json={"_embedded": {"sw360:components": [
                {
                    "name": "Spring Framework",
                    "externalIds": {
                        "package-url": purl_list
                    },
                    "_links": {"self": {
                        "href": SW360_BASE_URL + "components/05a6"}
                    }
                }
            ]}})

        assert self.app.client is not None
        if self.app.client:
            purl_service = PurlService(self.app.client)
            purl_service.build_purl_cache()

            assert purl_service.purl_cache["maven"]["org.springframework"]["spring-tx"][None] == [{
                "purl": PackageURL("maven", "org.springframework", "spring-tx"),
                "href": SW360_BASE_URL + "components/05a6"}]
            assert purl_service.purl_cache["maven"]["org.springframework"]["spring-jcl"][None] == [{
                "purl": PackageURL("maven", "org.springframework", "spring-jcl"),
                "href": SW360_BASE_URL + "components/05a6"}]

    @responses.activate
    def test_multiple_purls(self) -> None:
        # add multiple purls for same release and component
        duplicate_releases = {"_embedded": {"sw360:releases": sw360_purl_releases + [
            {"externalIds": {"package-url": "pkg:deb/debian/sed@4.4%2B1%7E2?arch=source"},
             "_links": {"self": {"href": SW360_BASE_URL + "releases/0623"}}},
            {"externalIds": {"package-url": "pkg:deb/debian/sed@4.4%2B1%7E2"},
             "_links": {"self": {"href": SW360_BASE_URL + "releases/0623"}}}]}}
        duplicate_components = {"_embedded": {"sw360:components": sw360_purl_components + [
            {"externalIds": {"package-url": "pkg:deb/debian/sed"},
             "_links": {"self": {"href": SW360_BASE_URL + "components/a035"}}}]}}
        # only duplicates => purl_cache must be completely empty
        responses.add(responses.GET,
                      SW360_BASE_URL + "releases/searchByExternalIds?package-url=",
                      json=duplicate_releases)
        responses.add(responses.GET,
                      SW360_BASE_URL + "components/searchByExternalIds?package-url=",
                      json=duplicate_components)

        assert self.app.client is not None
        purl_service = PurlService(self.app.client)
        purl_service.build_purl_cache()

        # returns all candidates including duplicates
        res = purl_service.search_releases_by_purl(PackageURL("deb", "debian", "sed", "4.4+1~2"))
        # all purls point to the same release
        assert len(res) == 1
        assert res[0] == sw360_purl_releases[0]["_links"]["self"]["href"]

        # returns all candidates including duplicates
        res = purl_service.search_components_by_purl(PackageURL("deb", "debian", "sed"))
        # all purls point to the same component
        assert len(res) == 1
        assert res[0] == sw360_purl_components[0]["_links"]["self"]["href"]

    @responses.activate
    def test_purl_duplicates(self) -> None:
        # add duplicate for release and component
        duplicate_releases = {
            "_embedded": {"sw360:releases": sw360_purl_releases[1:2] + [{
                "externalIds": {
                    "package-url": "pkg:gem/mini_portile2@2.4.0"},
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/1234"}}}]}}
        duplicate_components = {
            "_embedded": {"sw360:components": sw360_purl_components[0:1] + [{
                "externalIds": {
                    "package-url": "pkg:deb/debian/sed?type=source"},
                "_links": {"self": {
                    "href": SW360_BASE_URL + "components/1234"}}}]}}
        # only duplicates => purl_cache must be completely empty
        responses.add(responses.GET,
                      SW360_BASE_URL + "releases/searchByExternalIds?package-url=",
                      json=duplicate_releases)
        responses.add(responses.GET,
                      SW360_BASE_URL + "components/searchByExternalIds?package-url=",
                      json=duplicate_components)

        assert self.app.client is not None
        if not self.app.client:
            return

        purl_service = PurlService(self.app.client)
        purl_service.build_purl_cache()
        # returns all candidates including duplicates
        res = purl_service.search_releases_by_purl(PackageURL("gem", name="mini_portile2", version="2.4.0"))
        assert len(res) == 2

        # returns all candidates including duplicates
        res = purl_service.search_components_by_purl(PackageURL("deb", "debian", "sed",
                                                                qualifiers={"type": "source"}))
        assert len(res) == 2

        # duplicates + normal data => duplicates must not be in purl_cache
        duplicate_releases["_embedded"]["sw360:releases"].append(
            sw360_purl_releases[0])
        duplicate_components["_embedded"]["sw360:components"].append(
            sw360_purl_components[1])
        responses.replace(responses.GET,
                          SW360_BASE_URL + "releases/searchByExternalIds?package-url=",
                          json=duplicate_releases)
        responses.replace(responses.GET,
                          SW360_BASE_URL + "components/searchByExternalIds?package-url=",
                          json=duplicate_components)

        purl_service = PurlService(self.app.client)
        purl_service.build_purl_cache()
        res = purl_service.search_releases_by_purl(PackageURL("gem", name="mini_portile2", version="2.4.0"))
        assert len(res) == 2
        res = purl_service.search_releases_by_purl(PackageURL("deb", "debian", "sed", "4.4+1~2",
                                                              qualifiers={"type": "source"}))
        assert len(res) == 1
        assert res[0] == sw360_purl_releases[0]["_links"]["self"]["href"]

        res = purl_service.search_components_by_purl(PackageURL("deb", "debian", "sed",
                                                                qualifiers={"type": "source"}))
        assert len(res) == 2
        res = purl_service.search_components_by_purl(PackageURL("gem", name="mini_portile2"))
        assert len(res) == 1
        assert res[0] == sw360_purl_components[1]["_links"]["self"]["href"]

    @responses.activate
    def test_purl_invalid(self) -> None:
        invalid_releases = {
            "_embedded": {"sw360:releases": sw360_purl_releases + [{
                "externalIds": {
                    # invalid purl: no "pkg:" prefix
                    "package-url": "gem/mini_portile2@2.0.0"},
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/1111"}}}]}}
        responses.add(responses.GET,
                      SW360_BASE_URL + "releases/searchByExternalIds?package-url=",
                      json=invalid_releases)
        responses.add(responses.GET,
                      SW360_BASE_URL + "components/searchByExternalIds?package-url=",
                      json={"_embedded": {"sw360:components": sw360_purl_components}})

        assert self.app.client is not None
        if not self.app.client:
            return

        purl_service = PurlService(self.app.client)
        purl_service.build_purl_cache()
        assert "2.0.0" not in purl_service.purl_cache["gem"][None]["mini_portile2"]

    @responses.activate
    def test_purl_search_release(self) -> None:
        purl_service = self.purl_build_cache()

        res = purl_service.search_releases_by_purl(
            PackageURL("deb", "debian", "sed", "4.4+1~2", qualifiers={"type": "source"}))
        assert res[0] == sw360_purl_releases[0]["_links"]["self"]["href"]

    @responses.activate
    def test_purl_search_component(self) -> None:
        purl_service = self.purl_build_cache()
        res = purl_service.search_components_by_purl(
            PackageURL.from_string(sw360_purl_components[0]["externalIds"]["package-url"]))
        assert res[0] == sw360_purl_components[0]["_links"]["self"]["href"]

        res = purl_service.search_components_by_purl(
            PackageURL("deb", "debian", "mypkg"))
        assert res == []

    @responses.activate
    def test_purl_search_component_via_release(self) -> None:
        responses.add(
            responses.GET,
            SW360_BASE_URL + "releases/searchByExternalIds?package-url=",
            json={"_embedded": {"sw360:releases": sw360_purl_releases}})
        responses.add(
            responses.GET,
            SW360_BASE_URL + "components/searchByExternalIds?package-url=",
            # only first entry for components so we need to search via release
            json={"_embedded": {"sw360:components": sw360_purl_components[0:1]}})

        assert self.app.client is not None
        if not self.app.client:
            return

        purl_service = PurlService(self.app.client)
        purl_service.build_purl_cache()

        # search for a component where we only have one release entry
        responses.add(
            responses.GET,
            sw360_purl_releases[1]["_links"]["self"]["href"],
            json={"_links": {"sw360:component": {"href": "myurl"}}})
        res = purl_service.search_components_by_purl(
            PackageURL.from_string(sw360_purl_components[1]["externalIds"]["package-url"]))
        assert res[0] == "myurl"

    @responses.activate
    def test_purl_search_component_via_release_conflicts(self) -> None:
        responses.add(
            responses.GET,
            SW360_BASE_URL + "releases/searchByExternalIds?package-url=",
            json={"_embedded": {"sw360:releases": sw360_purl_releases + [{
                "externalIds": {
                    "package-url": "pkg:gem/mini_portile2@2.2.0"},
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06dd"}}}]
            }})
        responses.add(
            responses.GET,
            SW360_BASE_URL + "components/searchByExternalIds?package-url=",
            # only first entry for components so we need to search via release
            json={"_embedded": {"sw360:components": sw360_purl_components[0:1]}})

        responses.add(
            responses.GET,
            sw360_purl_releases[1]["_links"]["self"]["href"],
            json={"_links": {"sw360:component": {"href": SW360_BASE_URL + "components/1"}}})
        responses.add(
            responses.GET,
            SW360_BASE_URL + "releases/06dd",
            json={"_links": {"sw360:component": {"href": SW360_BASE_URL + "components/2"}}})

        assert self.app.client is not None
        if not self.app.client:
            return

        purl_service = PurlService(self.app.client)
        # request all results
        res = purl_service.search_components_by_purl(
            PackageURL.from_string(sw360_purl_components[1]["externalIds"]["package-url"]))
        assert len(res) == 2
        if res[0] == SW360_BASE_URL + "components/2":
            assert res[1] == SW360_BASE_URL + "components/1"
        elif res[0] == SW360_BASE_URL + "components/1":
            assert res[1] == SW360_BASE_URL + "components/2"
        else:
            assert False, "Unexpected result: " + str(res)

    def test_purl_search_component_and_release(self) -> None:
        test_cache: Dict[str, Any] = {
            "maven": {
                "org.test": {
                    "c1": {
                        None: [{
                            "purl": PackageURL("maven", "org.test", "c1"),
                            "href": "self/href/c1"}],
                        "1": [{
                            "purl": PackageURL("maven", "org.test", "c1", "1"),
                            "href": "self/href/r1"}]
                    }
                }
            }
        }

        assert self.app.client is not None
        if not self.app.client:
            return

        purl_service = PurlService(self.app.client, cache=test_cache)
        c = purl_service.search_components_by_purl(PackageURL("maven", "org.test", "c1", "1"))
        r = purl_service.search_releases_by_purl(PackageURL("maven", "org.test", "c1", "1"))
        self.assertIsNotNone(c)
        self.assertIsNotNone(r)
        self.assertEqual(c[0], "self/href/c1")
        self.assertEqual(r[0], "self/href/r1")


if __name__ == "__main__":
    APP = TestPurlService()
    APP.setUp()
    APP.test_purl_build_cache()
