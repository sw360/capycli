# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from capycli.dependencies.handle_dependencies import run_dependency_command
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestHandleDependencies(TestBase):
    def test_not_getdependencies_command(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("xx_unknown_xx")

        out = self.capture_stdout(run_dependency_command, args)
        self.assertEqual("", out)

    def test_no_getdependencies_subcommand(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")

        out = self.capture_stdout(run_dependency_command, args)
        self.assertTrue("No subcommand specified!" in out)
        self.assertTrue("getdependencies - dependency detection specific sub-commands" in out)

    def test_unknown_subcommand(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("xx_unkown_xx")

        try:
            run_dependency_command(args)
            self.assertTrue(False, "We must not arrive here!")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_getdependencies_nuget(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("nuget")
        args.help = True

        out = self.capture_stdout(run_dependency_command, args)
        self.assertTrue("Usage: capycli getdependencies nuget" in out)

    def test_getdependencies_python(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("python")
        args.help = True

        out = self.capture_stdout(run_dependency_command, args)
        self.assertTrue("usage: capycli getdependencies python" in out)

    def test_getdependencies_javascript(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("javascript")
        args.help = True

        out = self.capture_stdout(run_dependency_command, args)
        self.assertTrue("CaPyCli getdependencies javascript" in out)

    def test_getdependencies_mavenpom(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("mavenpom")
        args.help = True

        out = self.capture_stdout(run_dependency_command, args)
        self.assertTrue("CaPyCli getdependencies mavenpom" in out)

    def test_getdependencies_mavenlist(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("mavenlist")
        args.help = True

        out = self.capture_stdout(run_dependency_command, args)
        self.assertTrue("CaPyCli getdependencies mavenlist" in out)
