# -------------------------------------------------------------------------------
# Copyright (c) 2020-2025 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import sys
import xml.etree.ElementTree as ET
from typing import Any

from cyclonedx.model import Property
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from packageurl import PackageURL

import capycli.common.json_support
import capycli.common.script_base
from capycli.common.capycli_bom_support import CycloneDxSupport, SbomCreator, SbomWriter
from capycli.common.print import print_red, print_text
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class GetJavaMavenPomDependencies(capycli.common.script_base.ScriptBase):
    """
    Determine Java components/dependencies for a given project.

    Read a pom.xml file, extracts the  dependencies
    and create a bill of material JSON file.
    """
    def parse_xmlns(self, file: str) -> ET.ElementTree:
        events = "start", "start-ns"

        root = None
        ns_map = []

        for event, elem in ET.iterparse(file, events):

            if event == "start-ns":
                ns_map.append(elem)

            elif event == "start":
                if root is None:
                    root = elem
                for prefix, uri in ns_map:
                    elem.set("xmlns:" + prefix, uri)  # type: ignore
                ns_map = []

        return ET.ElementTree(root)

    def process_pom_file(self, pom_file: str) -> Bom:
        """Read pom.xml and convert to bill of material"""
        try:
            tree = self.parse_xmlns(pom_file)
        except Exception as ex:
            print_red("This seems not to be a pom.xml file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)

        root = tree.getroot()
        if not root:
            print_red("This seems not to be a pom.xml file!")
            sys.exit(ResultCode.RESULT_GENERAL_ERROR)

        ns = ""
        for key, value in root.items():
            if key == "xmlns:":
                ns = "{" + value + "}"
                break

        if root.tag != ns + "project":
            print_red("This seems not to be a pom.xml file!")
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)

        artifacts = []
        for elem in root:
            if elem.tag == ns + "dependencies":
                for dep in elem:
                    if dep.tag == ns + "dependency":
                        artifact = {}
                        for item in dep:
                            if item.text and item.tag == ns + "groupId":
                                artifact["groupId"] = item.text.strip()
                            if item.text and item.tag == ns + "artifactId":
                                artifact["artifactId"] = item.text.strip()
                            if item.text and item.tag == ns + "version":
                                artifact["version"] = item.text.strip()

                        artifacts.append(artifact)

        sbom = SbomCreator.create([], addlicense=True, addprofile=True, addtools=True)
        for artifact in artifacts:
            purl = PackageURL(
                "maven", artifact.get("groupId", ""),
                artifact.get("artifactId", ""), artifact.get("version", ""),
                "", "")
            cx_comp = Component(
                name=artifact.get("artifactId", ""),
                version=artifact.get("version", ""),
                purl=purl,
                bom_ref=purl.to_string()
            )

            prop = Property(
                name=CycloneDxSupport.CDX_PROP_LANGUAGE,
                value="Java")
            cx_comp.properties.add(prop)

            sbom.components.add(cx_comp)

        return sbom

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)

        print_text(
            "\n" + capycli.get_app_signature() +
            " - Determine Java components/dependencies\n")

        if args.help:
            print("Usage:")
            print("    CaPyCli getdependencies mavenpom -i <pom file> -o <bom.json>")
            print("")
            print("    Options:")
            print("     -i INPUTFILE      pom input file to read from (JSON)")
            print("     -o OUTPUTFILE     bom file to write to")
            return

        if not args.inputfile:
            print_red("No input file (pom.xml) specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if not args.outputfile:
            print_red("No output SBOM file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        print_text("Reading input file " + args.inputfile)
        sbom = self.process_pom_file(args.inputfile)

        print_text("Writing new SBOM to " + args.outputfile)
        SbomWriter.write_to_json(sbom, args.outputfile, True)
        print_text(" " + self.get_comp_count_text(sbom) + " items written to file.")

        print()
