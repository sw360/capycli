# -------------------------------------------------------------------------------
# Copyright (c) 2019-25 Siemens
# All Rights Reserved.
# Author: martin.stoffel@siemens.com, thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import glob
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional
from xml.dom import minidom

import requests
from cyclonedx.factory.license import LicenseFactory
from cyclonedx.model import ExternalReference, ExternalReferenceType, Property, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from packageurl import PackageURL

import capycli.common.json_support
import capycli.common.script_base
from capycli import get_logger
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomCreator, SbomWriter
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = get_logger(__name__)


class GetNuGetDependencies(capycli.common.script_base.ScriptBase):
    """
    Determine Nuget components/dependencies for a given project.
    Read a packages.config file or a .net core project file, extracts the real dependencies.
    """

    def __init__(self) -> None:
        self.verbose = False
        self.rid_list: List[str] = [
            # Windows RIDs
            "win-x64", "win-x86", "win-arm64",
            # Linux RIDs
            "linux-x64",  # Most desktop distributions like CentOS Stream, Debian, Fedora, Ubuntu, and derivatives
            "linux-musl-x64",  # Lightweight distributions using musl like Alpine Linux
            "linux-musl-arm64",  # Used to build Docker images for 64-bit Arm v8 and minimalistic base images
            "linux-arm",  # Linux distributions running on Arm like Raspbian on Raspberry Pi Model 2+
            "linux-arm64",  # Linux distributions running on 64-bit Arm like Ubuntu Server 64-bit on RasPi Model 3+
            "linux-bionic-arm64",  # Distributions using Android's bionic libc, for example, Termux
            "linux-loongarch64",  # Linux distributions running on LoongArch64

            # macOS RIDs
            "osx-x64",  # Minimum OS version is macOS 10.12 Sierra
            "osx-arm64",

            # iOS RIDs
            "ios-arm64",
            "iossimulator-arm64",
            "iossimulator-x64",

            # Android RIDs
            "android-arm64"
            "android-arm"
            "android-x64"
            "android-x86"
        ]
        self.wellknown_dev_dependencies: List[str] = [
            # Analyzers
            "StyleCop.Analyzers",
            "xunit.analyzers",
            "NUnit.Analyzers",
            "Microsoft.CodeAnalysis",
            "Microsoft.CodeAnalysis.Common",
            "Microsoft.CodeAnalysis.Analyzers",
            "Microsoft.CodeAnalysis.CSharp",
            "Microsoft.CodeAnalysis.Razor",
            "Microsoft.CodeAnalysis.CSharp.CodeStyle",

            # Code generation
            "Microsoft.CodeAnalysis.CSharp.Workspaces",
            "Microsoft.CodeAnalysis.Workspaces.Common",
            "Microsoft.CodeAnalysis.VisualBasic",
            "Microsoft.CodeAnalysis.Scripting",
            "Microsoft.CodeAnalysis.Scripting.Common",
            "Microsoft.CodeAnalysis.VisualBasic.Workspaces",
            "Microsoft.CodeAnalysis.AnalyzerUtilities",
            "Microsoft.CodeAnalysis.CSharp.Features",
            "Microsoft.CodeAnalysis.Workspaces.MSBuild",
            "Microsoft.CodeAnalysis.NetAnalyzers",
            "Microsoft.CodeAnalysis.Compilers",
            "Roslynator.Analyzers",
            "Roslynator.Formatting.Analyzers",
            "Roslynator.CodeAnalysis.Analyzers",
            "Roslynator.CodeFixes",
            "Roslynator.DotNet.Cli",
            "Roslynator.Core",
            "Roslynator.CSharp",

            # Test frameworks
            "Microsoft.NET.Test.Sdk",
            "MSTest.TestAdapter",
            "MSTest.TestFramework",
            "xunit"
            "xunit.abstractions",
            "xunit.core",
            "xunit.assert",
            "xunit.runner.visualstudio",
            "xunit.runner.console",
            "xunit.runner.json",
            "xunit.runner.msbuild",
            "NUnit",
            "NUnit3.TestAdapter",
            "NUnit.ConsoleRunner",
            "NUnit.Console",
            "NUnit.Engine",

            # Mocking frameworks
            "Moq",

            # Code coverage
            "coverlet.msbuild",
            "coverlet.collector",
            "Microsoft.CodeCoverage"

            # Extras
            "Microsoft.CSharp",
            "Microsoft.NETCore.Platforms",
            "Microsoft.NETCore.Targets",
            "Microsoft.TestPlatform.ObjectModel",
            "Microsoft.TestPlatform.TestHost",
            "NETStandard.Library"
        ]
        self.name_net_runtime = ".Net Runtime"
        self.name_net_desktop_runtime = ".Net Desktop Runtime"
        self.name_aspnet_core = "ASP.NET Core"
        self.nuget_api_base_url = "https://api.nuget.org/v3-flatcontainer/"

    def convert_project_file(self, csproj_file: str) -> Bom:
        """Read packages.config or .csproj file and convert to bill of material"""
        sbom = SbomCreator.create([], addlicense=True, addprofile=True, addtools=True)

        data = minidom.parse(csproj_file)

        # old style: packages
        for s in data.getElementsByTagName("package"):
            print_text(s.attributes["id"].value)

            name = s.attributes["id"].value.strip()
            version = s.attributes["version"].value.strip()
            purl = PackageURL("nuget", "", name, version, "", "")
            cxcomp = Component(
                name=name,
                version=version,
                purl=purl,
                bom_ref=purl.to_string())

            prop = Property(
                name=CycloneDxSupport.CDX_PROP_LANGUAGE,
                value="C#")
            cxcomp.properties.add(prop)

            self.add_component_to_bom(sbom, cxcomp)

        # new style: PackageReference
        for a in data.getElementsByTagName("ItemGroup"):
            for s in a.getElementsByTagName("PackageReference"):

                name = s.attributes["Include"].value
                version = ""
                if "Version" in s.attributes:
                    # option a) version as attribute
                    version = s.attributes["Version"].value
                else:
                    # option b) version as sub tag
                    version = s.getElementsByTagName("Version")
                    if (not version) or (version.length < 1):
                        print_yellow("No version for for package " + name)
                    else:
                        version = version.item(0).childNodes.item(0).nodeValue

                purl = PackageURL("nuget", "", name, version, "", "")
                cxcomp = Component(
                    name=name,
                    version=version,
                    purl=purl,
                    bom_ref=purl.to_string())

                prop = Property(
                    name=CycloneDxSupport.CDX_PROP_LANGUAGE,
                    value="C#")
                cxcomp.properties.add(prop)

                self.add_component_to_bom(sbom, cxcomp)

        return sbom

    def is_test_project(self, csproj_file: str) -> bool:
        """
        Check if the given csproj file is a test project.
        This is done by checking for the presence of certain test-related packages.
        """
        data = minidom.parse(csproj_file)

        if data.getElementsByTagName("IsTestProject"):
            for s in data.getElementsByTagName("IsTestProject"):
                if s.firstChild and s.firstChild.nodeValue == "true":  # type: ignore
                    return True

        return False

    def convert_solution_file(self, solution_file: str) -> Bom:
        """
        Read Visual Studio solution file, extract all sub-projects and
        convert all of them to a single bill of material
        """
        totalbom = SbomCreator.create([], addlicense=True, addprofile=True, addtools=True)
        slnfolder = os.path.dirname(solution_file)

        with open(solution_file) as fin:
            for line in fin:
                if line.lower().startswith("project"):
                    # example:
                    #   Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "CommonUI", "CommonUI\CommonUI.csproj", "{2E2C30AD-83B1-409D-B227-DE5BC7916AA7}"  # noqa
                    parts = re.split('"', line)
                    if len(parts) < 6:
                        continue

                    # example:
                    #   parts[3] = "CommonUI"
                    #   parts[5] = "CommonUI\CommonUI.csproj"
                    if not parts[5].endswith(".csproj"):
                        continue

                    print_text("  Processing", parts[5])
                    csproj_file = os.path.join(slnfolder, parts[5])
                    csproj_bom = self.convert_project_file(csproj_file)
                    if not self.is_test_project(csproj_file):
                        self.determine_extras(csproj_file, csproj_bom)
                    totalbom = self.merge_bom(totalbom, csproj_bom)

        return totalbom

    def merge_bom(self, bom: Bom, bom_to_add: Bom) -> Bom:
        """
        Merge the bom_to_add into the existing bom.
        """
        for comp_new in bom_to_add.components:
            found = False
            for comp in bom.components:
                if (comp.name == comp_new.name) and (comp.version == comp_new.version):
                    found = True
                    break

            if not found:
                bom.components.add(comp_new)

        return bom

    def determine_extras(self, csproj_file: str, bom: Bom) -> None:
        """Determine extra dependencies, .Net Runtime, ASP.NET, etc."""
        folder = os.path.dirname(csproj_file)
        release_folder = os.path.join(folder, "bin", "Release")
        if not os.path.isdir(release_folder) and self.verbose:
            print_yellow("    Release folder not found: " + release_folder)
            return

        for file in glob.glob(os.path.join(release_folder, "**", "*.deps.json"), recursive=True):
            self.analyse_deps_json_file(file, bom)

    def analyse_deps_json_file(self, deps_json_file: str, bom: Bom) -> None:
        """Analyse the deps.json file and add components to the BOM."""

        # There can be three different .deps.json files:
        # 1. .deps.json file in the runtime folder, i.e. "net8.0"
        #    This one does not contain the .Net Runtime dependencies
        # 2. .deps.json file in the runtime/rid folder, i.e. "net8.0/win-x64"
        #    This is the one we need to analyse, it contains all the real dependencies
        # 3. .deps.json file in the runtime/rid/publish folder, i.e. "net8.0/win-x64/publish"
        #    This one should be identical to the one in the runtime/rid folder

        folder = os.path.dirname(deps_json_file)
        parts = os.path.split(folder)

        if parts[1] not in self.rid_list:
            if self.verbose:
                print_yellow("    Ignoring .deps.json file in folder " + folder + ", not a recognized RID: " + parts[1])
            return

        print_text("  Processing .deps.json file " + deps_json_file)
        parts = os.path.split(deps_json_file)
        project_name = parts[1][:-10]
        try:
            deps_data = capycli.common.json_support.load_json_file(deps_json_file)
        except Exception as ex:
            print_red("Error reading .deps.json file: " + repr(ex))
            return

        if "targets" not in deps_data:
            print_red("No targets found in .deps.json file.")
            return

        for target in deps_data["targets"]:
            for package_name, package_info in deps_data["targets"][target].items():
                if package_name.startswith(project_name):
                    # Skip the project itself, we only want the dependencies
                    continue

                if package_name.startswith("runtimepack.Microsoft.NETCore.App"):
                    self.add_runtime_component(package_name, bom)
                    continue

                if package_name.startswith("runtimepack.Microsoft.WindowsDesktop.App"):
                    self.add_runtime_desktop_component(package_name, bom)
                    continue

                if package_name.startswith("runtimepack.Microsoft.AspNetCore.App"):
                    self.add_aspnet_component(package_name, bom)
                    continue

                # Ignore well-known dev dependencies
                ignore = False
                for to_ignore in self.wellknown_dev_dependencies:
                    if package_name.startswith(to_ignore):
                        if self.verbose:
                            print_yellow("    Ignoring well-known dev dependency " + package_name)
                        ignore = True
                        break

                if ignore:
                    continue

                # Ignore all runtime stuff
                if package_name.startswith("runtime."):
                    continue

                parts = package_name.split("/")
                name = parts[0]
                version = parts[1]

                purl = PackageURL("nuget", "", name, version, "", "")
                cxcomp = Component(
                    name=name,
                    version=version,
                    purl=purl,
                    bom_ref=purl.to_string())

                prop = Property(
                    name=CycloneDxSupport.CDX_PROP_LANGUAGE,
                    value="C#")
                cxcomp.properties.add(prop)

                self.add_component_to_bom(bom, cxcomp)

    def add_runtime_component(self, package_name: str, bom: Bom) -> None:
        """Add the .NET Runtime component to the BOM."""
        parts = package_name.split("/")
        if len(parts) < 2:
            print_red("Invalid runtime package name: " + package_name)
            return

        version = parts[1]

        # dummy purl
        purl = PackageURL("nuget", "", self.name_net_runtime, version, "", "")
        cxcomp = Component(
            name=self.name_net_runtime,
            version=version,
            purl=purl,
            bom_ref=purl.to_string())

        prop = Property(
            name=CycloneDxSupport.CDX_PROP_LANGUAGE,
            value="C#")
        cxcomp.properties.add(prop)

        if self.verbose:
            print_text("    Adding runtime component " + self.name_net_runtime + " " + version)

        self.add_component_to_bom(bom, cxcomp)

    def add_runtime_desktop_component(self, package_name: str, bom: Bom) -> None:
        """Add the .NET Runtime component to the BOM."""
        parts = package_name.split("/")
        if len(parts) < 2:
            print_red("Invalid runtime package name: " + package_name)
            return

        version = parts[1]

        # dummy purl
        purl = PackageURL("nuget", "", self.name_net_desktop_runtime, version, "", "")
        cxcomp = Component(
            name=self.name_net_desktop_runtime,
            version=version,
            purl=purl,
            bom_ref=purl.to_string())

        prop = Property(
            name=CycloneDxSupport.CDX_PROP_LANGUAGE,
            value="C#")
        cxcomp.properties.add(prop)

        if self.verbose:
            print_text("    Adding runtime component " + self.name_net_desktop_runtime + " " + version)

        self.add_component_to_bom(bom, cxcomp)

    def add_aspnet_component(self, package_name: str, bom: Bom) -> None:
        """Add the ASP.NET Core component to the BOM."""
        parts = package_name.split("/")
        if len(parts) < 2:
            print_red("Invalid runtime package name: " + package_name)
            return

        version = parts[1]

        # dummy purl
        purl = PackageURL("nuget", "", self.name_aspnet_core, version, "", "")
        cxcomp = Component(
            name=self.name_aspnet_core,
            version=version,
            purl=purl,
            bom_ref=purl.to_string())

        prop = Property(
            name=CycloneDxSupport.CDX_PROP_LANGUAGE,
            value="C#")
        cxcomp.properties.add(prop)

        if self.verbose:
            print_text("    Adding runtime component " + self.name_aspnet_core + " " + version)

        self.add_component_to_bom(bom, cxcomp)

    def add_component_to_bom(self, bom: Bom, comp: Component) -> None:
        """Add a component to the BOM if it does not already exist."""
        for existing_comp in bom.components:
            if (existing_comp.name == comp.name) and (existing_comp.version == comp.version):
                return

        if comp.name in self.wellknown_dev_dependencies:
            if self.verbose:
                print_yellow(f"    Ignoring well-known dev dependency {comp.name} {comp.version}")
            return

        if self.verbose:
            print_text(f"    Adding component {comp.name} {comp.version}")

        bom.components.add(comp)

    def get_nuget_metadata(self, name: str, version: str) -> Optional[Dict[str, Any]]:
        # extras
        if name == self.name_net_runtime:
            return {
                "repository": "https://github.com/dotnet/runtime",
                "sourcecode": "https://github.com/dotnet/runtime/archive/refs/tags/v" + version + ".zip",
                "homepage": "https://dot.net/",
                "license": "MIT"
            }

        if name == self.name_aspnet_core:
            return {
                "repository": "https://github.com/dotnet/aspnetcore",
                "sourcecode": "https://github.com/dotnet/aspnetcore/archive/refs/tags/v" + version + ".zip",
                "homepage": "https://dotnet.microsoft.com/en-us/apps/aspnet",
                "license": "MIT"
            }

        if name == self.name_net_desktop_runtime:
            return {
                "repository": "https://github.com/dotnet/windowsdesktop",
                "sourcecode": "https://github.com/dotnet/windowsdesktop/archive/refs/tags/v" + version + ".zip",
                "license": "MIT"
            }

        url = self.nuget_api_base_url + name.lower() + "/" + version + "/" + name.lower() + ".nuspec"
        try:
            response = requests.get(url)
            if not response.ok:
                print_yellow(
                    "  WARNING: no meta data available for package " +
                    name + ", " + version)
                return None

            json: Dict[str, Any] = {}
            xml = response.content
            if not xml:
                print_yellow(
                    "  WARNING: no meta data available for package " +
                    name + ", " + version)
                return None

            # parse XML
            data = minidom.parseString(xml)
            authors_xml = data.getElementsByTagName("authors")
            # <authors>James Newton-King</authors>
            if authors_xml and authors_xml.length > 0:
                json["author"] = authors_xml.item(0).firstChild.nodeValue.strip()  # type: ignore

            license_xml = data.getElementsByTagName("license")
            # <license type="expression">MIT</license>
            if license_xml and license_xml.length > 0:
                ld = license_xml.item(0)
                if ld.attributes and ld.attributes["type"].value == "expression":  # type: ignore
                    json["license"] = ld.firstChild.nodeValue.strip()  # type: ignore

            if not json.get("license", ""):
                license_xml = data.getElementsByTagName("licenseUrl")
                # <licenseUrl>https://raw.github.com/JamesNK/Newtonsoft.Json/master/LICENSE.md</licenseUrl>
                if license_xml and license_xml.length > 0:
                    json["license"] = license_xml.item(0).firstChild.nodeValue.strip()  # type: ignore

            repository_xml = data.getElementsByTagName("repository")
            # <repository type="git" url="https://github.com/NuGet/NuGet.Client.git" />
            if repository_xml and repository_xml.length > 0:
                rep = repository_xml.item(0)
                if rep.attributes and rep.attributes["url"]:  # type: ignore
                    json["repository"] = rep.attributes["url"].value  # type: ignore

            project_xml = data.getElementsByTagName("projectUrl")
            # projectUrl copyright  repository projectUrl packageProjectUrl
            if project_xml and project_xml.length > 0:
                json["project"] = project_xml.item(0).firstChild.nodeValue.strip()  # type: ignore

            copyright_xml = data.getElementsByTagName("copyright")
            if copyright_xml and copyright_xml.length > 0:
                json["copyright"] = copyright_xml.item(0).firstChild.nodeValue.strip()  # type: ignore

            description_xml = data.getElementsByTagName("description")
            if description_xml and description_xml.length > 0:
                json["description"] = description_xml.item(0).firstChild.nodeValue.strip()  # type: ignore

            return json

        except Exception as ex:
            print_red(
                "  ERROR: unable to retrieve meta data for package " +
                name + ", " + version + ": " + str(ex))

        return None

    def search_meta_data(self, sbom: Bom) -> None:
        if self.verbose:
            print_text("\nFinding meta-data:")

        cxcomp: Component
        for cxcomp in sbom.components:
            version = cxcomp.version or ""
            data = self.get_nuget_metadata(cxcomp.name, version)
            if not data:
                continue

            if data.get("author", ""):
                cxcomp.authors.add(data["author"])
                LOG.debug("  got author")

            if data.get("license", ""):
                license_factory = LicenseFactory()
                cxcomp.licenses.add(license_factory.make_with_name(data["license"]))
                LOG.debug("  got license")

            if data.get("sourcecode", ""):
                ext_ref = ExternalReference(
                    type=ExternalReferenceType.DISTRIBUTION,
                    comment=CaPyCliBom.SOURCE_URL_COMMENT,
                    url=XsUri(data["sourcecode"]))
                cxcomp.external_references.add(ext_ref)

            if data.get("repository", ""):
                ext_ref = ExternalReference(
                    type=ExternalReferenceType.DISTRIBUTION,
                    comment="repository",
                    url=XsUri(data["repository"]))
                cxcomp.external_references.add(ext_ref)

                sourcecode = data["repository"] + "/archive/refs/tags/v" + cxcomp.version + ".zip"
                ext_ref = ExternalReference(
                    type=ExternalReferenceType.DISTRIBUTION,
                    comment=CaPyCliBom.SOURCE_URL_COMMENT,
                    url=XsUri(sourcecode))
                cxcomp.external_references.add(ext_ref)
                LOG.debug("  got source file url")

            if data.get("project", ""):
                ext_ref = ExternalReference(
                    type=ExternalReferenceType.WEBSITE,
                    url=XsUri(data["project"]))
                cxcomp.external_references.add(ext_ref)
                LOG.debug("  got homepage")
            elif data.get("homepage", ""):
                ext_ref = ExternalReference(
                    type=ExternalReferenceType.WEBSITE,
                    url=XsUri(data["homepage"]))
                cxcomp.external_references.add(ext_ref)
                LOG.debug("  got homepage")

            if data.get("copyright", ""):
                cxcomp.copyright = data["copyright"]
                LOG.debug("  got copyright")

            if data.get("description", ""):
                cxcomp.description = data["description"]
                LOG.debug("  got description")

    def check_meta_data(self, sbom: Bom) -> bool:
        """
        Check whether all required meta-data is available.

        Args:
            sbom (Bom): the SBOM

        Returns:
            bool: True if all required meta-data is available; otherwise False.
        """

        if self.verbose:
            print_text("\nChecking meta-data:")

        result = True
        cxcomp: Component
        for cxcomp in sbom.components:
            if self.verbose:
                print_text(f"  {cxcomp.name}, {cxcomp.version}")

            if not cxcomp.purl:
                result = False
                if self.verbose:
                    print_yellow("    package-url missing")

            homepage = CycloneDxSupport.get_ext_ref_website(cxcomp)
            if not homepage:
                result = False
                if self.verbose:
                    print_yellow("    Homepage missing")

            if not cxcomp.licenses:
                if self.verbose:
                    LOG.debug("    License missing")
            elif len(cxcomp.licenses) == 0:
                if self.verbose:
                    LOG.debug("    License missing")

            src_url = CycloneDxSupport.get_ext_ref_source_url(cxcomp)
            if not src_url:
                result = False
                if self.verbose:
                    print_yellow("    Source code URL missing")

        return result

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
            " - Determine Nuget components/dependencies\n")

        if args.help:
            print("Usage: capycli getdependencies nuget -i <csproj file> -o <bom.json>")
            print("")
            print("    Options:")
            print("     -i INPUTFILE      csproj or sln input file to read from")
            print("     -o OUTPUTFILE     bom file to write to")
            print("     -v, --verbose         verbose output")
            print("     --search-meta-data    search for package meta data")
            return

        if not args.inputfile:
            print_red("No input file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not os.path.isfile(args.inputfile):
            print_red("Input file not found!")
            sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

        if not args.outputfile:
            print_red("No output SBOM file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        self.verbose = args.verbose

        print_text("Reading input file " + args.inputfile)
        if args.inputfile.endswith(".sln"):
            sbom = self.convert_solution_file(args.inputfile)
        else:  # assume ".csproj"
            sbom = self.convert_project_file(args.inputfile)

        if args.search_meta_data:
            self.search_meta_data(sbom)

        self.check_meta_data(sbom)

        if self.verbose:
            print()

        print_text("\nWriting new SBOM to " + args.outputfile)
        try:
            SbomWriter.write_to_json(sbom, args.outputfile, True)
        except Exception as ex:
            print_red("Error writing updated SBOM file: " + repr(ex))
            sys.exit(ResultCode.RESULT_ERROR_WRITING_BOM)
        print_text(" " + self.get_comp_count_text(sbom) + " items written to file.")

        print()
