# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

import responses
from sw360.sw360error import SW360Error

from capycli.common.script_base import ScriptBase
from capycli.main.result_codes import ResultCode
from tests.test_base import TestBase


class ResponseMock():
    def __init__(self, text=None, ok=False, status_code=200, url=None):
        self.text = text
        self.ok = ok
        self.url = url
        self.status_code = status_code
        self.content = None


class TestScriptBase(TestBase):
    @responses.activate
    def test_login_fails_no_answer(self):
        sut = ScriptBase()

        try:
            sut.login(token=TestBase.MYTOKEN, url=TestBase.MYURL)
            self.assertTrue(False, "Failed to report login error")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_AUTH_ERROR, ex.code)

    @responses.activate
    def test_login_fails_unauthorized(self):
        sut = ScriptBase()

        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'unauthorized'}",
            status=401,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            sut.login(token=TestBase.MYTOKEN, url=TestBase.MYURL)
            self.assertTrue(False, "Failed to report login error")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_AUTH_ERROR, ex.code)

    @responses.activate
    def test_login_fails_error(self):
        sut = ScriptBase()

        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'error'}",
            status=500,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            sut.login(token=TestBase.MYTOKEN, url=TestBase.MYURL)
            self.assertTrue(False, "Failed to report login error")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_AUTH_ERROR, ex.code)

    @responses.activate
    def test_login_fails_no_url(self):
        if os.environ.get("SW360ServerUrl", None):
            # SW360ServerUrl has a value that would mess up the test
            return

        sut = ScriptBase()

        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'error'}",
            status=500,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            sut.login(token=TestBase.MYTOKEN)
            self.assertTrue(False, "Failed to report login error")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_ACCESSING_SW360, ex.code)

    @responses.activate
    def test_login_success(self):
        sut = ScriptBase()

        self.add_login_response()

        value = sut.login(token=TestBase.MYTOKEN, url=TestBase.MYURL)
        self.assertTrue(value)

    def test_analyze_token_ok(self):
        sut = ScriptBase()
        encoded = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsic3czNjAtUkVTVC"
                   + "1BUEkiXSwidXNlcl9uYW1lIjoidGhvbWFzLmdyYWZAc2llbWVucy5jb20iLCJ"
                   + "zY29wZSI6WyJSRUFEIiwiV1JJVEUiXSwiZXhwIjoxNTgxNzU0MjY4LCJhdXRo"
                   + "b3JpdGllcyI6WyJSRUFEIiwiV1JJVEUiXSwianRpIjoiYmRkYzg5NTEtYmZhZ"
                   + "S00NzVkLWIyZmQtMDQwNTliODY1OThlIiwiY2xpZW50X2lkIjoieHh4In0.D2"
                   + "cGwTWorpXOESMBZeWCip_7HQKyi-91Zwtmy_x_Z_0")
        out = self.capture_stdout(sut.analyze_token, encoded)
        self.assertTrue("Analyzing token..." in out)
        self.assertTrue("Token will expire on" in out)

    def test_analyze_token_fail(self):
        sut = ScriptBase()
        encoded = "eyXXJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        out = self.capture_stdout(sut.analyze_token, encoded)
        self.assertTrue("Analyzing token..." in out)
        self.assertTrue("Unable to analyze token" in out)

    @responses.activate
    def test_find_project_success(self):
        sut = ScriptBase()

        self.add_login_response()

        login = sut.login(token=TestBase.MYTOKEN, url=TestBase.MYURL)
        self.assertTrue(login)

        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects?name=MyName",
            json={
                "_embedded": {
                    "sw360:projects": [{
                        "name": "MyName",
                        "version": "MyVersion",
                        "securityResponsibles": [],
                        "considerReleasesFromExternalList": False,
                        "projectType": "PRODUCT",
                        "visibility": "EVERYONE",
                        "_links": {
                            "self": {
                                "href": TestBase.MYURL + "resource/api/projects/007"
                            }
                        }
                    }]
                }
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        val = sut.find_project("MyName", "MyVersion", True)
        self.assertEqual("007", val)

    @responses.activate
    def test_find_project_fail_sw360_error(self):
        sut = ScriptBase()
        self.add_login_response()

        login = sut.login(token=TestBase.MYTOKEN, url=TestBase.MYURL)
        self.assertTrue(login)

        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects?name=MyName",
            json={
                "_embedded": {
                    "sw360:projects": []
                }
            },
            status=500,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        try:
            sut.find_project("MyName", "MyVersion")
            self.assertTrue(False, "Failed to report find error")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_ACCESSING_SW360, ex.code)

    @responses.activate
    def test_find_project_fail_no_project(self):
        sut = ScriptBase()
        self.add_login_response()

        login = sut.login(token=TestBase.MYTOKEN, url=TestBase.MYURL)
        self.assertTrue(login)

        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects?name=MyName",
            json={
                "_embedded": {
                    "sw360:projects": []
                }
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        val = sut.find_project("MyName", "MyVersion")
        self.assertEqual("", val)

    @responses.activate
    def test_find_project_fail_version_not_found(self):
        sut = ScriptBase()
        self.add_login_response()

        login = sut.login(token=TestBase.MYTOKEN, url=TestBase.MYURL)
        self.assertTrue(login)

        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/projects?name=MyName",
            json={
                "_embedded": {
                    "sw360:projects": [{
                        "name": "MyName",
                        "version": "OtherVersion",
                        "securityResponsibles": [],
                        "considerReleasesFromExternalList": False,
                        "projectType": "PRODUCT",
                        "visibility": "EVERYONE",
                        "_links": {
                            "self": {
                                "href": TestBase.MYURL + "resource/api/projects/007"
                            }
                        }
                    }]
                }
            },
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        val = sut.find_project("MyName", "MyVersion", True)
        self.assertEqual("", val)

    def test_get_error_message_no_info(self):
        sut = ScriptBase()

        swex = SW360Error()
        val = sut.get_error_message(swex)
        self.assertIsNotNone(val)
        self.assertEqual("SW360Error('None')", val)

    def test_get_error_message_login(self):
        sut = ScriptBase()

        swex = SW360Error(None, TestBase.MYURL, message="Unable to login:")
        val = sut.get_error_message(swex)
        self.assertIsNotNone(val)
        self.assertEqual("SW360Error('Unable to login:')", val)

    def test_get_error_message(self):
        sut = ScriptBase()

        text = """{"text": "some message", "status_code" : "500"}"""
        text2 = """{
            "error": "some other error",
            "status": 500,
            "message": "another message"
            }"""
        resp = ResponseMock(text, False, 500, TestBase.MYURL)
        resp.content = text2.encode("utf-8")

        swex = SW360Error(resp, TestBase.MYURL, message="some error")
        val = sut.get_error_message(swex)
        self.assertIsNotNone(val)
        self.assertEqual("Error=some other error(500): another message", val)


if __name__ == '__main__':
    APP = TestScriptBase()
    APP.test_get_error_message()
