# -------------------------------------------------------------------------------
# Copyright (c) 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from typing import List

from cyclonedx.model.component import Component

from capycli import LOG
from capycli.main.exceptions import CaPyCliException

# -------------------------------------
# Expected File Format
#
# <component name>, <component version>
#
# Example
# python, 3.8
# colorama, 0.4.3
# wheel, 0.34.2
# tomli, 2.0.1
# -------------------------------------


class PlainTextSupport():
    @classmethod
    def flatlist_to_cdx_components(cls, inputfile: str) -> List[Component]:
        """Convert a flat list of components to a list
        of CycloneDX components."""
        bom = []
        LOG.debug(f"Reading from file {inputfile}")
        try:
            with open(inputfile, encoding="utf-8") as fin:
                for line in fin:
                    line = line.strip()
                    parts = line.split(",")

                    if len(parts) < 2:
                        continue

                    name = parts[0].strip()
                    version = parts[1].strip()
                    LOG.debug(f"  Reading from text: name={name}, version={version}")
                    cxcomp = Component(
                        name=name,
                        version=version)

                    bom.append(cxcomp)
        except Exception as exp:
            raise CaPyCliException("Error reading text file: " + str(exp))

        LOG.debug("done")
        return bom

    @classmethod
    def write_cdx_components_as_flatlist(cls, bom: list[Component], outputfile: str) -> None:
        LOG.debug(f"Writing to file {outputfile}")
        try:
            with open(outputfile, "w", encoding="utf-8") as fout:
                for cx_comp in bom:
                    name = cx_comp.name
                    version = cx_comp.version
                    fout.write(f"{name}, {version}\n")
        except Exception as exp:
            raise CaPyCliException("Error writing text file: " + str(exp))

        LOG.debug("done")
