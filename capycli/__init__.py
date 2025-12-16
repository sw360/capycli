# -------------------------------------------------------------------------------
# Copyright (c) 2019-2025 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: (c) 2019-2023 Siemens
# -------------------------------------------------------------------------------

"""Top-level module for CaPyCli.

This module
- initializes logging for the command-line tool
- tracks the version of the package
- provides a way to configure logging for the command-line tool
"""

import importlib
import logging
import os
import sys
from typing import Any
import tomllib

from colorama import Fore, Style, init

APP_NAME = "CaPyCli"
VERBOSITY_LEVEL = 1


def is_debug_logging_enabled() -> bool:
    return VERBOSITY_LEVEL > 1


def _get_project_meta() -> Any:
    """Read version information from poetry configuration file."""
    try:
        with open('pyproject.toml', mode='rb') as pyproject:
            return tomllib.load(pyproject)['tool']['poetry']
    except Exception:
        # ignore all errors
        pass


def get_app_version() -> str:
    """Get the version string of this application"""
    version = ""
    try:
        # this will only work when the package has been installed
        version = importlib.metadata.version("capycli")
    except:  # noqa
        pass

    if not version:
        # use version information from poetry
        pkg_meta = _get_project_meta()
        if pkg_meta and 'version' in pkg_meta:
            version = str(pkg_meta['version'])

    if not version:
        version = "0.0.0-no-version"

    return version


def get_app_signature() -> str:
    """Get the signature of this application."""
    version = get_app_version()
    return f"{APP_NAME}, {version}"


# There is nothing lower than logging.DEBUG (10) in the logging library,
# but we want an extra level to avoid being too verbose when using -vv.
_EXTRA_VERBOSE = 5
logging.addLevelName(_EXTRA_VERBOSE, "VERBOSE")

_VERBOSITY_TO_LOG_LEVEL = {
    # output more than warnings but not debugging info
    1: logging.INFO,  # INFO is a numerical level of 20
    # output debugging information
    2: logging.DEBUG,  # DEBUG is a numerical level of 10
    # output extra verbose debugging information
    3: _EXTRA_VERBOSE,
}


def is_running_in_ci() -> bool:
    """Check if the application is running in a CI environment."""
    return "GITLAB_CI" in os.environ


def ensure_color_console_output() -> None:
    """Ensure that the console output is colored."""
    if is_running_in_ci():
        if "NO_COLOR" not in os.environ:
            # required for colorama's TTY detection to work properly in Gitlab setting,
            # for details see https://github.com/tartley/colorama/issues/214
            os.environ["PYCHARM_HOSTED"] = "1"


# initialize colorama
ensure_color_console_output()
init()


class ConsoleHandler(logging.Handler):
    """Handler that write to stderr for errors and to stdout
    for other logiing records."""
    def __init__(self) -> None:
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record."""
        try:
            msg = self.format(record)
            if record.levelno >= 40:
                # error, critical
                sys.stderr.write(msg)
            elif record.levelno >= 30:
                # warning
                sys.stderr.write(msg)
                print(msg)
            else:
                # info, debug, all other
                # suppress all cyclonedx serialize log output
                if record.name == "serializable":
                    return
                print(msg)
        except Exception:
            self.handleError(record)


class ColorFormatter(logging.Formatter):
    """
    A logging formatter for color console output.
    Critical messages and errors are displayed in red.
    Warnings are displayed in yellow.
    Infos are displayed in white.
    Debug messages are displayed in blue.
    """
    def __init__(self, verbosity: int) -> None:
        super().__init__()
        self.verbosity = verbosity
        self.fmt = "%(asctime)s:%(levelname)s:%(name)s: %(message)s"
        if self.verbosity == 1:
            self.fmt = "%(message)s"

    def get_color_format(self, levelno: int, fmt: str) -> Any:
        if levelno >= 50:
            color = Fore.LIGHTRED_EX
        elif levelno >= 40:
            color = Fore.LIGHTRED_EX
        elif levelno >= 30:
            color = Fore.LIGHTYELLOW_EX
        elif levelno >= 20:
            color = Fore.LIGHTWHITE_EX
        elif levelno >= 10:
            color = Fore.LIGHTBLUE_EX
        else:
            color = Fore.WHITE

        return color + fmt + Style.RESET_ALL

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.get_color_format(record.levelno, self.fmt)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class ColoredLogger(logging.Logger):
    """
    A color console logger that uses ColorFormatter
    to display colored log messages and uses ConsoleHandler
    to output critical messages, errors and warnings to stderr.
    Infos and debug messages will be sent to stdout.
    """
    def __init__(self, name: str):
        logging.Logger.__init__(self, name, logging.DEBUG)

        self.propagate = False
        self.setVerbosity(1)

    def getVerbosity(self) -> int:
        return self.__verbosity

    def setVerbosity(self, value: int) -> None:
        self.__verbosity = value
        console = ConsoleHandler()
        color_formatter = ColorFormatter(self.__verbosity)
        console.setFormatter(color_formatter)
        self.handlers.clear()
        self.addHandler(console)

    def handle(self, record: logging.LogRecord) -> None:
        if self.isEnabledFor(record.levelno):
            return super().handle(record)


def configure_logging(verbosity: int) -> logging.Logger:
    """
    Configure logging.

    :param int verbosity:
        How verbose to be in logging information.
    """
    logging.setLoggerClass(ColoredLogger)

    global VERBOSITY_LEVEL
    VERBOSITY_LEVEL = verbosity

    if verbosity < 0:
        verbosity = 0
    if verbosity > 3:
        verbosity = 3

    log_level = _VERBOSITY_TO_LOG_LEVEL[verbosity]

    # log_level = logging.DEBUG # too much output from other libraries
    logging.basicConfig(level=log_level)

    logger = logging.getLogger(__name__)
    logger.setVerbosity(verbosity)  # type: ignore
    logger.setLevel(log_level)

    global LOG
    LOG = logger

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get one of our colored loggers for the specified name."""
    logger = logging.getLogger(name)
    logger.setVerbosity(VERBOSITY_LEVEL)  # type: ignore
    log_level = _VERBOSITY_TO_LOG_LEVEL[VERBOSITY_LEVEL]
    logger.setLevel(log_level)
    return logger


# Initialize logging
LOG = configure_logging(1)
