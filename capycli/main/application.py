# -------------------------------------------------------------------------------
# Copyright (c) 2019-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

"""Module containing the application logic for CaPyCli."""

import sys
import time
from typing import Any, Optional, List

import capycli
from capycli.bom import handle_bom
from capycli.common.print import print_red
from capycli.dependencies import handle_dependencies
from capycli.main import options
from capycli.main.result_codes import ResultCode
from capycli.mapping import handle_mapping
from capycli.moverview import handle_moverview
from capycli.project import handle_project

LOG = capycli.get_logger(__name__)

DEBUG_LOGGING = False


class Application(object):
    def __init__(self, program="CaPyCli", version=capycli.get_app_version()) -> None:
        """Initialize our application."""

        #: The timestamp when the Application instance was instantiated.
        self.start_time = time.time()
        #: The timestamp when the Application finished reported errors.
        self.end_time = 0  # type: float
        #: The name of the program being run
        self.program = program
        #: The version of the program being run
        self.version = version

        #: The user-supplied options parsed into an instance of
        #: :class:`argparse.Namespace`
        self.options = None
        #: The left over arguments that were not parsed by
        #: :attr:`option_manager`
        self.args = None

    def check_for_version_display(self, argv: Any) -> bool:
        """Check for --version option"""
        for arg in argv:
            if arg == "--version":
                print(
                    "\n" + capycli.APP_NAME +
                    " - Clearing Automation Python Command Line Tool\n")
                print("version", capycli.get_app_version())
                return True

        return False

    def check_for_global_help(self, argv: Any) -> bool:
        """Check for -h option without any command"""
        global_help = False
        if len(argv) > 1:
            # it must be a single help parameter
            return False

        for arg in argv:
            if (arg == "-h") or (arg == "--help"):
                global_help = True

        return global_help

    def exit(self) -> None:
        """Handle finalization and exiting the program."""
        pass

    def has_debug_switch(self, argv: Any) -> bool:
        for arg in argv:
            if arg.lower() == "-x":
                return True

        return False

    def initialize(self, argv: Any) -> None:
        if self.has_debug_switch(argv):
            capycli.configure_logging(2)
            global DEBUG_LOGGING
            DEBUG_LOGGING = True
        else:
            capycli.configure_logging(1)

    def emit_exit_code(self, system_exit_exception: Optional[SystemExit]) -> None:
        if system_exit_exception is None:
            # successfull
            if self.options and self.options.ex:
                print("Exit code = 0")
            # no need to do sys.exit(0) here - 0 is terh default exit code
            # sys.exit(ResultCode.RESULT_OPERATION_SUCCEEDED)
        else:
            if isinstance(system_exit_exception.code, str):
                print(system_exit_exception.code)

            if isinstance(system_exit_exception.code, int):
                sys.exit(system_exit_exception.code)

            if self.options and self.options.ex:
                print("Exit code = 1")
            sys.exit(ResultCode.RESULT_GENERAL_ERROR)

    def _run(self, argv: List[str]) -> None:
        self.initialize(argv)

        cmdline = options.CommandlineSupport()

        # check for some general overrides
        # --version
        if self.check_for_version_display(argv):
            return

        # --help / -h
        if self.check_for_global_help(argv):
            cmdline.parser.print_help()
            return

        if len(argv) < 1:
            LOG.error("No command specified!")
            cmdline.parser.print_help()
            return

        self.options = cmdline.process_commandline(argv)

        command: str
        if self.options:
            command = self.options.command[0].lower()
        if command == "getdependencies":
            handle_dependencies.run_dependency_command(self.options)
        elif command == "bom":
            handle_bom.run_bom_command(self.options)
        elif command == "mapping":
            handle_mapping.run_mapping_command(self.options)
        elif command == "moverview":
            handle_moverview.run_moverview_command(self.options)
        elif command == "project":
            handle_project.run_project_command(self.options)
        else:
            print_red("Unknown command: " + command)
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

    def run(self, argv: List[str]) -> None:
        """Run our application.
        This method will also handle KeyboardInterrupt exceptions for the
        entirety of the CaPyCli application.
        """

        system_exit_exception = None
        try:
            self._run(argv)
        except KeyboardInterrupt:
            print("... stopped")
            LOG.critical("Caught keyboard interrupt from user")
            self.catastrophic_failure = True
        except SystemExit as sysex:
            system_exit_exception = sysex

        self.emit_exit_code(system_exit_exception)
