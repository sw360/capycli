# -------------------------------------------------------------------------------
# Copyright (c) 2022-23 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import tempfile
from io import StringIO
from typing import Any
from unittest.mock import patch

import pytest
from cli_test_helpers import ArgvContext  # type: ignore

from capycli.bom.create_components import BomCreateComponents
from capycli.main import cli
from tests.test_base import AppArguments, TestBase


class TestBomCreateReleasesIntegration(TestBase):
    def setUp(self) -> None:
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def test_bom_create_releases_help(self) -> None:
        sut = BomCreateComponents()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("createreleases")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCLI bom createcomponents" in out)

    def test_bom_create_components_help(self) -> None:
        sut = BomCreateComponents()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("createcomponents")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCLI bom createcomponents" in out)

    @patch('sys.stdout', new_callable=StringIO)
    def test_bom_create_components_shall_cause_error_on_missing_input(self, stdout: Any) -> None:
        """
        Does 'capycli bom createcomponents' fail with error message if the user missed specifying the input file
        """
        with pytest.raises(SystemExit):
            with ArgvContext("capycli", "bom", "createcomponents"):
                # app = Application()
                # app.run()
                cli.main()
        assert "No input file specified!" in stdout.getvalue()

    @patch('sys.stdout', new_callable=StringIO)
    def test_bom_create_components_shall_cause_error_on_missing_input_file(self, stdout: Any) -> None:
        """
        Does 'capycli bom createcomponents' fail with error message if the input file doesn't exist
        """
        with pytest.raises(SystemExit):
            with ArgvContext("capycli", "bom", "createcomponents", "-i", self.test_dir + "/not_existing.json"):
                # app = Application()
                # app.run()
                cli.main()
        assert "Input file not found!" in stdout.getvalue()
