# -------------------------------------------------------------------------------
# Copyright (c) 2022-2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, manuel.schaffer@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os
import responses

import capycli.common.json_support
import capycli.common.script_base
from capycli.bom.findsources import FindSources
from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase
from unittest.mock import MagicMock, patch


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
        self.assertTrue("6 source file URLs were found" in out)

        sbom = CaPyCliBom.read_sbom(args.outputfile)
        self.assertIsNotNone(sbom)
        self.assertEqual(8, len(sbom.components))
        self.assertEqual("colorama", sbom.components[0].name)
        self.assertEqual("0.4.6", sbom.components[0].version)
        self.assertEqual(
            "https://github.com/tartley/colorama/archive/refs/tags/0.4.6.zip",
            CycloneDxSupport.get_ext_ref_source_url(sbom.components[0]))

        self.assertEqual("into-stream", sbom.components[1].name)
        self.assertEqual("6.0.0", sbom.components[1].version)
        self.assertEqual(
            "https://github.com/sindresorhus/into-stream/archive/refs/tags/v6.0.0.zip",
            CycloneDxSupport.get_ext_ref_source_url(sbom.components[1]))

        self.assertEqual("python", sbom.components[2].name)
        self.assertEqual("3.8", sbom.components[2].version)

        self.assertEqual("something", sbom.components[3].name)
        self.assertEqual("0.38.4", sbom.components[3].version)

        self.assertEqual("tiny-lru", sbom.components[4].name)
        self.assertEqual("11.0.1", sbom.components[4].version)
        self.assertEqual(
            "https://github.com/avoidwork/tiny-lru/archive/refs/tags/11.0.1.zip",
            CycloneDxSupport.get_ext_ref_source_url(sbom.components[4]))

        self.assertEqual("tomli", sbom.components[5].name)
        self.assertEqual("2.0.1", sbom.components[5].version)
        self.assertEqual(
            "https://github.com/hukkin/tomli/archive/refs/tags/2.0.1.zip",
            CycloneDxSupport.get_ext_ref_source_url(sbom.components[5]))

        self.assertEqual("wheel", sbom.components[6].name)
        self.assertEqual("0.38.4", sbom.components[6].version)
        self.assertEqual(
            "https://github.com/pypa/wheel/archive/refs/tags/0.38.4.zip",
            CycloneDxSupport.get_ext_ref_source_url(sbom.components[6]))

        self.assertEqual("yamljs", sbom.components[7].name)
        self.assertEqual("0.3.0", sbom.components[7].version)
        self.assertEqual(
            "https://github.com/jeremyfa/yaml.js/archive/refs/tags/v0.3.0.zip",
            CycloneDxSupport.get_ext_ref_source_url(sbom.components[7]))

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

    @responses.activate
    def test_get_release_component_id(self):
        # Mock the sw360 client
        mock_client = MagicMock()
        mock_client.get_release.return_value = {"_links": {"sw360:component": {"href": self.MYURL + 'components/123'}}}

        # Call the method and assert the result
        find_sources = FindSources()
        find_sources.client = mock_client
        component_id = find_sources.get_release_component_id("some_release_id")
        self.assertEqual(component_id, "123")

    @responses.activate
    def test_find_source_url_from_component(self):
        # Mock the client
        mock_client = MagicMock()
        mock_client.get_component.return_value = {"_embedded": {"sw360:releases": [{"_links": {"self": {"href": self.MYURL + 'releases/456'}}}]}}  # noqa
        mock_client.get_release.return_value = {"_links": {"sw360:component": {"href": self.MYURL + 'components/123'}}, "sourceCodeDownloadurl": "http://github.com/some/repo/0.0.0"}  # noqa

        # Call the method and assert the result
        find_sources = FindSources()
        find_sources.client = mock_client  # Inject the mocked client
        source_url = find_sources.find_source_url_from_component(component_id="some_component_id")
        self.assertEqual(source_url, "http://github.com/some/repo/0.0.0")

    @patch('requests.get')
    @patch('bs4.BeautifulSoup')
    def test_get_pkg_go_repo_url_success(self, mock_beautifulsoup, mock_requests_get):
        # Mocking successful response
        mock_requests_get.return_value.text = '<div class="UnitMeta-repo"><a href="https://github.com/example/repo/1.0.0">Repo Link</a></div>'  # noqa
        mock_beautifulsoup.return_value.find.return_value = MagicMock(get=lambda x: 'https://github.com/example/repo/1.0.0')  # noqa
        find_sources = FindSources()
        repo_url = find_sources.get_pkg_go_repo_url('example/package')
        self.assertEqual(repo_url, 'https://github.com/example/repo/1.0.0')

    @patch('requests.get', side_effect=Exception('Some error'))
    def test_get_pkg_go_repo_url_error(self, mock_requests_get):
        # Mocking an exception during the request
        find_sources = FindSources()
        repo_url = find_sources.get_pkg_go_repo_url('some/package')
        self.assertEqual(repo_url, 'https://pkg.go.dev/some/package')

    @patch('capycli.bom.findsources.FindSources.get_github_info')
    @patch('capycli.bom.findsources.FindSources.get_matching_tag')
    def test_find_golang_url_github(self, mock_get_github_info, mock_get_matching_tag):
        # Mocking a GitHub scenario
        mock_get_github_info.return_value = 'https://pkg.go.dev/github.com/opencontainers/runc'
        mock_get_matching_tag.return_value = 'https://github.com/opencontainers/runc/archive/refs/tags/v1.0.1.zip'
        find_sources = FindSources()
        component = MagicMock()
        component.name = 'github.com/opencontainers/runc'
        component.version = 'v1.0.1'
        source_url = find_sources.find_golang_url(component)

        self.assertEqual(source_url, 'https://pkg.go.dev/github.com/opencontainers/runc')

    def test_find_golang_url_non_github(self):
        # Mocking a non-GitHub scenario
        find_sources = FindSources()
        component = MagicMock()
        component.name = 'example/package'
        component.version = 'v1.0.0'
        source_url = find_sources.find_golang_url(component)

        self.assertEqual(source_url, '')

    def test_no_matching_tag(self):

        validTag = "3.2.0"
        invalidTag = "0.03"
        emptyString = ""
        githubUrl = "https://github.com/apache/kafka"
        zipball_url = "https://api.github.com/repos/apache/kafka/zipball/refs/tags/" + validTag
        sourceUrl = "https://github.com/apache/kafka/archive/refs/tags/" + validTag + ".zip"
        findResource = capycli.bom.findsources.FindSources()
        # test Empty tagInfo array
        tagInfo = []
        actual = capycli.bom.findsources.FindSources.get_matching_tag(findResource, tagInfo, validTag, githubUrl)
        self.assertEqual(actual, None)
        # test Empty tag string
        tagInfo = [{"name": emptyString, "zipball_url": zipball_url}]
        actual = capycli.bom.findsources.FindSources.get_matching_tag(findResource, tagInfo, validTag, githubUrl)
        self.assertEqual(actual, '')
        # test Empty url string
        tagInfo = [{"name": validTag, "zipball_url": emptyString}]
        actual = capycli.bom.findsources.FindSources.get_matching_tag(findResource, tagInfo, validTag, githubUrl)
        self.assertEqual(actual, None)
        # test non-matching tag
        tagInfo = [{"name": invalidTag, "zipball_url": zipball_url}]
        actual = capycli.bom.findsources.FindSources.get_matching_tag(findResource, tagInfo, validTag, githubUrl)
        self.assertEqual(actual, '')
        # test valid tag
        tagInfo = [{"name": validTag, "zipball_url": zipball_url}]
        actual = capycli.bom.findsources.FindSources.get_matching_tag(findResource, tagInfo, validTag, githubUrl)
        self.assertEqual(actual, sourceUrl)

    @patch("time.sleep")
    def test_get_source_url_success(self, mock_sleep):
        mock_client = MagicMock()
        mock_release_id = "123"
        mock_source_url = "https://example.com/source.zip"

        mock_client.get_release.return_value = {"sourceCodeDownloadurl": mock_source_url}

        findsources = FindSources()
        findsources.client = mock_client
        result = findsources.get_source_url_from_release(mock_release_id)
        self.assertEqual(result, mock_source_url)
        mock_sleep.assert_not_called()

    def test_get_source_url_no_source_url(self):
        mock_client = MagicMock()
        mock_release_id = "123"

        mock_client.get_release.return_value = {"sourceCodeDownloadurl": ""}
        findsources = FindSources()
        findsources.client = mock_client

        result = findsources.get_source_url_from_release(mock_release_id)
        self.assertIsNone(result)
        mock_client.get_release.assert_called_once_with(mock_release_id)

    def test_get_source_url_exception(self):
        mock_client = MagicMock()
        mock_release_id = "123"

        mock_client.get_release.side_effect = Exception("Unexpected error")
        findsources = FindSources()
        findsources.client = mock_client
        with self.assertRaises(Exception):
            findsources.get_source_url_from_release(mock_release_id)
        mock_client.get_release.assert_called_once_with(mock_release_id)
