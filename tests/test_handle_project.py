# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from capycli.main.result_codes import ResultCode
from capycli.project.handle_project import run_project_command
from tests.test_base import AppArguments, TestBase


class TestHandleProject(TestBase):
    def test_not_project_command(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("xx_unknown_xx")

        out = self.capture_stdout(run_project_command, args)
        self.assertEqual("", out)

    def test_no_project_subcommand(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("project")

        out = self.capture_stdout(run_project_command, args)
        self.assertTrue("No subcommand specified!" in out)
        self.assertTrue("project - project related sub-commands" in out)

    def test_unknown_subcommand(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("xx_unkown_xx")

        try:
            run_project_command(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_project_find(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("find")
        args.help = True

        out = self.capture_stdout(run_project_command, args)
        self.assertTrue("usage: CaPyCli project find" in out)

    def test_project_show(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("show")
        args.help = True

        out = self.capture_stdout(run_project_command, args)
        self.assertTrue("usage: CaPyCli project show " in out)

    def test_project_prerequisites(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("prerequisites")
        args.help = True

        out = self.capture_stdout(run_project_command, args)
        self.assertTrue("Usage: CaPyCli project prerequisites" in out)

    def test_project_licenses(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("licenses")
        args.help = True

        out = self.capture_stdout(run_project_command, args)
        self.assertTrue("usage: CaPyCli project licenses" in out)

    def test_project_getlicenseinfo(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("getlicenseinfo")
        args.help = True

        out = self.capture_stdout(run_project_command, args)
        self.assertTrue("Usage: CaPyCli project GetLicenseInfo" in out)

    def test_project_createreadme(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createreadme")
        args.help = True

        out = self.capture_stdout(run_project_command, args)
        self.assertTrue("usage: CaPyCli project createreadme" in out)

    def test_project_create(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("create")
        args.help = True

        out = self.capture_stdout(run_project_command, args)
        self.assertTrue("usage: CaPyCli project create" in out)

    def test_project_update(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("update")
        args.help = True

        out = self.capture_stdout(run_project_command, args)
        self.assertTrue("usage: CaPyCli project create" in out)

    def test_project_createbom(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("createbom")
        args.help = True

        out = self.capture_stdout(run_project_command, args)
        self.assertTrue("usage: CaPyCli project createbom" in out)

    def test_project_vulnerabilities(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("vulnerabilities")
        args.help = True

        out = self.capture_stdout(run_project_command, args)
        self.assertTrue("usage: CaPyCli project vulnerabilities" in out)

    def test_project_ecc(self) -> None:
        args = AppArguments()
        args.command = []
        args.command.append("project")
        args.command.append("ecc")
        args.help = True

        out = self.capture_stdout(run_project_command, args)
        self.assertTrue("usage: CaPyCli project ecc" in out)
