# -------------------------------------------------------------------------------
# Copyright (c) 2019-2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import json
import os
import sys
from typing import Any, Dict, List, Optional

from cyclonedx.model import ExternalReferenceType
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from packageurl import PackageURL

import capycli.common.json_support
import capycli.common.script_base
from capycli import get_logger
from capycli.bom.legacy import LegacySupport
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomWriter
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class FilterBom(capycli.common.script_base.ScriptBase):
    """
    Apply a filter file to a SBOM

    Expected filter file format
    {
        "Include": [
            "optional-Sub-Filter_to_include.json"
        ],
        "Components": [
            {
                "comment": "optional comment",
                "component": {
                    "Name": "Tethys.Logging.Console"
                },
                "Mode": "remove"
            },
            {
                "component": {
                    "Name": ".NET Core",
                    "Version" : "2.1"
                },
                "Mode": "add"
            }
        ]
    }
    """
    def __init__(self) -> None:
        self.verbose = False

    def load_filter_file(self, filter_file: str) -> Dict[str, Any]:
        """Load a single filter file - without any further processing"""
        f = open(filter_file, "r")
        filter = json.load(f)
        return filter

    def append_components(self, clist: List[Dict[str, Any]], to_add_list: List[Dict[str, Any]]) -> None:
        for to_add in to_add_list:
            clist.append(to_add)

    def show_filter(self, filter: Dict[str, Any]) -> None:
        for entry in filter["Components"]:
            comp = entry["component"]
            print_text(
                "  ", comp.get("Name", ""), comp.get("Version", ""),
                comp.get("RepositoryId", ""), entry["Mode"])

    def find_bom_item(self, bom: Bom, filterentry: Dict[str, Any]) -> Optional[Component]:
        """Find an entry in list of bom items."""
        for component in bom.components:
            if component.purl:
                if filterentry.get("RepositoryId", "x") == component.purl:
                    return component

                if filterentry.get("purl", "x") == component.purl:
                    return component

                if filterentry.get("package-url", "x") == component.purl:
                    return component

            if filterentry.get("Name", "x") == component.name:
                if filterentry.get("Version", "x") == component.version:
                    return component

        return None

    def create_bom_item_from_filter_entry(self, filterentry: Dict[str, Any]) -> Component:
        comp = LegacySupport.legacy_component_to_cdx(filterentry)
        return comp

    def update_bom_item_from_filter_entry(self, component: Component, filterentry: Dict[str, Any]) -> None:
        if filterentry["Name"]:
            component.name = filterentry["Name"]

        if "Version" in filterentry:
            component.version = filterentry.get("Version", "")

        if ("Language" in filterentry) and filterentry.get("Language", ""):
            CycloneDxSupport.update_or_set_property(
                component,
                CycloneDxSupport.CDX_PROP_LANGUAGE,
                filterentry.get("Language", ""))

        source_file_url = ""
        if "SourceFileUrl" in filterentry:
            source_file_url = filterentry.get("SourceFileUrl", "")
        elif "SourceUrl" in filterentry:
            source_file_url = filterentry.get("SourceUrl", "")
        if source_file_url:
            CycloneDxSupport.update_or_set_ext_ref(
                component,
                ExternalReferenceType.DISTRIBUTION,
                CaPyCliBom.SOURCE_URL_COMMENT,
                value=source_file_url)

        if ("SourceFile" in filterentry) and filterentry.get("SourceFile", ""):
            CycloneDxSupport.update_or_set_ext_ref(
                component,
                ExternalReferenceType.DISTRIBUTION,
                CaPyCliBom.SOURCE_FILE_COMMENT,
                value=filterentry.get("SourceFile", ""))

        if ("BinaryFile" in filterentry) and filterentry.get("BinaryFile", ""):
            CycloneDxSupport.update_or_set_ext_ref(
                component,
                ExternalReferenceType.DISTRIBUTION,
                CaPyCliBom.BINARY_FILE_COMMENT,
                value=filterentry.get("BinaryFile", ""))

        rtype = ""
        if "RepositoryType" in filterentry:
            rtype = filterentry.get("RepositoryType", "")
        if rtype and ("RepositoryId" in filterentry) and filterentry.get("RepositoryId", ""):
            component.purl = PackageURL.from_string(filterentry.get("RepositoryId", ""))

        if ("Sw360Id" in filterentry) and filterentry.get("Sw360Id", ""):
            CycloneDxSupport.update_or_set_property(
                component,
                CycloneDxSupport.CDX_PROP_SW360ID,
                filterentry.get("Sw360Id", ""))

    def filter_bom(self, bom: Bom, filter_file: str) -> Bom:
        list_temp = []

        filter = self.load_filter_file(filter_file)
        if self.verbose:
            print_text("  Got", len(filter["Components"]), "filter entries")

        filter_folder = os.path.dirname(filter_file)
        for include in filter.get("Include", []):
            # load additional filter files

            if not os.path.exists(include):
                # if include is not an absolute path, try relative path
                include = os.path.join(filter_folder, include)

            if not os.path.exists(include):
                print_yellow("  Filter file " + include + " does not exist!")
                continue

            print("  Loading filter include ", include)
            filter_include = self.load_filter_file(include)
            if self.verbose:
                print_text("    Got", len(filter_include["Components"]), "filter entries")
            self.append_components(filter["Components"], filter_include["Components"])

        print_text("  Total", len(filter["Components"]), "filter entries")
        # self.show_filter(filter)

        # preprocess
        for filterentry in filter["Components"]:
            filterentry["Processed"] = False
            mode = filterentry.get("Mode", "")
            if (mode != "remove") and (mode != "add"):
                print_yellow(
                    "  Invalid filter mode for " +
                    filterentry["component"].get("Name", "???") + ", " +
                    filterentry["component"].get("Version", "???") + ": " +
                    mode)

        for component in bom.components:
            del_item = False

            for filterentry in filter["Components"]:
                if "component" not in filterentry:
                    continue

                match = False
                if "Name" in filterentry["component"]:
                    prefix = ""
                    if filterentry["component"]["Name"].endswith("*"):
                        prefix = filterentry["component"]["Name"][:-1]

                    if prefix:
                        match = component.name.startswith(prefix)
                    else:
                        match = component.name == filterentry["component"]["Name"]
                elif "RepositoryId" in filterentry["component"]:
                    prefix = ""
                    if filterentry["component"]["RepositoryId"].endswith("*"):
                        prefix = filterentry["component"]["RepositoryId"][:-1]

                    if component.purl:
                        if prefix:
                            match = component.purl.to_string().startswith(prefix)
                        else:
                            match = component.purl.to_string() == filterentry["component"]["RepositoryId"]

                if match:
                    if filterentry["Mode"] == "remove":
                        filterentry["Processed"] = True
                        del_item = True
                        if self.verbose:
                            print_text("  Removing " + component.name + ", " + component.version)
                        break

            if not del_item:
                list_temp.append(component)

        for filterentry in filter["Components"]:
            if filterentry["Mode"] == "add":
                existing_entry = self.find_bom_item(bom, filterentry["component"])
                if existing_entry:
                    self.update_bom_item_from_filter_entry(existing_entry, filterentry["component"])
                    if self.verbose:
                        print_text("  Updated " + existing_entry.name + ", " + (existing_entry.version or ""))
                else:
                    if filterentry["component"].get("Name") is None:
                        print_red("To be added dependency missing Name attribute in Filter file.")
                        sys.exit(ResultCode.RESULT_FILTER_ERROR)

                    bomitem = self.create_bom_item_from_filter_entry(filterentry["component"])
                    list_temp.append(bomitem)
                    if self.verbose:
                        print_text("  Added " + bomitem.name + ", " + (bomitem.version or ""))

                filterentry["Processed"] = True

        if self.verbose:
            for filterentry in filter["Components"]:
                if not filterentry["Processed"]:
                    print_yellow(
                        "  No matching entry found for " +
                        filterentry["component"]["Name"] + ", " +
                        filterentry["component"].get("Version", "(all)"))

            print()

        root_component = bom.metadata.component
        bom.components.clear()
        bom.dependencies.clear()
        for c in list_temp:
            bom.components.add(c)
            if root_component:
                bom.register_dependency(root_component, [c])

        return bom

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)

        print_text("\n" + capycli.APP_NAME + ", " + capycli.get_app_version() + " - Apply a filter file to a SBOM\n")

        if args.help:
            print("Usage: CaPyCli bom filter [-h] [-v] -i INPUTFILE -o OUTPUTFILE -filterfile FILTERFILE")
            print("")
            print("Options:")
            print("  -h, --help              show this help message and exit")
            print("  -i INPUTFILE            input file to read from (JSON)")
            print("  -o OUTPUTFILE           output file to write to")
            print("  -filterfile FILTERFILE  filter file to use")
            print("  -v VERBOSE              be verbose")
            return

        if not args.inputfile:
            print_red("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if not args.filterfile:
            print_red("No filter file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.filterfile):
            print_red("Filter file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if not args.outputfile:
            print_red("No output file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        self.verbose = args.verbose

        print_text("Loading SBOM file", args.inputfile)
        try:
            sbom = CaPyCliBom.read_sbom(args.inputfile)
        except Exception as ex:
            print_red("Error reading input SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)
        if self.verbose:
            print_text(" ", self.get_comp_count_text(sbom), "read from SBOM")

        print_text("Applying filter file", args.filterfile)
        sbom = self.filter_bom(sbom, args.filterfile)

        print_text("Writing new SBOM to " + args.outputfile)
        try:
            SbomWriter.write_to_json(sbom, args.outputfile, True)
        except Exception as ex:
            print_red("Error writing updated SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_WRITING_BOM)
        if self.verbose:
            print_text(" ", self.get_comp_count_text(sbom), "written to SBOM file")

        print("\n")
