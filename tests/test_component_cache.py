# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import responses

from capycli.common.component_cache import ComponentCacheManagement
from tests.test_base import TestBase


class TestComponentCache(TestBase):
    MYTOKEN = "MYTOKEN"
    MYURL = "https://my.server.com/"
    ERROR_MSG_NO_LOGIN = "Unable to login"
    CACHE_FILE = "dummy_cache.json"

    @responses.activate
    def test_refresh_component_cache_with_cache(self) -> None:
        sut = ComponentCacheManagement()

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
                            "sourceCodeDownloadurl" : "http://www.google.com",
                            "binaryDownloadurl" : "http://www.google.com/binaries",
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

        result = sut.refresh_component_cache(
            self.CACHE_FILE,
            fast=True,
            token=self.MYTOKEN,
            oauth2=False,
            url=self.MYURL,
        )

        self.assertIsNotNone(result)
        self.assertEqual(1, len(result))
        self.assertEqual("colorama", result[0]["Name"])
        self.assertEqual("0.4.3", result[0]["Version"])
        self.assertEqual("3765276512", result[0]["Id"])
        self.assertEqual("17653524", result[0]["ComponentId"])

        self.assertEqual("http://www.google.com", result[0]["DownloadUrl"])
        self.assertEqual("spring-core-4.3.4.zip", result[0]["SourceFile"])
        self.assertEqual("da373e491d3863477568896089ee9457bc316799", result[0]["SourceFileHash"])

        self.assertEqual("spring-core-4.3.4.RELEASE.jar", result[0]["BinaryFile"])
        self.assertEqual("da373e491d3863477568896089ee9457bc316783", result[0]["BinaryFileHash"])

        self.assertIsNotNone(result[0]["ExternalIds"])
        self.assertEqual("pkg:pypi/colorama@0.4.3", result[0]["ExternalIds"]["package-url"])

    @responses.activate
    def test_refresh_component_cache_no_cache(self) -> None:
        sut = ComponentCacheManagement()

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
                            "sourceCodeDownloadurl" : "http://www.google.com",
                            "binaryDownloadurl" : "http://www.google.com/binaries",
                            "_links": {
                                "sw360:component" : {
                                    "href" : "https://sw360.org/api/components/17653524"
                                },
                                "self": {
                                    "href": "https://my.server.com/resource/api/releases/3765276512"
                                }
                            },
                            "_embedded" : {
                                "sw360:attachments" : [ {
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
                                    } ]
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

        result = sut.refresh_component_cache(
            self.CACHE_FILE,
            fast=True,
            token=self.MYTOKEN,
            oauth2=False,
            url=self.MYURL,
        )

        self.assertIsNotNone(result)
        self.assertEqual(1, len(result))
        self.assertEqual("colorama", result[0]["Name"])
        self.assertEqual("0.4.3", result[0]["Version"])
        self.assertEqual("3765276512", result[0]["Id"])
        self.assertEqual("17653524", result[0]["ComponentId"])

        self.assertEqual("http://www.google.com", result[0]["DownloadUrl"])
        self.assertEqual("spring-core-4.3.4.zip", result[0]["SourceFile"])
        self.assertEqual("da373e491d3863477568896089ee9457bc316799", result[0]["SourceFileHash"])

        self.assertEqual("spring-core-4.3.4.RELEASE.jar", result[0]["BinaryFile"])
        self.assertEqual("da373e491d3863477568896089ee9457bc316783", result[0]["BinaryFileHash"])

        self.assertIsNotNone(result[0]["ExternalIds"])
        self.assertEqual("pkg:pypi/colorama@0.4.3", result[0]["ExternalIds"]["package-url"])


if __name__ == "__main__":
    APP = TestComponentCache()
    APP.test_refresh_component_cache_with_cache()
