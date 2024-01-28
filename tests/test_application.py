# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, manuel.schaffer@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from typing import List

import capycli.common.json_support
import capycli.common.script_base
from capycli.main.application import Application
from capycli.main.result_codes import ResultCode
from tests.test_base import TestBase


class TestApplication(TestBase):
    """
    Tests for the Application class.
    """
    def test_init(self) -> None:
        sut = Application()
        self.assertEqual("CaPyCli", sut.program)
        self.assertIsNotNone(sut.version)

    def test_check_no_arguments(self) -> None:
        sut = Application()
        args: List[str] = []

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("Commands and Sub-Commands" in out)

    def test_check_unknown_argument(self) -> None:
        sut = Application()
        args: List[str] = []
        args.append("xx_unknown_xx")

        try:
            sut.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit as sysex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, sysex.code)

    def test_check_for_version_display(self) -> None:
        sut = Application()
        args: List[str] = []
        args.append("capycli")
        args.append("--version")

        out = self.capture_stdout(sut._run, args)
        self.assertTrue("CaPyCli - Clearing Automation Python Command Line Tool" in out)
        self.assertTrue("version " in out)

    def test_check_for_global_help(self) -> None:
        sut = Application()
        args: List[str] = []
        args.append("-h")

        out = self.capture_stdout(sut._run, args)
        self.assertTrue("Commands and Sub-Commands" in out)

    def test_check_for_debug_switch(self) -> None:
        sut = Application()
        args: List[str] = []
        args.append("-x")
        args.append("-h")

        self.assertFalse(capycli.main.application.DEBUG_LOGGING)
        try:
            sut.run(args)
            self.assertTrue(False, "We must not arrive here")
        except SystemExit:
            pass

        self.assertTrue(capycli.main.application.DEBUG_LOGGING)

    def test_getdependencies(self) -> None:
        sut = Application()
        args: List[str] = []
        args.append("getdependencies")
        args.append("-h")

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("getdependencies - dependency detection specific sub-commands" in out)

    def test_bom(self) -> None:
        sut = Application()
        args: List[str] = []
        args.append("bom")
        args.append("-h")

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("bom               bill of material" in out)

    def test_mapping(self) -> None:
        sut = Application()
        args: List[str] = []
        args.append("mapping")
        args.append("-h")

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("mapping - mapping sub-commands" in out)

    def test_moverview(self) -> None:
        sut = Application()
        args: List[str] = []
        args.append("moverview")
        args.append("-h")

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("moverview - mapping overview sub-commands" in out)

    def test_project(self) -> None:
        sut = Application()
        args: List[str] = []
        args.append("project")
        args.append("-h")

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("project - project related sub-commands" in out)


if __name__ == "__main__":
    APP = TestApplication()
    APP.test_check_no_arguments()
