# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import sys
from typing import Any

import capycli.project.check_prerequisites
import capycli.project.create_bom
import capycli.project.create_project
import capycli.project.create_readme
import capycli.project.find_project
import capycli.project.get_license_info
import capycli.project.show_ecc
import capycli.project.show_licenses
import capycli.project.show_project
import capycli.project.show_vulnerabilities
from capycli.common.print import print_red
from capycli.main.result_codes import ResultCode


def run_project_command(args: Any) -> None:
    command = args.command[0].lower()
    if command != "project":
        return

    if len(args.command) < 2:
        print_red("No subcommand specified!")
        print()

        # display `project` related help
        print("project - project related sub-commands")
        print("    Find              find a project by name")
        print("    Prerequisites     checks whether all prerequisites for a successfull")
        print("                      software clearing are fulfilled")
        print("    Show              show project details")
        print("    Licenses          show licenses of all cleared compponents")
        print("    Create            create or update a project on SW360")
        print("    Update            update an exiting project, preserving linked releases")
        print("    GetLicenseInfo    get license info of all project components")
        print("    CreateBom         create a SBOM for a project on SW360")
        print("    CreateReadme      create a Readme_OSS")
        print("    Vulnerabilities   show security vulnerabilities of a project")
        print("    ECC               Show export control status of a project")
        return

    subcommand = args.command[1].lower()
    if subcommand == "find":
        """Find a project on SW360 and display the project id."""
        app = capycli.project.find_project.FindProject()
        app.run(args)
        return

    if subcommand == "show":
        """Show the project details."""
        app2 = capycli.project.show_project.ShowProject()
        app2.run(args)
        return

    if subcommand == "prerequisites":
        """Checks whether all prerequisites for a successfull software clearing are fulfilled."""
        app3 = capycli.project.check_prerequisites.CheckPrerequisites()
        app3.run(args)
        return

    if subcommand == "licenses":
        """Show licenses of all cleared components."""
        app4 = capycli.project.show_licenses.ShowLicenses()
        app4.run(args)
        return

    if subcommand == "getlicenseinfo":
        """Get license info on all project components."""
        app5 = capycli.project.get_license_info.GetLicenseInfo()
        app5.run(args)
        return

    if subcommand == "createreadme":
        """Create a Readme_OSS."""
        app6 = capycli.project.create_readme.CreateReadmeOss()
        app6.run(args)
        return

    if subcommand == "create":
        """Create or update a project on SW360."""
        app7 = capycli.project.create_project.CreateProject()
        app7.run(args)
        return

    if subcommand == "update":
        """Update a project on SW360, preserving existing releases."""
        app8 = capycli.project.create_project.CreateProject(onlyUpdateProject=True)
        app8.run(args)
        return

    if subcommand == "createbom":
        """Create a SBOM for a project on SW360."""
        app9 = capycli.project.create_bom.CreateBom()
        app9.run(args)
        return

    if subcommand == "vulnerabilities":
        """Show security vulnerabilities of a project."""
        app10 = capycli.project.show_vulnerabilities.ShowSecurityVulnerability()
        app10.run(args)
        return

    if subcommand == "ecc":
        """Show export control status of a project."""
        app11 = capycli.project.show_ecc.ShowExportControlStatus()
        app11.run(args)
        return

    print_red("Unknown sub-command: " + subcommand)
    sys.exit(ResultCode.RESULT_COMMAND_ERROR)
