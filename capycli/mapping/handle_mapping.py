# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import sys

import capycli.mapping.mapping_to_html
import capycli.mapping.mapping_to_xlsx
from capycli.common.print import print_red
from capycli.main.result_codes import ResultCode


def run_mapping_command(args):
    command = args.command[0].lower()
    if command != "mapping":
        return

    if len(args.command) < 2:
        print_red("No subcommand specified!")
        print()

        # display `mapping` related help
        print("mapping - mapping sub-commands")
        print("    ToHtml            create a HTML page showing the mapping result")
        print("    ToXlsx            create an Excel sheet showing the mapping result")
        return

    subcommand = args.command[1].lower()
    if subcommand == "tohtml":
        """Create a HTML page showing the mapping result."""
        app = capycli.mapping.mapping_to_html.MappingToHtml()
        app.run(args)
        return

    if subcommand == "toxlsx":
        """Create an Excel sheet showing the mapping result."""
        app = capycli.mapping.mapping_to_xlsx.MappingToExcelXlsx()
        app.run(args)
        return

    print_red("Unknown sub-command: " + subcommand)
    sys.exit(ResultCode.RESULT_COMMAND_ERROR)
