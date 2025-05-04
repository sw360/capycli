# -------------------------------------------------------------------------------
# Copyright (c) 2025 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
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
    def __init__(self) -> None:
        self.github_project_name_regex = re.compile(r"^[a-zA-Z0-9-]+(/[a-zA-Z0-9-]+)*$")

    @staticmethod
    def github_request(url: str, username: str = "", token: str = "",
                       return_response: bool = False,
                       allow_redirects: bool = True,  # default in requests
                       ) -> Any:
        try:
            headers = {}
            if token:
                headers["Authorization"] = "token " + token
            if username:
                headers["Username"] = username
            response = requests.get(url, headers=headers,
                                    allow_redirects=allow_redirects)
            if response.status_code == 429 \
                    or 'rate limit exceeded' in response.reason \
                    or 'API rate limit exceeded' in response.json().get('message', ''):
                print(
                    Fore.LIGHTYELLOW_EX +
                    "      Github API rate limit exceeded - wait 60s and retry ... " +
                    Style.RESET_ALL)
                time.sleep(60)
                return GitHubSupport.github_request(url, username, token, return_response=return_response)
            if response.json().get('message', '').startswith("Bad credentials"):
                print_red("Invalid GitHub credential provided - aborting!")
                sys.exit(ResultCode.RESULT_ERROR_ACCESSING_SERVICE)

        except AttributeError as err:
            # response.json() did not return a dictionary
            if hasattr(err, 'name'):
                name = err.name
            else:  # Python prior to 3.10
                name = err.args[0].split("'")[3]
            if not name == 'get':
                raise

        except requests.exceptions.JSONDecodeError:
            response._content = b'{}'

        except requests.exceptions.ConnectionError as ex:
            print(
                Fore.LIGHTYELLOW_EX +
                f"      Connection issues accessing {url} " + repr(ex) +
                "\n      Retrying in 60 seconds!" +
                Style.RESET_ALL)
            time.sleep(60)
            return GitHubSupport.github_request(url, username, token, return_response=return_response)

        except Exception as ex:
            print(
                Fore.LIGHTYELLOW_EX +
                "      Error accessing GitHub: " + repr(ex) +
                Style.RESET_ALL)
            response = requests.Response()
            response._content = \
                b'{' + f'"exception": "{repr(ex)}"'.encode() + b'}'
        return response if return_response else response.json()

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
        url = github_url.replace(".git", "").replace("#readme", "")[github_url.find(git) + len(git):]
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
