# -------------------------------------------------------------------------------
# Copyright (c) 2026 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
from unittest.mock import mock_open, patch

import responses

from capycli.bom.component_check import ComponentCheck
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestComponentCheck(TestBase):
    INPUTFILE1 = "sbom_for_component_check.json"
    INPUTFILE2 = "component_checks_extra.json"
    INPUT_INVALID = "plaintext.txt"

    def test_show_help(self) -> None:
        sut = ComponentCheck()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("componentcheck")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCli bom componentcheck" in out)

    def test_no_input_file_specified(self) -> None:
        try:
            sut = ComponentCheck()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("componentcheck")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_file_not_found(self) -> None:
        try:
            sut = ComponentCheck()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("componentcheck")
            args.inputfile = "DOESNOTEXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_error_reading_bom(self) -> None:
        try:
            sut = ComponentCheck()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("componentcheck")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUT_INVALID)

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, ex.code)

    def test_real_bom1(self) -> None:
        sut = ComponentCheck()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("componentcheck")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.verbose = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE1 in out)
        self.assertTrue("Reading component checklist..." in out)
        self.assertTrue("Got component checklist." in out)
        self.assertTrue("0 components will be ignored." in out)
        self.assertTrue("7 components read from SBOM" in out)
        self.assertTrue("pandas 5.0 is known as a Python component that has additional binary dependencies" in out)
        self.assertTrue("pytest 7.4.3 seems to be a development dependency" in out)

    def test_real_bom2(self) -> None:
        sut = ComponentCheck()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("componentcheck")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.local_checklist_list = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE2)
        args.debug = True
        args.search_meta_data = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue(self.INPUTFILE1 in out)
        self.assertTrue("Reading component checklist..." in out)
        self.assertTrue("Got component checklist." in out)
        self.assertTrue("1 components will be ignored." in out)
        self.assertTrue("gulp 123 seems to be a development dependency" in out)
        self.assertTrue("junit 1.2.3 seems to be a development dependency" in out)
        self.assertTrue("junit 1.2.4 seems to be a development dependency" in out)
        self.assertFalse("pytest 7.4.3 seems to be a development dependency" in out)

    @responses.activate
    def test_read_granularity_list_local(self) -> None:
        check_components = ComponentCheck()
        read_data = '''
{
  "dev_dependencies": {
    "maven": [
      { "namespace": "org.eclipse.jdt", "name": "zjunitz" }
    ]
  },
  "python_binary_components": [],
  "files_to_ignore": []
}
        '''
        # with patch('builtins.open', new_callable=mock_open(read_data=read_data)) as mock_file:
        with patch("builtins.open", mock_open(read_data=read_data)) as mock_file:

            check_components.read_component_check_list(local_check_list_file="component_checks.json")
            mock_file.assert_called_once_with("component_checks.json", "r", encoding="utf-8")
            self.assertEqual(check_components.component_check_list["dev_dependencies"]["maven"][0]["name"], "zjunitz")

        self.delete_file("component_checks.json")

    @responses.activate
    def test_read_granularity_list_local_file_not_found(self) -> None:
        sut = ComponentCheck()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("componentcheck")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.local_checklist_list = "DOESNOTEXIST"

        sut.run(args)
        out = self.capture_stdout(sut.run, args)
        self.assertTrue("File not found: [Errno 2] No such file or directory: 'DOESNOTEXIST'" in out)

    @responses.activate
    def test_read_granularity_list_local_invalid_file(self) -> None:
        sut = ComponentCheck()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("componentcheck")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.local_checklist_list = os.path.join(os.path.dirname(__file__), "fixtures", "maven-raw.txt")

        sut.run(args)
        out = self.capture_stdout(sut.run, args)
        self.assertTrue("An unexpected error occurred: " in out)

    @responses.activate
    def test_read_granularity_list_download(self) -> None:
        check_components = ComponentCheck()
        body_data = '''
{
  "dev_dependencies": {
    "maven": [
      { "namespace": "org.eclipse.jdt", "name": "xjunitx" }
    ]
  },
  "python_binary_components": [],
  "files_to_ignore": []
}
        '''
        responses.add(responses.GET, 'http://example.com/component_checks_extra.json', body=body_data)

        check_components.read_component_check_list(download_url='http://example.com/component_checks_extra.json')
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, 'http://example.com/component_checks_extra.json')
        self.assertEqual(check_components.component_check_list["dev_dependencies"]["maven"][0]["name"], "xjunitx")

        self.delete_file("component_checks.json")

    @responses.activate
    def test_read_component_check_download_error(self) -> None:
        responses.add(responses.GET, 'http://wrongurl.com/granularity.csv', status=500)
        check_granularity = ComponentCheck()

        check_granularity.read_component_check_list(download_url='http://wrongurl.com/granularity.csv')

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, 'http://wrongurl.com/granularity.csv')

        # check default fallback
        self.assertEqual(check_granularity.component_check_list["dev_dependencies"]["maven"][0]["name"], "junit")


if __name__ == '__main__':
    APP = TestComponentCheck()
    APP.test_real_bom2()
