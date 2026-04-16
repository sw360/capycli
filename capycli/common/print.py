# -------------------------------------------------------------------------------
# Copyright (c) 2023-2026 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import datetime
from typing import Any

import capycli.common


def _get_debug_prefix() -> str:
    """Returns a prefix similar to the one from logging."""
    d = datetime.datetime.now()
    ms = d.strftime("%f")[:3]
    prefix = d.strftime("%Y-%m-%d %H:%M:%S,") + ms + ":TEXT:CaPyCLI: "
    return prefix


def print_red(*args: Any, **kwargs: Any) -> None:
    """Print the given text in red color."""
    if capycli.is_debug_logging_enabled():
        print(_get_debug_prefix(), end="")
    # Fore.LIGHTRED_EX = \x1b[91m
    # Style.RESET_ALL = \x1b[0m
    # For whatever reason the colorama constants do not work here, so we use the escape codes directly.
    myargs = [f"\x1b[91m{arg}\x1b[0m" for arg in args]
    print(*myargs, **kwargs)


def print_yellow(*args: Any, **kwargs: Any) -> None:
    """Print the given text in red color."""
    if capycli.is_debug_logging_enabled():
        print(_get_debug_prefix(), end="")
    # Fore.LIGHTYELLOW_EX = \x1b[93m
    # For whatever reason the colorama constants do not work here, so we use the escape codes directly.
    myargs = [f"\x1b[93m{arg}\x1b[0m" for arg in args]
    print(*myargs, **kwargs)


def print_green(*args: Any, **kwargs: Any) -> None:
    """Print the given text in red color."""
    if capycli.is_debug_logging_enabled():
        print(_get_debug_prefix(), end="")
    # Fore.LIGHTGREEN_EX = \x1b[92m
    # For whatever reason the colorama constants do not work here, so we use the escape codes directly.
    myargs = [f"\x1b[92m{arg}\x1b[0m" for arg in args]
    print(*myargs, **kwargs)


def print_text(*args: Any, **kwargs: Any) -> None:
    """Print the given text."""
    if capycli.is_debug_logging_enabled():
        print(_get_debug_prefix(), end="")
    print(*args, **kwargs)
