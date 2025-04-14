# -------------------------------------------------------------------------------
# Copyright (c) 2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import sys
from typing import Any

import capycli.config.list
import capycli.mapping.mapping_to_xlsx
from capycli.common.print import print_red
from capycli.main.result_codes import ResultCode


def run_config_command(args: Any) -> None:
    command = args.command[0].lower()
    if command != "config":
        return

    if len(args.command) < 2:
        print_red("No subcommand specified!")
        print()

        # display `mapping` related help
        print("config - mapping sub-commands")
        print("    list            List the configuration settings")
        print("    ToXlsx            create an Excel sheet showing the mapping result")
        return

    subcommand = args.command[1].lower()
    if subcommand == "list":
        """List the configuration settings."""
        app = capycli.config.list.ConfigList()
        app.run(args)
        return

    if subcommand == "toxlsx":
        """Create an Excel sheet showing the mapping result."""
        app2 = capycli.mapping.mapping_to_xlsx.MappingToExcelXlsx()
        app2.run(args)
        return

    print_red("Unknown sub-command: " + subcommand)
    sys.exit(ResultCode.RESULT_COMMAND_ERROR)
