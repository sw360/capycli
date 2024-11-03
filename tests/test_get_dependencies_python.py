# -------------------------------------------------------------------------------
# Copyright (c) 2023-2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import os

import responses

from capycli.common.capycli_bom_support import CaPyCliBom, CycloneDxSupport
from capycli.dependencies.python import GetPythonDependencies, InputFileType
from capycli.main.result_codes import ResultCode
from tests.test_base import AppArguments, TestBase


class TestGetDependenciesPython(TestBase):
    INPUTFILE = "poetry.lock"
    INPUTFILE2 = "sbom_with_sw360.json"
    OUTPUTFILE1 = "test_requirements.txt"
    OUTPUTFILE2 = "output.json"

    def test_show_help(self) -> None:
        sut = GetPythonDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("python")
        args.help = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("usage: capycli getdependencies python" in out)

    def test_no_input_file_specified(self) -> None:
        try:
            sut = GetPythonDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("python")

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_file_not_found(self) -> None:
        try:
            sut = GetPythonDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("python")
            args.inputfile = "DOESNOTEXIST"

            sut.run(args)
            self.assertTrue(False, "Failed to report missing file")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_FILE_NOT_FOUND, ex.code)

    def test_no_output_file_specified(self) -> None:
        try:
            sut = GetPythonDependencies()

            # create argparse command line argument object
            args = AppArguments()
            args.command = []
            args.command.append("getdependencies")
            args.command.append("python")
            args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE2)

            sut.run(args)
            self.assertTrue(False, "Failed to report missing argument")
        except SystemExit as ex:
            self.assertEqual(ResultCode.RESULT_COMMAND_ERROR, ex.code)

    def test_simple_bom(self) -> None:
        # create a test requirements file
        requirements = """
        certifi==2022.12.7 ; python_version >= "3.8" and python_version < "4"
        chardet==3.0.4 ; python_version >= "3.8" and python_version < "4.0"
        """
        with open(self.OUTPUTFILE1, "w") as outfile:
            outfile.write(requirements)

        sut = GetPythonDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("python")
        args.inputfile = self.OUTPUTFILE1
        args.outputfile = self.OUTPUTFILE2
        args.verbose = True
        args.debug = True

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("certifi, 2022.12.7" in out)
        self.assertTrue("chardet, 3.0.4" in out)

        self.delete_file(self.OUTPUTFILE1)
        self.delete_file(self.OUTPUTFILE2)

    @responses.activate
    def test_get_metadata(self) -> None:
        # create a test requirements file
        requirements = """
        chardet==3.0.4 ; python_version >= "3.8" and python_version < "4.0"
        """
        with open(self.OUTPUTFILE1, "w") as outfile:
            outfile.write(requirements)

        sut = GetPythonDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("python")
        args.inputfile = self.OUTPUTFILE1
        args.outputfile = self.OUTPUTFILE2
        args.verbose = True
        args.debug = True
        args.search_meta_data = True

        # for login
        responses.add(
            responses.GET,
            url="https://pypi.org/pypi/chardet/3.0.4/json",
            body="""
            {
                "info": {
                    "author": "Daniel Blanchard",
                    "description": "Chardet: The Universal Character Encoding Detector",
                    "home_page": "https://github.com/chardet/chardet",
                    "license": "LGPL",
                    "package_url": "https://pypi.org/project/chardet/",
                    "summary": "Universal encoding detector for Python 2 and 3"
                },
                "urls": [
                {
                    "comment_text": "",
                    "digests": {
                        "blake2b_256": "bca901ffebfb562e4274b6487b4bb1ddec7ca55ec7510b22e4c51f14098443b8",
                        "md5": "0004b00caff7bb543a1d0d0bd0185a03",
                        "sha256": "fc323ffcaeaed0e0a02bf4d117757b98aed530d9ed4531e3e15460124c106691"
                    },
                    "downloads": -1,
                    "filename": "chardet-3.0.4-py2.py3-none-any.whl",
                    "has_sig": false,
                    "md5_digest": "0004b00caff7bb543a1d0d0bd0185a03",
                    "packagetype": "bdist_wheel",
                    "python_version": "py2.py3",
                    "requires_python": null,
                    "size": 133356,
                    "upload_time": "2017-06-08T14:34:33",
                    "upload_time_iso_8601": "2017-06-08T14:34:33.552855Z",
                    "url": "https://files.pythonhosted.org/packages/bc/a9/01ffebf/chardet-3.0.4-py2.py3-none-any.whl",
                    "yanked": false,
                    "yanked_reason": null
                },
                {
                    "comment_text": "",
                    "digests": {
                        "blake2b_256": "fcbba5768c230f9ddb03acc9ef3f0d4a3cf93462473795d18e9535498c8f929d",
                        "md5": "7dd1ba7f9c77e32351b0a0cfacf4055c",
                        "sha256": "84ab92ed1c4d4f16916e05906b6b75a6c0fb5db821cc65e70cbd64a3e2a5eaae"
                    },
                    "downloads": -1,
                    "filename": "chardet-3.0.4.tar.gz",
                    "has_sig": false,
                    "md5_digest": "7dd1ba7f9c77e32351b0a0cfacf4055c",
                    "packagetype": "sdist",
                    "python_version": "source",
                    "requires_python": null,
                    "size": 1868453,
                    "upload_time": "2017-06-08T14:34:35",
                    "upload_time_iso_8601": "2017-06-08T14:34:35.581047Z",
                    "url": "https://files.pythonhosted.org/packages/fc/bb/a5768c230/chardet-3.0.4.tar.gz",
                    "yanked": false,
                    "yanked_reason": null
                }
            ]}
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        self.assertTrue("chardet, 3.0.4" in out)

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE2)
        self.assertIsNotNone(sbom)
        self.assertEqual(1, len(sbom.components))
        self.assertEqual("chardet", sbom.components[0].name)
        self.assertEqual("3.0.4", sbom.components[0].version)
        self.assertEqual("Universal encoding detector for Python 2 and 3", sbom.components[0].description)
        self.assertEqual(
            "https://github.com/chardet/chardet",
            str(CycloneDxSupport.get_ext_ref_website(sbom.components[0])))
        self.assertEqual(
            "https://pypi.org/project/chardet/",
            str(CycloneDxSupport.get_ext_ref_by_comment(sbom.components[0], "PyPi URL")))

        self.assertEqual(1, len(sbom.components[0].licenses))
        lic = sbom.components[0].licenses[0]
        self.assertEqual("LGPL", lic.name)

        self.assertEqual(
            "https://files.pythonhosted.org/packages/bc/a9/01ffebf/chardet-3.0.4-py2.py3-none-any.whl",
            str(CycloneDxSupport.get_ext_ref_binary_url(sbom.components[0])))
        self.assertEqual(
            "chardet-3.0.4-py2.py3-none-any.whl",
            str(CycloneDxSupport.get_ext_ref_binary_file(sbom.components[0])))

        self.assertEqual(
            "https://files.pythonhosted.org/packages/fc/bb/a5768c230/chardet-3.0.4.tar.gz",
            str(CycloneDxSupport.get_ext_ref_source_url(sbom.components[0])))
        self.assertEqual(
            "chardet-3.0.4.tar.gz",
            str(CycloneDxSupport.get_ext_ref_source_file(sbom.components[0])))

        self.delete_file(self.OUTPUTFILE1)
        self.delete_file(self.OUTPUTFILE2)

    @responses.activate
    def test_get_metadata_no_package_meta_info(self) -> None:
        # create a test requirements file
        requirements = """
        chardet==3.0.4 ; python_version >= "3.8" and python_version < "4.0"
        """
        with open(self.OUTPUTFILE1, "w") as outfile:
            outfile.write(requirements)

        sut = GetPythonDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("python")
        args.inputfile = self.OUTPUTFILE1
        args.outputfile = self.OUTPUTFILE2
        args.verbose = True
        args.debug = True
        args.search_meta_data = True

        # for login
        responses.add(
            responses.GET,
            url="https://pypi.org/pypi/chardet/3.0.4/json",
            body="""
            {
                "info": {
                    "author": "Daniel Blanchard",
                    "description": "Chardet: The Universal Character Encoding Detector",
                    "home_page": "https://github.com/chardet/chardet",
                    "license": "LGPL",
                    "package_url": "https://pypi.org/project/chardet/",
                    "summary": "Universal encoding detector for Python 2 and 3"
                }
            ]}
            """,
            status=500,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        # capycli.common.json_support.write_json_to_file(out, "DEBUG.TXT")
        self.assertTrue("chardet, 3.0.4" in out)
        self.assertTrue("WARNING: no meta data available for package" in out)

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE2)
        self.assertIsNotNone(sbom)
        self.assertEqual(1, len(sbom.components))
        self.assertEqual("chardet", sbom.components[0].name)
        self.assertEqual("3.0.4", sbom.components[0].version)

        self.delete_file(self.OUTPUTFILE1)
        self.delete_file(self.OUTPUTFILE2)

    @responses.activate
    def test_get_metadata_invalid_answer(self) -> None:
        # create a test requirements file
        requirements = """
        chardet==3.0.4 ; python_version >= "3.8" and python_version < "4.0"
        """
        with open(self.OUTPUTFILE1, "w") as outfile:
            outfile.write(requirements)

        sut = GetPythonDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("python")
        args.inputfile = self.OUTPUTFILE1
        args.outputfile = self.OUTPUTFILE2
        args.verbose = True
        args.debug = True
        args.search_meta_data = True

        # for login
        responses.add(
            responses.GET,
            url="https://pypi.org/pypi/chardet/3.0.4/json",
            body="""
            INVALID
            """,
            status=200,
            content_type="application/json",
            adding_headers={"Authorization": "Token " + self.MYTOKEN},
        )

        out = self.capture_stdout(sut.run, args)
        # capycli.common.json_support.write_json_to_file(out, "STDOUT.TXT")
        self.assertTrue("chardet, 3.0.4" in out)
        # self.assertTrue("WARNING: no meta data available for package" in out)

        sbom = CaPyCliBom.read_sbom(self.OUTPUTFILE2)
        self.assertIsNotNone(sbom)
        self.assertEqual(1, len(sbom.components))
        self.assertEqual("chardet", sbom.components[0].name)
        self.assertEqual("3.0.4", sbom.components[0].version)

        self.delete_file(self.OUTPUTFILE1)
        self.delete_file(self.OUTPUTFILE2)

    def test_localfile(self) -> None:
        # create a test requirements file
        requirements = """
        chardet
        certifi>=9.9.9
        django>=1.5,<1.6
        """
        with open(self.OUTPUTFILE1, "w") as outfile:
            outfile.write(requirements)

        sut = GetPythonDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("python")
        args.inputfile = self.OUTPUTFILE1
        args.outputfile = self.OUTPUTFILE2
        args.verbose = True
        args.debug = True
        args.search_meta_data = True

        out = self.capture_stdout(sut.run, args)
        # capycli.common.json_support.write_json_to_file(out, "STDOUT.TXT")
        self.assertTrue("WARNING: chardet does not have a version specified. Skipping." in out)
        self.assertTrue("WARNING: certifi is not pinned to a specific version. Using: 9.9.9" in out)
        # self.assertTrue("django is not pinned to a specific version. Using: 1.5" in out)

        self.delete_file(self.OUTPUTFILE1)
        self.delete_file(self.OUTPUTFILE2)

    def test_determine_file_type(self) -> None:
        sut = GetPythonDependencies()

        actual = sut.determine_file_type("requirements.txt")
        self.assertEqual(InputFileType.REQUIREMENTS, actual)

        actual = sut.determine_file_type("poetry.lock")
        self.assertEqual(InputFileType.POETRY_LOCK, actual)

        # test fallback
        actual = sut.determine_file_type(".gitignore")
        self.assertEqual(InputFileType.REQUIREMENTS, actual)

    def test_process_poetry_1_4_0_lock(self) -> None:
        self.delete_file(self.OUTPUTFILE2)

        sut = GetPythonDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("python")
        args.inputfile = os.path.join(os.path.dirname(__file__), "fixtures", self.INPUTFILE)
        args.outputfile = self.OUTPUTFILE2
        args.verbose = True
        args.debug = True
        args.search_meta_data = False

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Checking meta-data:" in out)
        self.assertTrue("cli_support" in out)
        self.assertTrue(self.OUTPUTFILE2 in out)
        self.assertTrue("34 components items written to file." in out)

        # ensure that dev dependencies are NOT listed
        self.assertTrue("flake8" not in out)
        self.assertTrue("responses" not in out)

        self.assertTrue(os.path.isfile(self.OUTPUTFILE2))

        self.delete_file(self.OUTPUTFILE2)

    def test_process_poetry_1_8_3_lock(self) -> None:
        # IMPORTANT: in this file there are no longer "category" values
        self.delete_file(self.OUTPUTFILE2)

        sut = GetPythonDependencies()

        # create argparse command line argument object
        args = AppArguments()
        args.command = []
        args.command.append("getdependencies")
        args.command.append("python")
        args.inputfile = self.INPUTFILE  # this is current version of this project!
        args.outputfile = self.OUTPUTFILE2
        args.verbose = True
        args.debug = True
        args.search_meta_data = False

        out = self.capture_stdout(sut.run, args)
        # self.dump_textfile(out, "DUMP.TXT")
        self.assertTrue("Checking meta-data:" in out)
        self.assertTrue("cli_support" in out)
        self.assertTrue(self.OUTPUTFILE2 in out)
        self.assertTrue("37 components items written to file." in out)

        # dev dependencies are *unfortunately* listed
        self.assertTrue("flake8" in out)
        self.assertTrue("responses" in out)

        self.assertTrue(os.path.isfile(self.OUTPUTFILE2))

        self.delete_file(self.OUTPUTFILE2)


if __name__ == "__main__":
    APP = TestGetDependenciesPython()
    APP.test_process_poetry_1_8_3_lock()
