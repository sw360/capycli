# -------------------------------------------------------------------------------
# (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from capycli import configure_logging
from tests.test_base import TestBase


class TestLogging(TestBase):
    DEBUG_MSG = "Debug message"
    INFO_MSG = "Info message"
    WARING_MSG = "Warning message"
    ERROR_MSG = "Error message"
    CRITICAL_MSG = "Critical message"

    def create_output(self) -> None:
        LOG = configure_logging(2)
        LOG.debug(self.DEBUG_MSG)
        LOG.info(self.INFO_MSG)
        LOG.warning(self.WARING_MSG)
        LOG.error(self.ERROR_MSG)
        LOG.critical(self.CRITICAL_MSG)

    def test_error_critical(self) -> None:
        out = self.capture_stderr(self.create_output)
        # self.dump_textfile(out, "dump.txt")
        self.assertTrue(self.CRITICAL_MSG in out)
        self.assertTrue(self.ERROR_MSG in out)
        self.assertTrue(self.WARING_MSG in out)
        self.assertFalse(self.INFO_MSG in out)
        self.assertFalse(self.DEBUG_MSG in out)

    def test_info_debug(self) -> None:
        out = self.capture_stdout_no_args(self.create_output)
        # self.dump_textfile(out, "dump.txt")
        self.assertFalse(self.CRITICAL_MSG in out)
        self.assertFalse(self.ERROR_MSG in out)
        self.assertTrue(self.WARING_MSG in out)
        self.assertTrue(self.INFO_MSG in out)
        self.assertTrue(self.DEBUG_MSG in out)
