# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import sys

import capycli.bom.bom_convert
import capycli.bom.check_bom
import capycli.bom.check_bom_item_status
import capycli.bom.check_granularity
import capycli.bom.create_components
import capycli.bom.diff_bom
import capycli.bom.download_sources
import capycli.bom.filter_bom
import capycli.bom.findsources
import capycli.bom.map_bom
import capycli.bom.merge_bom
import capycli.bom.show_bom
from capycli.common.print import print_red
from capycli.main.result_codes import ResultCode


def run_bom_command(args) -> None:
    command = args.command[0].lower()
    if command != "bom":
        return

    if len(args.command) < 2:
        print_red("No subcommand specified!")
        print()

        # display `bom` related help
        print("bom               bill of material (BOM) specific sub-commands")
        print("    Show              display contents of a BOM")
        print("    Convert           Convert SBOM formats")
        print("    Filter            apply filter file to a BOM")
        print("    Check             check that all releases in the BOM exist on target SW360 instance")
        print("    CheckItemStatus   show additional information about BOM items on SW360")
        print("    Map               map a given BOM to data on SW360")
        print("    CreateReleases    create new releases for existing components on SW360")
        print("    CreateComponents  create new components and releases on SW360 (use with care!)")
        print("    DownloadSources   download source files from the URL specified in the SBOM")
        print("    Granularity       check a bill of material for potential component granularity issues")
        print("    Diff              compare two bills of material.")
        print("    Merge             merge two bills of material.")
        print("    Findsources       determine the source code for SBOM items.")
        return

    subcommand = args.command[1].lower()
    if subcommand == "show":
        """Print SBOM contents to stdout."""
        app1 = capycli.bom.show_bom.ShowBom()
        app1.run(args)
        return

    if subcommand == "filter":
        """Apply a filter file to a SBOM."""
        app2 = capycli.bom.filter_bom.FilterBom()
        app2.run(args)
        return

    if subcommand == "check":
        """Check that all releases listed in the SBOM really exist
        on the given target SW360 instance."""
        app3 = capycli.bom.check_bom.CheckBom()
        app3.run(args)
        return

    if subcommand == "checkitemstatus":
        """Show additional information about SBOM items on SW360."""
        app4 = capycli.bom.check_bom_item_status.CheckBomItemStatus()
        app4.run(args)
        return

    if subcommand == "map":
        """Map a given SBOM to data on SW360."""
        app5 = capycli.bom.map_bom.MapBom()
        app5.run(args)
        return

    if subcommand == "createreleases":
        """Create new releases on SW360 for existing components."""
        app6 = capycli.bom.create_components.BomCreateComponents(onlyCreateReleases=True)
        app6.run(args)
        return

    if subcommand == "createcomponents":
        """Create new components and releases on SW360."""
        app7 = capycli.bom.create_components.BomCreateComponents()
        app7.run(args)
        return

    if subcommand == "downloadsources":
        """Download source files from the URL specified in the SBOM."""
        app8 = capycli.bom.download_sources.BomDownloadSources()
        app8.run(args)
        return

    if subcommand == "granularity":
        """Check the granularity of the releases in the SBOM."""
        app9 = capycli.bom.check_granularity.CheckGranularity()
        app9.run(args)
        return

    if subcommand == "diff":
        """Compare two SBOM files."""
        app10 = capycli.bom.diff_bom.DiffBom()
        app10.run(args)
        return

    if subcommand == "merge":
        """Merge two SBOM files."""
        app11 = capycli.bom.merge_bom.MergeBom()
        app11.run(args)
        return

    if subcommand == "findsources":
        """Determine the source code for SBOM items."""
        app12 = capycli.bom.findsources.FindSources()
        app12.run(args)
        return

    if subcommand == "convert":
        """Convert SBOM formats."""
        app13 = capycli.bom.bom_convert.BomConvert()
        app13.run(args)
        return

    print_red("Unknown sub-command: ")
    sys.exit(ResultCode.RESULT_COMMAND_ERROR)
