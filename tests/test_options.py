# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from capycli.main.options import CommandlineSupport
from tests.test_base import TestBase


class TestCommandlineSupport(TestBase):
    INPUTFILE_INVALID = "plaintext.txt"

    def test_read_config(self):
        sut = CommandlineSupport()
        toml_str = """
           [capycli]
           url = "https://secretserver.com"
           token = "superToken"
           """
        val = sut.read_config(None, toml_str)
        self.assertIsNotNone(val)
        self.assertEqual("https://secretserver.com", val["url"])
        self.assertEqual("superToken", val["token"])

    def test_process_commandline(self):
        sut = CommandlineSupport()
        argv = [
            "bom",
            "show",
            "-v",
            "-X",
            "-url",
            "https://testserver.com",
        ]

        args = sut.parser.parse_args(argv)
        self.assertIsNotNone(args)
        self.assertEqual("https://testserver.com", args.sw360_url)
        self.assertIsNone(args.sw360_token)

        toml_str = """
           [capycli]
           sw360_url = "https://secretserver.com"
           sw360_token = "superToken"
           """
        cf = sut.read_config(None, toml_str)
        self.assertIsNotNone(cf)
        self.assertEqual("https://secretserver.com", cf["sw360_url"])
        self.assertEqual("superToken", cf["sw360_token"])

        for key in cf:
            if hasattr(args, key) and not args.__getattribute__(key):
                args.__setattr__(key, cf[key])

        # test if only non-existing args have been updated
        self.assertEqual("https://testserver.com", args.sw360_url)
        self.assertEqual("superToken", args.sw360_token)


if __name__ == '__main__':
    APP = TestCommandlineSupport()
    APP.test_process_commandline()
