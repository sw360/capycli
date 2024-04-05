# -------------------------------------------------------------------------------
# Copyright (c) 2019-24 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

"""Contains the logic for all of the default options for CaPyCli."""

import os
from typing import Any, Dict

import tomli

import capycli
from capycli.bom.bom_convert import BomFormat
from capycli.bom.map_bom import MapMode
from capycli.main.argument_parser import ArgumentParser

LOG = capycli.get_logger(__name__)


class CommandlineSupport():
    CONFIG_FILE_NAME = ".capycli.cfg"

    def __init__(self) -> None:
        custom_prog = "CaPyCli, " + capycli.get_app_version()
        custom_usage = "CaPyCli command subcommand [options]"
        command_help = """Commands and Sub-Commands
    getdependencies     dependency detection specific commands
        Nuget             determine dependencies for a .Net/Nuget project
        Python            determine dependencies for a Python project
        Javascript        determine dependencies for a JavaScript project
        MavenPom          determine dependencies for a Java/Maven project using the pom.xml file
        MavenList         determine dependencies for a Java/Maven project using a Maven command

    bom                 bill of material (BOM) specific commands
        Show              display contents of a SBOM
        Convert           convert SBOM formats
        Filter            apply filter file to a SBOM
        Check             check that all releases in the SBOM exist on target SW360 instance
        CheckItemStatus   show additional information about SBOM items on SW360
        Map               map a given SBOM to data on SW360
        CreateReleases    create new releases for existing components on SW360
        CreateComponents  create new components and releases on SW360 (use with care!)
        DownloadSources   download source files from the URL specified in the SBOM
        Granularity       check a bill of material for potential component granularity issues
        Diff              compare two bills of material.
        Merge             merge two bills of material.
        Findsources       determine the source code for SBOM items.

    mapping
        ToHtml            create a HTML page showing the mapping result
        ToXlsx            create an Excel sheet showing the mapping result

    moverview
        ToHtml            create a HTML page showing the mapping result overview
        ToXlsx            create an Excel sheet showing the mapping result overview

    project
        Find              find a project by name
        Prerequisites     checks whether all prerequisites for a successfull
                          software clearing are fulfilled
        Show              show project details
        Licenses          show licenses of all cleared compponents
        Create            create or update a project on SW360
        Update            update an exiting project, preserving linked releases
        GetLicenseInfo    get license info of all project components
        CreateBom         create a SBOM for a project on SW360
        CreateReadme      create a Readme_OSS
        Vulnerabilities   show security vulnerabilities of a project
        ECC               show export control status of a project

    Note that each command has also its own help display, i.e. if you enter
    `capycli project vulnerabilities -h` you will get a help that only shows the options
    for this specific sub-command.
    Entering `capycli project -h` shows all available sub-commands of the project command.
        """
        self.parser = ArgumentParser(
            prog=custom_prog,
            usage=custom_usage,
            description="SW360 Clearing Automation Command Line Interface, version " + capycli.get_app_version())
        self.parser.add_command_help(command_help)

        # store all positional argument in command
        self.parser.add_argument(
            "command",
            nargs="+",
            help="command and subcommand to process")

        self.parser.add_argument(
            "-h",
            "--help",
            help="show a help message and exit",
            action="store_true",
        )

        self.register_options()

    def register_options(self) -> None:
        input_formats = []
        input_formats.append(BomFormat.TEXT)
        input_formats.append(BomFormat.CSV)
        input_formats.append(BomFormat.LEGACY)
        input_formats.append(BomFormat.LEGACY_CX)
        input_formats.append(BomFormat.SBOM)
        input_formats.append(BomFormat.CAPYCLI)

        output_formats = []
        output_formats.append(BomFormat.CAPYCLI)
        output_formats.append(BomFormat.SBOM)
        output_formats.append(BomFormat.TEXT)
        output_formats.append(BomFormat.CSV)
        output_formats.append(BomFormat.LEGACY)
        output_formats.append(BomFormat.HTML)

        map_modes = []
        map_modes.append(MapMode.ALL)
        map_modes.append(MapMode.FOUND)
        map_modes.append(MapMode.NOT_FOUND)

        self.parser.add_argument(
            "-i",
            "--inputfile",
            dest="inputfile",
            help="input file to read from",
        )

        self.parser.add_argument(
            "-ri",
            "--raw-input",
            dest="raw_input",
            help="raw data input file to parse repository urls"
        )

        self.parser.add_argument(
            "-o",
            "--outputfile",
            dest="outputfile",
            help="output file to write to",
        )

        self.parser.add_argument(
            "-filterfile",
            dest="filterfile",
            help="filter file to use",
        )

        self.parser.add_argument(
            "-v",
            help="be verbose",
            dest="verbose",
            action="store_true",
        )

        self.parser.add_argument(
            "-t",
            "--token",
            dest="sw360_token",
            help="use this token for access to SW360",
        )

        self.parser.add_argument(
            "-gt",
            "--github_token",
            dest="github_token",
            help="use this token for access to github",
        )

        self.parser.add_argument(
            "-oa",
            "--oauth2",
            help="this is an oauth2 token",
            action="store_true",
        )

        self.parser.add_argument(
            "-url",
            dest="sw360_url",
            help="use this URL for access to SW360"
        )

        self.parser.add_argument(
            "--nocache",
            dest="nocache",
            help="do not use component cache",
            action="store_true"
        )

        self.parser.add_argument(
            "-cf",
            "--cachefile",
            dest="cachefile",
            help="cache file name to use",
        )

        self.parser.add_argument(
            "-rc",
            "--refresh_cache",
            dest="refresh_cache",
            help="refresh component cache",
            action="store_true",
        )

        self.parser.add_argument(
            "-sc",
            "--similar",
            help="look for components with similar name",
            action="store_true",
        )

        self.parser.add_argument(
            "-ov",
            "--overview",
            dest="create_overview",
            help="create an mapping overview JSON file",
        )

        self.parser.add_argument(
            "-mr",
            "--mapresult",
            dest="write_mapresult",
            help="create a JSON file with the mapping details",
        )

        # used by project commands
        self.parser.add_argument(
            "-name",
            help="name of the project"
        )

        # used by project commands
        self.parser.add_argument(
            "-version",
            help="version of the project"
        )

        # used by project commands
        self.parser.add_argument(
            "-id",
            dest="id",
            help="SW360 id of the project, supersedes name and version parameters"
        )

        # used by GetLicenseInfo
        self.parser.add_argument(
            "-ncli",
            "--no-overwrite-cli",
            dest="ncli",
            help="do not overwrite existing CLI files",
            action="store_true",
        )

        # used by GetLicenseInfo
        self.parser.add_argument(
            "-nconf",
            "--no-overwrite-config",
            dest="nconf",
            help="do not overwrite an existing configuration file",
            action="store_true",
        )

        # used by GetLicenseInfo
        self.parser.add_argument(
            "-dest",
            "--destination",
            dest="destination",
            help="the destination folder",
        )

        # used by CreateProject
        self.parser.add_argument(
            "-source",
            dest="source",
            help="source folder or additional source file"
        )

        # special parsing flag for MapBom
        self.parser.add_argument(
            "--dbx",
            dest="dbx",
            help="relaxed handling of debian version numbers (check subcommand help!)",
            action="store_true",
        )

        self.parser.add_argument(
            "--download",
            help="enable automatic download of missing sources",
            action="store_true",
        )

        # used by getdependencies python
        self.parser.add_argument(
            "--search-meta-data",
            dest="search_meta_data",
            help="search for component meta-data",
            action="store_true",
        )

        # used by project create
        self.parser.add_argument(
            "-old-version",
            dest="old_version",
            help="previous version "
        )

        self.parser.add_argument(
            "-ex",
            help="show exit code",
            action="store_true",
        )

        # used by bom map
        self.parser.add_argument(
            "-rr",
            dest="result_required",
            help="there must be a clearing result available",
            action="store_true"
        )

        # used by getdependencies python
        self.parser.add_argument(
            "-package-source",
            dest="package_source",
            help="URL of the package manager to use",
        )

        # used by bom CheckItemStatus
        self.parser.add_argument(
            "-all",
            help="show/use all items",
            action="store_true",
        )

        # used by ShowSecurityVulnerability
        self.parser.add_argument(
            "-format",
            dest="format",
            help="format to use (text, json, xml)",
        )

        # used by ShowSecurityVulnerability
        self.parser.add_argument(
            "-fe",
            "--forceexit",
            dest="force_exit",
            help="force a specific exit code",
        )

        # used by MapBom
        self.parser.add_argument(
            "-m",
            "--mode",
            choices=map_modes,
            dest="mode",
            help="specific mode for some commands",
        )

        # used by bom convert
        self.parser.add_argument(
            "-if",
            choices=input_formats,
            dest="inputformat",
            help="Specify input file format")

        # used by bom convert
        self.parser.add_argument(
            "-of",
            choices=output_formats,
            dest="outputformat",
            help="Specify output file format")

        # used by bom Granularity
        self.parser.add_argument(
            "-rg",
            "--remote-granularity",
            dest="remote_granularity_list",
            help="read the granularity list file from the download URL specified"
        )

        # used by bom Granularity
        self.parser.add_argument(
            "-lg",
            "--local-granularity",
            dest="local_granularity_list",
            help="read the granularity list file from local"
        )

        self.parser.add_argument(
            "-X",
            dest="debug", action="store_true",
            help="Enable debug output")

        # used by CheckPrerequisites
        self.parser.add_argument(
            "--forceerror",
            dest="force_error",
            action="store_true",
            help="force an error exit code in case of visual errors",
        )

    def read_config(self, filename: str = "", config_string: str = "") -> Dict[str, Any]:
        """
        Read configuration from string or config file.
        """

        toml_dict = None
        try:
            if config_string:
                toml_dict = tomli.loads(config_string)
            elif filename:
                with open(filename, "rb") as f:
                    toml_dict = tomli.load(f)
            else:
                if os.path.isfile(self.CONFIG_FILE_NAME):
                    with open(self.CONFIG_FILE_NAME, "rb") as f:
                        toml_dict = tomli.load(f)

            if not toml_dict:
                return {}

            if "capycli" not in toml_dict:
                return {}

            return toml_dict["capycli"]
        except tomli.TOMLDecodeError as tex:
            LOG.warning("Config file has invalid format: " + repr(tex))
        except Exception as ex:
            LOG.warning("Error reading config file: " + repr(ex))

        return {}

    def process_commandline(self, argv: Any) -> Any:
        """Reads the command line arguments"""
        args = self.parser.parse_args(argv)
        cfg = self.read_config()

        if cfg:
            for key in cfg:
                args_key = key

                # handle some common naming mistakes
                if args_key == "url":
                    args_key = "sw360_url"
                if args_key == "url":
                    args_key = "sw360_url"
                if args_key == "raw-input":
                    args_key = "raw_input"
                if args_key == "token":
                    args_key = "sw360_token"
                if args_key == "oa":
                    args_key = "oauth2"
                if args_key == "search-meta-data":
                    args_key = "search_meta_data"
                if args_key == "old-version":
                    args_key = "old_version"
                if args_key == "package-source":
                    args_key = "package_source"
                if args_key == "forceexit":
                    args_key = "force_exit"

                if hasattr(args, args_key) and not args.__getattribute__(args_key):
                    args.__setattr__(args_key, cfg[key])

        return args
