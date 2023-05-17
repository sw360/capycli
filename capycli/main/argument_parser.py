# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

"""Custom argument parser."""

import argparse
import os
import sys
import textwrap


class ArgumentParser(argparse.ArgumentParser):
    """Custom argument parser."""
    def __init__(self, *args, **kwargs):
        self.options = []
        super(ArgumentParser, self).__init__(*args, **kwargs, add_help=False)
        self.program = {key: kwargs[key] for key in kwargs}
        self.command_help = None

    def add_command_help(self, command_help):
        self.command_help = command_help

    def add_argument(self, *args, **kwargs):
        super(ArgumentParser, self).add_argument(*args, **kwargs)
        option = {}
        option["flags"] = [item for item in args]
        for key in kwargs:
            option[key] = kwargs[key]
        self.options.append(option)

    def print_help(self):
        wrapper = textwrap.TextWrapper(width=120)

        # Print usage
        if "usage" in self.program:
            print("Usage: %s" % self.program["usage"])
        else:
            usage = []
            for option in self.options:
                for item in option["flags"]:
                    if "metavar" in option:
                        usage += ["[%s %s]" % (item, option["metavar"])]
                    elif "dest" in option:
                        usage += ["[%s %s]" % (item, option["dest"].upper())]
                    else:
                        usage += ["[%s]" % item]

            wrapper.initial_indent = "Usage: %s " % os.path.basename(sys.argv[0])
            wrapper.subsequent_indent = len(wrapper.initial_indent) * " "
            output = str.join(" ", usage)
            output = wrapper.fill(output)
            print(output)
        print()

        # Print description
        if "description" in self.program:
            print(self.program["description"])
            print()

        # Print command help
        if self.command_help:
            print(self.command_help)
            print()

        # Print options
        print("Options:")
        maxlen = 0
        for option in self.options:
            option["flags2"] = str.join(
                ", ",
                ["%s %s" % (item, option["metavar"])
                    if "metavar" in option else "%s %s" % (item, option["dest"].upper())
                    if "dest" in option else item for item in option["flags"]])
            if len(option["flags2"]) > maxlen:
                maxlen = len(option["flags2"])
        for option in self.options:
            template = "  %-" + str(maxlen) + "s  "
            wrapper.initial_indent = template % option["flags2"]
            wrapper.subsequent_indent = len(wrapper.initial_indent) * " "
            if "help" in option and "default" in option:
                output = option["help"]
                output += " (default: '%s')" % option["default"] \
                    if isinstance(option["default"], str) \
                    else " (default: %s)" % str(option["default"])
                output = wrapper.fill(output)
            elif "help" in option:
                output = option["help"]
                output = wrapper.fill(output)
            elif "default" in option:
                output = "Default: '%s'" % option["default"] \
                    if isinstance(option["default"], str) \
                    else "Default: %s" % str(option["default"])
                output = wrapper.fill(output)
            else:
                output = wrapper.initial_indent
            print(output)
