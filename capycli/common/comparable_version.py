# -------------------------------------------------------------------------------
# Copyright (c) 2022-2024 Siemens
# All Rights Reserved.
# Author: rayk.bajohr@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, List, Tuple

from capycli import get_logger

LOG = get_logger(__name__)


class IncompatibleVersionError(Exception):
    """Base class for version compare exceptions"""
    pass


class ComparableVersion:
    """Version string comparison."""
    parts: List[Tuple[Any, Any]]
    version: str

    def __init__(self, version: str) -> None:
        self.version = version
        try:
            self.parts = self.parse(version)
        except Exception:
            LOG.warning("Unable to parse version %s", version)
            raise  # pass on to caller as object is useless without self.parts

    @staticmethod
    def parse(version: str) -> List[Tuple[bool, int | str]]:
        version = version.lower()

        isdigit = False
        parts: List[Tuple[bool, int | str]] = []
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
                parts[i] = (True, int(part[1]))

        return parts

    def compare(self, other: ComparableVersion) -> int:
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
    def get_part_or_default(part_list: List[Tuple[bool, int | str]], pos: int,
                            other: List[Tuple[bool, int | str]]) -> str | int:
        if pos < len(part_list):
            return part_list[pos][1]
        elif pos < len(other):
            # No more item: if number 0 otherwise ''
            return 0 if other[pos][0] else ""
        else:
            return ""

    def compare_recursive(self, me: List[Tuple[bool, int | str]], i: int,
                          other: List[Tuple[bool, int | str]], j: int) -> int:
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
        # if str(left) > str(right): => test fails
        # if int(left) > int(right): => test fails
        if left > right:  # type: ignore
            return 1
        else:
            return -1

    def __eq__(self, other: ComparableVersion | object) -> bool:
        """describes equality operator(==)"""
        if not isinstance(other, self.__class__):
            return False

        try:
            return self.compare(other) == 0
        except IncompatibleVersionError:
            return self.version.__eq__(other.version)

    def __ne__(self, other: ComparableVersion | object) -> bool:
        """describes not equal to operator(!=)"""
        if not isinstance(other, self.__class__):
            return False

        try:
            return self.compare(other) != 0
        except IncompatibleVersionError:
            return self.version.__ne__(other.version)

    def __le__(self, other: ComparableVersion) -> bool:
        """describes less than or equal to (<=)"""
        try:
            return self.compare(other) <= 0
        except IncompatibleVersionError:
            return self.version.__le__(other.version)

    def __ge__(self, other: ComparableVersion) -> bool:
        """describes greater than or equal to (>=)"""
        try:
            return self.compare(other) >= 0
        except IncompatibleVersionError:
            return self.version.__ge__(other.version)

    def __gt__(self, other: ComparableVersion) -> bool:
        """describes greater than (>)"""
        try:
            return self.compare(other) > 0
        except IncompatibleVersionError:
            return self.version.__gt__(other.version)

    def __lt__(self, other: ComparableVersion) -> bool:
        """describes less than operator(<)"""
        try:
            return self.compare(other) < 0
        except IncompatibleVersionError:
            return self.version.__lt__(other.version)

    def __repr__(self) -> str:
        return self.version

    @property
    def major(self) -> str:
        if self.parts:
            return self.parts[0][1]
        else:
            return self.version
