# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

"""
Support methods for python scripts.
"""

import time
from typing import Any, Dict

from cyclonedx.model.component import Component


def printProgressBar(
    iteration: int, total: int, prefix: str = '', suffix: str = '', decimals: int = 1,
        length: int = 100, fill: str = '█', printEnd: str = "\r") -> None:
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end=printEnd)

    # print New Line on Complete
    if iteration == total:
        print()


class ScriptSupport:
    """Support methods for python scripts."""

    @staticmethod
    def show_progress(total: int, current: int) -> None:
        """Show progress for the user"""
        pos0 = "\x1b[0G"
        out = "[" + str(total) + "/" + str(current) + "]"
        # back = "\b" * len(out)
        print(out + pos0, end="", flush=True)

    @staticmethod
    def get_time() -> str:
        """Show current (local) time"""
        now = time.localtime()
        t = str(now.tm_year) + "-" + str(now.tm_mon) + "-" \
            + str(now.tm_mday) + ", " + str(now.tm_hour) + ":" \
            + str(now.tm_min) + ":" + str(now.tm_sec)
        return t

    @staticmethod
    def get_full_name_from_dict(dictionary: Dict[Any, Any], name_key: str, version_key: str) -> str:
        """Returns the full name of a project or release"""
        fullname = dictionary[name_key]
        if (version_key in dictionary) and (dictionary[version_key]):
            fullname = fullname + ", " + dictionary[version_key]

        return fullname

    @staticmethod
    def get_full_name_from_component(component: Component) -> str:
        """Returns the full name of a CycloneDX component"""
        fullname = component.name
        if component.version:
            fullname = fullname + ", " + component.version

        return fullname
