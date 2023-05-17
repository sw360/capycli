# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from capycli.main.result_codes import ResultCode
from capycli.mapping.handle_mapping import run_mapping_command
from tests.test_base import AppArguments, TestBase


class TestHandleMapping(TestBase):
    def test_not_mapping_command(self):
        args = AppArguments()
        args.command = []
        args.command.append("xx_unknown_xx")

        out = self.capture_stdout(run_mapping_command, args)
        self.assertEqual("", out)

    def test_no_mapping_subcommand(self):
        args = AppArguments()
        args.command = []
        args.command.append("mapping")

        out = self.capture_stdout(run_mapping_command, args)
        self.assertTrue("No subcommand specified!" in out)
        self.assertTrue("mapping - mapping sub-commands" in out)

    def test_unknown_subcommand(self):
        args = AppArguments()
        args.command = []
        args.command.append("mapping")
        args.command.append("xx_unkown_xx")

        try:
            run_mapping_command(args)
            self.assertTrue(False, "We must not arrive here!")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_mapping_tohtml(self):
        args = AppArguments()
        args.command = []
        args.command.append("mapping")
        args.command.append("tohtml")
        args.help = True

        out = self.capture_stdout(run_mapping_command, args)
        self.assertTrue("usage: CaPyCli mapping tohtml" in out)

    def test_mapping_toxlsx(self):
        args = AppArguments()
        args.command = []
        args.command.append("mapping")
        args.command.append("toxlsx")
        args.help = True

        out = self.capture_stdout(run_mapping_command, args)
        self.assertTrue("usage: CaPyCli mapping toxlsx" in out)
