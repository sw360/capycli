# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import json

from capycli.main.exceptions import CaPyCliException


def load_json_file(filename):
    """Load a JSON file"""
    try:
        with open(filename, encoding="utf-8") as fin:
            data = json.load(fin)
    except Exception as exp:
        raise CaPyCliException("Invalid JSON file: " + str(exp))

    return data


def write_json_to_file(data, filename):
    """Write the data a JSON file"""
    try:
        with open(filename, "w", encoding="utf-8") as outfile:
            json.dump(data, outfile, indent=2, separators=(',', ': '))
    except Exception as exp:
        raise CaPyCliException("Error writing JSON file: " + str(exp))


def print_json(data, sort_keys=False):
    """Dump a JSON object to screen"""
    print(json.dumps(data, indent=2, sort_keys=sort_keys))
