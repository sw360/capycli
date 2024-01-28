# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import sys
from typing import Any

import capycli.moverview.moverview_to_html
import capycli.moverview.moverview_to_xlsx
from capycli.common.print import print_red
from capycli.main.result_codes import ResultCode


def run_moverview_command(args: Any) -> None:
    command = args.command[0].lower()
    if command != "moverview":
        return

    if len(args.command) < 2:
        print_red("No subcommand specified!")
        print()

        # display `moverview` related help
        print("moverview - mapping overview sub-commands")
        print("    ToHtml            create a HTML page showing the mapping result overview")
        print("    ToXlsx            create an Excel sheet showing the mapping result overview")
        return

    subcommand = args.command[1].lower()
    if subcommand == "tohtml":
        """Create a HTML page showing the mapping overview."""
        app = capycli.moverview.moverview_to_html.MappingOverviewToHtml()
        app.run(args)
        return

    if subcommand == "toxlsx":
        """Create an Excel sheet showing the mapping overview."""
        app2 = capycli.moverview.moverview_to_xlsx.MappingOverviewToExcelXlsx()
        app2.run(args)
        return

    print_red("Unknown sub-command: " + subcommand)
    sys.exit(ResultCode.RESULT_COMMAND_ERROR)
