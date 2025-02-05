# -------------------------------------------------------------------------------
# Copyright (c) 2023-2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import json
import os
from typing import Any, Dict, List, Tuple

import responses
import responses.matchers

from capycli.main.result_codes import ResultCode
from capycli.project.create_project import CreateProject
from tests.test_base import AppArguments, TestBase


def min_json_matcher(check: Dict[str, Any]) -> Any:
    # responses.matcher.multipart_matcher didn't work for me
    def match(request: Any) -> Tuple[bool, str]:
        result = True
        reason = ""

        if isinstance(request.body, bytes):
            request_body = request.body.decode("utf-8")
        print(request)

        json_body = json.loads(request_body) if request_body else {}
        for key in check:
            if key not in json_body:
                result = False
                reason = ("Entry " + key + " not found!")
                break

            if check[key] != json_body[key]:
                result = False
                reason = ("Entry[" + key + "] = '" + json_body[key] + "' does not match expected " + check[key])
                break

        return result, reason
    return match


def update_release_matcher(releases: List[str]) -> Any:
    """
    Matches the updated releases.

    Args:
        releases (list[str]): list of releases
    """
    def match(request: Any) -> Tuple[bool, str]:
        result = True
        reason = ""

        if isinstance(request.body, bytes):
            request_body = request.body.decode("utf-8")
        print(request)

        json_body = json.loads(request_body) if request_body else {}

        if len(json_body) != len(releases):
            result = False
            reason = ("Number of releases does not match, got " + str(len(json_body)) +
                      " expected: " + str(len(releases)))
        else:
            for rel in releases:
                if rel not in request_body:
                    result = False
                    reason = ("Release " + rel + " not found in: " + request_body)

        return result, reason
    return match


