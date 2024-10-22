# -------------------------------------------------------------------------------
# Copyright (c) 2023-2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from typing import List

from cyclonedx.model.component import Component
from sortedcontainers import SortedSet

from capycli import LOG

# -------------------------------------
# Expected File Format
#
# <component name>;<component version>;<optional description>
#
# Example
# python;3.8;some description
# colorama;0.4.3;another description
# wheel;0.34.2;
# tomli;2.0.1;
# -------------------------------------


class CsvSupport():
    @classmethod
    def csv_to_cdx_components(cls, inputfile: str) -> List[Component]:
        """Convert a csv file of components to a list
        of CycloneDX components."""
        bom = []
        LOG.debug(f"Reading from file {inputfile}")
        with open(inputfile) as fin:
            for line in fin:
                line = line.strip()
                parts = line.split(";")
                if len(parts) < 2:
                    continue

                name = parts[0].strip()
                version = parts[1].strip()
                description = ""
                if len(parts) > 2:
                    description = parts[2].strip()
                LOG.debug(f"  Reading from csv: name={name}, version={version}, "
                          + f"description={description}")
                cxcomp = Component(
                    name=name,
                    version=version,
                    description=description)

                bom.append(cxcomp)

        return bom

    @classmethod
    def write_cdx_components_as_csv(cls, bom: SortedSet, outputfile: str) -> None:
        LOG.debug(f"Writing to file {outputfile}")
        with open(outputfile, "w", encoding="utf-8") as fout:
            for cx_comp in bom:

                name = cx_comp.name
                version = cx_comp.version
                description = ""
                if cx_comp.description:
                    description = cx_comp.description
                fout.write(f"{name};{version};{description}\n")  # noqa

        LOG.debug("done")
