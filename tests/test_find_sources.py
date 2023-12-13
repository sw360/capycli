# -------------------------------------------------------------------------------
# Copyright (c) 2022-2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, manuel.schaffer@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

import capycli.common.json_support
import capycli.common.script_base
from capycli.bom.findsources import FindSources
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestFindSources(TestBase):
    INPUT_BAD = "plaintext.txt"
    INPUTFILE = "sbom_for_find_sources.json"
    OUTPUTFILE = "output.json"

    def test_show_help(self) -> None:
        sut = FindSources()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("findsources")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli bom findsources [-h]" in out)

    def test_no_input_file_specified(self) -> None:
        try:
            sut = FindSources()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("findsources")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_file_not_found(self) -> None:
        try:
            sut = FindSources()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("python")
            args.inputfile = "findsources"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_file_invalid(self) -> None:
        try:
            sut = FindSources()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("python")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUT_BAD)

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, ex.code)

    def test_find_sources(self) -> None:
        sut = FindSources()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("python")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)
        args.outputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.OUTPUTFILE)
        args.debug = True
        args.verbose = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE in out)
        self.assertTrue(self.OUTPUTFILE in out)
        self.assertTrue("Using anonymous GitHub access" in out)
        self.assertTrue("8 components read from SBOM" in out)
        self.assertTrue("1 source files were already available" in out)
        self.assertTrue("5 source file URLs were found" in out)

        sbom = CaPyCliBom.read_sbom(args.outputfile)
        self.assertIsNotNone(sbom)
        self.assertEqual(8, len(sbom.components))
        self.assertEqual("colorama", sbom.components[0].name)
        self.assertEqual("0.4.6", sbom.components[0].version)
        self.assertEqual(
            "https://github.com/tartley/colorama/archive/refs/tags/0.4.6.zip",
            str(CycloneDxSupport.get_ext_ref_source_url(sbom.components[0])))

        self.assertEqual("into-stream", sbom.components[1].name)
        self.assertEqual("6.0.0", sbom.components[1].version)
        self.assertEqual(
            "https://github.com/sindresorhus/into-stream/archive/refs/tags/v6.0.0.zip",
            str(CycloneDxSupport.get_ext_ref_source_url(sbom.components[1])))

        self.assertEqual("python", sbom.components[2].name)
        self.assertEqual("3.8", sbom.components[2].version)

        self.assertEqual("something", sbom.components[3].name)
        self.assertEqual("0.38.4", sbom.components[3].version)

        self.assertEqual("tiny-lru", sbom.components[4].name)
        self.assertEqual("11.0.1", sbom.components[4].version)
        self.assertEqual(
            "https://github.com/avoidwork/tiny-lru/archive/refs/tags/11.0.1.zip",
            str(CycloneDxSupport.get_ext_ref_source_url(sbom.components[4])))

        self.assertEqual("tomli", sbom.components[5].name)
        self.assertEqual("2.0.1", sbom.components[5].version)
        self.assertEqual(
            "https://github.com/hukkin/tomli/archive/refs/tags/2.0.1.zip",
            str(CycloneDxSupport.get_ext_ref_source_url(sbom.components[5])))

        self.assertEqual("wheel", sbom.components[6].name)
        self.assertEqual("0.38.4", sbom.components[6].version)
        self.assertEqual(
            "https://github.com/pypa/wheel/archive/refs/tags/0.38.4.zip",
            str(CycloneDxSupport.get_ext_ref_source_url(sbom.components[6])))

        self.assertEqual("yamljs", sbom.components[7].name)
        self.assertEqual("0.3.0", sbom.components[7].version)
        self.assertEqual(
            "https://github.com/jeremyfa/yaml.js/archive/refs/tags/v0.3.0.zip",
            str(CycloneDxSupport.get_ext_ref_source_url(sbom.components[7])))

        self.delete_file(args.outputfile)

    def test_get_repo_name(self):
        # simple
        repo = "https://github.com/JamesNK/Newtonsoft.Json"
        actual = capycli.bom.findsources.FindSources.get_repo_name(repo)

        self.assertEqual("JamesNK/Newtonsoft.Json", actual)

        # trailing .git
        repo = "https://github.com/restsharp/RestSharp.git"
        actual = capycli.bom.findsources.FindSources.get_repo_name(repo)

        self.assertEqual("restsharp/RestSharp", actual)

        # trailing #readme
        repo = "https://github.com/restsharp/RestSharp#readme"
        actual = capycli.bom.findsources.FindSources.get_repo_name(repo)

        self.assertEqual("restsharp/RestSharp", actual)

        # prefix git
        repo = "git://github.com/restsharp/RestSharp#readme"
        actual = capycli.bom.findsources.FindSources.get_repo_name(repo)

        self.assertEqual("restsharp/RestSharp", actual)

        # prefix git+https
        repo = "git+https://github.com/restsharp/RestSharp#readme"
        actual = capycli.bom.findsources.FindSources.get_repo_name(repo)

        self.assertEqual("restsharp/RestSharp", actual)

    def test_normalize_version(self):
        sut = FindSources()
        param_list = [('We don\'t know', '0.0.0'), ('pre_pr_153572', '0.0.0'), ('1_27_1_1', '1.27.1.1'),
                      ('2.6.3', '2.6.3'), ('2.0.0.RELEASE', '2.0.0'), ('1.29', '1.29.0'), ('1.06', '1.6.0'),
                      ('1_27_1', '1.27.1'), ('v1.1.1', '1.1.1'), ('v1.1.1.RELEASE', '1.1.1'), ('0.4.M3', '0.4.0'),
                      ('V1_9_9_1', '1.9.9.1')]
        for version, expected in param_list:
            with self.subTest("Convert input version to semver", version=version, expected=expected):
                actual = sut.to_semver_string(version)
                self.assertEqual(actual, expected)
                self.assertTrue(actual == expected, 'version %s is %s' % (actual, expected))
