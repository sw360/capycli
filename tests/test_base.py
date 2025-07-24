# -------------------------------------------------------------------------------
# Copyright (c) 2021-2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, manuel.schaffer@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import sys
import unittest
from io import BytesIO, TextIOWrapper
from typing import Any, Dict, List

import responses

SW360_BASE_URL = "https://my.server.com/resource/api/"


class AppArguments():
    # Examples
    # command=['bom', 'diff', '.\\Tests\\bom_diff_1.json', '.\\tests\\bom_diff_1.json']

    def __init__(self) -> None:
        self.cachefile: str = ""
        self.command: List[str] = []
        self.create_overview: str = ""
        self.cyclonedx: bool = False
        self.dbx: bool = False
        self.debug: bool = False
        self.destination: str = ""
        self.download: bool = False
        self.ex: bool = False
        self.filterfile: str = ""
        self.help: bool = False
        self.id: str = ""
        self.inputfile: str = ""
        self.matchmode: str = ""
        self.name: str = ""
        self.ncli: bool = False
        self.nconf: bool = False
        self.nocache: bool = False
        self.oauth2: bool = False
        self.old_version: str = ""
        self.outputfile: str = ""
        self.package_source: str = ""
        self.raw_input: str = ""
        self.refresh_cache: bool = False
        self.result_required: bool = False
        self.search_meta_data: bool = False
        self.similar: bool = False
        self.source: str = ""
        self.sw360_token: str = ""
        self.sw360_url: str = ""
        self.verbose: bool = False
        self.verbose2: bool = False
        self.version: str = ""
        self.write_mapresult: str = ""
        self.xml: bool = False
        self.all: bool = False
        self.mode: str = "all"
        self.format: str = ""
        self.force_exit: str = ""
        self.inputformat: str = ""
        self.outputformat: str = ""
        self.remote_granularity_list: str = ""
        self.local_granularity_list: str = ""
        self.github_token: str = ""
        self.force_error: bool = False
        self.project_mainline_state = ""
        self.copy_from = ""


