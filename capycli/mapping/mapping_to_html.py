# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import sys
from typing import Any, Dict, List

import capycli.common.html_support
import capycli.common.json_support
import capycli.common.script_base
from capycli import get_logger
from capycli.bom.map_bom import MapBom
from capycli.common.map_result import MapResult
from capycli.common.print import print_red, print_text
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class MappingToHtml(capycli.common.script_base.ScriptBase):
    """Create a HTML page showing the mapping result"""

    RELEASE_URL = os.environ.get("SW360ServerUrl", "") + "/group/guest/components/-/component/release/detailRelease/"

    def mapping_result_to_html(self, details: List[Dict[str, Any]], outputfile: str) -> None:
        """Create a HTML page showing the mapping overview"""
        myhtml = capycli.common.html_support.HtmlSupport()
        lineend = myhtml.get_lineend()

        with open(outputfile, "w") as htmlfile:
            myhtml.write_start(htmlfile)
            style = myhtml.create_style()
            myhtml.write_header(htmlfile, "Mapping Result Details", style)
            myhtml.start_body(htmlfile)
            myhtml.write_title_heading(htmlfile, "Mapping Result Details")

            htmlfile.write("<table>" + lineend)
            htmlfile.write(
                "<tr><th>BOM Component</th><th>Mapping Result</th><th>Matching Component</th></tr>"
                + lineend
            )

            full_match = True
            for mapresult in details:
                versiontext = mapresult["BomItem"]["Name"]
                if "Version" in mapresult["BomItem"]:
                    versiontext = versiontext + ", " + mapresult["BomItem"]["Version"]

                color = "black"
                if (mapresult["Result"] == MapResult.INVALID) or (
                    mapresult["Result"] == MapResult.NO_MATCH
                ):
                    color = "red"
                    full_match = False
                else:
                    if MapBom.is_good_match(mapresult["Result"]):
                        color = "blue"
                    else:
                        color = "orange"
                        full_match = False

                htmlfile.write("<tr>" + lineend)

                htmlfile.write("<td>")
                htmlfile.write('<span style="color:' + color + ';">')
                htmlfile.write(versiontext)
                htmlfile.write("</span>")
                htmlfile.write("</td>" + lineend)

                htmlfile.write("<td>")
                htmlfile.write('<span style="color:' + color + ';">')
                htmlfile.write(
                    MapResult.map_code_to_string(mapresult["Result"])
                    + " ("
                    + str(mapresult["Result"])
                    + ")"
                )
                htmlfile.write("</span>")
                htmlfile.write("</td>" + lineend)

                htmlfile.write("<td>")
                htmlfile.write('<span style="color:' + color + ';">')
                if (mapresult["Result"] == MapResult.INVALID) or (
                    mapresult["Result"] == MapResult.NO_MATCH
                ):
                    htmlfile.write("(none)")
                else:
                    for matchitem in mapresult["Matches"]:
                        htmlfile.write(matchitem["Name"] + ", " + matchitem["Version"])
                        htmlfile.write("<br/>")

                        if "Sw360Id" in matchitem:
                            id = matchitem["Sw360Id"]
                        else:
                            id = matchitem["Id"]

                        # htmlfile.write("Sw360Id = " + id)
                        htmlfile.write(
                            '<a href="'
                            + self.RELEASE_URL
                            + id
                            + '" target="_blank">'
                            + id
                            + "</a>"
                        )
                        htmlfile.write("<br/>")
                        mid = ""
                        if "RepositoryType" in matchitem:
                            mid = matchitem["RepositoryType"]
                        if "RepositoryId" in matchitem:
                            mid = mid + " = " + matchitem["RepositoryId"]

                        if mid:
                            htmlfile.write(mid)
                            htmlfile.write("<br/>")

                        htmlfile.write("<br/>")

                htmlfile.write("</span>")
                htmlfile.write("</td>" + lineend)

                htmlfile.write("</tr>" + lineend)

            htmlfile.write("</table>" + lineend)

            htmlfile.write("<p>")
            htmlfile.write("Overall Result: <span")
            if full_match:
                htmlfile.write(' style="color:blue;">COMPLETE')
            else:
                htmlfile.write(' style="color:red;">INCOMPLETE')
            htmlfile.write("</span></p>" + lineend)

            myhtml.end_body_and_finish(htmlfile)

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)

        print_text(
            "\n" + capycli.APP_NAME + ", " + capycli.get_app_version() +
            " - Create a HTML page showing the mapping result\n")

        if args.help:
            print("usage: CaPyCli mapping tohtml -i <mapping_result.json> -o <mapping_result.html>")
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

        print_text("Loading mapping result " + args.inputfile)
        try:
            mapping_result = capycli.common.json_support.load_json_file(args.inputfile)
        except Exception as ex:
            print_red("Error reading input file: " + repr(ex))
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        print_text("Creating HTML page " + args.outputfile)
        self.mapping_result_to_html(mapping_result, args.outputfile)

        print()
