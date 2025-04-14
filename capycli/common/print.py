# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import datetime
from typing import Any
import os
from colorama import Fore, Style, init
# Force color support in GitLab CI
FORCE_COLOR = os.environ.get("CI") == "true" and os.environ.get("GITLAB_CI") == "true"

# Initialize colorama with auto-reset and force mode if in GitLab CI
init(autoreset=True, strip=not FORCE_COLOR)
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
    print(Fore.LIGHTRED_EX, end="")
    print(*args, **kwargs, end="")
    print(Style.RESET_ALL)


def print_yellow(*args: Any, **kwargs: Any) -> None:
    """Print the given text in red color."""
    if capycli.is_debug_logging_enabled():
        print(_get_debug_prefix(), end="")
    print(Fore.LIGHTYELLOW_EX, end="")
    print(*args, **kwargs, end="")
    print(Style.RESET_ALL)


def print_green(*args: Any, **kwargs: Any) -> None:
    """Print the given text in red color."""
    if capycli.is_debug_logging_enabled():
        print(_get_debug_prefix(), end="")
    print(Fore.LIGHTGREEN_EX, end="")
    print(*args, **kwargs, end="")
    print(Style.RESET_ALL)


def print_text(*args: Any, **kwargs: Any) -> None:
    """Print the given text."""
    if capycli.is_debug_logging_enabled():
        print(_get_debug_prefix(), end="")
    print(*args, **kwargs)
