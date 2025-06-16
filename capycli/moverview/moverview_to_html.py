# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import sys
from typing import Any, Dict

import capycli.common.html_support
import capycli.common.json_support
import capycli.common.script_base
from capycli import get_logger
from capycli.bom.map_bom import MapBom
from capycli.common.map_result import MapResult
from capycli.common.print import print_red, print_text
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class MappingOverviewToHtml(capycli.common.script_base.ScriptBase):
    """Create a HTML page showing the mapping overview."""

    def mapping_overview_to_html(self, overview: Dict[str, Any], outputfile: str) -> None:
        """Create a HTML page showing the mapping overview"""
        myhtml = capycli.common.html_support.HtmlSupport()
        lineend = myhtml.get_lineend()

        with open(outputfile, "w") as htmlfile:
            myhtml.write_start(htmlfile)
            style = myhtml.create_style()
            myhtml.write_header(htmlfile, "Mapping Result Overview", style)
            myhtml.start_body(htmlfile)
            myhtml.write_title_heading(htmlfile, "Mapping Result Overview")

            htmlfile.write("<p>")
            htmlfile.write("Overall Result: <span")
            if overview["OverallResult"] == "COMPLETE":
                htmlfile.write(' style="color:blue;">')
            else:
                htmlfile.write(' style="color:red;">')

            htmlfile.write(overview["OverallResult"])
            htmlfile.write("</span></p>" + lineend)

            htmlfile.write("<table>" + lineend)

            htmlfile.write("<tr><th>Component</th><th>Mapping Result</th></tr>" + lineend)

            for item in overview["Details"]:
                htmlfile.write("<tr>" + lineend)
                htmlfile.write("<td>" + item["BomItem"] + "</td><td>")

                if (item["ResultCode"] == MapResult.INVALID) or (
                    item["ResultCode"] == MapResult.NO_MATCH
                ):
                    htmlfile.write('<span style="color:red;">')
                else:
                    if MapBom.is_good_match(item["ResultCode"]):
                        htmlfile.write('<span style="color:blue;">')
                    else:
                        htmlfile.write('<span style="color:orange;">')

                htmlfile.write(item["ResultText"] + " (" + str(item["ResultCode"]) + ")")
                htmlfile.write("</span>")
                htmlfile.write("</td>" + lineend)
                htmlfile.write("</tr>" + lineend)

            htmlfile.write("</table>" + lineend)

            myhtml.end_body_and_finish(htmlfile)

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)

        print_text(
            "\n" + capycli.get_app_signature() +
            " - Create a HTML page showing the mapping overview\n")

        if args.help:
            print("usage: CaPyCli moverview tohtml -i <mapping_overview.json> -o <mapping_overview.html>")
            print("")
            print("optional arguments:")
            print("-h, --help            show this help message and exit")
            print("-i INPUTFILE,         input mapping result JSON file to read from")
            print("-o OUTPUTFILE,        output HTML file to write to")
            print("")
            return

        if not args.inputfile:
            print_red("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if not args.outputfile:
            print_red("No output file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        print_text("Loading mapping overview " + args.inputfile)
        try:
            overview = capycli.common.json_support.load_json_file(args.inputfile)
        except Exception as ex:
            print_red("Error reading input file: " + repr(ex))
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        print_text("Creating HTML page " + args.outputfile)
        try:
            self.mapping_overview_to_html(overview, args.outputfile)
        except Exception as ex:
            print_red("Error creating overview file: " + repr(ex))
            sys.exit(ResultCode.RESULT_GENERAL_ERROR)

        print()
