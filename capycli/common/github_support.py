# -------------------------------------------------------------------------------
# Copyright (c) 2026 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, marvin.fette@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

"""
Support methods for accessing GitHub
"""

import re
import sys
import time
from typing import Any

import requests
from colorama import Fore, Style

from capycli.common.print import print_red
from capycli.main.result_codes import ResultCode


class GitHubSupport:
    """Support methods for accessing GitHub"""
    default_wait_time = 60  # seconds
    default_gh_api_timeout = 15  # seconds
    last_request_error = False

    def __init__(self) -> None:
        self.github_project_name_regex = re.compile(r"^[a-zA-Z0-9-]+(/[a-zA-Z0-9-]+)*$")

    @staticmethod
    def github_request(url: str, username: str = "", token: str = "",
                       return_response: bool = False,
                       allow_redirects: bool = True,  # default in requests
                       ) -> Any:
        """Helper method to perform GitHub API requests"""
        try:
            response = requests.get(url, headers=GitHubSupport._gh_request_headers(token, username),
                                    allow_redirects=allow_redirects,
                                    timeout=GitHubSupport.default_gh_api_timeout)

            # Check for rate limit errors (403 Forbidden or 429 Too Many Requests)
            if GitHubSupport._blocked_by_ratelimit(response):
                wait_time = GitHubSupport._calculate_ratelimit_wait_time(response)
                print(
                    Fore.LIGHTYELLOW_EX +
                    f"      Github API rate limit exceeded - wait {wait_time}s and retry ... " +
                    Style.RESET_ALL)
                time.sleep(wait_time)
                return GitHubSupport.github_request(
                    url, username, token, return_response=return_response,
                    allow_redirects=allow_redirects)

            # Check for credential issues
            if GitHubSupport._credential_issue(response):
                print_red("Invalid GitHub credential provided - aborting!")
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SERVICE)

            # Check for not found (404)
            if response.status_code == 404:
                print(
                    Fore.LIGHTYELLOW_EX +
                    f"      Resource not found at {url} - could be intended or not ... " +
                    Style.RESET_ALL)
                return response if return_response else response.json()

            # Raise an exception for other HTTP errors
            response.raise_for_status()

        except requests.exceptions.RequestException as ex:
            if GitHubSupport.last_request_error:
                print_red(
                    f"      Persistent issues accessing {url} " + repr(ex) +
                    "\n      Aborting after retried once!")
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SERVICE)

            GitHubSupport.last_request_error = True

            print(
                Fore.LIGHTYELLOW_EX +
                f"      Connection issues accessing {url} " + repr(ex) +
                "\n      Retrying using the same url." +
                Style.RESET_ALL)
            return GitHubSupport.github_request(url, username, token,
                    return_response=return_response, allow_redirects=allow_redirects)

        # Reset the error flag on success or after handling exceptions
        GitHubSupport.last_request_error = False
        return response if return_response else response.json()

    @staticmethod
    def _gh_request_headers(token: str = "", username: str = "") -> dict:
        """Helper method to construct headers for GitHub API requests."""
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = "token " + token
        if username:
            headers["Username"] = username
        return headers

    @staticmethod
    def _blocked_by_ratelimit(response: requests.Response) -> bool:
        """Check if the GitHub API response indicates that the rate limit has been exceeded."""
        if not response.status_code == 403 and not response.status_code == 429:
            return False
        if 'x-ratelimit-remaining' in response.headers:
            remaining = int(response.headers['x-ratelimit-remaining'])
            return remaining == 0
        return False

    @staticmethod
    def _calculate_ratelimit_wait_time(response: requests.Response) -> int:
        """Calculate the wait time until the GitHub API rate limit resets."""
        if 'x-ratelimit-reset' in response.headers:
            reset_time = int(response.headers['x-ratelimit-reset'])
            current_time = int(time.time())
            wait_time = reset_time - current_time
            return max(wait_time, 0)
        if 'retry-after' in response.headers:
            return int(response.headers['retry-after'])
        return GitHubSupport.default_wait_time

    @staticmethod
    def _credential_issue(response: requests.Response) -> bool:
        """Check if the response indicates a credential issue."""
        if response.status_code == 401:
            return True
        if not response.ok:
            message = response.json().get('message', '')
            return "bad credentials" in message.lower()
        return False

    @staticmethod
    def get_repositories(name: str, language: str, username: str = "", token: str = "") -> Any:
        """Query for GitHub repositories"""
        query = name + " language:" + language.lower()
        search_url = "https://api.github.com/search/repositories?q=" + query
        return GitHubSupport.github_request(search_url, username, token)

    @staticmethod
    def get_repo_name(github_url: str) -> str:
        """Extract the GitHub repo name from the specified URL."""
        git = "github.com/"
        url = github_url.replace(".git", "").replace(
            "#readme", "")[github_url.find(git) + len(git):]
        split = url.split("/")

        if len(split) > 0:
            if len(split) > 1:
                repo_name = split[0] + "/" + split[1]
            else:
                repo_name = split[0]
        else:
            print(
                Fore.LIGHTYELLOW_EX +
                "      Error getting repo name from: " + github_url +
                Style.RESET_ALL)
            return ""

        return repo_name

    #  curl -L -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28"
    # https://api.github.com/repos/tngraf/tethys.logging

    @staticmethod
    def get_repository_info(repository: str, username: str = "", token: str = "") -> Any:
        """Query for a single GitHub repository"""
        url = "https://api.github.com/repos/" + repository
        return GitHubSupport.github_request(url, username, token)
