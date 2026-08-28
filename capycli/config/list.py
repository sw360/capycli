# -------------------------------------------------------------------------------
# Copyright (c) 2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
from typing import Any, Dict

import capycli.common.html_support
import capycli.common.json_support
import capycli.common.script_base
from capycli import get_logger
from capycli.common.print import print_green, print_text, print_yellow
from capycli.main.options import CommandlineSupport

LOG = get_logger(__name__)


class ConfigList(capycli.common.script_base.ScriptBase):
    """List the configuration settings"""

    def print_config(self, config: Dict[str, Any]) -> None:
        for key in config:
            print(" ", key, "=", config[key])

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)

        print_text(
            "\n" + capycli.APP_NAME + ", " + capycli.get_app_version() +
            " - List the configuration settings\n")

        if args.help:
            print("usage: CaPyCli config list")
            print("")
            return

        cmd_support = CommandlineSupport()

        config: Dict[str, Any] = {}
        env_url = os.environ["SW360ServerUrl"]
        if (env_url):
            print_green("Environment: SW360ServerUrl =", env_url)
            config["url"] = env_url

        env_token = os.environ["SW360ProductionToken"]
        if (env_token):
            print_green("Environment: SW360ServerUrl =", env_token)
            config["token"] = env_token

        print()

        home = os.path.expanduser("~")
        user_cfg = os.path.join(home, cmd_support.CONFIG_FILE_NAME)
        if os.path.isfile(user_cfg):
            print_green("User .capycli.cfg found")
            config_user = cmd_support.read_config(user_cfg)
            self.print_config(config_user)
            config = cmd_support.update_config(config, config_user)
        else:
            print_yellow("No user .capycli.cfg found!")

        if os.path.isfile(cmd_support.CONFIG_FILE_NAME):
            print_green("\nLocal .capycli.cfg found")
            config_local = cmd_support.read_config()
            self.print_config(config_local)
            config = cmd_support.update_config(config, config_local)
        else:
            print_yellow("\nNo local .capycli.cfg found!")

        print()

        print_text("Resulting configuration:")
        self.print_config(config)
        print()