class TestCreateProject(TestBase):
    INPUTFILE = "sbom_for_create_project.json"
    INPUTFILE_INVALID = "plaintext.txt"
    PROJECT_INFO = "projectinfo.json"

    def test_show_help(self) -> None:
        sut = CreateProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("create")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli project create" in out)

    def test_no_file_specified(self) -> None:
        try:
            sut = CreateProject()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("create")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_no_id_no_name(self) -> None:
        try:
            sut = CreateProject()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("create")
            args.inputfile = "DOES_NOT_EXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_no_id_no_version(self) -> None:
        try:
            sut = CreateProject()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("create")
            args.inputfile = "DOES_NOT_EXIST"
            args.name = "CaPyCLI"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_no_id_no_source(self) -> None:
        try:
            sut = CreateProject()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("create")
            args.inputfile = "DOES_NOT_EXIST"
            args.name = "CaPyCLI"
            args.version = "TEST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_no_id_source_not_found(self) -> None:
        try:
            sut = CreateProject()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("create")
            args.inputfile = "DOES_NOT_EXIST"
            args.name = "CaPyCLI"
            args.version = "TEST"
            args.source = "DOES_NOT_EXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_file_not_found(self) -> None:
        try:
            sut = CreateProject()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("create")
            args.name = "CaPyCLI"
            args.version = "TEST"
            args.source = os.path.join(os.path.dirname(__file__), "fixtures", TestCreateProject.PROJECT_INFO)
            args.inputfile = "DOES_NOT_EXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    @responses.activate
    def test_no_login(self) -> None:
        sut = CreateProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("create")
        args.sw360_url = "https://my.server.com"
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.source = os.path.join(os.path.dirname(__file__), "fixtures", TestCreateProject.PROJECT_INFO)
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestCreateProject.INPUTFILE)

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_AUTH_ERROR, ex.code)

    @responses.activate
    def test_bom_file_invalid(self) -> None:
        try:
            sut = CreateProject()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("create")
            args.sw360_token = TestBase.MYTOKEN
            args.sw360_url = TestBase.MYURL
            args.name = "CaPyCLI"
            args.version = "TEST"
            args.source = os.path.join(os.path.dirname(__file__), "fixtures", TestCreateProject.PROJECT_INFO)
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestCreateProject.INPUTFILE_INVALID)

            self.add_login_response()

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, ex.code)

    @responses.activate
    def test_project_file_invalid(self) -> None:
        try:
            sut = CreateProject()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("project")
            args.command.append("create")
            args.sw360_token = TestBase.MYTOKEN
            args.sw360_url = TestBase.MYURL
            args.name = "CaPyCLI"
            args.version = "TEST"
            args.source = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_INVALID)
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)

            self.add_login_response()

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    @responses.activate
    def test_create_project(self) -> None:
        sut = CreateProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("check")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.name = "CaPyCLI"
        args.version = "TEST"
        args.source = os.path.join(os.path.dirname(__file__), "fixtures", self.PROJECT_INFO)
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)
        args.verbose = True
        args.debug = True

        self.add_login_response()

        # find project
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects?name=CaPyCLI",
            json={
                "_embedded": {
                    "sw360:projects": [{
                        "name": "CaPyCLI",
                        "version": "1.9.0",
                        "securityResponsibles": [],
                        "considerReleasesFromExternalList": False,
                        "projectType": "PRODUCT",
                        "visibility": "EVERYONE",
                        "_links": {
                            "self": {
                                "href": TestBase.MYURL + "resource/api/projects/376576"
                            }
                        }
                    }]
                }
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # create project
        # server returns complete project, here we only mock a part of it
        responses.add(
            responses.POST,
            url=self.MYURL + "resource/api/projects",
            json={
                "name": "CaPyCLI",
                "_links": {
                    "self": {
                        "href": self.MYURL + "resource/api/projects/0206"
                    }
                }
            },
            match=[
                responses.matchers.json_params_matcher({
                    "businessUnit": "SI",
                    "description": "CaPyCLI",
                    "linkedReleases": {
                        "a5cae39f39db4e2587a7d760f59ce3d0": {
                            "mainlineState": "SPECIFIC",
                            "releaseRelation": "DYNAMICALLY_LINKED",
                            "setMainlineState": True,
                            "setReleaseRelation": True
                        }
                    },
                    "name": "CaPyCLI",
                    "ownerGroup": "SI",
                    "projectOwner": "thomas.graf@siemens.com",
                    "projectResponsible": "thomas.graf@siemens.com",
                    "projectType": "INNER_SOURCE",
                    "tag": "SI BP DB Demo",
                    "version": "TEST",
                    "visibility": "EVERYONE"}
                )
            ],
            status=201,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE in out)
        self.assertTrue("Searching for project..." in out)
        self.assertTrue(self.PROJECT_INFO in out)
        self.assertTrue("Creating project ..." in out)
        self.assertTrue("Project created: 0206" in out)

    @responses.activate
    def test_project_for_update_not_found(self) -> None:
        sut = CreateProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("create")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.id = "007"
        args.source = os.path.join(os.path.dirname(__file__), "fixtures", self.PROJECT_INFO)
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)
        args.verbose = True
        args.debug = True

        self.add_login_response()

        # purl cache: components
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/007",
            body="""{}""",
            status=404,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_ACCESSING_SW360, ex.code)

    @responses.activate
    def test_project_update(self) -> None:
        sut = CreateProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("create")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.id = "007"
        args.source = os.path.join(os.path.dirname(__file__), "fixtures", self.PROJECT_INFO)
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)
        args.verbose = True
        args.debug = True

        self.add_login_response()

        # get project
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/007",
            json={
                "name": "CaPyCLI",
                "version": "1.9.0",
                "securityResponsibles": [],
                "considerReleasesFromExternalList": False,
                "projectType": "PRODUCT",
                "visibility": "EVERYONE",
                "_links": {
                    "self": {
                        "href": TestBase.MYURL + "resource/api/projects/007"
                    }
                },
                "linkedReleases": [{
                    "release": "https://sw360.org/api/releases/3765276512",
                    "mainlineState": "SPECIFIC",
                    "relation": "UNKNOWN",
                }],
                "_embedded": {
                    "sw360:releases": [{
                        "name": "Angular 2.3.0",
                        "version": "2.3.0",
                        "_links": {
                            "self": {
                                "href": "https://sw360.org/api/releases/3765276512"
                            }
                        }
                    }]
                }
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # update project releases
        responses.add(
            responses.POST,
            url=self.MYURL + "resource/api/projects/007/releases",
            json={
                # server returns complete project, here we only mock a part of it
                "name": "CaPyCLI",
                "veraion": "1.9.0",
                "businessUnit": "SI",
                "description": "CaPyCLI",
                "linkedReleases": {
                    "a5cae39f39db4e2587a7d760f59ce3d0": {
                        "mainlineState": "SPECIFIC",
                        "releaseRelation": "DYNAMICALLY_LINKED",
                        "setMainlineState": True,
                        "setReleaseRelation": True
                    }
                },
                "_links": {
                    "self": {
                        "href": self.MYURL + "resource/api/projects/007"
                    }
                },
                "_embedded": {
                    "sw360:releases": [{
                        "name": "Angular 2.3.0",
                        "version": "2.3.0",
                        "_links": {
                            "self": {
                                "href": "https://sw360.org/api/releases/3765276512"
                            }
                        }
                    }]
                }
            },
            match=[
                update_release_matcher(["a5cae39f39db4e2587a7d760f59ce3d0"])
            ],
            status=201,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # update project
        responses.add(
            responses.PATCH,
            url=self.MYURL + "resource/api/projects/007",
            json={
                # server returns complete project, here we only mock a part of it
                "name": "CaPyCLI",
                "veraion": "1.9.0",
                "businessUnit": "SI",
                "description": "CaPyCLI",
                "linkedReleases": {
                    "a5cae39f39db4e2587a7d760f59ce3d0": {
                        "mainlineState": "SPECIFIC",
                        "releaseRelation": "DYNAMICALLY_LINKED",
                        "setMainlineState": True,
                        "setReleaseRelation": True
                    }
                },
                "_links": {
                    "self": {
                        "href": self.MYURL + "resource/api/projects/007"
                    }
                },
                "_embedded": {
                    "sw360:releases": [{
                        "name": "Angular 2.3.0",
                        "version": "2.3.0",
                        "_links": {
                            "self": {
                                "href": "https://sw360.org/api/releases/3765276512"
                            }
                        }
                    }]
                }
            },
            match=[
                min_json_matcher(
                    {
                        "businessUnit": "SI",
                        "description": "CaPyCLI",
                        "ownerGroup": "SI",
                        "projectOwner": "thomas.graf@siemens.com",
                        "projectResponsible": "thomas.graf@siemens.com",
                        "projectType": "INNER_SOURCE",
                        "tag": "SI BP DB Demo",
                        "visibility": "EVERYONE"
                    })
            ],
            status=201,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE in out)

    @responses.activate
    def test_project_copy_from(self) -> None:
        """copy project 007 to 017"""
        sut = CreateProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("create")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.version = "2.0.0"
        args.copy_from = "007"
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)
        args.verbose = True
        args.debug = True

        self.add_login_response()

        new_project_json = {
            "name": "CaPyCLI",
            "version": "2.0.0",
            "securityResponsibles": [],
            "considerReleasesFromExternalList": False,
            "projectType": "PRODUCT",
            "visibility": "EVERYONE",
            "_links": {
                "self": {
                    "href": TestBase.MYURL + "resource/api/projects/017"
                }
            },
            "linkedReleases": [{
                "release": "https://sw360.org/api/releases/a5cae39f39db4e2587a7d760f59ce3d0",
                "mainlineState": "SPECIFIC",
                "relation": "UNKNOWN",
            }],
            "_embedded": {
                "sw360:releases": [{
                    "name": "charset-normalizer",
                    "version": "3.1.0",
                    "_links": {
                        "self": {
                            "href": "https://sw360.org/api/releases/a5cae39f39db4e2587a7d760f59ce3d0",
                        }
                    }
                }]
            }
        }

        responses.add(
            responses.POST,
            url=self.MYURL + "resource/api/projects/duplicate/007",
            json=new_project_json,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/017",
            json=new_project_json,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # update project releases
        responses.add(
            responses.POST,
            url=self.MYURL + "resource/api/projects/017/releases",
            json={
                # server returns complete project, here we only mock a part of it
                "name": "CaPyCLI",
                "veraion": "1.9.0",
                "businessUnit": "SI",
                "description": "CaPyCLI",
                "linkedReleases": {
                    "a5cae39f39db4e2587a7d760f59ce3d0": {
                        "mainlineState": "SPECIFIC",
                        "releaseRelation": "DYNAMICALLY_LINKED",
                        "setMainlineState": True,
                        "setReleaseRelation": True
                    }
                },
                "_links": {
                    "self": {
                        "href": self.MYURL + "resource/api/projects/007"
                    }
                },
                "_embedded": {
                    "sw360:releases": [{
                        "name": "Angular 2.3.0",
                        "version": "2.3.0",
                        "_links": {
                            "self": {
                                "href": "https://sw360.org/api/releases/3765276512"
                            }
                        }
                    }]
                }
            },
            match=[
                update_release_matcher(["a5cae39f39db4e2587a7d760f59ce3d0"])
            ],
            status=201,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # update project
        responses.add(
            responses.PATCH,
            url=self.MYURL + "resource/api/projects/017",
            json={
                # server returns complete project, here we only mock a part of it
                "name": "CaPyCLI",
                "veraion": "1.9.0",
                "businessUnit": "SI",
                "description": "CaPyCLI",
                "linkedReleases": {
                    "a5cae39f39db4e2587a7d760f59ce3d0": {
                        "mainlineState": "SPECIFIC",
                        "releaseRelation": "DYNAMICALLY_LINKED",
                        "setMainlineState": True,
                        "setReleaseRelation": True
                    }
                },
                "_links": {
                    "self": {
                        "href": self.MYURL + "resource/api/projects/007"
                    }
                },
                "_embedded": {
                    "sw360:releases": [{
                        "name": "Angular 2.3.0",
                        "version": "2.3.0",
                        "_links": {
                            "self": {
                                "href": "https://sw360.org/api/releases/3765276512"
                            }
                        }
                    }]
                }
            },
            match=[
                min_json_matcher(
                    {
                        "businessUnit": "SI",
                        "description": "CaPyCLI",
                        "ownerGroup": "SI",
                        "projectOwner": "thomas.graf@siemens.com",
                        "projectResponsible": "thomas.graf@siemens.com",
                        "projectType": "INNER_SOURCE",
                        "tag": "SI BP DB Demo",
                        "visibility": "EVERYONE"
                    })
            ],
            status=201,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE in out)

    @responses.activate
    def xtest_project_update_old_version(self) -> None:
        sut = CreateProject()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("create")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.id = "008"
        args.source = os.path.join(os.path.dirname(__file__), "fixtures", self.PROJECT_INFO)
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)
        args.verbose = True
        args.debug = True
        args.old_version = "1.9.0"

        self.add_login_response()

        # get project
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects/008",
            json={
                "name": "CaPyCLI",
                "version": "1.9.9",
                "securityResponsibles": [],
                "considerReleasesFromExternalList": False,
                "projectType": "PRODUCT",
                "visibility": "EVERYONE",
                "_links": {
                    "self": {
                        "href": TestBase.MYURL + "resource/api/projects/008"
                    }
                },
                "_embedded": {
                    "sw360:releases": [{
                        "name": "Angular 2.3.0",
                        "version": "2.3.0",
                        "_links": {
                            "self": {
                                "href": "https://sw360.org/api/releases/3765276512"
                            }
                        }
                    }]
                }
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # update project releases
        responses.add(
            responses.POST,
            url=self.MYURL + "resource/api/projects/008/releases",
            json={
                # server returns complete project, here we only mock a part of it
                "name": "CaPyCLI",
                "veraion": "1.9.9",
                "businessUnit": "SI",
                "description": "CaPyCLI",
                "linkedReleases": {
                    "a5cae39f39db4e2587a7d760f59ce3d0": {
                        "mainlineState": "SPECIFIC",
                        "releaseRelation": "DYNAMICALLY_LINKED",
                        "setMainlineState": True,
                        "setReleaseRelation": True
                    }
                },
                "_links": {
                    "self": {
                        "href": self.MYURL + "resource/api/projects/008"
                    }
                },
                "_embedded": {
                    "sw360:releases": [{
                        "name": "Angular 2.3.0",
                        "version": "2.3.0",
                        "_links": {
                            "self": {
                                "href": "https://sw360.org/api/releases/3765276512"
                            }
                        }
                    }]
                }
            },
            match=[
                update_release_matcher(["a5cae39f39db4e2587a7d760f59ce3d0"])
            ],
            status=201,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # update project
        responses.add(
            responses.PATCH,
            url=self.MYURL + "resource/api/projects/008",
            json={
                # server returns complete project, here we only mock a part of it
                "name": "CaPyCLI",
                "veraion": "1.9.0",
                "businessUnit": "SI",
                "description": "CaPyCLI",
                "linkedReleases": {
                    "a5cae39f39db4e2587a7d760f59ce3d0": {
                        "mainlineState": "SPECIFIC",
                        "releaseRelation": "DYNAMICALLY_LINKED",
                        "setMainlineState": True,
                        "setReleaseRelation": True
                    }
                },
                "_links": {
                    "self": {
                        "href": self.MYURL + "resource/api/projects/007"
                    }
                },
                "_embedded": {
                    "sw360:releases": [{
                        "name": "Angular 2.3.0",
                        "version": "2.3.0",
                        "_links": {
                            "self": {
                                "href": "https://sw360.org/api/releases/3765276512"
                            }
                        }
                    }]
                }
            },
            match=[
                responses.matchers.json_params_matcher(
                    {
                        "businessUnit": "SI",
                        "description": "CaPyCLI",
                        "ownerGroup": "SI",
                        "projectOwner": "thomas.graf@siemens.com",
                        "projectResponsible": "thomas.graf@siemens.com",
                        "projectType": "INNER_SOURCE",
                        "tag": "SI BP DB Demo",
                        "visibility": "EVERYONE"
                    })
            ],
            status=201,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE in out)

    # test invalid entry in project_config ("inner source" instead of INNER_SOURCE)

    # test unknown/invalid release id

    # test upload attachments
