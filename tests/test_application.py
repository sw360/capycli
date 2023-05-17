# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, manuel.schaffer@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------


import capycli.common.json_support
import capycli.common.script_base
from capycli.main.application import Application
from capycli.main.result_codes import ResultCode
from tests.test_base import TestBase


class TestApplication(TestBase):
    """
    Tests for the Application class.
    """
    def test_init(self):
        sut = Application()
        self.assertEqual("CaPyCli", sut.program)
        self.assertIsNotNone(sut.version)

    def test_check_no_arguments(self):
        sut = Application()
        args = []

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("Commands and Sub-Commands" in out)

    def test_check_unknown_argument(self):
        sut = Application()
        args = []
        args.append("xx_unknown_xx")

        try:
            sut.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, sysex.code)

    def test_check_for_version_display(self):
        sut = Application()
        args = []
        args.append("capycli")
        args.append("--version")

        out = self.capture_stdout(sut._run, args)
        self.assertTrue("CaPyCli - Clearing Automation Python Command Line Tool" in out)
        self.assertTrue("version " in out)

    def test_check_for_global_help(self):
        sut = Application()
        args = []
        args.append("-h")

        out = self.capture_stdout(sut._run, args)
        self.assertTrue("Commands and Sub-Commands" in out)

    def test_check_for_debug_switch(self):
        sut = Application()
        args = []
        args.append("-x")
        args.append("-h")

        self.assertFalse(capycli.main.application.DEBUG_LOGGING)
        try:
            sut.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit:
            pass

        self.assertTrue(capycli.main.application.DEBUG_LOGGING)

    def test_getdependencies(self):
        sut = Application()
        args = []
        args.append("getdependencies")
        args.append("-h")

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("getdependencies - dependency detection specific sub-commands" in out)

    def test_bom(self):
        sut = Application()
        args = []
        args.append("bom")
        args.append("-h")

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("bom               bill of material" in out)

    def test_mapping(self):
        sut = Application()
        args = []
        args.append("mapping")
        args.append("-h")

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("mapping - mapping sub-commands" in out)

    def test_moverview(self):
        sut = Application()
        args = []
        args.append("moverview")
        args.append("-h")

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("moverview - mapping overview sub-commands" in out)

    def test_project(self):
        sut = Application()
        args = []
        args.append("project")
        args.append("-h")

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("project - project related sub-commands" in out)


if __name__ == "__main__":
    APP = TestApplication()
    APP.test_check_no_arguments()
