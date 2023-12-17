# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from capycli.bom.handle_bom import run_bom_command
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestHandleBom(TestBase):
    def test_not_bom_command(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("xx_unknown_xx")

        out = self.capture_stdout(run_bom_command, args)
        self.assertEqual("", out)

    def test_no_bom_subcommand(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")

        out = self.capture_stdout(run_bom_command, args)
        self.assertTrue("No subcommand specified!" in out)
        self.assertTrue("bom               bill of material" in out)

    def test_unknown_subcommand(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("xx_unkown_xx")

        try:
            run_bom_command(args)
            self.assertTrue(False, "We must not arrive here!")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_bom_show(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("show")
        args.help = True

        out = self.capture_stdout(run_bom_command, args)
        self.assertTrue("usage: capycli bom show" in out)

    def test_bom_filter(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("filter")
        args.help = True

        out = self.capture_stdout(run_bom_command, args)
        self.assertTrue("Usage: CaPyCli bom filter" in out)

    def test_bom_check(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("check")
        args.help = True

        out = self.capture_stdout(run_bom_command, args)
        self.assertTrue("usage: CaPyCli bom check" in out)

    def test_bom_checkitemstatus(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("checkitemstatus")
        args.help = True

        out = self.capture_stdout(run_bom_command, args)
        self.assertTrue("usage: capycli bom CheckItemStatus" in out)

    def test_bom_map(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("map")
        args.help = True

        out = self.capture_stdout(run_bom_command, args)
        self.assertTrue("usage: CaPyCLI bom map" in out)

    def test_bom_createreleases(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("createreleases")
        args.help = True

        out = self.capture_stdout(run_bom_command, args)
        self.assertTrue("usage: CaPyCLI bom createreleases" in out)

    def test_bom_downloadsources(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("downloadsources")
        args.help = True

        out = self.capture_stdout(run_bom_command, args)
        self.assertTrue("usage: capycli bom downloadsources" in out)

    def test_bom_granularity(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("granularity")
        args.help = True

        out = self.capture_stdout(run_bom_command, args)
        self.assertTrue("usage: CaPyCli bom granularity" in out)

    def test_bom_diff(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("diff")
        args.help = True

        out = self.capture_stdout(run_bom_command, args)
        self.assertTrue("usage: CaPyCli bom diff" in out)

    def test_bom_merge(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("merge")
        args.help = True

        out = self.capture_stdout(run_bom_command, args)
        self.assertTrue("usage: CaPyCli bom merge" in out)

    def test_bom_findsources(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("findsources")
        args.help = True

        out = self.capture_stdout(run_bom_command, args)
        self.assertTrue("usage: CaPyCli bom findsources" in out)

    def test_bom_convert(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("convert")
        args.help = True

        out = self.capture_stdout(run_bom_command, args)
        self.assertTrue("usage: CaPyCli bom convert" in out)
