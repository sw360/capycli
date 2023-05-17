# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

"""Command-line implementation of CaPyCli."""

import sys

from capycli.main import application


def main(argv: list = None):
    """Execute the main bit of the application.
    This handles the creation of an instance of :class:`Application`, runs it,
    and then exits the application.
    :param list argv:
        The arguments to be passed to the application for parsing.
    """
    if argv is None:
        argv = sys.argv[1:]

    app = application.Application()
    app.run(argv)
    app.exit()
