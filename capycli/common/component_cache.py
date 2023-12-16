# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import json
import os
import sys

import sw360
from capycli import get_logger
from capycli.common.print import print_red, print_text, print_yellow
from capycli.common.script_support import ScriptSupport
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class ComponentCacheManagement():
    """Manages the component cache"""

    CACHE_FILENAME = "ComponentCache.json"
    CACHE_ALL_RELEASES = "AllReleases.json"

    def __init__(self, token=None, oauth2=False, url=None) -> None:
        self.token = token
        self.oauth2 = oauth2
        self.releases = None
        self.old_releases = None
        self.sw360_url = None

    @classmethod
    def read_component_cache(cls, cachefile: str) -> dict:
        """Read the cached list of SW360 releases"""

        """
        Cache data:
          {
            "Id": "958ce9f48a488aa3b548c797212216b2",
            "CpeId": "cpe:2.3:a:rdesktop.org:rdesktop:1.8.3",
            "Name": "rdesktop",
            "Version": "1.8.3",
            "ComponentId": "3a41f30d97f3543968d6cf67e50485ca",
            "ReleaseDate": "0001-01-01T00:00:00",
            "ExternalIds": {},
            "CreatedOn": "2018-05-17T00:00:00",
            "MainlineState": 0,
            "ClearingState": 0,
            "CreatedBy": null,
            "CreatorDepartment": null,
            "Languages": [],
            "DownloadUrl": "https://github.com/rdesktop/rdesktop/tree/v1.8.3",
            "Href": "https://sw360.siemens.com/resource/api/releases/958c...2",
            "SourceFile": "rdesktop-1.8.3.zip",
            "SourceFileHash": "3989b3dd9856346417f57a6a31cd04b4cf67a646"
          },
        """

        try:
            with open(cachefile) as fin:
                release_cache = json.load(fin)
        except FileNotFoundError:
            print_yellow("Component cache file '" + cachefile + "'not found!")
            release_cache = None

        return release_cache

    @classmethod
    def get_attachment(cls, release: dict, att_type: str):
        """Return the first attachment that matches the specified type"""
        if "_embedded" not in release:
            return None

        if "sw360:attachments" not in release["_embedded"]:
            return None

        # unnecessary complex SW360 data
        # should be for att in release["_embedded"]["sw360:attachments"]:
        # but it is a list in a list
        if len(release["_embedded"]["sw360:attachments"]) == 0:
            return None

        if type(release["_embedded"]["sw360:attachments"][0]) is list:
            for att in release["_embedded"]["sw360:attachments"][0]:
                if att["attachmentType"] == att_type:
                    return att
        else:
            for att in release["_embedded"]["sw360:attachments"]:
                if att["attachmentType"] == att_type:
                    return att

        return None

    @staticmethod
    def get_value_or_default(release, key):
        """Return a dictionary value if it exists, otherwise an empty string"""
        if key not in release:
            return ""

        return release[key]

    def read_existing_component_cache(self, cachefile: str) -> int:
        """Read the (already existing) cache file"""
        try:
            with open(cachefile) as fin:
                self.old_releases = json.load(fin)
        except FileNotFoundError:
            self.old_releases = None

        if self.old_releases:
            return len(self.old_releases)
        else:
            return 0

    def get_rest_client(self, token: str = None, oauth2: bool = False, url: str = None):
        """Get an instance of the REST API client"""
        self.sw360_url = os.environ.get("SW360ServerUrl", None)
        sw360_api_token = os.environ.get("SW360ProductionToken", None)

        if token:
            sw360_api_token = token

        if url:
            self.sw360_url = url

        if self.sw360_url[-1] != "/":
            self.sw360_url += "/"

        if not self.sw360_url:
            print_red("  No SW360 server URL specified!")
            sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SW360)

        if not sw360_api_token:
            print_red("  No SW360 API token specified!")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        client = sw360.sw360_api.SW360(self.sw360_url, sw360_api_token, oauth2)
        if not client.login_api(sw360_api_token):
            print_red("ERROR: login failed")
            sys.exit(ResultCode.RESULT_AUTH_ERROR)

        return client

    @classmethod
    def convert_release_details(cls, client, details) -> dict:
        """
        Convert the SW360 release data into our own data.
        """
        if not details:
            return

        try:
            release = {}
            release["Id"] = client.get_id_from_href(
                details["_links"]["self"]["href"]
            )
            release["Sw360Id"] = release["Id"]
            release["CpeId"] = cls.get_value_or_default(details, "cpeId")
            release["Name"] = details["name"]
            release["Version"] = cls.get_value_or_default(details, "version")
            release["ComponentId"] = client.get_id_from_href(
                details["_links"]["sw360:component"]["href"]
            )
            release["ReleaseDate"] = cls.get_value_or_default(
                details, "releaseDate"
            )
            if "externalIds" in details:
                release["ExternalIds"] = details["externalIds"]
            else:
                release["ExternalIds"] = []
            release["CreatedOn"] = cls.get_value_or_default(details, "createdOn")
            release["MainlineState"] = cls.get_value_or_default(
                details, "mainlineState"
            )
            release["ClearingState"] = cls.get_value_or_default(
                details, "clearingState"
            )
            release["CreatedBy"] = ""
            release["CreatorDepartment"] = ""
            release["Languages"] = []
            release["DownloadUrl"] = cls.get_value_or_default(
                details, "sourceCodeDownloadurl"
            )
            release["Href"] = ""

            att = cls.get_attachment(details, "SOURCE")
            if att:
                release["SourceFile"] = att["filename"]
                release["SourceFileHash"] = att.get("sha1", "")
            else:
                release["SourceFile"] = ""
                release["SourceFileHash"] = ""

            att = cls.get_attachment(details, "BINARY")
            if att:
                release["BinaryFile"] = att["filename"]
                release["BinaryFileHash"] = att.get("sha1", "")
            else:
                release["BinaryFile"] = ""
                release["BinaryFileHash"] = ""

            return release
        except Exception as ex:
            print_red(
                "  Error getting details on " + details["_links"]["self"]["href"] + " " +
                repr(ex))

    def refresh_component_cache(
            self, cachefile: str, fast: bool, token: str = None,
            oauth2: bool = False, url: str = None):
        """
        Read all releases from SW360. May take 90 minutes!
        The new multi-threaded approach takes about one hour for 25.000
        releases.
        """
        client = self.get_rest_client(token, oauth2, url)

        print(" Retrieving information on all release details (approx. 2 minutes)...")
        allnew = client.get_all_releases(all_details=True)

        # reset global list
        self.releases = []

        for newdata in allnew:
            internal = self.convert_release_details(client, newdata)
            if internal:
                self.releases.append(internal)

        print_text(" Got all " + str(len(self.releases)) + " releases.")

        with open(cachefile, "w") as fout:
            json.dump(self.releases, fout, indent=4)

        print_text(ScriptSupport.get_time() + " end.")

        return self.releases
