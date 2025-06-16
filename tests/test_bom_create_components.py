# -------------------------------------------------------------------------------
# Copyright (c) 2021-2025 Siemens
# All Rights Reserved.
# Author: gernot.hillier@siemens.com, thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

"""unit tests for bom/create_components.py in default mode.
Most functionality is tested in test_bom_create_releases.py"""

import os

import responses
from cyclonedx.model import ExternalReferenceType
from cyclonedx.model.component import Component
from packageurl import PackageURL

import capycli.bom.create_components
from capycli.bom.create_components import BomCreateComponents
from capycli.common.capycli_bom_support import CycloneDxSupport
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase
from tests.test_base_vcr import SW360_BASE_URL


class CapycliTestBomCreateComponents(TestBase):
    INPUTFILE1 = "sbom_for_create_components1.json"
    INPUTFILE_INVALID = "plaintext.txt"
    INPUTFILE_EMPTY = "sbom_no_components.json"
    OUTPUTFILE = "output.json"

    @responses.activate
    def setUp(self) -> None:
        self.app = capycli.bom.create_components.BomCreateComponents(onlyCreateReleases=False)
        responses.add(responses.GET, SW360_BASE_URL, json={"status": "ok"})
        self.app.login("sometoken", "https://my.server.com")

    @responses.activate
    def test_create_component(self) -> None:
        """Component and Release don't exist. So create them.
        """
        responses.add(responses.GET, SW360_BASE_URL + 'components?name=activemodel', json={
            "_embedded": {"sw360:components": []}})

        component_data = {
            "name": "activemodel", "componentType": "OSS",
            "description": "something", "categories": ["devel"],
            "homepage": "http://test.org", "languages": ["Ruby"],
            "externalIds": {"package-url": "pkg:gem/activemodel"},
            "additionalData": {"createdWith": capycli.get_app_signature()}}

        responses.add(
            responses.POST,
            SW360_BASE_URL + 'components',
            # verify data we send in POST
            match=[responses.matchers.json_params_matcher(component_data)],
            # server answer with created release data
            json={**component_data,
                  "_links": {"self": {
                      "href": SW360_BASE_URL + "components/06a6e5"}}})

        release_data = {"name": "activemodel", "version": "5.2.4.3",
                        "mainlineState": "OPEN", "languages": ["Ruby"],
                        "sourceCodeDownloadurl": "http://test.org",
                        "externalIds": {"package-url": "pkg:gem/activemodel@5.2.4.3"},
                        "additionalData": {"createdWith": capycli.get_app_signature()}}
        responses.add(
            responses.POST,
            SW360_BASE_URL + 'releases',
            # verify data we send in POST
            match=[responses.matchers.json_params_matcher({
                **release_data, "componentId": "06a6e5",
            })],
            # server answer with created release data
            json={**release_data,
                  "_links": {"self": {
                      "href": SW360_BASE_URL + "releases/06a6e7"}}})

        item = Component(
            name="activemodel",
            version="5.2.4.3",
            description="something",
            purl=PackageURL.from_string("pkg:gem/activemodel@5.2.4.3")
        )
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_LANGUAGE, "Ruby")
        CycloneDxSupport.update_or_set_property(item, CycloneDxSupport.CDX_PROP_CATEGORIES, "devel")
        CycloneDxSupport.update_or_set_ext_ref(item, ExternalReferenceType.WEBSITE, "", "http://test.org")

        self.app.create_component_and_release(item)
        assert len(responses.calls) == 3

    @responses.activate
    def test_create_comp_release_no_component_id_required(self) -> None:
        """Release doesn't exist. So create it.
        """
        responses.add(responses.GET, SW360_BASE_URL + 'components?name=activemodel', json={
            "_embedded": {"sw360:components": [{
                "name": "activemodel",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "components/06a6e5"}}}]}})
        responses.add(responses.GET, SW360_BASE_URL + 'components/06a6e5', json={
            "name": "activemodel",
            "_links": {"self": {
                    "href": SW360_BASE_URL + "components/06a6e5"}},
            "_embedded": {"sw360:releases": [{
                "name": "activemodel",
                "version": "5.2.1",
                "_links": {"self": {
                    "href": SW360_BASE_URL + "releases/06a6e6"}}}]}})
        responses.add(
            responses.POST,
            SW360_BASE_URL + 'releases',
            # verify data we send in POST
            match=[responses.matchers.json_params_matcher({
                "name": "activemodel",
                "componentId": "06a6e5",
                "version": "5.2.4.3",
                "mainlineState": "OPEN",
                "additionalData": {"createdWith": capycli.get_app_signature()}})],
            # server answer with created release data
            json={"version": "5.2.4.3",
                  "_links": {"self": {
                      "href": SW360_BASE_URL + "releases/06a6e7"}}})

        item = Component(
            name="activemodel",
            version="5.2.4.3"
        )
        self.app.create_component_and_release(item)
        id = CycloneDxSupport.get_property_value(item, CycloneDxSupport.CDX_PROP_SW360ID)
        assert id == "06a6e7"

    def test_show_help_components(self) -> None:
        sut = BomCreateComponents()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("createcomponents")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: CaPyCLI bom createcomponents" in out)

    def test_no_file_specified(self) -> None:
        try:
            sut = BomCreateComponents()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("createreleases")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_file_not_found(self) -> None:
        try:
            sut = BomCreateComponents()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("bom")
            args.command.append("createreleases")
            args.inputfile = "DOESNOTEXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    @responses.activate
    def test_no_login(self) -> None:
        sut = BomCreateComponents()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("createcomponents")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE1)
        args.sw360_url = "https://my.server.com"
        args.debug = True
        args.verbose = True

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_AUTH_ERROR, ex.code)

    @responses.activate
    def test_inputfile_invalid(self) -> None:
        sut = BomCreateComponents()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("createcomponents")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_INVALID)
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True

        self.add_login_response()

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, ex.code)

    @responses.activate
    def test_create_components_no_components(self) -> None:
        sut = BomCreateComponents()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("createcomponents")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_EMPTY)
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True

        self.add_login_response()

        out = TestBase.capture_stdout(sut.run, args)
        # TestBase.dump_textfile(out, "DUMP.TXT")
        self.assertTrue(self.INPUTFILE_EMPTY in out)
        self.assertTrue("0 components read from SBOM" in out)
        self.assertTrue("Creating items..." in out)

    @responses.activate
    def xtest_create_components(self) -> None:
        sut = BomCreateComponents()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("bom")
        args.command.append("createcomponents")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE_INVALID)
        args.sw360_token = TestBase.MYTOKEN
        args.sw360_url = TestBase.MYURL
        args.debug = True
        args.verbose = True

        self.add_login_response()

        try:
            sut.run(args)
            self.assertTrue(False, "Failed to report login failure")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_ERROR_READING_BOM, ex.code)


if __name__ == "__main__":
    APP = CapycliTestBomCreateComponents()
    APP.setUp()
    APP.test_create_component()
