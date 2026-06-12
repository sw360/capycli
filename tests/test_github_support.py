# -------------------------------------------------------------------------------
# Copyright (c) 2025 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from unittest.mock import MagicMock

from capycli.common.github_support import GitHubSupport
from tests.test_base import TestBase


class GitHubSupportTest(TestBase):
    """Test class for GitHubSupport methods"""
    INPUTFILE1 = "sbom.siemens.capycli.json"
    OUTPUTFILE = "test.html"

    def test_init(self) -> None:
        """Test GitHubSupport initialization"""
        gh_support = GitHubSupport()
        self.assertIsNotNone(gh_support.github_project_name_regex)
        # Test regex pattern matching
        self.assertIsNotNone(gh_support.github_project_name_regex.match("owner/repo"))
        self.assertIsNotNone(gh_support.github_project_name_regex.match("sw360/capycli"))
        self.assertIsNone(gh_support.github_project_name_regex.match("invalid url with spaces"))

    def test_gh_request_headers_no_credentials(self) -> None:
        """Test header construction without credentials"""
        # Without api=True, no Accept header is added
        headers = GitHubSupport._gh_request_headers()
        self.assertEqual(headers, {})
        # With api=True, Accept header is added
        headers = GitHubSupport._gh_request_headers(api=True)
        self.assertEqual(headers, {"Accept": "application/vnd.github+json"})

    def test_gh_request_headers_with_token(self) -> None:
        """Test header construction with token"""
        headers = GitHubSupport._gh_request_headers(token="test_token", api=True)
        self.assertEqual(headers["Accept"], "application/vnd.github+json")
        self.assertEqual(headers["Authorization"], "token test_token")
        self.assertNotIn("Username", headers)

    def test_gh_request_headers_with_username_and_token(self) -> None:
        """Test header construction with username and token"""
        headers = GitHubSupport._gh_request_headers(token="test_token", username="test_user", api=True)
        self.assertEqual(headers["Accept"], "application/vnd.github+json")
        self.assertEqual(headers["Authorization"], "token test_token")
        self.assertEqual(headers["Username"], "test_user")

    def test_blocked_by_ratelimit_not_blocked(self) -> None:
        """Test rate limit check when not blocked"""
        response = MagicMock()
        response.status_code = 200
        response.headers = {}
        self.assertFalse(GitHubSupport._blocked_by_ratelimit(response))

    def test_blocked_by_ratelimit_403_with_remaining(self) -> None:
        """Test rate limit check when blocked with 403"""
        response = MagicMock()
        response.status_code = 403
        response.headers = {'x-ratelimit-remaining': '0'}
        self.assertTrue(GitHubSupport._blocked_by_ratelimit(response))

    def test_blocked_by_ratelimit_429_with_remaining(self) -> None:
        """Test rate limit check when blocked with 429"""
        response = MagicMock()
        response.status_code = 429
        response.headers = {'x-ratelimit-remaining': '0'}
        self.assertTrue(GitHubSupport._blocked_by_ratelimit(response))

    def test_blocked_by_ratelimit_403_with_remaining_nonzero(self) -> None:
        """Test rate limit check when 403 but remaining > 0"""
        response = MagicMock()
        response.status_code = 403
        response.headers = {'x-ratelimit-remaining': '10'}
        self.assertFalse(GitHubSupport._blocked_by_ratelimit(response))

    def test_calculate_ratelimit_wait_time_with_retry_after(self) -> None:
        """Test wait time calculation with retry-after header"""
        response = MagicMock()
        response.headers = {'retry-after': '30'}
        wait_time = GitHubSupport._calculate_ratelimit_wait_time(response)
        self.assertEqual(wait_time, 30)

    def test_calculate_ratelimit_wait_time_default(self) -> None:
        """Test wait time calculation with no headers"""
        response = MagicMock()
        response.headers = {}
        wait_time = GitHubSupport._calculate_ratelimit_wait_time(response)
        self.assertEqual(wait_time, GitHubSupport.default_wait_time)

    def test_credential_issue_bad_credentials(self) -> None:
        """Test credential issue detection with bad credentials"""
        response = MagicMock()
        response.ok = False
        response.json.return_value = {"message": "Bad credentials"}
        self.assertTrue(GitHubSupport._credential_issue(response))

    def test_credential_issue_no_issue(self) -> None:
        """Test credential issue detection with valid response"""
        response = MagicMock()
        response.ok = True
        self.assertFalse(GitHubSupport._credential_issue(response))

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
    APP = GitHubSupportTest()
    APP.test_get_repository_info()
