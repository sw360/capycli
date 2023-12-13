# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import html
import json
import os
import platform
import sys
from io import TextIOWrapper
from typing import Any, Dict, List

from cli_support import CliFile, LicenseTools

import capycli.common.script_base
from capycli import get_logger
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class CreateReadmeOss(capycli.common.script_base.ScriptBase):
    """Create a Readme_OSS."""

    LICENSE_TAG = "License"
    COPYRIGHT_TAG = "Copyright"
    CONTENT_TAG = "Content"

    def __init__(self) -> None:
        if platform.system() == "Windows":
            self.lineend = "\n"
        else:
            self.lineend = "\n"

    @staticmethod
    def element_has_not_readme_tag(element: Any) -> bool:
        """Determines whether the specified item has a
        'not for Readme_OSS' tag."""
        if len(element.tags) == 0:
            return False

        tags = element.tags[0].split(",")
        for tag in tags:
            if tag.upper() == LicenseTools.NOT_README_TAG:
                return True

        return False

    @staticmethod
    def license_has_not_readme_tag(lic: object) -> bool:
        return CreateReadmeOss.element_has_not_readme_tag(lic)

    @staticmethod
    def component_has_not_readme_tag(comp: object) -> bool:
        return CreateReadmeOss.element_has_not_readme_tag(comp)

    def write_start(self, htmlfile) -> None:
        """Writes the start tags."""
        htmlfile.write('<?xml version="1.0" encoding="utf - 8" ?>' + self.lineend)
        htmlfile.write(
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" ' +
            '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
            + self.lineend)
        htmlfile.write('<html xmlns="http://www.w3.org/1999/xhtml">' + self.lineend)

    def write_header(self, htmlfile: TextIOWrapper) -> None:
        """Writes the header tags."""
        htmlfile.write("<head>" + self.lineend)
        htmlfile.write(
            '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'
            + self.lineend)

        htmlfile.write('<style type="text/css">' + self.lineend)
        htmlfile.write("* { " + self.lineend)
        htmlfile.write("font-family: Arial;" + self.lineend)
        htmlfile.write("font-size: 14px;" + self.lineend)
        htmlfile.write("}" + self.lineend)
        htmlfile.write(self.lineend)
        htmlfile.write("h1 {" + self.lineend)
        htmlfile.write("font-size: 18px;" + self.lineend)
        htmlfile.write("}" + self.lineend)
        htmlfile.write(self.lineend)
        htmlfile.write("h2 {" + self.lineend)
        htmlfile.write("font-size: 16px;" + self.lineend)
        htmlfile.write("}" + self.lineend)
        htmlfile.write(self.lineend)
        htmlfile.write("h3 {" + self.lineend)
        htmlfile.write("font-size: 14px;" + self.lineend)
        htmlfile.write("}" + self.lineend)
        htmlfile.write(self.lineend)
        htmlfile.write("p {" + self.lineend)
        htmlfile.write("font-weight: normal" + self.lineend)
        htmlfile.write("}" + self.lineend)
        htmlfile.write(self.lineend)
        htmlfile.write("body {" + self.lineend)
        htmlfile.write("background: #ffffff;" + self.lineend)
        htmlfile.write("}" + self.lineend)
        htmlfile.write(self.lineend)
        htmlfile.write(".top {" + self.lineend)
        htmlfile.write("text-decoration: none;" + self.lineend)
        htmlfile.write("color: blue;" + self.lineend)
        htmlfile.write("padding: 0px 1em;" + self.lineend)
        htmlfile.write("}" + self.lineend)
        htmlfile.write(self.lineend)
        htmlfile.write(".inset {" + self.lineend)
        htmlfile.write("margin: 0.7em;" + self.lineend)
        htmlfile.write("padding: 0.7em;" + self.lineend)
        htmlfile.write("background: white;" + self.lineend)
        htmlfile.write("border-top: 1px solid silver;" + self.lineend)
        htmlfile.write("xborder-right: 1px solid silver;" + self.lineend)
        htmlfile.write("}" + self.lineend)
        htmlfile.write(self.lineend)
        htmlfile.write(".inset p {" + self.lineend)
        htmlfile.write("white-space: pre-wrap;" + self.lineend)
        htmlfile.write("}" + self.lineend)
        htmlfile.write(self.lineend)
        htmlfile.write(".inset .groupId {" + self.lineend)
        htmlfile.write("color: black;" + self.lineend)
        htmlfile.write("font-size: 12px;" + self.lineend)
        htmlfile.write("}" + self.lineend)
        htmlfile.write(self.lineend)
        htmlfile.write(".title {" + self.lineend)
        htmlfile.write("visibility: hidden;" + self.lineend)
        htmlfile.write("}" + self.lineend)
        htmlfile.write(self.lineend)
        htmlfile.write(".error {" + self.lineend)
        htmlfile.write("background: #e95850;" + self.lineend)
        htmlfile.write("}" + self.lineend)
        htmlfile.write("</style>" + self.lineend)

        htmlfile.write("<title>" + self.lineend)
        htmlfile.write("Open Source Software" + self.lineend)
        htmlfile.write("</title>" + self.lineend)
        htmlfile.write("</head>" + self.lineend)

    def start_body(self, htmlfile: TextIOWrapper) -> None:
        """Write the start body tag."""
        htmlfile.write("<body>" + self.lineend)

    def write_title_heading(self, htmlfile: TextIOWrapper, title: str) -> None:
        """Write the title."""
        htmlfile.write("<h1>" + title + "</h1>" + self.lineend)

    def write_preamble(self, config: dict, htmlfile: TextIOWrapper) -> None:
        """Writes the legal preamble."""
        company = config.get("CompanyName", "YOUR COMPANY")
        htmlfile.write("<h2>Open Source Software</h2>" + self.lineend)
        htmlfile.write(
            "Note to Resellers: Please pass on this document to your customer " +
            "to avoid license breach and copyright infringements."
            + self.lineend)
        htmlfile.write("<br />" + self.lineend)
        htmlfile.write("<br />Third-Party Software Information Document" + self.lineend)
        htmlfile.write("<br />" + self.lineend)
        htmlfile.write(
            "<br />This product, solution or service (&quot;Product&quot;) contains " +
            "third-party software components listed in this document. These components " +
            "are Open Source Software licensed under a license approved by the Open Source " +
            f"Initiative (www.opensource.org) or similar licenses as determined by {company} " +
            "(&quot;OSS&quot;) and/or commercial or freeware software components. With " +
            "respect to the OSS components, the applicable OSS license conditions prevail " +
            "over any other terms and conditions covering the Product. The OSS portions of " +
            "this Product are provided royalty-free and can be used at no charge."
            + self.lineend
        )
        htmlfile.write("<br />" + self.lineend)
        htmlfile.write(
            f"<br />If {company} has combined or linked certain components of the Product with/to " +
            "OSS components licensed under the GNU LGPL version 2 or later as per the " +
            "definition of the applicable license, and if use of the corresponding object " +
            "file is not unrestricted (&quot;LGPL Licensed Module&quot;, whereas the LGPL " +
            "Licensed Module and the components that the LGPL Licensed Module is combined " +
            "with or linked to is the &quot;Combined Product&quot;), the following additional " +
            "rights apply, if the relevant LGPL license criteria are met: (i) you are entitled " +
            "to modify the Combined Product for your own use, including but not limited to the " +
            "right to modify the Combined Product to relink modified versions of the LGPL " +
            "Licensed Module, and (ii) you may reverse-engineer the Combined Product, but only " +
            "to debug your modifications. The modification right does not include the right " +
            "to distribute such modifications and you shall maintain in confidence any " +
            "information resulting from such reverse-engineering of a Combined Product."
            + self.lineend)
        htmlfile.write("<br />" + self.lineend)
        htmlfile.write(
            f"<br />Certain OSS licenses require {company} to make source code available, for " +
            "example, the GNU General Public License, the GNU Lesser General Public License " +
            "and the Mozilla Public License. If such licenses are applicable and this " +
            "Product is not shipped with the required source code, a copy of this source " +
            "code can be obtained by anyone in receipt of this information during the " +
            "period required by the applicable OSS licenses by contacting the following address:"
            + self.lineend)
        htmlfile.write("<br />" + self.lineend)
        adr_line1 = config.get("CompanyAddress1", "")
        if adr_line1:
            htmlfile.write("<br />  " + adr_line1 + self.lineend)
        adr_line2 = config.get("CompanyAddress2", "")
        if adr_line1:
            htmlfile.write("<br />  " + adr_line2 + self.lineend)
        adr_line3 = config.get("CompanyAddress3", "")
        if adr_line3:
            htmlfile.write("<br />  " + adr_line3 + self.lineend)
        adr_line4 = config.get("CompanyAddress4", "")
        if adr_line4:
            htmlfile.write("<br />  " + adr_line4 + self.lineend)
        htmlfile.write(
            "<br />  Keyword: Open Source Request (please specify Product name and version, " +
            "if applicable)" + self.lineend)
        htmlfile.write("<br />" + self.lineend)
        htmlfile.write(
            f"<br />{company} may charge a handling fee of up to 5 EUR to fulfil the request."
            + self.lineend)
        htmlfile.write("<br />" + self.lineend)
        htmlfile.write(
            "<br /> Warranty regarding further use of the Open Source Software:"
            + self.lineend)
        htmlfile.write("<br />" + self.lineend)
        htmlfile.write(
            f"<br /> {company}' warranty obligations are set forth in your agreement with " +
            f"{company}. {company} does not provide any warranty or technical support for this " +
            "Product or any OSS components contained in it if they are modified or used in " +
            f"any manner not specified by {company}. The license conditions listed below may " +
            "contain disclaimers that apply between you and the respective licensor. For the " +
            f"avoidance of doubt, {company} does not make any warranty commitment on behalf of " +
            "or binding upon any third party licensor."
            + self.lineend)
        htmlfile.write("<br />" + self.lineend)
        htmlfile.write(
            "<br />Open Source Software and/or other third-party software contained in " +
            "this Product:" + self.lineend)
        htmlfile.write("<br />" + self.lineend)
        htmlfile.write(
            "<br /> Please note the following license conditions and copyright notices " +
            "applicable to Open Source Software and/or other components (or parts thereof):"
            + self.lineend)
        htmlfile.write("<br />" + self.lineend)

    def write_release_overview(self, htmlfile, cli_files) -> None:
        """Writes the release overview."""
        htmlfile.write('<h2 id="releaseHeader">Releases</h2>' + self.lineend)
        htmlfile.write('<ul id="releaseOverview">' + self.lineend)

        for cliFile in cli_files:
            if self.component_has_not_readme_tag(cliFile):
                continue

            # print(self.get_reference_from_name(cliFile.component))

            htmlfile.write("<li>" + self.lineend)
            htmlfile.write(
                '<a href="#h3'
                + self.get_reference_from_name(cliFile.component)
                + '">'
                + cliFile.component
                + "</a>"
                + self.lineend
            )
            htmlfile.write("</li>" + self.lineend)

        # for subProject in this.subProjects
        # 	htmlfile.write("<li>")
        # 	htmlfile.write('<a href=\"#h3' +
        #   self.GetReferenceFromName(subProject.ProjectName) +
        #   '">{subProject.ProjectName}</a>')
        # 	htmlfile.write("</li>")

        htmlfile.write("</ul>" + self.lineend)

    def get_reference_from_name(self, name: str) -> str:
        """HTML references must not include spaces"""
        result = name.replace(" ", "_")
        return result

    def write_sub_project_info(self, htmlfile: TextIOWrapper, cli_files) -> None:
        """Writes the sub project information."""

        # NOT YET IMPLEMENTED

        pass

    def write_release_info(self, htmlfile: TextIOWrapper, cli_files) -> None:
        """Writes the release information."""
        htmlfile.write("<p>" + self.lineend)
        htmlfile.write("<strong>" + self.lineend)
        htmlfile.write(
            "Please note the following license conditions and copyright notices " +
            "applicable to Open Source Software and/or other components (or parts " +
            "thereof):" + self.lineend)
        htmlfile.write("</strong>" + self.lineend)

        htmlfile.write('<ul id="releases" style="list-style-type:none">' + self.lineend)

        for cliFile in cli_files:
            print("    Writing", cliFile.component, "...")

            if self.component_has_not_readme_tag(cliFile):
                continue

            self.write_single_release_info(htmlfile, cliFile)

        htmlfile.write("</ul>" + self.lineend)

    def write_single_sub_project_info(self, htmlfile: TextIOWrapper) -> None:
        """Writes the single sub-project information."""

        # NOT YET IMPLEMENTED

        pass

    def write_single_release_info(self, htmlfile: TextIOWrapper, clifile) -> None:
        """Writes the single release information."""
        htmlfile.write(
            '<li id="'
            + self.get_reference_from_name(clifile.component)
            + '" class="release" title="'
            + clifile.component
            + '">'
            + self.lineend
        )
        htmlfile.write('<div class="inset">' + self.lineend)
        htmlfile.write(
            '<h3 id="h3'
            + self.get_reference_from_name(clifile.component)
            + '">'
            + self.lineend
        )
        htmlfile.write(clifile.component + self.lineend)

        htmlfile.write(
            '<a class="top" href="#releaseHeader">&#8679;</a>' + self.lineend
        )
        htmlfile.write("</h3>" + self.lineend)
        htmlfile.write("</div>" + self.lineend)

        self.write_copyrights(htmlfile, clifile)
        self.write_acknowledgements(htmlfile, clifile)
        self.write_licenses(htmlfile, clifile)

        htmlfile.write("</li>" + self.lineend)

    def is_already_html_encoded(self, text: str) -> bool:
        """Check for some common escape sequences to find out whether the
        given text is already escaped"""
        if "&lt;" in text:
            return True
        if "&gt;" in text:
            return True
        if "&quot;" in text:
            return True
        if "&copy;" in text:
            return True
        if "&#39" in text:
            return True

        return False

    def html_escape(self, text: str) -> str:
        """Escapes the given text, if not already escaped."""
        if not self.is_already_html_encoded(text):
            return html.escape(text)

        return text

    def write_copyrights(self, htmlfile: TextIOWrapper, clifile) -> None:
        """Writes the copyrights."""
        if len(clifile.copyrights) < 1:
            return

        htmlfile.write(self.lineend)
        htmlfile.write("<b>Copyrights:<br /></b>" + self.lineend)
        htmlfile.write('<pre class="copyrights">' + self.lineend)
        for copyr in clifile.copyrights:
            htmlfile.write(self.html_escape(copyr.text) + self.lineend)

        htmlfile.write("</pre>" + self.lineend)
        htmlfile.write(self.lineend)

    def release_has_acknowledgements(self, clifile) -> bool:
        """Determines whether the given release has acknowledgements."""
        for lic in clifile.licenses:
            if len(lic.acknowledgements) > 0:
                return True

        return False

    def write_acknowledgements(self, htmlfile: TextIOWrapper, clifile) -> None:
        """Writes the acknowledgements."""
        if not self.release_has_acknowledgements(clifile):
            return

        htmlfile.write(self.lineend)
        htmlfile.write("<b>Acknowledgements:<br /></b>" + self.lineend)
        htmlfile.write('<pre class="acknowledgements">' + self.lineend)
        for lic in clifile.licenses:
            if self.license_has_not_readme_tag(lic):
                continue

            for acknowledgement in lic.acknowledgements:
                htmlfile.write(self.html_escape(acknowledgement) + self.lineend)

        htmlfile.write("</pre>" + self.lineend)
        htmlfile.write("\n" + self.lineend)

    def write_licenses(self, htmlfile: TextIOWrapper, clifile) -> None:
        """Writes the licenses."""
        htmlfile.write(self.lineend)
        htmlfile.write("<b>Licenses:<br /></b>" + self.lineend)
        htmlfile.write(
            '<ul id="licenseTexts" style="list-style-type:none">' + self.lineend
        )
        count = 1
        for lic in clifile.licenses:
            if self.license_has_not_readme_tag(lic):
                continue

            htmlfile.write('<li id="licenseTextItem' + str(count) + '">' + self.lineend)
            htmlfile.write(
                "<h3>"
                + lic.name
                + '<a class="top" href="#releaseHeader">&#8679;</a></h3>'
                + self.lineend)
            htmlfile.write(
                '<pre class="licenseText" id="licenseText'
                + str(count)
                + '">'
                + self.lineend)

            # print(lic.license_text)

            htmlfile.write(self.html_escape(lic.license_text) + self.lineend)
            htmlfile.write("</pre>" + self.lineend)
            htmlfile.write("</li>" + self.lineend)
            htmlfile.write(self.lineend)
            count = count + 1

        htmlfile.write("</ul>" + self.lineend)
        htmlfile.write(self.lineend)

    def end_body_and_finish(self, htmlfile: TextIOWrapper) -> None:
        htmlfile.write("</body>" + self.lineend)
        htmlfile.write("</html>" + self.lineend)

    def read_config_file(self, filename: str) -> Dict[str, Any]:
        with open(filename) as file:
            text = file.read()
            config = json.loads(text)
        return config

    def read_cli_files(self, config: Dict[str, Any]) -> List[str]:
        """Reads all CLI files"""
        cli_files = []
        unique_components = []
        for file in config["Components"]:
            component_name = file["ComponentName"]
            if component_name not in unique_components:
                unique_components.append(component_name)
            else:
                print_yellow("        Multiple CLI files exist for the same component - manual review needed!")
            filename = file["CliFile"]
            if os.path.isfile(filename):
                print_text("    Reading", component_name, "...")
                clifile = CliFile()
                try:
                    clifile.read_from_file(filename)
                except Exception as ex:
                    print_red(f"Error reading CLI file '{filename}': " + repr(ex))
                    continue

                # set correct component name
                clifile.component = component_name
                cli_files.append(clifile)
            else:
                print_yellow("    No data available for " + component_name)
                clifile = CliFile()
                clifile.component = component_name
                cli_files.append(clifile)

        return cli_files

    def create_readme(self, cli_files: list, output_filename: str, config: dict) -> None:
        """Generates the readme."""
        htmlfile = open(output_filename, "w", encoding="utf-8")
        self.write_start(htmlfile)
        self.write_header(htmlfile)
        self.start_body(htmlfile)
        self.write_title_heading(htmlfile, config.get("ProjectName", "???"))
        self.write_preamble(config, htmlfile)
        self.write_release_overview(htmlfile, cli_files)
        self.write_release_info(htmlfile, cli_files)
        self.write_sub_project_info(htmlfile, cli_files)

        self.end_body_and_finish(htmlfile)
        htmlfile.close()

    def show_command_help(self) -> None:
        print("\nusage: CaPyCli project createreadme [options]")
        print("Options:")
        print("""
  -h, --help       show this help message and exit
  -i CONFIGFILE    readme_oss configuration JSON file
  -o OUTPUTFILE    output file to write to
        """)

        print()

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)

        print_text(
            "\n" + capycli.APP_NAME + ", " + capycli.get_app_version() +
            " - Create a Readme_OSS\n")

        if args.help:
            self.show_command_help()
            return

        if not args.inputfile:
            print_red("No input config file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not args.outputfile:
            print_red("No Readme_OSS file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Config file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        print_text("  Reading config file " + args.inputfile)
        try:
            config = self.read_config_file(args.inputfile)
        except Exception as ex:
            print_red("Error reading config file: " + repr(ex))
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        print_text("  Reading CLI files...")
        cli_files = self.read_cli_files(config)

        print_text("\n  Creating Readme_OSS...")
        self.create_readme(cli_files, args.outputfile, config)

        print_text("\ndone.")
