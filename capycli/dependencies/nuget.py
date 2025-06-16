# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: martin.stoffel@siemens.com, thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import re
import sys
from typing import Any
from xml.dom import minidom

from cyclonedx.model import Property
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from packageurl import PackageURL

import capycli.common.json_support
import capycli.common.script_base
from capycli import get_logger
from capycli.common.capycli_bom_support import CycloneDxSupport, SbomCreator, SbomWriter
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class GetNuGetDependencies(capycli.common.script_base.ScriptBase):
    """
    Determine Nuget components/dependencies for a given project.
    Read a packages.config file or a .net core project file, extracts the real dependencies.
    """

    def convert_project_file(self, csproj_file: str) -> Bom:
        """Read packages.config or .csproj file and convert to bill of material"""
        sbom = SbomCreator.create([], addlicense=True, addprofile=True, addtools=True)

        data = minidom.parse(csproj_file)

        # old style: packages
        for s in data.getElementsByTagName("package"):
            print_text(s.attributes["id"].value)

            name = s.attributes["id"].value.strip()
            version = s.attributes["version"].value.strip()
            purl = PackageURL("nuget", "", name, version, "", "")
            cxcomp = Component(
                name=name,
                version=version,
                purl=purl,
                bom_ref=purl.to_string())

            prop = Property(
                name=CycloneDxSupport.CDX_PROP_LANGUAGE,
                value="C#")
            cxcomp.properties.add(prop)

            sbom.components.add(cxcomp)

        # new style: PackageReference
        for a in data.getElementsByTagName("ItemGroup"):
            for s in a.getElementsByTagName("PackageReference"):

                name = s.attributes["Include"].value
                version = ""
                if "Version" in s.attributes:
                    # option a) version as attribute
                    version = s.attributes["Version"].value
                else:
                    # option b) version as sub tag
                    version = s.getElementsByTagName("Version")
                    if (not version) or (version.length < 1):
                        print_yellow("No version for for package " + name)
                    else:
                        version = version.item(0).childNodes.item(0).nodeValue

                purl = PackageURL("nuget", "", name, version, "", "")
                cxcomp = Component(
                    name=name,
                    version=version,
                    purl=purl,
                    bom_ref=purl.to_string())

                prop = Property(
                    name=CycloneDxSupport.CDX_PROP_LANGUAGE,
                    value="C#")
                cxcomp.properties.add(prop)

                sbom.components.add(cxcomp)

        return sbom

    def convert_solution_file(self, solution_file: str) -> Bom:
        """
        Read Visual Studio solution file, extract all sub-projects and
        convert all of them to a single bill of material
        """
        totalbom = SbomCreator.create([], addlicense=True, addprofile=True, addtools=True)
        slnfolder = os.path.dirname(solution_file)

        with open(solution_file) as fin:
            for line in fin:
                if line.lower().startswith("project"):
                    # example:
                    #   Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "CommonUI", "CommonUI\CommonUI.csproj", "{2E2C30AD-83B1-409D-B227-DE5BC7916AA7}"  # noqa
                    parts = re.split('"', line)
                    if len(parts) < 6:
                        continue

                    # example:
                    #   parts[3] = "CommonUI"
                    #   parts[5] = "CommonUI\CommonUI.csproj"
                    if not parts[5].endswith(".csproj"):
                        continue

                    print_text("  Processing", parts[5])
                    csproj_file = os.path.join(slnfolder, parts[5])
                    csproj_bom = self.convert_project_file(csproj_file)
                    totalbom = self.merge_bom(totalbom, csproj_bom)

        return totalbom

    def merge_bom(self, bom: Bom, bom_to_add: Bom) -> Bom:
        """
        Merge the bom_to_add into the existing bom.
        """
        for comp_new in bom_to_add.components:
            found = False
            for comp in bom.components:
                if (comp.name == comp_new.name) and (comp.version == comp_new.version):
                    found = True
                    break

            if not found:
                bom.components.add(comp_new)

        return bom

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)

        print_text(
            "\n" + capycli.get_app_signature() +
            " - Determine Nuget components/dependencies\n")

        if args.help:
            print("Usage: capycli getdependencies nuget -i <csproj file> -o <bom.json>")
            print("")
            print("    Options:")
            print("     -i INPUTFILE      csproj or sln input file to read from")
            print("     -o OUTPUTFILE     bom file to write to")
            return

        if not args.inputfile:
            print_red("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if not args.outputfile:
            print_red("No output SBOM file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        print_text("Reading input file " + args.inputfile)
        if args.inputfile.endswith(".sln"):
            sbom = self.convert_solution_file(args.inputfile)
        else:  # assume ".csproj"
            sbom = self.convert_project_file(args.inputfile)

        print_text("Writing new SBOM to " + args.outputfile)
        try:
            SbomWriter.write_to_json(sbom, args.outputfile, True)
        except Exception as ex:
            print_red("Error writing updated SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_WRITING_BOM)
        print_text(" " + self.get_comp_count_text(sbom) + " items written to file.")

        print()
