# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from typing import List, Optional

from cyclonedx.model.component import Component

from capycli import LOG
from capycli.common.html_support import HtmlSupport
from capycli.main.exceptions import CaPyCliException


class HtmlConversionSupport():
    @classmethod
    def write_cdx_components_as_html(
            cls,
            bom: List[Component],
            outputfile: str,
            project: Optional[Component]) -> None:
        myhtml = HtmlSupport()
        lineend = myhtml.get_lineend()

        LOG.debug(f"Writing to file {outputfile}")
        try:
            with open(outputfile, "w") as htmlfile:
                name = ""
                if project:
                    name = project.name
                    if project.version:
                        name += ", " + project.version
                myhtml.write_start(htmlfile)
                style = myhtml.create_style()
                title = "Software Bill of Material"
                if name:
                    title += " for project " + name
                myhtml.write_header(htmlfile, title, style)
                myhtml.start_body(htmlfile)
                myhtml.write_title_heading(htmlfile, title)

                htmlfile.write("<table>" + lineend)

                htmlfile.write("<tr><th>Component</th><th>Version</th></tr>" + lineend)

                for cx_comp in bom:
                    htmlfile.write("<tr>" + lineend)
                    htmlfile.write(
                        "<td>"
                        + str(cx_comp.name)
                        + "</td><td>"
                        + str(cx_comp.version)
                        + "</td>"
                        + lineend
                    )
                    htmlfile.write("</tr>" + lineend)

                htmlfile.write("</table>" + lineend)

                myhtml.end_body_and_finish(htmlfile)
        except Exception as exp:
            raise CaPyCliException("Error writing HTML file: " + str(exp))

        LOG.debug("done")
