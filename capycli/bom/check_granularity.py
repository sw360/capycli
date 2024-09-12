# -------------------------------------------------------------------------------
# Copyright (c) 2021-2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources  # type: ignore
import os
import sys
from typing import Any, List, Optional

import requests
from cyclonedx.model import ExternalReferenceType
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from packageurl import PackageURL
from sortedcontainers import SortedSet

import capycli.common.json_support
import capycli.common.script_base
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomWriter
from capycli.common.print import print_red, print_text, print_yellow
from capycli.dependencies.javascript import GetJavascriptDependencies
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class PotentialGranularityIssue:
    """Class to hold potential granularity issues."""
    def __init__(self, component: str, replacement: str, comment: str = "", source_url: str = "") -> None:
        self.component: str = component
        self.replacement: str = replacement
        self.comment: str = comment
        self.source_url: str = source_url


class CheckGranularity(capycli.common.script_base.ScriptBase):
    """
    Check the granularity of all releases in the SBOM.
    """
    def __init__(self) -> None:
        self.granularity_list: List[PotentialGranularityIssue] = []

    @staticmethod
    def get_granularity_list(download_url: str) -> None:
        '''This will only download granularity file from a public repository.
        Make sure to give the raw version of the granularity file separated by ;'''
        response = requests.get(download_url)
        response.raise_for_status()
        with open('granularity_list.csv', 'wb') as f1:
            f1.write(response.content)

    def read_granularity_list(self, download_url: str = "", local_read_granularity: bool = False) -> None:
        """Reads the granularity list from file."""
        self.granularity_list = []
        text_list = ""
        if local_read_granularity:
            try:
                with open('granularity_list.csv', 'r') as f1:
                    text_list = f1.read()
            except FileNotFoundError as e:
                print(f"File not found: {e} \n Reading the default granularity list")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        if download_url:
            try:
                CheckGranularity.get_granularity_list(download_url)
                with open('granularity_list.csv', 'r') as f1:
                    text_list = f1.read()
            except FileNotFoundError as e:
                print(f"File not found: {e} \n Reading the default granularity list")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        if not text_list:
            if sys.version_info >= (3, 9):
                resources = pkg_resources.files("capycli.data")
                text_list = (resources / "granularity_list.csv").read_text()
            else:
                text_list = pkg_resources.read_text("capycli.data", "granularity_list.csv")

        for line in text_list.splitlines():
            # ignore header (first) line
            if line.startswith("component_name;replacement_name"):
                continue

            # ignore comments
            if line.startswith("#"):
                continue

            line = line.strip()
            if not line:
                continue

            # split line
            parts = line.split(";")
            if len(parts) < 2:
                continue

            component = parts[0]
            replacement = parts[1]
            comment = ""
            if len(parts) > 2:
                comment = parts[2]

            source_url = ""
            if len(parts) > 3:
                source_url = parts[3]

            issue = PotentialGranularityIssue(component, replacement, comment, source_url)
            self.granularity_list.append(issue)

    def find_match(self, name: str) -> Optional[PotentialGranularityIssue]:
        """Finds a match by component name."""
        for match in self.granularity_list:
            if match.component.lower() == name.lower():
                return match

        return None

    def get_new_fixed_component(self, component: Component, new_name: str, new_src_url: str) -> Component:
        """Get a !NEW! CycloneDX component to replace the old one."""
        source_url_bak = CycloneDxSupport.get_ext_ref_source_url(component)
        if new_src_url:
            source_url_bak = new_src_url
        language_bak = CycloneDxSupport.get_property(component, CycloneDxSupport.CDX_PROP_LANGUAGE)

        # build new package-url
        purl: PackageURL
        if component.purl:
            old_purl = component.purl
            purl = PackageURL(old_purl.type, old_purl.namespace, new_name, component.version)

            if self.search_meta_data:
                if str(component.purl).startswith("pkg:npm"):
                    GetJavascriptDependencies().try_find_component_metadata(component, "")
        else:
            LOG.warning("  No package-url available - creating default purl")
            purl = PackageURL("generic", "", new_name, component.version)

        # create new component (this is the only way to set a new bom_ref)
        component_new = Component(
            name=new_name,
            version=component.version,
            purl=purl,
            bom_ref=purl.to_string()
        )

        # restore properties we can keep
        if source_url_bak:
            CycloneDxSupport.update_or_set_ext_ref(
                component_new,
                ExternalReferenceType.VCS,
                "",
                source_url_bak
            )

        if language_bak:
            component_new.properties.add(language_bak)

        if component.purl and self.search_meta_data:
            if str(component.purl).startswith("pkg:npm"):
                component_new = GetJavascriptDependencies().try_find_component_metadata(component_new, "")

        return component_new

    def merge_duplicates(self, clist: List[Component]) -> List[Component]:
        """Checks for each release if there are duplicates after granularity check."""
        new_list: List[Component] = []
        for release in clist:
            count = len([item for item in new_list if item.name == release.name
                         and item.version == release.version])
            if count > 0:
                continue
            else:
                new_list.append(release)

        print()
        print_text(str(len(clist) - len(new_list)) + " items can be reduced by granularity check")

        return new_list

    def check_bom_items(self, sbom: Bom) -> Bom:
        """Checks for each release in the list whether it can be found on the specified
        SW360 instance."""

        new_comp_list = []
        for component in sbom.components:
            match = self.find_match(component.name)
            if not match:
                new_comp_list.append(component)
                continue

            print_yellow(
                component.name + ", " +
                component.version + " should get replaced by " +
                match.replacement)

            new_component = self.get_new_fixed_component(
                component,
                match.replacement,
                match.source_url)

            new_comp_list.append(new_component)

        reduced = self.merge_duplicates(new_comp_list)
        sbom.components = SortedSet(reduced)
        return sbom

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)

        print_text(
            "\n" + capycli.APP_NAME + ", " + capycli.get_app_version() +
            " - Check the granularity of all releases in the SBOM.\n")

        if args.help:
            print("usage: CaPyCli bom granularity [-h] [-v] -i bomfile -o updated")
            print("")
            print("optional arguments:")
            print("    -h, --help            show this help message and exit")
            print("    -i INPUTFILE          SBOM file to read from (JSON)")
            print("    -o OUTPUTFILE         write updated to this file (optional)")
            print("    -v                    be verbose")
            print("    -rg                   read the granularity list file from the URL specified")
            print("    -lg                   read the granularity list file from local")
            return

        if not args.inputfile:
            print_red("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        print_text("Reading granularity data from granularity_list.csv...")
        try:
            self.read_granularity_list(args.remote_granularity_list, args.local_granularity_list)
        except Exception as ex:
            print_red("Error reading granularity data: " + repr(ex))
            sys.exit(ResultCode.RESULT_GENERAL_ERROR)
        print("  " + str(len(self.granularity_list)) + " items read.")

        print_text("\nLoading SBOM file", args.inputfile)
        try:
            sbom = CaPyCliBom.read_sbom(args.inputfile)
            for c in sbom.components:
                print(c)
        except Exception as ex:
            print_red("Error reading SBOM: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_READING_BOM)

        if args.verbose:
            print_text(" ", self.get_comp_count_text(sbom), " read from SBOM")

        self.search_meta_data = args.search_meta_data

        new_sbom = self.check_bom_items(sbom)

        print()
        if args.outputfile:
            print_text("Writing new SBOM to " + args.outputfile)

            try:
                SbomWriter.write_to_json(new_sbom, args.outputfile, True)
            except Exception as ex:
                print_red("Error writing new SBOM: " + repr(ex))
                sys.exit(ResultCode.RESULT_ERROR_WRITING_BOM)

            print_text(" " + self.get_comp_count_text(new_sbom) + " written to file " + args.outputfile)
        else:
            print_text("To get updated SBOM file - use the '-o <filename>' parameter")

        print_text("\nDone.")
