# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import sys
from typing import Any, Optional

from cyclonedx.model.bom import Bom
from cyclonedx.model.bom_ref import BomRef
from cyclonedx.model.component import Component
from cyclonedx.model.dependency import Dependency

import capycli.common.script_base
from capycli.common.capycli_bom_support import CaPyCliBom, SbomWriter
from capycli.common.print import print_red, print_text
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)

"""
A general question for merge and diff operation is HOW we compare SBOM component.
For CaPyCLI 1.x the answer was easy: we had a simple JSON format to store component
information and we only compared name and version.

For CaPyCLI 2.x we have CycloneDX as format to store component information and we have
more questions regarding the component comparison:
- what about the package-url?
- what about the bom-ref?
- what happens if certain properties are different?
- what happens if certain external references are different?
- what about the SBOM meta-data
  - what about differences in tools?
  - what about differences in properties like siemens:profile?
  - what about differences in licenses?

cyclonedx-cli only compares group, name and version when doing a diff.
At the moment (version 0.24.2) they do not do any comparison while merging.

Current idea:
* Only compare group, name and version for every component.
* Do not care about different properties, external references, etc. of components with identical group,
  name and version. We cannot really decide what to do. Merging of these component properties could be
  as wrong as comparing them.
* Consider `merge` as an operation to merge a secondary SBOM into a master SBOM.
  The metadata, license and siemens:profile of the master will be persisted in the result.

Remember KISS ("Keep it simple, stupid!"). Use this simple merge approach for the time being.
If there is the need to do better or a great idea on how to do better, we can change the approach.
"""


class MergeBom(capycli.common.script_base.ScriptBase):
    """Merge two SBOM files.
    """

    @staticmethod
    def are_same(c1: Component, c2: Component, deep: bool = False) -> bool:
        """
        Compares two components. If deep if False, then only
        group, name and version are compared.

        If deep is True, also properties and external references are compared.
        """
        if (c1.group != c2.group) or (c1.name != c2.name) or (c1.version != c2.version):
            return False

        if deep:
            # TBD
            pass

        return True

    def find_in_bom(self, bom: Bom, component: Component) -> Optional[Component]:
        """Searches for an item with the given name and version in the given SBOM."""
        for c in bom.components:
            if self.are_same(c, component):
                return c

        return None

    def find_dependency(self, bom_ref: BomRef, bom: Bom) -> Optional[Component]:
        """Find a certain dependency (component) by bom_ref in the given bom."""
        component: Component
        for component in bom.components:
            if component.bom_ref == bom_ref:
                return component

        return None

    def merge_boms(self, bom_old: Bom, bom_new: Bom) -> Bom:
        """Merges two SBOMs."""

        # step 1: merge components
        component_new: Component
        for component_new in bom_new.components:
            found = self.find_in_bom(bom_old, component_new)
            if not found:
                bom_old.components.add(component_new)

        # step 2: reconstruct dependencies
        dep: Dependency
        for dep in bom_new.dependencies:
            cr = self.find_dependency(dep.ref, bom_new)
            if not cr:
                continue
            for d in dep.dependencies:
                cd = self.find_dependency(d.ref, bom_new)
                if cd:
                    bom_old.register_dependency(cr, [cd])

        return bom_old

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)

        print_text(
            "\n" + capycli.get_app_signature() +
            " - Merge two SBOM files.\n")

        if args.help:
            print("usage: CaPyCli bom merge [-h] [-v] bomfile1 bomfile2 [outputfile]")
            print("")
            print("positional arguments:")
            print("    bomfile1              first bill of material, JSON")
            print("    bomfile2              second bill of material, JSON")
            print("")
            print("optional arguments:")
            print("    -h, --help            show this help message and exit")
            print("    outputfile            if outputfile is specified the new SBOM will be written")
            print("                          to this file. Default is overwrite bomfile1")
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

        output = args.command[2]
        if len(args.command) == 5:
            output = args.command[4]

        print_text("Loading first SBOM file", args.command[2])
        try:
            bom_old = CaPyCliBom.read_sbom(args.command[2])
        except Exception as ex:
            print_red("Error reading input SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)
        print_text(" ", self.get_comp_count_text(bom_old), "read from SBOM")

        print_text("Loading second SBOM file", args.command[3])
        try:
            bom_new = CaPyCliBom.read_sbom(args.command[3])
        except Exception as ex:
            print_red("Error reading input SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)
        print_text(" ", self.get_comp_count_text(bom_new), "read from SBOM")

        bom_merged = self.merge_boms(bom_old, bom_new)

        print_text("Writing combined SBOM with", self.get_comp_count_text(bom_merged), "to", output)
        try:
            SbomWriter.write_to_json(bom_merged, output, True)
        except Exception as ex:
            print_red("Error writing updated SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_WRITING_BOM)

        print_text()
