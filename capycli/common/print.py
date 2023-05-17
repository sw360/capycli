# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import datetime

from colorama import Fore, Style

import capycli.common


def _get_debug_prefix() -> str:
    """Returns a prefix similar to the one from logging."""
    d = datetime.datetime.now()
    ms = d.strftime("%f")[:3]
    prefix = d.strftime("%Y-%m-%d %H:%M:%S,") + ms + ":TEXT:CaPyCLI: "
    return prefix


def print_red(*args, **kwargs) -> None:
    """Print the given text in red color."""
    if capycli.is_debug_logging_enabled():
        print(_get_debug_prefix(), end="")
    print(Fore.LIGHTRED_EX, end="")
    print(*args, **kwargs, end="")
    print(Style.RESET_ALL)


def print_yellow(*args, **kwargs) -> None:
    """Print the given text in red color."""
    if capycli.is_debug_logging_enabled():
        print(_get_debug_prefix(), end="")
    print(Fore.LIGHTYELLOW_EX, end="")
    print(*args, **kwargs, end="")
    print(Style.RESET_ALL)


def print_green(*args, **kwargs) -> None:
    """Print the given text in red color."""
    if capycli.is_debug_logging_enabled():
        print(_get_debug_prefix(), end="")
    print(Fore.LIGHTGREEN_EX, end="")
    print(*args, **kwargs, end="")
    print(Style.RESET_ALL)


def print_text(*args, **kwargs) -> None:
    """Print the given text."""
    if capycli.is_debug_logging_enabled():
        print(_get_debug_prefix(), end="")
    print(*args, **kwargs)
