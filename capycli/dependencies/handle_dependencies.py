# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import sys
from typing import Any

import capycli.dependencies.javascript
import capycli.dependencies.maven_list
import capycli.dependencies.maven_pom
import capycli.dependencies.nuget
import capycli.dependencies.python
from capycli.common.print import print_red
from capycli.main.result_codes import ResultCode


def run_dependency_command(args: Any) -> None:
    command = args.command[0].lower()
    if command != "getdependencies":
        return

    if len(args.command) < 2:
        print_red("No subcommand specified!")
        print()

        # display `getdependencies` related help
        print("getdependencies - dependency detection specific sub-commands")
        print("    Nuget             determine dependencies for a .Net/Nuget project")
        print("    Python            determine dependencies for a Python project")
        print("    Javascript        determine dependencies for a JavaScript project")
        print("    MavenPom          determine dependencies for a Java/Maven project using the pom.xml file")
        print("    MavenList         determine dependencies for a Java/Maven project using a Maven command")
        return

    subcommand = args.command[1].lower()
    if subcommand == "nuget":
        """Determine Nuget components/dependencies for a given project"""
        app = capycli.dependencies.nuget.GetNuGetDependencies()
        app.run(args)
        return

    if subcommand == "python":
        """Determine Python components/dependencies for a given project"""
        app2 = capycli.dependencies.python.GetPythonDependencies()
        app2.run(args)
        return

    if subcommand == "javascript":
        """Determine Javascript components/dependencies for a given project"""
        app3 = capycli.dependencies.javascript.GetJavascriptDependencies()
        app3.run(args)
        return

    if subcommand == "mavenpom":
        """Determine Java components/dependencies for a given project"""
        app4 = capycli.dependencies.maven_pom.GetJavaMavenPomDependencies()
        app4.run(args)
        return

    if subcommand == "mavenlist":
        """Determine Java components/dependencies for a given project"""
        app5 = capycli.dependencies.maven_list.GetJavaMavenTreeDependencies()
        app5.run(args)
        return

    print_red("Unknown sub-command: " + subcommand)
    sys.exit(ResultCode.RESULT_COMMAND_ERROR)
