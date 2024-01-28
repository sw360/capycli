# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from capycli.main.result_codes import ResultCode
from capycli.moverview.handle_moverview import run_moverview_command
from tests.test_base import AppArguments, TestBase


class TestHandleMoverview(TestBase):
    def test_not_moverview_command(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("xx_unknown_xx")

        out = self.capture_stdout(run_moverview_command, args)
        self.assertEqual("", out)

    def test_no_moverview_subcommand(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("moverview")

        out = self.capture_stdout(run_moverview_command, args)
        self.assertTrue("No subcommand specified!" in out)
        self.assertTrue("moverview - mapping overview sub-commands" in out)

    def test_unknown_subcommand(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("moverview")
        args.command.append("xx_unkown_xx")

        try:
            run_moverview_command(args)
            self.assertTrue(False, "We must not arrive here!")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_moverview_tohtml(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("moverview")
        args.command.append("tohtml")
        args.help = True

        out = self.capture_stdout(run_moverview_command, args)
        self.assertTrue("usage: CaPyCli moverview tohtml" in out)

    def test_moverview_toxlsx(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("moverview")
        args.command.append("toxlsx")
        args.help = True

        out = self.capture_stdout(run_moverview_command, args)
        self.assertTrue("usage: CaPyCli moverview toxlsx" in out)
