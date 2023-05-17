# -------------------------------------------------------------------------------
# Copyright (c) 2019-23 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com, sameer.panda@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import subprocess

import capycli.common.script_base


class DependenciesBase(capycli.common.script_base.ScriptBase):
    def find_source_file(self, source_url: str, package_name: str, version: str) -> str:
        """Find source file for the given package."""
        res = ""
        args = ["git", "ls-remote", "--tag", source_url]
        proc = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False)
        raw_bin_data = proc.stdout
        raw_data = raw_bin_data.decode("utf-8")
        lines = raw_data.split("\n")
        for line in lines:
            ref = line.split("\t")[-1].replace("refs/tags/", "").strip()
            if ref == (package_name + "@" + version):
                if str(source_url).endswith(".git"):
                    res = source_url.replace(".git", "/archive/refs/tags/" + (package_name + "@" + version) + ".zip")
                else:
                    res = source_url + "/archive/refs/tags/" + (package_name + "@" + version) + ".zip"
                break
            elif ref == version:
                if str(source_url).endswith(".git"):
                    res = source_url.replace(".git", "/archive/refs/tags/" + ref + ".zip")
                else:
                    res = source_url + "/archive/refs/tags/" + ref + ".zip"
                break
            elif not str(version).startswith("v") and ref == ("v" + version):
                if str(source_url).endswith(".git"):
                    res = source_url.replace(".git", "/archive/refs/tags/" + ref + ".zip")
                else:
                    res = source_url + "/archive/refs/tags/" + ref + ".zip"
                    break

        return res
