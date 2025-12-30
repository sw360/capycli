# -------------------------------------------------------------------------------
# Copyright (c) 2025 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import os
import sys
import tomllib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from cyclonedx.contrib.license.factories import LicenseFactory
from cyclonedx.model import ExternalReference, ExternalReferenceType, Property, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from halo import Halo
from packageurl import PackageURL

import capycli.common.script_base
from capycli import get_logger
from capycli.bom.findsources import FindSources
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomCreator, SbomWriter
from capycli.common.print import print_red, print_text, print_yellow
from capycli.dependencies.python import GetPythonDependencies
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


@dataclass
class PackageEntry:
    """Represents the relevant data of a cargo.toml or cargo.lock entry."""
    name: str
    version: str
    description: str
    source: str
    checksum: str
    dependencies: List[str]
    added: bool


class GetRustDependencies(capycli.common.script_base.ScriptBase):
    """
    Determine Rust components/dependencies for a given project
    """

    def __init__(self) -> None:
        self.verbose = False
        self.github_name: str = ""
        self.github_token: str = ""
        self.spinner_shape = {
            "interval": 80,
            "frames": [
                "⣾",
                "⣽",
                "⣻",
                "⢿",
                "⡿",
                "⣟",
                "⣯",
                "⣷"
            ]
        }

    def get_package_meta_info(self, name: str, version: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves meta data of the given package from crates.io.

        :param name: the name of the component.
        :param version: the version of the component.
        :type name: string.
        :type version: string.
        :return: the PyPi meta data.
        :rtype: JSON dictionary or None.
        """
        url = "https://crates.io/api/v1/crates/" + name + "/" + version

        if self.verbose:
            LOG.debug("  Retrieving meta data for " + name + ", " + version)

        try:
            response = requests.get(url)
            if not response.ok:
                print_yellow(
                    "  WARNING: no meta data available for package " +
                    name + ", " + version)
                return None

            json = response.json()
            return json
        except Exception as ex:
            print_red(
                "  ERROR: unable to retrieve meta data for package " +
                name + ", " + version + ": " + str(ex))

        return None

    def add_meta_data_to_bomitem(self, cxcomp: Component) -> None:
        """
        Try to lookup meta data for the given item.

        :param bomitem: a single bill of material item (a single component)
        :type bomitem: dictionary
        """
        version = ""
        if cxcomp.version:
            version = cxcomp.version
        metadata = self.get_package_meta_info(cxcomp.name, version)
        if not metadata:
            LOG.debug(f"No metadata found for {cxcomp.name}, {cxcomp.version}")
            return

        if metadata:
            data = metadata.get("version", {})

            # "repository": "https://github.com/microsoft/windows-rs"
            repository = data.get("repository", "")
            if repository:
                LOG.debug("  got repository")
                ext_ref = ExternalReference(
                    type=ExternalReferenceType.VCS,
                    url=XsUri(repository))
                cxcomp.external_references.add(ext_ref)

            homepage = data.get("homepage", "")
            if homepage == "None":
                homepage = ""
            if not homepage and repository:
                homepage = repository
            if homepage:
                LOG.debug("  got website/homepage")
                ext_ref = ExternalReference(
                    type=ExternalReferenceType.WEBSITE,
                    url=XsUri(homepage))
                cxcomp.external_references.add(ext_ref)

            # "license": "MIT OR Apache-2.0"
            license: str = data.get("license", "")
            if license:
                license_factory = LicenseFactory()
                # most Rust components are dual-licensed, MIT OR Apache-2.0
                if (license.lower() == "mit or apache-2.0") or (license.lower() == "apache-2.0 or mit"):
                    cxcomp.licenses.add(license_factory.make_with_expression(license))
                else:
                    cxcomp.licenses.add(license_factory.make_with_name(license))
                LOG.debug("  got license")

            # "checksum": "ae137229bcbd6cdf0f7b80a31df61766145077ddf49416a728b02cb3921ff3fc"

            # "description": "Rust for Windows
            description = data.get("description", "")
            if description and not cxcomp.description:
                cxcomp.description = description

            # before we use the dl_path information, let's see whether we
            # have a homepage URL already *and* it is GitHub *and*
            # we find the matching source code on GitHub
            source_url = ""
            if homepage and FindSources.is_github_repo(homepage):
                fs = FindSources()
                fs.github_name = self.github_name
                fs.github_token = self.github_token

                # first try to guess the source code URL.
                # this works for GitHub releases and does no require
                # rate-limited GitHub API calls
                source_url = fs.guess_source_code_url(homepage, version=version)
                if source_url:
                    ext_ref = ExternalReference(
                        type=ExternalReferenceType.DISTRIBUTION,
                        comment=CaPyCliBom.SOURCE_URL_COMMENT,
                        url=XsUri(source_url))
                    cxcomp.external_references.add(ext_ref)
                    LOG.debug("  got GitHub source file url")
                else:
                    # ok, guess does not help.
                    # Lets hope that the GitHub API can help us
                    # beforer we run into rate-limiting issues
                    source_url = fs.get_github_source_url(homepage, version=version)
                    if source_url:
                        ext_ref = ExternalReference(
                            type=ExternalReferenceType.DISTRIBUTION,
                            comment=CaPyCliBom.SOURCE_URL_COMMENT,
                            url=XsUri(source_url))
                        cxcomp.external_references.add(ext_ref)
                        LOG.debug("  got GitHub source file url")

            # "dl_path": "/api/v1/crates/windows-sys/0.61.2/download"
            dl_path = data.get("dl_path", "")
            dl_path = "https://crates.io" + dl_path
            if not source_url and dl_path:
                ext_ref = ExternalReference(
                    type=ExternalReferenceType.DISTRIBUTION,
                    comment=CaPyCliBom.SOURCE_URL_COMMENT,
                    url=XsUri(dl_path))
                cxcomp.external_references.add(ext_ref)
                LOG.debug("  got dl_path")

    def read_toml_file(self, filename: str, err_hint: str = "") -> Dict[str, Any]:
        """
        Ready a TOML file.

        Args:
            filename (str): the filename

        Returns:
            dict[str, Any]: dictionary
        """
        try:
            with open(filename, "rb") as f:
                toml_data = tomllib.load(f)

            return toml_data
        except Exception as ex:
            LOG.debug(f"Does not look like a {err_hint} file: " + repr(ex))

        return {}

    def analyze_cargo_toml(self,
                           filename: str,
                           packages: list[PackageEntry]) -> None:
        """
        Analyze a Cargo.toml file.

        Args:
            filename (str): the filename
        """
        manifest = self.read_toml_file(filename, "Cargo.toml")

        # analyze project cargo.toml file(s)
        if "package" in manifest:
            pkg = PackageEntry(
                name=manifest["package"]["name"],
                version=manifest["package"].get("version", ""),
                description=manifest["package"].get("description", ""),
                source="",
                checksum="",
                dependencies=[],
                added=False
            )
            packages.append(pkg)
            print_text(f"    Found package: {pkg.name}, version: {pkg.version}")

    def analyze_cargo_lock(self, filename: str) -> list[PackageEntry]:
        """
        Analyze a Cargo.lock file and return all packages/entries found.
        """
        cargo_lock = self.read_toml_file(filename, "Cargo.lock")
        cargo_lock_version = cargo_lock.get("version", 1)
        LOG.debug(f"  Cargo.lock version: {cargo_lock_version}")

        entry_list: List[PackageEntry] = []
        for package in cargo_lock.get("package", []):
            pkg = PackageEntry(
                name=package.get("name", "").strip(),
                version=package.get("version", "").strip(),
                description=package.get("description", "").strip(),
                source=package.get("source", "").strip(),
                checksum=package.get("checksum", "").strip(),
                # dependencies=[dep.split(" ")[0] for dep in package.get("dependencies", [])]
                dependencies=[dep for dep in package.get("dependencies", [])],
                added=False)

            LOG.debug(f"  Processing raw entry: {pkg.name}, {pkg.version}")
            entry_list.append(pkg)

        return entry_list

    def find_lock_entry(self, name: str, entries: List[PackageEntry]) -> Optional[PackageEntry]:
        for entry in entries:
            if name == entry.name:
                return entry

        return None

    def add_entry(self,
                  entry: PackageEntry,
                  entry_list: List[PackageEntry],
                  all_entries: List[PackageEntry],
                  is_package: bool) -> None:
        """Adds an entry and all its dependencies to the final list."""
        if entry.added:
            return

        if not is_package:
            entry_list.append(entry)
            entry.added = True
        else:
            print_yellow(f"    Ignoring package: {entry.name}, {entry.version}")
        for dep2 in entry.dependencies:
            dep_entry = self.find_lock_entry(dep2, all_entries)
            if dep_entry:
                if not dep_entry.source:
                    print_yellow(f"    Ignoring local dependency: {dep_entry.name}, {dep_entry.version}")
                    continue
                self.add_entry(dep_entry, entry_list, all_entries, False)
            else:
                LOG.warning(f"Dependency {dep2} not found!")

    def get_lock_file_entries_for_sbom(self,
                                       all_entries: List[PackageEntry],
                                       packages: list[PackageEntry]) -> List[PackageEntry]:
        """Filter lock file entries to get rid of dev, etc. dependencies."""
        entry_list: List[PackageEntry] = []
        for package in packages:
            entry = self.find_lock_entry(package.name, all_entries)
            if entry:
                self.add_entry(entry, entry_list, all_entries, True)
            else:
                LOG.warning(f"Dependency {package} not found!")

        return entry_list

    def sbom_from_cargo_files(self, folder: str, search_meta_data: bool) -> Bom:
        manifest = self.read_toml_file(os.path.join(folder, "Cargo.toml"))

        # analyze workspace or single project
        project_files: list[str] = []
        if "workspace" in manifest:
            print_text("Evaluating Cargo workspace...")
            projects = manifest["workspace"]["members"]
            for proj in projects:
                project_files.append(os.path.join(folder, proj, "Cargo.toml"))
        else:
            project_files.append(os.path.join(folder, "Cargo.toml"))

        # analyze project cargo.toml file(s)
        packages: list[PackageEntry] = []
        for proj_file in project_files:
            print_text("  Analyzing project file: " + proj_file)
            self.analyze_cargo_toml(proj_file, packages)

        # analyze lock file
        print_text("  Analyzing lock file...")
        all_entries = self.analyze_cargo_lock(os.path.join(folder, "Cargo.lock"))
        entries = self.get_lock_file_entries_for_sbom(all_entries, packages)

        creator = SbomCreator()
        sbom = creator.create([], addlicense=True, addprofile=True, addtools=True)

        if search_meta_data:
            print_text("\nRetrieving package meta data")
            if self.verbose:
                spinner = Halo(text="Retrieving package meta data", spinner=self.spinner_shape)
                spinner.start()

        if len(packages) > 0:
            # add application/package
            app_comp = Component(
                name=packages[0].name,
                version=packages[0].version,
                description=packages[0].description)

        for package in entries:
            if search_meta_data and self.verbose:
                spinner.text = f"Processing package {package.name}, {package.version}"
            purl = PackageURL(type="cargo", name=package.name, version=package.version)
            cxcomp = Component(
                name=package.name,
                version=package.version,
                purl=purl,
                bom_ref=purl.to_string(),
                description=package.description)

            prop = Property(
                name=CycloneDxSupport.CDX_PROP_LANGUAGE,
                value="Rust")
            cxcomp.properties.add(prop)

            if search_meta_data:
                self.add_meta_data_to_bomitem(cxcomp)

            sbom.components.add(cxcomp)
            sbom.register_dependency(app_comp, [cxcomp])

            sbom.metadata.component = app_comp

        if search_meta_data and self.verbose:
            spinner.succeed('Package meta data processing completed.')
            spinner.stop()

        return sbom

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
            "        \n" + capycli.get_app_signature() +
            " - Determine Rust components/dependencies\n")

        if args.help:
            print("usage: capycli getdependencies rust [-i INPUTFILE] [-o OUTFILE] [-v] [--search-meta-data]")
            print("")
            print("Determine Rust project dependencies")
            print("")
            print("optional arguments:")
            print("    -h, --help                     show this help message and exit")
            print("    -i FOLDER, --inputfile FOLDER  folder with the rust cargo project")
            print("    -o OUTFILE, --outfile OUTFILE  output SBOM file")
            print("    -v, --verbose                  verbose output")
            print("    --search-meta-data             search for package meta data")
            print("    -name NAME                     (optional) GitHub name for login")
            print("    -gt TOKEN                      (optional) GitHub token for login")
            return

        if not args.inputfile:
            print_red("No input folder specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isdir(args.inputfile):
            print_red("Input folder not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if not args.outputfile:
            print_red("No output SBOM file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        self.verbose = args.verbose
        self.github_name = args.name
        self.github_token = args.github_token

        sbom = self.sbom_from_cargo_files(args.inputfile, args.search_meta_data)

        GetPythonDependencies.check_meta_data(sbom, self.verbose)

        if self.verbose:
            print()

        print_text("Writing new SBOM to " + args.outputfile)
        SbomWriter.write_to_json(sbom, args.outputfile, True)
        print_text(" " + self.get_comp_count_text(sbom) + " items written to file.")

        print()
