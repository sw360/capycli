# -------------------------------------------------------------------------------
# Copyright (c) 2026 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources  # type: ignore

import json
import os
import sys
from typing import Any, Dict, List

import requests

# from cyclonedx.model import ExternalReferenceType
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component

import capycli.common.script_base
from capycli.common.capycli_bom_support import CaPyCliBom
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class ComponentCheck(capycli.common.script_base.ScriptBase):
    """
    Check the SBOM for special components.
    """
    def __init__(self) -> None:
        self.component_check_list: Dict[str, Any] = {}
        self.files_to_ignore: List[Dict[str, Any]] = []
        self.verbose = False

    @staticmethod
    def get_component_check_list(download_url: str) -> None:
        """This will only download the component check file from a public repository."""
        response = requests.get(download_url)
        response.raise_for_status()
        with open("component_checks.json", "wb") as f1:
            f1.write(response.content)

    def read_component_check_list(self, download_url: str = "", local_check_list_file: str = "") -> None:
        """Reads the component check list from file."""
        self.component_check_list = {}
        if local_check_list_file:
            try:
                with open(local_check_list_file, "r", encoding="utf-8") as fin:
                    self.component_check_list = json.load(fin)
                if self.verbose:
                    print_text(f"  Reading component checklist from {local_check_list_file}...")
            except FileNotFoundError as e:
                print_yellow(f"File not found: {e} \n Reading the default component check list")
            except Exception as e:
                print_red(f"An unexpected error occurred: {e}")
        if download_url:
            try:
                ComponentCheck.get_component_check_list(download_url)
                with open("component_checks.json", "r", encoding="utf-8") as fin:
                    self.component_check_list = json.load(fin)
                if self.verbose:
                    print_text(f"  Reading component checklist from {download_url}...")
            except FileNotFoundError as e:
                print_yellow(f"File not found: {e} \n Reading the default component check list")
            except Exception as e:
                print_red(f"An unexpected error occurred: {e}")
        if not self.component_check_list:
            text_list = ""
            if sys.version_info >= (3, 9):
                resources = pkg_resources.files("capycli.data")
                text_list = (resources / "component_checks.json").read_text()
            else:
                text_list = pkg_resources.read_text("capycli.data", "component_checks.json")

            self.component_check_list = json.loads(text_list)

    def get_dev_dependencies(self, ecosystem: str) -> List[Dict[str, Any]]:
        """Get the list of dependencies for a specific eco-system."""
        dd = self.component_check_list.get("dev_dependencies", [])
        if not dd:
            return []

        return dd.get(ecosystem, [])

    def is_dev_dependency(self, comp: Component) -> bool:
        """Check whether the given component matches any known development dependency."""
        if comp.purl:
            # preferred: check by package-url
            pd = comp.purl.to_dict()
            ecosystem = pd.get("type", "").lower()
            for entry in self.get_dev_dependencies(ecosystem):
                name_to_compare = entry.get("name", "")
                if comp.purl.namespace and entry.get("namespace", ""):
                    if comp.purl.namespace.lower() != entry.get("namespace", ""):
                        continue

                if comp.name.lower() == name_to_compare.lower():
                    return True

                # it can happen that comp.purl.namespace is empty, but the namespace
                # ...is included in the name
                if entry.get("namespace", ""):
                    name_to_compare = entry.get("namespace", "") + "/" + name_to_compare

                if comp.name.lower() == name_to_compare.lower():
                    return True
        else:
            # fallback: only check by name
            dd = self.component_check_list.get("dev_dependencies", [])
            for ecosystem in dd:
                for entry in dd.get(ecosystem, []):
                    if comp.name.lower() == entry.get("name", ""):
                        return True

        return False

    def is_python_binary_component(self, comp: Component) -> bool:
        """Check whether the given component matches any known python component
        with additional binary dependencies."""
        if comp.purl:
            pd = comp.purl.to_dict()
            if pd.get("type", "").lower() != "pypi":
                return False

        pbc = self.component_check_list.get("python_binary_components", [])
        for entry in pbc:
            if comp.name.lower() == entry.get("name", ""):
                return True

        return False

    def is_file_to_ignore(self, comp: Component) -> bool:
        """Check whether the given component is to be ignored."""
        for entry in self.files_to_ignore:
            if comp.name.lower() == entry.get("name", ""):
                return True

        return False

    def check_bom_items(self, sbom: Bom) -> int:
        """Check the SBOM for special components."""
        special_component_count = 0
        for component in sbom.components:
            if self.is_file_to_ignore(component):
                continue

            if self.is_dev_dependency(component):
                special_component_count += 1
                print_yellow("  ", component.name, component.version, "seems to be a development dependency")

            if self.is_python_binary_component(component):
                special_component_count += 1
                print_yellow("  ", component.name, component.version,
                             "is known as a Python component that has additional binary dependencies")

        return special_component_count

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)
        else:
            # suppress (debug) log output from requests and urllib
            logging.getLogger("requests").setLevel(logging.WARNING)
            logging.getLogger("urllib3").setLevel(logging.WARNING)
            logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

        print_text(
            "\n" + capycli.get_app_signature() +
            " - Check the SBOM for special components.\n")

        if args.help:
            print_text("usage: CaPyCli bom componentcheck [-h] [-v] -i bomfile [-rcl URL] [-lcl FILE]")
            print_text("")
            print_text("optional arguments:")
            print_text("    -h, --help      show this help message and exit")
            print_text("    -i INPUTFILE    SBOM file to read from (JSON)")
            print_text("    -v              be verbose")
            print_text("    -rcl            read the component check list file from the URL specified")
            print_text("    -lcl            read the component check list file from local")
            print("    --forceerror          force an error exit code in case of validation errors or warnings")
            return

        if not args.inputfile:
            print_red("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        self.verbose = args.verbose

        print_text("Reading component checklist...")
        try:
            self.read_component_check_list(args.remote_check_list, args.local_checklist_list)
        except Exception as ex:
            print_red("Error reading component checklist " + repr(ex))
            sys.exit(ResultCode.RESULT_GENERAL_ERROR)
        if len(self.component_check_list) > 0:
            print_text("  Got component checklist.")

        self.files_to_ignore = self.component_check_list.get("files_to_ignore", [])
        print_text(f"  {len(self.files_to_ignore)} components will be ignored.")

        print_text("\nLoading SBOM file", args.inputfile)
        try:
            sbom = CaPyCliBom.read_sbom(args.inputfile)
            # for c in sbom.components:
            #    print(c)
        except Exception as ex:
            print_red("Error reading SBOM: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)

        if args.verbose:
            print_text(" ", self.get_comp_count_text(sbom), "read from SBOM")

        result = self.check_bom_items(sbom)
        print_text("\nDone.")
        if result > 0:
            if args.force_error:
                if args.verbose:
                    print_yellow("Special component(s) found, exiting with code != 0")
                sys.exit(ResultCode.RESULT_SPECIAL_COMPONENT_FOUND)
