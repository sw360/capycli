# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

"""
Support methods for HTML generation
"""

import html
import os
import platform
from io import TextIOWrapper


class HtmlSupport:
    """Support methods for HTML generation"""

    def __init__(self) -> None:
        if platform.system() == "Windows":
            self.lineend = "\r\n"
        else:
            self.lineend = "\n"

    def get_lineend(self) -> str:
        """Return the os specific lineend"""
        return self.lineend

    def write_start(self, htmlfile: TextIOWrapper) -> None:
        """Writes the start tags."""
        htmlfile.write(
            '<?xml version="1.0" encoding="utf - 8" ?>' +
            self.lineend)
        htmlfile.write(
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"'
            + '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
            + self.lineend
        )
        htmlfile.write(
            '<html xmlns="http://www.w3.org/1999/xhtml">' +
            self.lineend)

    def write_header(self, htmlfile: TextIOWrapper, title: str, style: str = "") -> None:
        """Writes the header tags."""
        htmlfile.write("<head>" + self.lineend)
        htmlfile.write(
            '<meta http-equiv="Content-Type" content="text/html;'
            + 'charset=utf-8" />'
            + self.lineend
        )

        htmlfile.write(style + self.lineend)

        htmlfile.write("<title>" + self.lineend)
        htmlfile.write(title + self.lineend)
        htmlfile.write("</title>" + self.lineend)
        htmlfile.write("</head>" + self.lineend)

    def start_body(self, htmlfile: TextIOWrapper) -> None:
        """Write the start body tag."""
        htmlfile.write("<body>" + self.lineend)

    def write_title_heading(self, htmlfile: TextIOWrapper, heading: str) -> None:
        """Write a H1 heading."""
        htmlfile.write("<h1>" + heading + "</h1>" + self.lineend)

    def end_body_and_finish(self, htmlfile: TextIOWrapper) -> None:
        """Write the end tags."""
        htmlfile.write("</body>" + self.lineend)
        htmlfile.write("</html>" + self.lineend)

    @classmethod
    def is_already_html_encoded(cls, text: str) -> bool:
        """Check for some common escape sequences to find out whether the
        given text is already escaped"""
        if "&lt;" in text:
            return True
        if "&gt;" in text:
            return True
        if "&quote;" in text:
            return True
        if "&#39" in text:
            return True

        return False

    def html_escape(self, text: str) -> str:
        """Escapes the given text, if not already escaped."""
        if not self.is_already_html_encoded(text):
            return html.escape(text)

        return text

    @classmethod
    def open_html_in_browser(cls) -> None:
        """show resulting html file"""
        os.system("output.html")

    def create_style(self):
        """Create the HTML style information"""
        lineend = self.get_lineend()
        style = '<style type="text/css">' + lineend
        style = style + "table, tr, th, td {" + lineend
        style = style + "    border: 1px solid black;" + lineend
        style = style + "    border-collapse: collapse;" + lineend
        style = style + "    padding: 3px;" + lineend
        style = style + "}" + lineend
        style = style + "tr:hover {" + lineend
        style = style + "    background-color: #f5f5f5;" + lineend
        style = style + "}" + lineend
        style = style + "th {" + lineend
        style = style + "    background-color: #d5d5d5;" + lineend
        style = style + "}" + lineend
        style = style + "</style>" + lineend

        return style
