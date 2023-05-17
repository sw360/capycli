# -------------------------------------------------------------------------------
# Copyright (c) 2022-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, manuel.schaffer@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
from unittest.mock import MagicMock, patch

import responses

from capycli.common.capycli_bom_support import CycloneDxSupport
from capycli.dependencies.maven_list import GetJavaMavenTreeDependencies
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestMavenTree(TestBase):
    OUTPUTFILE = "output.json"
    INPUTFILE = "maven-dependency-list.txt"
    INPUTFILE_RAW = "maven-raw.txt"

    def test_show_help(self) -> None:
        sut = GetJavaMavenTreeDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("MavenPom")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("CaPyCli getdependencies mavenlist" in out)

    def test_no_output_file(self) -> None:
        try:
            sut = GetJavaMavenTreeDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("MavenPom")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_input_file_not_found(self) -> None:
        try:
            sut = GetJavaMavenTreeDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("MavenPom")
            args.outputfile = self.OUTPUTFILE
            args.inputfile = "DOES_NOT_EXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_maven_list_source_regex(self):
        inputfile_raw = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_RAW)
        urls = GetJavaMavenTreeDependencies()\
            .extract_urls(inputfile_raw, GetJavaMavenTreeDependencies.SOURCES_REGEX)

        self.assertEqual(2, len(urls), "unexpected amount of detected source urls")

    def test_maven_list_binary_regex(self):
        inputfile_raw = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_RAW)
        urls = GetJavaMavenTreeDependencies() \
            .extract_urls(inputfile_raw, GetJavaMavenTreeDependencies.BINARIES_REGEX)

        self.assertEqual(1, len(urls), "unexpected amount of detected source urls")

    @responses.activate
    @patch("subprocess.run")
    def test_create_full_dependency_list_from_maven_list_file(self, mock_subprocess_run):
        file1 = os.path.join(os.path.dirname(__file__), "fixtures", "spring-boot-starter-json-2.4.3.pom")
        with open(file1, 'r') as file:
            content = file.read()
        responses.add(responses.GET, ("https://devops.bt.siemens.com/artifactory/maven2-all/org/"
                                      "springframework/boot/spring-boot-starter-json/2.4.3/spring"
                                      "-boot-starter-json-2.4.3.pom"), body=content)

        file2 = os.path.join(os.path.dirname(__file__), "fixtures", "spring-boot-tags.txt")
        with open(file2, 'rb') as file:
            spring_boot_tags = file.read()
        mock_subprocess_run.return_value = MagicMock(stdout=spring_boot_tags)

        inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)
        inputfile_raw = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_RAW)
        bom = GetJavaMavenTreeDependencies() \
            .create_full_dependency_list_from_maven_list_file(inputfile, inputfile_raw, "./")
        self.assertEqual(230, len(bom.components), "unexpected amount of detected bom items")

        filled_source_url = [b for b in bom.components if CycloneDxSupport.get_ext_ref_source_url(b) != ""]
        self.assertEqual(2, len(filled_source_url))

        filled_binary_url = [b for b in bom.components if CycloneDxSupport.get_ext_ref_binary_url(b) != ""]
        self.assertEqual(1, len(filled_binary_url))

        bom_spring_boot_starter_json = next(
            (filter(lambda x: (x.name == "spring-boot-starter-json"), bom.components)), None)
        self.assertEqual(CycloneDxSupport.get_ext_ref_source_url(bom_spring_boot_starter_json),
                         ("https://github.com/spring-projects/spring-boot/archive/refs/tags/v2.4.3.zip"))

    def test_create_full_dependency_list_from_maven_list_file2(self) -> None:
        sut = GetJavaMavenTreeDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("MavenPom")
        args.outputfile = self.OUTPUTFILE
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)
        args.raw_input = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_RAW)
        args.source = "./"
        args.verbose = True
        args.debug = True

        self.delete_file(self.OUTPUTFILE)
        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Read mvn dependency list file..." in out)
        self.assertTrue("Writing new SBOM to" in out)
        self.assertTrue(self.OUTPUTFILE in out)
        self.assertTrue("230 components items written to file" in out)

        self.assertTrue(os.path.isfile(self.OUTPUTFILE))

        self.delete_file(self.OUTPUTFILE)


if __name__ == '__main__':
    APP = TestMavenTree()
    APP.test_create_full_dependency_list_from_maven_list_file()
