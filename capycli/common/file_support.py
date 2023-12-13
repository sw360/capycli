# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

"""
File support methods
"""

import os
import shutil

from colorama import Fore, Style


def create_backup(filename: str) -> None:
    """Create backup file"""
    try:
        if os.path.isfile(filename):
            shutil.copyfile(filename, filename + ".bak")
    except Exception as ex:
        print(
            Fore.LIGHTRED_EX +
            "Error creating file backup: " + repr(ex) +
            Style.RESET_ALL)
