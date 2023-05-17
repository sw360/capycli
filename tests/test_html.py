# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

from capycli.bom.html import HtmlConversionSupport
from capycli.common.capycli_bom_support import CaPyCliBom
from tests.test_base import TestBase


class TestHtml(TestBase):
    INPUTFILE1 = "sbom.siemens.capycli.json"
    OUTPUTFILE = "test.html"

    def test_write(self) -> None:
        filename = os.path.join(os.path.dirname(__file__), "fixtures", TestHtml.INPUTFILE1)
        bom = CaPyCliBom.read_sbom(filename)

        print("C =", bom.metadata.component)

        filename_out = os.path.join(
            os.path.dirname(__file__), "fixtures", TestHtml.OUTPUTFILE)
        HtmlConversionSupport.write_cdx_components_as_html(
            bom.components,
            filename_out,
            bom.metadata.component)

        TestHtml.delete_file(filename_out)
