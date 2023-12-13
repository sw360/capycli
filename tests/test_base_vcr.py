# -------------------------------------------------------------------------------
# Copyright (c) 2021-23 Siemens
# All Rights Reserved.
# Author: gernot.hillier@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import unittest
from typing import Any

import pytest
import vcr

SW360_BASE_URL = "https://my.server.com/resource/api/"


class CapycliTestBase(unittest.TestCase):
    @pytest.fixture(autouse=True)  # type: ignore
    def capsys(self, capsys: Any) -> None:
        """internal helper to access stdout/stderr captured by pytest
        """
        self.capsys = capsys

    def vcr(self, name: str, record_mode: str = "none") -> Any:
        """use vcr to mockup requests for integration tests

        This provides a context manager for later integration tests using Python vcr.
        It automatically strips authorization headers from recording.

        To record an http request, use:

        with self.vcr("mytest.vcr", record_mode="once"):
            client.get_component("some_id")

        For a test using the recorded fixture file, simply omit `record_mode`:

        with self.vcr("mytest.vcr"):
            client.get_component("some_id")

        :param name: name of the fixture file to use for recording/playback
        :type name: str
        :param record_mode: vcr record mode, see vcr docs - defaults to "none"
        :type record_mode: str, optional
        :return: vcr context manager
        :rtype: context manager
        """
        return vcr.use_cassette("tests/fixtures/" + name,   # type : ignore
                                filter_headers=["Authorization", "User-Agent"],
                                match_on=["method", "uri", "headers", "raw_body"],
                                record_mode=record_mode)