class TestBasePytest:
    MYTOKEN = "MYTOKEN"
    MYURL = "https://my.server.com/"
    ERROR_MSG_NO_LOGIN = "Unable to login"

    @staticmethod
    def delete_file(filename: str) -> None:
        """Delete the given file."""
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as ex:
            print("Error removing file:", filename, repr(ex))

    @staticmethod
    def dump_textfile(text: str, filename: str) -> None:
        """Dump the given text to the given file."""
        with open(filename, "w") as outfile:
            outfile.write(text)

    @staticmethod
    def capture_stderr(func: Any, *args: Any, **kwargs: Any) -> str:
        """Capture stderr for the given function and return result as string"""
        # setup the environment
        old_stderr = sys.stderr
        sys.stderr = TextIOWrapper(BytesIO(), sys.stderr.encoding)

        error = None

        try:
            func(*args, **kwargs)
        except Exception as err:
            error = err
        finally:
            # get output
            sys.stderr.seek(0)       # jump to the start
            out = sys.stderr.read()  # read output

            # restore stdout
            sys.stderr.close()
            sys.stderr = old_stderr

        if error is None:
            return out
        print(out)
        sys.stdout.flush()
        raise error

    @staticmethod
    def capture_stdout(func: Any, *args: Any, **kwargs: Any) -> str:
        """Capture stdout for the given function and return result as string"""
        # setup the environment
        old_stdout = sys.stdout
        sys.stdout = TextIOWrapper(BytesIO(), sys.stdout.encoding)

        error = None

        try:
            func(*args, **kwargs)
        except Exception as err:
            error = err
        finally:
            # get output
            sys.stdout.seek(0)       # jump to the start
            out = sys.stdout.read()  # read output

            # restore stdout
            sys.stdout.close()
            sys.stdout = old_stdout

        if error is None:
            return out
        print(out)
        sys.stdout.flush()
        raise error

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

    @staticmethod
    def get_project_for_test() -> Dict[str, Any]:
        """
        Return a SW360 project for unit testing.
        """
        project = {
            "name": "CaPyCLI",
            "description": "Software clearing for CaPyCLI, the clearing automation scripts for Python",
            "version": "1.9.0",
            "externalIds": {
                "com.siemens.code.project.id": "69287"
            },
            "additionalData": {},
            "createdOn": "2023-03-14",
            "businessUnit": "SI",
            "state": "ACTIVE",
            "tag": "Demo",
            "clearingState": "IN_PROGRESS",
            "projectResponsible": "thomas.graf@siemens.com",
            "roles": {},
            "securityResponsibles": [
                "thomas.graf@siemens.com"
            ],
            "projectOwner": "thomas.graf@siemens.com",
            "ownerAccountingUnit": "",
            "ownerGroup": "",
            "ownerCountry": "",
            "preevaluationDeadline": "",
            "systemTestStart": "",
            "systemTestEnd": "",
            "deliveryStart": "",
            "phaseOutSince": "",
            "enableSvm": True,
            "considerReleasesFromExternalList": False,
            "licenseInfoHeaderText": "dummy",
            "enableVulnerabilitiesDisplay": True,
            "clearingSummary": "",
            "specialRisksOSS": "",
            "generalRisks3rdParty": "",
            "specialRisks3rdParty": "",
            "deliveryChannels": "",
            "remarksAdditionalRequirements": "",
            "projectType": "INNER_SOURCE",
            "visibility": "EVERYONE",
            "linkedProjects": [],
            "linkedReleases": [
                {
                    "createdBy": "thomas.graf@siemens.com",
                    "release": "https://my.server.com/resource/api/releases/r001",
                    "mainlineState": "SPECIFIC",
                    "comment": "Automatically updated by SCC",
                    "createdOn": "2023-03-14",
                    "relation": "UNKNOWN"
                },
                {
                    "createdBy": "thomas.graf@siemens.com",
                    "release": "https://my.server.com/resource/api/releases/r002",
                    "mainlineState": "MAINLINE",
                    "comment": "Automatically updated by SCC",
                    "createdOn": "2023-03-14",
                    "relation": "DYNAMICALLY_LINKED"
                }
            ],
            "_links": {
                "self": {
                    "href": "https://my.server.com/resource/api/projects/p001"
                }
            },
            "_embedded": {
                "createdBy": {
                    "email": "thomas.graf@siemens.com",
                    "deactivated": False,
                    "fullName": "Thomas Graf",
                    "_links": {
                        "self": {
                            "href": "https://my.server.com/resource/api/users/byid/thomas.graf%2540siemens.com"
                        }
                    }
                },
                "sw360:releases": [
                    {
                        "name": "wheel",
                        "version": "0.38.4",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/releases/r001"
                            }
                        }
                    },
                    {
                        "name": "cli-support",
                        "version": "1.3",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/releases/r002"
                            }
                        }
                    }
                ]
            }
        }

        return project

    @staticmethod
    def get_release_wheel_for_test() -> Dict[str, Any]:
        """
        Return a SW360 release for unit testing.
        """
        release_wheel = {
            "name": "wheel",
            "version": "0.38.4",
            "releaseDate": "",
            "componentType": "OSS",
            "externalIds": {
                "package-url": "pkg:pypi/wheel@0.38.4"
            },
            "createdOn": "2023-02-16",
            "mainlineState": "SPECIFIC",
            "clearingState": "APPROVED",
            "createdBy": "thomas.graf@siemens.com",
            "contributors": [],
            "subscribers": [],
            "roles": {},
            "otherLicenseIds": [],
            "languages": [
                "Python"
            ],
            "operatingSystems": [],
            "softwarePlatforms": [],
            "sourceCodeDownloadurl": "https://github.com/pypa/wheel/archive/refs/tags/0.38.4.zip",
            "binaryDownloadurl": "",
            "cpeId": "",
            "eccInformation": {
                "al": "N",
                "eccn": "N",
                "eccStatus": "APPROVED"
            },
            "_links": {
                "sw360:component": {
                    "href": "https://my.server.com/resource/api/components/c001"
                },
                "self": {
                    "href": "https://my.server.com/resource/api/releases/r001"
                },
                "curies": [
                    {
                        "href": "https://my.server.com/resource/docs/{rel}.html",
                        "name": "sw360",
                        "templated": True
                    }
                ]
            },
            "_embedded": {
                "sw360:licenses": [
                    {
                        "OSIApproved": "NA",
                        "FSFLibre": "NA",
                        "checked": True,
                        "shortName": "MIT",
                        "fullName": "MIT License",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/licenses/MIT"
                            }
                        }
                    }
                ],
                "sw360:attachments": [
                    {
                        "filename": "CLIXML_wheel-0.38.4.xml",
                        "sha1": "ccd9f1ed2f59c46ff3f0139c05bfd76f83fd9851",
                        "attachmentType": "COMPONENT_LICENSE_INFO_XML",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/attachments/r001a001"
                            }
                        }
                    },
                    {
                        "filename": "wheel-0.38.4.zip",
                        "sha1": "a30b637ddfbb1f017eafb0f60a837442937c5eb0",
                        "attachmentType": "SOURCE",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/attachments/r001a002"
                            }
                        }
                    }
                ]
            }
        }

        return release_wheel

    @staticmethod
    def get_release_cli_for_test() -> Dict[str, Any]:
        """
        Return a SW360 release for unit testing.
        """
        release_cli = {
            "name": "cli-support",
            "version": "1.3",
            "releaseDate": "",
            "componentType": "OSS",
            "externalIds": {
                "package-url": "pkg:pypi/cli-support@1.3"
            },
            "createdOn": "2023-03-14",
            "repository": {
                "url": "https://github.com/sw360/clipython.git",
                "repositorytype": "GIT"
            },
            "mainlineState": "SPECIFIC",
            "clearingState": "APPROVED",
            "createdBy": "thomas.graf@siemens.com",
            "contributors": [],
            "subscribers": [],
            "roles": {},
            "otherLicenseIds": [],
            "languages": [
                "Python"
            ],
            "operatingSystems": [],
            "softwarePlatforms": [],
            "sourceCodeDownloadurl": "https://github.com/sw360/clipython",
            "binaryDownloadurl": "",
            "cpeId": "",
            "eccInformation": {
                "al": "N",
                "eccn": "N",
                "eccStatus": "APPROVED"
            },
            "_links": {
                "sw360:component": {
                    "href": "https://my.server.com/resource/api/components/c001"
                },
                "self": {
                    "href": "https://my.server.com/resource/api/releases/r002"
                },
                "curies": [
                    {
                        "href": "https://my.server.com/resource/docs/{rel}.html",
                        "name": "sw360",
                        "templated": True
                    }
                ]
            },
            "_embedded": {
                "sw360:licenses": [
                    {
                        "OSIApproved": "NA",
                        "FSFLibre": "NA",
                        "checked": True,
                        "shortName": "MIT",
                        "fullName": "MIT License",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/licenses/MIT"
                            }
                        }
                    }
                ],
                "sw360:attachments": [
                    {
                        "filename": "clipython-1.3.0.zip",
                        "sha1": "0fc54fe4bb73989ce669ad26a8976e7753d31acb",
                        "attachmentType": "SOURCE",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/attachments/r002a001"
                            }
                        }
                    },
                    {
                        "filename": "CLIXML_clipython-1.3.0.xml",
                        "sha1": "dd4c38387c6811dba67d837af7742d84e61e20de",
                        "attachmentType": "COMPONENT_LICENSE_INFO_XML",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/attachments/r002a002"
                            }
                        }
                    }
                ]
            }
        }

        return release_cli

    def get_cli_file_mit(self) -> str:
        """
        Return the XML contents of a CLI file with MIT license.
        """
        return """<?xml version="1.0" encoding="utf-8" standalone="no"?>
<ComponentLicenseInformation
    component="charset_normalizer-3.1.0.zip" creator="thomas.graf@siemens.com"
    date="2023-03-14" baseDoc="" toolUsed="CliEditor" componentID="" includesAcknowledgements="false"
    componentSHA1="67878344e28168dd11b9d6f9c3dbd80a4c1e1b9e" Version="1.5">
  <GeneralInformation>
    <ReportId>168fafd4-c25b-11ed-8ced-6f5dd240728b</ReportId>
    <ReviewedBy />
    <ComponentName>charset-normalizer</ComponentName>
    <Community>NA</Community>
    <ComponentVersion>3.1.0</ComponentVersion>
    <ComponentHash>67878344E28168DD11B9D6F9C3DBD80A4C1E1B9E</ComponentHash>
    <ComponentReleaseDate>NA</ComponentReleaseDate>
    <LinkComponentManagement></LinkComponentManagement>
    <LinkScanTool />
    <ComponentId>
      <Type>package-url</Type>
      <Id>pkg:pypi/charset-normalizer@3.1.0</Id>
    </ComponentId>
  </GeneralInformation>
  <AssessmentSummary>
    <GeneralAssessment><![CDATA[N/A]]></GeneralAssessment>
    <CriticalFilesFound>None</CriticalFilesFound>
    <DependencyNotes>None</DependencyNotes>
    <ExportRestrictionsFound>None</ExportRestrictionsFound>
    <UsageRestrictionsFound>None</UsageRestrictionsFound>
    <AdditionalNotes><![CDATA[NA]]></AdditionalNotes>
  </AssessmentSummary>
  <License type="global" name="MIT" spdxidentifier="MIT">
    <Content><![CDATA[Permission is hereby granted]]></Content>
    <Files><![CDATA[charset_normalizer/__init__.py]]></Files>
    <FileHash><![CDATA[7d1b9e407eaae7983be386ef9b9a21642ce140e9]]></FileHash>
    <Tags></Tags>
  </License>
  <Copyright>
    <Content><![CDATA[© 2012 XXX]]></Content>
    <Files><![CDATA[README.md]]></Files>
    <FileHash><![CDATA[4e033debe19d28cb1b17adfbf7c1b9f2383281fa]]></FileHash>
  </Copyright>
  <IrrelevantFiles>
    <Files><![CDATA[]]></Files>
  </IrrelevantFiles>
  <Tags></Tags>
  <Comment></Comment>
  <ExternalIds />
</ComponentLicenseInformation>
            """


class TestBase(unittest.TestCase, TestBasePytest):
    pass
