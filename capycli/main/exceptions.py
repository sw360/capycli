# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

"""Exception for CaPyCli."""


class CaPyCliException(Exception):
    def __init__(self, msg: str = "") -> None:
        super().__init__(msg)
