# -------------------------------------------------------------------------------
# Copyright (c) 2020-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, manuel.schaffer@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import Any, List, Optional, Tuple

import requests
from cyclonedx.model import ExternalReference, ExternalReferenceType, Property, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from packageurl import PackageURL

import capycli.common.dependencies_base
import capycli.common.json_support
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport, SbomCreator, SbomWriter
from capycli.common.print import print_red, print_text, print_yellow
from capycli.main.result_codes import ResultCode

LOG = capycli.get_logger(__name__)


class GetJavaMavenTreeDependencies(capycli.common.dependencies_base.DependenciesBase):
    SOURCES_REGEX = r'.*Downloading.+(https://?[-a-zA-Z0-9@:%._+~#=/]{1,256}-(source|sources).jar).*'
    BINARIES_REGEX = r'.*Downloaded.+(https://?[-a-zA-Z0-9@:%._+~#=/]{1,256}.jar).*'

    def add_urls(
            self, cx_comp: Component,
            parsed_sources: List[str], parsed_binaries: List[str],
            source_files: List[str], binary_files: List[str], files_directory: str) -> None:
        """
        Adds URLs to corresponding bom item. This is done by checking if a dependency
        with the corresponding naming exists inside the list of parsed URLs and also
        inside the download folder

        :param bomitem: a single bom item
        :param parsed_sources: a list of sources URLs
        :param parsed_binaries: a list of binaries URLs
        :param source_files: a list of source files from the sources download folder
        :param binary_files: a list of binary files from the binaries download folder
        """
        src_url = None
        version = ""
        if cx_comp.version:
            version = cx_comp.version
        for source in parsed_sources:
            if cx_comp.name + "-" + version + "-source.jar" in source \
                    or cx_comp.name + "-" + version + "-sources.jar" in source:
                src_url = source
                for source_file in source_files:
                    if cx_comp.name + "-" + version in source_file:
                        src_url = source
                        break
                else:
                    continue
                break

        if src_url:
            ext_ref = ExternalReference(
                reference_type=ExternalReferenceType.DISTRIBUTION,
                comment=CaPyCliBom.SOURCE_URL_COMMENT,
                url=XsUri(src_url))
            cx_comp.external_references.add(ext_ref)

        bin_url = None
        for binary in parsed_binaries:
            if cx_comp.name + "-" + version + ".jar" in binary:
                bin_url = binary
                for binary_file in binary_files:
                    if cx_comp.name + "-" + version in binary_file:
                        bin_url = os.path.join(files_directory, binary_file)
                        break
                else:
                    continue
                break

        if bin_url:
            ext_ref = ExternalReference(
                reference_type=ExternalReferenceType.DISTRIBUTION,
                comment=CaPyCliBom.BINARY_URL_COMMENT,
                url=XsUri(bin_url))
            cx_comp.external_references.add(ext_ref)

    def extract_urls(self, download_output_file: str, regex: str) -> List[str]:
        """
        Parses the output of mvn command using provided regex
        :param download_output_file: the mvn command output to be parsed
        :param regex: the regex string that will be used for parsing
        """
        parsed_urls: List[str] = []

        lines = open(download_output_file).read().split("\n")
        for line in lines:
            parts = re.findall(regex, line)
            if parts and len(parts) > 0:
                url = parts[0]
                # if isinstance(url, Tuple):
                if type(url) is Tuple:
                    url = url[0]
                if url not in parsed_urls:
                    parsed_urls.append(url)

        return parsed_urls

    def find_package_info(self, binary_file_url: str) -> Optional[ET.Element]:
        """
        Downloads a pom file and returns the parsed content
        :param  binary_file_url: a binary file url
        """
        url = re.sub(r"\.jar$", ".pom", binary_file_url)

        try:
            response = requests.get(
                url, headers={"Accept": "text/xml"}
            )
            if response.ok:
                res = ET.fromstring(response.content)

                return res
        except Exception as ex:
            print_red("  Error retrieving component meta data: " + repr(ex))

        return None

    def try_find_metadata(self, cx_comp: Component) -> None:
        """
        Extract information from pom file and add it to bom
        :param bomitem: item of a bom which represents a single package
        """
        version = ""
        if cx_comp.version:
            version = cx_comp.version

        bin_file_url = CycloneDxSupport.get_ext_ref_binary_url(cx_comp)
        if bin_file_url:
            info = self.find_package_info(str(bin_file_url))
            if not info:
                print_yellow(
                    "  No info found for component " +
                    cx_comp.name +
                    ", " +
                    version)
                return

            namespaces = {"pom": "http://maven.apache.org/POM/4.0.0"}
            project_url = info.find("./pom:url", namespaces)
            if project_url is not None and project_url.text:
                CycloneDxSupport.update_or_set_ext_ref(
                    cx_comp, ExternalReferenceType.WEBSITE, "", project_url.text)
            scm_url = info.find("./pom:scm/pom:url", namespaces)
            if scm_url is not None:
                url = scm_url.text
                if url:
                    CycloneDxSupport.update_or_set_ext_ref(
                        cx_comp, ExternalReferenceType.VCS, "", url)
                    if "github.com" in url:
                        if not str(url).startswith("http"):
                            url = "https://" + url
                        # bomitem["SourceUrl"] = url
                        src_file_url = self.find_source_file(url, cx_comp.name, version)
                        CycloneDxSupport.update_or_set_ext_ref(
                            cx_comp, ExternalReferenceType.DISTRIBUTION,
                            CaPyCliBom.SOURCE_URL_COMMENT, src_file_url)

                        print(src_file_url)
            description = info.find("./pom:description", namespaces)
            if description is not None:
                cx_comp.description = description.text

    """
    Determine Java components/dependencies for a given project.

    Run the Maven Dependency List command, extract the dependencies
    and create a bill of material JSON file.
    """
    def create_full_dependency_list_from_maven_command(self) -> Bom:
        """
        Create a full list of dependencies - including transitive
        dependencies of the current project using the
        Maven Dependency Lis command:
          mvn dependency:list

        :return a list of the local Python packages
        :rtype list of package item dictionaries, as returned by pip
        """
        args = ["mvn dependency:list -B"]
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)

        sbom = SbomCreator.create([], addlicense=True, addprofile=True, addtools=True)
        if not proc.stdout:
            return sbom

        raw_bin_data = proc.stdout.read()
        raw_data = raw_bin_data.decode("utf-8")
        lines = raw_data.split("\n")
        p = re.compile(r"\[INFO\]\s*(\S*):compile(?!:)\s*", re.IGNORECASE | re.MULTILINE)
        for line in lines:
            x = p.split(line)
            if len(x) == 3:
                bomitem = self.create_bom_item(x)
                if not sbom.components.__contains__(bomitem):
                    sbom.components.add(bomitem)

        return sbom

    def create_full_dependency_list_from_maven_list_file(self, maven_list_file: str, raw_file: str, source: str) -> Bom:
        """
        Create a full list of dependencies - including transitive
        dependencies of the current project using the
        export of Maven Dependency Lis command:
          mvn dependency:list

        :return a list of the local Python packages
        :rtype list of package item dictionaries, as retuned by pip
        """
        if raw_file:
            parsed_sources = self.extract_urls(raw_file, self.SOURCES_REGEX)
            parsed_binaries = self.extract_urls(raw_file, self.BINARIES_REGEX)

            if not parsed_sources or len(parsed_sources) == 0:
                print_text("Parsed sources URL list has no items")

            if not parsed_binaries or len(parsed_binaries) == 0:
                print_text("Parsed binaries URL list has no items")

            if source:
                source_files = os.listdir(os.path.join(os.getcwd(), source))
                binary_files = os.listdir(os.path.join(os.getcwd(), source))
            else:
                source_files = []
                binary_files = []

        with open(maven_list_file) as file:
            lines = file.readlines()
            lines = [line.rstrip() for line in lines]

        sbom = SbomCreator.create([], addlicense=True, addprofile=True, addtools=True)
        list_p = [
            re.compile(r"\s*(\S*):compile(?!:)\s*", re.IGNORECASE | re.MULTILINE),
            re.compile(r"\s*(\S*):runtime(?!:)\s*", re.IGNORECASE | re.MULTILINE),
            re.compile(r"\s*(\S*):test(?!:)\s*", re.IGNORECASE | re.MULTILINE),
            re.compile(r"\s*(\S*):provided(?!:)\s*", re.IGNORECASE | re.MULTILINE),
            re.compile(r"\s*(\S*):system(?!:)\s*", re.IGNORECASE | re.MULTILINE)
        ]
        for line in lines:
            for p in list_p:
                x = p.split(line)
                if len(x) == 3:
                    bomitem = self.create_bom_item(x)
                    if raw_file:
                        self.add_urls(bomitem,
                                      parsed_sources,
                                      parsed_binaries,
                                      source_files,
                                      binary_files,
                                      source)

                        self.try_find_metadata(bomitem)

                    if not sbom.components.__contains__(bomitem):
                        sbom.components.add(bomitem)

        return sbom

    def create_bom_item(self, x: List[str]) -> Component:
        """
        Create a CycloneDX BOM item.
        """
        dependency = x[1]
        # print("dependency", dependency)
        parts = dependency.split(":")
        # 0 = groupId
        # 1 = artifactId
        # 2 = jar
        # 3 = version
        if len(parts) < 4:
            parts = parts

        purl = PackageURL("maven", parts[0], parts[1], parts[3], "", "")
        cx_comp = Component(
            name=parts[1],
            version=parts[3],
            purl=purl,
            bom_ref=purl.to_string()
        )

        prop = Property(
            name=CycloneDxSupport.CDX_PROP_LANGUAGE,
            value="Java")
        cx_comp.properties.add(prop)

        return cx_comp

    def run(self, args: Any) -> None:
        """Main method()"""
        if args.debug:
            global LOG
            LOG = capycli.get_logger(__name__)

        print_text(
            "\n" + capycli.APP_NAME + ", " + capycli.get_app_version() +
            " - Determine Java components/dependencies\n")

        if args.help:
            print("Usage:")
            print("    CaPyCli getdependencies mavenlist -o <bom.json> [-source SOURCE] [-ri RAW_INPUT]")
            print("")
            print("Options:")
            print("    -source SOURCE    source folder or additional source file")
            print("    -i INPUT          input file - the output of 'mvn dependency:list' commands")
            print("    -ri RAW_INPUT     raw data input file to parse repository urls")
            print("    -o OUTPUTFILE     bom file to write to")
            return

        if not args.outputfile:
            print_red("No output SBOM file specified!")
            sys.exit(ResultCode.RESULT_COMMAND_ERROR)

        if not args.inputfile:
            print("Running mvn dependency:list command...")
            sbom = self.create_full_dependency_list_from_maven_command()
        else:
            if not os.path.isfile(args.inputfile):
                print_red("Input file not found!")
                sys.exit(ResultCode.RESULT_FILE_NOT_FOUND)

            print("Read mvn dependency list file...")
            sbom = self.create_full_dependency_list_from_maven_list_file(args.inputfile, args.raw_input, args.source)

        print_text("Writing new SBOM to " + args.outputfile)
        SbomWriter.write_to_json(sbom, args.outputfile, True)
        print_text(" " + self.get_comp_count_text(sbom) + " items written to file.")

        print()
