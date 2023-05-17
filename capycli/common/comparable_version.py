# -------------------------------------------------------------------------------
# Copyright (c) 2022-2023 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from capycli import get_logger

LOG = get_logger(__name__)


class IncompatibleVersionError(Exception):
    """Base class for version compare exceptions"""
    pass


class ComparableVersion:
    """Version string comparison."""
    parts: list
    version: str

    def __init__(self, version: str):
        self.version = version
        try:
            self.parts = self.parse(version)
        except Exception:
            LOG.warning("Unable to parse version %s", version)

    @staticmethod
    def parse(version: str):
        version = version.lower()

        isdigit = False
        parts = []
        start = 0
        for i, c in enumerate(version):
            if c in [".", "-", "_"]:
                parts.append((isdigit, version[start:i]))
                start = i + 1
            elif c.isdigit():
                if not isdigit and i > start:
                    parts.append((isdigit, version[start:i]))
                    start = i
                isdigit = True
            else:
                if isdigit and i > start:
                    parts.append((isdigit, version[start:i]))
                    start = i
                isdigit = False

        if start < len(version):
            parts.append((isdigit, version[start:]))

        for i, part in enumerate(parts):
            if part[0]:
                parts[i] = (part[0], int(part[1]))

        return parts

    def compare(self, other):
        """
        Compare versions
        :param other: other version
        :return: 0 - equal, 1 - greater than, -1 - less than
        """
        try:
            return self.compare_recursive(self.parts, 0, other.parts, 0)
        except (TypeError, IndexError) as e:
            raise IncompatibleVersionError(e)

    @staticmethod
    def get_part_or_default(part_list: list, pos: int, other: list):
        if pos < len(part_list):
            return part_list[pos][1]
        elif pos < len(other):
            # No more item: if number 0 otherwise ''
            return 0 if other[pos][0] else ""
        else:
            return ""

    def compare_recursive(self, me, i, other, j):
        """
        Recursive go through version parts and compare them.
        Rules:
        1) if both part list reach the end version is equal - use greater equals since we full missing 0 to compare
        2.28 to 2.28.0.
        2) if first part is not a number -> skip the part for this version
        3) if either parts of on list reach the end -> if other part is number go for 0 otherwise ''
        """
        if i >= len(me) and j >= len(other):
            return 0
        elif i == 0 and not me[i][0]:
            # Skip prefix
            return self.compare_recursive(me, i + 1, other, j)
        elif j == 0 and not other[j][0]:
            # Skip prefix
            return self.compare_recursive(me, i, other, j + 1)

        left = self.get_part_or_default(me, i, other)
        right = self.get_part_or_default(other, j, me)

        if left == right:
            return self.compare_recursive(me, i + 1, other, j + 1)
        if left > right:
            return 1
        else:
            return -1

    def __eq__(self, other):
        """describes equality operator(==)"""
        try:
            return self.compare(other) == 0
        except IncompatibleVersionError:
            return self.version.__eq__(other.version)

    def __ne__(self, other):
        """describes not equal to operator(!=)"""
        try:
            return self.compare(other) != 0
        except IncompatibleVersionError:
            return self.version.__ne__(other.version)

    def __le__(self, other):
        """descries less than or equal to (<=)"""
        try:
            return self.compare(other) <= 0
        except IncompatibleVersionError:
            return self.version.__le__(other.version)

    def __ge__(self, other):
        """describes greater than or equal to (>=)"""
        try:
            return self.compare(other) >= 0
        except IncompatibleVersionError:
            return self.version.__ge__(other.version)

    def __gt__(self, other):
        """describes greater than (>)"""
        try:
            return self.compare(other) > 0
        except IncompatibleVersionError:
            return self.version.__gt__(other.version)

    def __lt__(self, other):
        """describes less than operator(<)"""
        try:
            return self.compare(other) < 0
        except IncompatibleVersionError:
            return self.version.__lt__(other.version)

    def __repr__(self):
        return self.version

    @property
    def major(self):
        if self.parts:
            return self.parts[0][1]
        else:
            return self.version
