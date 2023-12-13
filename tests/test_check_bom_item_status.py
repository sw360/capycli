# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

import responses

from capycli.bom.check_bom_item_status import CheckBomItemStatus
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestCheckBomItemStatus(TestBase):
    INPUTFILE = "sbom_with_sw360.json"
    INPUTFILE2 = "sbom_with_sw360_two_ids_missing.json"

    def test_show_help(self) -> None:
        sut = CheckBomItemStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("checkitemstatus")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: capycli bom CheckItemStatus" in out)

    def test_no_file_specified(self) -> None:
        try:
            sut = CheckBomItemStatus()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("checkitemstatus")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_file_not_found(self) -> None:
        try:
            sut = CheckBomItemStatus()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("checkitemstatus")
            args.inputfile = "DOESNOTEXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    @responses.activate
    def test_no_login(self) -> None:
        sut = CheckBomItemStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("checkitemstatus")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestCheckBomItemStatus.INPUTFILE)

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_AUTH_ERROR, ex.code)

    @responses.activate
    def test_simple_bom(self) -> None:
        sut = CheckBomItemStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("checkitemstatus")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestCheckBomItemStatus.INPUTFILE)

        # for login
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'ok'}",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for colorama
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/9a2373710bd44769a2560dd31280901d",
            body='{"name": "colorama", "version": "0.4.6"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for python
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/05c30bf89a512463260b57e84d99b38f",
            body='{"name": "python", "version": "3.8"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for tomli
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/fa0d21eb17574ba9ae17e5c9b432558e",
            body='{"name": "tomli", "version": "2.0.1"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for wheel
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/e0995819173d4ac8b1a4da3548935976",
            body='{"name": "wheel", "version": "0.38.4"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("colorama, 0.4.6" in out)
        self.assertTrue("python, 3.8" in out)
        self.assertTrue("tomli, 2.0.1" in out)
        self.assertTrue("wheel, 0.38.4" in out)

    @responses.activate
    def test_simple_bom_without_id(self) -> None:
        sut = CheckBomItemStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("checkitemstatus")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestCheckBomItemStatus.INPUTFILE2)

        # for login
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'ok'}",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for colorama
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/9a2373710bd44769a2560dd31280901d",
            body='{"name": "colorama", "version": "0.4.6"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for python
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/05c30bf89a512463260b57e84d99b38f",
            body='{"name": "python", "version": "3.8"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for tomli (1)
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases?name=tomli",
            body='''{"_embedded" : {
              "sw360:releases" : [ {
                "name": "tomli",
                "version": "2.0.1",
                "_links" : {
                "self" : {
                "href" : "https://my.server.com/resource/api/releases/fa0d21eb17574ba9ae17e5c9b432558e"
                }
                }
                } ]
                }}''',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for tomli (2)
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/fa0d21eb17574ba9ae17e5c9b432558e",
            body='{"name": "tomli", "version": "2.0.1"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for wheel (1)
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases?name=wheel",
            body='''{"_embedded" : {
                "sw360:releases" : [ {
                "name": "wheel",
                "version": "0.38.4",
                "_links" : {
                "self" : {
                "href" : "https://my.server.com/resource/api/releases/e0995819173d4ac8b1a4da3548935976"
                }
                }
                } ]
                }}''',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for wheel (2)
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/e0995819173d4ac8b1a4da3548935976",
            body='{"name": "wheel", "version": "0.38.4"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("colorama, 0.4.6" in out)
        self.assertTrue("python, 3.8" in out)
        self.assertTrue("tomli, 2.0.1" in out)
        self.assertTrue("wheel, 0.38.4" in out)

    @responses.activate
    def test_simple_bom_with_errors(self) -> None:
        sut = CheckBomItemStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("checkitemstatus")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.verbose = True
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestCheckBomItemStatus.INPUTFILE)

        # for login
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'ok'}",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for colorama
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/9a2373710bd44769a2560dd31280901d",
            body='{"name": "colorama", "version": "0.4.6"}',
            status=404,  # not found
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for python
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/05c30bf89a512463260b57e84d99b38f",
            body='{"name": "python", "version": "3.8"}',
            status=500,  # internal server error
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for tomli
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/fa0d21eb17574ba9ae17e5c9b432558e",
            body='{"name": "tomli", "version": "2.0.1"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for wheel
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/e0995819173d4ac8b1a4da3548935976",
            body='{"name": "wheel", "version": "0.38.4"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("colorama, 0.4.6" in out)
        self.assertTrue("python, 3.8" in out)
        self.assertTrue("tomli, 2.0.1" in out)
        self.assertTrue("wheel, 0.38.4" in out)

    @responses.activate
    def test_simple_bom_without_id_with_errors(self) -> None:
        sut = CheckBomItemStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("checkitemstatus")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestCheckBomItemStatus.INPUTFILE2)

        # for login
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'ok'}",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for colorama
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/9a2373710bd44769a2560dd31280901d",
            body='{"name": "colorama", "version": "0.4.6"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for python
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/05c30bf89a512463260b57e84d99b38f",
            body='{"name": "python", "version": "3.8"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for tomli (1)
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases?name=tomli",
            body='''{"_embedded" : {
                "sw360:releases" : [ {
                "name": "tomli",
                "version": "2.0.1",
                "_links" : {
                "self" : {
                "href" : "https://my.server.com/resource/api/releases/fa0d21eb17574ba9ae17e5c9b432558e"
                }
                }
                } ]
                }}''',
            status=404,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for tomli (2)
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/fa0d21eb17574ba9ae17e5c9b432558e",
            body='{"name": "tomli", "version": "2.0.1"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for wheel (1)
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases?name=wheel",
            body='''
            {"_embedded" : {
                "sw360:releases" : [ {
                  "name": "wheel",
                  "version": "0.38.4",
                  "_links" : {
                    "self" : {
                      "href" : "https://my.server.com/resource/api/releases/e0995819173d4ac8b1a4da3548935976"
                     }
                   }
                } ]
                }}''',
            status=500,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for wheel (2)
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/e0995819173d4ac8b1a4da3548935976",
            body='{"name": "wheel", "version": "0.38.4"}',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("colorama, 0.4.6" in out)
        self.assertTrue("python, 3.8" in out)
        self.assertTrue("tomli, 2.0.1" in out)
        self.assertTrue("wheel, 0.38.4" in out)

    @responses.activate
    def test_simple_bom_show_all(self) -> None:
        sut = CheckBomItemStatus()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("checkitemstatus")
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", TestCheckBomItemStatus.INPUTFILE)
        args.all = True

        # for login
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/",
            body="{'status': 'ok'}",
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for colorama release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/9a2373710bd44769a2560dd31280901d",
            body='''
            {
                "name": "colorama",
                "version": "0.4.6",
                "_links": {
                    "sw360:component": {
                        "href": "https://my.server.com/resource/api/components/1234"
                    }
                }
            }
            ''',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for colorama component
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/components/1234",
            body='''
            {
                "name": "colorama",
                "_embedded" : {
                    "sw360:releases" : [ {
                        "name": "colorama",
                        "version": "0.4.6",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/releases/9a2373710bd44769a2560dd31280901d"
                            }
                        }
                    }]
                }
            }
            ''',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for python release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/05c30bf89a512463260b57e84d99b38f",
            body='''
              {
                "name": "python",
                "version": "3.8",
                "_links": {
                    "sw360:component": {
                        "href": "https://my.server.com/resource/api/components/1235"
                    }
                }
              }
            ''',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for python component
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/components/1235",
            body='''
            {
                "name": "python",
                "_embedded" : {
                    "sw360:releases" : [ {
                        "name": "python",
                        "version": "3.8",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/releases/9a2373710bd44769a2560dd31280901d"
                            }
                        }
                    }]
                }
            }
            ''',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for tomli release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/fa0d21eb17574ba9ae17e5c9b432558e",
            body='''
              {
                "name": "tomli",
                "version": "2.0.1",
                "_links": {
                    "sw360:component": {
                        "href": "https://my.server.com/resource/api/components/1236"
                    }
                }
              }
            ''',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for tomli component
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/components/1236",
            body='''
            {
                "name": "tomli",
                "_embedded" : {
                    "sw360:releases" : [ {
                        "name": "tomli",
                        "version": "2.0.1",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/releases/9a2373710bd44769a2560dd31280901d"
                            }
                        }
                    }]
                }
            }
            ''',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for wheel release
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/releases/e0995819173d4ac8b1a4da3548935976",
            body='''
              {
                "name": "wheel",
                "version": "0.38.4",
                "_links": {
                    "sw360:component": {
                        "href": "https://my.server.com/resource/api/components/1237"
                    }
                }
              }
            ''',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        # for wheel component
        responses.add(
            responses.GET,
            url=self.MYURL + "resource/api/components/1237",
            body='''
            {
                "name": "wheel",
                "_embedded" : {
                    "sw360:releases" : [
                      {
                        "name": "wheel",
                        "version": "0.38.4",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/releases/9a2373710bd44769a2560dd31280901d"
                            }
                        }
                      },
                      {
                        "name": "wheel",
                        "version": "0.39.9",
                        "_links": {
                            "self": {
                                "href": "https://my.server.com/resource/api/releases/9a2373710bd44769a2560dd31280901d"
                            }
                        }
                    }]
                }
            }
            ''',
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("colorama, 0.4.6" in out)
        self.assertTrue("python, 3.8" in out)
        self.assertTrue("tomli, 2.0.1" in out)
        self.assertTrue("wheel, 0.38.4" in out)
        self.assertTrue("0.39.9" in out)


if __name__ == "__main__":
    lib = TestCheckBomItemStatus()
    lib.test_simple_bom_with_errors()
