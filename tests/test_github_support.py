# -------------------------------------------------------------------------------
# Copyright (c) 2025 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from capycli.common.github_support import GitHubSupport
from tests.test_base import TestBase


class GitHubSupportHtml(TestBase):
    """Test class for GitHubSupport methods"""
    INPUTFILE1 = "sbom.siemens.capycli.json"
    OUTPUTFILE = "test.html"

    def test_get_repositories(self) -> None:
        actual = GitHubSupport.get_repositories("capycli", "python")
        self.assertIsNotNone(actual, "GitHub request failed")
        if actual.get("total_count", 0) == 0:
            self.fail("No repositories found for the given query")

        name_match = [r for r in actual.get("items") if r.get("name", "") == "capycli"]
        if len(name_match) == 0:
            self.fail("CaPyCLI repository not found!")

    def test_get_repo_name(self) -> None:
        # simple
        repo = "https://github.com/JamesNK/Newtonsoft.Json"
        actual = GitHubSupport.get_repo_name(repo)

        self.assertEqual("JamesNK/Newtonsoft.Json", actual)

        # trailing .git
        repo = "https://github.com/restsharp/RestSharp.git"
        actual = GitHubSupport.get_repo_name(repo)

        self.assertEqual("restsharp/RestSharp", actual)

        # trailing #readme
        repo = "https://github.com/restsharp/RestSharp#readme"
        actual = GitHubSupport.get_repo_name(repo)

        self.assertEqual("restsharp/RestSharp", actual)

        # prefix git
        repo = "git://github.com/restsharp/RestSharp#readme"
        actual = GitHubSupport.get_repo_name(repo)

        self.assertEqual("restsharp/RestSharp", actual)

        # prefix git+https
        repo = "git+https://github.com/restsharp/RestSharp#readme"
        actual = GitHubSupport.get_repo_name(repo)

        self.assertEqual("restsharp/RestSharp", actual)

    def test_get_repository_info(self) -> None:
        actual = GitHubSupport.get_repository_info("sw360/capycli")
        self.assertIsNotNone(actual, "GitHub request failed")
        language = actual.get("language", "")
        if not language:
            self.fail("No language found for repository CaPyCLI")

        actual = GitHubSupport.get_repository_info("CycloneDX/cyclonedx-gomod")
        self.assertIsNotNone(actual, "GitHub request failed")
        license_info = actual.get("license", {})
        if not license_info:
            self.fail("No license info found")

        license_spdx_id = license_info.get("spdx_id", "")
        if license_spdx_id != "Apache-2.0":
            self.fail("No license SPDX ID found")

        license_name = license_info.get("name", "")
        if license_name != "Apache License 2.0":
            self.fail("No license name found")


if __name__ == "__main__":
    APP = GitHubSupportHtml()
    APP.test_get_repository_info()
