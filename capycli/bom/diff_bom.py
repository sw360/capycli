# -------------------------------------------------------------------------------
# Copyright (c) 2021-2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, manuel.schaffer@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import sys
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component

import capycli.common.json_support
import capycli.common.script_base
from capycli.bom.merge_bom import MergeBom
from capycli.common.capycli_bom_support import CaPyCliBom, SbomCreator, SbomWriter
from capycli.common.comparable_version import ComparableVersion
from capycli.common.print import print_green, print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class DiffType(str, Enum):
    """Enumeration of component diff results."""

    # Unknown result.
    UNKNOWN = "UNKNOWN"

    # Components are identical.
    IDENTICAL = "IDENTICAL"

    # New component.
    NEW = "NEW"

    # Obsolete component.
    OBSOLETE = "OBSOLETE"

    # A minor update, i.e. x.y.z => x.y.z+1 or x.y.z => x.y+1.zz
    MINOR_UPDATE = "MINOR_UPDATE"

    # A major update, i.e. x.y.z => x+1.yy.zz
    MAJOR_UPDATE = "MAJOR_UPDATE"


class DiffBom(capycli.common.script_base.ScriptBase):
    """Compare two SBOM files    """
    def __init__(self) -> None:
        self.equal_bom: Bom
        self.diff_bom: Bom

    def find_in_bom(self, bom: Bom, component: Component) -> Optional[Component]:
        """Searches for an item with the given name and version in the given SBOM."""
        for c in bom.components:
            if MergeBom.are_same(c, component):
                return c

        return None

    def compare_boms(self, bom_old: Bom, bom_new: Bom) -> Tuple[Bom, Bom]:
        equal_bom = SbomCreator.create([])
        diff_bom = SbomCreator.create([])
        for comp_old in bom_old.components:
            found = self.find_in_bom(bom_new, comp_old)
            if found:
                print_green(
                    "  Release exists in both SBOMs: " +
                    comp_old.name + ", " + comp_old.version)
                if not self.find_in_bom(equal_bom, comp_old):
                    equal_bom.components.add(comp_old)
            else:
                print_red(
                    "  Release has been removed:     " +
                    comp_old.name + ", " + comp_old.version)
                diff_bom.components.add(comp_old)

        for comp_new in bom_new.components:
            found = self.find_in_bom(bom_old, comp_new)
            if not found:
                print_yellow(
                    "  New release:                  " +
                    comp_new.name + ", " + comp_new.version)
                diff_bom.components.add(comp_new)

        return equal_bom, diff_bom

    def compare_boms_with_updates(self, bom_old: Bom, bom_new: Bom) -> List[Dict[str, Any]]:
        """Determine differences in the bills or materials."""
        result: List[Dict[str, Any]] = []

        for comp_old in bom_old.components:
            ritem = {}
            ritem["Name"] = comp_old.name
            ritem["Version"] = comp_old.version

            found = self.find_in_bom(bom_new, comp_old)
            if found:
                ritem["Result"] = DiffType.IDENTICAL
                result.append(ritem)
            else:
                ritem["Result"] = DiffType.OBSOLETE
                result.append(ritem)

        for comp_new in bom_new.components:
            found = self.find_in_bom(bom_old, comp_new)
            if not found:
                ritem = {}
                ritem["Name"] = comp_new.name
                ritem["Version"] = comp_new.version
                ritem["Result"] = DiffType.NEW
                result.append(ritem)

        return self.check_for_updates(result)

    def check_for_updates(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Try to determine if the differences are updates of existing components."""
        removeList = []

        for item in result:
            if item["Result"] != DiffType.OBSOLETE:
                continue

            for itemNew in result:
                if itemNew["Result"] != DiffType.NEW:
                    continue

                if itemNew["Name"].lower() != item["Name"].lower():
                    continue

                try:
                    verOld = ComparableVersion(item["Version"])
                    verNew = ComparableVersion(itemNew["Version"])

                    itemNew["VersionOld"] = item["Version"]
                    if verOld.major != verNew.major:
                        itemNew["Result"] = DiffType.MAJOR_UPDATE
                    else:
                        itemNew["Result"] = DiffType.MINOR_UPDATE

                    removeList.append(item)
                except ValueError:
                    pass

        # remove obsolete entries
        for entry in removeList:
            result.remove(entry)

        return result

    def display_result(self, result: List[Dict[str, Any]], show_identical: bool) -> None:
        for item in result:
            if item["Result"] == DiffType.IDENTICAL:
                if show_identical:
                    print_green(
                        "  Release exists in both SBOMs: " +
                        item["Name"] + ", " + item["Version"])

                continue

            if item["Result"] == DiffType.OBSOLETE:
                print_red(
                    "  Release has been removed:     " +
                    item["Name"] + ", " + item["Version"])
                continue

            if item["Result"] == DiffType.NEW:
                print_yellow(
                    "  New release:                  " +
                    item["Name"] + ", " + item["Version"])
                continue

            if item["Result"] == DiffType.MINOR_UPDATE:
                print_yellow(
                    "  Minor update:                 " +
                    item["Name"] + ", " + item["VersionOld"] + " -> " + item["Version"])
                continue

            if item["Result"] == DiffType.MAJOR_UPDATE:
                print_yellow(
                    "  Major update:                 " +
                    item["Name"] + ", " + item["VersionOld"] + " -> " + item["Version"])
                continue

            # fallback
            print_red(
                "  Unknown result:               " +
                str(item["Result"]) + ": " +
                item["Name"] + ", " + item["Version"])

    def write_result_to_json(self, filename: str, result: List[Dict[str, Any]]) -> None:
        """Write comparison result to a JSON file."""
        capycli.common.json_support.write_json_to_file(result, filename)

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)

        print_text(
            "\n" + capycli.APP_NAME + ", " + capycli.get_app_version() +
            " - Compare two SBOM files.\n")

        if args.help:
            print("usage: CaPyCli bom diff [-h] bomfile_old bomfile_new [-o OUTPUTFILE] [-mr WRITE_MAPRESULT]")
            print("")
            print("The main goal is to find differenses in whole components.")
            print("")
            print("positional arguments:")
            print("    bomfile_old           bill of material, JSON")
            print("    bomfile_new           bill of material, JSON")
            print("")
            print("optional arguments:")
            print("    -h, --help            show this help message and exit")
            print("    -o OUTPUTFILE         output file to write a list of different items to")
            print("    -mr WRITE_MAPRESULT   create a JSON file with the identical SBOM items")
            print("    -v                    improved difference output")
            print("    -all                  improved output, show also identical components")
            return

        if len(args.command) < 4:
            print_red("Not enough input files specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.command[2]):
            print_red("First SBOM file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if not os.path.isfile(args.command[3]):
            print_red("Second SBOM file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        print_text("Loading first SBOM file", args.command[2])
        try:
            bom_old = CaPyCliBom.read_sbom(args.command[2])
        except Exception as ex:
            print_red("Error reading first input SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)
        print_text(" ", len(bom_old.components), "components read from SBOM")

        print_text("Loading second SBOM file", args.command[3])
        try:
            bom_new = CaPyCliBom.read_sbom(args.command[3])
        except Exception as ex:
            print_red("Error reading second input SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)
        print_text(" ", self.get_comp_count_text(bom_new), "read from SBOM")

        print_text()
        if args.verbose:
            result = self.compare_boms_with_updates(bom_old, bom_new)
            self.display_result(result, args.all)
            if args.outputfile:
                self.write_result_to_json(args.outputfile, result)
                args.outputfile = None
        else:
            self.equal_bom, self.diff_bom = self.compare_boms(bom_old, bom_new)

        if args.outputfile:
            print_text(" Creating updated SBOM " + args.outputfile)
            try:
                SbomWriter.write_to_json(self.diff_bom, args.outputfile, True)
            except Exception as ex:
                print_red("Error writing updated SBOM file: " + repr(ex))
                sys.exit(ResultCode.RESULT_ERROR_WRITING_BOM)

        if args.write_mapresult:
            print_text(" Creating mapping result file " + args.write_mapresult)
            try:
                SbomWriter.write_to_json(self.equal_bom, args.write_mapresult, True)
            except Exception as ex:
                print_red("Error writing mapping result SBOM file: " + repr(ex))
                sys.exit(ResultCode.RESULT_ERROR_WRITING_BOM)
            print_text(" " + self.get_comp_count_text(self.equal_bom) + " written to file.")

        print_text()
